"""Authored dangerous Floor 1 route."""

from app.content.route_spec import RouteNodeKind, RouteNodeSpec, RouteSpec


ROUTE = RouteSpec(
    route_id="floor_one",
    nodes=(
        RouteNodeSpec("floor_one_battle_01", "Goblin Ambush", RouteNodeKind.COMBAT, "dungeon_goblin_quad"),
        RouteNodeSpec("floor_one_battle_02", "Goblin Patrol", RouteNodeKind.COMBAT, "dungeon_goblin_trio"),
        RouteNodeSpec("floor_one_battle_03", "Goblin Pair", RouteNodeKind.COMBAT, "surface_goblin_pair"),
        RouteNodeSpec("floor_one_battle_04", "Goblin Scout", RouteNodeKind.COMBAT, "surface_goblin_solo"),
        RouteNodeSpec("floor_one_battle_05", "Goblin Ambush", RouteNodeKind.COMBAT, "dungeon_goblin_quad"),
        RouteNodeSpec("floor_one_midway_rest", "Midway Rest", RouteNodeKind.REST),
        RouteNodeSpec("floor_one_battle_06", "Goblin Pair", RouteNodeKind.COMBAT, "surface_goblin_pair"),
        RouteNodeSpec("floor_one_battle_07", "Goblin Patrol", RouteNodeKind.COMBAT, "dungeon_goblin_trio"),
        RouteNodeSpec("floor_one_battle_08", "Goblin Ambush", RouteNodeKind.COMBAT, "dungeon_goblin_quad"),
        RouteNodeSpec("floor_one_battle_09", "Goblin Patrol", RouteNodeKind.COMBAT, "dungeon_goblin_trio"),
        RouteNodeSpec("floor_one_pre_boss_rest", "Pre-Boss Rest", RouteNodeKind.REST),
        RouteNodeSpec("floor_one_battle_10", "Goblin Lord", RouteNodeKind.BOSS, "surface_goblin_lord"),
    ),
)


__all__ = ["ROUTE"]
