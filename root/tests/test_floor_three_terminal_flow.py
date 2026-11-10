from app.combat.battle import Battle
from app.combat.result import MoveResult
from app.content.catalog import create_enemy_state, get_drifter_spec
from app.game.overworld_session import OverworldSession, OverworldSessionResult
from app.player.player_state import PlayerState
from app.presentation.battle_models import InteractionPhase
from app.presentation.overworld_models import OverworldScreen
from app.ui.terminal_battle_ui import TerminalBattleUI
from app.ui.terminal_overworld_ui import TerminalOverworldUI
from tests.combat_test_support import AlwaysOneRng, OneHitResolver
from tests.game_test_support import three_member_hub_game
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


class ScriptedFloorThreeOverworldUI(TerminalOverworldUI):
    def __init__(self, game_state_provider):
        self._game_state_provider = game_state_provider
        self.current_view = None
        self.views = []
        self._recovered_rest_nodes = set()
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
        if view.screen is OverworldScreen.HUB:
            return "o" if self.game_state.party_state.floor_three_cleared else "3"
        if view.screen is OverworldScreen.REST:
            node_id = self.game_state.overworld_state.current_route_node_id
            if node_id not in self._recovered_rest_nodes:
                self._recovered_rest_nodes.add(node_id)
                return "r"
            return "n"
        if view.screen is OverworldScreen.MAIN:
            return "e"
        if view.screen is OverworldScreen.OPTIONS:
            return "q"
        if view.screen is OverworldScreen.QUIT_CONFIRMATION:
            return "y"
        raise AssertionError(f"unexpected terminal screen: {view.screen}")


class ScriptedFloorThreeBattleUI(TerminalBattleUI):
    def __init__(self, encounters):
        self.current_view = None
        self.encounters = encounters
        self._recorded_encounter = False
        super().__init__(
            input_func=self._choose_input,
            output_func=lambda _message: None,
            width_provider=lambda: 100,
            interactive=False,
        )

    def render(self, view):
        self.current_view = view
        if not self._recorded_encounter:
            self.encounters.append(
                (
                    view.encounter_label,
                    tuple(member.target_id for member in view.party_members),
                )
            )
            self._recorded_encounter = True
        super().render(view)

    def _choose_input(self, _prompt):
        if self.current_view.interaction_phase is InteractionPhase.ACTIONS:
            return "a"
        return "1"


def floor_three_ready_game():
    game = three_member_hub_game()
    zhaivra = PlayerState(get_drifter_spec("zhaivra").create_character())
    assert game.party_state.recruit_companion(game.player_state, zhaivra, cost=0)
    party = game.party_state
    assert party.start_floor_one_run() == 100
    assert party.complete_floor_one_boss(game.active_party_members)
    assert party.start_floor_two_run() == 100
    assert party.complete_floor_two_boss(game.active_party_members)
    return game


def test_terminal_completes_floor_three_with_pair_then_four_member_boss(tmp_path):
    game = floor_three_ready_game()
    rng = AlwaysOneRng()
    resolver = PlayerOnlyOneHitResolver()
    encounters = []
    session_ref = {}
    overworld_ui = ScriptedFloorThreeOverworldUI(
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
        battle_ui_factory=lambda: ScriptedFloorThreeBattleUI(encounters),
        save_port=make_test_save_port(tmp_path / "terminal-floor-three.json"),
        run_event_rng=rng,
    )
    session_ref["session"] = session

    assert session.run() is OverworldSessionResult.QUIT

    assert len(encounters) == 10
    assert encounters[0][0] == "Goblin Pair"
    assert len(encounters[0][1]) == 2
    assert encounters[-1][0] == "Goblin Lord"
    assert encounters[-1][1] == (
        "drifter_branoc",
        "drifter_azhvielle",
        "drifter_joruun",
        "drifter_zhaivra",
    )
    assert all(len(participants) == 2 for _, participants in encounters[:-1])
    assert session.game_state.party_state.floor_three_cleared
    assert session.game_state.party_state.phase.value == "hub"
    assert OverworldScreen.REST in tuple(view.screen for view in overworld_ui.views)
