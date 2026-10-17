"""Overworld session orchestration around the existing Battle boundary."""

from enum import StrEnum
from typing import TypeAlias, Union

from app.content.catalog import (
    get_encounter_spec,
    get_encounter_rewards,
    get_drifter_spec,
    get_route_node_spec,
    get_route_successor_id,
)
from app.content.route_spec import RouteNodeKind
from app.game.game_state import GameState
from app.game.overworld_state import ContextualRoutePhase
from app.game.party_state import DungeonPhase
from app.persistence.save_port_contract import (
    SaveLoadStatus,
    SavePortError,
    is_save_port,
)
from app.iteration import first_or_none
from app.player.player_state import PlayerState
from app.presentation.overworld_models import (
    OverworldAction,
    OverworldAvailabilityReason,
    OverworldScreen,
    OverworldView,
)
from app.presentation.battle_models import BattleView, InteractionPhase
from app.presentation.overworld_presenter import OverworldPresenter
from app.ui.overworld_ui import (
    ChooseCompanion,
    ChooseOverworldAction,
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
    ConfirmInventoryUse,
    GoBack,
)


class OverworldSession:
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
        if presenter is None:
            presenter = OverworldPresenter()
        if not isinstance(presenter, OverworldPresenter):
            raise TypeError("presenter must be an OverworldPresenter")
        if save_port is not None and not is_save_port(save_port):
            raise TypeError("save_port must satisfy SavePort")

        self._game_state = game_state
        self._ui = ui
        self._battle_factory = battle_factory
        self._enemy_factory = enemy_factory
        self._battle_ui_factory = battle_ui_factory
        self._presenter = presenter
        self._save_port = save_port
        self._screen = self._initial_screen(game_state)
        self._selected_item_key = None
        self._adventure_text = None
        self._notice = None
        self._quit_return_screen = None
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
            return view
        return self._build_view()

    def submit(self, session_input: SessionInput):
        if self._active_battle is not None:
            battle = self._active_battle
            current_view = battle.current_view()
            if battle.is_complete:
                result = self._finalize_active_battle()
                if result is not None:
                    return result
                return current_view
            if not isinstance(session_input, _BATTLE_INPUT_TYPES):
                return current_view
            view = battle.submit(session_input)
            if battle.is_complete:
                result = self._finalize_active_battle()
                if result is not None:
                    return result
            return view

        view = self._build_view()
        if isinstance(session_input, _BATTLE_INPUT_TYPES):
            return view
        if isinstance(session_input, ChoosePermanentStatIncrease):
            self._increase_permanent_stat(view, session_input)
            if self._stale_enabled_stat_input(view, session_input):
                self._notice = "That stat is not available."
            return self._build_view()
        if isinstance(session_input, ChooseOverworldItem):
            self._select_item(view, session_input)
            return self._build_view()
        if isinstance(session_input, ChooseCompanion):
            self._select_companion(view, session_input)
            return self._build_view()
        if not isinstance(session_input, ChooseOverworldAction):
            self._notice = "That option is not available."
            return self._build_view()
        if not self._action_is_offered(
            view,
            session_input.action,
        ) and not self._stale_load_was_offered(session_input.action):
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
            return battle_view
        if session_input.action is OverworldAction.READY:
            party_state = self.game_state.party_state
            party_members = (self.game_state.player_state,) + party_state.companions
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
            return battle_view
        result = self._dispatch(session_input.action)
        if result is OverworldSessionResult.QUIT:
            return result
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
        return self._presenter.build(
            self.game_state,
            screen=self._screen,
            selected_item_key=self._selected_item_key,
            adventure_text=self._adventure_text,
            notice=self._notice,
            save_available=self._save_available(),
            load_available=self._load_available(),
        )

    def _save_available(self):
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

    def _select_companion(self, view, session_input):
        if view.screen is not OverworldScreen.COMPANION_SELECTION:
            self._notice = "That Drifter is not available."
            return
        if self.game_state.party_state.phase is not DungeonPhase.HUB:
            self._screen = OverworldScreen.HUB
            self._adventure_text = None
            self._notice = "That Drifter is not available."
            return
        choice = first_or_none(
            choice
            for choice in view.companion_choices
            if choice.drifter_id == session_input.drifter_id
        )
        if choice is None:
            self._notice = "That Drifter is not available."
            return
        if not choice.enabled:
            self._notice = "You need 65 shared gold to recruit a Drifter."
            return
        try:
            profile = get_drifter_spec(choice.drifter_id)
            companion = PlayerState(profile.create_character())
            recruited = self.game_state.party_state.recruit_companion(
                self.game_state.player_state,
                companion,
            )
        except (TypeError, ValueError):
            self._notice = "That Drifter is not available."
            return
        if not recruited:
            self._notice = "You need 65 shared gold to recruit a Drifter."
            return
        self._screen = OverworldScreen.PARTY_READY
        lead_name = self.game_state.player_state.character.full_display_name
        self._adventure_text = (
            f"{profile.display_name} joins {lead_name}. "
            "Your party is ready to set out."
        )
        self._notice = None

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
            new_value = self.game_state.player_state.increase_permanent_stat(
                row.stat_name
            )
        except (TypeError, ValueError):
            self._notice = "That stat is not available."
            return

        self._notice = (
            f"{row.label} increased to {new_value}. "
            f"Growth Points remaining: "
            f"{self.game_state.player_state.growth_points}."
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
        navigation = {
            OverworldAction.CHARACTER: OverworldScreen.CHARACTER,
            OverworldAction.ITEMS: OverworldScreen.ITEMS,
            OverworldAction.MAP: OverworldScreen.MAP,
            OverworldAction.OPTIONS: OverworldScreen.OPTIONS,
            OverworldAction.SKILLS: OverworldScreen.SKILLS,
            OverworldAction.WEAPON: OverworldScreen.WEAPON,
            OverworldAction.EQUIPMENT: OverworldScreen.EQUIPMENT,
        }
        if action in navigation:
            self._screen = navigation[action]
            if self._screen is not OverworldScreen.ITEMS:
                self._selected_item_key = None
            return None
        if action is OverworldAction.BACK:
            self._navigate_back()
            return None
        if action is OverworldAction.RECRUIT_COMPANION:
            self._screen = OverworldScreen.COMPANION_SELECTION
            self._adventure_text = "Choose one Drifter to join your party."
            return None
        if action is OverworldAction.READY:
            self._notice = "That option is not available."
            return None
        if action is OverworldAction.RETURN_TO_HUB:
            if not self.game_state.party_state.complete_extraction(
                (self.game_state.player_state,)
                + self.game_state.party_state.companions
            ):
                self._notice = "Those rewards are no longer available."
                return None
            self._screen = OverworldScreen.HUB
            self._adventure_text = (
                "You return to the Floor 1 Hub. The tutorial rewards are secured."
            )
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
            if self._screen is OverworldScreen.LOAD_CONFIRMATION:
                self._screen = OverworldScreen.OPTIONS
                self._adventure_text = None
                self._notice = None
                return None
            self._screen = self._quit_return_screen or OverworldScreen.OPTIONS
            self._quit_return_screen = None
            return None
        if action is OverworldAction.CONFIRM:
            if self._screen is OverworldScreen.LOAD_CONFIRMATION:
                self._load_saved_session()
                return None
            return OverworldSessionResult.QUIT
        if action is OverworldAction.REST:
            if self._screen is OverworldScreen.REST:
                self._resolve_current_rest(recover=True)
            else:
                self._open_current_rest()
            return None
        if action is OverworldAction.SKIP_REST:
            self._resolve_current_rest(recover=False)
            return None
        if action is OverworldAction.MENU:
            if self._screen is OverworldScreen.REST:
                self._screen = OverworldScreen.MAIN
                return None
            self._notice = "That option is not available."
            return None
        if action in {OverworldAction.ENTER_ENCOUNTER, OverworldAction.RETRY}:
            self._run_current_encounter()
            return None
        self._notice = self._unavailable_action_message(action)
        return None

    def _save_current_session(self):
        try:
            result = self._save_port_instance().save(self.game_state)
        except (SavePortError, TypeError, ValueError):
            self._notice = "The game could not be saved."
        else:
            if result.status is not SaveLoadStatus.SAVED:
                self._notice = result.error or "The game could not be saved."
            else:
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
        self._notice = "Saved session loaded."
        self._adventure_text = None

    def _navigate_back(self):
        if self._screen in {
            OverworldScreen.COMPANION_SELECTION,
            OverworldScreen.PARTY_READY,
        }:
            self._screen = OverworldScreen.HUB
            self._adventure_text = None
            return
        if self._screen in {
            OverworldScreen.SKILLS,
            OverworldScreen.WEAPON,
            OverworldScreen.EQUIPMENT,
        }:
            self._screen = OverworldScreen.CHARACTER
            return
        if self._screen is OverworldScreen.ITEM_INSPECT:
            self._screen = OverworldScreen.ITEMS
            return
        if self._screen is OverworldScreen.MAP_INSPECT:
            self._screen = OverworldScreen.MAP
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
        if game_state.party_state.phase in {
            DungeonPhase.HUB,
            DungeonPhase.PARTY_READY,
        }:
            return OverworldScreen.HUB
        if game_state.party_state.phase is DungeonPhase.EXTRACTION:
            return OverworldScreen.EXTRACTION
        if game_state.party_state.phase is DungeonPhase.OUTING:
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
            if (
                party_state.phase is not DungeonPhase.OUTING
                or party_state.tutorial_complete
                or len(party_state.companions) != 1
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
            self._active_battle_context = (
                None,
                encounter_id,
                exp_reward,
                gold_reward,
                None,
            )
            try:
                self._active_battle = self._battle_factory(
                    self.game_state.player_state,
                    enemies,
                    ui=ui,
                    encounter_label="Goblin Trio",
                    party=party_state.companions,
                )
            except Exception:
                self._active_battle_context = None
                raise
            return self._active_battle

        overworld = self.game_state.overworld_state
        current_node_id = overworld.current_route_node_id
        current_node = get_route_node_spec(current_node_id)
        if current_node.encounter_id is None:
            self._notice = "No encounter is available here."
            return None
        encounter = get_encounter_spec(current_node.encounter_id)
        exp_reward, gold_reward = get_encounter_rewards(encounter.encounter_id)

        checkpoint = self.game_state.player_state.create_battle_checkpoint()
        overworld.begin_surface_route()
        enemies = tuple(
            self._enemy_factory(archetype_id, tier=0)
            for archetype_id in encounter.enemy_archetype_ids
        )
        self._active_battle_context = (
            current_node_id,
            encounter.encounter_id,
            exp_reward,
            gold_reward,
            checkpoint,
        )
        try:
            self._active_battle = self._battle_factory(
                self.game_state.player_state,
                enemies,
                ui=ui,
                encounter_label=current_node.display_label,
            )
        except Exception:
            self._active_battle_context = None
            raise
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
            checkpoint,
        ) = context
        overworld = self.game_state.overworld_state
        if winner is None:
            winner = battle.winner
        if encounter_id == "dungeon_goblin_trio":
            selection_requested = False
            party_state = self.game_state.party_state
            if winner == "player":
                if not self._battle_enemies_are_defeated(battle):
                    raise RuntimeError(
                        "Battle reported victory before every enemy was defeated"
                    )
                if not party_state.begin_extraction(
                    experience=exp_reward,
                    gold=gold_reward,
                ):
                    raise RuntimeError("the tutorial could not enter Extraction")
                self._screen = OverworldScreen.EXTRACTION
                self._adventure_text = (
                    "The Goblin trio is defeated. Return to the hub to secure "
                    "your rewards."
                )
            else:
                if not party_state.reset_failed_tutorial():
                    raise RuntimeError("the tutorial defeat could not be cleared")
                self._screen = OverworldScreen.MAIN
                self._adventure_text = None
                selection_requested = True
            self._selected_item_key = None
            self._notice = None
            self._active_battle = None
            self._active_battle_context = None
            return (
                OverworldSessionResult.SELECT_DRIFTER
                if selection_requested
                else None
            )

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
            levels_gained = player.apply_encounter_reward(
                exp_reward,
                gold_reward,
            )
            growth_points_gained = player.growth_points - growth_points_before
            self.game_state.world_state.mark_encounter_defeated(encounter_id)
            overworld.advance_to(next_node_id, contextual_phase=next_phase)
            if next_node.kind is RouteNodeKind.DUNGEON_ENTRANCE:
                if not self.game_state.party_state.arrive_at_hub(player):
                    raise RuntimeError("the party could not arrive at the dungeon hub")
            self._adventure_text = self._victory_adventure_text(
                current_node_id,
                next_node_id,
                exp_reward=exp_reward,
                gold_reward=gold_reward,
                levels_gained=levels_gained,
                growth_points_gained=growth_points_gained,
                resulting_level=player.level_state.current,
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
            self.game_state.player_state.restore_battle_checkpoint(checkpoint)
            overworld.set_contextual_route_phase(ContextualRoutePhase.RETRY)
            self._adventure_text = self.DEFEAT_ADVENTURE_TEXT
        if winner != "player":
            self._screen = OverworldScreen.MAIN
        self._selected_item_key = None
        self._notice = None
        self._active_battle = None
        self._active_battle_context = None
        return None

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

        next_node_id = get_route_successor_id(current_node_id)
        if next_node_id is None:
            self._notice = "That Rest has no available successor."
            return
        next_node = get_route_node_spec(next_node_id)
        next_phase = self._contextual_phase_for_node(next_node.kind)

        if recover:
            player = self.game_state.player_state
            player.health.heal(player.health.maximum)
            player.mana_resource.restore(player.mana_resource.maximum)

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
    ):
        completed = get_route_node_spec(completed_node_id).display_label
        next_node = get_route_node_spec(next_node_id).display_label
        lines = [
            f"{completed} is defeated.",
            f"Rewards: {exp_reward} EXP and {gold_reward} gold.",
        ]
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
