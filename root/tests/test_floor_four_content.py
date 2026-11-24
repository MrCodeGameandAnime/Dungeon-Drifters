from app.content.catalog import (
    create_enemy_state,
    get_enemy_spec,
    get_encounter_spec,
    get_route_spec,
)
from app.content.route_spec import RouteNodeKind
from app.content.vendor_catalog import FIRST_CLEAR_REWARDS


EXPECTED_NODES = (
    ("floor_four_battle_01", RouteNodeKind.COMBAT, "m8_floor_four_encounter_01"),
    ("floor_four_battle_02", RouteNodeKind.COMBAT, "m8_floor_four_encounter_02"),
    ("floor_four_battle_03", RouteNodeKind.COMBAT, "m8_floor_four_encounter_03"),
    ("floor_four_battle_04", RouteNodeKind.COMBAT, "m8_floor_four_encounter_04"),
    ("floor_four_battle_05", RouteNodeKind.COMBAT, "m8_floor_four_encounter_05"),
    ("floor_four_rest_midpoint", RouteNodeKind.REST, None),
    ("floor_four_battle_06", RouteNodeKind.COMBAT, "m8_floor_four_encounter_06"),
    ("floor_four_battle_07", RouteNodeKind.COMBAT, "m8_floor_four_encounter_07"),
    ("floor_four_battle_08", RouteNodeKind.COMBAT, "m8_floor_four_encounter_08"),
    ("floor_four_battle_09", RouteNodeKind.COMBAT, "m8_floor_four_encounter_09"),
    ("floor_four_rest_pre_boss", RouteNodeKind.REST, None),
    ("floor_four_battle_10", RouteNodeKind.BOSS, "m8_tidebound_curator_boss"),
)

EXPECTED_COMPOSITIONS = {
    "m8_floor_four_encounter_01": ("reliquary_sentinel", "drowned_stalker"),
    "m8_floor_four_encounter_02": ("brine_oracle", "drowned_stalker"),
    "m8_floor_four_encounter_03": ("reliquary_sentinel", "reliquary_sentinel"),
    "m8_floor_four_encounter_04": ("brine_oracle", "reliquary_sentinel"),
    "m8_floor_four_encounter_05": ("ashbound_hound", "drowned_stalker"),
    "m8_floor_four_encounter_06": ("reliquary_sentinel", "brine_oracle"),
    "m8_floor_four_encounter_07": (
        "drowned_stalker", "drowned_stalker", "brine_oracle"
    ),
    "m8_floor_four_encounter_08": (
        "reliquary_sentinel", "ashbound_hound", "brine_oracle"
    ),
    "m8_floor_four_encounter_09": (
        "brine_oracle", "brine_oracle", "drowned_stalker"
    ),
    "m8_tidebound_curator_boss": ("tidebound_curator", "reliquary_sentinel"),
}


def test_floor_four_route_matches_approved_twelve_node_order():
    route = get_route_spec("floor_four")

    assert tuple(
        (node.node_id, node.kind, node.encounter_id) for node in route.nodes
    ) == EXPECTED_NODES


def test_floor_four_encounters_match_approved_compositions():
    assert {
        encounter_id: get_encounter_spec(encounter_id).enemy_archetype_ids
        for encounter_id in EXPECTED_COMPOSITIONS
    } == EXPECTED_COMPOSITIONS


def test_floor_four_enemies_have_tier_three_profiles():
    expected = {
        "reliquary_sentinel": (115, (12, 15)),
        "brine_oracle": (80, (9, 10, 13)),
        "drowned_stalker": (90, (10, 14)),
        "ashbound_hound": (100, (11, 16)),
        "tidebound_curator": (300, (17, 18, 23)),
    }
    for archetype_id, (expected_hp, expected_powers) in expected.items():
        enemy = create_enemy_state(archetype_id, tier=3)
        assert enemy.tier == 3
        assert enemy.health.maximum == expected_hp
        assert enemy.combat_moves
        assert tuple(move.power for move in enemy.combat_moves) == expected_powers


def test_floor_four_grade_four_material_sources_are_authored_on_correct_enemies():
    expected = {
        "reliquary_sentinel": (
            "m8_floor_four_metal_drop_01", "grade_iv_metal", 3000
        ),
        "drowned_stalker": (
            "m8_floor_four_fiber_drop_01", "grade_iv_fiber", 3000
        ),
        "ashbound_hound": (
            "m8_floor_four_timber_drop_01", "grade_iv_timber", 3000
        ),
        "tidebound_curator": (
            "m8_floor_four_core_drop_01", "grade_iv_cores", 10000
        ),
    }

    for archetype_id, (source_id, item_id, chance_bps) in expected.items():
        drops = get_enemy_spec(archetype_id).item_drop_table_for_tier(3)
        source = next(drop for drop in drops if drop.source_id == source_id)
        assert (source.item_id, source.quantity, source.chance_bps) == (
            item_id,
            1,
            chance_bps,
        )


def test_floor_four_first_clear_grants_exactly_one_grade_four_crystal():
    assert [
        (reward.source_id, reward.floor_id, reward.item_id, reward.quantity)
        for reward in FIRST_CLEAR_REWARDS
        if reward.floor_id == "floor_four"
    ] == [
        (
            "m8_floor_four_first_clear_crystal",
            "floor_four",
            "grade_iv_magic_crystal",
            1,
        )
    ]
