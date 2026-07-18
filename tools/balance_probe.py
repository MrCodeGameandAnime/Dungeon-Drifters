"""Opt-in seeded balance probe with persistent Markdown and JSON artifacts."""

from __future__ import annotations

import json
import platform
import random
from statistics import median
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


PROBE_VERSION = "4"
SNAPSHOT_ID = "m9-pre-progression"
SNAPSHOT_LABEL = "M9 base roster before XP, leveling, and skill trees"
SEED_CORPUS_VERSION = 1
ROUTE_POLICY_VERSION = 2
GOBLIN_SEEDS = tuple(range(1, 25)) + (47,)
STRESS_SEEDS = tuple(range(1, 99)) + (101, 202)
STRESS_HP = 300
OUTPUT_ROOT = REPOSITORY_ROOT / "tools" / "balance_probe_outputs"


@dataclass(frozen=True)
class Route:
    label: str
    character_type: type
    signature: str
    infusion_item: str | None = None
    infusion_companion: str | None = None
    description: str = ""


ROUTES = (
    Route("Branoc Brace", Brawler, "branoc"),
    Route("Azhvielle Gravemantle", BlackMage, "azhvielle"),
    Route(
        "Azhvielle Frost",
        BlackMage,
        "azhvielle_frost",
        description="Mournglass Bloom while affordable, then Scepter Sweep.",
    ),
    Route("Zhaivra Fire", RogueArcher, "zhaivra", "ember_shard", "deep_coal"),
    Route("Zhaivra Poison", RogueArcher, "zhaivra", "deep_coal", "night_berry"),
    Route("Joruun Water", Monk, "water"),
    Route("Joruun Air", Monk, "air"),
    Route("Joruun Storm", Monk, "storm"),
)

