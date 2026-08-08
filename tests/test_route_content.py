from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from app.content.catalog import (
    ROUTE_SPECS,
    _build_route_catalog,
    get_route_spec,
)
from app.content.route_spec import (
    EncounterSpec,
    RouteNodeKind,
    RouteNodeSpec,
    RouteSpec,
)
from app.game.encounter_manifest import SURFACE_ROUTE_MANIFEST
from app.game.overworld_route import SURFACE_ROUTE_NODES
from tools.generate_content_catalog import discover_route_ids


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SURFACE_ROUTE = (
    ("surface_goblin_solo", "Goblin Ambush", "combat", ("goblin",)),
    ("surface_goblin_pair", "Goblin Pair", "combat", ("goblin", "goblin")),
    ("surface_warrior_solo", "Goblin Warrior", "combat", ("goblin_warrior",)),
    ("surface_rest_after_warrior_solo", "Woodland Rest", "rest", None),
    (
        "surface_warrior_pair",
        "Warrior Patrol",
        "combat",
        ("goblin_warrior", "goblin_warrior"),
    ),
    ("surface_shaman_solo", "Goblin Shaman", "combat", ("goblin_shaman",)),
    (
        "surface_shaman_pair",
        "Shaman Pair",
        "combat",
        ("goblin_shaman", "goblin_shaman"),
    ),
    ("surface_rest_after_shaman_pair", "Ritual Clearing Rest", "rest", None),
    (
        "surface_elite_patrol",
        "Elite Patrol",
        "combat",
        ("goblin_elite", "goblin"),
    ),
    ("surface_rest_before_goblin_lord", "Final Approach Rest", "rest", None),
    (
        "surface_goblin_lord",
        "Goblin Lord",
        "boss",
        ("goblin_lord", "goblin", "goblin_warrior"),
    ),
    (
        "surface_dungeon_entrance",
        "Dungeon Entrance",
        "dungeon_entrance",
        None,
    ),
)


def route_values(route):
    return tuple(
        (
            node.node_id,
            node.display_label,
            node.kind.value,
            node.encounter.enemy_archetype_ids if node.encounter else None,
        )
        for node in route.nodes
    )


def test_surface_route_spec_matches_the_independent_authored_contract():
    route = get_route_spec("surface")

    assert route.route_id == "surface"
    assert route_values(route) == EXPECTED_SURFACE_ROUTE
    assert len(route.nodes) == 12
    assert sum(node.encounter is not None for node in route.nodes) == 8
    assert sum(node.kind is RouteNodeKind.REST for node in route.nodes) == 3
    assert tuple(spec.route_id for spec in ROUTE_SPECS) == ("surface",)
    assert discover_route_ids() == ("surface",)


def test_game_route_and_manifest_are_derived_without_behavioral_drift():
    route = get_route_spec("surface")

    assert tuple(
        (node.node_id, node.display_label, node.kind)
        for node in SURFACE_ROUTE_NODES
    ) == tuple(
        (node.node_id, node.display_label, node.kind)
        for node in route.nodes
    )
    assert tuple(
        node.encounter.enemy_archetype_ids if node.encounter else None
        for node in SURFACE_ROUTE_MANIFEST
    ) == tuple(
        node.encounter.enemy_archetype_ids if node.encounter else None
        for node in route.nodes
    )
    assert tuple(
        node.next_node_id for node in SURFACE_ROUTE_MANIFEST
    ) == tuple(
        route.nodes[index + 1].node_id if index + 1 < len(route.nodes) else None
        for index in range(len(route.nodes))
    )


def test_route_specs_and_nested_records_are_immutable():
    route = get_route_spec("surface")
    node = route.nodes[0]

    with pytest.raises(FrozenInstanceError):
        route.route_id = "changed"
    with pytest.raises(FrozenInstanceError):
        node.display_label = "Changed"
    with pytest.raises(FrozenInstanceError):
        node.encounter.enemy_archetype_ids = ("changed",)
    with pytest.raises(TypeError):
        route.nodes[0] = node
    with pytest.raises(TypeError):
        ROUTE_SPECS[0] = route


