from dataclasses import FrozenInstanceError

import pytest

from app.game.encounter_manifest import (
    EncounterManifest,
    RouteManifestNode,
    SURFACE_ROUTE_MANIFEST,
    encounter_manifest,
    inspectable_encounter_for_node,
    route_manifest_node,
)
from app.game.overworld_route import SURFACE_ROUTE_NODES


EXPECTED_MANIFEST = (
    ("surface_goblin_solo", "surface_goblin_pair", ("goblin",), 40, 3, False),
    (
        "surface_goblin_pair",
        "surface_warrior_solo",
        ("goblin", "goblin"),
        80,
        6,
        False,
    ),
    (
        "surface_warrior_solo",
        "surface_rest_after_warrior_solo",
        ("goblin_warrior",),
        60,
        5,
        False,
    ),
    ("surface_rest_after_warrior_solo", "surface_warrior_pair", None, 0, 0, False),
    (
        "surface_warrior_pair",
        "surface_shaman_solo",
        ("goblin_warrior", "goblin_warrior"),
        120,
        10,
        False,
    ),
    (
        "surface_shaman_solo",
        "surface_shaman_pair",
        ("goblin_shaman",),
        90,
        7,
        False,
    ),
    (
        "surface_shaman_pair",
        "surface_rest_after_shaman_pair",
        ("goblin_shaman", "goblin_shaman"),
        180,
        14,
        False,
    ),
    ("surface_rest_after_shaman_pair", "surface_elite_patrol", None, 0, 0, False),
    (
        "surface_elite_patrol",
        "surface_rest_before_goblin_lord",
        ("goblin_elite", "goblin"),
        190,
        12,
        False,
    ),
    ("surface_rest_before_goblin_lord", "surface_goblin_lord", None, 0, 0, False),
    (
        "surface_goblin_lord",
        "surface_dungeon_entrance",
        ("goblin_lord", "goblin", "goblin_warrior"),
        300,
        18,
        True,
    ),
    ("surface_dungeon_entrance", None, None, 0, 0, False),
)


def manifest_values():
    return tuple(
        (
            node.node_id,
            node.next_node_id,
            node.encounter.enemy_archetype_ids if node.encounter else None,
            node.encounter.exp_reward if node.encounter else 0,
            node.encounter.gold_reward if node.encounter else 0,
            node.encounter.boss if node.encounter else False,
        )
        for node in SURFACE_ROUTE_MANIFEST
    )


def test_surface_route_manifest_matches_the_approved_contract_exactly():
    assert manifest_values() == EXPECTED_MANIFEST
    assert tuple(node.node_id for node in SURFACE_ROUTE_MANIFEST) == tuple(
        node.node_id for node in SURFACE_ROUTE_NODES
    )


def test_encounter_counts_rewards_and_unique_boss_match_the_contract():
    encounters = tuple(
        node.encounter for node in SURFACE_ROUTE_MANIFEST if node.encounter
    )

    assert len(encounters) == 8
    assert len({encounter.encounter_id for encounter in encounters}) == 8
    assert sum(encounter.exp_reward for encounter in encounters) == 1060
    assert sum(encounter.gold_reward for encounter in encounters) == 75
    assert tuple(encounter.encounter_id for encounter in encounters if encounter.boss) == (
        "surface_goblin_lord",
    )
    assert sum(
        archetype_id == "goblin_lord"
        for encounter in encounters
        for archetype_id in encounter.enemy_archetype_ids
    ) == 1


def test_shaman_appears_in_both_approved_shaman_encounters():
    assert encounter_manifest("surface_shaman_solo").enemy_archetype_ids == (
        "goblin_shaman",
    )
    assert encounter_manifest("surface_shaman_pair").enemy_archetype_ids == (
        "goblin_shaman",
        "goblin_shaman",
    )


@pytest.mark.parametrize(
    ("node_id", "expected_encounter_id"),
    (
        ("surface_goblin_pair", "surface_goblin_pair"),
        ("surface_rest_after_warrior_solo", "surface_warrior_pair"),
        ("surface_rest_after_shaman_pair", "surface_elite_patrol"),
        ("surface_rest_before_goblin_lord", "surface_goblin_lord"),
        ("surface_dungeon_entrance", None),
    ),
)
def test_inspectable_encounter_uses_current_combat_or_next_combat_after_rest(
    node_id,
    expected_encounter_id,
):
    encounter = inspectable_encounter_for_node(node_id)
    assert (
        encounter.encounter_id if encounter is not None else None
    ) == expected_encounter_id


def test_manifest_records_and_compositions_are_immutable():
    node = route_manifest_node("surface_goblin_pair")
    encounter = node.encounter

    with pytest.raises(FrozenInstanceError):
        node.next_node_id = "changed"
    with pytest.raises(FrozenInstanceError):
        encounter.gold_reward = 999
    with pytest.raises(TypeError):
        encounter.enemy_archetype_ids[0] = "changed"


@pytest.mark.parametrize(
    "factory",
    (
        lambda: EncounterManifest("", ("goblin",), 1, 1, False),
        lambda: EncounterManifest("id", (), 1, 1, False),
        lambda: EncounterManifest("id", ["goblin"], 1, 1, False),
        lambda: EncounterManifest("id", ("goblin",), -1, 1, False),
        lambda: EncounterManifest("id", ("goblin",), 1, -1, False),
        lambda: EncounterManifest("id", ("goblin",), 1, 1, 1),
        lambda: RouteManifestNode("", None),
        lambda: RouteManifestNode("id", 4),
        lambda: RouteManifestNode("id", None, object()),
    ),
)
def test_invalid_manifest_values_fail_explicitly_without_mutating_authored_data(
    factory,
):
    before = manifest_values()
    with pytest.raises((TypeError, ValueError)):
        factory()
    assert manifest_values() == before


def test_unknown_manifest_lookups_fail_explicitly():
    with pytest.raises(ValueError, match="unknown surface route node"):
        route_manifest_node("unknown")
    with pytest.raises(ValueError, match="unknown surface encounter"):
        encounter_manifest("unknown")
    with pytest.raises(TypeError, match="node_id must be a string"):
        route_manifest_node(None)
