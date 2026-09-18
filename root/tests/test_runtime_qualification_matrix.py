import importlib.util
from pathlib import Path

import pytest


TOOL_PATH = Path(__file__).parents[1] / "tools" / "runtime_qualification_matrix.py"
SPEC = importlib.util.spec_from_file_location(
    "runtime_qualification_matrix", TOOL_PATH
)
matrix = importlib.util.module_from_spec(SPEC)


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
    SPEC.loader.exec_module(matrix)


def _successful_output(
    *,
    implementation="cpython",
    version="3.13.0",
    platform="win32",
):
    _load_tool()
    lines = [
        "MYP|IMPLEMENTATION|%s" % implementation,
        "MYP|VERSION|%s" % version,
        "MYP|PLATFORM|%s" % platform,
    ]
    lines.extend("MYP|%s|PASS" % stage for stage in matrix.EXPECTED_STAGES)
    lines.extend("MYP|ROUTE|%s|PASS" % node for node in ROUTE_NODES)
    lines.extend(
        (
            "MYP|MEMORY|ROUTE_FINAL_STATE|AFTER|FREE|620512|ALLOC|404000",
            "MYP|RESULT|RAW_PROBE_STAGES_COMPLETE",
        )
    )
    return "\n".join(lines)


def test_build_command_uses_exact_runtime_argv_shapes_and_preserves_spaces():
    _load_tool()
    python = Path("C:/Python Install/python.exe")
    micropython = Path("C:/Micro Python/micropython.exe")
    probe = Path("C:/Dungeon Drifters/root/tools/micropython_probe.py")
    bootstrap = Path(
        "C:/Dungeon Drifters/root/tools/micropython_probe_bootstrap.py"
    )
    source = Path("C:/Dungeon Drifters/root/src")

    assert matrix.build_command(
        "CPYTHON_NATIVE", python, micropython, probe, bootstrap, source
    ) == [str(python), str(probe), str(source)]
    assert matrix.build_command(
        "CPYTHON_FORCED_OVERLAY", python, micropython, probe, bootstrap, source
    ) == [str(python), str(bootstrap), str(source)]
    assert matrix.build_command(
        "MICROPYTHON_DEFAULT", python, micropython, probe, bootstrap, source
    ) == [str(micropython), str(bootstrap), str(source)]
    assert matrix.build_command(
        "MICROPYTHON_448K", python, micropython, probe, bootstrap, source
    ) == [
        str(micropython),
        "-X",
        "heapsize=448K",
        str(bootstrap),
        str(source),
    ]


def test_complete_output_extracts_expected_semantic_signature():
    _load_tool()

    observation = matrix.parse_output(_successful_output(), returncode=0)

    assert matrix.validate_semantic_contract(observation, returncode=0) == (
        tuple(matrix.EXPECTED_STAGES),
        ROUTE_NODES,
        matrix.COMPLETION_MARKER,
    )


def test_memory_and_runtime_identity_lines_do_not_change_signature():
    _load_tool()
    first = _successful_output()
    second = first.replace("cpython", "micropython")
    second = second.replace("3.13.0", "1.29.0")
    second = second.replace("620512|ALLOC|404000", "1|ALLOC|999999")

    first_signature = matrix.validate_semantic_contract(
        matrix.parse_output(first, returncode=0), returncode=0
    )
    second_signature = matrix.validate_semantic_contract(
        matrix.parse_output(second, returncode=0), returncode=0
    )

    assert first_signature == second_signature


def test_missing_stage_fails_contract():
    _load_tool()
    lines = _successful_output().splitlines()
    lines.remove("MYP|ROUTE_EVIDENCE_RELEASE|PASS")

    with pytest.raises(matrix.SemanticContractError):
        matrix.validate_semantic_contract(
            matrix.parse_output("\n".join(lines), returncode=0), returncode=0
        )