SUPER_USAGE_POLICY = (
    "Use the authored Super immediately when the typed Super action is offered "
    "and enabled, after required initial route preparation."
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
            return self._action_input(view)
        if view.interaction_phase == InteractionPhase.SUPER_MOVES:
            enabled = [option for option in view.move_options if option.enabled]
            if len(enabled) != 1:
                raise RuntimeError(
                    f"expected exactly one enabled Super move for {self.route.label}, "
                    f"got {len(enabled)}"
                )
            return ChooseMove(enabled[0].selection_key)
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

    def _action_input(self, view):
        if self.route.signature == "zhaivra" and self.stage == "start":
            self.stage = "inventory"
            return ChooseAction(ActionIntent.ITEMS)
        if view.super_meter.activation_offered:
            return ChooseAction(ActionIntent.SUPER)
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

        if self.route.signature == "azhvielle_frost":
            if "Mournglass Bloom" in offered and offered["Mournglass Bloom"].enabled:
                return "Mournglass Bloom"
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
    super_names = {
        move.name
        for move in player.combat_moves
        if move.resource_type.value == "super"
    }
    super_uses = sum(
        1
        for entry in session.history
        if entry.accepted is True
        and entry.actor_name == player.display_name
        and entry.action_name in super_names
    )
    return {
        "seed": seed,
        "won": winner == "player",
        "turns": player_actions,
        "final_hp": player.health.current,
        "maximum_hp": player.health.maximum,
        "final_mana": player.mana_resource.current,
        "maximum_mana": player.mana_resource.maximum,
        "super_uses": super_uses,
        "final_super": player.super_resource.current,
        "maximum_super": player.super_resource.maximum,
    }


def collect_results():
    results = {"goblin_results": [], "stress_results": []}
    for encounter_type, stress, seeds in (
        ("goblin", False, GOBLIN_SEEDS),
        ("stress_300_hp", True, STRESS_SEEDS),
    ):
        bucket = results["goblin_results" if not stress else "stress_results"]
        for route in ROUTES:
            encounters = [_encounter(route, seed, stress=stress) for seed in seeds]
            bucket.append(_aggregate(route, encounter_type, seeds, encounters))
    return results


def _aggregate(route, encounter_type, seeds, encounters):
    return {
        "character": route.label.split()[0],
        "path": route.label,
        "enemy": "Goblin",
        "encounter_type": encounter_type,
        "seeds": list(seeds),
        "wins": sum(item["won"] for item in encounters),
        "attempts": len(encounters),
        "win_rate": sum(item["won"] for item in encounters) / len(encounters),
        "average_turns": sum(item["turns"] for item in encounters) / len(encounters),
        "median_turns": median(item["turns"] for item in encounters),
        "average_final_hp": sum(item["final_hp"] for item in encounters) / len(encounters),
        "average_final_mana": sum(item["final_mana"] for item in encounters) / len(encounters),
        "total_super_uses": sum(item["super_uses"] for item in encounters),
        "encounters_with_super": sum(item["super_uses"] > 0 for item in encounters),
        "average_super_uses": sum(item["super_uses"] for item in encounters) / len(encounters),
        "maximum_hp": encounters[0]["maximum_hp"],
        "encounters": encounters,
    }


def _number(value):
    return str(int(value)) if value == int(value) else f"{value:.1f}"


def _table(title, records):
    lines = [
        f"## {title}",
        "",
        "| Character/path | Wins | Win rate | Avg turns | Median turns | Avg final HP | Avg final Mana | Super uses | Encounters using Super | Avg Supers |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for record in records:
        lines.append(
            f"| {record['path']} | {record['wins']}/{record['attempts']} | "
            f"{record['win_rate']:.1%} | {_number(record['average_turns'])} | "
            f"{_number(record['median_turns'])} | "
            f"{_number(record['average_final_hp'])}/{record['maximum_hp']} | "
            f"{_number(record['average_final_mana'])} | "
            f"{record['total_super_uses']} | {record['encounters_with_super']} | "
            f"{_number(record['average_super_uses'])} |"
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
        f"- Goblin seeds: `{metadata['goblin_seeds']}`",
        f"- Stress seeds: `{metadata['stress_seeds']}`",
        f"- Snapshot ID: `{metadata['snapshot_id']}`",
        f"- Snapshot label: `{metadata['snapshot_label']}`",
        f"- Probe version: `{metadata['probe_version']}`",
        f"- Seed corpus version: `{metadata['seed_corpus_version']}`",
        f"- Route policy version: `{metadata['route_policy_version']}`",
        f"- Route count: `{metadata['route_count']}`",
        f"- Goblin seed count: `{metadata['goblin_seed_count']}`",
        f"- Stress seed count: `{metadata['stress_seed_count']}`",
        f"- Scenario count: `{metadata['scenario_count']}`",
        f"- Super usage policy: `{metadata['super_usage_policy']}`",
        "",
        "## Route Policies",
        "",
        *[f"- {route['label']} (v{route['version']})" for route in metadata["route_policies"]],
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
            result = subprocess.run(
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
            )
            return True, result.stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return False, ""

    status_succeeded, status = run("status", "--porcelain", "--untracked-files=all")
    branch_succeeded, branch = run("branch", "--show-current")
    commit_succeeded, commit_sha = run("rev-parse", "HEAD")
    return {
        "branch": branch if branch_succeeded and branch else "unknown",
        "commit_sha": commit_sha if commit_succeeded and commit_sha else "unknown",
        "working_tree_state": (
            "unknown" if not status_succeeded else ("clean" if not status else "dirty")
        ),
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
        "snapshot_id": SNAPSHOT_ID,
        "snapshot_label": SNAPSHOT_LABEL,
        "seed_corpus_version": SEED_CORPUS_VERSION,
        "route_policy_version": ROUTE_POLICY_VERSION,
        "goblin_seeds": list(GOBLIN_SEEDS),
        "stress_seeds": list(STRESS_SEEDS),
        "route_count": len(ROUTES),
        "goblin_seed_count": len(GOBLIN_SEEDS),
        "stress_seed_count": len(STRESS_SEEDS),
        "scenario_count": len(ROUTES) * (len(GOBLIN_SEEDS) + len(STRESS_SEEDS)),
        "route_policies": [
            {"label": route.label, "version": ROUTE_POLICY_VERSION}
            for route in ROUTES
        ],
        "super_usage_policy": SUPER_USAGE_POLICY,
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
            "25 seeded Goblin encounters for every route, using their signature mechanics, plus 100 longer 300-HP stress encounters.",
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
