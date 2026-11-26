"""Authored paired approach through the Ashen Vault."""

from app.content.route_spec import RouteNodeKind, RouteNodeSpec, RouteSpec


ROUTE = RouteSpec(
    route_id="floor_five_approach",
    nodes=(
        RouteNodeSpec(
            "floor_five_battle_01",
            "Hound and Stalker",
            RouteNodeKind.COMBAT,
            "m8_floor_five_encounter_01",
        ),
        RouteNodeSpec(
            "floor_five_battle_02",
            "Oracle and Hound",
            RouteNodeKind.COMBAT,
            "m8_floor_five_encounter_02",
        ),
        RouteNodeSpec(
            "floor_five_battle_03",
            "Sentinel Pair",
            RouteNodeKind.COMBAT,
            "m8_floor_five_encounter_03",
        ),
        RouteNodeSpec(
            "floor_five_rest_midpoint",
            "Midpoint Rest",
            RouteNodeKind.REST,
        ),
        RouteNodeSpec(
            "floor_five_battle_04",
            "Hound Pair",
            RouteNodeKind.COMBAT,
            "m8_floor_five_encounter_04",
        ),
        RouteNodeSpec(
            "floor_five_battle_05",
            "Vault Guard and Oracle",
            RouteNodeKind.COMBAT,
            "m8_floor_five_encounter_05",
        ),
        RouteNodeSpec(
            "floor_five_battle_06",
            "Vault Watchers",
            RouteNodeKind.COMBAT,
            "m8_floor_five_encounter_06",
        ),
    ),
)


__all__ = ["ROUTE"]
