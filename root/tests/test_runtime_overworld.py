import pytest

from app.combat.battle import Battle
from app.combat.result import MoveResult
from app.content.catalog import create_drifter, create_enemy_state
from app.game.game_state import GameState
from app.game.overworld_session import (
    OverworldSession,
    OverworldSessionResult,
)
from app.game.overworld_state import ContextualRoutePhase
from app.game.save_repository import SaveRepository
from app.player.player_state import PlayerState
from app.presentation.battle_models import ActionIntent, InteractionPhase
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.ui.battle_ui import ChooseAction, ChooseMove, ChooseTarget
from app.ui.overworld_ui import ChooseOverworldAction


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


class PlayerOneHitResolver(OneHitResolver):
    def resolve_move(
        self,
        actor,
        target,
        move_name,
        *,
        combat_state=None,
        character_run_state=None,
    ):
        if not hasattr(actor, "character"):
            return MoveResult(
                accepted=True,
                hit=False,
                move_name=move_name,
                resource_spent=0,
                damage=0,
                healing=0,
                statuses_applied=(),
                reason=None,
            )
        return super().resolve_move(
            actor,
            target,
            move_name,
            combat_state=combat_state,
            character_run_state=character_run_state,
        )


class DefeatResolver:
    def resolve_move(
        self,
        actor,
        target,
        move_name,
        *,
        combat_state=None,
        character_run_state=None,
    ):
        del move_name, combat_state, character_run_state
        if hasattr(actor, "character"):
            damage = 0
        else:
            damage = target.health.current
            target.health.take_damage(damage)
        return MoveResult(
            accepted=True,
            hit=damage > 0,
            move_name="scripted",
            resource_spent=0,
            damage=damage,
            healing=0,
            statuses_applied=(),
            reason=None,
        )


class StepBattleFactory:
    def __init__(self, resolvers):
        self.resolvers = list(resolvers)
        self.battles = []

    def __call__(self, player_state, enemies, *, ui, encounter_label):
        resolver = self.resolvers[min(len(self.battles), len(self.resolvers) - 1)]
        factory = self

        class NoRunBattle(Battle):
            def run(self):
                raise AssertionError("step-driven sessions must not call Battle.run()")

        battle = NoRunBattle(
            player_state,
            enemies,
            ui=ui,
            resolver=resolver,
            rng=AlwaysOneRng(),
            encounter_label=encounter_label,
        )
        factory.battles.append(battle)
        return battle


class EnemyFactory:
    def __init__(self):
        self.enemies = []

    def __call__(self, archetype_id, *, tier):
        enemy = create_enemy_state(archetype_id, tier=tier)
        self.enemies.append(enemy)
        return enemy


def make_session(tmp_path, *, resolvers):
    game = GameState(PlayerState(create_drifter("branoc")))
    battle_factory = StepBattleFactory(resolvers)
    enemy_factory = EnemyFactory()
    session = OverworldSession(
        game,
        ui=None,
        battle_factory=battle_factory,
        enemy_factory=enemy_factory,
        battle_ui_factory=None,
        save_repository=SaveRepository(tmp_path / "save.json"),
    )
    return session, battle_factory, enemy_factory


def finish_current_battle(session):
    battle_view = session.submit(ChooseAction(ActionIntent.ATTACK))
    assert battle_view.interaction_phase is InteractionPhase.REGULAR_MOVES
    return session.submit(
        ChooseMove(battle_view.move_options[0].selection_key)
    )


def test_step_driven_session_owns_active_battle_and_finalizes_victory(tmp_path):
    session, battle_factory, enemy_factory = make_session(
        tmp_path,
        resolvers=(OneHitResolver(),),
    )

    main_view = session.current_view()
    assert main_view.screen is OverworldScreen.MAIN
    assert main_view.contextual_route_option.action is OverworldAction.ENTER_ENCOUNTER

    first_battle_view = session.submit(
        ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER)
    )
    battle = battle_factory.battles[0]
    assert first_battle_view.interaction_phase is InteractionPhase.ACTIONS
    assert session.active_battle is battle
    assert battle.enemies == (enemy_factory.enemies[0],)

    final_view = finish_current_battle(session)
    assert final_view.interaction_phase is InteractionPhase.COMPLETE
    assert final_view.action_options == ()
    assert session.active_battle is None
    assert session.current_view().screen is OverworldScreen.MAIN
    assert session.game_state.world_state.defeated_encounters == (
        "surface_goblin_solo",
    )
    assert session.game_state.overworld_state.current_route_node_id == (
        "surface_goblin_pair"
    )


def test_step_driven_session_rejects_cross_mode_input_without_mutation(tmp_path):
    session, _battle_factory, _enemy_factory = make_session(
        tmp_path,
        resolvers=(OneHitResolver(),),
    )
    session.submit(ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER))
    before = session.game_state.snapshot()
    before_battle = session.active_battle

    returned = session.submit(ChooseOverworldAction(OverworldAction.OPTIONS))

    assert returned == before_battle.current_view()
    assert session.active_battle is before_battle
    assert session.game_state.snapshot() == before


