"""Authored Floor II route with two Rest checkpoints."""

from app.content.route_spec import RouteNodeKind, RouteNodeSpec, RouteSpec


ROUTE = RouteSpec(
    route_id="floor_two",
    nodes=(
        RouteNodeSpec("floor_two_battle_01", "Goblin Pair", RouteNodeKind.COMBAT, "surface_goblin_pair"),
        RouteNodeSpec("floor_two_battle_02", "Goblin Warrior", RouteNodeKind.COMBAT, "surface_warrior_solo"),
        RouteNodeSpec("floor_two_battle_03", "Goblin Patrol", RouteNodeKind.COMBAT, "dungeon_goblin_trio"),
        RouteNodeSpec("floor_two_battle_04", "Goblin Shaman", RouteNodeKind.COMBAT, "surface_shaman_solo"),
        RouteNodeSpec("floor_two_battle_05", "Cave-In Ambush", RouteNodeKind.COMBAT, "floor_two_cave_in"),
        RouteNodeSpec("floor_two_midway_rest", "Midway Rest", RouteNodeKind.REST),
        RouteNodeSpec("floor_two_battle_06", "Warrior Patrol", RouteNodeKind.COMBAT, "surface_warrior_pair"),
        RouteNodeSpec("floor_two_battle_07", "Goblin Patrol", RouteNodeKind.COMBAT, "dungeon_goblin_trio"),
        RouteNodeSpec("floor_two_battle_08", "Elite Patrol", RouteNodeKind.COMBAT, "surface_elite_patrol"),
        RouteNodeSpec("floor_two_battle_09", "Shaman Pair", RouteNodeKind.COMBAT, "surface_shaman_pair"),
        RouteNodeSpec("floor_two_pre_boss_rest", "Pre-Boss Rest", RouteNodeKind.REST),
        RouteNodeSpec("floor_two_battle_10", "Goblin Lord", RouteNodeKind.BOSS, "surface_goblin_lord"),
    ),
)


__all__ = ["ROUTE"]
