"""Host-side cross-runtime closure qualification for the DD raw probe."""

import argparse
import importlib.util
import subprocess
from dataclasses import dataclass
from pathlib import Path


EXPECTED_STAGES = (
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
    "ROUTE_CONSTRUCTION",
    "ROUTE_INITIAL_VIEW",
    "SURFACE_ROUTE_COMPLETE",
    "ROUTE_FINAL_STATE",
    "ROUTE_EVIDENCE_RELEASE",
    "ROUTE_SESSION_TEARDOWN",
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

COMPLETION_MARKER = "MYP|RESULT|RAW_PROBE_STAGES_COMPLETE"

CPYTHON_NATIVE = "CPYTHON_NATIVE"
CPYTHON_FORCED_OVERLAY = "CPYTHON_FORCED_OVERLAY"
MICROPYTHON_DEFAULT = "MICROPYTHON_DEFAULT"
MICROPYTHON_448K = "MICROPYTHON_448K"

_IMPLEMENTATION_PREFIX = "MYP|IMPLEMENTATION|"
_VERSION_PREFIX = "MYP|VERSION|"
_PLATFORM_PREFIX = "MYP|PLATFORM|"


class SemanticContractError(ValueError):
    """Raised when probe output violates the sealed semantic contract."""


class ToolingError(RuntimeError):
    """Raised when the host cannot execute or parse a qualification run."""


@dataclass(frozen=True)
class OutputObservation:
    implementation: object
    version: object
    platform: object
    stage_pass_sequence: tuple
    route_pass_sequence: tuple
    failure_markers: tuple
    completion_count: int
    lines: tuple

    @property
    def signature(self):
        return (
            self.stage_pass_sequence,
            self.route_pass_sequence,
            COMPLETION_MARKER,
        )


@dataclass(frozen=True)
class RuntimeResult:
    mode: str
    command: tuple
    returncode: object
    classification: str
    observation: object
    signature: object
    error: object
    stdout: str
    stderr: str


@dataclass(frozen=True)
class PressureObservation:
    classification: str
    result: object = None


def build_command(mode, python, micropython, probe, bootstrap, source):
    if mode == CPYTHON_NATIVE:
        return [str(python), str(probe), str(source)]
    if mode == CPYTHON_FORCED_OVERLAY:
        return [str(python), str(bootstrap), str(source)]
    if mode == MICROPYTHON_DEFAULT:
        return [str(micropython), str(bootstrap), str(source)]
    if mode == MICROPYTHON_448K:
        return [
            str(micropython),
            "-X",
            "heapsize=448K",
            str(bootstrap),
            str(source),
        ]
    raise ValueError("unknown qualification mode: %s" % mode)


def parse_output(stdout, stderr="", *, returncode=0):
    del returncode
    combined = "\n".join(value for value in (stdout, stderr) if value)
    lines = tuple(combined.splitlines())
    stages = []
    routes = []
    failures = []
    implementation = None
    version = None
    platform = None

    for line in lines:
        if line.startswith(_IMPLEMENTATION_PREFIX):
            implementation = line[len(_IMPLEMENTATION_PREFIX) :]
            continue
        if line.startswith(_VERSION_PREFIX):
            version = line[len(_VERSION_PREFIX) :]
            continue
        if line.startswith(_PLATFORM_PREFIX):
            platform = line[len(_PLATFORM_PREFIX) :]
            continue
        if line.startswith("MYP|ROUTE|"):
            fields = line.split("|", 4)
            if len(fields) >= 4 and fields[3] == "PASS":
                routes.append(fields[2])
            elif len(fields) == 5 and fields[3] == "FAIL":
                failures.append(line)
            continue
        fields = line.split("|", 3)
        if len(fields) == 3 and fields[0] == "MYP":
            if fields[1] != "BOOT" and fields[2] == "PASS":
                stages.append(fields[1])
            continue
        if len(fields) == 4 and fields[0] == "MYP" and fields[2] == "FAIL":
            failures.append(line)

    return OutputObservation(
        implementation=implementation,
        version=version,
        platform=platform,
        stage_pass_sequence=tuple(stages),
        route_pass_sequence=tuple(routes),
        failure_markers=tuple(failures),
        completion_count=lines.count(COMPLETION_MARKER),
        lines=lines,
    )


def validate_semantic_contract(observation, *, returncode):
    if returncode != 0:
        raise SemanticContractError(
            "probe exited with return code %s" % returncode
        )
    if observation.failure_markers:
        raise SemanticContractError(
            "probe emitted failure marker: %s" % observation.failure_markers[0]
        )
    if observation.stage_pass_sequence != tuple(EXPECTED_STAGES):
        raise SemanticContractError(
            "stage sequence mismatch: expected %s, got %s"
            % (EXPECTED_STAGES, observation.stage_pass_sequence)
        )
    if observation.route_pass_sequence != tuple(EXPECTED_ROUTE_NODES):
        raise SemanticContractError(
            "route sequence mismatch: expected %s, got %s"
            % (EXPECTED_ROUTE_NODES, observation.route_pass_sequence)
        )
    if observation.completion_count != 1:
        raise SemanticContractError(
            "expected one completion marker, got %s"
            % observation.completion_count
        )
    return observation.signature


def first_signature_difference(expected, actual):
    labels = ("stage", "route node", "completion marker")
    for part_index, label in enumerate(labels):
        expected_part = expected[part_index]
        actual_part = actual[part_index]
        if expected_part == actual_part:
            continue
        limit = min(len(expected_part), len(actual_part))
        for index in range(limit):
            if expected_part[index] != actual_part[index]:
                return "%s %s: expected %s, got %s" % (
                    label,
                    index + 1,
                    expected_part[index],
                    actual_part[index],
                )
        return "%s length: expected %s, got %s" % (
            label,
            len(expected_part),
            len(actual_part),
        )
    return None


def _expected_identity(mode):
    if mode in (CPYTHON_NATIVE, CPYTHON_FORCED_OVERLAY):
        return {"implementation": "cpython"}
    return {
        "implementation": "micropython",
        "version": "1.29.0",
        "platform": "win32",
    }


def _validate_identity(observation, mode):
    expected = _expected_identity(mode)
    for field, value in expected.items():
        if getattr(observation, field) != value:
            raise SemanticContractError(
                "%s identity mismatch: expected %s=%s, got %s"
                % (mode, field, value, getattr(observation, field))
            )


def run_runtime(mode, python, micropython, probe, bootstrap, source):
    command = build_command(mode, python, micropython, probe, bootstrap, source)
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )
    except OSError as error:
        return RuntimeResult(
            mode=mode,
            command=tuple(command),
            returncode=None,
            classification="TOOLING_FAILURE",
            observation=None,
            signature=None,
            error=str(error),
            stdout="",
            stderr="",
        )

    observation = parse_output(
        completed.stdout,
        completed.stderr,
        returncode=completed.returncode,
    )
    try:
        signature = validate_semantic_contract(
            observation,
            returncode=completed.returncode,
        )
        _validate_identity(observation, mode)
    except SemanticContractError as error:
        classification = "RUNTIME_FAILURE"
        signature = None
        message = str(error)
    else:
        classification = "PASS"
        message = None

    return RuntimeResult(
        mode=mode,
        command=tuple(command),
        returncode=completed.returncode,
        classification=classification,
        observation=observation,
        signature=signature,
        error=message,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def compare_primary_signatures(results):
    signatures = [results[mode].signature for mode in (
        CPYTHON_NATIVE,
        CPYTHON_FORCED_OVERLAY,
        MICROPYTHON_DEFAULT,
    )]
    if any(signature is None for signature in signatures):
        return False, "one or more primary runtimes did not pass"
    expected = (
        tuple(EXPECTED_STAGES),
        tuple(EXPECTED_ROUTE_NODES),
        COMPLETION_MARKER,
    )
    for signature in signatures:
        if signature != expected:
            return False, "primary runtime differs from expected contract"
    for left, right in zip(signatures, signatures[1:]):
        if left != right:
            return False, first_signature_difference(left, right)
    return True, None


def _load_heap_sweep():
    path = Path(__file__).with_name("micropython_heap_sweep.py")
    spec = importlib.util.spec_from_file_location("micropython_heap_sweep", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pressure_observation(heap_sweep, executable, bootstrap, source, heap_kib):
    result = heap_sweep.run_probe(
        executable,
        bootstrap,
        source,
        heap_kib,
    )
    if result.returncode == 0:
        if result.classification != "PASS":
            return PressureObservation("UNEXPECTED_FAILURE", result)
        try:
            observation = parse_output(
                result.stdout,
                result.stderr,
                returncode=result.returncode,
            )
            validate_semantic_contract(observation, returncode=result.returncode)
            _validate_identity(observation, MICROPYTHON_448K)
        except SemanticContractError:
            return PressureObservation("UNEXPECTED_FAILURE", result)
        return PressureObservation("PASS", result)
    if result.failure_type == "MemoryError":
        return PressureObservation("MEMORY_LIMIT", result)
    return PressureObservation("UNEXPECTED_FAILURE", result)


def classify_pressure_confirmation(heap_kib, observations):
    classifications = [value.classification for value in observations]
    if heap_kib == 448 and classifications == ["PASS"] * 3:
        return "STABLE_PASS", "3/3"
    if heap_kib == 416 and classifications == ["MEMORY_LIMIT"] * 3:
        return "MEMORY_LIMIT_CONFIRMED", "3/3"
    if heap_kib == 448:
        count = sum(value == "PASS" for value in classifications)
    else:
        count = sum(value == "MEMORY_LIMIT" for value in classifications)
    return "PRESSURE_REGRESSION", "%s/3" % count


def closure_complete(
    *,
    runtime_passed,
    semantic_parity,
    heap_448_status,
    heap_416_status,
):
    return (
        runtime_passed
        and semantic_parity
        and heap_448_status == "STABLE_PASS"
        and heap_416_status == "MEMORY_LIMIT_CONFIRMED"
    )


def _print_runtime(result):
    if result.classification == "PASS":
        observation = result.observation
        print(
            "MYP20|RUNTIME|%s|PASS|IMPLEMENTATION|%s|VERSION|%s|PLATFORM|%s"
            % (
                result.mode,
                observation.implementation,
                observation.version,
                observation.platform,
            )
        )
    else:
        print(
            "MYP20|RUNTIME|%s|%s|RETURN|%s|ERROR|%s"
            % (result.mode, result.classification, result.returncode, result.error)
        )


def _parser():
    repository_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True)
    parser.add_argument("--micropython", required=True)
    parser.add_argument(
        "--probe",
        default=str(repository_root / "tools" / "micropython_probe.py"),
    )
    parser.add_argument(
        "--bootstrap",
        default=str(repository_root / "tools" / "micropython_probe_bootstrap.py"),
    )
    parser.add_argument("--source", default=str(repository_root / "src"))
    return parser


def _run_pressure_confirmation(heap_sweep, executable, bootstrap, source, heap_kib):
    observations = [
        _pressure_observation(
            heap_sweep,
            executable,
            bootstrap,
            source,
            heap_kib,
        )
        for _ in range(3)
    ]
    status, count = classify_pressure_confirmation(heap_kib, observations)
    print("MYP20|HEAP|%sK|%s|%s" % (heap_kib, status, count))
    for index, observation in enumerate(observations, start=1):
        if observation.classification in ("PASS", "MEMORY_LIMIT"):
            continue
        result = observation.result
        print(
            "MYP20|HEAP|%sK|RUN|%s|%s|%s"
            % (
                heap_kib,
                index,
                observation.classification,
                getattr(result, "failure_message", None),
            )
        )
    return status


def main(argv=None):
    args = _parser().parse_args(argv)
    modes = (
        CPYTHON_NATIVE,
        CPYTHON_FORCED_OVERLAY,
        MICROPYTHON_DEFAULT,
        MICROPYTHON_448K,
    )
    results = {}
    for mode in modes:
        result = run_runtime(
            mode,
            args.python,
            args.micropython,
            args.probe,
            args.bootstrap,
            args.source,
        )
        results[mode] = result
        _print_runtime(result)
        if result.classification != "PASS":
            return 1

    parity, difference = compare_primary_signatures(results)
    if parity:
        print("MYP20|SEMANTIC_PARITY|PASS")
    else:
        print("MYP20|SEMANTIC_PARITY|FAIL|%s" % difference)
        return 1

    heap_sweep = _load_heap_sweep()
    heap_448_status = _run_pressure_confirmation(
        heap_sweep,
        args.micropython,
        args.bootstrap,
        args.source,
        448,
    )
    if heap_448_status != "STABLE_PASS":
        return 1

    heap_416_status = _run_pressure_confirmation(
        heap_sweep,
        args.micropython,
        args.bootstrap,
        args.source,
        416,
    )
    if heap_416_status != "MEMORY_LIMIT_CONFIRMED":
        return 1

    if closure_complete(
        runtime_passed=True,
        semantic_parity=parity,
        heap_448_status=heap_448_status,
        heap_416_status=heap_416_status,
    ):
        print("MYP20|RESULT|CLOSURE_COMPLETE")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
