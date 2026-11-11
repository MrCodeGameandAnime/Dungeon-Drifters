"""Overworld session orchestration around the existing Battle boundary."""

from enum import StrEnum
from typing import TypeAlias, Union

from app.content.catalog import (
    get_encounter_spec,
    get_encounter_item_rewards,
    get_encounter_item_drop_tables,
    get_encounter_rewards,
    get_drifter_spec,
    get_route_node_spec,
    get_route_successor_id,
    get_permanent_discovery_source,
)
from app.content.route_spec import RouteNodeKind
from app.content.armor_spec import get_armor_modifier
from app.content.equipment_spec import get_equipment_template
from app.content.weapon_progression_spec import get_material_spec
from app.game.game_state import GameState
from app.game.expedition_state import _now_utc
from app.game.hub_economy import HubEconomyService
from app.game.overworld_state import ContextualRoutePhase, OverworldState
from app.game.party_state import DungeonPhase, PartyState
from app.game.recruitment import available_recruitment_event
from app.game.permanent_discovery import (
    DiscoveryClaimStatus,
    PermanentDiscoveryService,
)
from app.game.run_events import RunEventService, RunEventStatus
from app.game.respec import RespecService, RespecStatus
from app.game.equipment import EquipmentActionStatus, EquipmentService
from app.game.armor_progression import ArmorProgressionService, ArmorProgressionStatus
from app.game.alchemist import AlchemistService, AlchemistStatus
from app.game.floor_two_boss_helper import (
    available_floor_two_boss_helper_ids,
    create_floor_two_boss_helper,
    floor_two_replay_requires_available_helper,
)
from app.persistence.save_port_contract import (
    SaveLoadStatus,
    SavePortError,
    is_save_port,
)
from app.iteration import first_or_none
from app.player.player_state import PlayerState
from app.presentation.overworld_models import (
    EquipmentConfirmationView,
    OverworldAction,
    OverworldAvailabilityReason,
    OverworldScreen,
    OverworldView,
    RespecPreviewView,
    StatRowView,
)
from app.presentation.battle_models import BattleView, InteractionPhase
from app.ui.overworld_ui import (
    ChooseAdvancementEquip,
    ChooseAdvancementPurchase,
    ChooseActivePair,
    ChooseDiscoverySearcher,
    ChooseDiscoveryTarget,
    ChooseExpeditionPlan,
    ChooseExpeditionReport,
    ChooseCompanion,
    ChooseFloorTwoBossHelper,
    ChooseCharacterTarget,
    ChooseMerchantCraftComponent,
    ChooseMerchantDismantle,
    ChooseMerchantImprove,
    ChooseMerchantTarget,
    ChooseMerchantTierV,
    ChooseEquipmentAction,
    ChooseEquipmentConfirmation,
    ChooseEquipmentInstance,
    ChooseHubSupplyAction,
    ChooseAlchemyRecipe,
    ChooseWeaponTarget,
    ChooseOverworldAction,
    ChooseOverworldHealingTarget,
    ChooseOverworldItem,
    ChoosePermanentStatIncrease,
    OverworldInput,
    is_overworld_ui,
)
from app.ui.battle_ui import (
    BattleInput,
    ChooseAction,
    ChooseInventoryCommand,
    ChooseInventoryCompanion,
    ChooseInventoryItem,
    ChooseHealingTarget,
    ChooseMove,
    ChooseTarget,
    ConfirmInventoryUse,
    GoBack,
)


class OverworldSessionResult(StrEnum):
    QUIT = "quit"
    SELECT_DRIFTER = "select_drifter"


SessionView: TypeAlias = Union[OverworldView, BattleView, OverworldSessionResult]
SessionInput: TypeAlias = Union[OverworldInput, BattleInput]


_BATTLE_INPUT_TYPES = (
    ChooseAction,
    ChooseMove,
    ChooseTarget,
    ChooseInventoryItem,
    ChooseInventoryCommand,
    ChooseInventoryCompanion,
    ChooseHealingTarget,
    ConfirmInventoryUse,
    GoBack,
)
_UNHANDLED_ACTION = object()


