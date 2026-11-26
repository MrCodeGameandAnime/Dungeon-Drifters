"""Hub-launched, standalone four-Drifter Floor V reunion encounter."""

from app.content.route_spec import RouteNodeKind, RouteNodeSpec, RouteSpec


ROUTE = RouteSpec(
    route_id="floor_five_reunion",
    nodes=(
        RouteNodeSpec(
            "floor_five_reunion_battle_01",
            "Ashen Regent",
            RouteNodeKind.BOSS,
            "m8_ashen_regent_boss",
        ),
    ),
)

__all__ = ["ROUTE"]
