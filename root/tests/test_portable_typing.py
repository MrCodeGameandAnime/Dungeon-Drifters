import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
OVERLAY_ROOT = ROOT / "portability" / "micropython"


def _run_forced_overlay(source):
    prelude = (
        "import sys\n"
        "import enum\n"
        "import re\n"
        "import keyword\n"
        "import collections\n"
        "import collections.abc\n"
        f"sys.path.insert(0, {str(OVERLAY_ROOT)!r})\n"
        f"sys.path.insert(1, {str(SRC_ROOT)!r})\n"
        "import dataclasses\n"
        "import typing\n"
    )
    return subprocess.run(
        [sys.executable, "-S", "-c", prelude + source],
        cwd=ROOT,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )


def test_native_cpython_typing_is_not_shadowed():
    import typing

    assert Path(typing.__file__).resolve().parent != OVERLAY_ROOT.resolve()


def test_forced_overlay_loads_typing_and_all_runtime_aliases():
    result = _run_forced_overlay(
        """
import typing
from pathlib import Path

assert Path(typing.__file__).resolve() == (Path.cwd() / "portability" / "micropython" / "typing.py").resolve()
assert set(typing.__all__) == {"Protocol", "runtime_checkable", "TypeAlias", "Sequence", "Union"}
assert typing.Union[int, str] == (int, str)
assert typing.Sequence[int] is typing.Sequence

from app.ui.battle_ui import BattleInput, BattleUI
from app.ui.overworld_ui import OverworldInput, OverworldUI
from app.game.overworld_session import SessionInput, SessionView

assert isinstance(BattleInput, tuple)
assert isinstance(OverworldInput, tuple)
assert isinstance(SessionInput, tuple)
assert isinstance(SessionView, tuple)

class UI:
    def render(self, view):
        pass

    def read_input(self, view):
        pass

from app.ui.battle_ui import is_battle_ui
from app.ui.overworld_ui import is_overworld_ui
assert is_battle_ui(UI())
assert is_overworld_ui(UI())
assert not isinstance(UI(), BattleUI)
"""
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_forced_overlay_preserves_combat_predicate_contracts():
    result = _run_forced_overlay(
        """
from app.combat.combatant import is_combatant, is_enemy_combatant

class CombatantDouble:
    display_name = "double"
    health = object()
    mana_resource = object()
    super_resource = object()
    generates_super = True
    can_defend = True
    combat_moves = ()

    def effective_stat(self, name):
        return 1

    def defend_reduction_percent(self, damage_type):
        return 0

    def is_alive(self):
        return True

class EnemyDouble(CombatantDouble):
    archetype_id = "double"
    tier = 0

assert is_combatant(CombatantDouble())
assert is_enemy_combatant(EnemyDouble())
assert not is_enemy_combatant(CombatantDouble())

for method_name in ("effective_stat", "defend_reduction_percent", "is_alive"):
    Broken = type("Broken", (EnemyDouble,), {method_name: None})
    assert not is_enemy_combatant(Broken())
    missing_attributes = {
        "display_name": "missing",
        "health": object(),
        "mana_resource": object(),
        "super_resource": object(),
        "generates_super": True,
        "can_defend": True,
        "combat_moves": (),
        "archetype_id": "missing",
        "tier": 0,
        "effective_stat": lambda self, name: 1,
        "defend_reduction_percent": lambda self, damage_type: 0,
        "is_alive": lambda self: True,
    }
    missing_attributes.pop(method_name)
    Missing = type("Missing", (), missing_attributes)
    assert not is_enemy_combatant(Missing())
"""
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_forced_overlay_loads_real_combat_and_ui_contracts():
    result = _run_forced_overlay(
        """
from app.content.catalog import create_drifter, create_enemy_definition
from app.enemies.state import EnemyState
from app.player.player_state import PlayerState
from app.combat.combatant import is_combatant, is_enemy_combatant
from app.ui.battle_ui import is_battle_ui
from app.ui.overworld_ui import is_overworld_ui

player = PlayerState(create_drifter("branoc"))
enemy = EnemyState(create_enemy_definition("goblin"))
assert is_combatant(player)
assert is_combatant(enemy)
assert is_enemy_combatant(enemy)

class Adapter:
    def render(self, view):
        pass

    def read_input(self, view):
        pass

assert is_battle_ui(Adapter())
assert is_overworld_ui(Adapter())
"""
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_forced_overlay_does_not_leak_into_host_process():
    result = _run_forced_overlay(
        """
from pathlib import Path
import typing
assert Path(typing.__file__).resolve() == (Path.cwd() / "portability" / "micropython" / "typing.py").resolve()
"""
    )
    assert result.returncode == 0, result.stdout + result.stderr
