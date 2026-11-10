"""Authored Floor III route with two Rest checkpoints and a full-party boss."""

from app.content.route_spec import RouteNodeKind, RouteNodeSpec, RouteSpec


ROUTE = RouteSpec(
    route_id="floor_three",
    nodes=(
        RouteNodeSpec("floor_three_battle_01", "Goblin Pair", RouteNodeKind.COMBAT, "surface_goblin_pair"),
        RouteNodeSpec("floor_three_battle_02", "Goblin Warrior", RouteNodeKind.COMBAT, "surface_warrior_solo"),
        RouteNodeSpec("floor_three_battle_03", "Goblin Patrol", RouteNodeKind.COMBAT, "dungeon_goblin_trio"),
        RouteNodeSpec("floor_three_battle_04", "Goblin Shaman", RouteNodeKind.COMBAT, "surface_shaman_solo"),
        RouteNodeSpec("floor_three_battle_05", "Elite Patrol", RouteNodeKind.COMBAT, "surface_elite_patrol"),
        RouteNodeSpec("floor_three_midway_rest", "Midway Rest", RouteNodeKind.REST),
        RouteNodeSpec("floor_three_battle_06", "Warrior Patrol", RouteNodeKind.COMBAT, "surface_warrior_pair"),
        RouteNodeSpec("floor_three_battle_07", "Goblin Squad", RouteNodeKind.COMBAT, "dungeon_goblin_quad"),
        RouteNodeSpec("floor_three_battle_08", "Elite Patrol", RouteNodeKind.COMBAT, "surface_elite_patrol"),
        RouteNodeSpec("floor_three_battle_09", "Shaman Pair", RouteNodeKind.COMBAT, "surface_shaman_pair"),
        RouteNodeSpec("floor_three_pre_boss_rest", "Pre-Boss Rest", RouteNodeKind.REST),
        RouteNodeSpec("floor_three_battle_10", "Goblin Lord", RouteNodeKind.BOSS, "surface_goblin_lord"),
    ),
)


__all__ = ["ROUTE"]
