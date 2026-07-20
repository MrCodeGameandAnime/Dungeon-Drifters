import pytest

from app.enemies.factory import create_enemy_state
from app.enemies.registry import get_enemy_registration


EXPECTED_REWARDS = {
    "goblin": (40, 3),
    "goblin_warrior": (60, 5),
    "goblin_shaman": (90, 7),
    "goblin_elite": (150, 9),
    "goblin_lord": (200, 10),
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
