"""Host-side constrained-heap qualification for the MicroPython probe."""

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROUTE_NODE_COUNT = 12
_MEMORY_RE = re.compile(
    r"^MYP\|MEMORY\|(.+)\|FREE\|(\d+)\|ALLOC\|(\d+)$"
)
_STAGE_PASS_RE = re.compile(r"^MYP\|([^|]+)\|PASS$")
_STAGE_FAIL_RE = re.compile(r"^MYP\|([^|]+)\|FAIL\|([^|]+)\|(.*)$")
_ROUTE_PASS_RE = re.compile(r"^MYP\|ROUTE\|([^|]+)\|PASS$")
_ROUTE_FAIL_RE = re.compile(
    r"^MYP\|ROUTE\|([^|]+)\|FAIL\|([^|]+)\|(.*)$"
)


@dataclass
class SweepResult:
    requested_heap_kib: object
    returncode: int
    classification: str
    complete: bool
    last_stage: object
    last_route_node: object
    failure_type: object
    failure_message: object
    lowest_free: object
    highest_alloc: object
    final_free: object
    final_alloc: object
    evidence_release_free: object
    evidence_release_alloc: object
    teardown_free: object
    teardown_alloc: object
    boot_free: object
    boot_alloc: object
    stdout: str
    stderr: str
    command: object = None


def build_command(executable, bootstrap, source, heap_kib=None):
    command = [str(executable)]
    if heap_kib is not None:
        command.extend(("-X", "heapsize=%sK" % heap_kib))
    command.extend((str(bootstrap), str(source)))
    return command


def _failure_from_lines(lines):
    failure_type = None
    failure_message = None
    for line in lines:
        match = _ROUTE_FAIL_RE.match(line)
        if match:
            failure_type = match.group(2)
            failure_message = match.group(3)
            continue
        match = _STAGE_FAIL_RE.match(line)
        if match:
            failure_type = match.group(2)
            failure_message = match.group(3)
    if failure_type is None:
        for line in lines:
            if "MemoryError" in line:
                failure_type = "MemoryError"
                failure_message = line.strip()
                break
    return failure_type, failure_message


def parse_probe_output(stdout, stderr="", *, requested_heap_kib=None, returncode=0):
    combined = "\n".join(value for value in (stdout, stderr) if value)
    lines = combined.splitlines()
    stage_passes = []
    last_stage = None
    route_passes = []
    last_route_node = None
    memory = {}

    for line in lines:
        match = _MEMORY_RE.match(line)
        if match:
            label = match.group(1)
            free = int(match.group(2))
            allocated = int(match.group(3))
            memory[label] = (free, allocated)
            continue

        match = _ROUTE_PASS_RE.match(line)
        if match:
            route_passes.append(match.group(1))
            last_route_node = match.group(1)
            continue

        match = _ROUTE_FAIL_RE.match(line)
        if match:
            last_route_node = match.group(1)
            continue

        match = _STAGE_PASS_RE.match(line)
        if match:
            stage_passes.append(match.group(1))
            last_stage = match.group(1)
            continue

        match = _STAGE_FAIL_RE.match(line)
        if match:
            last_stage = match.group(1)

    required_stages = {
        "ROUTE_FINAL_STATE",
        "ROUTE_EVIDENCE_RELEASE",
        "ROUTE_SESSION_TEARDOWN",
    }
    complete = (
        "MYP|RESULT|RAW_PROBE_STAGES_COMPLETE" in lines
        and required_stages.issubset(stage_passes)
        and len(set(route_passes)) == ROUTE_NODE_COUNT
    )
    failure_type, failure_message = _failure_from_lines(lines)
    if complete and returncode == 0:
        classification = "PASS"
    elif returncode != 0 and "MemoryError" in combined:
        classification = "MEMORY_LIMIT"
    else:
        classification = "UNEXPECTED_FAILURE"

    memory_values = tuple(memory.values())
    lowest_free = min((value[0] for value in memory_values), default=None)
    highest_alloc = max((value[1] for value in memory_values), default=None)

    def _memory_value(label, index):
        values = memory.get(label)
        return None if values is None else values[index]

    return SweepResult(
        requested_heap_kib=requested_heap_kib,
        returncode=returncode,
        classification=classification,
        complete=complete,
        last_stage=last_stage,
        last_route_node=last_route_node,
        failure_type=failure_type,
        failure_message=failure_message,
        lowest_free=lowest_free,
        highest_alloc=highest_alloc,
        final_free=_memory_value("ROUTE_FINAL_STATE|AFTER", 0),
        final_alloc=_memory_value("ROUTE_FINAL_STATE|AFTER", 1),
        evidence_release_free=_memory_value(
            "ROUTE_EVIDENCE_RELEASE|AFTER", 0
        ),
        evidence_release_alloc=_memory_value(
            "ROUTE_EVIDENCE_RELEASE|AFTER", 1
        ),
        teardown_free=_memory_value("ROUTE_SESSION_TEARDOWN|AFTER", 0),
        teardown_alloc=_memory_value("ROUTE_SESSION_TEARDOWN|AFTER", 1),
        boot_free=_memory_value("BOOT", 0),
        boot_alloc=_memory_value("BOOT", 1),
        stdout=stdout,
        stderr=stderr,
    )


