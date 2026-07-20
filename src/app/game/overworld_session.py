"""Overworld session orchestration around the existing Battle boundary."""

from enum import StrEnum

from app.game.encounter_manifest import (
    create_route_encounter_enemies,
    route_manifest_node,
)
from app.game.game_state import GameState
from app.game.overworld_route import RouteNodeKind, route_node
from app.game.overworld_state import ContextualRoutePhase
from app.presentation.overworld_models import (
    OverworldAction,
    OverworldAvailabilityReason,
    OverworldScreen,
)
from app.presentation.overworld_presenter import OverworldPresenter
from app.ui.overworld_ui import (
    ChooseOverworldAction,
    ChooseOverworldItem,
    ChoosePermanentStatIncrease,
    OverworldUI,
)


class OverworldSessionResult(StrEnum):
    QUIT = "quit"


class OverworldSession:
    DEFEAT_ADVENTURE_TEXT = (
        "The encounter drove you back. Your footing is restored; retry when ready."
    )

    def __init__(
        self,
        game_state,
        *,
        ui,
        battle_factory,
        enemy_factory,
        battle_ui_factory,
        presenter=None,
    ):
        if not isinstance(game_state, GameState):
            raise TypeError("game_state must be a GameState")
        if not isinstance(ui, OverworldUI):
            raise TypeError("ui must satisfy OverworldUI")
        for name, value in (
            ("battle_factory", battle_factory),
            ("enemy_factory", enemy_factory),
            ("battle_ui_factory", battle_ui_factory),
        ):
            if not callable(value):
                raise TypeError(f"{name} must be callable")
        if presenter is None:
            presenter = OverworldPresenter()
        if not isinstance(presenter, OverworldPresenter):
            raise TypeError("presenter must be an OverworldPresenter")

        self._game_state = game_state
        self._ui = ui
        self._battle_factory = battle_factory
        self._enemy_factory = enemy_factory
        self._battle_ui_factory = battle_ui_factory
        self._presenter = presenter
        self._screen = OverworldScreen.MAIN
        self._selected_item_key = None
        self._adventure_text = None
        self._notice = None
        self._quit_return_screen = None

    @property
    def game_state(self):
        return self._game_state

    def run(self):
        while True:
            view = self._build_view()
            self._ui.render(view)
            overworld_input = self._ui.read_input(view)
            if isinstance(overworld_input, ChoosePermanentStatIncrease):
                self._increase_permanent_stat(view, overworld_input)
                continue
            if isinstance(overworld_input, ChooseOverworldItem):
                self._select_item(view, overworld_input)
                continue
            if not isinstance(overworld_input, ChooseOverworldAction):
                self._notice = "That option is not available."
                continue
            if not self._action_is_offered(view, overworld_input.action):
                self._notice = "That option is not available."
                continue
            if self._dispatch(overworld_input.action) is OverworldSessionResult.QUIT:
                return OverworldSessionResult.QUIT

    def _build_view(self):
        return self._presenter.build(
            self.game_state,
            screen=self._screen,
            selected_item_key=self._selected_item_key,
            adventure_text=self._adventure_text,
            notice=self._notice,
        )

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

    def _increase_permanent_stat(self, view, overworld_input):
        if view.screen is not OverworldScreen.SKILLS or view.skills is None:
            self._notice = "That stat is not available."
            return

        row = next(
            (
                row
                for row in view.skills.stats
                if row.stat_name == overworld_input.stat_name
            ),
            None,
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
        if action is OverworldAction.CANCEL:
            self._screen = self._quit_return_screen or OverworldScreen.OPTIONS
            self._quit_return_screen = None
            return None
        if action is OverworldAction.CONFIRM:
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

    def _navigate_back(self):
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
        self._screen = OverworldScreen.MAIN
        self._selected_item_key = None

    def _run_current_encounter(self):
        overworld = self.game_state.overworld_state
        current_node_id = overworld.current_route_node_id
        manifest_node = route_manifest_node(current_node_id)
        if manifest_node.encounter is None:
            self._notice = "No encounter is available here."
            return

        checkpoint = self.game_state.player_state.create_battle_checkpoint()
        overworld.begin_surface_route()
        enemies = create_route_encounter_enemies(
            current_node_id,
            enemy_factory=self._enemy_factory,
        )
        battle = self._battle_factory(
            self.game_state.player_state,
            enemies,
            ui=self._battle_ui_factory(),
            encounter_label=route_node(current_node_id).display_label,
        )
        winner = battle.run()
        if winner == "player":
            if not self._battle_enemies_are_defeated(battle):
                raise RuntimeError(
                    "Battle reported victory before every enemy was defeated"
                )
            next_node_id = manifest_node.next_node_id
            if next_node_id is None:
                raise RuntimeError(
                    "a completed encounter must have an authored successor"
                )
            next_node = route_node(next_node_id)
            next_phase = self._contextual_phase_for_node(next_node.kind)
            encounter_id = manifest_node.encounter.encounter_id
            if encounter_id in self.game_state.world_state.defeated_encounters:
                raise RuntimeError("encounter has already been defeated")
            player = self.game_state.player_state
            growth_points_before = player.growth_points
            levels_gained = player.apply_encounter_reward(
                manifest_node.encounter.exp_reward,
                manifest_node.encounter.gold_reward,
            )
            growth_points_gained = player.growth_points - growth_points_before
            self.game_state.world_state.mark_encounter_defeated(encounter_id)
            overworld.advance_to(next_node_id, contextual_phase=next_phase)
            self._adventure_text = self._victory_adventure_text(
                current_node_id,
                next_node_id,
                exp_reward=manifest_node.encounter.exp_reward,
                gold_reward=manifest_node.encounter.gold_reward,
                levels_gained=levels_gained,
                growth_points_gained=growth_points_gained,
                resulting_level=player.level_state.current,
            )
            self._screen = (
                OverworldScreen.REST
                if next_node.kind is RouteNodeKind.REST
                else OverworldScreen.MAIN
            )
        else:
            self.game_state.player_state.restore_battle_checkpoint(checkpoint)
            overworld.set_contextual_route_phase(ContextualRoutePhase.RETRY)
            self._adventure_text = self.DEFEAT_ADVENTURE_TEXT
        if winner != "player":
            self._screen = OverworldScreen.MAIN
        self._selected_item_key = None
        self._notice = None

    def _open_current_rest(self):
        overworld = self.game_state.overworld_state
        node_id = overworld.current_route_node_id
        if (
            route_node(node_id).kind is not RouteNodeKind.REST
            or node_id in overworld.resolved_rest_node_ids
        ):
            self._notice = "That Rest is not available."
            return
        self._screen = OverworldScreen.REST

    def _resolve_current_rest(self, *, recover):
        overworld = self.game_state.overworld_state
        current_node_id = overworld.current_route_node_id
        current_node = route_node(current_node_id)
        if (
            current_node.kind is not RouteNodeKind.REST
            or current_node_id in overworld.resolved_rest_node_ids
        ):
            self._notice = "That Rest is not available."
            return

        manifest_node = route_manifest_node(current_node_id)
        next_node_id = manifest_node.next_node_id
        if next_node_id is None:
            self._notice = "That Rest has no available successor."
            return
        next_node = route_node(next_node_id)
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
        completed = route_node(completed_node_id).display_label
        next_node = route_node(next_node_id).display_label
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