@pytest.mark.parametrize(
    "factory,error",
    (
        (lambda: EncounterSpec([]), TypeError),
        (lambda: EncounterSpec(()), ValueError),
        (lambda: EncounterSpec(("Bad ID",)), ValueError),
        (lambda: EncounterSpec(("goblin",) * 5), ValueError),
        (lambda: RouteNodeSpec("Bad ID", "Label", RouteNodeKind.REST), ValueError),
        (lambda: RouteNodeSpec("node", " ", RouteNodeKind.REST), ValueError),
        (lambda: RouteNodeSpec("node", "Label", "rest"), TypeError),
        (
            lambda: RouteNodeSpec("node", "Label", RouteNodeKind.COMBAT),
            ValueError,
        ),
        (
            lambda: RouteNodeSpec(
                "node",
                "Label",
                RouteNodeKind.REST,
                EncounterSpec(("goblin",)),
            ),
            ValueError,
        ),
        (lambda: RouteSpec("route", []), TypeError),
        (lambda: RouteSpec("route", ()), ValueError),
        (lambda: RouteSpec("route", (object(),)), TypeError),
    ),
)
def test_route_specs_reject_invalid_authored_values(factory, error):
    with pytest.raises(error):
        factory()


def test_route_spec_rejects_duplicate_nodes_and_invalid_dungeon_ownership():
    route = get_route_spec("surface")

    with pytest.raises(ValueError, match="node IDs must be unique"):
        replace(route, nodes=(route.nodes[0], route.nodes[0], route.nodes[-1]))
    route_without_dungeon = replace(route, nodes=route.nodes[:-1])
    assert all(
        node.kind is not RouteNodeKind.DUNGEON_ENTRANCE
        for node in route_without_dungeon.nodes
    )
    with pytest.raises(ValueError, match="dungeon entrance must be unique and final"):
        replace(
            route,
            nodes=(
                RouteNodeSpec(
                    "early_dungeon",
                    "Early Dungeon",
                    RouteNodeKind.DUNGEON_ENTRANCE,
                ),
                route.nodes[0],
                route.nodes[-1],
            ),
        )


def test_route_catalog_rejects_mismatch_duplicates_and_unknown_enemies():
    route = get_route_spec("surface")

    with pytest.raises(ValueError, match="directory ID"):
        _build_route_catalog((("wrong", route),))
    with pytest.raises(ValueError, match="duplicate route ID"):
        _build_route_catalog((("surface", route), ("surface", route)))
    with pytest.raises(ValueError, match="unknown enemy archetype"):
        _build_route_catalog((("surface", route),), enemy_catalog={})
    with pytest.raises(ValueError, match="unknown route ID"):
        get_route_spec("unknown")


def test_route_generator_rejects_directory_and_authored_id_mismatch(tmp_path):
    route_path = tmp_path / "wrong" / "route.py"
    route_path.parent.mkdir()
    route_path.write_text(
        'ROUTE = RouteSpec(route_id="authored")\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="directory ID"):
        discover_route_ids(tmp_path)


def test_game_adapters_contain_no_authored_route_or_composition_tables():
    overworld_source = (ROOT / "src/app/game/overworld_route.py").read_text(
        encoding="utf-8"
    )
    manifest_source = (ROOT / "src/app/game/encounter_manifest.py").read_text(
        encoding="utf-8"
    )

    for node_id, display_label, _kind, composition in EXPECTED_SURFACE_ROUTE:
        assert node_id not in overworld_source
        assert display_label not in overworld_source
        assert node_id not in manifest_source
        if composition:
            for archetype_id in composition:
                assert f'"{archetype_id}"' not in manifest_source


def test_generated_runtime_catalog_contains_no_route_discovery_code():
    generated_source = (
        ROOT / "src/app/content/_generated_catalog.py"
    ).read_text(encoding="utf-8")
    catalog_source = (ROOT / "src/app/content/catalog.py").read_text(encoding="utf-8")

    for source in (generated_source, catalog_source):
        assert "pathlib" not in source
        assert "pkgutil" not in source
        assert "importlib" not in source