def test_step_driven_session_preserves_multi_enemy_targeting_and_order(tmp_path):
    session, battle_factory, enemy_factory = make_session(
        tmp_path,
        resolvers=(PlayerOneHitResolver(),),
    )
    game = session.game_state
    game.overworld_state.advance_to(
        "surface_goblin_pair",
        contextual_phase=ContextualRoutePhase.ENTER_ENCOUNTER,
    )

    battle_view = session.submit(
        ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER)
    )
    assert battle_view.interaction_phase is InteractionPhase.ACTIONS
    battle_view = session.submit(ChooseAction(ActionIntent.ATTACK))
    battle_view = session.submit(
        ChooseMove(battle_view.move_options[0].selection_key)
    )
    assert battle_view.interaction_phase is InteractionPhase.TARGETS
    assert tuple(option.target_id for option in battle_view.target_options) == (
        "enemy_1",
        "enemy_2",
    )

    battle_view = session.submit(ChooseTarget("enemy_2"))
    battle = battle_factory.battles[0]
    assert battle_view.interaction_phase is InteractionPhase.ACTIONS
    assert battle.enemies[0].is_alive()
    assert not battle.enemies[1].is_alive()
    assert enemy_factory.enemies == list(battle.enemies)

    battle_view = session.submit(ChooseAction(ActionIntent.ATTACK))
    battle_view = session.submit(
        ChooseMove(battle_view.move_options[0].selection_key)
    )
    assert battle_view.interaction_phase is InteractionPhase.COMPLETE
    assert session.active_battle is None
    assert game.world_state.defeated_encounters == ("surface_goblin_pair",)


def test_step_driven_defeat_restores_checkpoint_and_retry_uses_fresh_battle(
    tmp_path,
):
    session, battle_factory, enemy_factory = make_session(
        tmp_path,
        resolvers=(DefeatResolver(), OneHitResolver()),
    )
    player = session.game_state.player_state
    player.health.take_damage(9)
    before = player.snapshot()

    session.submit(ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER))
    defeat_view = finish_current_battle(session)

    assert defeat_view.interaction_phase is InteractionPhase.COMPLETE
    assert session.active_battle is None
    assert player.snapshot() == before
    assert session.game_state.world_state.defeated_encounters == ()
    assert session.game_state.overworld_state.current_route_node_id == (
        "surface_goblin_solo"
    )
    retry_view = session.current_view()
    assert retry_view.contextual_route_option.action is OverworldAction.RETRY

    session.submit(ChooseOverworldAction(OverworldAction.RETRY))
    assert len(battle_factory.battles) == 2
    assert battle_factory.battles[1] is not battle_factory.battles[0]
    assert enemy_factory.enemies[1] is not enemy_factory.enemies[0]
    final_view = finish_current_battle(session)
    assert final_view.interaction_phase is InteractionPhase.COMPLETE
    assert session.game_state.world_state.defeated_encounters == (
        "surface_goblin_solo",
    )


def test_step_driven_rest_resolution_remains_session_owned(tmp_path):
    session, _battle_factory, _enemy_factory = make_session(
        tmp_path,
        resolvers=(OneHitResolver(),),
    )
    game = session.game_state
    game.overworld_state.advance_to(
        "surface_goblin_pair",
        contextual_phase=ContextualRoutePhase.NONE,
    )
    game.overworld_state.advance_to(
        "surface_warrior_solo",
        contextual_phase=ContextualRoutePhase.ENTER_ENCOUNTER,
    )
    game.overworld_state.advance_to("surface_rest_after_warrior_solo")

    main_view = session.current_view()
    assert main_view.contextual_route_option.action is OverworldAction.REST
    rest_view = session.submit(
        ChooseOverworldAction(OverworldAction.REST)
    )
    assert rest_view.screen is OverworldScreen.REST
    assert rest_view.contextual_route_option.action is OverworldAction.SKIP_REST

    after = session.submit(
        ChooseOverworldAction(OverworldAction.SKIP_REST)
    )
    assert after.screen is OverworldScreen.MAIN
    assert game.overworld_state.resolved_rest_node_ids == (
        "surface_rest_after_warrior_solo",
    )
    assert game.overworld_state.current_route_node_id == "surface_warrior_pair"


def test_step_driven_quit_returns_session_result(tmp_path):
    session, _battle_factory, _enemy_factory = make_session(
        tmp_path,
        resolvers=(OneHitResolver(),),
    )
    session.submit(ChooseOverworldAction(OverworldAction.OPTIONS))
    session.submit(ChooseOverworldAction(OverworldAction.QUIT))

    assert session.submit(ChooseOverworldAction(OverworldAction.CONFIRM)) is (
        OverworldSessionResult.QUIT
    )


def test_compatibility_run_requires_an_overworld_ui(tmp_path):
    session, _battle_factory, _enemy_factory = make_session(
        tmp_path,
        resolvers=(OneHitResolver(),),
    )

    with pytest.raises(RuntimeError, match="overworld UI"):
        session.run()
