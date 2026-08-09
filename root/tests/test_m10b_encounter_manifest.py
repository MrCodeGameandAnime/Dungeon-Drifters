from dataclasses import FrozenInstanceError

import pytest

from app.content.catalog import (
    ENCOUNTER_SPECS,
    get_encounter_rewards,
    get_encounter_spec,
    get_inspectable_encounter_spec,
    get_route_node_spec,
    get_route_successor_id,
)
from app.content.route_spec import RouteNodeKind
from tests.content_test_support import SURFACE_ROUTE_NODES


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
    values = []
    for node in SURFACE_ROUTE_NODES:
        encounter = (
            get_encounter_spec(node.encounter_id)
            if node.encounter_id is not None
            else None
        )
        rewards = get_encounter_rewards(encounter.encounter_id) if encounter else (0, 0)
        values.append(
            (
                node.node_id,
                get_route_successor_id(node.node_id),
                encounter.enemy_archetype_ids if encounter else None,
                rewards[0],
                rewards[1],
                node.kind is RouteNodeKind.BOSS,
            )
        )
    return tuple(values)


def test_surface_route_manifest_matches_the_approved_contract_exactly():
    assert manifest_values() == EXPECTED_MANIFEST


def test_encounter_counts_rewards_and_unique_boss_match_the_contract():
    assert len(ENCOUNTER_SPECS) == 8
    assert sum(
        get_encounter_rewards(spec.encounter_id)[0] for spec in ENCOUNTER_SPECS
    ) == 1060
    assert sum(
        get_encounter_rewards(spec.encounter_id)[1] for spec in ENCOUNTER_SPECS
    ) == 75
    assert tuple(
        node.encounter_id
        for node in SURFACE_ROUTE_NODES
        if node.kind is RouteNodeKind.BOSS
    ) == ("surface_goblin_lord",)
    assert sum(
        archetype_id == "goblin_lord"
        for encounter in ENCOUNTER_SPECS
        for archetype_id in encounter.enemy_archetype_ids
    ) == 1


def test_shaman_appears_in_both_approved_shaman_encounters():
    assert get_encounter_spec("surface_shaman_solo").enemy_archetype_ids == (
        "goblin_shaman",
    )
    assert get_encounter_spec("surface_shaman_pair").enemy_archetype_ids == (
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
    encounter = get_inspectable_encounter_spec(node_id)
    assert (encounter.encounter_id if encounter else None) == expected_encounter_id


def test_catalog_route_and_encounter_records_are_immutable():
    node = get_route_node_spec("surface_goblin_pair")
    encounter = get_encounter_spec(node.encounter_id)
    with pytest.raises(FrozenInstanceError):
        node.display_label = "changed"
    with pytest.raises(FrozenInstanceError):
        encounter.encounter_id = "changed"
    with pytest.raises(TypeError):
        encounter.enemy_archetype_ids[0] = "changed"


def test_unknown_catalog_lookups_fail_explicitly():
    with pytest.raises(ValueError, match="unknown route node ID"):
        get_route_node_spec("unknown")
    with pytest.raises(ValueError, match="unknown encounter ID"):
        get_encounter_spec("unknown")
