from app.combat.battle import Battle
from app.combat.result import MoveResult
from app.content.catalog import create_enemy_state
from app.game.overworld_session import OverworldSession
from app.game.new_game import create_new_game
from app.game.save_repository import SaveRepository
from app.presentation.battle_models import InteractionPhase
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.ui.battle_ui import ChooseAction, ChooseMove, ChooseTarget
from app.ui.overworld_ui import ChooseOverworldAction


EXPECTED_ENCOUNTERS = (
    "surface_goblin_solo",
    "surface_goblin_pair",
    "surface_warrior_solo",
    "surface_warrior_pair",
    "surface_shaman_solo",
    "surface_shaman_pair",
    "surface_elite_patrol",
    "surface_goblin_lord",
)

EXPECTED_RESTS = (
    "surface_rest_after_warrior_solo",
    "surface_rest_after_shaman_pair",
    "surface_rest_before_goblin_lord",
)

EXPECTED_COMPOSITIONS = (
    ("goblin",),
    ("goblin", "goblin"),
    ("goblin_warrior",),
    ("goblin_warrior", "goblin_warrior"),
    ("goblin_shaman",),
    ("goblin_shaman", "goblin_shaman"),
    ("goblin_elite", "goblin"),
    ("goblin_lord", "goblin", "goblin_warrior"),
)


class DeterministicRng:
    def randint(self, _start, _end):
        return 1

    def choice(self, options):
        return tuple(options)[0]


class DeterministicResolver:
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
        damage = 0
        if hasattr(target, "archetype_id") and target.is_alive():
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


class HeadlessBattleFactory:
    def __init__(self):
        self.battles = []

    def __call__(self, player_state, enemies, *, ui, encounter_label):
        assert ui is None
        battle = Battle(
            player_state,
            enemies,
            ui=None,
            resolver=DeterministicResolver(),
            rng=DeterministicRng(),
            encounter_label=encounter_label,
        )
        self.battles.append(battle)
        return battle


class HeadlessEnemyFactory:
    def __init__(self):
        self.enemies = []

    def __call__(self, archetype_id, *, tier):
        enemy = create_enemy_state(archetype_id, tier=tier)
        self.enemies.append(enemy)
        return enemy


def _complete_battle(session, first_view):
    view = first_view
    while view.interaction_phase is not InteractionPhase.COMPLETE:
        if view.interaction_phase is InteractionPhase.ACTIONS:
            view = session.submit(ChooseAction("attack"))
        elif view.interaction_phase is InteractionPhase.REGULAR_MOVES:
            view = session.submit(ChooseMove(view.move_options[0].selection_key))
        elif view.interaction_phase is InteractionPhase.TARGETS:
            target = next(
                option.target_id
                for option in view.target_options
                if option.enabled
            )
            view = session.submit(ChooseTarget(target))
        else:
            raise AssertionError(f"unexpected Battle phase: {view.interaction_phase!r}")
    return session.current_view()


def test_headless_semantic_runtime_completes_the_surface_route_without_persistence(
    tmp_path,
):
    game = create_new_game("branoc")
    battle_factory = HeadlessBattleFactory()
    enemy_factory = HeadlessEnemyFactory()
    save_path = tmp_path / "must-not-be-created.json"
    session = OverworldSession(
        game,
        ui=None,
        battle_factory=battle_factory,
        enemy_factory=enemy_factory,
        battle_ui_factory=None,
        save_repository=SaveRepository(save_path),
    )

    view = session.current_view()
    assert view.screen is OverworldScreen.MAIN
    assert view.contextual_route_option.action is OverworldAction.ENTER_ENCOUNTER

    encounter_ids = []
    rest_ids = []
    while not game.overworld_state.route_complete:
        view = session.current_view()
        if view.screen is OverworldScreen.REST:
            rest_ids.append(game.overworld_state.current_route_node_id)
            assert view.contextual_route_option.action is OverworldAction.SKIP_REST
            view = session.submit(ChooseOverworldAction(OverworldAction.REST))
            assert view.screen is OverworldScreen.MAIN
            continue

        assert view.screen is OverworldScreen.MAIN

        route_action = view.contextual_route_option.action
        if route_action is OverworldAction.ENTER_ENCOUNTER:
            current_node_id = game.overworld_state.current_route_node_id
            encounter_ids.append(current_node_id)
            battle_view = session.submit(ChooseOverworldAction(route_action))
            view = _complete_battle(session, battle_view)
            assert view.screen is OverworldScreen.MAIN or view.screen is OverworldScreen.REST
        elif route_action is OverworldAction.REST:
            rest_view = session.submit(ChooseOverworldAction(route_action))
            assert rest_view.screen is OverworldScreen.REST
            view = session.submit(ChooseOverworldAction(OverworldAction.REST))
            assert view.screen is OverworldScreen.MAIN
        else:
            raise AssertionError(f"unexpected route action: {route_action!r}")

    assert tuple(encounter_ids) == EXPECTED_ENCOUNTERS
    assert tuple(rest_ids) == EXPECTED_RESTS
    assert game.world_state.defeated_encounters == EXPECTED_ENCOUNTERS
    assert game.overworld_state.resolved_rest_node_ids == EXPECTED_RESTS
    assert game.overworld_state.current_route_node_id == "surface_dungeon_entrance"
    assert game.overworld_state.route_complete is True
    assert game.overworld_state.dungeon_entrance_reached is True

    assert tuple(
        tuple(enemy.archetype_id for enemy in battle.enemies)
        for battle in battle_factory.battles
    ) == EXPECTED_COMPOSITIONS
    all_enemies = [
        enemy
        for battle in battle_factory.battles
        for enemy in battle.enemies
    ]
    assert len(all_enemies) == 14
    assert len({id(enemy) for enemy in all_enemies}) == 14
    assert all(
        battle.interaction_phase is InteractionPhase.COMPLETE
        for battle in battle_factory.battles
    )
    assert session.active_battle is None

    final_view = session.current_view()
    assert final_view.screen is OverworldScreen.MAIN
    assert final_view.contextual_route_option is None
    assert game.player_state.level_state.current == 9
    assert game.player_state.exp_state.current == 68
    assert game.player_state.growth_points == 24
    assert game.player_state.gold == 75
    assert not save_path.exists()
