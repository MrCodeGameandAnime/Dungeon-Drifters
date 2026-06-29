import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.combat.enemy import Goblin, Orc, SkeletonArcher, SnakeLord, Zombie
from app.combat.enemy_state import EnemyState


EXPECTED_ENEMIES = {
    Goblin: {
        "name": "Goblin",
        "stats": {
            "constitution": 2,
            "spirit": 1,
            "intelligence": 1,
            "strength": 3,
            "dexterity": 1,
            "intuition": 1,
        },
        "hp": 60,
        "mana": 10,
        "moves": {1: "slash", 2: "jumping slash", 3: "suplex"},
    },
    Orc: {
        "name": "Orc",
        "stats": {
            "constitution": 5,
            "spirit": 1,
            "intelligence": 1,
            "strength": 7,
            "dexterity": 1,
            "intuition": 1,
        },
        "hp": 60,
        "mana": 10,
        "moves": {1: "slash", 2: "jumping slash", 3: "suplex"},
    },
    SkeletonArcher: {
        "name": "Skeleton Archer",
        "stats": {
            "constitution": 5,
            "spirit": 1,
            "intelligence": 1,
            "strength": 7,
            "dexterity": 1,
            "intuition": 1,
        },
        "hp": 60,
        "mana": 10,
        "moves": {1: "slash", 2: "jumping slash", 3: "suplex"},
    },
    Zombie: {
        "name": "Zombie",
        "stats": {
            "constitution": 5,
            "spirit": 1,
            "intelligence": 1,
            "strength": 7,
            "dexterity": 1,
            "intuition": 1,
        },
        "hp": 60,
        "mana": 10,
        "moves": {1: "slash", 2: "jumping slash", 3: "suplex"},
    },
    SnakeLord: {
        "name": "Snake Lord",
        "stats": {
            "constitution": 5,
            "spirit": 1,
            "intelligence": 1,
            "strength": 7,
            "dexterity": 1,
            "intuition": 1,
        },
        "hp": 60,
        "mana": 10,
        "moves": {1: "slash", 2: "jumping slash", 3: "suplex"},
    },
}


def test_enemy_definitions_preserve_authored_data():
    for enemy_type, expected in EXPECTED_ENEMIES.items():
        enemy = enemy_type()

        assert enemy.name == expected["name"]
        assert enemy.hp == expected["hp"]
        assert enemy.mana == expected["mana"]
        assert enemy.moves == expected["moves"]
        for stat_name, value in expected["stats"].items():
            assert getattr(enemy, stat_name) == value


def test_enemy_state_copies_definition_into_runtime_state():
    for enemy_type, expected in EXPECTED_ENEMIES.items():
        definition = enemy_type()
        enemy_state = EnemyState(definition)

        assert enemy_state.definition is definition
        assert enemy_state.display_name == expected["name"]
        assert enemy_state.name == expected["name"]
        assert enemy_state.health.current == expected["hp"]
        assert enemy_state.health.maximum == expected["hp"]
        assert enemy_state.mana_resource.current == expected["mana"]
        assert enemy_state.mana_resource.maximum == expected["mana"]
        assert enemy_state.moves == expected["moves"]
        assert enemy_state.combat_moves == tuple(expected["moves"].values())
        for stat_name, value in expected["stats"].items():
            assert enemy_state.effective_stat(stat_name) == value


def test_enemy_states_do_not_share_runtime_resources_stats_or_moves():
    first = EnemyState(Goblin())
    second = EnemyState(Goblin())

    first.health.take_damage(5)
    first.mana_resource.spend(3)
    first.permanent_stats.increase_stat("strength", 1)
    first.moves[4] = "runtime only"

    assert first.health is not second.health
    assert first.mana_resource is not second.mana_resource
    assert first.permanent_stats is not second.permanent_stats
    assert first.stats is not second.stats
    assert first.moves is not second.moves
    assert first.health.current == 55
    assert second.health.current == 60
    assert first.mana_resource.current == 7
    assert second.mana_resource.current == 10
    assert first.effective_stat("strength") == 4
    assert second.effective_stat("strength") == 3
    assert 4 in first.moves
    assert 4 not in second.moves


def test_runtime_mutation_does_not_mutate_enemy_definition():
    definition = Goblin()
    enemy_state = EnemyState(definition)

    enemy_state.health.take_damage(10)
    enemy_state.health.heal(3)
    enemy_state.mana_resource.spend(4)
    enemy_state.permanent_stats.increase_stat("constitution", 1)
    enemy_state.moves[1] = "changed slash"

    assert definition.hp == 60
    assert definition.mana == 10
    assert definition.constitution == 2
    assert definition.moves == {1: "slash", 2: "jumping slash", 3: "suplex"}


def test_enemy_state_alive_status_comes_from_health():
    enemy_state = EnemyState(Goblin())

    assert enemy_state.is_alive()
    enemy_state.health.take_damage(enemy_state.health.maximum)

    assert not enemy_state.is_alive()


if __name__ == "__main__":
    test_enemy_definitions_preserve_authored_data()
    test_enemy_state_copies_definition_into_runtime_state()
    test_enemy_states_do_not_share_runtime_resources_stats_or_moves()
    test_runtime_mutation_does_not_mutate_enemy_definition()
    test_enemy_state_alive_status_comes_from_health()
    print("Enemy state test passed.")