def test_out_of_order_stage_fails_contract():
    _load_tool()
    lines = _successful_output().splitlines()
    first = lines.index("MYP|ROUTE_FINAL_STATE|PASS")
    second = lines.index("MYP|ROUTE_EVIDENCE_RELEASE|PASS")
    lines[first], lines[second] = lines[second], lines[first]

    with pytest.raises(matrix.SemanticContractError):
        matrix.validate_semantic_contract(
            matrix.parse_output("\n".join(lines), returncode=0), returncode=0
        )


def test_missing_route_node_fails_contract():
    _load_tool()
    lines = _successful_output().splitlines()
    lines.remove("MYP|ROUTE|surface_shaman_pair|PASS")

    with pytest.raises(matrix.SemanticContractError):
        matrix.validate_semantic_contract(
            matrix.parse_output("\n".join(lines), returncode=0), returncode=0
        )


def test_duplicate_completion_marker_fails_contract():
    _load_tool()
    output = _successful_output() + "\n" + matrix.COMPLETION_MARKER

    with pytest.raises(matrix.SemanticContractError):
        matrix.validate_semantic_contract(
            matrix.parse_output(output, returncode=0), returncode=0
        )


def test_fail_marker_fails_even_when_process_exit_code_is_zero():
    _load_tool()
    output = _successful_output() + "\nMYP|ROUTE|surface_goblin_solo|FAIL|AssertionError|bad"

    with pytest.raises(matrix.SemanticContractError):
        matrix.validate_semantic_contract(
            matrix.parse_output(output, returncode=0), returncode=0
        )


def test_first_signature_difference_reports_stage_or_route_position():
    _load_tool()
    expected = matrix.parse_output(_successful_output(), returncode=0)
    broken_output = _successful_output().replace(
        "surface_shaman_pair", "surface_wrong"
    )
    actual = matrix.parse_output(broken_output, returncode=0)

    difference = matrix.first_signature_difference(
        matrix.validate_semantic_contract(expected, returncode=0),
        actual.signature,
    )

    assert difference == "route node 7: expected surface_shaman_pair, got surface_wrong"


def test_448k_confirmation_requires_three_passes():
    _load_tool()
    results = [matrix.PressureObservation("PASS") for _ in range(3)]

    assert matrix.classify_pressure_confirmation(448, results) == (
        "STABLE_PASS",
        "3/3",
    )


def test_448k_instability_is_pressure_regression():
    _load_tool()
    results = [
        matrix.PressureObservation("PASS"),
        matrix.PressureObservation("MEMORY_LIMIT"),
        matrix.PressureObservation("PASS"),
    ]

    assert matrix.classify_pressure_confirmation(448, results) == (
        "PRESSURE_REGRESSION",
        "2/3",
    )


def test_416k_requires_three_memory_limits():
    _load_tool()
    results = [matrix.PressureObservation("MEMORY_LIMIT") for _ in range(3)]

    assert matrix.classify_pressure_confirmation(416, results) == (
        "MEMORY_LIMIT_CONFIRMED",
        "3/3",
    )


def test_416k_success_is_pressure_regression():
    _load_tool()
    results = [
        matrix.PressureObservation("MEMORY_LIMIT"),
        matrix.PressureObservation("PASS"),
        matrix.PressureObservation("MEMORY_LIMIT"),
    ]

    assert matrix.classify_pressure_confirmation(416, results) == (
        "PRESSURE_REGRESSION",
        "2/3",
    )


def test_only_complete_matrix_can_emit_closure_result():
    _load_tool()
    assert matrix.closure_complete(
        runtime_passed=True,
        semantic_parity=True,
        heap_448_status="STABLE_PASS",
        heap_416_status="MEMORY_LIMIT_CONFIRMED",
    ) is True
    assert matrix.closure_complete(
        runtime_passed=True,
        semantic_parity=False,
        heap_448_status="STABLE_PASS",
        heap_416_status="MEMORY_LIMIT_CONFIRMED",
    ) is False
