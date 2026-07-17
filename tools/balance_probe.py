"""Opt-in seeded balance probe with persistent Markdown and JSON artifacts."""

from __future__ import annotations

import json
import platform
import random
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from app.combat.battle import Battle
from app.combat.battle import random as battle_random
from app.combat.resolver import CombatResolver
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.player.character import BlackMage, Brawler, Monk, RogueArcher
from app.player.player_state import PlayerState
from app.presentation.battle_models import ActionIntent, BattleEventType, InteractionPhase
from app.presentation.battle_session import BattlePresentationSession
from app.ui.battle_ui import (
    ChooseAction,
    ChooseInventoryCommand,
    ChooseInventoryCompanion,
    ChooseInventoryItem,
    ChooseMove,
    ConfirmInventoryUse,
)
from app.player.run_items import InventoryCommand


PROBE_VERSION = "1"
SEEDS = (11, 23, 47)
STRESS_HP = 300
OUTPUT_ROOT = REPOSITORY_ROOT / "tools" / "balance_probe_outputs"


@dataclass(frozen=True)
class Route:
    label: str
    character_type: type
    signature: str
    infusion_item: str | None = None
    infusion_companion: str | None = None


ROUTES = (
    Route("Branoc", Brawler, "branoc"),
    Route("Azhvielle", BlackMage, "azhvielle"),
    Route("Zhaivra Fire", RogueArcher, "zhaivra", "ember_shard", "deep_coal"),
    Route("Zhaivra Poison", RogueArcher, "zhaivra", "deep_coal", "night_berry"),
    Route("Joruun Water", Monk, "water"),
    Route("Joruun Air", Monk, "air"),
    Route("Joruun Storm", Monk, "storm"),
)


class RecordingSession(BattlePresentationSession):
    def __init__(self):
        super().__init__()
        self.history = []

    def record(self, entry):
        self.history.append(entry)
        super().record(entry)


class ProbeUI:
    def __init__(self, route):
        self.route = route
        self.stage = "start"
        self.inputs = 0

    def render(self, _view):
        return None

    def read_input(self, view):
        self.inputs += 1
        if self.inputs > 400:
            raise RuntimeError(f"probe did not terminate: {self.route.label}")
        if view.interaction_phase == InteractionPhase.ACTIONS:
            return self._action_input()
        if view.interaction_phase == InteractionPhase.REGULAR_MOVES:
            return ChooseMove(self._move_key(view))
        if view.interaction_phase == InteractionPhase.INVENTORY:
            return ChooseInventoryItem(self.route.infusion_item)
        if view.interaction_phase == InteractionPhase.INVENTORY_ITEM:
            return ChooseInventoryCommand(InventoryCommand.USE)
        if view.interaction_phase == InteractionPhase.INVENTORY_COMBINATION:
            return ChooseInventoryCompanion(self.route.infusion_companion)
        if view.interaction_phase == InteractionPhase.INVENTORY_CONFIRMATION:
            self.stage = "prepared"
            return ConfirmInventoryUse(True)
        raise RuntimeError(f"unexpected probe phase: {view.interaction_phase}")

    def _action_input(self):
        if self.route.signature == "zhaivra" and self.stage == "start":
            self.stage = "inventory"
            return ChooseAction(ActionIntent.ITEMS)
        return ChooseAction(ActionIntent.ATTACK)

    def _move_key(self, view):
        offered = {option.selection_key: option for option in view.move_options}

        if self.route.signature == "branoc":
            if self.stage == "start" and "Brace" in offered:
                self.stage = "braced"
                return "Brace"
            if self.stage == "braced" and "Ironwake Dismemberment" in offered:
                self.stage = "answered"
                return "Ironwake Dismemberment"
            return "Crestgrave Reaping"

        if self.route.signature == "azhvielle":
            if "Gravemantle Rupture" in offered and offered["Gravemantle Rupture"].enabled:
                return "Gravemantle Rupture"
            if "Gloamweight Sepulcher" in offered and offered["Gloamweight Sepulcher"].enabled:
                return "Gloamweight Sepulcher"
            return "Scepter Sweep"

        if self.route.signature == "zhaivra":
            if self.stage == "prepared" and "Infused Barb" in offered:
                self.stage = "fired"
                return "Infused Barb"
            return "Mournpoint Verdict"

        if self.route.signature == "water":
            if self.stage == "start" and "Hydro Whip" in offered:
                self.stage = "water_ready"
                return "Hydro Whip"
            if self.stage == "water_ready" and "Lightning Palm" in offered:
                self.stage = "finished_setup"
                return "Lightning Palm"
            return "Bring the Horse to Water"

        if self.route.signature == "air":
            if self.stage == "start" and "Tempest Surge" in offered:
                self.stage = "air_ready"
                return "Tempest Surge"
            if self.stage == "air_ready" and "Lightning Palm" in offered:
                self.stage = "finished_setup"
                return "Lightning Palm"
            return "Bring the Horse to Water"

        if self.route.signature == "storm":
            if self.stage == "start" and "Hydro Whip" in offered:
                self.stage = "water_ready"
                return "Hydro Whip"
            if self.stage == "water_ready" and "Tempest Surge" in offered:
                self.stage = "storm_ready"
                return "Tempest Surge"
            if self.stage == "storm_ready" and "Lightning Palm" in offered:
                self.stage = "finished_setup"
                return "Lightning Palm"
            return "Bring the Horse to Water"

        raise RuntimeError(f"unknown probe route: {self.route.signature}")


