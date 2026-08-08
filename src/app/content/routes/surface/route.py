"""Authored v0.3 surface route."""

from app.content.route_spec import (
    EncounterSpec,
    RouteNodeKind,
    RouteNodeSpec,
    RouteSpec,
)


ROUTE = RouteSpec(
    route_id="surface",
    nodes=(
        RouteNodeSpec(
            "surface_goblin_solo",
            "Goblin Ambush",
            RouteNodeKind.COMBAT,
            EncounterSpec(("goblin",)),
        ),
        RouteNodeSpec(
            "surface_goblin_pair",
            "Goblin Pair",
            RouteNodeKind.COMBAT,
            EncounterSpec(("goblin", "goblin")),
        ),
        RouteNodeSpec(
            "surface_warrior_solo",
            "Goblin Warrior",
            RouteNodeKind.COMBAT,
            EncounterSpec(("goblin_warrior",)),
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
            EncounterSpec(("goblin_warrior", "goblin_warrior")),
        ),
        RouteNodeSpec(
            "surface_shaman_solo",
            "Goblin Shaman",
            RouteNodeKind.COMBAT,
            EncounterSpec(("goblin_shaman",)),
        ),
        RouteNodeSpec(
            "surface_shaman_pair",
            "Shaman Pair",
            RouteNodeKind.COMBAT,
            EncounterSpec(("goblin_shaman", "goblin_shaman")),
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
            EncounterSpec(("goblin_elite", "goblin")),
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
            EncounterSpec(("goblin_lord", "goblin", "goblin_warrior")),
        ),
        RouteNodeSpec(
            "surface_dungeon_entrance",
            "Dungeon Entrance",
            RouteNodeKind.DUNGEON_ENTRANCE,
        ),
    ),
)


__all__ = ["ROUTE"]
