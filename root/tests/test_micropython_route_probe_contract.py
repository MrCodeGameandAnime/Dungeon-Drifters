import ast
from runpy import run_path
from types import SimpleNamespace
from pathlib import Path

import pytest


PROBE_PATH = Path(__file__).parents[1] / "tools" / "micropython_probe.py"
HUB_PROBE_PATH = (
    Path(__file__).parents[1] / "tools" / "micropython_hub_probe.py"
)

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


def _hub_probe_source():
    return HUB_PROBE_PATH.read_text(encoding="utf-8")


def _hub_probe_tree():
    return ast.parse(_hub_probe_source(), filename=str(HUB_PROBE_PATH))


def _assigned_literal(tree, name):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"probe does not define {name}")


def _stage_calls(tree, function_name="_run_stage"):
    stages = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != function_name:
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
    assert _assigned_literal(tree, "_EXPECTED_PROGRESS") == (9, 68, 24, 0)


def test_probe_runs_the_full_hub_tutorial_after_surface_route():
    hub_stages = _stage_calls(_hub_probe_tree(), "run_stage")
    assert tuple(hub_stages) == (
        "HUB_RECRUITMENT",
        "HUB_READY",
        "HUB_TUTORIAL_BATTLE",
        "HUB_EXTRACTION",
        "HUB_RETURN",
        "HUB_FINAL_STATE",
    )

    source = _probe_source()
    route_final = source.index('_run_stage("ROUTE_FINAL_STATE"')
    hub_run = source.index("_run_hub_tutorial()", route_final)
    evidence_release = source.index('_run_stage("ROUTE_EVIDENCE_RELEASE"')
    assert route_final < evidence_release < hub_run
    live_state_assert = source.index("_assert_route_live_state()", hub_run)
    assert hub_run < live_state_assert


@pytest.mark.parametrize(
    "retained_evidence",
    ("compositions", "enemies", "initial_view", "completion_count"),
)
def test_hub_probe_rejects_retained_surface_route_evidence(retained_evidence):
    recruit_companion = run_path(str(HUB_PROBE_PATH))[
        "_recruit_companion"
    ]
    state = {
        "route_battle_factory": SimpleNamespace(
            battle_compositions=[],
            completed_count=0,
        ),
        "route_enemy_factory": SimpleNamespace(enemies=[]),
    }
    if retained_evidence == "compositions":
        state["route_battle_factory"].battle_compositions.append(("goblin",))
    elif retained_evidence == "enemies":
        state["route_enemy_factory"].enemies.append(object())
    elif retained_evidence == "initial_view":
        state["route_initial_view"] = object()
    else:
        state["route_battle_factory"].completed_count = 8

    with pytest.raises(AssertionError, match="route evidence.*retained"):
        recruit_companion(state)


def test_probe_records_battle_summaries_without_retaining_completed_battles():
    source = _probe_source()
    factory = source[
        source.index("class _RouteBattleFactory:") : source.index(
            "class _RouteEnemyFactory:"
        )
    ]

    assert "self.battle_compositions = []" in factory
    assert "self.completed_count = 0" in factory
    assert "self.battles.append(battle)" not in factory
    assert "party=()" in factory
    assert "party=party" in factory


def test_probe_releases_route_evidence_only_after_final_state():
    source = _probe_source()

    assert source.index("def _assert_route_final_state") < source.index(
        "def _release_route_evidence"
    )
    assert source.index("def _release_route_evidence") < source.index(
        '"ROUTE_EVIDENCE_RELEASE"'
    )


def test_memory_error_dumps_heap_map_before_logging_or_collection():
    tree = _probe_tree()
    runner = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_run_stage"
    )
    error_handler = next(
        handler
        for node in ast.walk(runner)
        if isinstance(node, ast.Try)
        for handler in node.handlers
    )
    first_statement = error_handler.body[0]

    assert isinstance(first_statement, ast.Expr)
    assert isinstance(first_statement.value, ast.Call)
    assert isinstance(first_statement.value.func, ast.Name)
    assert first_statement.value.func.id == "_emit_heap_map_on_memory_error"
    assert isinstance(first_statement.value.args[0], ast.Name)
    assert first_statement.value.args[0].id == "error"

    helper = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_emit_heap_map_on_memory_error"
    )
    heap_map_call = next(
        node
        for node in ast.walk(helper)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "mem_info"
    )
    assert ast.literal_eval(heap_map_call.args[0]) == 1


def test_completed_first_battle_evidence_is_released_before_session_import():
    source = _probe_source()
    main_body = source[source.index("def main():") : source.rindex("main()")]
    helper_start = source.index("def _release_first_battle_evidence():")
    helper_end = source.index("\ndef _import_overworld_session():", helper_start)
    helper = source[helper_start:helper_end]
    session_constructor_start = source.index("def _construct_headless_session():")
    session_constructor_end = source.index(
        "\ndef _obtain_session_view():", session_constructor_start
    )
    session_constructor = source[session_constructor_start:session_constructor_end]
    session_completion_start = source.index(
        "def _complete_first_session_encounter():"
    )
    session_completion_end = source.index(
        "\ndef _construct_route_qualification():", session_completion_start
    )
    session_completion = source[session_completion_start:session_completion_end]

    assert main_body.index('"BATTLE_COMPLETE"') < main_body.index(
        "_release_first_battle_evidence()"
    ) < main_body.index('"SESSION_IMPORT"')
    assert 'STATE["battle_factory_type"] = STATE["battle"].__class__' in helper
    assert 'del STATE["battle_view"]' in helper
    assert 'del STATE["enemies"]' in helper
    assert 'del STATE["battle"]' in helper
    assert 'del STATE["game"]' in helper
    assert "gc.collect()" in helper
    assert 'STATE["battle_factory_type"]' in session_constructor
    assert 'from app.game.new_game import create_new_game' in session_constructor
    assert 'game = create_new_game("branoc")' in session_constructor
    assert 'STATE["session_game"] = game' in session_constructor
    assert 'STATE["battle"]' not in session_constructor
    assert 'STATE["session_game"].world_state.defeated_encounters' in (
        session_completion
    )


def test_probe_excludes_host_persistence_and_test_dependencies():
    source = _probe_source() + _hub_probe_source()
    tree = ast.parse(source)
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
    assert "SaveCoordinator" not in source
    assert "build_default_save_port" not in source
    assert "os.walk" not in source
    assert "os.listdir" not in source
    assert "os.scandir" not in source
    assert "glob(" not in source
    assert "open(" not in source
    assert "Path(" not in source