def run_probe(executable, bootstrap, source, heap_kib=None):
    command = build_command(executable, bootstrap, source, heap_kib)
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    result = parse_probe_output(
        completed.stdout,
        completed.stderr,
        requested_heap_kib=heap_kib,
        returncode=completed.returncode,
    )
    result.command = command
    return result


def refinement_heaps(passing_heap_kib, failing_heap_kib, step_kib=32):
    return list(
        range(passing_heap_kib - step_kib, failing_heap_kib, -step_kib)
    )


def classify_repeated_results(results):
    classifications = [
        value.classification if hasattr(value, "classification") else value
        for value in results
    ]
    if classifications and all(value == "PASS" for value in classifications):
        return "STABLE_PASS"
    if "PASS" in classifications and any(
        value != "PASS" for value in classifications
    ):
        return "TRANSITION"
    if classifications and all(
        value == "MEMORY_LIMIT" for value in classifications
    ):
        return "MEMORY_LIMIT"
    return "UNEXPECTED_FAILURE"


def format_summary(label, result):
    return (
        "MYP19|HEAP|%s|%s|RETURN|%s|COMPLETE|%s|"
        "BOOT_FREE|%s|BOOT_ALLOC|%s|LOWEST_FREE|%s|"
        "HIGHEST_ALLOC|%s|FINAL_FREE|%s|FINAL_ALLOC|%s|"
        "EVIDENCE_FREE|%s|EVIDENCE_ALLOC|%s|TEARDOWN_FREE|%s|"
        "TEARDOWN_ALLOC|%s"
        % (
            label,
            result.classification,
            result.returncode,
            result.complete,
            result.boot_free,
            result.boot_alloc,
            result.lowest_free,
            result.highest_alloc,
            result.final_free,
            result.final_alloc,
            result.evidence_release_free,
            result.evidence_release_alloc,
            result.teardown_free,
            result.teardown_alloc,
        )
    )


def _parser():
    repository_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--micropython", required=True)
    parser.add_argument(
        "--bootstrap",
        default=str(repository_root / "tools" / "micropython_probe_bootstrap.py"),
    )
    parser.add_argument("--source", default=str(repository_root / "src"))
    return parser


def _print_result(label, result):
    print(format_summary(label, result))
    if result.classification == "UNEXPECTED_FAILURE":
        print(
            "MYP19|FAILURE|%s|%s|%s"
            % (label, result.failure_type, result.failure_message)
        )


def main(argv=None):
    args = _parser().parse_args(argv)
    executable = Path(args.micropython)
    bootstrap = Path(args.bootstrap)
    source = Path(args.source)

    baseline = run_probe(executable, bootstrap, source)
    _print_result("DEFAULT", baseline)
    if baseline.classification != "PASS":
        return 1

    results = {}
    control = run_probe(executable, bootstrap, source, 1024)
    results[1024] = control
    _print_result("1024K", control)
    if control.classification != "PASS":
        return 1

    for heap_kib in (896, 768, 640, 512, 384, 256):
        result = run_probe(executable, bootstrap, source, heap_kib)
        results[heap_kib] = result
        _print_result("%sK" % heap_kib, result)
        if result.classification == "UNEXPECTED_FAILURE":
            return 1

    passing = sorted(
        heap_kib
        for heap_kib, result in results.items()
        if result.classification == "PASS"
    )
    memory_limits = sorted(
        heap_kib
        for heap_kib, result in results.items()
        if result.classification == "MEMORY_LIMIT"
    )
    smallest_pass = passing[0] if passing else None
    lower_limits = [value for value in memory_limits if value < smallest_pass]
    nearest_lower = max(lower_limits) if lower_limits else None

    if smallest_pass is not None and nearest_lower is not None:
        for heap_kib in refinement_heaps(smallest_pass, nearest_lower):
            result = run_probe(executable, bootstrap, source, heap_kib)
            results[heap_kib] = result
            _print_result("%sK" % heap_kib, result)
            if result.classification == "UNEXPECTED_FAILURE":
                return 1

    passing = sorted(
        heap_kib
        for heap_kib, result in results.items()
        if result.classification == "PASS"
    )
    if not passing:
        return 1
    smallest_pass = passing[0]
    stability = [
        run_probe(executable, bootstrap, source, smallest_pass)
        for _ in range(3)
    ]
    stability_classification = classify_repeated_results(stability)
    print(
        "MYP19|STABLE_PASS|%sK|%s|%s/3"
        % (
            smallest_pass,
            stability_classification,
            sum(result.classification == "PASS" for result in stability),
        )
    )
    if stability_classification != "STABLE_PASS":
        return 1

    nearest_lower = max(
        (
            heap_kib
            for heap_kib, result in results.items()
            if heap_kib < smallest_pass
            and result.classification == "MEMORY_LIMIT"
        ),
        default=None,
    )
    if nearest_lower is not None:
        lower_stability = [
            run_probe(executable, bootstrap, source, nearest_lower)
            for _ in range(3)
        ]
        lower_classification = classify_repeated_results(lower_stability)
        print(
            "MYP19|BOUNDARY|LOWER|%sK|%s|%s/3"
            % (
                nearest_lower,
                lower_classification,
                sum(
                    result.classification == "MEMORY_LIMIT"
                    for result in lower_stability
                ),
            )
        )
        if lower_classification == "UNEXPECTED_FAILURE":
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