class OverworldSession:
    FLOOR_ONE_WARNING = (
        "Death means returning to the Hub. All unsecured XP, gold, and items "
        "are lost. No retry, rewind, or continue."
    )
    DEFEAT_ADVENTURE_TEXT = (
        "The encounter drove you back. Your footing is restored; retry when ready."
    )

    def __init__(
        self,
        game_state,
        *,
        battle_factory,
        enemy_factory,
        ui=None,
        battle_ui_factory=None,
        presenter=None,
        save_port=None,
        run_event_rng=None,
        now_factory=None,
    ):
        if not isinstance(game_state, GameState):
            raise TypeError("game_state must be a GameState")
        if ui is not None and not is_overworld_ui(ui):
            raise TypeError("ui must satisfy OverworldUI")
        for name, value in (
            ("battle_factory", battle_factory),
            ("enemy_factory", enemy_factory),
        ):
            if not callable(value):
                raise TypeError(f"{name} must be callable")
        if battle_ui_factory is not None and not callable(battle_ui_factory):
            raise TypeError("battle_ui_factory must be callable")
        from app.presentation.overworld_presenter import OverworldPresenter

        if presenter is None:
            presenter = OverworldPresenter()
        if not isinstance(presenter, OverworldPresenter):
            raise TypeError("presenter must be an OverworldPresenter")
        if save_port is not None and not is_save_port(save_port):
            raise TypeError("save_port must satisfy SavePort")
        if run_event_rng is not None and not callable(
            getattr(run_event_rng, "randint", None)
        ):
            raise TypeError("run_event_rng must provide randint")
        if now_factory is not None and not callable(now_factory):
            raise TypeError("now_factory must be callable")

        self._game_state = game_state
        self._ui = ui
        self._battle_factory = battle_factory
        self._enemy_factory = enemy_factory
        self._battle_ui_factory = battle_ui_factory
        self._presenter = presenter
        self._save_port = save_port
        self._run_event_rng = run_event_rng
        self._now_factory = now_factory
        self._screen = self._initial_screen(game_state)
        self._selected_item_key = None
        self._selected_character_target_id = None
        self._selected_equipment_target_id = None
        self._selected_merchant_target_id = None
        self._selected_weapon_target_id = None
        self._respec_preview = None
        self._respec_target_id = None
        self._selected_equipment_instance_id = None
        self._equipment_preview = None
        self._equipment_pending_input = None
        self._adventure_text = None
        self._notice = None
        self._quit_return_screen = None
        self._rest_return_screen = None
        self._discovery_source_id = None
        self._discovery_target_id = None
        self._expedition_outing_floor_id = None
        self._expedition_pending = None
        self._active_battle = None
        self._active_battle_context = None
        self._last_presented_view = None

    @property
    def game_state(self):
        return self._game_state

    @property
    def active_battle(self):
        return self._active_battle

    def current_view(self) -> SessionView:
        if self._active_battle is not None:
            battle = self._active_battle
            view = battle.current_view()
            if battle.is_complete:
                self._finalize_active_battle()
            return self._with_expedition_status(view)
        return self._build_view()

    def _with_expedition_status(self, view):
        assignment = self.game_state.expedition_state.active_assignment
        if not isinstance(view, BattleView) or assignment is None:
            return view
        now = (
            self._now_factory()
            if self._now_factory is not None
            else _now_utc()
        )
        remaining = self.game_state.expedition_state.assignment_remaining_seconds(now)
        clock = (
            "complete; settles when the outing ends"
            if remaining == 0
            else f"{remaining // 60}:{remaining % 60:02d} remaining"
        )
        labels = {
            "floor_one": "Floor I",
            "floor_two": "Floor II",
            "floor_three": "Floor III",
        }
        names = tuple(
            self.game_state.member_for_drifter_id(drifter_id).character.full_display_name
            for drifter_id in assignment["expedition_drifter_ids"]
        )
        status = (
            f"Expedition: {assignment['category'].title()} at "
            f"{labels[assignment['destination_floor_id']]} | {clock} | "
            + " + ".join(names)
        )
        return view.with_expedition_status(status)

    def submit(self, session_input: SessionInput):
        if self._active_battle is not None:
            battle = self._active_battle
            current_view = battle.current_view()
            if battle.is_complete:
                result = self._finalize_active_battle()
                if result is not None:
                    return result
                return self._with_expedition_status(current_view)
            if not isinstance(session_input, _BATTLE_INPUT_TYPES):
                return self._with_expedition_status(current_view)
            view = battle.submit(session_input)
            if battle.is_complete:
                result = self._finalize_active_battle()
                if result is not None:
                    return result
            return self._with_expedition_status(view)

        view = self._build_view()
        if isinstance(session_input, _BATTLE_INPUT_TYPES):
            return view
        if isinstance(session_input, (ChooseHubSupplyAction, ChooseAlchemyRecipe)):
            self._perform_hub_economy_action(view, session_input)
            return self._build_view()
        if isinstance(session_input, ChoosePermanentStatIncrease):
            self._increase_permanent_stat(view, session_input)
            if self._stale_enabled_stat_input(view, session_input):
                self._notice = "That stat is not available."
            return self._build_view()
        if isinstance(
            session_input,
            (ChooseAdvancementPurchase, ChooseAdvancementEquip),
        ):
            self._perform_advancement_action(view, session_input)
            return self._build_view()
        if isinstance(session_input, ChooseOverworldItem):
            self._select_item(view, session_input)
            return self._build_view()
        if isinstance(session_input, ChooseOverworldHealingTarget):
            self._use_overworld_healing_potion(view, session_input)
            return self._build_view()
        if isinstance(session_input, ChooseCompanion):
            self._select_companion(view, session_input)
            return self._build_view()
        if isinstance(session_input, ChooseFloorTwoBossHelper):
            self._select_floor_two_boss_helper(view, session_input)
            return self._build_view()
        if isinstance(session_input, ChooseActivePair):
            self._select_active_pair(view, session_input)
            return self._build_view()
        if isinstance(session_input, ChooseDiscoverySearcher):
            self._select_discovery_searcher(view, session_input)
            return self._build_view()
        if isinstance(session_input, ChooseDiscoveryTarget):
            self._select_discovery_target(view, session_input)
            return self._build_view()
        if isinstance(session_input, ChooseExpeditionPlan):
            self._select_expedition_plan(view, session_input)
            return self._build_view()
        if isinstance(session_input, ChooseExpeditionReport):
            self._claim_expedition_report(view, session_input)
            return self._build_view()
        if isinstance(session_input, ChooseCharacterTarget):
            self._select_character_target(view, session_input)
            return self._build_view()
        if isinstance(session_input, ChooseMerchantTarget):
            self._select_merchant_target(view, session_input)
            return self._build_view()
        if isinstance(session_input, ChooseWeaponTarget):
            self._select_weapon_target(view, session_input)
            return self._build_view()
        if isinstance(session_input, ChooseEquipmentInstance):
            self._select_equipment_instance(view, session_input)
            return self._build_view()
        if isinstance(session_input, ChooseEquipmentAction):
            self._perform_equipment_action(view, session_input)
            return self._build_view()
        if isinstance(session_input, ChooseEquipmentConfirmation):
            self._confirm_equipment_action(view, session_input)
            return self._build_view()
        if isinstance(
            session_input,
            (
                ChooseMerchantImprove,
                ChooseMerchantDismantle,
                ChooseMerchantCraftComponent,
                ChooseMerchantTierV,
            ),
        ):
            self._perform_merchant_action(view, session_input)
            return self._build_view()
        if not isinstance(session_input, ChooseOverworldAction):
            self._notice = "That option is not available."
            return self._build_view()
        if not self._action_is_offered(
            view,
            session_input.action,
        ) and not self._stale_load_was_offered(session_input.action):
            disabled_option = first_or_none(
                option
                for option in view.options
                if option.action is session_input.action and not option.enabled
            )
            if (
                disabled_option is not None
                and disabled_option.disabled_reason
                is OverworldAvailabilityReason.FLOOR_TWO_REPLAY_REQUIRES_AVAILABLE_HELPER
            ):
                self._notice = (
                    "Choose an active pair that leaves D3 or D4 available "
                    "for the Floor II boss."
                )
            elif (
                disabled_option is not None
                and disabled_option.disabled_reason
                is OverworldAvailabilityReason.FLOOR_THREE_REQUIRES_FULL_ROSTER
            ):
                self._notice = (
                    "Recruit D3 and D4 before starting Floor 3."
                )
            else:
                self._notice = (
                    "That Rest is not available."
                    if session_input.action
                    in {OverworldAction.REST, OverworldAction.SKIP_REST}
                    and (
                        view.screen is OverworldScreen.REST
                        or getattr(self._last_presented_view, "screen", None)
                        is OverworldScreen.REST
                    )
                    else "That option is not available."
                )
            return self._build_view()
        if session_input.action in {
            OverworldAction.ENTER_ENCOUNTER,
            OverworldAction.RETRY,
        }:
            battle = self._create_active_battle(ui=None)
            if battle is None:
                return self._build_view()
            battle_view = battle.current_view()
            if battle.is_complete:
                result = self._finalize_active_battle()
                if result is not None:
                    return result
            return self._with_expedition_status(battle_view)
        if session_input.action is OverworldAction.READY:
            party_state = self.game_state.party_state
            party_members = self.game_state.active_party_members
            self._select_party_target(party_members[0])
            checkpoints = tuple(
                member.create_battle_checkpoint() for member in party_members
            )
            if not party_state.begin_outing():
                self._notice = "Your party is not ready to set out."
                return self._build_view()
            try:
                battle = self._create_active_battle(ui=None, tutorial=True)
            except Exception:
                for member, checkpoint in zip(party_members, checkpoints):
                    member.restore_battle_checkpoint(checkpoint)
                party_state.cancel_outing_start()
                raise
            if battle is None:
                for member, checkpoint in zip(party_members, checkpoints):
                    member.restore_battle_checkpoint(checkpoint)
                self._active_battle_context = None
                party_state.cancel_outing_start()
                return self._build_view()
            battle_view = battle.current_view()
            if battle.is_complete:
                result = self._finalize_active_battle()
                if result is not None:
                    return result
            return self._with_expedition_status(battle_view)
        result = self._dispatch(session_input.action)
        if result is OverworldSessionResult.QUIT:
            return result
        if isinstance(result, BattleView):
            return self._with_expedition_status(result)
        return self._build_view()

    def run(self):
        if self._ui is None:
            raise RuntimeError("run() requires an overworld UI")
        if self._battle_ui_factory is None:
            raise RuntimeError("run() requires a battle UI factory")

        view = self.current_view()
        battle_ui = None
        while True:
            if isinstance(view, BattleView):
                if battle_ui is None:
                    battle_ui = self._battle_ui_factory()
                battle_ui.render(view)
                if view.interaction_phase is InteractionPhase.COMPLETE:
                    view = self.current_view()
                    battle_ui = None
                    continue
                battle_input = battle_ui.read_input(view)
                view = self.submit(battle_input)
                if view is OverworldSessionResult.SELECT_DRIFTER:
                    return view
                continue

            battle_ui = None
            self._last_presented_view = view
            self._ui.render(view)
            overworld_input = self._ui.read_input(view)
            result = self.submit(overworld_input)
            if result in {
                OverworldSessionResult.QUIT,
                OverworldSessionResult.SELECT_DRIFTER,
            }:
                return result
            if isinstance(result, (OverworldView, BattleView)):
                view = result
            else:
                view = self.current_view()

    def _stale_enabled_stat_input(self, current_view, session_input):
        previous_view = self._last_presented_view
        if (
            previous_view is None
            or previous_view.screen is not OverworldScreen.SKILLS
            or previous_view.skills is None
            or current_view.skills is None
        ):
            return False
        previous_row = first_or_none(
            row
            for row in previous_view.skills.stats
            if row.stat_name == session_input.stat_name
        )
        current_row = first_or_none(
            row
            for row in current_view.skills.stats
            if row.stat_name == session_input.stat_name
        )
        return bool(
            previous_row
            and previous_row.increase_enabled
            and current_row
            and not current_row.increase_enabled
        )

    def _stale_load_was_offered(self, action):
        if action is not OverworldAction.LOAD:
            return False
        previous_view = self._last_presented_view
        return bool(
            previous_view
            and previous_view.screen is OverworldScreen.OPTIONS
            and self._action_is_offered(previous_view, action)
        )

    def _build_view(self):
        if (
            self._screen is OverworldScreen.COMPANION_SELECTION
            and available_recruitment_event(self.game_state) is None
        ):
            self._screen = OverworldScreen.HUB
            self._adventure_text = None
        return self._presenter.build(
            self.game_state,
            screen=self._screen,
            selected_item_key=self._selected_item_key,
            selected_character_target_id=(
                self._selected_equipment_target_id
                if self._screen is OverworldScreen.EQUIPMENT
                else self._selected_character_target_id
            ),
            selected_merchant_target_id=(
                self._selected_merchant_target_id
                or self._selected_character_target_id
            ),
            selected_weapon_target_id=(
                self._selected_weapon_target_id
                or self._selected_character_target_id
            ),
            adventure_text=self._adventure_text,
            notice=self._notice,
            save_available=self._save_available(),
            load_available=self._load_available(),
            respec_available=(
                self._screen is OverworldScreen.SKILLS
                and self.game_state.party_state.phase is DungeonPhase.HUB
            ),
            respec_preview=self._respec_preview,
            selected_equipment_instance_id=self._selected_equipment_instance_id,
            equipment_confirmation=self._equipment_confirmation_view(),
            discovery_source_id=self._discovery_source_id,
            discovery_target_id=self._discovery_target_id,
            expedition_outing_floor_id=self._expedition_outing_floor_id,
            expedition_pending=self._expedition_pending,
            now=(self._now_factory() if self._now_factory is not None else None),
        )

    def _select_expedition_plan(self, view, session_input):
        if view.screen is not OverworldScreen.EXPEDITION_SETUP:
            self._notice = "That expedition choice is not available."
            return
        choice = first_or_none(
            item
            for item in view.expedition_choices
            if item.destination_floor_id == session_input.destination_floor_id
            and item.category == session_input.category
        )
        if choice is None or not choice.enabled:
            self._notice = (
                choice.disabled_reason
                if choice is not None
                else "That expedition choice is not available."
            )
            return
        self._expedition_pending = {
            "destination_floor_id": choice.destination_floor_id,
            "category": choice.category,
        }
        self._screen = OverworldScreen.EXPEDITION_CONFIRMATION
        self._notice = None

    def _claim_expedition_report(self, view, session_input):
        if view.screen is not OverworldScreen.EXPEDITIONS:
            self._notice = "That expedition report is not available."
            return
        report = first_or_none(
            item
            for item in view.expedition_reports
            if item.report_id == session_input.report_id
        )
        if report is None:
            self._notice = "That expedition report is not available."
            return
        if report.claimed:
            self._notice = "That expedition report was already claimed."
            return
        from app.game.expeditions import ExpeditionClaimStatus, ExpeditionService

        options = (
            {}
            if self._now_factory is None
            else {"now_factory": self._now_factory}
        )
        result = ExpeditionService(
            self._save_port_instance(),
            **options,
        ).claim_report(
            self.game_state,
            session_input.report_id,
            confirmed=True,
        )
        if result.status is ExpeditionClaimStatus.CLAIMED:
            self._game_state = result.game_state
            self._notice = "Expedition report claimed."
        elif result.status is ExpeditionClaimStatus.SAVE_FAILED:
            self._notice = "The report could not be saved. Nothing changed."
        elif result.status is ExpeditionClaimStatus.ALREADY_CLAIMED:
            self._notice = "That expedition report was already claimed."
        else:
            self._notice = "That expedition report is no longer available."

    def _confirm_expedition_launch(self):
        from app.game.expeditions import ExpeditionLaunchStatus, ExpeditionService

        if self._expedition_pending is None or self._expedition_outing_floor_id is None:
            self._notice = "That expedition launch is not available."
            return None
        options = (
            {}
            if self._now_factory is None
            else {"now_factory": self._now_factory}
        )
        result = ExpeditionService(
            self._save_port_instance(),
            **options,
        ).launch(
            self.game_state,
            outing_floor_id=self._expedition_outing_floor_id,
            destination_floor_id=self._expedition_pending["destination_floor_id"],
            category=self._expedition_pending["category"],
            confirmed=True,
        )
        if result.status is not ExpeditionLaunchStatus.LAUNCHED:
            self._notice = (
                result.reason
                or {
                    ExpeditionLaunchStatus.INSUFFICIENT_ENERGY:
                    "You need 10 energy to launch an assignment.",
                    ExpeditionLaunchStatus.SAVE_FAILED:
                    "The assignment could not be saved. Nothing changed.",
                    ExpeditionLaunchStatus.FLOOR_THREE_BLOCKED:
                    "An assignment cannot accompany a Floor III outing.",
                }.get(result.status, "That expedition launch is not available.")
            )
            return None
        self._game_state = result.game_state
        self._expedition_pending = None
        self._expedition_outing_floor_id = None
        self._screen = OverworldScreen.MAIN
        self._adventure_text = "Your party sets out; the expedition runs passively."
        battle = self._create_active_battle(ui=None)
        if battle is None:
            self._notice = "Your assignment is active. Enter the encounter when ready."
            return None
        battle_view = battle.current_view()
        if battle.is_complete:
            result = self._finalize_active_battle()
            if result is not None:
                return result
        return battle_view

    def _equipment_confirmation_view(self):
        if self._screen is not OverworldScreen.EQUIPMENT_CONFIRMATION:
            return None
        preview = self._equipment_preview
        if preview is None:
            return None
        details = []
        if preview.gold_cost:
            details.append(f"Cost: {preview.gold_cost} gold")
        if preview.gold_award:
            details.append(f"Gain: {preview.gold_award} gold")
        if preview.material_costs:
            details.append(
                "Materials consumed: "
                + ", ".join(
                    f"{quantity} {get_material_spec(item_id).display_name}"
                    for item_id, quantity in preview.material_costs
                )
            )
        if preview.material_yields:
            details.append(
                "Salvage gained: "
                + ", ".join(
                    f"{quantity} {get_material_spec(item_id).display_name}"
                    for item_id, quantity in preview.material_yields
                )
            )
        if preview.incoming_modifier is not None:
            details.append(
                "Incoming modifier consumed: "
                + get_armor_modifier(preview.incoming_modifier).name
            )
        if preview.destroyed_modifiers:
            names = ", ".join(
                get_armor_modifier(modifier_id).name
                for modifier_id in preview.destroyed_modifiers
            )
            details.append(f"Modifiers permanently destroyed: {names}")
        if preview.extracted_modifiers:
            names = ", ".join(
                get_armor_modifier(modifier_id).name
                for modifier_id in preview.extracted_modifiers
            )
            details.append(f"Modifiers recovered: {names}")
        if preview.destroys_equipment:
            details.append("Donor armor will be destroyed.")
        if preview.action == "sell":
            details.append(
                "Only authored gold is awarded; attached modifiers are not returned."
            )
        elif preview.action == "dismantle":
            details.append(
                "Only authored salvage is awarded; attached modifiers are not returned."
            )
        elif preview.action == "extract":
            details.append(
                "Installed modifiers are preserved; the donor armor is sacrificed."
            )
        elif preview.action == "affix":
            details.append("The incoming modifier and listed costs will be consumed.")
            if preview.displaced_modifiers:
                details.append(
                    "Replacing the installed modifier permanently destroys it."
                )
        action = preview.action.replace("_", " ").title()
        return EquipmentConfirmationView(
            title=f"Confirm {action}",
            details=tuple(details) or ("Proceed with this equipment action?",),
        )

    def _save_available(self):
        if self.game_state.overworld_state.active_route_id == "floor_one":
            overworld = self.game_state.overworld_state
            return bool(
                self._screen is OverworldScreen.REST
                and self.game_state.party_state.phase is DungeonPhase.OUTING
                and get_route_node_spec(
                    overworld.current_route_node_id
                ).kind
                is RouteNodeKind.REST
                and overworld.current_route_node_id
                not in overworld.resolved_rest_node_ids
            )
        return self._screen in {
            OverworldScreen.OPTIONS,
            OverworldScreen.REST,
        }

    def _load_available(self):
        if self._screen is not OverworldScreen.OPTIONS:
            return False
        try:
            return self._save_port_instance().inspect().status is SaveLoadStatus.VALID
        except SavePortError:
            return False

    def _save_port_instance(self):
        if self._save_port is None:
            from app.persistence.bootstrap import build_default_save_port

            self._save_port = build_default_save_port()
        return self._save_port

    def _select_item(self, view, overworld_input):
        if view.screen is not OverworldScreen.ITEMS or view.inventory is None:
            self._notice = "That item is not available."
            return
        if not any(
            item.selection_key == overworld_input.selection_key
            for item in view.inventory.items
        ):
            self._notice = "That item is not available."
            return
        self._selected_item_key = overworld_input.selection_key
        self._notice = None

    def _perform_advancement_action(self, view, session_input):
        skills = view.skills
        if (
            view.screen is not OverworldScreen.SKILLS
            or skills is None
            or skills.selected_target_id != session_input.drifter_id
        ):
            self._notice = "That skill is not available for the selected Drifter."
            return
        try:
            player = self.game_state.member_for_drifter_id(
                session_input.drifter_id
            )
        except (TypeError, ValueError):
            self._notice = "That Drifter is not available."
            return

        if isinstance(session_input, ChooseAdvancementPurchase):
            option = first_or_none(
                row
                for row in skills.advancement_options
                if row.skill_id == session_input.skill_id
            )
            if option is None or not option.can_purchase:
                self._notice = (
                    option.blocked_reason
                    if option is not None
                    else "That skill is not available."
                )
                return
            try:
                purchased = player.purchase_advancement(session_input.skill_id)
            except (TypeError, ValueError):
                self._notice = "That skill is not available."
                return
            self._notice = (
                f"{purchased.name} learned for {purchased.gp_cost} Growth Points."
            )
            return

        if not any(
            move.move_id == session_input.move_id
            for move in skills.available_moves
        ):
            self._notice = "That move is not unlocked for the selected Drifter."
            return
        try:
            player.equip_normal_move(
                session_input.move_id,
                slot=session_input.slot,
            )
        except (TypeError, ValueError):
            self._notice = "That move cannot be equipped in this slot."
            return
        self._notice = f"Loadout slot {session_input.slot + 1} updated."

    def _use_overworld_healing_potion(self, view, session_input):
        if (
            view.screen is not OverworldScreen.HEALING_TARGETS
            or not any(
                target.drifter_id == session_input.drifter_id
                for target in view.healing_targets
            )
            or self._selected_item_key != "carried-item:healing_potion"
        ):
            self._notice = "That healing target is not available."
            return
        target = self.game_state.member_for_drifter_id(session_input.drifter_id)
        before = target.health.current
        if not self.game_state.party_state.use_healing_potion(
            target,
            deployed_members=self.game_state.active_party_members,
        ):
            self._notice = "The Healing Potion is no longer available."
            return
        restored = target.health.current - before
        self._screen = OverworldScreen.ITEMS
        if self.game_state.party_state.carried_items.get("healing_potion", 0):
            self._selected_item_key = "carried-item:healing_potion"
        else:
            self._selected_item_key = None
        self._notice = (
            f"Healing Potion restored {restored} HP to "
            f"{target.character.full_display_name}."
        )

    def _select_companion(self, view, session_input):
        if view.screen is not OverworldScreen.COMPANION_SELECTION:
            self._notice = "That Drifter is not available."
            return
        event = available_recruitment_event(self.game_state)
        if event is None:
            self._screen = OverworldScreen.HUB
            self._adventure_text = None
            self._notice = "That Drifter is not available."
            return
        choice = first_or_none(
            choice
            for choice in view.companion_choices
            if choice.event_id == session_input.event_id
            and choice.drifter_id == session_input.drifter_id
        )
        if choice is None or event.event_id != session_input.event_id:
            self._notice = "That Drifter is not available."
            return
        if self.game_state.party_state.shared_gold < event.cost:
            self._notice = f"You need {event.cost} shared gold to recruit a Drifter."
            return
        try:
            profile = get_drifter_spec(choice.drifter_id)
            companion = PlayerState(profile.create_character())
            if event.event_id == "floor_two_hub_recruitment":
                candidate = self.game_state.clone()
                recruited = candidate.party_state.recruit_companion(
                    candidate.player_state,
                    companion,
                    cost=event.cost,
                )
                if not recruited:
                    self._notice = (
                        f"You need {event.cost} shared gold to recruit a Drifter."
                    )
                    return
                try:
                    result = self._save_port_instance().save(candidate)
                except (SavePortError, TypeError, ValueError):
                    result = None
                if result is None or result.status is not SaveLoadStatus.SAVED:
                    self._notice = (
                        "The recruitment could not be saved. Nothing changed."
                    )
                    return
                self._game_state = candidate
                self._screen = OverworldScreen.HUB
                self._adventure_text = (
                    f"{profile.display_name} joins the roster at Level 1. "
                    "Your active party remains unchanged."
                )
                self._notice = None
                return
            if event.route_id == "floor_two":
                candidate = self.game_state.clone()
                target_level = min(
                    member.level_state.current
                    for member in candidate.active_party_members
                )
                while companion.level_state.current < target_level:
                    companion.gain_experience(
                        companion.level_state.next_threshold
                    )
                recruited = candidate.party_state.recruit_floor_two_companion(
                    companion,
                    recruited_ids=tuple(
                        member.character.profile.drifter_id
                        for member in candidate.recruited_members
                    ),
                    cost=event.cost,
                )
                if not recruited:
                    self._notice = (
                        f"You need {event.cost} shared gold to recruit a Drifter."
                    )
                    return
                candidate.story_state.complete_event(event.event_id)
                try:
                    result = self._save_port_instance().save(candidate)
                except (SavePortError, TypeError, ValueError):
                    result = None
                if result is None or result.status is not SaveLoadStatus.SAVED:
                    self._notice = (
                        "The recruitment could not be saved. Nothing changed."
                    )
                    return
                self._game_state = candidate
                self._screen = OverworldScreen.REST
                self._rest_return_screen = None
                self._adventure_text = (
                    f"{profile.display_name} joins the roster at Midway Rest. "
                    "Your active party remains unchanged."
                )
                self._notice = None
                return
            recruited = self.game_state.party_state.recruit_companion(
                self.game_state.player_state,
                companion,
                cost=event.cost,
            )
        except (TypeError, ValueError):
            self._notice = "That Drifter is not available."
            return
        if not recruited:
            self._notice = f"You need {event.cost} shared gold to recruit a Drifter."
            return
        self.game_state.story_state.complete_event(event.event_id)
        self._screen = OverworldScreen.PARTY_READY
        lead_name = self.game_state.player_state.character.full_display_name
        self._adventure_text = (
            f"{profile.display_name} joins {lead_name}. "
            "Your party is ready to set out."
        )
        self._notice = None

    def _select_floor_two_boss_helper(self, view, session_input):
        if (
            view.screen is not OverworldScreen.FLOOR_TWO_HELPER_SELECTION
            or not any(
                choice.drifter_id == session_input.drifter_id
                for choice in view.temporary_helper_choices
            )
        ):
            self._notice = "That temporary helper is not available."
            return
        candidate = self.game_state.clone()
        node_id = candidate.overworld_state.current_route_node_id
        try:
            if not candidate.party_state.select_floor_two_boss_helper(
                session_input.drifter_id,
                node_id=node_id,
            ):
                self._notice = "A Floor II boss helper has already been selected."
                return
            result = self._save_port_instance().save(candidate)
        except (OSError, SavePortError, TypeError, ValueError):
            result = None
        if result is None or result.status is not SaveLoadStatus.SAVED:
            self._notice = "The helper choice could not be saved. Nothing changed."
            return
        self._game_state = candidate
        self._screen = (
            OverworldScreen.REST
            if node_id == "floor_two_pre_boss_rest"
            else OverworldScreen.MAIN
        )
        self._adventure_text = None
        self._notice = None

    def _select_active_pair(self, view, session_input):
        offered = any(
            choice.drifter_ids == session_input.drifter_ids
            for choice in view.active_party_choices
        )
        if view.screen is not OverworldScreen.PARTY_SELECTION or not offered:
            self._notice = "That party is not available."
            return
        try:
            self.game_state.party_state.select_active_pair(
                session_input.drifter_ids,
                recruited_ids=tuple(
                    member.character.profile.drifter_id
                    for member in self.game_state.recruited_members
                ),
            )
        except (TypeError, ValueError):
            self._notice = "That party is not available."
            return
        self._select_party_target(
            self.game_state.member_for_drifter_id(session_input.drifter_ids[0])
        )
        self._screen = OverworldScreen.HUB
        self._adventure_text = None
        self._notice = None

    def _select_party_target(self, member):
        drifter_id = member.character.profile.drifter_id
        self._selected_character_target_id = drifter_id
        self._selected_merchant_target_id = drifter_id
        self._selected_weapon_target_id = drifter_id

    def _select_merchant_target(self, view, session_input):
        merchant = view.merchant
        if view.screen is not OverworldScreen.MERCHANT or merchant is None:
            self._notice = "That Drifter is not available."
            return
        if not any(
            target.drifter_id == session_input.drifter_id
            for target in merchant.targets
        ):
            self._notice = "That Drifter is not available."
            return
        self._selected_merchant_target_id = session_input.drifter_id
        self._selected_character_target_id = session_input.drifter_id
        self._selected_weapon_target_id = session_input.drifter_id
        self._notice = None

    def _select_weapon_target(self, view, session_input):
        weapon = view.weapon
        if view.screen is not OverworldScreen.WEAPON or weapon is None:
            self._notice = "That Drifter is not available."
            return
        if not any(
            target.drifter_id == session_input.drifter_id
            for target in weapon.targets
        ):
            self._notice = "That Drifter is not available."
            return
        self._selected_weapon_target_id = session_input.drifter_id
        self._selected_character_target_id = session_input.drifter_id
        self._selected_merchant_target_id = session_input.drifter_id
        self._notice = None

    def _select_character_target(self, view, session_input):
        targets = None
        if view.screen is OverworldScreen.CHARACTER and view.character is not None:
            targets = view.character.targets
        elif view.screen is OverworldScreen.SKILLS and view.skills is not None:
            targets = view.skills.targets
        elif view.screen is OverworldScreen.EQUIPMENT and view.equipment is not None:
            targets = view.equipment.targets
        if targets is None or not any(
            target.drifter_id == session_input.drifter_id for target in targets
        ):
            self._notice = "That Drifter is not available."
            return
        if view.screen is OverworldScreen.EQUIPMENT:
            self._selected_equipment_target_id = session_input.drifter_id
        else:
            self._selected_character_target_id = session_input.drifter_id
            self._selected_weapon_target_id = session_input.drifter_id
            self._selected_merchant_target_id = session_input.drifter_id
        self._notice = None

    def _select_equipment_instance(self, view, session_input):
        equipment = view.equipment
        if view.screen is not OverworldScreen.EQUIPMENT or equipment is None:
            self._notice = "That equipment is not available."
            return
        if not any(
            item.instance_id == session_input.instance_id
            for item in equipment.instances
        ):
            self._notice = "That equipment is not available."
            return
        self._selected_equipment_instance_id = session_input.instance_id
        self._notice = None

    def _perform_equipment_action(self, view, session_input):
        equipment = view.equipment
        if (
            view.screen is not OverworldScreen.EQUIPMENT
            or equipment is None
            or session_input.equipment_instance_id != equipment.selected_instance_id
            or session_input.target_drifter_id != equipment.selected_target_id
        ):
            self._notice = "Choose that equipment and Drifter before continuing."
            return
        action = first_or_none(
            candidate
            for candidate in equipment.actions
            if candidate.operation == session_input.operation.value
            and candidate.modifier_instance_id == session_input.modifier_instance_id
        )
        if action is None or not action.enabled:
            self._notice = "That equipment action is not available."
            return
        if session_input.operation.value == "equip":
            result = EquipmentService(
                save_port=self._save_port_instance()
            ).equip(
                self.game_state,
                target_drifter_id=session_input.target_drifter_id,
                instance_id=session_input.equipment_instance_id,
            )
            if result.status is EquipmentActionStatus.EQUIPPED:
                self._game_state = result.game_state
                self._notice = "Equipment assigned to the selected Drifter."
            else:
                self._notice = "That equipment could not be assigned."
            return
        if session_input.operation.value in {"upgrade", "advance_rarity"}:
            service = ArmorProgressionService(save_port=self._save_port_instance())
            if session_input.operation.value == "upgrade":
                result = service.upgrade_stat(
                    self.game_state,
                    instance_id=session_input.equipment_instance_id,
                )
                success = ArmorProgressionStatus.UPGRADED
                completed = "Armor stats upgraded."
            else:
                result = service.advance_rarity(
                    self.game_state,
                    instance_id=session_input.equipment_instance_id,
                )
                success = ArmorProgressionStatus.RARITY_ADVANCED
                completed = "Armor rarity advanced."
            if result.status is success:
                self._game_state = result.game_state
                self._notice = completed
            else:
                self._notice = (
                    "That armor action could not be completed: "
                    + result.status.value.replace("_", " ")
                    + "."
                )
            return

        if session_input.operation.value == "sell":
            preview = AlchemistService.preview_sale(
                self.game_state,
                instance_id=session_input.equipment_instance_id,
            )
        elif session_input.operation.value == "dismantle":
            preview = AlchemistService.preview_dismantle(
                self.game_state,
                instance_id=session_input.equipment_instance_id,
            )
        elif session_input.operation.value == "extract":
            preview = AlchemistService.preview_extraction(
                self.game_state,
                instance_id=session_input.equipment_instance_id,
            )
        elif session_input.operation.value == "affix":
            preview = AlchemistService.preview_affix(
                self.game_state,
                instance_id=session_input.equipment_instance_id,
                modifier_instance_id=session_input.modifier_instance_id,
            )
        else:
            self._notice = "That equipment action is not available."
            return
        if not preview.can_apply:
            self._notice = (
                "That Alchemist action is unavailable: "
                + preview.status.value.replace("_", " ")
                + "."
            )
            return
        self._equipment_preview = preview
        self._equipment_pending_input = session_input
        self._screen = OverworldScreen.EQUIPMENT_CONFIRMATION
        self._notice = None

    def _confirm_equipment_action(self, view, session_input):
        if (
            view.screen is not OverworldScreen.EQUIPMENT_CONFIRMATION
            or self._equipment_preview is None
            or self._equipment_pending_input is None
        ):
            self._notice = "That confirmation is not available."
            return
        if not session_input.confirmed:
            self._screen = OverworldScreen.EQUIPMENT
            self._equipment_preview = None
            self._equipment_pending_input = None
            self._notice = "Cancelled. Nothing changed."
            return

        pending = self._equipment_pending_input
        preview = self._equipment_preview
        instance_id = pending.equipment_instance_id
        try:
            item_name = get_equipment_template(
                self.game_state.party_state.equipment_instance(instance_id).definition_id
            ).name
        except ValueError:
            item_name = "Equipment"
        alchemist = AlchemistService(save_port=self._save_port_instance())
        if pending.operation.value == "sell":
            result = alchemist.sell(
                self.game_state,
                instance_id=instance_id,
                confirmation=preview,
            )
            success = AlchemistStatus.SOLD
            notice = f"Sold {item_name}; gained {preview.gold_award} gold. Installed modifiers were destroyed."
        elif pending.operation.value == "dismantle":
            result = alchemist.dismantle(
                self.game_state,
                instance_id=instance_id,
                confirmation=preview,
            )
            success = AlchemistStatus.DISMANTLED
            notice = f"Dismantled {item_name}; gained authored salvage. Installed modifiers were destroyed."
        elif pending.operation.value == "extract":
            result = alchemist.extract(
                self.game_state,
                instance_id=instance_id,
                confirmation=preview,
            )
            success = AlchemistStatus.EXTRACTED
            notice = f"Extracted modifiers from {item_name}; the donor armor was destroyed."
        elif pending.operation.value == "affix":
            result = alchemist.affix(
                self.game_state,
                instance_id=instance_id,
                modifier_instance_id=pending.modifier_instance_id,
                confirmation=preview,
            )
            success = (
                AlchemistStatus.REPLACED
                if preview.displaced_modifiers
                else AlchemistStatus.AFFIXED
            )
            incoming = get_armor_modifier(preview.incoming_modifier).name
            notice = f"Installed {incoming}."
            if preview.displaced_modifiers:
                displaced = ", ".join(
                    get_armor_modifier(modifier_id).name
                    for modifier_id in preview.displaced_modifiers
                )
                notice += f" {displaced} was permanently destroyed."
        else:
            self._notice = "That confirmation is not available."
            return

        self._screen = OverworldScreen.EQUIPMENT
        self._equipment_preview = None
        self._equipment_pending_input = None
        if result.status is success:
            self._game_state = result.game_state
            if pending.operation.value in {"sell", "dismantle", "extract"}:
                self._selected_equipment_instance_id = None
            self._notice = notice
        else:
            self._notice = (
                "Nothing changed. The action could not be completed: "
                + result.status.value.replace("_", " ")
                + "."
            )

    def _perform_hub_economy_action(self, view, session_input):
        economy = view.hub_economy
        if view.screen is not OverworldScreen.MERCHANT or economy is None:
            self._notice = "That Hub supply action is not available."
            return
        service = HubEconomyService(self.game_state)
        if isinstance(session_input, ChooseAlchemyRecipe):
            recipe = first_or_none(
                value for value in economy.recipes
                if value.recipe_id == session_input.recipe_id
            )
            if recipe is None or not recipe.can_craft:
                self._notice = "That Alchemy recipe is not available."
                return
            result = service.craft_alchemy(recipe.recipe_id)
            self._notice = (
                f"Crafted {recipe.display_name}."
                if result.success
                else "The Alchemy recipe could not be completed."
            )
            return

        item = first_or_none(
            value for value in economy.items
            if value.item_id == session_input.item_id
        )
        if item is None:
            self._notice = "That Hub item is not available."
            return
        operation = session_input.operation.value
        enabled = {
            "buy": item.can_buy,
            "sell": item.can_sell,
            "load": item.can_load,
            "unload": item.can_unload,
        }[operation]
        if not enabled:
            self._notice = {
                "buy": "That item is unavailable or you do not have enough gold.",
                "sell": "That item is not sellable or is not in Hub storage.",
                "load": "That item is not in storage or the carried pack is full.",
                "unload": "That item is not in the carried pack.",
            }[operation]
            return
        result = getattr(service, operation)(item_id=item.item_id, quantity=1)
        if not result.success:
            self._notice = {
                "insufficient_gold": "You do not have enough gold.",
                "insufficient_items": "That quantity is no longer available.",
                "pack_full": "The carried pack is full.",
                "not_carryable": "That item cannot be carried as a supply.",
                "not_sellable": "That item cannot be sold.",
            }.get(result.reason, "That Hub supply action was rejected.")
            return
        self._notice = {
            "buy": f"Bought 1 {item.display_name} into Hub storage.",
            "sell": f"Sold 1 {item.display_name} for {result.gold_delta} gold.",
            "load": f"Loaded 1 {item.display_name} into the carried pack.",
            "unload": f"Returned 1 {item.display_name} to Hub storage.",
        }[operation]

    def _perform_merchant_action(self, view, session_input):
        from app.game.weapon_progression import WeaponProgressionService

        merchant = view.merchant
        if view.screen is not OverworldScreen.MERCHANT or merchant is None:
            self._notice = "That merchant action is not available."
            return
        target_id = session_input.target_drifter_id
        if target_id != merchant.selected_target_id or not any(
            target.drifter_id == target_id for target in merchant.targets
        ):
            self._notice = "Choose that Drifter before using the merchant."
            return

        service = WeaponProgressionService(self.game_state)
        if isinstance(session_input, ChooseMerchantTierV):
            if merchant.tier_v.completed or not merchant.tier_v.can_attempt:
                self._notice = (
                    "The Tier V attempt is not available: "
                    f"{merchant.tier_v.blocked_reason or 'already complete'}."
                )
                return
            result = service.attempt_tier_v(target_drifter_id=target_id)
            if result.success:
                self._notice = "Tier V succeeded. Grade-IV materials were consumed."
            elif result.attempted:
                self._notice = (
                    "Tier V attempt failed. Grade-IV materials were consumed; "
                    "weapon progress was preserved."
                )
            else:
                self._notice = self._merchant_failure_message(result.reason)
            return
        if isinstance(session_input, ChooseMerchantCraftComponent):
            recipe = first_or_none(
                candidate
                for candidate in merchant.component_recipes
                if candidate.component_id == session_input.component_id
            )
            if recipe is None or not recipe.can_craft:
                self._notice = "That component recipe is not available."
                return
            result = service.craft_component(
                target_drifter_id=target_id,
                component_id=recipe.component_id,
            )
            if result.success:
                effect_summary = "; ".join(recipe.effect_summary)
                self._notice = (
                    f"Crafted and installed {recipe.display_name} in "
                    f"{recipe.slot_label}. "
                    f"Crafting Level {result.crafting_level}."
                )
                if effect_summary:
                    self._notice += f" Effects: {effect_summary}."
            else:
                self._notice = self._merchant_failure_message(result.reason)
            return
        if isinstance(session_input, ChooseMerchantImprove):
            slot = first_or_none(
                candidate
                for candidate in merchant.slots
                if candidate.slot_id == session_input.slot_id
            )
            if slot is None or not slot.can_improve:
                self._notice = "That weapon improvement is not available."
                return
            result = service.improve_slot(
                target_drifter_id=target_id,
                slot_id=slot.slot_id,
            )
            if result.success:
                self._notice = (
                    f"{slot.label} improved to {result.slot_progress}/100. "
                    f"Crafting Level {result.crafting_level}."
                )
            else:
                self._notice = self._merchant_failure_message(result.reason)
            return

        dismantle = first_or_none(
            candidate
            for candidate in merchant.dismantle_items
            if candidate.item_id == session_input.item_id
        )
        if dismantle is None or session_input.quantity > dismantle.quantity:
            self._notice = "That dismantling action is not available."
            return
        result = service.dismantle(
            target_drifter_id=target_id,
            item_id=dismantle.item_id,
            quantity=session_input.quantity,
        )
        if result.success:
            outputs = ", ".join(
                f"{quantity} {item_id.replace('_', ' ')}"
                for item_id, quantity in sorted(result.materials.items())
            )
            self._notice = f"Dismantled {dismantle.display_name}: {outputs}."
        else:
            self._notice = "That item is no longer available to dismantle."

    @staticmethod
    def _merchant_failure_message(reason):
        return {
            "tier_locked": "All weapon slots and Crafting must reach the current tier gate first.",
            "insufficient_materials": "You do not have enough of the required material.",
            "maximum_progress": "That weapon slot is fully improved.",
            "already_installed": "That component is already installed.",
        }.get(reason, "That weapon improvement is not available.")

    def _increase_permanent_stat(self, view, overworld_input):
        if view.screen is not OverworldScreen.SKILLS or view.skills is None:
            self._notice = "That stat is not available."
            return

        row = first_or_none(
            row
            for row in view.skills.stats
            if row.stat_name == overworld_input.stat_name
        )
        if row is None or not row.increase_enabled:
            self._notice = self._stat_unavailable_message(
                row.disabled_reason if row is not None else None
            )
            return

        try:
            selected_id = view.skills.selected_target_id
            member = self.game_state.member_for_drifter_id(selected_id)
            new_value = member.increase_permanent_stat(row.stat_name)
        except (TypeError, ValueError):
            self._notice = "That stat is not available."
            return

        self._notice = (
            f"{row.label} increased to {new_value}. "
            f"Growth Points remaining: "
            f"{member.growth_points}."
        )

    @staticmethod
    def _stat_unavailable_message(reason):
        if reason is OverworldAvailabilityReason.NO_GROWTH_POINTS:
            return "Earn Growth Points by leveling up."
        if reason is OverworldAvailabilityReason.STAT_AT_MAXIMUM:
            return "That stat is already at its maximum."
        return "That stat is not available."

    @staticmethod
    def _action_is_offered(view, action):
        contextual = view.contextual_route_option
        if (
            contextual is not None
            and contextual.action is action
            and contextual.enabled
        ):
            return True
        return any(
            option.action is action and option.enabled
            for option in view.options
        )

    def _dispatch(self, action):
        self._notice = None
        result = self._dispatch_overworld_navigation(action)
        if result is not _UNHANDLED_ACTION:
            return result
        result = self._dispatch_party_action(action)
        if result is not _UNHANDLED_ACTION:
            return result
        result = self._dispatch_floor_one_action(action)
        if result is not _UNHANDLED_ACTION:
            return result
        result = self._dispatch_discovery_action(action)
        if result is not _UNHANDLED_ACTION:
            return result
        if action is OverworldAction.RETURN_TO_HUB:
            self._return_to_hub()
            return None
        result = self._dispatch_menu_action(action)
        if result is not _UNHANDLED_ACTION:
            return result
        result = self._dispatch_rest_action(action)
        if result is not _UNHANDLED_ACTION:
            return result
        if action in (OverworldAction.ENTER_ENCOUNTER, OverworldAction.RETRY):
            self._run_current_encounter()
            return None
        self._notice = self._unavailable_action_message(action)
        return None

    def _dispatch_overworld_navigation(self, action):
        if action is OverworldAction.BACK:
            self._navigate_back()
            return None
        navigation = {
            OverworldAction.CHARACTER: OverworldScreen.CHARACTER,
            OverworldAction.ITEMS: OverworldScreen.ITEMS,
            OverworldAction.MAP: OverworldScreen.MAP,
            OverworldAction.OPTIONS: OverworldScreen.OPTIONS,
            OverworldAction.SKILLS: OverworldScreen.SKILLS,
            OverworldAction.WEAPON: OverworldScreen.WEAPON,
            OverworldAction.EQUIPMENT: OverworldScreen.EQUIPMENT,
            OverworldAction.MERCHANT: OverworldScreen.MERCHANT,
            OverworldAction.SELECT_PARTY: OverworldScreen.PARTY_SELECTION,
        }
        if action in navigation:
            if (
                self._screen is OverworldScreen.REST
                and self.game_state.overworld_state.active_route_id
                in {"floor_one", "floor_two", "floor_three"}
                and navigation[action]
                in {OverworldScreen.CHARACTER, OverworldScreen.ITEMS}
            ):
                self._rest_return_screen = OverworldScreen.REST
            self._screen = navigation[action]
            if self._screen is not OverworldScreen.ITEMS:
                self._selected_item_key = None
            return None
        return _UNHANDLED_ACTION

    def _dispatch_party_action(self, action):
        if action is OverworldAction.EXPEDITIONS:
            from app.game.expeditions import ExpeditionService

            if (
                self._screen is not OverworldScreen.HUB
                or self.game_state.party_state.phase is not DungeonPhase.HUB
                or not ExpeditionService._is_unlocked(self.game_state)
            ):
                self._notice = "Expeditions are not available here."
                return None
            self._screen = OverworldScreen.EXPEDITIONS
            self._adventure_text = None
            return None
        if action in {
            OverworldAction.PREPARE_EXPEDITION_FLOOR_ONE,
            OverworldAction.PREPARE_EXPEDITION_FLOOR_TWO,
        }:
            if (
                self._screen is not OverworldScreen.EXPEDITIONS
                or self.game_state.party_state.phase is not DungeonPhase.HUB
            ):
                self._notice = "Choose an outing from the Hub first."
                return None
            outing_floor_id = (
                "floor_one"
                if action is OverworldAction.PREPARE_EXPEDITION_FLOOR_ONE
                else "floor_two"
            )
            if outing_floor_id == "floor_two" and (
                not self.game_state.party_state.floor_one_cleared
                or (
                    self.game_state.party_state.floor_two_cleared
                    and floor_two_replay_requires_available_helper(
                        self.game_state.party_state.active_drifter_ids
                    )
                )
            ):
                self._notice = (
                    "Choose an active pair that leaves D3 or D4 available "
                    "for the Floor II boss."
                )
                return None
            if outing_floor_id == "floor_one" and not self.game_state.party_state.tutorial_complete:
                self._notice = "Your party is not ready to set out."
                return None
            self._expedition_outing_floor_id = outing_floor_id
            self._screen = OverworldScreen.EXPEDITION_SETUP
            self._notice = None
            return None
        if action is OverworldAction.CHOOSE_FLOOR_TWO_HELPER:
            overworld = self.game_state.overworld_state
            party = self.game_state.party_state
            if (
                self._screen is not OverworldScreen.REST
                or overworld.active_route_id != "floor_two"
                or overworld.current_route_node_id != "floor_two_pre_boss_rest"
                or party.phase is not DungeonPhase.OUTING
                or party.floor_two_boss_helper_id is not None
                or not available_floor_two_boss_helper_ids(
                    party.active_drifter_ids
                )
            ):
                self._notice = "Temporary help is not available here."
                return None
            self._screen = OverworldScreen.FLOOR_TWO_HELPER_SELECTION
            self._adventure_text = (
                "At the Rest, D3 and D4 warn that a difficult battle lies ahead "
                "and offer to help. Choose one for the Floor II boss only."
            )
            self._notice = None
            return None
        if action is OverworldAction.RECRUIT_COMPANION:
            if available_recruitment_event(self.game_state) is None:
                self._notice = "Recruitment is not available here."
                return None
            if self._screen is OverworldScreen.REST:
                self._rest_return_screen = OverworldScreen.REST
            self._screen = OverworldScreen.COMPANION_SELECTION
            self._adventure_text = "Choose one Drifter to join your party."
            return None
        if action is OverworldAction.SELECT_PARTY:
            self._screen = OverworldScreen.PARTY_SELECTION
            self._adventure_text = "Choose the two Drifters for your next outing."
            return None
        if action is OverworldAction.READY:
            self._notice = "That option is not available."
            return None
        return _UNHANDLED_ACTION

    def _dispatch_floor_one_action(self, action):
        if action is OverworldAction.START_FLOOR_ONE:
            self._screen = OverworldScreen.FLOOR_ONE_WARNING
            self._adventure_text = self.FLOOR_ONE_WARNING
            return None
        if action is OverworldAction.START_FLOOR_TWO:
            return self._start_floor_two()
        if action is OverworldAction.START_FLOOR_THREE:
            return self._start_floor_three()
        if action is OverworldAction.FINALIZE_FLOOR_TWO_CLEAR:
            if not self.game_state.floor_two_boss_settlement_pending:
                self._notice = "That option is not available."
                return None
            self._finalize_floor_two_boss_clear()
            return None
        if action is OverworldAction.FINALIZE_FLOOR_THREE_CLEAR:
            if not self.game_state.floor_three_boss_settlement_pending:
                self._notice = "That option is not available."
                return None
            self._finalize_floor_three_boss_clear()
            return None
        if action is OverworldAction.SET_OUT:
            return self._start_floor_one()
        if action is OverworldAction.RETURN_WITH_TALISMAN:
            self._return_with_talisman()
            return None
        if action is not OverworldAction.EXTRACT:
            return _UNHANDLED_ACTION
        party_state = self.game_state.party_state
        route_id = self.game_state.overworld_state.active_route_id
        if (
            route_id not in {"floor_one", "floor_two", "floor_three"}
            or self._screen is not OverworldScreen.REST
            or party_state.phase is not DungeonPhase.OUTING
        ):
            self._notice = "Extraction is not available here."
            return None
        if not self._persist_floor_one_rest_fallback(extraction=True):
            return None
        begin_extraction = (
            {
                "floor_one": party_state.begin_floor_one_extraction,
                "floor_two": party_state.begin_floor_two_extraction,
                "floor_three": party_state.begin_floor_three_extraction,
            }[route_id]
        )
        if not begin_extraction(partial=True):
            self._notice = "Extraction is not available here."
            return None
        self._screen = OverworldScreen.EXTRACTION
        floor_number = {"floor_one": 1, "floor_two": 2, "floor_three": 3}[route_id]
        self._adventure_text = (
            f"You extract from Floor {floor_number} early. Half of adjusted XP and gold "
            "are secured, and all run items are kept."
        )
        return None

    def _dispatch_discovery_action(self, action):
        if action not in {
            OverworldAction.SEARCH_SITE,
            OverworldAction.CLAIM_DISCOVERY,
        }:
            return _UNHANDLED_ACTION
        overworld = self.game_state.overworld_state
        party = self.game_state.party_state
        source_id = "ancient_well_floor2_01"
        if (
            self._screen is not OverworldScreen.REST
            or overworld.active_route_id != "floor_two"
            or overworld.current_route_node_id != "floor_two_pre_boss_rest"
            or party.phase is not DungeonPhase.OUTING
        ):
            self._notice = "That discovery is not available here."
            return None
        source = get_permanent_discovery_source(source_id)
        discovered = (
            source_id in self.game_state.world_state.discovered_permanent_discovery_sources
        )
        claimed = source_id in self.game_state.world_state.permanent_discovery_claims
        if action is OverworldAction.SEARCH_SITE:
            already_searched = any(
                event["run_id"] == party.floor_two_run_id
                and event["node_id"] == overworld.current_route_node_id
                and event["kind"] == "discovery_search"
                for event in party.resolved_run_events
            )
            if discovered or claimed or already_searched:
                self._notice = "This site has already been searched in this run."
                return None
            self._discovery_source_id = source_id
            self._discovery_target_id = None
            self._screen = OverworldScreen.DISCOVERY_SEARCHERS
            self._adventure_text = (
                "Choose an active Drifter to search the Ancient Well. "
                "Their Intuition affects the search."
            )
            self._notice = None
            return None
        if claimed or not discovered:
            self._notice = "There is no unclaimed discovery here."
            return None
        self._discovery_source_id = source.source_id
        self._discovery_target_id = None
        self._screen = OverworldScreen.DISCOVERY_TARGETS
        self._adventure_text = (
            "The Ancient Well is revealed. Choose one active Drifter to "
            "receive its permanent +5 Max HP."
        )
        self._notice = None
        return None

    def _select_discovery_searcher(self, view, session_input):
        if (
            view.screen is not OverworldScreen.DISCOVERY_SEARCHERS
            or self._discovery_source_id is None
            or not any(
                choice.drifter_id == session_input.drifter_id
                for choice in view.discovery_choices
            )
        ):
            self._notice = "That searcher is not available."
            return
        source = get_permanent_discovery_source(self._discovery_source_id)
        rng = self._run_event_rng
        if rng is None:
            from app import randomness

            rng = randomness
        try:
            result = RunEventService(
                save_port=self._save_port_instance(),
                rng=rng,
            ).search_discovery(
                self.game_state,
                node_id=self.game_state.overworld_state.current_route_node_id,
                searcher_drifter_id=session_input.drifter_id,
                source=source,
            )
        except (OSError, SavePortError, TypeError, ValueError):
            result = None
        if result is None or result.status is RunEventStatus.SAVE_FAILED:
            self._screen = OverworldScreen.REST
            self._notice = "The search could not be saved. Nothing changed."
            return
        if result.status is RunEventStatus.INVALID_TARGET:
            self._notice = "Only an active Drifter can search this site."
            return
        if result.status is RunEventStatus.INVALID_SOURCE:
            self._screen = OverworldScreen.REST
            self._notice = "This discovery source is unavailable."
            return
        if result.status is RunEventStatus.ALREADY_FOUND:
            self._game_state = result.game_state
            self._screen = OverworldScreen.DISCOVERY_TARGETS
            self._adventure_text = (
                "The Ancient Well is already revealed. Choose one active "
                "Drifter to receive its permanent +5 Max HP."
            )
            return
        if result.status not in {
            RunEventStatus.RESOLVED,
            RunEventStatus.ALREADY_RESOLVED,
        }:
            self._screen = OverworldScreen.REST
            self._notice = "The search could not be completed."
            return
        self._game_state = result.game_state
        if result.found:
            self._screen = OverworldScreen.DISCOVERY_TARGETS
            self._adventure_text = (
                "You found the Ancient Well. Choose one active Drifter to "
                "receive its permanent +5 Max HP."
            )
            self._notice = None
        else:
            self._screen = OverworldScreen.REST
            self._discovery_source_id = None
            self._notice = (
                "The search found nothing. This site cannot be searched "
                "again until a later Floor II run."
            )

    def _select_discovery_target(self, view, session_input):
        if (
            view.screen is not OverworldScreen.DISCOVERY_TARGETS
            or self._discovery_source_id is None
            or not any(
                choice.drifter_id == session_input.drifter_id
                for choice in view.discovery_choices
            )
        ):
            self._notice = "Only an active Drifter can receive this discovery."
            return
        target = self.game_state.member_for_drifter_id(session_input.drifter_id)
        self._discovery_target_id = session_input.drifter_id
        self._screen = OverworldScreen.DISCOVERY_CONFIRMATION
        self._adventure_text = (
            f"Consume the Ancient Well for {target.character.full_display_name}? "
            "This permanently grants +5 Max HP to that Drifter only."
        )
        self._notice = None

    def _confirm_discovery_claim(self):
        if (
            self._screen is not OverworldScreen.DISCOVERY_CONFIRMATION
            or self._discovery_source_id is None
            or self._discovery_target_id is None
        ):
            self._notice = "That discovery claim is not available."
            return
        source = get_permanent_discovery_source(self._discovery_source_id)
        try:
            result = PermanentDiscoveryService(
                (source,),
                save_port=self._save_port_instance(),
            ).consume(
                self.game_state,
                source.source_id,
                self._discovery_target_id,
                confirmed=True,
            )
        except (OSError, SavePortError, TypeError, ValueError):
            result = None
        if result is not None and result.status is DiscoveryClaimStatus.CLAIMED:
            target = result.game_state.member_for_drifter_id(
                self._discovery_target_id
            )
            self._game_state = result.game_state
            self._screen = OverworldScreen.REST
            self._notice = (
                f"Ancient Well claimed by {target.character.full_display_name}: "
                "+5 Max HP."
            )
            self._discovery_source_id = None
            self._discovery_target_id = None
            return
        if result is not None and result.status is DiscoveryClaimStatus.SAVE_FAILED:
            self._notice = "The discovery could not be saved. Nothing changed."
            return
        self._screen = OverworldScreen.REST
        self._discovery_source_id = None
        self._discovery_target_id = None
        self._notice = "That discovery is no longer available."

    def _start_floor_two(self):
        party_state = self.game_state.party_state
        overworld = self.game_state.overworld_state
        if (
            party_state.floor_two_cleared
            and floor_two_replay_requires_available_helper(
                party_state.active_drifter_ids
            )
        ):
            self._notice = (
                "Choose an active pair that leaves D3 or D4 available "
                "for the Floor II boss."
            )
            return None
        party_snapshot = party_state.snapshot()
        overworld_snapshot = overworld.snapshot()
        party_members = self.game_state.active_party_members
        checkpoints = tuple(
            member.create_battle_checkpoint() for member in party_members
        )
        try:
            party_state.start_floor_two_run()
            self._select_party_target(party_members[0])
            overworld.begin_route("floor_two")
            self._screen = OverworldScreen.MAIN
            self._adventure_text = "Your party sets out into Floor 2."
            battle = self._create_active_battle(ui=None)
            if battle is None:
                raise RuntimeError("the first Floor 2 encounter is unavailable")
        except Exception:
            for member, checkpoint in zip(party_members, checkpoints):
                member.restore_battle_checkpoint(checkpoint)
            self.game_state._party_state = PartyState.from_snapshot(
                party_snapshot,
                companions=party_state.companions,
                active_drifter_ids=party_state.active_drifter_ids,
            )
            self.game_state._overworld_state = OverworldState.from_snapshot(
                overworld_snapshot
            )
            self._active_battle = None
            self._active_battle_context = None
            self._screen = OverworldScreen.HUB
            self._adventure_text = None
            self._notice = "The Floor 2 run could not be started."
            return None

        battle_view = battle.current_view()
        if battle.is_complete:
            self._finalize_active_battle()
        return battle_view

    def _start_floor_three(self):
        party_state = self.game_state.party_state
        overworld = self.game_state.overworld_state
        if self.game_state.expedition_state.active_assignment is not None:
            self._notice = "End the current outing before starting Floor 3."
            return None
        if not party_state.floor_two_cleared:
            self._notice = "Clear Floor 2 before starting Floor 3."
            return None
        if len(self.game_state.recruited_members) != 4:
            self._notice = "Recruit D3 and D4 before starting Floor 3."
            return None

        party_snapshot = party_state.snapshot()
        overworld_snapshot = overworld.snapshot()
        party_members = self.game_state.active_party_members
        checkpoints = tuple(
            member.create_battle_checkpoint() for member in party_members
        )
        try:
            party_state.start_floor_three_run()
            self._select_party_target(party_members[0])
            overworld.begin_route("floor_three")
            self._screen = OverworldScreen.MAIN
            self._adventure_text = "Your party sets out into Floor 3."
            battle = self._create_active_battle(ui=None)
            if battle is None:
                raise RuntimeError("the first Floor 3 encounter is unavailable")
        except Exception:
            for member, checkpoint in zip(party_members, checkpoints):
                member.restore_battle_checkpoint(checkpoint)
            self.game_state._party_state = PartyState.from_snapshot(
                party_snapshot,
                companions=party_state.companions,
                active_drifter_ids=party_state.active_drifter_ids,
            )
            self.game_state._overworld_state = OverworldState.from_snapshot(
                overworld_snapshot
            )
            self._active_battle = None
            self._active_battle_context = None
            self._screen = OverworldScreen.HUB
            self._adventure_text = None
            self._notice = "The Floor 3 run could not be started."
            return None

        battle_view = battle.current_view()
        if battle.is_complete:
            self._finalize_active_battle()
        return battle_view

    def _return_to_hub(self):
        if self.game_state.expedition_state.active_assignment is None:
            party_state = self.game_state.party_state
            route_id = self.game_state.overworld_state.active_route_id
            dungeon_extraction = route_id in {
                "floor_one",
                "floor_two",
                "floor_three",
            }
            secured_items = dict(party_state.outing_rewards.items)
            complete_extraction = {
                "floor_one": party_state.complete_extraction,
                "floor_two": party_state.complete_floor_two_extraction,
                "floor_three": party_state.complete_floor_three_extraction,
            }.get(route_id, party_state.complete_extraction)
            if not complete_extraction(self.game_state.active_party_members):
                self._notice = "Those rewards are no longer available."
                return
            self.game_state._bind_equipment_state()
            self._restore_recruited_party()
            if dungeon_extraction:
                self.game_state.overworld_state.return_to_surface_entrance()
            self._screen = OverworldScreen.HUB
            if dungeon_extraction:
                floor_number = {"floor_one": 1, "floor_two": 2, "floor_three": 3}[route_id]
                self._adventure_text = (
                    f"You extract from Floor {floor_number} to the Hub. "
                    "Your run rewards are secured and your "
                    + "recruited Drifters are fully restored. "
                    + _item_reward_text(secured_items, prefix="Items secured:")
                )
                self._persist_floor_one_hub_outcome()
            else:
                self._adventure_text = (
                    "You return to the Floor 1 Hub. The tutorial rewards are secured. "
                    + _item_reward_text(secured_items, prefix="Items secured:")
                )
            return

        candidate = self.game_state.clone()
        party_state = candidate.party_state
        route_id = candidate.overworld_state.active_route_id
        dungeon_extraction = route_id in {"floor_one", "floor_two", "floor_three"}
        secured_items = dict(party_state.outing_rewards.items)
        secured_base_xp = party_state.outing_rewards.experience
        complete_extraction = {
            "floor_one": party_state.complete_extraction,
            "floor_two": party_state.complete_floor_two_extraction,
            "floor_three": party_state.complete_floor_three_extraction,
        }.get(route_id, party_state.complete_extraction)
        if not complete_extraction(
            candidate.active_party_members,
        ):
            self._notice = "Those rewards are no longer available."
            return
        self._restore_members(candidate.recruited_members)
        candidate._bind_equipment_state()
        if dungeon_extraction:
            candidate.overworld_state.return_to_surface_entrance()
            settled = self._persist_outing_terminal_state(
                candidate,
                secured_base_xp=secured_base_xp,
            )
            if settled is None:
                return
            self._game_state = settled
        else:
            self._game_state = candidate
        self._screen = OverworldScreen.HUB
        if dungeon_extraction:
            floor_number = {"floor_one": 1, "floor_two": 2, "floor_three": 3}[route_id]
            self._adventure_text = (
                f"You extract from Floor {floor_number} to the Hub. "
                "Your run rewards are secured and your "
                + "recruited Drifters are fully restored. "
                + _item_reward_text(secured_items, prefix="Items secured:")
            )
        else:
            self._adventure_text = (
                "You return to the Floor 1 Hub. The tutorial rewards are secured. "
                + _item_reward_text(secured_items, prefix="Items secured:")
            )

    def _return_with_talisman(self):
        if self.game_state.expedition_state.active_assignment is None:
            party_state = self.game_state.party_state
            if (
                self.game_state.floor_two_boss_settlement_pending
                or self.game_state.overworld_state.active_route_id
                not in {"floor_one", "floor_two", "floor_three"}
                or self.game_state.floor_three_boss_settlement_pending
                or party_state.phase is not DungeonPhase.OUTING
            ):
                self._notice = "The Return Talisman cannot be used here."
                return
            if not self._persist_floor_one_talisman_fallback():
                return
            if not party_state.return_with_talisman(
                self.game_state.active_party_members,
                recruited_members=self.game_state.recruited_members,
            ):
                self._notice = "The Return Talisman is no longer available."
                return
            self.game_state._bind_equipment_state()
            self._restore_recruited_party()
            self.game_state.overworld_state.return_to_surface_entrance()
            self._screen = OverworldScreen.HUB
            self._adventure_text = (
                "The Return Talisman brings your party back to the Hub. "
                "Adjusted XP is secured; run gold and items are lost."
            )
            self._selected_item_key = None
            self._notice = None
            return

        candidate = self.game_state.clone()
        party_state = candidate.party_state
        if (
            candidate.floor_two_boss_settlement_pending
            or (
                candidate.overworld_state.active_route_id
                not in {"floor_one", "floor_two", "floor_three"}
            )
            or candidate.floor_three_boss_settlement_pending
            or party_state.phase is not DungeonPhase.OUTING
        ):
            self._notice = "The Return Talisman cannot be used here."
            return
        route_id = candidate.overworld_state.active_route_id
        secured_base_xp = {
            "floor_one": party_state._floor_one_payout(partial=False).experience,
            "floor_two": party_state._floor_two_payout(partial=False).experience,
            "floor_three": party_state._floor_three_payout(partial=False).experience,
        }[route_id]
        if not party_state.return_with_talisman(
            candidate.active_party_members,
            recruited_members=candidate.recruited_members,
        ):
            self._notice = "The Return Talisman is no longer available."
            return
        self._restore_members(candidate.recruited_members)
        candidate._bind_equipment_state()
        candidate.overworld_state.return_to_surface_entrance()
        settled = self._persist_outing_terminal_state(
            candidate,
            secured_base_xp=secured_base_xp,
        )
        if settled is None:
            return
        self._game_state = settled
        self._screen = OverworldScreen.HUB
        self._adventure_text = (
            "The Return Talisman brings your party back to the Hub. "
            "Adjusted XP is secured; run gold and items are lost."
        )
        self._selected_item_key = None
        self._notice = None

    def _restore_recruited_party(self):
        self._restore_members(self.game_state.recruited_members)

    def _persist_floor_one_talisman_fallback(self):
        fallback = self.game_state.clone()
        if not fallback.party_state.return_with_talisman(
            fallback.active_party_members,
            recruited_members=fallback.recruited_members,
        ):
            self._notice = "The Return Talisman is no longer available."
            return False
        self._restore_members(fallback.recruited_members)
        fallback._bind_equipment_state()
        fallback.overworld_state.return_to_surface_entrance()
        try:
            result = self._save_port_instance().save(fallback)
        except (SavePortError, TypeError, ValueError):
            result = None
        if result is None or result.status is not SaveLoadStatus.SAVED:
            self._notice = (
                "The Hub return could not be saved. The last committed save "
                "remains available."
            )
            return False
        return True

    @staticmethod
    def _restore_members(members):
        for member in members:
            member.health.heal(member.health.maximum)
            member.mana_resource.restore(member.mana_resource.maximum)

    def _open_respec_confirmation(self, view):
        skills = view.skills
        if (
            view.screen is not OverworldScreen.SKILLS
            or skills is None
            or not skills.respec_available
            or skills.selected_target_id is None
        ):
            self._notice = "Respec is only available for a selected Drifter at the Hub."
            return
        try:
            service = RespecService(save_port=self._save_port_instance())
            preview = service.preview(
                self.game_state,
                skills.selected_target_id,
            )
            player = self.game_state.member_for_drifter_id(
                skills.selected_target_id
            )
        except (OSError, SavePortError, TypeError, ValueError):
            self._notice = "A respec preview is not available for that Drifter."
            return
        self._respec_target_id = skills.selected_target_id
        self._respec_preview = RespecPreviewView(
            drifter_id=preview.drifter_id,
            display_name=player.character.full_display_name,
            first_respec=preview.first_respec,
            revision_parchment_cost=preview.revision_parchment_cost,
            growth_points_refunded=preview.growth_points_refunded,
            current_growth_points=preview.current_growth_points,
            resulting_growth_points=preview.resulting_growth_points,
            removed_stat_points=preview.purchased_stat_points,
            removed_skills=(
                preview.purchased_passive_skill_ids
                + preview.purchased_active_skill_ids
            ),
            resulting_stats=tuple(
                StatRowView(
                    stat_name=name,
                    label=name.capitalize(),
                    value=value,
                )
                for name, value in preview.resulting_stats
            ),
        )
        self._screen = OverworldScreen.RESPEC_CONFIRMATION
        self._adventure_text = (
            f"Review the full respec for {player.character.full_display_name}. "
            "Confirm to refund tracked M3 purchases and remove their effects."
        )
        self._notice = None

    def _confirm_respec(self):
        if (
            self._screen is not OverworldScreen.RESPEC_CONFIRMATION
            or self._respec_target_id is None
        ):
            self._notice = "That respec is not available."
            return
        result = RespecService(
            save_port=self._save_port_instance(),
        ).respec(
            self.game_state,
            self._respec_target_id,
            confirmed=True,
        )
        target_id = self._respec_target_id
        self._respec_preview = None
        self._respec_target_id = None
        self._screen = OverworldScreen.SKILLS
        self._adventure_text = None
        if result.status is RespecStatus.RESPECCED:
            self._game_state = result.game_state
            self._selected_character_target_id = target_id
            self._notice = (
                f"Respec complete. {result.preview.growth_points_refunded} "
                "Growth Points refunded; independent weapon progression preserved."
            )
        elif result.status is RespecStatus.INSUFFICIENT_PARCHMENT:
            self._notice = "A Revision Parchment is required for another respec."
        elif result.status is RespecStatus.SAVE_FAILED:
            self._notice = "The respec could not be saved. Nothing changed."
        else:
            self._notice = "That respec is no longer available. Nothing changed."

    def _dispatch_menu_action(self, action):
        if action is OverworldAction.RESPEC:
            self._open_respec_confirmation(self._build_view())
            return None
        if action is OverworldAction.USE:
            if (
                self._screen is not OverworldScreen.ITEMS
                or self._selected_item_key != "carried-item:healing_potion"
                or self.game_state.party_state.carried_items.get(
                    "healing_potion", 0
                )
                < 1
            ):
                self._notice = "That item cannot be used right now."
                return None
            self._screen = OverworldScreen.HEALING_TARGETS
            self._notice = None
            return None
        if action is OverworldAction.INSPECT:
            if self._screen is OverworldScreen.ITEMS:
                self._screen = OverworldScreen.ITEM_INSPECT
            elif self._screen is OverworldScreen.MAP:
                self._screen = OverworldScreen.MAP_INSPECT
            return None
        if action is OverworldAction.QUIT:
            self._quit_return_screen = self._screen
            self._screen = OverworldScreen.QUIT_CONFIRMATION
            return None
        if action is OverworldAction.SAVE:
            self._save_current_session()
            return None
        if action is OverworldAction.LOAD:
            self._screen = OverworldScreen.LOAD_CONFIRMATION
            self._adventure_text = (
                "Load the saved session and replace the current session?"
            )
            return None
        if action is OverworldAction.CANCEL:
            if self._screen is OverworldScreen.EXPEDITION_CONFIRMATION:
                self._screen = OverworldScreen.EXPEDITION_SETUP
                self._notice = "Cancelled. No energy was spent."
                return None
            if self._screen is OverworldScreen.DISCOVERY_CONFIRMATION:
                self._navigate_back()
                return None
            if self._screen is OverworldScreen.RESPEC_CONFIRMATION:
                self._screen = OverworldScreen.SKILLS
                self._respec_preview = None
                self._respec_target_id = None
                self._adventure_text = None
                self._notice = None
                return None
            if self._screen is OverworldScreen.EQUIPMENT_CONFIRMATION:
                self._confirm_equipment_action(
                    self._build_view(),
                    ChooseEquipmentConfirmation(False),
                )
                return None
            if self._screen is OverworldScreen.LOAD_CONFIRMATION:
                self._screen = OverworldScreen.OPTIONS
                self._adventure_text = None
                self._notice = None
                return None
            self._screen = self._quit_return_screen or OverworldScreen.OPTIONS
            self._quit_return_screen = None
            return None
        if action is OverworldAction.CONFIRM:
            if self._screen is OverworldScreen.EXPEDITION_CONFIRMATION:
                return self._confirm_expedition_launch()
            if self._screen is OverworldScreen.DISCOVERY_CONFIRMATION:
                self._confirm_discovery_claim()
                return None
            if self._screen is OverworldScreen.LOAD_CONFIRMATION:
                self._load_saved_session()
                return None
            if self._screen is OverworldScreen.RESPEC_CONFIRMATION:
                self._confirm_respec()
                return None
            if self._screen is OverworldScreen.EQUIPMENT_CONFIRMATION:
                self._confirm_equipment_action(
                    self._build_view(),
                    ChooseEquipmentConfirmation(True),
                )
                return None
            return OverworldSessionResult.QUIT
        return _UNHANDLED_ACTION

    def _dispatch_rest_action(self, action):
        if action is OverworldAction.REST:
            if self._screen is OverworldScreen.REST:
                self._resolve_current_rest(recover=True)
            else:
                self._open_current_rest()
            return
        if action is OverworldAction.SKIP_REST:
            self._resolve_current_rest(recover=False)
            return
        if action is OverworldAction.MENU:
            if self._screen is OverworldScreen.REST:
                self._screen = OverworldScreen.MAIN
                return
            self._notice = "That option is not available."
            return
        return _UNHANDLED_ACTION

    def _start_floor_one(self):
        party_state = self.game_state.party_state
        overworld = self.game_state.overworld_state
        party_snapshot = party_state.snapshot()
        overworld_snapshot = overworld.snapshot()
        party_members = self.game_state.active_party_members
        checkpoints = tuple(
            member.create_battle_checkpoint() for member in party_members
        )
        try:
            party_state.start_floor_one_run()
            self._select_party_target(party_members[0])
            overworld.begin_route("floor_one")
            self._screen = OverworldScreen.MAIN
            self._adventure_text = "Your party sets out into Floor 1."
            battle = self._create_active_battle(ui=None)
            if battle is None:
                raise RuntimeError("the first Floor 1 encounter is unavailable")
        except Exception:
            for member, checkpoint in zip(party_members, checkpoints):
                member.restore_battle_checkpoint(checkpoint)
            self.game_state._party_state = PartyState.from_snapshot(
                party_snapshot,
                companions=party_state.companions,
                active_drifter_ids=party_state.active_drifter_ids,
            )
            self.game_state._overworld_state = OverworldState.from_snapshot(
                overworld_snapshot
            )
            self._active_battle = None
            self._active_battle_context = None
            self._screen = OverworldScreen.HUB
            self._adventure_text = None
            self._notice = "The Floor 1 run could not be started."
            return None

        battle_view = battle.current_view()
        if battle.is_complete:
            self._finalize_active_battle()
        return battle_view

    def _persist_floor_one_hub_outcome(self):
        try:
            result = self._save_port_instance().save(self.game_state)
        except (SavePortError, TypeError, ValueError):
            result = None
        if result is None or result.status is not SaveLoadStatus.SAVED:
            self._notice = (
                "The Hub return could not be saved. The last committed save "
                "remains available."
            )

    def _persist_outing_terminal_state(self, candidate, *, secured_base_xp):
        from app.game.expeditions import (
            ExpeditionService,
            ExpeditionSettlementStatus,
        )

        now_factory = self._now_factory
        options = {} if now_factory is None else {"now_factory": now_factory}
        port = self._save_port_instance()
        now = now_factory() if now_factory is not None else _now_utc()
        candidate.expedition_state.update_energy(now)
        if candidate.expedition_state.active_assignment is not None:
            result = ExpeditionService(port, **options).settle_outing(
                candidate,
                secured_base_xp=secured_base_xp,
                now=now,
            )
            if result.status in {
                ExpeditionSettlementStatus.SETTLED,
                ExpeditionSettlementStatus.INCOMPLETE,
            }:
                return result.game_state
            if result.status is not ExpeditionSettlementStatus.NO_ASSIGNMENT:
                self._notice = (
                    "The outing return could not be saved. The last committed "
                    "save remains available."
                )
                return None

        try:
            saved = port.save(candidate)
        except (OSError, SavePortError, TypeError, ValueError):
            saved = None
        if saved is None or saved.status is not SaveLoadStatus.SAVED:
            self._notice = (
                "The outing return could not be saved. The last committed "
                "save remains available."
            )
            return None
        return candidate

    def _persist_floor_one_rest_fallback(self, *, extraction=False):
        has_active_assignment = (
            self.game_state.expedition_state.active_assignment is not None
        )
        fallback = self.game_state.clone()
        party_state = fallback.party_state
        party_members = fallback.active_party_members
        route_id = fallback.overworld_state.active_route_id
        secured_base_xp = 0
        if extraction:
            begin_extraction = {
                "floor_one": party_state.begin_floor_one_extraction,
                "floor_two": party_state.begin_floor_two_extraction,
                "floor_three": party_state.begin_floor_three_extraction,
            }[route_id]
            complete_extraction = {
                "floor_one": party_state.complete_extraction,
                "floor_two": party_state.complete_floor_two_extraction,
                "floor_three": party_state.complete_floor_three_extraction,
            }[route_id]
            if not begin_extraction(partial=True):
                self._notice = "The next step could not be saved. You remain at this Rest."
                return False
            secured_base_xp = party_state.outing_rewards.experience
            if not complete_extraction(
                party_members,
            ):
                self._notice = "The next step could not be saved. You remain at this Rest."
                return False
        else:
            fail_run = {
                "floor_one": party_state.fail_floor_one_run,
                "floor_two": party_state.fail_floor_two_run,
                "floor_three": party_state.fail_floor_three_run,
            }[route_id]
            if not fail_run(
                party_members,
                recruited_members=fallback.recruited_members,
            ):
                self._notice = "The next step could not be saved. You remain at this Rest."
                return False

        self._restore_members(fallback.recruited_members)
        fallback._bind_equipment_state()

        fallback.overworld_state.return_to_surface_entrance()
        persisted = self._persist_outing_terminal_state(
            fallback,
            secured_base_xp=secured_base_xp,
        )
        if persisted is None:
            self._notice = "The next step could not be saved. You remain at this Rest."
            return False
        if extraction and has_active_assignment:
            from app.game.expedition_state import ExpeditionState

            self.game_state._expedition_state = ExpeditionState.from_snapshot(
                persisted.expedition_state.snapshot()
            )
        return True

    def _save_current_session(self):
        from app.game.expedition_state import MAX_EXPEDITION_ENERGY

        has_active_assignment = (
            self.game_state.expedition_state.active_assignment is not None
        )
        full_energy_without_anchor = (
            not has_active_assignment
            and self.game_state.expedition_state.energy == MAX_EXPEDITION_ENERGY
            and self.game_state.expedition_state.energy_anchor_utc is None
        )
        candidate = (
            self.game_state
            if full_energy_without_anchor
            else self.game_state.clone()
        )
        now = (
            self._now_factory()
            if self._now_factory is not None
            else _now_utc()
        )
        if not full_energy_without_anchor:
            candidate.expedition_state.update_energy(now)
            candidate.expedition_state.observe_assignment_time(now)
        try:
            result = self._save_port_instance().save(candidate)
        except (SavePortError, TypeError, ValueError):
            self._notice = "The game could not be saved."
        else:
            if result.status is not SaveLoadStatus.SAVED:
                self._notice = result.error or "The game could not be saved."
            else:
                self._game_state = candidate
                self._notice = "Game saved."

    def _load_saved_session(self):
        try:
            result = self._save_port_instance().load()
        except SavePortError:
            result = None
        if result is None or result.status is not SaveLoadStatus.LOADED:
            self._notice = (
                "The saved game could not be loaded."
                if result is None
                else result.error or "The saved game could not be loaded."
            )
            self._screen = OverworldScreen.OPTIONS
            self._adventure_text = None
            return
        self._game_state = result.game_state
        self._screen = self._initial_screen(self.game_state)
        self._selected_item_key = None
        self._quit_return_screen = None
        self._rest_return_screen = None
        self._notice = "Saved session loaded."
        self._adventure_text = None

    def _navigate_back(self):
        if self._screen is OverworldScreen.EXPEDITION_SETUP:
            self._screen = OverworldScreen.EXPEDITIONS
            self._expedition_outing_floor_id = None
            self._expedition_pending = None
            self._adventure_text = None
            self._notice = None
            return
        if self._screen is OverworldScreen.EXPEDITIONS:
            self._screen = OverworldScreen.HUB
            self._adventure_text = None
            self._notice = None
            return
        if self._screen is OverworldScreen.DISCOVERY_CONFIRMATION:
            self._screen = OverworldScreen.DISCOVERY_TARGETS
            self._discovery_target_id = None
            self._adventure_text = (
                "Choose one active Drifter to receive the Ancient Well's "
                "permanent +5 Max HP."
            )
            self._notice = None
            return
        if self._screen in {
            OverworldScreen.DISCOVERY_SEARCHERS,
            OverworldScreen.DISCOVERY_TARGETS,
        }:
            self._screen = OverworldScreen.REST
            self._discovery_source_id = None
            self._discovery_target_id = None
            self._adventure_text = None
            self._notice = None
            return
        if self._screen is OverworldScreen.RESPEC_CONFIRMATION:
            self._screen = OverworldScreen.SKILLS
            self._respec_preview = None
            self._respec_target_id = None
            self._adventure_text = None
            return
        if self._screen is OverworldScreen.EQUIPMENT_CONFIRMATION:
            self._screen = OverworldScreen.EQUIPMENT
            self._equipment_preview = None
            self._equipment_pending_input = None
            self._notice = "Cancelled. Nothing changed."
            return
        if self._screen in {
            OverworldScreen.COMPANION_SELECTION,
            OverworldScreen.PARTY_SELECTION,
            OverworldScreen.PARTY_READY,
        }:
            self._screen = (
                OverworldScreen.REST
                if self._screen is OverworldScreen.COMPANION_SELECTION
                and self._rest_return_screen is OverworldScreen.REST
                else OverworldScreen.HUB
            )
            self._rest_return_screen = None
            self._adventure_text = None
            return
        if self._screen is OverworldScreen.FLOOR_TWO_HELPER_SELECTION:
            self._screen = (
                OverworldScreen.REST
                if self.game_state.overworld_state.current_route_node_id
                == "floor_two_pre_boss_rest"
                else OverworldScreen.MAIN
            )
            self._adventure_text = None
            self._notice = None
            return
        if self._screen in {
            OverworldScreen.SKILLS,
            OverworldScreen.WEAPON,
            OverworldScreen.EQUIPMENT,
        }:
            self._screen = OverworldScreen.CHARACTER
            return
        if self._screen is OverworldScreen.MERCHANT:
            self._screen = OverworldScreen.HUB
            return
        if self._screen is OverworldScreen.ITEM_INSPECT:
            self._screen = OverworldScreen.ITEMS
            return
        if self._screen is OverworldScreen.HEALING_TARGETS:
            self._screen = OverworldScreen.ITEMS
            return
        if self._screen is OverworldScreen.MAP_INSPECT:
            self._screen = OverworldScreen.MAP
            return
        if self._screen in {
            OverworldScreen.CHARACTER,
            OverworldScreen.ITEMS,
        } and self._rest_return_screen is OverworldScreen.REST:
            self._screen = OverworldScreen.REST
            self._rest_return_screen = None
            return
        self._screen = (
            OverworldScreen.HUB
            if self.game_state.party_state.phase
            in {DungeonPhase.HUB, DungeonPhase.PARTY_READY}
            else OverworldScreen.MAIN
        )
        self._selected_item_key = None

    @staticmethod
    def _initial_screen(game_state):
        if (
            game_state.floor_two_boss_settlement_pending
            or game_state.floor_three_boss_settlement_pending
        ):
            return OverworldScreen.MAIN
        if game_state.party_state.phase in {
            DungeonPhase.HUB,
            DungeonPhase.PARTY_READY,
        }:
            return OverworldScreen.HUB
        if game_state.party_state.phase is DungeonPhase.EXTRACTION:
            return OverworldScreen.EXTRACTION
        if game_state.party_state.phase is DungeonPhase.OUTING:
            overworld = game_state.overworld_state
            if overworld.active_route_id in {
                "floor_one",
                "floor_two",
                "floor_three",
            }:
                current_node = get_route_node_spec(
                    overworld.current_route_node_id
                )
                if (
                    current_node.kind is RouteNodeKind.REST
                    and overworld.current_route_node_id
                    not in overworld.resolved_rest_node_ids
                ):
                    return OverworldScreen.REST
                if overworld.current_contextual_route_phase in {
                    ContextualRoutePhase.ENTER_ENCOUNTER,
                    ContextualRoutePhase.RETRY,
                }:
                    return OverworldScreen.MAIN
            return OverworldScreen.OUTING
        return OverworldScreen.MAIN

    def _run_current_encounter(self):
        battle = self._create_active_battle(ui=None)
        if battle is None:
            return
        battle_ui = self._battle_ui_factory()
        view = battle.current_view()
        while True:
            battle_ui.render(view)
            if battle.is_complete:
                self._finalize_active_battle()
                return
            view = battle.submit(battle_ui.read_input(view))

    def _create_active_battle(self, *, ui, tutorial=False):
        if self._active_battle is not None:
            raise RuntimeError("an encounter is already active")
        if tutorial:
            party_state = self.game_state.party_state
            party_members = self.game_state.active_party_members
            if (
                party_state.phase is not DungeonPhase.OUTING
                or party_state.tutorial_complete
                or len(party_members) != 2
            ):
                self._notice = "Your party is not ready for the tutorial encounter."
                return None
            encounter_id = "dungeon_goblin_trio"
            encounter = get_encounter_spec(encounter_id)
            exp_reward, gold_reward = get_encounter_rewards(encounter_id)
            enemies = tuple(
                self._enemy_factory(archetype_id, tier=0)
                for archetype_id in encounter.enemy_archetype_ids
            )
            checkpoints = tuple(
                member.create_battle_checkpoint() for member in party_members
            )
            try:
                self._active_battle = self._battle_factory(
                    party_members[0],
                    enemies,
                    ui=ui,
                    encounter_label="Goblin Trio",
                    party=party_members[1:],
                )
            except Exception:
                for member, checkpoint in zip(party_members, checkpoints):
                    member.restore_battle_checkpoint(checkpoint)
                self._active_battle_context = None
                raise
            self._active_battle_context = (
                None,
                encounter_id,
                exp_reward,
                gold_reward,
                party_members,
                checkpoints,
                None,
            )
            return self._active_battle

        overworld = self.game_state.overworld_state
        current_node_id = overworld.current_route_node_id
        current_node = get_route_node_spec(current_node_id)
        if current_node.encounter_id is None:
            self._notice = "No encounter is available here."
            return None
        encounter = get_encounter_spec(current_node.encounter_id)
        exp_reward, gold_reward = get_encounter_rewards(encounter.encounter_id)

        is_floor_one = overworld.active_route_id == "floor_one"
        is_floor_two = overworld.active_route_id == "floor_two"
        is_floor_three = overworld.active_route_id == "floor_three"
        is_party_run = is_floor_one or is_floor_two or is_floor_three
        party_members = (
            self.game_state.active_party_members
            if is_party_run
            else (self.game_state.player_state,)
        )
        if is_floor_three and current_node.kind is RouteNodeKind.BOSS:
            active_ids = set(self.game_state.party_state.active_drifter_ids)
            party_members += tuple(
                member
                for member in self.game_state.recruited_members
                if member.character.profile.drifter_id not in active_ids
            )
        if is_floor_two and current_node.kind is RouteNodeKind.BOSS:
            helper_id = self.game_state.party_state.floor_two_boss_helper_id
            if helper_id is None:
                self._notice = (
                    "Choose D3 or D4 at the Pre-Boss Rest before entering this boss."
                )
                return None
            helper = create_floor_two_boss_helper(
                helper_id,
                min(member.level_state.current for member in party_members),
            )
            party_members += (helper,)
        checkpoints = tuple(
            member.create_battle_checkpoint() for member in party_members
        )
        if not is_party_run:
            overworld.begin_surface_route()
        tier = 2 if is_floor_three else (1 if is_floor_two else 0)
        enemies = tuple(
            self._enemy_factory(archetype_id, tier=tier)
            for archetype_id in encounter.enemy_archetype_ids
        )
        try:
            battle_kwargs = {
                "ui": ui,
                "encounter_label": current_node.display_label,
            }
            if encounter.cave_in_power is not None:
                battle_kwargs["cave_in_power"] = encounter.cave_in_power
            if is_party_run:
                battle_kwargs["party"] = party_members[1:]
                battle_kwargs["party_state"] = self.game_state.party_state
                battle_kwargs["smoke_escape_allowed"] = (
                    current_node.kind is not RouteNodeKind.BOSS
                )
            self._active_battle = self._battle_factory(
                party_members[0],
                enemies,
                **battle_kwargs,
            )
        except Exception:
            for member, checkpoint in zip(party_members, checkpoints):
                member.restore_battle_checkpoint(checkpoint)
            self._active_battle_context = None
            raise
        self._active_battle_context = (
            current_node_id,
            encounter.encounter_id,
            exp_reward,
            gold_reward,
            party_members,
            checkpoints,
            (
                self.game_state.party_state.carried_items
                if is_floor_two or is_floor_three
                else None
            ),
        )
        return self._active_battle

    def _finalize_active_battle(self, *, winner=None):
        battle = self._active_battle
        context = self._active_battle_context
        if battle is None or context is None:
            raise RuntimeError("there is no active encounter to finalize")
        (
            current_node_id,
            encounter_id,
            exp_reward,
            gold_reward,
            party_members,
            checkpoints,
            carried_supplies_checkpoint,
        ) = context
        overworld = self.game_state.overworld_state
        if winner is None:
            winner = battle.winner
        if winner == "escaped":
            if (
                overworld.active_route_id
                not in {"floor_one", "floor_two", "floor_three"}
                or current_node_id is None
                or not self.game_state.party_state.tutorial_complete
            ):
                raise RuntimeError("Smoke Bomb escape is unavailable in this encounter")
            self._screen = OverworldScreen.MAIN
            self._adventure_text = (
                "The Smoke Bomb ends the encounter. No rewards are earned; "
                "the enemies remain, and your party can prepare and retry."
            )
            self._selected_item_key = None
            self._notice = None
            self._active_battle = None
            self._active_battle_context = None
            return None
        if current_node_id is None and encounter_id == "dungeon_goblin_trio":
            party_state = self.game_state.party_state
            if winner == "player":
                if not self._battle_enemies_are_defeated(battle):
                    raise RuntimeError(
                        "Battle reported victory before every enemy was defeated"
                    )
                if not party_state.begin_extraction(
                    experience=exp_reward,
                    gold=gold_reward,
                    items=dict(get_encounter_item_rewards(encounter_id)),
                ):
                    raise RuntimeError("the tutorial could not enter Extraction")
                self._screen = OverworldScreen.EXTRACTION
                self._adventure_text = (
                    "The Goblin trio is defeated. Return to the hub to secure "
                    "your rewards."
                )
            else:
                if not party_state.reset_failed_tutorial(party_members):
                    raise RuntimeError("the tutorial defeat could not be cleared")
                self._screen = OverworldScreen.PARTY_READY
                self._adventure_text = (
                    "The party was defeated. Your recruited Drifters return fully "
                    "restored; ready again when you are."
                )
            self._selected_item_key = None
            self._notice = None
            self._active_battle = None
            self._active_battle_context = None
            return None

        if overworld.active_route_id == "floor_one":
            self._finalize_floor_one_battle(
                battle,
                winner=winner,
                current_node_id=current_node_id,
                exp_reward=exp_reward,
                gold_reward=gold_reward,
                party_members=party_members,
            )
            return None

        if overworld.active_route_id == "floor_two":
            self._finalize_floor_two_battle(
                battle,
                winner=winner,
                current_node_id=current_node_id,
                encounter_id=encounter_id,
                exp_reward=exp_reward,
                gold_reward=gold_reward,
                party_members=party_members,
                checkpoints=checkpoints,
                carried_supplies_checkpoint=carried_supplies_checkpoint,
            )
            return None

        if overworld.active_route_id == "floor_three":
            self._finalize_floor_three_battle(
                battle,
                winner=winner,
                current_node_id=current_node_id,
                encounter_id=encounter_id,
                exp_reward=exp_reward,
                gold_reward=gold_reward,
                party_members=party_members,
                checkpoints=checkpoints,
                carried_supplies_checkpoint=carried_supplies_checkpoint,
            )
            return None

        if winner == "player":
            if not self._battle_enemies_are_defeated(battle):
                raise RuntimeError(
                    "Battle reported victory before every enemy was defeated"
                )
            next_node_id = get_route_successor_id(current_node_id)
            if next_node_id is None:
                raise RuntimeError(
                    "a completed encounter must have an authored successor"
                )
            next_node = get_route_node_spec(next_node_id)
            next_phase = self._contextual_phase_for_node(next_node.kind)
            if encounter_id in self.game_state.world_state.defeated_encounters:
                raise RuntimeError("encounter has already been defeated")
            player = self.game_state.player_state
            growth_points_before = player.growth_points
            secured_experience = self.game_state.party_state.secured_xp_awards(
                (player,),
                exp_reward,
            )[0]
            levels_gained = player.apply_encounter_reward(
                secured_experience,
                gold_reward,
            )
            growth_points_gained = player.growth_points - growth_points_before
            item_rewards = dict(get_encounter_item_rewards(encounter_id))
            if item_rewards:
                self.game_state.party_state.add_shared_items(item_rewards)
            self.game_state.world_state.mark_encounter_defeated(encounter_id)
            overworld.advance_to(next_node_id, contextual_phase=next_phase)
            if next_node.kind is RouteNodeKind.DUNGEON_ENTRANCE:
                if not self.game_state.party_state.arrive_at_hub(player):
                    raise RuntimeError("the party could not arrive at the dungeon hub")
            self._adventure_text = self._victory_adventure_text(
                current_node_id,
                next_node_id,
                exp_reward=secured_experience,
                gold_reward=gold_reward,
                levels_gained=levels_gained,
                growth_points_gained=growth_points_gained,
                resulting_level=player.level_state.current,
                item_rewards=item_rewards,
            )
            self._screen = (
                OverworldScreen.HUB
                if next_node.kind is RouteNodeKind.DUNGEON_ENTRANCE
                else (
                    OverworldScreen.REST
                    if next_node.kind is RouteNodeKind.REST
                    else OverworldScreen.MAIN
                )
            )
        else:
            for member, checkpoint in zip(party_members, checkpoints):
                member.restore_battle_checkpoint(checkpoint)
            overworld.set_contextual_route_phase(ContextualRoutePhase.RETRY)
            self._adventure_text = self.DEFEAT_ADVENTURE_TEXT
        if winner != "player":
            self._screen = OverworldScreen.MAIN
        self._selected_item_key = None
        self._notice = None
        self._active_battle = None
        self._active_battle_context = None
        return None

    def _finalize_floor_two_battle(
        self,
        battle,
        *,
        winner,
        current_node_id,
        encounter_id,
        exp_reward,
        gold_reward,
        party_members,
        checkpoints,
        carried_supplies_checkpoint,
    ):
        party_state = self.game_state.party_state
        overworld = self.game_state.overworld_state
        current_node = get_route_node_spec(current_node_id)

        if winner != "player":
            if self.game_state.expedition_state.active_assignment is None:
                if not party_state.fail_floor_two_run(
                    self.game_state.active_party_members,
                    recruited_members=self.game_state.recruited_members,
                ):
                    raise RuntimeError("the Floor 2 defeat could not be cleared")
                self.game_state._bind_equipment_state()
                overworld.return_to_surface_entrance()
                self._restore_recruited_party()
                self._persist_floor_one_hub_outcome()
            else:
                candidate = self.game_state.clone()
                if not candidate.party_state.fail_floor_two_run(
                    candidate.active_party_members,
                    recruited_members=candidate.recruited_members,
                ):
                    raise RuntimeError("the Floor 2 defeat could not be cleared")
                candidate._bind_equipment_state()
                candidate.overworld_state.return_to_surface_entrance()
                self._restore_members(candidate.recruited_members)
                settled = self._persist_outing_terminal_state(
                    candidate,
                    secured_base_xp=0,
                )
                if settled is None:
                    return
                self._game_state = settled
            self._screen = OverworldScreen.HUB
            self._adventure_text = (
                "The party was defeated. All unsecured XP, gold, items, and "
                "carried supplies were lost. Your recruited party returns "
                "fully restored to the Hub."
            )
        else:
            if not self._battle_enemies_are_defeated(battle):
                raise RuntimeError(
                    "Battle reported victory before every enemy was defeated"
                )
            next_node_id = get_route_successor_id(current_node_id)
            candidate = self.game_state.clone()
            if current_node.kind is not RouteNodeKind.BOSS:
                if next_node_id is None:
                    raise RuntimeError(
                        "a Floor 2 encounter must have an authored successor"
                    )
                next_node = get_route_node_spec(next_node_id)
                candidate.overworld_state.advance_to(
                    next_node_id,
                    contextual_phase=self._contextual_phase_for_node(
                        next_node.kind
                    ),
                )

            from app.game.run_events import RunEventService, RunEventStatus

            rng = self._run_event_rng
            if rng is None:
                from app import randomness

                rng = randomness
            service = RunEventService(
                save_port=self._save_port_instance(),
                rng=rng,
            )
            result = service.resolve_encounter_rewards(
                candidate,
                node_id=current_node_id,
                experience=exp_reward,
                gold=gold_reward,
                enemy_drop_tables=get_encounter_item_drop_tables(
                    encounter_id,
                    tier=1,
                ),
            )
            if result.status not in {
                RunEventStatus.RESOLVED,
                RunEventStatus.ALREADY_RESOLVED,
            }:
                for member, checkpoint in zip(party_members, checkpoints):
                    member.restore_battle_checkpoint(checkpoint)
                party_state.restore_carried_supplies_checkpoint(
                    carried_supplies_checkpoint
                )
                overworld.set_contextual_route_phase(ContextualRoutePhase.RETRY)
                self._screen = OverworldScreen.MAIN
                self._adventure_text = (
                    f"{current_node.display_label} is defeated, but its "
                    "rewards could not be saved. Retry the encounter."
                )
                self._notice = "The Floor 2 encounter outcome could not be saved."
                self._active_battle = None
                self._active_battle_context = None
                return

            committed = result.game_state
            if current_node.kind is RouteNodeKind.BOSS:
                self._game_state = committed
                self._finalize_floor_two_boss_clear()
            else:
                self._game_state = committed
                next_node = get_route_node_spec(next_node_id)
                self._screen = (
                    OverworldScreen.REST
                    if next_node.kind is RouteNodeKind.REST
                    else OverworldScreen.MAIN
                )
                drop_text = _item_reward_text(
                    dict(result.items),
                    prefix="Items found:",
                )
                self._adventure_text = (
                    f"{current_node.display_label} is defeated. Unsecured "
                    f"rewards: {exp_reward} EXP and {gold_reward} gold. "
                    f"{drop_text} The route continues toward "
                    f"{next_node.display_label}."
                )
                self._notice = None

        self._selected_item_key = None
        self._active_battle = None
        self._active_battle_context = None

    def _finalize_floor_two_boss_clear(self):
        committed = self.game_state
        if not committed.floor_two_boss_settlement_pending:
            self._notice = "That option is not available."
            return False
        settled = committed.clone()
        secured_base_xp = settled.party_state._floor_two_payout(
            partial=False
        ).experience
        if not settled.party_state.complete_floor_two_boss(
            settled.active_party_members,
        ):
            raise RuntimeError("Floor 2 boss rewards could not be secured")
        self._restore_members(settled.recruited_members)
        settled._bind_equipment_state()
        settled.overworld_state.return_to_surface_entrance()
        saved_state = self._persist_outing_terminal_state(
            settled,
            secured_base_xp=secured_base_xp,
        )
        if saved_state is None:
            self._screen = OverworldScreen.MAIN
            self._adventure_text = (
                "The Goblin Lord's victory is saved, but the Hub return could "
                "not be saved. Finalize the Floor 2 clear to retry."
            )
            self._notice = "The Floor 2 clear could not be saved."
            return False

        self._game_state = saved_state
        self._screen = OverworldScreen.HUB
        self._adventure_text = (
            "The Goblin Lord is defeated. Floor 2 is cleared; all run rewards "
            "are secured and your recruited party returns fully restored to the Hub."
        )
        self._notice = None
        return True

    def _finalize_floor_three_battle(
        self,
        battle,
        *,
        winner,
        current_node_id,
        encounter_id,
        exp_reward,
        gold_reward,
        party_members,
        checkpoints,
        carried_supplies_checkpoint,
    ):
        party_state = self.game_state.party_state
        overworld = self.game_state.overworld_state
        current_node = get_route_node_spec(current_node_id)

        if winner != "player":
            if self.game_state.expedition_state.active_assignment is None:
                if not party_state.fail_floor_three_run(
                    self.game_state.active_party_members,
                    recruited_members=self.game_state.recruited_members,
                ):
                    raise RuntimeError("the Floor 3 defeat could not be cleared")
                self.game_state._bind_equipment_state()
                overworld.return_to_surface_entrance()
                self._restore_recruited_party()
                self._persist_floor_one_hub_outcome()
            else:
                candidate = self.game_state.clone()
                if not candidate.party_state.fail_floor_three_run(
                    candidate.active_party_members,
                    recruited_members=candidate.recruited_members,
                ):
                    raise RuntimeError("the Floor 3 defeat could not be cleared")
                candidate._bind_equipment_state()
                candidate.overworld_state.return_to_surface_entrance()
                self._restore_members(candidate.recruited_members)
                settled = self._persist_outing_terminal_state(
                    candidate,
                    secured_base_xp=0,
                )
                if settled is None:
                    return
                self._game_state = settled
            self._screen = OverworldScreen.HUB
            self._adventure_text = (
                "The party was defeated. All unsecured XP, gold, items, and "
                "carried supplies were lost. Your recruited party returns "
                "fully restored to the Hub."
            )
        else:
            if not self._battle_enemies_are_defeated(battle):
                raise RuntimeError(
                    "Battle reported victory before every enemy was defeated"
                )
            next_node_id = get_route_successor_id(current_node_id)
            candidate = self.game_state.clone()
            if current_node.kind is not RouteNodeKind.BOSS:
                if next_node_id is None:
                    raise RuntimeError(
                        "a Floor 3 encounter must have an authored successor"
                    )
                next_node = get_route_node_spec(next_node_id)
                candidate.overworld_state.advance_to(
                    next_node_id,
                    contextual_phase=self._contextual_phase_for_node(
                        next_node.kind
                    ),
                )

            rng = self._run_event_rng
            if rng is None:
                from app import randomness

                rng = randomness
            service = RunEventService(
                save_port=self._save_port_instance(),
                rng=rng,
            )
            result = service.resolve_encounter_rewards(
                candidate,
                node_id=current_node_id,
                experience=exp_reward,
                gold=gold_reward,
                enemy_drop_tables=get_encounter_item_drop_tables(
                    encounter_id,
                    tier=2,
                ),
            )
            if result.status not in {
                RunEventStatus.RESOLVED,
                RunEventStatus.ALREADY_RESOLVED,
            }:
                for member, checkpoint in zip(party_members, checkpoints):
                    member.restore_battle_checkpoint(checkpoint)
                party_state.restore_carried_supplies_checkpoint(
                    carried_supplies_checkpoint
                )
                overworld.set_contextual_route_phase(ContextualRoutePhase.RETRY)
                self._screen = OverworldScreen.MAIN
                self._adventure_text = (
                    f"{current_node.display_label} is defeated, but its "
                    "rewards could not be saved. Retry the encounter."
                )
                self._notice = "The Floor 3 encounter outcome could not be saved."
                self._active_battle = None
                self._active_battle_context = None
                return

            committed = result.game_state
            if current_node.kind is RouteNodeKind.BOSS:
                self._game_state = committed
                self._finalize_floor_three_boss_clear()
            else:
                self._game_state = committed
                next_node = get_route_node_spec(next_node_id)
                self._screen = (
                    OverworldScreen.REST
                    if next_node.kind is RouteNodeKind.REST
                    else OverworldScreen.MAIN
                )
                drop_text = _item_reward_text(
                    dict(result.items),
                    prefix="Items found:",
                )
                self._adventure_text = (
                    f"{current_node.display_label} is defeated. Unsecured "
                    f"rewards: {exp_reward} EXP and {gold_reward} gold. "
                    f"{drop_text} The route continues toward "
                    f"{next_node.display_label}."
                )
                self._notice = None

        self._selected_item_key = None
        self._active_battle = None
        self._active_battle_context = None

    def _finalize_floor_three_boss_clear(self):
        committed = self.game_state
        if not committed.floor_three_boss_settlement_pending:
            self._notice = "That option is not available."
            return False
        settled = committed.clone()
        event = settled.party_state.run_event(
            "floor_three:"
            f"{settled.party_state.floor_three_run_id}:"
            "floor_three_battle_10:encounter_rewards"
        )
        if event is None:
            raise RuntimeError("the Floor 3 boss reward evidence is missing")
        boss_experience = event["result"]["experience"]
        party_state = settled.party_state
        pre_boss_experience = party_state.outing_rewards.experience - boss_experience
        replay_rate = party_state.floor_three_outing_xp_multiplier_percent
        secured_base_xp = (
            pre_boss_experience * replay_rate // (100 * 2) * 2
            + boss_experience * replay_rate // (100 * 4) * 4
        )
        if not settled.party_state.complete_floor_three_boss(
            settled.recruited_members,
            boss_experience=boss_experience,
        ):
            raise RuntimeError("Floor 3 boss rewards could not be secured")
        self._restore_members(settled.recruited_members)
        settled._bind_equipment_state()
        settled.overworld_state.return_to_surface_entrance()
        saved_state = self._persist_outing_terminal_state(
            settled,
            secured_base_xp=secured_base_xp,
        )
        if saved_state is None:
            self._screen = OverworldScreen.MAIN
            self._adventure_text = (
                "The Floor 3 boss victory is saved, but the Hub return could "
                "not be saved. Finalize the Floor 3 clear to retry."
            )
            self._notice = "The Floor 3 clear could not be saved."
            return False

        self._game_state = saved_state
        self._screen = OverworldScreen.HUB
        self._adventure_text = (
            "The Floor 3 boss is defeated. Floor 3 is cleared; rewards are "
            "secured and all four recruited Drifters return fully restored to the Hub."
        )
        self._notice = None
        return True

    def _finalize_floor_one_battle(
        self,
        battle,
        *,
        winner,
        current_node_id,
        exp_reward,
        gold_reward,
        party_members,
    ):
        party_state = self.game_state.party_state
        overworld = self.game_state.overworld_state
        current_node = get_route_node_spec(current_node_id)

        if winner == "player":
            if not self._battle_enemies_are_defeated(battle):
                raise RuntimeError(
                    "Battle reported victory before every enemy was defeated"
                )
            if current_node.kind is RouteNodeKind.BOSS:
                boss_items = dict(
                    get_encounter_item_rewards(current_node.encounter_id)
                )
                if self.game_state.expedition_state.active_assignment is None:
                    party_state.add_floor_one_rewards(
                        experience=exp_reward,
                        gold=gold_reward,
                        items=boss_items,
                    )
                    secured_items = dict(party_state.outing_rewards.items)
                    if not party_state.complete_floor_one_boss(party_members):
                        raise RuntimeError(
                            "Floor 1 boss rewards could not be secured"
                        )
                    self._restore_recruited_party()
                    overworld.return_to_surface_entrance()
                    self._screen = OverworldScreen.HUB
                    self._adventure_text = (
                        "The Goblin Lord is defeated. Floor 1 is cleared; all run "
                        + "rewards are secured and your recruited party returns to the Hub. "
                        + _item_reward_text(secured_items, prefix="Items secured:")
                    )
                    self._persist_floor_one_hub_outcome()
                    self._selected_item_key = None
                    self._active_battle = None
                    self._active_battle_context = None
                    return

                candidate = self.game_state.clone()
                candidate_party = candidate.party_state
                candidate_party.add_floor_one_rewards(
                    experience=exp_reward,
                    gold=gold_reward,
                    items=boss_items,
                )
                secured_items = dict(candidate_party.outing_rewards.items)
                secured_base_xp = candidate_party._floor_one_payout(
                    partial=False
                ).experience
                if not candidate_party.complete_floor_one_boss(
                    candidate.active_party_members,
                ):
                    raise RuntimeError("Floor 1 boss rewards could not be secured")
                self._restore_members(candidate.recruited_members)
                candidate._bind_equipment_state()
                candidate.overworld_state.return_to_surface_entrance()
                saved_state = self._persist_outing_terminal_state(
                    candidate,
                    secured_base_xp=secured_base_xp,
                )
                if saved_state is None:
                    return
                self._game_state = saved_state
                self._screen = OverworldScreen.HUB
                self._adventure_text = (
                    "The Goblin Lord is defeated. Floor 1 is cleared; all run "
                    + "rewards are secured and your recruited party returns to the Hub. "
                    + _item_reward_text(secured_items, prefix="Items secured:")
                )
            else:
                item_rewards = dict(
                    get_encounter_item_rewards(current_node.encounter_id)
                )
                party_state.add_floor_one_rewards(
                    experience=exp_reward,
                    gold=gold_reward,
                    items=item_rewards,
                )
                next_node_id = get_route_successor_id(current_node_id)
                if next_node_id is None:
                    raise RuntimeError(
                        "a Floor 1 encounter must have an authored successor"
                    )
                next_node = get_route_node_spec(next_node_id)
                overworld.advance_to(
                    next_node_id,
                    contextual_phase=self._contextual_phase_for_node(
                        next_node.kind
                    ),
                )
                self._screen = (
                    OverworldScreen.REST
                    if next_node.kind is RouteNodeKind.REST
                    else OverworldScreen.MAIN
                )
                self._adventure_text = (
                    f"{current_node.display_label} is defeated. Unsecured "
                    f"rewards: {exp_reward} EXP and {gold_reward} gold. "
                    f"{_item_reward_text(item_rewards)} "
                    f"The route continues toward {next_node.display_label}."
                )
        else:
            if self.game_state.expedition_state.active_assignment is None:
                if not party_state.fail_floor_one_run(
                    party_members,
                    recruited_members=self.game_state.recruited_members,
                ):
                    raise RuntimeError("the Floor 1 defeat could not be cleared")
                self.game_state._bind_equipment_state()
                overworld.return_to_surface_entrance()
                self._restore_recruited_party()
                self._persist_floor_one_hub_outcome()
            else:
                candidate = self.game_state.clone()
                if not candidate.party_state.fail_floor_one_run(
                    candidate.active_party_members,
                    recruited_members=candidate.recruited_members,
                ):
                    raise RuntimeError("the Floor 1 defeat could not be cleared")
                candidate._bind_equipment_state()
                candidate.overworld_state.return_to_surface_entrance()
                self._restore_members(candidate.recruited_members)
                saved_state = self._persist_outing_terminal_state(
                    candidate,
                    secured_base_xp=0,
                )
                if saved_state is None:
                    return
                self._game_state = saved_state
            self._screen = OverworldScreen.HUB
            self._adventure_text = (
                "The party was defeated. All unsecured XP, gold, and items "
                "were lost. Your recruited party returns fully restored to the Hub."
            )

        self._selected_item_key = None
        self._active_battle = None
        self._active_battle_context = None

    def _open_current_rest(self):
        overworld = self.game_state.overworld_state
        node_id = overworld.current_route_node_id
        if (
            get_route_node_spec(node_id).kind is not RouteNodeKind.REST
            or node_id in overworld.resolved_rest_node_ids
        ):
            self._notice = "That Rest is not available."
            return
        self._screen = OverworldScreen.REST

    def _resolve_current_rest(self, *, recover):
        overworld = self.game_state.overworld_state
        current_node_id = overworld.current_route_node_id
        current_node = get_route_node_spec(current_node_id)
        if (
            current_node.kind is not RouteNodeKind.REST
            or current_node_id in overworld.resolved_rest_node_ids
        ):
            self._notice = "That Rest is not available."
            return
        if (
            not recover
            and overworld.active_route_id == "floor_two"
            and current_node_id == "floor_two_pre_boss_rest"
            and self.game_state.party_state.floor_two_boss_helper_id is None
        ):
            self._notice = (
                "Choose D3 or D4 at the Pre-Boss Rest before continuing."
            )
            return

        next_node_id = get_route_successor_id(current_node_id)
        if next_node_id is None:
            self._notice = "That Rest has no available successor."
            return
        next_node = get_route_node_spec(next_node_id)
        next_phase = self._contextual_phase_for_node(next_node.kind)

        if recover:
            members = (self.game_state.player_state,)
            if overworld.active_route_id in {
                "floor_one",
                "floor_two",
                "floor_three",
            }:
                members = self.game_state.active_party_members
            for member in members:
                member.health.heal(member.health.maximum)
                member.mana_resource.restore(member.mana_resource.maximum)

            if overworld.active_route_id in {
                "floor_one",
                "floor_two",
                "floor_three",
            }:
                self.game_state.party_state.secure_outing_equipment()
                self._screen = OverworldScreen.REST
                self._notice = None
                self._adventure_text = (
                    f"You recover at {current_node.display_label}. HP and Mana "
                    "are fully restored. You may continue or extract."
                )
                return

        if (
            overworld.active_route_id
            in {"floor_one", "floor_two", "floor_three"}
            and not self._persist_floor_one_rest_fallback()
        ):
            return

        overworld.record_resolved_rest_node(current_node_id)
        overworld.advance_to(next_node_id, contextual_phase=next_phase)
        self._screen = OverworldScreen.MAIN
        self._selected_item_key = None
        self._notice = None
        if recover:
            self._adventure_text = (
                f"You rest at {current_node.display_label}. HP and Mana are "
                f"fully restored. The route continues toward "
                f"{next_node.display_label}."
            )
        else:
            self._adventure_text = (
                f"You continue from {current_node.display_label} without "
                f"resting. The route continues toward "
                f"{next_node.display_label}."
            )

    @staticmethod
    def _battle_enemies_are_defeated(battle):
        enemies = getattr(battle, "enemies", None)
        if enemies is None:
            raise RuntimeError(
                "a winning Battle must expose its canonical enemy tuple"
            )
        if not enemies:
            raise RuntimeError(
                "a winning Battle must expose at least one enemy"
            )
        return all(not enemy.is_alive() for enemy in enemies)

    @staticmethod
    def _contextual_phase_for_node(node_kind):
        if node_kind in {RouteNodeKind.COMBAT, RouteNodeKind.BOSS}:
            return ContextualRoutePhase.ENTER_ENCOUNTER
        return ContextualRoutePhase.NONE

    @staticmethod
    def _victory_adventure_text(
        completed_node_id,
        next_node_id,
        *,
        exp_reward,
        gold_reward,
        levels_gained,
        growth_points_gained,
        resulting_level,
        item_rewards=(),
    ):
        completed = get_route_node_spec(completed_node_id).display_label
        next_node = get_route_node_spec(next_node_id).display_label
        lines = [
            f"{completed} is defeated.",
            f"Rewards: {exp_reward} EXP and {gold_reward} gold.",
        ]
        if item_rewards:
            lines.append(_item_reward_text(item_rewards))
        if levels_gained == 1:
            point_label = (
                "Growth Point"
                if growth_points_gained == 1
                else "Growth Points"
            )
            lines.append(
                f"Level up! Reached Level {resulting_level} and gained "
                f"{growth_points_gained} {point_label}."
            )
        elif levels_gained > 1:
            point_label = (
                "Growth Point"
                if growth_points_gained == 1
                else "Growth Points"
            )
            lines.append(
                f"Level up! Gained {levels_gained} levels, reached "
                f"Level {resulting_level}, and gained "
                f"{growth_points_gained} {point_label}."
            )
        lines.append(f"The route continues toward {next_node}.")
        return " ".join(lines)

    @staticmethod
    def _unavailable_action_message(action):
        if action in {
            OverworldAction.CRAFT,
            OverworldAction.USE,
            OverworldAction.SAVE,
            OverworldAction.LOAD,
        }:
            return "That feature is not yet available."
        return "That option is not available."


def _display_item_name(item_id):
    return " ".join(
        word[:1].upper() + word[1:]
        for word in item_id.split("_")
    )


def _item_reward_text(items, *, prefix="Items:"):
    pairs = items.items() if isinstance(items, dict) else items
    readable = tuple(
        f"{quantity} {_display_item_name(item_id)}"
        for item_id, quantity in sorted(pairs)
        if quantity
    )
    if not readable:
        return f"{prefix} none."
    return f"{prefix} {', '.join(readable)}."
