from app.combat.battle import Battle
from app.combat.result import MoveResult
from app.content.catalog import create_enemy_state
from app.game.overworld_session import OverworldSession, OverworldSessionResult
from app.presentation.battle_models import InteractionPhase
from app.presentation.overworld_models import OverworldScreen
from app.ui.terminal_battle_ui import TerminalBattleUI
from app.ui.terminal_overworld_ui import TerminalOverworldUI
from tests.combat_test_support import AlwaysOneRng, OneHitResolver
from tests.game_test_support import completed_hub_game
from tests.persistence_test_support import make_test_save_port


class PlayerOnlyOneHitResolver:
    def __init__(self):
        self._player_resolver = OneHitResolver()

    def resolve_move(
        self,
        actor,
        target,
        move_name,
        *,
        combat_state=None,
        character_run_state=None,
    ):
        if hasattr(actor, "character"):
            return self._player_resolver.resolve_move(
                actor,
                target,
                move_name,
                combat_state=combat_state,
                character_run_state=character_run_state,
            )
        return MoveResult(
            accepted=True,
            hit=True,
            move_name=move_name,
            resource_spent=0,
            damage=0,
            healing=0,
            statuses_applied=(),
            reason=None,
        )


class ScriptedTerminalOverworldUI(TerminalOverworldUI):
    def __init__(self, game_state_provider):
        self._game_state_provider = game_state_provider
        self.current_view = None
        self.views = []
        self._helper_input_sent = False
        self._search_input_sent = False
        self._input_count = 0
        super().__init__(
            input_func=self._choose_input,
            output_func=lambda _message: None,
            width_provider=lambda: 100,
            interactive=False,
        )

    @property
    def game_state(self):
        return self._game_state_provider()

    def render(self, view):
        self.current_view = view
        self.views.append(view)
        super().render(view)

    def _choose_input(self, _prompt):
        view = self.current_view
        self._input_count += 1
        if self._input_count > 40:
            raise AssertionError("terminal route requested too many overworld inputs")
        if view.screen is OverworldScreen.HUB:
            if self.game_state.party_state.floor_two_cleared:
                return "o"
            return "2"
        if view.screen is OverworldScreen.REST:
            node_id = self.game_state.overworld_state.current_route_node_id
            if (
                node_id == "floor_two_pre_boss_rest"
                and not self._search_input_sent
            ):
                self._search_input_sent = True
                return "s"
            if (
                node_id == "floor_two_pre_boss_rest"
                and not self._helper_input_sent
            ):
                self._helper_input_sent = True
                return "b"
            return "n"
        if view.screen is OverworldScreen.COMPANION_SELECTION:
            index = next(
                index
                for index, choice in enumerate(view.companion_choices, start=1)
                if choice.drifter_id == "zhaivra"
            )
            return str(index)
        if view.screen is OverworldScreen.FLOOR_TWO_HELPER_SELECTION:
            index = next(
                index
                for index, choice in enumerate(
                    view.temporary_helper_choices,
                    start=1,
                )
                if choice.drifter_id == "zhaivra"
            )
            return str(index)
        if view.screen is OverworldScreen.DISCOVERY_SEARCHERS:
            return "1"
        if view.screen is OverworldScreen.DISCOVERY_TARGETS:
            return "2"
        if view.screen is OverworldScreen.DISCOVERY_CONFIRMATION:
            return "y"
        if view.screen is OverworldScreen.MAIN:
            return "e"
        if view.screen is OverworldScreen.OPTIONS:
            return "q"
        if view.screen is OverworldScreen.QUIT_CONFIRMATION:
            return "y"
        raise AssertionError(f"unexpected terminal screen: {view.screen}")


class ScriptedTerminalBattleUI(TerminalBattleUI):
    def __init__(self, encounters):
        self.current_view = None
        self.encounters = encounters
        self._recorded_encounter = False
        self._input_count = 0
        super().__init__(
            input_func=self._choose_input,
            output_func=lambda _message: None,
            width_provider=lambda: 100,
            interactive=False,
        )

    def render(self, view):
        self.current_view = view
        if not self._recorded_encounter:
            self.encounters.append(view.encounter_label)
            self._recorded_encounter = True
        super().render(view)

    def _choose_input(self, _prompt):
        self._input_count += 1
        if self._input_count > 100:
            raise AssertionError(
                "battle input loop: "
                f"{self.current_view.interaction_phase} at "
                f"{self.current_view.encounter_label}"
            )
        if self.current_view.interaction_phase is InteractionPhase.ACTIONS:
            return "a"
        return "1"


def test_terminal_can_start_and_complete_floor_two_with_temporary_helper_and_discovery(
    tmp_path,
):
    game = completed_hub_game()
    assert game.party_state.start_floor_one_run() == 100
    assert game.party_state.complete_floor_one_boss(game.active_party_members)
    game.party_state.add_shared_gold(55)

    rng = AlwaysOneRng()
    resolver = PlayerOnlyOneHitResolver()
    encounters = []
    session_ref = {}
    overworld_ui = ScriptedTerminalOverworldUI(
        lambda: session_ref["session"].game_state
    )
    session = OverworldSession(
        game,
        ui=overworld_ui,
        battle_factory=lambda player, enemies, **kwargs: Battle(
            player,
            enemies,
            rng=rng,
            resolver=resolver,
            **kwargs,
        ),
        enemy_factory=create_enemy_state,
        battle_ui_factory=lambda: ScriptedTerminalBattleUI(encounters),
        save_port=make_test_save_port(tmp_path / "terminal-floor-two.json"),
        run_event_rng=rng,
    )
    session_ref["session"] = session

    assert session.run() is OverworldSessionResult.QUIT

    assert len(encounters) == 10
    assert encounters[-1] == "Goblin Lord"
    assert session.game_state.party_state.floor_two_cleared
    assert tuple(
        member.character.profile.drifter_id
        for member in session.game_state.recruited_members
    ) == ("branoc", "azhvielle")
    assert session.game_state.world_state.permanent_discovery_claims == (
        "ancient_well_floor2_01",
    )
    assert OverworldScreen.FLOOR_TWO_HELPER_SELECTION in tuple(
        view.screen for view in overworld_ui.views
    )
    assert OverworldScreen.COMPANION_SELECTION not in tuple(
        view.screen for view in overworld_ui.views
    )
    assert OverworldScreen.DISCOVERY_CONFIRMATION in tuple(
        view.screen for view in overworld_ui.views
    )
