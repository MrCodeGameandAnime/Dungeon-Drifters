"""Authored v0.3 surface route."""

from app.content.route_spec import RouteNodeKind, RouteNodeSpec, RouteSpec


ROUTE = RouteSpec(
    route_id="surface",
    nodes=(
        RouteNodeSpec(
            "surface_goblin_solo",
            "Goblin Ambush",
            RouteNodeKind.COMBAT,
            "surface_goblin_solo",
        ),
        RouteNodeSpec(
            "surface_goblin_pair",
            "Goblin Pair",
            RouteNodeKind.COMBAT,
            "surface_goblin_pair",
        ),
        RouteNodeSpec(
            "surface_warrior_solo",
            "Goblin Warrior",
            RouteNodeKind.COMBAT,
            "surface_warrior_solo",
        ),
        RouteNodeSpec(
            "surface_rest_after_warrior_solo",
            "Woodland Rest",
            RouteNodeKind.REST,
        ),
        RouteNodeSpec(
            "surface_warrior_pair",
            "Warrior Patrol",
            RouteNodeKind.COMBAT,
            "surface_warrior_pair",
        ),
        RouteNodeSpec(
            "surface_shaman_solo",
            "Goblin Shaman",
            RouteNodeKind.COMBAT,
            "surface_shaman_solo",
        ),
        RouteNodeSpec(
            "surface_shaman_pair",
            "Shaman Pair",
            RouteNodeKind.COMBAT,
            "surface_shaman_pair",
        ),
        RouteNodeSpec(
            "surface_rest_after_shaman_pair",
            "Ritual Clearing Rest",
            RouteNodeKind.REST,
        ),
        RouteNodeSpec(
            "surface_elite_patrol",
            "Elite Patrol",
            RouteNodeKind.COMBAT,
            "surface_elite_patrol",
        ),
        RouteNodeSpec(
            "surface_rest_before_goblin_lord",
            "Final Approach Rest",
            RouteNodeKind.REST,
        ),
        RouteNodeSpec(
            "surface_goblin_lord",
            "Goblin Lord",
            RouteNodeKind.BOSS,
            "surface_goblin_lord",
        ),
        RouteNodeSpec(
            "surface_dungeon_entrance",
            "Dungeon Entrance",
            RouteNodeKind.DUNGEON_ENTRANCE,
        ),
    ),
)


__all__ = ["ROUTE"]
