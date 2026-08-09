from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path

import pytest

from app.content.catalog import (
    ENCOUNTER_SPECS,
    ROUTE_SPECS,
    _build_encounter_catalog,
    _build_route_catalog,
    get_encounter_spec,
    get_encounter_rewards,
    get_enemy_spec,
    get_route_node_spec,
    get_route_spec,
    get_route_successor_id,
)
from app.content.encounter_spec import EncounterSpec
from app.content.route_spec import RouteNodeKind, RouteNodeSpec, RouteSpec
from app.game.game_state import GameState
from app.game.save_state import build_save_document, reconstruct_game_state
from app.player.player_state import PlayerState
from app.content.catalog import get_drifter_spec_by_choice as get_profile_by_choice
from tools.generate_content_catalog import (
    discover_encounter_ids,
    discover_route_ids,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SURFACE_ROUTE = (
    ("surface_goblin_solo", "Goblin Ambush", "combat", "surface_goblin_solo"),
    ("surface_goblin_pair", "Goblin Pair", "combat", "surface_goblin_pair"),
    ("surface_warrior_solo", "Goblin Warrior", "combat", "surface_warrior_solo"),
    ("surface_rest_after_warrior_solo", "Woodland Rest", "rest", None),
    (
        "surface_warrior_pair",
        "Warrior Patrol",
        "combat",
        "surface_warrior_pair",
    ),
    ("surface_shaman_solo", "Goblin Shaman", "combat", "surface_shaman_solo"),
    (
        "surface_shaman_pair",
        "Shaman Pair",
        "combat",
        "surface_shaman_pair",
    ),
    ("surface_rest_after_shaman_pair", "Ritual Clearing Rest", "rest", None),
    (
        "surface_elite_patrol",
        "Elite Patrol",
        "combat",
        "surface_elite_patrol",
    ),
    ("surface_rest_before_goblin_lord", "Final Approach Rest", "rest", None),
    (
        "surface_goblin_lord",
        "Goblin Lord",
        "boss",
        "surface_goblin_lord",
    ),
    (
        "surface_dungeon_entrance",
        "Dungeon Entrance",
        "dungeon_entrance",
        None,
    ),
)

EXPECTED_ENCOUNTERS = (
    ("surface_goblin_solo", ("goblin",)),
    ("surface_goblin_pair", ("goblin", "goblin")),
    ("surface_warrior_solo", ("goblin_warrior",)),
    ("surface_warrior_pair", ("goblin_warrior", "goblin_warrior")),
    ("surface_shaman_solo", ("goblin_shaman",)),
    ("surface_shaman_pair", ("goblin_shaman", "goblin_shaman")),
    ("surface_elite_patrol", ("goblin_elite", "goblin")),
    (
        "surface_goblin_lord",
        ("goblin_lord", "goblin", "goblin_warrior"),
    ),
)

EXPECTED_REWARDS = (
    ("surface_goblin_solo", 40, 3),
    ("surface_goblin_pair", 80, 6),
    ("surface_warrior_solo", 60, 5),
    ("surface_warrior_pair", 120, 10),
    ("surface_shaman_solo", 90, 7),
    ("surface_shaman_pair", 180, 14),
    ("surface_elite_patrol", 190, 12),
    ("surface_goblin_lord", 300, 18),
)


def route_values(route):
    return tuple(
        (
            node.node_id,
            node.display_label,
            node.kind.value,
            node.encounter_id,
        )
        for node in route.nodes
    )


def test_surface_route_spec_matches_the_independent_authored_contract():
    route = get_route_spec("surface")

    assert route.route_id == "surface"
    assert route_values(route) == EXPECTED_SURFACE_ROUTE
    assert len(route.nodes) == 12
    assert sum(node.encounter_id is not None for node in route.nodes) == 8
    assert sum(node.kind is RouteNodeKind.REST for node in route.nodes) == 3
    assert tuple(spec.route_id for spec in ROUTE_SPECS) == ("surface",)
    assert discover_route_ids() == ("surface",)


def test_eight_encounter_packages_match_the_independent_authored_contract():
    assert tuple(
        (encounter_id, get_encounter_spec(encounter_id).enemy_archetype_ids)
        for encounter_id, _composition in EXPECTED_ENCOUNTERS
    ) == EXPECTED_ENCOUNTERS
    assert {spec.encounter_id for spec in ENCOUNTER_SPECS} == {
        encounter_id for encounter_id, _composition in EXPECTED_ENCOUNTERS
    }
    assert set(discover_encounter_ids()) == {
        encounter_id for encounter_id, _composition in EXPECTED_ENCOUNTERS
    }


def test_route_order_compositions_and_successors_are_derived_without_drift():
    route = get_route_spec("surface")

    assert tuple(
        (node.node_id, node.display_label, node.kind)
        for node in route.nodes
    ) == tuple((node_id, label, RouteNodeKind(kind)) for node_id, label, kind, _ in EXPECTED_SURFACE_ROUTE)
    assert tuple(
        (
            get_encounter_spec(node.encounter_id).enemy_archetype_ids
            if node.encounter_id
            else None
        )
        for node in route.nodes
    ) == tuple(
        dict(EXPECTED_ENCOUNTERS).get(encounter_id)
        for _node_id, _label, _kind, encounter_id in EXPECTED_SURFACE_ROUTE
    )
    assert tuple(
        get_route_successor_id(node.node_id) for node in route.nodes
    ) == tuple(
        route.nodes[index + 1].node_id if index + 1 < len(route.nodes) else None
        for index in range(len(route.nodes))
    )


def test_rewards_and_boss_state_are_derived_from_canonical_content():
    route = get_route_spec("surface")
    derived = []
    for node in route.nodes:
        if node.encounter_id is None:
            continue
        encounter = get_encounter_spec(node.encounter_id)
        enemies = tuple(
            get_enemy_spec(archetype_id)
            for archetype_id in encounter.enemy_archetype_ids
        )
        derived.append(
            (
                encounter.encounter_id,
                sum(enemy.exp_reward for enemy in enemies),
                sum(enemy.gold_reward for enemy in enemies),
            )
        )

    assert tuple(derived) == EXPECTED_REWARDS
    assert tuple(
        (encounter_id, *get_encounter_rewards(encounter_id))
        for encounter_id, _exp, _gold in EXPECTED_REWARDS
    ) == EXPECTED_REWARDS
    assert sum(exp for _encounter_id, exp, _gold in derived) == 1_060
    assert sum(gold for _encounter_id, _exp, gold in derived) == 75
    assert tuple(
        node.encounter_id
        for node in route.nodes
        if node.kind is RouteNodeKind.BOSS
    ) == ("surface_goblin_lord",)


def test_route_specs_and_nested_records_are_immutable():
    route = get_route_spec("surface")
    node = route.nodes[0]

    with pytest.raises(FrozenInstanceError):
        route.route_id = "changed"
    with pytest.raises(FrozenInstanceError):
        node.display_label = "Changed"
    with pytest.raises(FrozenInstanceError):
        get_encounter_spec(node.encounter_id).enemy_archetype_ids = ("changed",)
    with pytest.raises(TypeError):
        route.nodes[0] = node
    with pytest.raises(TypeError):
        ROUTE_SPECS[0] = route
    with pytest.raises(TypeError):
        ENCOUNTER_SPECS[0] = get_encounter_spec(node.encounter_id)


@pytest.mark.parametrize(
    "factory,error",
    (
        (lambda: EncounterSpec("encounter", []), TypeError),
        (lambda: EncounterSpec("encounter", ()), ValueError),
        (lambda: EncounterSpec("Bad ID", ("goblin",)), ValueError),
        (lambda: EncounterSpec("encounter", ("Bad ID",)), ValueError),
        (lambda: EncounterSpec("encounter", ("goblin",) * 5), ValueError),
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
                "encounter",
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


def test_catalogs_reject_mismatches_duplicates_and_unknown_references():
    route = get_route_spec("surface")
    encounter = get_encounter_spec("surface_goblin_solo")

    with pytest.raises(ValueError, match="directory ID"):
        _build_encounter_catalog((("wrong", encounter),))
    with pytest.raises(ValueError, match="duplicate encounter ID"):
        _build_encounter_catalog(
            ((encounter.encounter_id, encounter),) * 2
        )
    with pytest.raises(ValueError, match="unknown enemy archetype"):
        _build_encounter_catalog(
            ((encounter.encounter_id, encounter),),
            enemy_catalog={},
        )
    with pytest.raises(ValueError, match="directory ID"):
        _build_route_catalog((("wrong", route),))
    with pytest.raises(ValueError, match="duplicate route ID"):
        _build_route_catalog((("surface", route), ("surface", route)))
    with pytest.raises(ValueError, match="unknown encounter"):
        _build_route_catalog((("surface", route),), encounter_catalog={})
    with pytest.raises(ValueError, match="unknown encounter ID"):
        get_encounter_spec("unknown")
    with pytest.raises(ValueError, match="unknown route ID"):
        get_route_spec("unknown")


def test_route_catalog_rejects_globally_duplicate_node_ids():
    route = get_route_spec("surface")
    second_route = RouteSpec(
        "second_route",
        (
            RouteNodeSpec(
                route.nodes[0].node_id,
                "Duplicate Node",
                RouteNodeKind.COMBAT,
                "surface_goblin_solo",
            ),
        ),
    )

    with pytest.raises(ValueError, match="global route node ID"):
        _build_route_catalog(
            (("surface", route), ("second_route", second_route))
        )


def test_route_generator_rejects_directory_and_authored_id_mismatch(tmp_path):
    route_path = tmp_path / "wrong" / "route.py"
    route_path.parent.mkdir()
    route_path.write_text(
        'ROUTE = RouteSpec(route_id="authored")\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="directory ID"):
        discover_route_ids(tmp_path)


def test_encounter_generator_rejects_directory_and_authored_id_mismatch(
    tmp_path,
):
    encounter_path = tmp_path / "wrong" / "encounter.py"
    encounter_path.parent.mkdir()
    encounter_path.write_text(
        'ENCOUNTER = EncounterSpec(encounter_id="authored")\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="directory ID"):
        discover_encounter_ids(tmp_path)


def test_obsolete_route_and_manifest_adapters_are_removed():
    assert not (ROOT / "src/app/game/overworld_route.py").exists()
    assert not (ROOT / "src/app/game/encounter_manifest.py").exists()


def test_required_runtime_readers_query_the_content_catalog_directly():
    paths = (
        "src/app/game/overworld_state.py",
        "src/app/game/overworld_session.py",
        "src/app/presentation/overworld_presenter.py",
        "src/app/game/save_state.py",
    )
    for relative_path in paths:
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "app.content.catalog" in source
        assert "app.game.overworld_route" not in source
        assert "app.game.encounter_manifest" not in source


def test_global_route_node_lookup_and_successors_match_authored_order():
    route = get_route_spec("surface")
    for index, node in enumerate(route.nodes):
        assert get_route_node_spec(node.node_id) is node
        assert get_route_successor_id(node.node_id) == (
            route.nodes[index + 1].node_id
            if index + 1 < len(route.nodes)
            else None
        )


def test_schema8_payload_is_byte_equivalent_after_canonical_reconstruction():
    player = PlayerState(get_profile_by_choice("1").create_character())
    document = build_save_document(GameState(player))
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":"))

    rebuilt = build_save_document(reconstruct_game_state(document))

    assert rebuilt == document
    assert json.dumps(rebuilt, sort_keys=True, separators=(",", ":")) == encoded
    assert rebuilt["schema_version"] == 8
    assert rebuilt["overworld"] == {
        "current_route_node_id": "surface_goblin_solo",
        "surface_route_begun": False,
        "dungeon_entrance_reached": False,
        "route_complete": False,
        "resolved_rest_node_ids": [],
        "current_contextual_route_phase": "enter_encounter",
    }


def test_generated_runtime_catalog_contains_no_route_discovery_code():
    generated_source = (
        ROOT / "src/app/content/_generated_catalog.py"
    ).read_text(encoding="utf-8")
    catalog_source = (ROOT / "src/app/content/catalog.py").read_text(encoding="utf-8")

    for source in (generated_source, catalog_source):
        assert "pathlib" not in source
        assert "pkgutil" not in source
        assert "importlib" not in source
