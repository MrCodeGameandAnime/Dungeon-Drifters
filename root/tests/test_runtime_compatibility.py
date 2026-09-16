from app.combat.battle import Battle
from app.combat.result import MoveResult
from app.content.catalog import create_enemy_state
from app.game.game_state import GameState
from app.game.new_game import create_new_game
from app.game.overworld_session import OverworldSession, OverworldSessionResult
from app.game.save_repository import SaveRepository
from app.ui.terminal_battle_ui import TerminalBattleUI
from app.ui.terminal_overworld_ui import TerminalOverworldUI


class AlwaysOneRng:
    def randint(self, _start, _end):
        return 1

    def choice(self, options):
        return tuple(options)[0]


class OneHitResolver:
    def resolve_move(
        self,
        actor,
        target,
        move_name,
        *,
        combat_state=None,
        character_run_state=None,
    ):
        del actor, combat_state, character_run_state
        damage = target.health.current
        target.health.take_damage(damage)
        return MoveResult(
            accepted=True,
            hit=True,
            move_name=move_name,
            resource_spent=0,
            damage=damage,
            healing=0,
            statuses_applied=(),
            reason=None,
        )


class NoRunBattle(Battle):
    def run(self):
        self.run_called = True
        raise AssertionError("OverworldSession.run must use the step boundary")


def test_terminal_session_driver_uses_semantic_battle_steps_once(tmp_path):
    game = create_new_game("branoc")
    overworld_inputs = iter(("e", "o", "q", "y"))
    battle_inputs = iter(("a", "crestgrave reaping"))
    output = []
    battles = []

    def battle_factory(player_state, enemies, *, ui, encounter_label):
        battle = NoRunBattle(
            player_state,
            enemies,
            ui=ui,
            resolver=OneHitResolver(),
            rng=AlwaysOneRng(),
            encounter_label=encounter_label,
        )
        battles.append(battle)
        return battle

    session = OverworldSession(
        game,
        ui=TerminalOverworldUI(
            input_func=lambda _prompt: next(overworld_inputs),
            output_func=output.append,
            width_provider=lambda: 80,
            interactive=False,
        ),
        battle_factory=battle_factory,
        enemy_factory=create_enemy_state,
        battle_ui_factory=lambda: TerminalBattleUI(
            input_func=lambda _prompt: next(battle_inputs),
            output_func=output.append,
            width_provider=lambda: 80,
            interactive=False,
        ),
        save_repository=SaveRepository(tmp_path / "save.json"),
    )

    assert session.run() is OverworldSessionResult.QUIT
    assert len(battles) == 1
    assert not getattr(battles[0], "run_called", False)
    assert session.active_battle is None
    assert game.world_state.defeated_encounters == ("surface_goblin_solo",)
    assert game.overworld_state.current_route_node_id == "surface_goblin_pair"
    assert game.player_state.exp_state.current == 40
    assert game.player_state.gold == 3
    assert any("Rewards: 40 EXP and 3 gold." in line for line in output)
