import importlib.util
from pathlib import Path


TOOL_PATH = Path(__file__).parents[1] / "tools" / "micropython_heap_sweep.py"
SPEC = importlib.util.spec_from_file_location("micropython_heap_sweep", TOOL_PATH)
heap_sweep = importlib.util.module_from_spec(SPEC)


ROUTE_NODES = (
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


def _load_tool():
    SPEC.loader.exec_module(heap_sweep)


def _successful_output():
    lines = [
        "MYP|ROUTE_CONSTRUCTION|PASS",
        "MYP|MEMORY|ROUTE_CONSTRUCTION|BEFORE|FREE|700000|ALLOC|1000",
    ]
    lines.extend("MYP|ROUTE|%s|PASS" % node for node in ROUTE_NODES)
    lines.extend(
        (
            "MYP|ROUTE_FINAL_STATE|PASS",
            "MYP|MEMORY|ROUTE_FINAL_STATE|AFTER|FREE|620512|ALLOC|404000",
            "MYP|ROUTE_EVIDENCE_RELEASE|PASS",
            "MYP|MEMORY|ROUTE_EVIDENCE_RELEASE|AFTER|FREE|700000|ALLOC|300000",
            "MYP|ROUTE_SESSION_TEARDOWN|PASS",
            "MYP|MEMORY|ROUTE_SESSION_TEARDOWN|AFTER|FREE|710000|ALLOC|200000",
            "MYP|RESULT|RAW_PROBE_STAGES_COMPLETE",
        )
    )
    return "\n".join(lines)


def test_build_command_keeps_paths_as_individual_arguments():
    _load_tool()

    command = heap_sweep.build_command(
        Path("C:/Micro Python/micropython.exe"),
        Path("C:/Dungeon Drifters/root/tools/micropython_probe_bootstrap.py"),
        Path("C:/Dungeon Drifters/root/src"),
        512,
    )

    assert command == [
        str(Path("C:/Micro Python/micropython.exe")),
        "-X",
        "heapsize=512K",
        str(
            Path(
                "C:/Dungeon Drifters/root/tools/"
                "micropython_probe_bootstrap.py"
            )
        ),
        str(Path("C:/Dungeon Drifters/root/src")),
    ]


def test_successful_output_parses_route_and_memory_evidence():
    _load_tool()

    result = heap_sweep.parse_probe_output(
        _successful_output(),
        requested_heap_kib=1024,
        returncode=0,
    )

    assert result.classification == "PASS"
    assert result.complete is True
    assert result.last_route_node == "surface_dungeon_entrance"
    assert result.lowest_free == 620512
    assert result.highest_alloc == 404000
    assert result.final_free == 620512
    assert result.final_alloc == 404000
    assert result.evidence_release_free == 700000
    assert result.evidence_release_alloc == 300000
    assert result.teardown_free == 710000
    assert result.teardown_alloc == 200000


def test_route_memory_error_is_classified_and_preserves_frontier():
    _load_tool()

    output = "\n".join(
        (
            "MYP|ROUTE|surface_goblin_solo|PASS",
            "MYP|ROUTE|surface_elite_patrol|FAIL|MemoryError|heap exhausted",
            "MYP|SURFACE_ROUTE_COMPLETE|FAIL|MemoryError|heap exhausted",
        )
    )
    result = heap_sweep.parse_probe_output(output, returncode=1)

    assert result.classification == "MEMORY_LIMIT"
    assert result.last_route_node == "surface_elite_patrol"
    assert result.failure_type == "MemoryError"
    assert result.failure_message == "heap exhausted"


def test_stage_memory_error_is_classified_before_route_traversal():
    _load_tool()

    result = heap_sweep.parse_probe_output(
        "MYP|CATALOG_IMPORT|FAIL|MemoryError|heap exhausted",
        returncode=1,
    )

    assert result.classification == "MEMORY_LIMIT"
    assert result.last_stage == "CATALOG_IMPORT"
    assert result.last_route_node is None


def test_semantic_failure_is_not_memory_limit():
    _load_tool()

    result = heap_sweep.parse_probe_output(
        "MYP|ROUTE|surface_elite_patrol|FAIL|AssertionError|wrong route",
        returncode=1,
    )

    assert result.classification == "UNEXPECTED_FAILURE"
    assert result.failure_type == "AssertionError"


def test_zero_return_without_completion_is_not_pass():
    _load_tool()

    result = heap_sweep.parse_probe_output(
        "MYP|ROUTE_FINAL_STATE|PASS",
        returncode=0,
    )

    assert result.classification == "UNEXPECTED_FAILURE"
    assert result.complete is False


def test_refinement_grid_uses_descending_32k_steps():
    _load_tool()

    assert heap_sweep.refinement_heaps(640, 512) == [608, 576, 544]


def test_repeated_results_distinguish_stable_pass_and_transition():
    _load_tool()

    assert heap_sweep.classify_repeated_results(
        ["PASS", "PASS", "PASS"]
    ) == "STABLE_PASS"
    assert heap_sweep.classify_repeated_results(
        ["PASS", "MEMORY_LIMIT", "PASS"]
    ) == "TRANSITION"


def test_machine_summary_contains_requested_heap_and_classification():
    _load_tool()

    result = heap_sweep.parse_probe_output(
        _successful_output(),
        requested_heap_kib=512,
        returncode=0,
    )

    summary = heap_sweep.format_summary("512K", result)

    assert summary.startswith("MYP19|HEAP|512K|PASS|")
    assert "FINAL_FREE|620512" in summary
    assert "FINAL_ALLOC|404000" in summary
