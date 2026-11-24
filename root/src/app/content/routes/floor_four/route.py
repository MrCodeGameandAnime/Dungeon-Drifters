"""Authored Drowned Reliquary route."""

from app.content.route_spec import RouteNodeKind, RouteNodeSpec, RouteSpec


ROUTE = RouteSpec(
    route_id="floor_four",
    nodes=(
        RouteNodeSpec("floor_four_battle_01", "Reliquary Sentinel", RouteNodeKind.COMBAT, "m8_floor_four_encounter_01"),
        RouteNodeSpec("floor_four_battle_02", "Brine Oracle", RouteNodeKind.COMBAT, "m8_floor_four_encounter_02"),
        RouteNodeSpec("floor_four_battle_03", "Sentinel Pair", RouteNodeKind.COMBAT, "m8_floor_four_encounter_03"),
        RouteNodeSpec("floor_four_battle_04", "Crosscurrent Guard", RouteNodeKind.COMBAT, "m8_floor_four_encounter_04"),
        RouteNodeSpec("floor_four_battle_05", "Ashbound Hound", RouteNodeKind.COMBAT, "m8_floor_four_encounter_05"),
        RouteNodeSpec("floor_four_rest_midpoint", "Midpoint Rest", RouteNodeKind.REST),
        RouteNodeSpec("floor_four_battle_06", "Tidal Wardens", RouteNodeKind.COMBAT, "m8_floor_four_encounter_06"),
        RouteNodeSpec("floor_four_battle_07", "Stalker Pack", RouteNodeKind.COMBAT, "m8_floor_four_encounter_07"),
        RouteNodeSpec("floor_four_battle_08", "Reliquary Patrol", RouteNodeKind.COMBAT, "m8_floor_four_encounter_08"),
        RouteNodeSpec("floor_four_battle_09", "Oracle Pair", RouteNodeKind.COMBAT, "m8_floor_four_encounter_09"),
        RouteNodeSpec("floor_four_rest_pre_boss", "Pre-Boss Rest", RouteNodeKind.REST),
        RouteNodeSpec("floor_four_battle_10", "Tidebound Curator", RouteNodeKind.BOSS, "m8_tidebound_curator_boss"),
    ),
)


__all__ = ["ROUTE"]
