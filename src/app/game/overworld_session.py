"""Overworld session orchestration around the existing Battle boundary."""

from enum import StrEnum

from app.game.game_state import GameState
from app.game.overworld_route import FIRST_SURFACE_NODE_ID, SECOND_SURFACE_NODE_ID
from app.game.overworld_state import ContextualRoutePhase
from app.presentation.overworld_models import (
    OverworldAction,
    OverworldScreen,
)
from app.presentation.overworld_presenter import OverworldPresenter
from app.ui.overworld_ui import (
    ChooseOverworldAction,
    ChooseOverworldItem,
    OverworldUI,
)


class OverworldSessionResult(StrEnum):
    QUIT = "quit"


class OverworldSession:
    INITIAL_ADVENTURE_TEXT = (
        "A Goblin blocks the road through Ketlyv. The surface route begins here."
    )
    VICTORY_ADVENTURE_TEXT = (
        "The first Goblin falls. Two more wait farther along the road."
    )
    DEFEAT_ADVENTURE_TEXT = (
        "The Goblin drove you back. Your footing is restored; retry when ready."
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
        self._adventure_text = self.INITIAL_ADVENTURE_TEXT
        self._notice = None

    @property
    def game_state(self):
        return self._game_state

    def run(self):
        while True:
            view = self._build_view()
            self._ui.render(view)
            overworld_input = self._ui.read_input(view)
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
            self._screen = OverworldScreen.ITEM_INSPECT
            return None
        if action is OverworldAction.QUIT:
            self._screen = OverworldScreen.QUIT_CONFIRMATION
            return None
        if action is OverworldAction.CANCEL:
            self._screen = OverworldScreen.OPTIONS
            return None
        if action is OverworldAction.CONFIRM:
            return OverworldSessionResult.QUIT
        if action in {OverworldAction.ENTER_ENCOUNTER, OverworldAction.RETRY}:
            self._run_first_encounter()
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
        self._screen = OverworldScreen.MAIN
        self._selected_item_key = None

    def _run_first_encounter(self):
        overworld = self.game_state.overworld_state
        if overworld.current_route_node_id != FIRST_SURFACE_NODE_ID:
            self._notice = "No encounter is available here."
            return
        checkpoint = self.game_state.player_state.create_battle_checkpoint()
        overworld.begin_surface_route()
        enemy = self._enemy_factory("goblin", tier=0)
        battle = self._battle_factory(
            self.game_state.player_state,
            enemy,
            ui=self._battle_ui_factory(),
        )
        winner = battle.run()
        if winner == "player":
            self.game_state.world_state.mark_encounter_defeated(
                FIRST_SURFACE_NODE_ID
            )
            overworld.advance_to(
                SECOND_SURFACE_NODE_ID,
                contextual_phase=ContextualRoutePhase.NONE,
            )
            self._adventure_text = self.VICTORY_ADVENTURE_TEXT
        else:
            self.game_state.player_state.restore_battle_checkpoint(checkpoint)
            overworld.set_contextual_route_phase(ContextualRoutePhase.RETRY)
            self._adventure_text = self.DEFEAT_ADVENTURE_TEXT
        self._screen = OverworldScreen.MAIN
        self._selected_item_key = None
        self._notice = None

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
