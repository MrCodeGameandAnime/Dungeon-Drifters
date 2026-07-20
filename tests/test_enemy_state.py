import pytest

from app.enemies.definition import (
    Enemy,
    EnemyBehavior,
    EnemyCapability,
    EnemyRank,
    EnemyRole,
)
from app.enemies.factory import (
    create_enemy_state,
)
from app.enemies.goblin.definition import Goblin
from app.enemies.registration import EnemyArchetypeRegistration
from app.enemies.registry import build_enemy_registry, get_enemy_registration
from app.enemies.state import EnemyState
import app.enemies.factory as factory_module
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
        "archetype_id": "goblin",
        "name": "Goblin",
        "rank": EnemyRank.COMMON,
        "role": EnemyRole.MELEE_SKIRMISHER,
        "behavior": EnemyBehavior.AGGRESSIVE,
        "capabilities": frozenset({EnemyCapability.BASIC_ATTACKS}),
        "stats": {
            "constitution": 2,
            "spirit": 1,
            "intelligence": 1,
            "strength": 3,
            "dexterity": 1,
            "intuition": 1,
        },
        "hp": 60,
        "mana": 0,
        "moves": {1: "slash", 2: "jumping slash"},
        "combat_moves": EXPECTED_COMBAT_MOVES,
    },
}


def test_enemy_definitions_preserve_authored_data():
    for enemy_type, expected in EXPECTED_ENEMIES.items():
        enemy = enemy_type()

        assert enemy.archetype_id == expected["archetype_id"]
        assert enemy.name == expected["name"]
        assert enemy.rank == expected["rank"]
        assert enemy.role == expected["role"]
        assert enemy.behavior == expected["behavior"]
        assert enemy.capabilities == expected["capabilities"]
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
        assert enemy_state.archetype_id == expected["archetype_id"]
        assert enemy_state.tier == 0
        assert enemy_state.rank == expected["rank"]
        assert enemy_state.role == expected["role"]
        assert enemy_state.behavior == expected["behavior"]
        assert enemy_state.capabilities == expected["capabilities"]
        assert not enemy_state.generates_super
        assert not enemy_state.can_defend
        assert enemy_state.defend_reduction_percent(DamageType.PHYSICAL) == 50
        assert enemy_state.defend_reduction_percent(DamageType.MAGICAL) == 40
        assert enemy_state.defend_reduction_percent(DamageType.HYBRID) == 30
        assert enemy_state.defend_reduction_percent(DamageType.HEALING) == 0
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


def test_factory_creates_goblin_enemy_state():
    enemy_state = create_enemy_state("goblin", tier=0)

    assert isinstance(enemy_state, EnemyState)
    assert isinstance(enemy_state.definition, Goblin)
    assert enemy_state.archetype_id == "goblin"
    assert enemy_state.tier == 0
    assert enemy_state.rank == EnemyRank.COMMON
    assert enemy_state.role == EnemyRole.MELEE_SKIRMISHER
    assert enemy_state.behavior == EnemyBehavior.AGGRESSIVE
    assert enemy_state.capabilities == frozenset({EnemyCapability.BASIC_ATTACKS})
    assert enemy_state.display_name == "Goblin"
    assert enemy_state.health.current == 60
    assert enemy_state.mana_resource.current == 0
    assert enemy_state.mana_resource.maximum == 0
    assert enemy_state.super_resource.current == 0
    assert enemy_state.super_resource.maximum == 100
    assert not enemy_state.generates_super
    assert not enemy_state.can_defend
    assert enemy_state.moves == {1: "slash", 2: "jumping slash"}
    assert [move_to_dict(move) for move in enemy_state.combat_moves] == EXPECTED_COMBAT_MOVES


def test_factory_rejects_unknown_enemy_type():
    try:
        create_enemy_state("orc", tier=0)
    except ValueError as error:
        assert "unknown enemy archetype" in str(error)
    else:
        raise AssertionError("Expected ValueError")


