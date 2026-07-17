from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


TOOL_PATH = Path(__file__).parents[1] / "tools" / "balance_probe.py"
SPEC = importlib.util.spec_from_file_location("balance_probe", TOOL_PATH)
balance_probe = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["balance_probe"] = balance_probe
SPEC.loader.exec_module(balance_probe)


FIXED_START = datetime(2026, 7, 17, 13, 42, 8, tzinfo=timezone(timedelta(hours=-4)))


def _fake_results():
    encounter = {
        "seed": 11,
        "won": True,
        "turns": 4,
        "final_hp": 80,
        "maximum_hp": 100,
        "final_mana": 12,
        "maximum_mana": 20,
    }
    aggregate = {
        "character": "Test",
        "path": "Test",
        "enemy": "Goblin",
        "encounter_type": "goblin",
        "seeds": [11],
        "wins": 1,
        "attempts": 1,
        "average_turns": 4,
        "average_final_hp": 80,
        "maximum_hp": 100,
        "encounters": [encounter],
    }
    return {"goblin_results": [aggregate], "stress_results": [aggregate]}


def test_run_id_is_reused_for_directory_and_all_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(balance_probe, "collect_results", _fake_results)
    monkeypatch.setattr(
        balance_probe,
        "_git_state",
        lambda: {
            "branch": "v0.2.9",
            "commit_sha": "abc123",
            "working_tree_state": "dirty",
            "tracked_changes": [" M tests/example.py"],
            "untracked_files": ["notes.txt"],
        },
    )

    run_id, _results, metadata, output_dir = balance_probe.run_probe(
        output_root=tmp_path, now=FIXED_START
    )

    assert run_id == "2026-07-17_13-42-08"
    assert output_dir == tmp_path / run_id
    assert sorted(path.name for path in output_dir.iterdir()) == [
        f"{run_id} metadata.json",
        f"{run_id} report.md",
        f"{run_id} results.json",
    ]
    report = (output_dir / f"{run_id} report.md").read_text(encoding="utf-8")
    assert "# Dungeon Drifters Balance Probe" in report
    assert "## Goblin Results" in report
    assert "## 300-HP Stress Results" in report
    assert "| Character/path | Wins | Avg turns | Avg final HP |" in report

    results = json.loads((output_dir / f"{run_id} results.json").read_text())
    saved_metadata = json.loads(
        (output_dir / f"{run_id} metadata.json").read_text()
    )
    assert results["run_id"] == run_id
    assert saved_metadata["run_id"] == run_id
    assert saved_metadata["probe_file"] == "tools/balance_probe.py"
    assert saved_metadata["working_tree_state"] == "dirty"
    assert "balance_probe_outputs" not in " ".join(
        saved_metadata["untracked_files"]
    )
    parsed_started = datetime.fromisoformat(saved_metadata["started_at"])
    assert parsed_started.utcoffset() is not None
    assert metadata == saved_metadata


def test_default_output_root_is_under_tools():
    assert balance_probe.OUTPUT_ROOT == TOOL_PATH.parent / "balance_probe_outputs"


def test_runs_with_different_timestamps_do_not_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(balance_probe, "collect_results", _fake_results)
    monkeypatch.setattr(
        balance_probe,
        "_git_state",
        lambda: {
            "branch": "v0.2.9",
            "commit_sha": "abc123",
            "working_tree_state": "clean",
            "tracked_changes": [],
            "untracked_files": [],
        },
    )

    first = balance_probe.run_probe(output_root=tmp_path, now=FIXED_START)
    second = balance_probe.run_probe(
        output_root=tmp_path, now=FIXED_START + timedelta(seconds=1)
    )

    assert first[0] != second[0]
    assert first[3].is_dir()
    assert second[3].is_dir()


def test_real_probe_scenarios_render_both_tables():
    results = balance_probe.collect_results()
    report = balance_probe.render_report(
        results,
        {
            "run_id": "test",
            "started_at": FIXED_START.isoformat(),
            "completed_at": FIXED_START.isoformat(),
            "branch": "test",
            "commit_sha": "test",
            "working_tree_state": "clean",
            "python_version": "test",
            "probe_file": "tools/balance_probe.py",
            "probe_version": "1",
            "seeds": list(balance_probe.SEEDS),
            "scenario_count": 42,
            "output_directory": "test",
        },
    )
    assert len(results["goblin_results"]) == 7
    assert len(results["stress_results"]) == 7
    assert "| Branoc |" in report
    assert "| Joruun Storm |" in report
    assert "## Goblin Results" in report
    assert "## 300-HP Stress Results" in report


def test_pytest_collection_excludes_permanent_probe():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=TOOL_PATH.parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "tools/balance_probe.py" not in result.stdout
