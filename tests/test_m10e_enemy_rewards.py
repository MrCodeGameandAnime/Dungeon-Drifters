import pytest

from app.enemies.factory import create_enemy_definition, create_enemy_state
from app.enemies.state import EnemyState
from app.enemies.registry import get_enemy_registration
from app.game.encounter_manifest import (
    SURFACE_ROUTE_MANIFEST,
    create_route_encounter_enemies,
    encounter_manifest,
)


EXPECTED_REWARDS = {
    "goblin": (40, 3),
    "goblin_warrior": (60, 5),
    "goblin_shaman": (90, 7),
    "goblin_elite": (150, 9),
    "goblin_lord": (200, 10),
}

EXPECTED_ENCOUNTER_REWARDS = {
    "surface_goblin_solo": (40, 3),
    "surface_goblin_pair": (80, 6),
    "surface_warrior_solo": (60, 5),
    "surface_warrior_pair": (120, 10),
    "surface_shaman_solo": (90, 7),
    "surface_shaman_pair": (180, 14),
    "surface_elite_patrol": (190, 12),
    "surface_goblin_lord": (300, 18),
}


@pytest.mark.parametrize("archetype_id, expected", EXPECTED_REWARDS.items())
def test_authored_enemy_definitions_own_exact_rewards(archetype_id, expected):
    definition = get_enemy_registration(archetype_id).definition_factory()

    assert (definition.exp_reward, definition.gold_reward) == expected


@pytest.mark.parametrize("archetype_id, expected", EXPECTED_REWARDS.items())
def test_enemy_state_delegates_read_only_definition_rewards(archetype_id, expected):
    enemy = create_enemy_state(archetype_id)

    assert (enemy.exp_reward, enemy.gold_reward) == expected
    with pytest.raises(AttributeError):
        enemy.exp_reward = 999
    with pytest.raises(AttributeError):
        enemy.gold_reward = 999


@pytest.mark.parametrize("field", ("exp_reward", "gold_reward"))
@pytest.mark.parametrize("value", (True, -1, "40", None))
def test_enemy_reward_values_require_nonnegative_integers(field, value):
    from app.enemies.definition import (
        Enemy,
        EnemyBehavior,
        EnemyCapability,
        EnemyRank,
        EnemyRole,
    )
    from app.enemies.goblin.moves import create_goblin_moves

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
        "combat_moves": create_goblin_moves(),
    }
    values[field] = value

    expected_error = ValueError if value == -1 else TypeError
    with pytest.raises(expected_error, match=field):
        Enemy(**values)


def test_authored_reward_properties_are_read_only():
    definition = get_enemy_registration("goblin").definition_factory()

    with pytest.raises(AttributeError):
        definition.exp_reward = 0
    with pytest.raises(AttributeError):
        definition.gold_reward = 0


@pytest.mark.parametrize("archetype_id", EXPECTED_REWARDS)
def test_factory_exposes_fresh_canonical_scaled_definitions(archetype_id):
    first = create_enemy_definition(archetype_id, tier=0)
    second = create_enemy_definition(archetype_id, tier=0)

    assert not isinstance(first, EnemyState)
    assert first is not second
    assert first.archetype_id == archetype_id
    assert (first.exp_reward, first.gold_reward) == EXPECTED_REWARDS[archetype_id]


def test_surface_manifest_rewards_equal_the_sum_of_authored_composition_values():
    for node in SURFACE_ROUTE_MANIFEST:
        if node.encounter is None:
            continue

        expected_exp = sum(
            EXPECTED_REWARDS[archetype_id][0]
            for archetype_id in node.encounter.enemy_archetype_ids
        )
        expected_gold = sum(
            EXPECTED_REWARDS[archetype_id][1]
            for archetype_id in node.encounter.enemy_archetype_ids
        )

        assert node.encounter.exp_reward == expected_exp
        assert node.encounter.gold_reward == expected_gold


def test_all_surface_encounter_totals_and_route_totals_are_exact():
    actual = {
        node.encounter.encounter_id: (
            node.encounter.exp_reward,
            node.encounter.gold_reward,
        )
        for node in SURFACE_ROUTE_MANIFEST
        if node.encounter is not None
    }

    assert actual == EXPECTED_ENCOUNTER_REWARDS
    assert sum(exp for exp, _ in actual.values()) == 1060
    assert sum(gold for _, gold in actual.values()) == 75


@pytest.mark.parametrize("encounter_id", EXPECTED_ENCOUNTER_REWARDS)
def test_runtime_enemy_mutation_cannot_change_manifest_reward(encounter_id):
    encounter = encounter_manifest(encounter_id)
    enemies = create_route_encounter_enemies(encounter_id)

    for enemy in enemies:
        enemy.health.take_damage(enemy.health.current)
        enemy.mana_resource.spend(enemy.mana_resource.current)

    assert (encounter.exp_reward, encounter.gold_reward) == (
        EXPECTED_ENCOUNTER_REWARDS[encounter_id]
    )