def test_factory_rejects_invalid_tier_values():
    invalid_type_values = (True, False, "0", 0.0, None)

    for value in invalid_type_values:
        try:
            create_enemy_state("goblin", tier=value)
        except TypeError as error:
            assert "enemy tier must be an integer" in str(error)
        else:
            raise AssertionError("Expected TypeError")

    try:
        create_enemy_state("goblin", tier=-1)
    except ValueError as error:
        assert "zero or greater" in str(error)
    else:
        raise AssertionError("Expected ValueError")

    try:
        create_enemy_state("goblin", tier=1)
    except ValueError as error:
        assert "goblin does not support tier 1" in str(error)
    else:
        raise AssertionError("Expected ValueError")


def test_direct_enemy_state_construction_uses_same_tier_validation():
    invalid_type_values = (True, False, "0", 0.0, None)

    for value in invalid_type_values:
        with pytest.raises(TypeError, match="enemy tier must be an integer"):
            EnemyState(Goblin(), tier=value)

    with pytest.raises(ValueError, match="zero or greater"):
        EnemyState(Goblin(), tier=-1)

    enemy_state = EnemyState(Goblin(), tier=0)

    assert enemy_state.tier == 0


def test_enemy_metadata_rejects_invalid_non_enum_values():
    valid_moves = (EXPECTED_COMBAT_MOVES,)

    def create_enemy(**overrides):
        values = {
            "strn": 1,
            "con": 1,
            "intl": 1,
            "dex": 1,
            "hp": 1,
            "mana": 0,
            "exp_reward": 0,
            "gold_reward": 0,
            "name": "Test",
            "archetype_id": "test",
            "rank": EnemyRank.COMMON,
            "role": EnemyRole.MELEE_SKIRMISHER,
            "behavior": EnemyBehavior.AGGRESSIVE,
            "capabilities": (EnemyCapability.BASIC_ATTACKS,),
            "combat_moves": Goblin().combat_moves,
        }
        values.update(overrides)
        return Enemy(**values)

    with pytest.raises(TypeError, match="rank"):
        create_enemy(rank="common")
    with pytest.raises(TypeError, match="role"):
        create_enemy(role="melee_skirmisher")
    with pytest.raises(TypeError, match="behavior"):
        create_enemy(behavior="aggressive")
    with pytest.raises(TypeError, match="capabilities"):
        create_enemy(capabilities={"basic_attacks"})
    with pytest.raises(TypeError, match="capabilities"):
        create_enemy(capabilities="basic_attacks")

    assert valid_moves


def test_enemy_states_do_not_share_runtime_resources_stats_or_moves():
    first = EnemyState(Goblin())
    second = EnemyState(Goblin())

    first.health.take_damage(5)
    first.mana_resource.restore(3)
    first.super_resource.gain(10)
    first.permanent_stats.increase_stat("strength", 1)
    first_moves = first.moves
    first_moves[4] = "runtime only"

    assert first.health is not second.health
    assert first.mana_resource is not second.mana_resource
    assert first.super_resource is not second.super_resource
    assert first.permanent_stats is not second.permanent_stats
    assert first.stats is not second.stats
    assert first.moves is not second.moves
    assert first.health.current == 55
    assert second.health.current == 60
    assert first.mana_resource.current == 0
    assert second.mana_resource.current == 0
    assert first.super_resource.current == 10
    assert second.super_resource.current == 0
    assert first.effective_stat("strength") == 4
    assert second.effective_stat("strength") == 3
    assert 4 in first_moves
    assert 4 not in first.moves
    assert 4 not in second.moves


