from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

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
        "win_rate": 1.0,
        "average_turns": 4,
        "median_turns": 4,
        "average_final_hp": 80,
        "average_final_mana": 12,
        "total_super_uses": 1,
        "encounters_with_super": 1,
        "average_super_uses": 1,
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
    assert "Super uses" in report

    results = json.loads((output_dir / f"{run_id} results.json").read_text())
    saved_metadata = json.loads(
        (output_dir / f"{run_id} metadata.json").read_text()
    )
    assert results["run_id"] == run_id
    assert saved_metadata["run_id"] == run_id
    assert saved_metadata["probe_file"] == "tools/balance_probe.py"
    assert saved_metadata["working_tree_state"] == "dirty"
    assert saved_metadata["scenario_count"] == 1000
    assert saved_metadata["route_count"] == 8
    assert saved_metadata["goblin_seed_count"] == 25
    assert saved_metadata["stress_seed_count"] == 100
    assert saved_metadata["probe_version"] == "4"
    assert saved_metadata["route_policy_version"] == 2
    assert saved_metadata["super_usage_policy"] == balance_probe.SUPER_USAGE_POLICY
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


def test_failed_git_status_reports_unknown(monkeypatch):
    def fake_run(command, **_kwargs):
        if "status" in command:
            raise subprocess.CalledProcessError(1, command)
        output = "v0.2.9" if "--show-current" in command else "abc123"
        return subprocess.CompletedProcess(command, 0, stdout=output)

    monkeypatch.setattr(balance_probe.subprocess, "run", fake_run)

    assert balance_probe._git_state()["working_tree_state"] == "unknown"


def test_write_failure_leaves_no_final_or_temporary_directory(tmp_path, monkeypatch):
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
    original_write_text = Path.write_text
    writes = 0

    def fail_on_second_write(path, text, *args, **kwargs):
        nonlocal writes
        writes += 1
        if writes == 2:
            raise OSError("injected write failure")
        return original_write_text(path, text, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_on_second_write)
    with pytest.raises(OSError, match="injected write failure"):
        balance_probe.run_probe(output_root=tmp_path, now=FIXED_START)

    assert list(tmp_path.iterdir()) == []


def test_probe_uses_separate_original_seed_sets(monkeypatch):
    calls = []

    def fake_encounter(route, seed, *, stress):
        calls.append((route.label, seed, stress))
        return {
            "seed": seed,
            "won": True,
            "turns": 1,
            "final_hp": 1,
            "maximum_hp": 1,
                "final_mana": 1,
                "maximum_mana": 1,
                "super_uses": 0,
                "final_super": 0,
                "maximum_super": 100,
            }

    monkeypatch.setattr(balance_probe, "_encounter", fake_encounter)
    balance_probe.collect_results()

    assert {seed for _label, seed, stress in calls if not stress} == set(
        balance_probe.GOBLIN_SEEDS
    )
    assert {seed for _label, seed, stress in calls if stress} == set(
        balance_probe.STRESS_SEEDS
    )
    assert sum(not stress for _label, _seed, stress in calls) == 8 * 25
    assert sum(stress for _label, _seed, stress in calls) == 8 * 100
    assert len(calls) == 1000


def test_seed_corpus_and_route_registry_are_locked():
    assert balance_probe.GOBLIN_SEEDS == tuple(range(1, 25)) + (47,)
    assert balance_probe.STRESS_SEEDS == tuple(range(1, 99)) + (101, 202)
    assert len(balance_probe.ROUTES) == 8
    labels = [route.label for route in balance_probe.ROUTES]
    assert labels == [
        "Branoc Brace",
        "Azhvielle Gravemantle",
        "Azhvielle Frost",
        "Zhaivra Fire",
        "Zhaivra Poison",
        "Joruun Water",
        "Joruun Air",
        "Joruun Storm",
    ]
    assert len(set(labels)) == 8
    assert balance_probe.ROUTES[1].signature != balance_probe.ROUTES[2].signature


def test_frost_route_uses_mournglass_then_scepter_fallback():
    route = next(route for route in balance_probe.ROUTES if route.signature == "azhvielle_frost")
    ui = balance_probe.ProbeUI(route)
    enabled = SimpleNamespace(
        move_options=[SimpleNamespace(selection_key="Mournglass Bloom", enabled=True)]
    )
    disabled = SimpleNamespace(
        move_options=[SimpleNamespace(selection_key="Mournglass Bloom", enabled=False)]
    )

    assert ui._move_key(enabled) == "Mournglass Bloom"
    assert ui._move_key(disabled) == "Scepter Sweep"
    assert "Gravemantle Rupture" not in route.label