def _encounter(route, seed, *, stress):
    random.seed(seed)
    battle_random.seed(seed)
    player = PlayerState(route.character_type())
    enemy = EnemyState(Goblin())
    if stress:
        enemy.health.set_maximum(STRESS_HP)
        enemy.health.current = STRESS_HP

    session = RecordingSession()
    battle = Battle(
        player,
        enemy,
        ui=ProbeUI(route),
        resolver=CombatResolver(rng=battle_random),
        presentation_session=session,
    )
    winner = battle.run()
    player_actions = sum(
        bool(
            entry.accepted
            and entry.actor_name == player.display_name
            and entry.event_type
            in {
                BattleEventType.DAMAGE,
                BattleEventType.MISS,
                BattleEventType.DEFEND,
                BattleEventType.HEALING,
                BattleEventType.UTILITY,
                BattleEventType.INVENTORY,
            }
        )
        for entry in session.history
    )
    return {
        "seed": seed,
        "won": winner == "player",
        "turns": player_actions,
        "final_hp": player.health.current,
        "maximum_hp": player.health.maximum,
        "final_mana": player.mana_resource.current,
        "maximum_mana": player.mana_resource.maximum,
    }


def collect_results():
    results = {"goblin_results": [], "stress_results": []}
    for encounter_type, stress in (("goblin", False), ("stress_300_hp", True)):
        bucket = results["goblin_results" if not stress else "stress_results"]
        for route in ROUTES:
            encounters = [_encounter(route, seed, stress=stress) for seed in SEEDS]
            bucket.append(_aggregate(route, encounter_type, encounters))
    return results


def _aggregate(route, encounter_type, encounters):
    return {
        "character": route.label.split()[0],
        "path": route.label,
        "enemy": "Goblin",
        "encounter_type": encounter_type,
        "seeds": list(SEEDS),
        "wins": sum(item["won"] for item in encounters),
        "attempts": len(encounters),
        "average_turns": sum(item["turns"] for item in encounters) / len(encounters),
        "average_final_hp": sum(item["final_hp"] for item in encounters) / len(encounters),
        "maximum_hp": encounters[0]["maximum_hp"],
        "encounters": encounters,
    }


def _number(value):
    return str(int(value)) if value == int(value) else f"{value:.1f}"


def _table(title, records):
    lines = [
        f"## {title}",
        "",
        "| Character/path | Wins | Avg turns | Avg final HP |",
        "|---|---:|---:|---:|",
    ]
    for record in records:
        lines.append(
            f"| {record['path']} | {record['wins']}/{record['attempts']} | "
            f"{_number(record['average_turns'])} | "
            f"{_number(record['average_final_hp'])}/{record['maximum_hp']} |"
        )
    return lines


