import pytest

from app.combat.combat_state import CombatState
from app.game.encounter_manifest import (
    SURFACE_ROUTE_MANIFEST,
    create_route_encounter_enemies,
)
from app.game.game_state import GameState
from app.player.character import Brawler
from app.player.player_state import PlayerState


EXPECTED_COMPOSITIONS = {
    "surface_goblin_solo": ("goblin",),
    "surface_goblin_pair": ("goblin", "goblin"),
    "surface_warrior_solo": ("goblin_warrior",),
    "surface_warrior_pair": ("goblin_warrior", "goblin_warrior"),
    "surface_shaman_solo": ("goblin_shaman",),
    "surface_shaman_pair": ("goblin_shaman", "goblin_shaman"),
    "surface_elite_patrol": ("goblin_elite", "goblin"),
    "surface_goblin_lord": (
        "goblin_lord",
        "goblin",
        "goblin_warrior",
    ),
}


@pytest.mark.parametrize(
    ("node_id", "expected_archetype_ids"),
    EXPECTED_COMPOSITIONS.items(),
)
def test_every_authored_encounter_instantiates_at_tier_zero_in_exact_order(
    node_id,
    expected_archetype_ids,
):
    enemies = create_route_encounter_enemies(node_id)

    assert tuple(enemy.archetype_id for enemy in enemies) == expected_archetype_ids
    assert tuple(enemy.tier for enemy in enemies) == (0,) * len(enemies)


def test_injected_factory_receives_every_authored_entry_exactly_once():
    calls = []
    sentinels = []

    def factory(archetype_id, *, tier):
        sentinel = object()
        calls.append((archetype_id, tier))
        sentinels.append(sentinel)
        return sentinel

    result = create_route_encounter_enemies(
        "surface_goblin_lord",
        enemy_factory=factory,
    )

    assert calls == [
        ("goblin_lord", 0),
        ("goblin", 0),
        ("goblin_warrior", 0),
    ]
    assert result == tuple(sentinels)


@pytest.mark.parametrize(
    "node_id",
    (
        "surface_goblin_pair",
        "surface_warrior_pair",
        "surface_shaman_pair",
    ),
)
def test_duplicate_enemies_own_independent_runtime_resources(node_id):
    first, second = create_route_encounter_enemies(node_id)

    assert first is not second
    assert first.definition is not second.definition
    assert first.health is not second.health
    assert first.mana_resource is not second.mana_resource
    assert first.super_resource is not second.super_resource
    assert first.permanent_stats is not second.permanent_stats
    assert first.stats is not second.stats

    first.health.take_damage(7)
    if first.mana_resource.maximum:
        assert first.mana_resource.spend(5) is True

    assert second.health.current == second.health.maximum
    assert second.mana_resource.current == second.mana_resource.maximum


def test_duplicate_enemies_remain_identity_distinct_in_combat_state():
    player = PlayerState(Brawler())
    first, second = create_route_encounter_enemies("surface_goblin_pair")
    combat_state = CombatState()

    combat_state.apply_burn(player, first)

    assert combat_state.burn_active(first) is True
    assert combat_state.burn_active(second) is False


def test_repeated_creation_never_reuses_runtime_or_resource_objects():
    first = create_route_encounter_enemies("surface_goblin_lord")
    second = create_route_encounter_enemies("surface_goblin_lord")

    for first_enemy, second_enemy in zip(first, second, strict=True):
        assert first_enemy is not second_enemy
        assert first_enemy.definition is not second_enemy.definition
        assert first_enemy.health is not second_enemy.health
        assert first_enemy.mana_resource is not second_enemy.mana_resource
        assert first_enemy.super_resource is not second_enemy.super_resource


@pytest.mark.parametrize(
    "node_id",
    (
        "surface_rest_after_warrior_solo",
        "surface_rest_after_shaman_pair",
        "surface_rest_before_goblin_lord",
        "surface_dungeon_entrance",
        "unknown_node",
    ),
)
def test_non_encounter_creation_fails_before_factory_or_session_mutation(node_id):
    game = GameState(PlayerState(Brawler()))
    before_snapshot = game.snapshot()
    before_manifest = repr(SURFACE_ROUTE_MANIFEST)
    calls = []

    def factory(archetype_id, *, tier):
        calls.append((archetype_id, tier))
        return object()

    with pytest.raises(ValueError):
        create_route_encounter_enemies(node_id, enemy_factory=factory)

    assert calls == []
    assert game.snapshot() == before_snapshot
    assert repr(SURFACE_ROUTE_MANIFEST) == before_manifest


def test_creation_and_runtime_mutation_do_not_change_authored_definitions():
    enemies = create_route_encounter_enemies("surface_shaman_pair")
    before = tuple(
        (
            enemy.definition.hp,
            enemy.definition.mana,
            tuple(enemy.definition.combat_moves),
        )
        for enemy in enemies
    )

    enemies[0].health.take_damage(12)
    assert enemies[0].mana_resource.spend(10) is True

    assert tuple(
        (
            enemy.definition.hp,
            enemy.definition.mana,
            tuple(enemy.definition.combat_moves),
        )
        for enemy in enemies
    ) == before


def test_enemy_factory_must_be_callable():
    with pytest.raises(TypeError, match="enemy_factory must be callable"):
        create_route_encounter_enemies(
            "surface_goblin_solo",
            enemy_factory=None,
        )
