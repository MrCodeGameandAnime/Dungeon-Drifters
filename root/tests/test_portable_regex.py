import ast
import os
import re as native_re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
OVERLAY_ROOT = ROOT / "portability" / "micropython"


def _production_patterns():
    patterns = []
    for path in sorted((ROOT / "src" / "app").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr != "compile" or not isinstance(node.func.value, ast.Name):
                continue
            if node.func.value.id != "re" or not node.args:
                continue
            if isinstance(node.args[0], ast.Constant) and isinstance(
                node.args[0].value, str
            ):
                patterns.append(node.args[0].value)
    return tuple(dict.fromkeys(patterns))


def _run_forced_compatibility(source):
    prelude = (
        "import sys\n"
        "import re as native_re\n"
        "import json\n"
        "import pathlib\n"
        "import typing\n"
        "import inspect\n"
        "import annotationlib\n"
        "import tempfile\n"
        "import shutil\n"
        "import compression\n"
        "del sys.modules['enum']\n"
        "del sys.modules['keyword']\n"
        f"sys.path.insert(0, {str(OVERLAY_ROOT)!r})\n"
        f"sys.path.insert(1, {str(SRC_ROOT)!r})\n"
        "from re_compat import install\n"
        "proxy = install(native_re)\n"
        "assert install(proxy) is proxy\n"
        "assert install(native_re) is proxy\n"
        "sys.modules['re'] = proxy\n"
    )
    return subprocess.run(
        [sys.executable, "-S", "-c", prelude + source],
        cwd=ROOT,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )


def test_native_cpython_uses_standard_library_re():
    assert Path(native_re.__file__).resolve().parent != OVERLAY_ROOT.resolve()
    assert native_re.fullmatch(r"[a-z][a-z0-9_]*", "goblin") is not None


def test_forced_proxy_preserves_native_engine_and_adds_only_fullmatch_boundary():
    result = _run_forced_compatibility(
        """
import re

assert getattr(re, "_dd_myp7_proxy", False) is True
assert re._native_re is native_re
native_pattern = native_re.compile(r"[a-z][a-z0-9_]*")
portable_pattern = re.compile(r"[a-z][a-z0-9_]*")
assert native_pattern is not portable_pattern
assert getattr(native_pattern, "_dd_myp7_pattern", False) is False
assert getattr(portable_pattern, "_dd_myp7_pattern", False) is True
assert re.search("ob", "goblin") is not None
assert portable_pattern.search("goblin") is not None
assert portable_pattern.fullmatch("goblin") is not None
assert portable_pattern.fullmatch("goblin!") is None
assert re.fullmatch(r"[a-z][a-z0-9_]*", "goblin") is not None
assert re.fullmatch(r"[a-z][a-z0-9_]*", "goblin!") is None
try:
    re.compile(r"x", 1)
except NotImplementedError:
    pass
else:
    raise AssertionError("unsupported regex flags were accepted")
"""
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_forced_proxy_matches_native_for_all_discovered_production_patterns():
    patterns = repr(_production_patterns())
    values = repr(
        (
            "goblin",
            "goblin_2",
            "a",
            "goblin!",
            "goblin extra",
            "Goblin",
            "_goblin",
            "",
            "class",
            "for",
            "return",
        )
    )
    result = _run_forced_compatibility(
        f"""
import re

patterns = {patterns}
values = {values}
for pattern_text in patterns:
    native_pattern = native_re.compile(pattern_text)
    portable_pattern = re.compile(pattern_text)
    for value in values:
        expected = native_re.fullmatch(pattern_text, value) is not None
        assert (portable_pattern.fullmatch(value) is not None) == expected
        assert (re.fullmatch(pattern_text, value) is not None) == expected
"""
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_forced_proxy_exercises_real_dd_validators_and_preserves_other_overlays():
    result = _run_forced_compatibility(
        """
import dataclasses
import enum
import keyword

from app.content.catalog import get_drifter_spec, get_enemy_spec, get_weapon_spec
from app.content.drifter_spec import DrifterSpec
from app.content.enemy_spec import EnemySpec
from app.content.route_spec import validate_content_id
from app.content.weapon_spec import WeaponSpec

assert enum.StrEnum.__module__ == "enum"
assert dataclasses.__file__.replace("\\\\", "/").endswith(
    "/portability/micropython/dataclasses.py"
)
assert keyword.iskeyword("class") is True

def replace_value(instance, field_name, value):
    values = {name: getattr(instance, name) for name in instance.__dataclass_fields__}
    values[field_name] = value
    return values

enemy = get_enemy_spec("goblin")
assert EnemySpec(**replace_value(enemy, "archetype_id", "goblin_2")).archetype_id == "goblin_2"
for value in ("Goblin", "has-dash", "two words", "_leading", "trailing!", "", "class"):
    try:
        EnemySpec(**replace_value(enemy, "archetype_id", value))
    except (TypeError, ValueError):
        pass
    else:
        raise AssertionError("EnemySpec accepted invalid ID")

drifter = get_drifter_spec("branoc")
assert DrifterSpec(**replace_value(drifter, "drifter_id", "goblin_2")).drifter_id == "goblin_2"
for value in ("Goblin", "has-dash", "two words", "_leading", "trailing!", "", "class"):
    try:
        DrifterSpec(**replace_value(drifter, "drifter_id", value))
    except (TypeError, ValueError):
        pass
    else:
        raise AssertionError("DrifterSpec accepted invalid ID")

assert validate_content_id("route_id", "dungeon_entrance") == "dungeon_entrance"
for value in ("Goblin", "has-dash", "two words", "_leading", "trailing!", "", "class"):
    try:
        validate_content_id("route_id", value)
    except (TypeError, ValueError):
        pass
    else:
        raise AssertionError("route validator accepted invalid ID")

weapon = get_weapon_spec("sunder_spire")
assert WeaponSpec(**replace_value(weapon, "item_id", "ember_shard")).item_id == "ember_shard"
for value in ("Goblin", "has-dash", "two words", "_leading", "trailing!", "", "class"):
    try:
        WeaponSpec(**replace_value(weapon, "item_id", value))
    except (TypeError, ValueError):
        pass
    else:
        raise AssertionError("WeaponSpec accepted invalid ID")
"""
    )
    assert result.returncode == 0, result.stdout + result.stderr
