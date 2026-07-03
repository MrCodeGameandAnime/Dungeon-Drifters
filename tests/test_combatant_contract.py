import pytest

from app.combat.combatant import Combatant
from app.combat.move import DamageType
from app.enemies.definition import EnemyBehavior, EnemyCapability, EnemyRank, EnemyRole
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.combat.move import Move
from app.player.character import Brawler
from app.player.player_state import PlayerState
from app.player.stats import PermanentStats



def inspect_combatant(combatant):
    return {
        "display_name": combatant.display_name,
        "health": (combatant.health.current, combatant.health.maximum),
        "mana": (combatant.mana_resource.current, combatant.mana_resource.maximum),
        "super": (combatant.super_resource.current, combatant.super_resource.maximum),
        "generates_super": combatant.generates_super,
        "can_defend": combatant.can_defend,
        "physical_defend": combatant.defend_reduction_percent(DamageType.PHYSICAL),
        "moves": tuple(move.name for move in combatant.combat_moves),
        "strength": combatant.effective_stat("strength"),
        "alive": combatant.is_alive(),
    }


def test_player_state_and_enemy_state_satisfy_combatant_contract():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())

    assert isinstance(player_state, Combatant)
    assert isinstance(enemy_state, Combatant)


def test_shared_inspection_works_without_type_branches():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())

    player_info = inspect_combatant(player_state)
    enemy_info = inspect_combatant(enemy_state)

    assert player_info["display_name"] == "Brawler"
    assert player_info["health"] == (60, 60)
    assert player_info["mana"] == (10, 10)
    assert player_info["super"] == (0, 100)
    assert player_info["generates_super"] is True
    assert player_info["can_defend"] is True
    assert player_info["physical_defend"] == 48
    assert player_info["strength"] == 18
    assert player_info["alive"]
    assert len(player_info["moves"]) == 5
    assert all(isinstance(move, Move) for move in player_state.combat_moves)

    assert enemy_info == {
        "display_name": "Goblin",
        "health": (60, 60),
        "mana": (0, 0),
        "super": (0, 100),
        "generates_super": False,
        "can_defend": False,
        "physical_defend": 50,
        "moves": ("slash", "jumping slash"),
        "strength": 3,
        "alive": True,
    }
    assert all(isinstance(move, Move) for move in enemy_state.combat_moves)
    assert enemy_state.archetype_id == "goblin"
    assert enemy_state.tier == 0
    assert enemy_state.rank == EnemyRank.COMMON
    assert enemy_state.role == EnemyRole.MELEE_SKIRMISHER
    assert enemy_state.behavior == EnemyBehavior.AGGRESSIVE
    assert enemy_state.capabilities == frozenset({EnemyCapability.BASIC_ATTACKS})


def test_effective_stat_supports_all_six_canonical_stats():
    combatants = (
        PlayerState(Brawler()),
        EnemyState(Goblin()),
    )

    for combatant in combatants:
        for stat_name in PermanentStats.STAT_NAMES:
            value = combatant.effective_stat(stat_name)
            assert isinstance(value, int)
            assert value >= 1


def test_invalid_effective_stat_names_fail_consistently():
    combatants = (
        PlayerState(Brawler()),
        EnemyState(Goblin()),
    )

    for combatant in combatants:
        with pytest.raises(ValueError):
            combatant.effective_stat("charisma")


def test_is_alive_delegates_to_health_state():
    player_state = PlayerState(Brawler())
    enemy_state = EnemyState(Goblin())

    player_state.health.take_damage(player_state.health.maximum)
    enemy_state.health.take_damage(enemy_state.health.maximum)

    assert not player_state.is_alive()
    assert not enemy_state.is_alive()