def test_factory_enemy_states_do_not_share_runtime_state():
    first = create_enemy_state("goblin", tier=0)
    second = create_enemy_state("goblin", tier=0)

    first.health.take_damage(5)
    first.mana_resource.restore(3)
    first.super_resource.gain(10)
    first.permanent_stats.increase_stat("strength", 1)
    first_moves = first.moves
    first_moves[4] = "runtime only"

    assert first.definition is not second.definition
    assert first.health is not second.health
    assert first.mana_resource is not second.mana_resource
    assert first.super_resource is not second.super_resource
    assert first.permanent_stats is not second.permanent_stats
    assert first.combat_moves is not second.combat_moves
    assert first.health.current == 55
    assert second.health.current == 60
    assert first.mana_resource.current == 0
    assert second.mana_resource.current == 0
    assert first.super_resource.current == 10
    assert second.super_resource.current == 0
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
    enemy_state.mana_resource.restore(4)
    enemy_state.permanent_stats.increase_stat("constitution", 1)
    mutated_definition_moves = definition.moves
    mutated_state_moves = enemy_state.moves
    mutated_definition_moves[1] = "changed slash"
    mutated_state_moves[1] = "changed slash"

    assert definition.hp == 60
    assert definition.mana == 0
    assert definition.constitution == 2
    assert definition.moves == {1: "slash", 2: "jumping slash"}
    assert enemy_state.moves == {1: "slash", 2: "jumping slash"}
    assert enemy_state.moves[1] == enemy_state.combat_moves[0].name
    assert EnemyState(definition).combat_moves == definition.combat_moves


def test_enemy_definition_moves_are_derived_and_cannot_diverge():
    enemy = Goblin()
    legacy_moves = enemy.moves
    legacy_moves[1] = "corrupted"

    assert enemy.moves == {1: "slash", 2: "jumping slash"}
    assert enemy.moves[1] == enemy.combat_moves[0].name
    assert EnemyState(enemy).combat_moves == enemy.combat_moves


def test_enemy_state_moves_are_derived_and_cannot_diverge():
    enemy_state = EnemyState(Goblin())
    legacy_moves = enemy_state.moves
    legacy_moves[1] = "corrupted"

    assert enemy_state.moves == {1: "slash", 2: "jumping slash"}
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


def test_capability_collections_are_immutable_and_not_shared():
    first = Goblin()
    second = Goblin()

    assert isinstance(first.capabilities, frozenset)
    assert first.capabilities == frozenset({EnemyCapability.BASIC_ATTACKS})
    assert first.capabilities is not second.capabilities
    with pytest.raises(AttributeError):
        first.capabilities.add(EnemyCapability.SUPER)


def test_registry_returns_fresh_definitions_and_factory_uses_registered_scaling_policy():
    registration = get_enemy_registration("goblin")
    first = registration.definition_factory()
    second = registration.definition_factory()

    assert first is not second
    assert first.combat_moves is not second.combat_moves
    assert registration.scaling_policy(first, 0) is first

    first_state = create_enemy_state("goblin", tier=0)
    second_state = create_enemy_state("goblin", tier=0)

    assert first_state is not second_state
    assert first_state.definition is not second_state.definition


def test_factory_uses_registered_scaling_policy(monkeypatch):
    calls = []

    def definition_factory():
        return Goblin()

    def scaling_policy(definition, tier):
        calls.append((definition.archetype_id, tier))
        return definition

    temporary_registration = EnemyArchetypeRegistration(
        archetype_id="test_goblin",
        definition_factory=definition_factory,
        scaling_policy=scaling_policy,
    )
    temporary_registry = build_enemy_registry((temporary_registration,))

    monkeypatch.setattr(
        factory_module,
        "get_enemy_registration",
        lambda archetype_id: temporary_registry[archetype_id],
    )

    enemy_state = factory_module.create_enemy_state("test_goblin", tier=0)

    assert enemy_state.archetype_id == "goblin"
    assert calls == [("goblin", 0)]


def test_duplicate_enemy_registrations_are_rejected():
    registration = get_enemy_registration("goblin")

    with pytest.raises(ValueError, match="duplicate enemy archetype registration: goblin"):
        build_enemy_registry((registration, registration))
