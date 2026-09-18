import keyword as native_keyword
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
        "import re\n"
        "import pathlib\n"
        "import typing\n"
        "import inspect\n"
        "import annotationlib\n"
        "import tempfile\n"
        "import shutil\n"
        "import compression\n"
        "import keyword as native_keyword\n"
        "del sys.modules['keyword']\n"
        "del sys.modules['enum']\n"
        f"sys.path.insert(0, {str(OVERLAY_ROOT)!r})\n"
        f"sys.path.insert(1, {str(SRC_ROOT)!r})\n"
    )
    return subprocess.run(
        [sys.executable, "-S", "-c", prelude + source],
        cwd=ROOT,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )


def test_forced_overlay_is_active_and_matches_native_keyword():
    hard_keywords = repr(tuple(native_keyword.kwlist))
    soft_keywords = repr(tuple(native_keyword.softkwlist))
    result = _run_forced_overlay(
        f"""
import keyword
from pathlib import Path

overlay = Path.cwd() / "portability" / "micropython"
assert Path(keyword.__file__).resolve() == (overlay / "keyword.py").resolve()
assert keyword.__all__ == ["iskeyword"]
assert not hasattr(keyword, "kwlist")
assert not hasattr(keyword, "softkwlist")
assert not hasattr(keyword, "issoftkeyword")
for value in {hard_keywords}:
    assert keyword.iskeyword(value) is True
for value in {soft_keywords}:
    assert keyword.iskeyword(value) is False
for value in ("goblin", "ember_shard", "dungeon_entrance"):
    assert keyword.iskeyword(value) is False
assert keyword.iskeyword("class") == native_keyword.iskeyword("class")
"""
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_forced_overlay_exercises_real_dd_validators_and_preserves_other_overlays():
    hard_keywords = repr(tuple(native_keyword.kwlist))
    result = _run_forced_overlay(
        f"""
import dataclasses
import enum
import keyword

from app.content.catalog import (
    ENCOUNTER_SPECS,
    ENEMY_SPECS,
    DRIFTER_SPECS,
    ROUTE_SPECS,
    WEAPON_SPECS,
    get_drifter_spec,
    get_enemy_spec,
    get_weapon_spec,
)
from app.content.enemy_spec import EnemySpec
from app.content.drifter_spec import DrifterSpec
from app.content.route_spec import validate_content_id
from app.content.weapon_spec import WeaponSpec
from app.combat.move import MoveKind

assert enum.StrEnum.__module__ == "enum"
assert dataclasses.__file__.replace("\\\\", "/").endswith("/portability/micropython/dataclasses.py")
assert keyword.iskeyword("class") is True

authored_ids = []
authored_ids.extend(spec.archetype_id for spec in ENEMY_SPECS)
authored_ids.extend(spec.drifter_id for spec in DRIFTER_SPECS)
authored_ids.extend(spec.starting_weapon_id for spec in DRIFTER_SPECS)
authored_ids.extend(spec.item_id for spec in WEAPON_SPECS)
authored_ids.extend(spec.encounter_id for spec in ENCOUNTER_SPECS)
for route in ROUTE_SPECS:
    authored_ids.append(route.route_id)
    authored_ids.extend(node.node_id for node in route.nodes)
    authored_ids.extend(
        node.encounter_id for node in route.nodes if node.encounter_id is not None
    )
for value in authored_ids:
    assert keyword.iskeyword(value) == native_keyword.iskeyword(value)

def replace_value(instance, field_name, value):
    values = {{name: getattr(instance, name) for name in instance.__dataclass_fields__}}
    values[field_name] = value
    return values

enemy = get_enemy_spec("goblin")
try:
    EnemySpec(**replace_value(enemy, "archetype_id", "class"))
except ValueError:
    pass
else:
    raise AssertionError("EnemySpec accepted a Python keyword archetype ID")

drifter = get_drifter_spec("branoc")
try:
    DrifterSpec(**replace_value(drifter, "drifter_id", "class"))
except ValueError:
    pass
else:
    raise AssertionError("DrifterSpec accepted a Python keyword ID")

try:
    DrifterSpec(**replace_value(drifter, "starting_weapon_id", "class"))
except ValueError:
    pass
else:
    raise AssertionError("DrifterSpec accepted a Python keyword weapon ID")

route_values = ("class", "two words", "UpperCase", "valid_route")
for value in route_values[:3]:
    try:
        validate_content_id("route_id", value)
    except (TypeError, ValueError):
        pass
    else:
        raise AssertionError("route validator accepted invalid ID")
assert validate_content_id("route_id", route_values[3]) == "valid_route"

weapon = get_weapon_spec("sunder_spire")
try:
    WeaponSpec(**replace_value(weapon, "item_id", "class"))
except ValueError:
    pass
else:
    raise AssertionError("WeaponSpec accepted a Python keyword item ID")

assert MoveKind("damage") is MoveKind.DAMAGE
assert {{MoveKind.DAMAGE: "ok"}}["damage"] == "ok"
assert all(keyword.iskeyword(value) is True for value in {hard_keywords})
"""
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_forced_overlay_matches_native_for_all_hard_keywords():
    values = repr(tuple(native_keyword.kwlist))
    result = _run_forced_overlay(
        f"""
import keyword
assert tuple(keyword.iskeyword(value) for value in {values}) == tuple(True for _ in {values})
"""
    )
    assert result.returncode == 0, result.stdout + result.stderr
