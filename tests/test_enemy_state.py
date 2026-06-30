from app.combat.enemy import Goblin, Orc, SkeletonArcher, SnakeLord, Zombie
from app.combat.enemy_state import EnemyState
from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType


EXPECTED_COMBAT_MOVES = [
    {
        "name": "slash",
        "kind": "damage",
        "resource_type": "none",
        "resource_cost": 0,
        "power": 8,
        "scales_with": ["strength"],
        "accuracy": 90,
        "target": "enemy",
        "damage_type": "physical",
        "mechanic": "basic_attack",
        "description": "A simple close-range strike.",
    },
    {
        "name": "jumping slash",
        "kind": "damage",
        "resource_type": "none",
        "resource_cost": 0,
        "power": 12,
        "scales_with": ["strength"],
        "accuracy": 80,
        "target": "enemy",
        "damage_type": "physical",
        "mechanic": "heavy_attack",
        "description": "A committed leaping slash.",
    },
    {
        "name": "suplex",
        "kind": "damage",
        "resource_type": "none",
        "resource_cost": 0,
        "power": 14,
        "scales_with": ["strength"],
        "accuracy": 75,
        "target": "enemy",
        "damage_type": "physical",
        "mechanic": "stagger",
        "description": "A forceful throw meant to disrupt the target.",
    },
]


def move_to_dict(move):
    return {
        "name": move.name,
        "kind": move.kind.value,
        "resource_type": move.resource_type.value,
        "resource_cost": move.resource_cost,
        "power": move.power,
        "scales_with": [
            attribute.value
            for attribute in move.scales_with
        ],
        "accuracy": move.accuracy,
        "target": move.target.value,
        "damage_type": move.damage_type.value,
        "mechanic": move.mechanic,
        "description": move.description,
    }


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
        "combat_moves": EXPECTED_COMBAT_MOVES,
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
        "combat_moves": EXPECTED_COMBAT_MOVES,
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
        "combat_moves": EXPECTED_COMBAT_MOVES,
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
        "combat_moves": EXPECTED_COMBAT_MOVES,
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
        "combat_moves": EXPECTED_COMBAT_MOVES,
    },
}


def test_enemy_definitions_preserve_authored_data():
    for enemy_type, expected in EXPECTED_ENEMIES.items():
        enemy = enemy_type()

        assert enemy.name == expected["name"]
        assert enemy.hp == expected["hp"]
        assert enemy.mana == expected["mana"]
        assert enemy.moves == expected["moves"]
        assert [move_to_dict(move) for move in enemy.combat_moves] == expected["combat_moves"]
        assert all(isinstance(move, Move) for move in enemy.combat_moves)
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
        assert [move_to_dict(move) for move in enemy_state.combat_moves] == expected["combat_moves"]
        assert all(isinstance(move, Move) for move in enemy_state.combat_moves)
        for stat_name, value in expected["stats"].items():
            assert enemy_state.effective_stat(stat_name) == value


def test_enemy_states_do_not_share_runtime_resources_stats_or_moves():
    first = EnemyState(Goblin())
    second = EnemyState(Goblin())

    first.health.take_damage(5)
    first.mana_resource.spend(3)
    first.permanent_stats.increase_stat("strength", 1)
    first_moves = first.moves
    first_moves[4] = "runtime only"

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
    assert 4 in first_moves
    assert 4 not in first.moves
    assert 4 not in second.moves


def test_runtime_mutation_does_not_mutate_enemy_definition():
    definition = Goblin()
    enemy_state = EnemyState(definition)

    enemy_state.health.take_damage(10)
    enemy_state.health.heal(3)
    enemy_state.mana_resource.spend(4)
    enemy_state.permanent_stats.increase_stat("constitution", 1)
    mutated_definition_moves = definition.moves
    mutated_state_moves = enemy_state.moves
    mutated_definition_moves[1] = "changed slash"
    mutated_state_moves[1] = "changed slash"

    assert definition.hp == 60
    assert definition.mana == 10
    assert definition.constitution == 2
    assert definition.moves == {1: "slash", 2: "jumping slash", 3: "suplex"}
    assert enemy_state.moves == {1: "slash", 2: "jumping slash", 3: "suplex"}
    assert enemy_state.moves[1] == enemy_state.combat_moves[0].name
    assert EnemyState(definition).combat_moves == definition.combat_moves


def test_enemy_definition_moves_are_derived_and_cannot_diverge():
    enemy = Goblin()
    legacy_moves = enemy.moves
    legacy_moves[1] = "corrupted"

    assert enemy.moves == {1: "slash", 2: "jumping slash", 3: "suplex"}
    assert enemy.moves[1] == enemy.combat_moves[0].name
    assert EnemyState(enemy).combat_moves == enemy.combat_moves


def test_enemy_state_moves_are_derived_and_cannot_diverge():
    enemy_state = EnemyState(Goblin())
    legacy_moves = enemy_state.moves
    legacy_moves[1] = "corrupted"

    assert enemy_state.moves == {1: "slash", 2: "jumping slash", 3: "suplex"}
    assert enemy_state.moves[1] == enemy_state.combat_moves[0].name
    assert all(
        enemy_state.moves[index] == enemy_state.combat_moves[index - 1].name
        for index in enemy_state.moves
    )


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
    test_enemy_definition_moves_are_derived_and_cannot_diverge()
    test_enemy_state_moves_are_derived_and_cannot_diverge()
    test_enemy_state_alive_status_comes_from_health()
    print("Enemy state test passed.")