def render_report(results, metadata):
    lines = [
        "# Dungeon Drifters Balance Probe",
        "",
        "## Run Metadata",
        "",
        f"- Run ID: `{metadata['run_id']}`",
        f"- Timestamp: `{metadata['started_at']}`",
        f"- Branch: `{metadata['branch']}`",
        f"- Commit SHA: `{metadata['commit_sha']}`",
        f"- Working-tree state: `{metadata['working_tree_state']}`",
        f"- Python version: `{metadata['python_version']}`",
        f"- Seeds: `{metadata['seeds']}`",
        f"- Scenario count: `{metadata['scenario_count']}`",
        "",
    ]
    lines.extend(_table("Goblin Results", results["goblin_results"]))
    lines.extend(["", *(_table("300-HP Stress Results", results["stress_results"]))])
    lines.extend(
        [
            "",
            "## Observations",
            "",
            "Results are deterministic for the configured seeds and routes; no automatic balance threshold is applied.",
            "",
        ]
    )
    return "\n".join(lines)


def _git_state():
    def run(*args):
        try:
            return subprocess.run(
                [
                    "git",
                    "-c",
                    f"safe.directory={REPOSITORY_ROOT}",
                    *args,
                ],
                cwd=REPOSITORY_ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return ""

    status = run("status", "--porcelain", "--untracked-files=all")
    return {
        "branch": run("branch", "--show-current") or "unknown",
        "commit_sha": run("rev-parse", "HEAD") or "unknown",
        "working_tree_state": "clean" if not status else "dirty",
        "tracked_changes": [line for line in status.splitlines() if line and not line.startswith("??")],
        "untracked_files": [line[3:] for line in status.splitlines() if line.startswith("?? ")],
    }


def run_probe(*, output_root=OUTPUT_ROOT, now=None):
    started = now or datetime.now().astimezone()
    run_id = started.strftime("%Y-%m-%d_%H-%M-%S")
    state = _git_state()
    results = collect_results()
    completed = datetime.now().astimezone()
    metadata = {
        "run_id": run_id,
        "started_at": started.isoformat(),
        "completed_at": completed.isoformat(),
        "branch": state["branch"],
        "commit_sha": state["commit_sha"],
        "working_tree_state": state["working_tree_state"],
        "python_version": platform.python_version(),
        "probe_file": "tools/balance_probe.py",
        "probe_version": PROBE_VERSION,
        "seeds": list(SEEDS),
        "scenario_count": len(ROUTES) * 2 * len(SEEDS),
        "output_directory": str(Path(output_root) / run_id),
        "tracked_changes": state["tracked_changes"],
        "untracked_files": state["untracked_files"],
    }
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    final_dir = output_root / run_id
    temp_dir = output_root / f".{run_id}.tmp"
    if final_dir.exists() or temp_dir.exists():
        raise FileExistsError(f"output run already exists: {run_id}")
    try:
        temp_dir.mkdir()
        (temp_dir / f"{run_id} report.md").write_text(
            render_report(results, metadata), encoding="utf-8"
        )
        (temp_dir / f"{run_id} results.json").write_text(
            json.dumps({"run_id": run_id, **results}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (temp_dir / f"{run_id} metadata.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        temp_dir.rename(final_dir)
    except Exception:
        if temp_dir.exists():
            for path in temp_dir.iterdir():
                path.unlink()
            temp_dir.rmdir()
        raise
    return run_id, results, metadata, final_dir


def _console_report(results):
    return "\n".join(
        [
            "3 seeded Goblin encounters for every character, using their signature mechanics, plus longer 300-HP stress encounters.",
            "",
            "**Goblin results**",
            "",
            *_table("", results["goblin_results"])[2:],
            "",
            "**300-HP stress results**",
            "",
            *_table("", results["stress_results"])[2:],
        ]
    )


def main():
    run_id, results, _metadata, final_dir = run_probe()
    print(_console_report(results))
    print()
    print("Balance probe run complete.")
    print()
    print(f"Run ID:\n{run_id}")
    print()
    print("Outputs:")
    for suffix in ("report.md", "results.json", "metadata.json"):
        print(f"tools/balance_probe_outputs/{run_id}/{run_id} {suffix}")


if __name__ == "__main__":
    main()
