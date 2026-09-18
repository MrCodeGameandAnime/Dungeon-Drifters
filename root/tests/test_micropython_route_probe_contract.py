import ast
from pathlib import Path


PROBE_PATH = Path(__file__).parents[1] / "tools" / "micropython_probe.py"

SEALED_STAGE_PREFIX = (
    "SOURCE_PATH",
    "CATALOG_IMPORT",
    "DRIFTER_SPEC",
    "NEW_GAME",
    "FIRST_ENCOUNTER",
    "ENEMY_STATE",
    "BATTLE_CONSTRUCTION",
    "BATTLE_VIEW",
    "BATTLE_INPUT",
    "BATTLE_COMPLETE",
    "SESSION_IMPORT",
    "SESSION_CONSTRUCTION",
    "SESSION_VIEW",
    "SESSION_ENCOUNTER_ENTRY",
    "SESSION_ENCOUNTER_COMPLETE",
)

EXPECTED_ROUTE_NODES = (
    "surface_goblin_solo",
    "surface_goblin_pair",
    "surface_warrior_solo",
    "surface_rest_after_warrior_solo",
    "surface_warrior_pair",
    "surface_shaman_solo",
    "surface_shaman_pair",
    "surface_rest_after_shaman_pair",
    "surface_elite_patrol",
    "surface_rest_before_goblin_lord",
    "surface_goblin_lord",
    "surface_dungeon_entrance",
)


def _probe_source():
    return PROBE_PATH.read_text(encoding="utf-8")


def _probe_tree():
    return ast.parse(_probe_source(), filename=str(PROBE_PATH))


def _assigned_literal(tree, name):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"probe does not define {name}")


def _stage_calls(tree):
    stages = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "_run_stage":
            continue
        if not node.args or not isinstance(node.args[0], ast.Constant):
            continue
        stages.append(node.args[0].value)
    return stages


def test_probe_preserves_myp17_stage_prefix_before_route_qualification():
    stages = _stage_calls(_probe_tree())
    assert tuple(stages[: len(SEALED_STAGE_PREFIX)]) == SEALED_STAGE_PREFIX

    route_stage_index = stages.index("ROUTE_CONSTRUCTION")
    assert route_stage_index >= len(SEALED_STAGE_PREFIX)
    assert tuple(stages[route_stage_index : route_stage_index + 6]) == (
        "ROUTE_CONSTRUCTION",
        "ROUTE_INITIAL_VIEW",
        "SURFACE_ROUTE_COMPLETE",
        "ROUTE_FINAL_STATE",
        "ROUTE_EVIDENCE_RELEASE",
        "ROUTE_SESSION_TEARDOWN",
    )

    assert stages.index("ROUTE_EVIDENCE_RELEASE") > stages.index(
        "ROUTE_FINAL_STATE"
    )
    assert stages.index("ROUTE_SESSION_TEARDOWN") > stages.index(
        "ROUTE_EVIDENCE_RELEASE"
    )


def test_probe_route_contract_contains_the_authored_surface_route():
    tree = _probe_tree()
    assert _assigned_literal(tree, "_ROUTE_NODE_IDS") == EXPECTED_ROUTE_NODES
    assert len(_assigned_literal(tree, "_EXPECTED_ENCOUNTERS")) == 8
    assert len(_assigned_literal(tree, "_EXPECTED_RESTS")) == 3
    assert len(_assigned_literal(tree, "_EXPECTED_COMPOSITIONS")) == 8
    assert _assigned_literal(tree, "_EXPECTED_ENEMY_COUNT") == 14
    assert _assigned_literal(tree, "_EXPECTED_FINAL_NODE") == (
        "surface_dungeon_entrance"
    )
    assert _assigned_literal(tree, "_EXPECTED_PROGRESS") == (9, 68, 24, 75)


def test_probe_releases_route_evidence_only_after_final_state():
    source = _probe_source()

    assert source.index("def _assert_route_final_state") < source.index(
        "def _release_route_evidence"
    )
    assert source.index("def _release_route_evidence") < source.index(
        '"ROUTE_EVIDENCE_RELEASE"'
    )


def test_probe_excludes_host_persistence_and_test_dependencies():
    source = _probe_source()
    tree = _probe_tree()
    imported_modules = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_from = {
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }

    assert imported_modules.isdisjoint(
        {"pytest", "tempfile", "pathlib", "shutil"}
    )
    assert imported_from.isdisjoint(
        {"pytest", "tempfile", "pathlib", "shutil"}
    )
    assert "SaveRepository" not in source
    assert "os.walk" not in source
    assert "os.listdir" not in source
    assert "os.scandir" not in source
    assert "glob(" not in source
    assert "open(" not in source
    assert "Path(" not in source