def test_super_action_priority_and_super_move_validation():
    route = balance_probe.ROUTES[0]
    ui = balance_probe.ProbeUI(route)

    enabled_super = SimpleNamespace(
        super_meter=SimpleNamespace(activation_offered=True)
    )
    disabled_super = SimpleNamespace(
        super_meter=SimpleNamespace(activation_offered=False)
    )
    assert ui._action_input(enabled_super) == balance_probe.ChooseAction(
        balance_probe.ActionIntent.SUPER
    )
    assert ui._action_input(disabled_super) == balance_probe.ChooseAction(
        balance_probe.ActionIntent.ATTACK
    )

    ui.stage = "braced"
    super_view = SimpleNamespace(
        interaction_phase=balance_probe.InteractionPhase.SUPER_MOVES,
        move_options=(SimpleNamespace(selection_key="Third Gate Obsequy", enabled=True),),
    )
    assert ui.read_input(super_view) == balance_probe.ChooseMove("Third Gate Obsequy")
    assert ui.stage == "braced"
    with pytest.raises(RuntimeError):
        ui.read_input(
            SimpleNamespace(
                interaction_phase=balance_probe.InteractionPhase.SUPER_MOVES,
                move_options=(),
            )
        )

    zhaivra = next(route for route in balance_probe.ROUTES if route.signature == "zhaivra")
    zhaivra_ui = balance_probe.ProbeUI(zhaivra)
    assert zhaivra_ui._action_input(enabled_super) == balance_probe.ChooseAction(
        balance_probe.ActionIntent.ITEMS
    )
    zhaivra_ui.stage = "prepared"
    assert zhaivra_ui._action_input(enabled_super) == balance_probe.ChooseAction(
        balance_probe.ActionIntent.SUPER
    )


def test_super_aggregate_metrics_use_accepted_encounter_counts():
    route = balance_probe.ROUTES[0]
    encounters = [
        {
            "seed": 1,
            "won": True,
            "turns": 4,
            "final_hp": 80,
            "maximum_hp": 100,
            "final_mana": 10,
            "maximum_mana": 20,
            "super_uses": 1,
            "final_super": 0,
            "maximum_super": 100,
        },
        {
            "seed": 2,
            "won": False,
            "turns": 6,
            "final_hp": 0,
            "maximum_hp": 100,
            "final_mana": 5,
            "maximum_mana": 20,
            "super_uses": 0,
            "final_super": 30,
            "maximum_super": 100,
        },
    ]

    aggregate = balance_probe._aggregate(route, "goblin", (1, 2), encounters)

    assert aggregate["total_super_uses"] == 1
    assert aggregate["encounters_with_super"] == 1
    assert aggregate["average_super_uses"] == 0.5


def test_snapshot_metadata_and_report_are_versioned():
    metadata = {
        "run_id": "test",
        "started_at": FIXED_START.isoformat(),
        "branch": "v0.2.9",
        "commit_sha": "test",
        "working_tree_state": "clean",
        "python_version": "test",
        "probe_version": "4",
        "snapshot_id": "m9-pre-progression",
        "snapshot_label": "M9 base roster before XP, leveling, and skill trees",
        "seed_corpus_version": 1,
        "route_policy_version": 2,
        "goblin_seeds": list(balance_probe.GOBLIN_SEEDS),
        "stress_seeds": list(balance_probe.STRESS_SEEDS),
        "route_count": 8,
        "goblin_seed_count": 25,
        "stress_seed_count": 100,
        "scenario_count": 1000,
        "super_usage_policy": balance_probe.SUPER_USAGE_POLICY,
        "route_policies": [
            {"label": route.label, "version": 1} for route in balance_probe.ROUTES
        ],
    }
    report = balance_probe.render_report(_fake_results(), metadata)

    assert "Azhvielle Frost" in report
    assert "Win rate" in report
    assert "Median turns" in report
    assert "m9-pre-progression" in report
    assert "Seed corpus version" in report
    assert "Route policy version" in report


def test_report_fixture_renders_both_tables():
    results = _fake_results()
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
            "probe_version": "4",
            "snapshot_id": "m9-pre-progression",
            "snapshot_label": "M9 base roster before XP, leveling, and skill trees",
            "seed_corpus_version": 1,
            "route_policy_version": 2,
            "goblin_seeds": list(balance_probe.GOBLIN_SEEDS),
            "stress_seeds": list(balance_probe.STRESS_SEEDS),
            "route_count": 8,
            "goblin_seed_count": 25,
            "stress_seed_count": 100,
            "scenario_count": 1000,
            "super_usage_policy": balance_probe.SUPER_USAGE_POLICY,
            "route_policies": [
                {"label": route.label, "version": 1} for route in balance_probe.ROUTES
            ],
            "output_directory": "test",
        },
    )
    assert len(results["goblin_results"]) == 1
    assert len(results["stress_results"]) == 1
    assert "| Test |" in report
    assert "- Joruun Storm (v1)" in report
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
