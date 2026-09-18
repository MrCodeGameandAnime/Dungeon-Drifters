import ast
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
OVERLAY_ROOT = ROOT / "portability" / "micropython"


def _production_enum_records():
    records = []
    for path in sorted((ROOT / "src" / "app").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        module = ".".join(path.relative_to(SRC_ROOT).with_suffix("").parts)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not any(
                isinstance(base, ast.Name) and base.id == "StrEnum"
                for base in node.bases
            ):
                continue
            members = []
            for statement in node.body:
                if isinstance(statement, ast.Assign):
                    targets = statement.targets
                    value = statement.value
                elif isinstance(statement, ast.AnnAssign):
                    targets = [statement.target]
                    value = statement.value
                else:
                    continue
                for target in targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        members.append((target.id, ast.literal_eval(value)))
            records.append((module, node.name, tuple(members)))
    return tuple(records)


def _run_forced_overlay(source):
    env = os.environ.copy()
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
        "del sys.modules['enum']\n"
        f"sys.path.insert(0, {str(OVERLAY_ROOT)!r})\n"
        f"sys.path.insert(1, {str(SRC_ROOT)!r})\n"
    )
    return subprocess.run(
        [sys.executable, "-S", "-c", prelude + source],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def test_forced_overlay_is_active_and_preserves_real_dd_enum_behavior():
    result = _run_forced_overlay(
        """
import enum
from pathlib import Path

overlay = Path.cwd() / "portability" / "micropython"
assert Path(enum.__file__).resolve().parent == overlay.resolve()
from app.combat.move import Move, MoveKind, ResourceType, ScalingAttribute, TargetType, DamageType

assert MoveKind("damage") is MoveKind.DAMAGE
assert MoveKind(MoveKind.DAMAGE) is MoveKind.DAMAGE
assert MoveKind.DAMAGE.value == "damage"
assert MoveKind.DAMAGE.name == "DAMAGE"
assert MoveKind.DAMAGE == "damage"
assert str(MoveKind.DAMAGE) == "damage"
assert isinstance(MoveKind.DAMAGE, MoveKind)
assert {MoveKind.DAMAGE: "ok"}["damage"] == "ok"

move = Move(
    name="Portable Slash",
    kind="damage",
    resource_type="none",
    resource_cost=0,
    power=1,
    scales_with=(ScalingAttribute("strength"),),
    accuracy=100,
    target=TargetType("enemy"),
    damage_type=DamageType("physical"),
    mechanic=None,
    description="A portable test move.",
)
assert move.kind is MoveKind.DAMAGE
assert move.resource_type is ResourceType.NONE

class MicroPythonMembers:
    def __init__(self, enum_type, members):
        self._enum_type = enum_type
        self._members = members

    def __getitem__(self, key):
        if isinstance(key, self._enum_type):
            raise KeyError(key)
        return self._members[key]

for enum_type in (MoveKind, ResourceType, ScalingAttribute, TargetType, DamageType):
    enum_type.__members__ = MicroPythonMembers(enum_type, enum_type.__members__)

assert MoveKind(MoveKind.DAMAGE) is MoveKind.DAMAGE

authored_move = Move(
    name="Authored Portable Slash",
    kind=MoveKind.DAMAGE,
    resource_type=ResourceType.NONE,
    resource_cost=0,
    power=1,
    scales_with=(ScalingAttribute.STRENGTH,),
    accuracy=100,
    target=TargetType.ENEMY,
    damage_type=DamageType.PHYSICAL,
    mechanic="basic_attack",
    description="An authored portable test move.",
)
assert authored_move.kind is MoveKind.DAMAGE
assert authored_move.resource_type is ResourceType.NONE
assert authored_move.scales_with == (ScalingAttribute.STRENGTH,)
assert authored_move.target is TargetType.ENEMY
assert authored_move.damage_type is DamageType.PHYSICAL
"""
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_forced_overlay_loads_every_discovered_production_enum():
    records = repr(_production_enum_records())
    result = _run_forced_overlay(
        f"""
import importlib

records = {records}
for module_name, class_name, members in records:
    enum_type = getattr(importlib.import_module(module_name), class_name)
    for member_name, value in members:
        member = getattr(enum_type, member_name)
        assert enum_type(value) is member
        assert enum_type(member) is member
        assert member.name == member_name
        assert member.value == value
        assert isinstance(member, enum_type)
"""
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_overlay_transforms_only_direct_strenum_subclasses_and_keeps_dataclasses_working():
    result = _run_forced_overlay(
        """
import builtins
import dataclasses

original_builder = builtins.__build_class__
from enum import StrEnum

class Ordinary:
    VALUE = "ordinary"

assert Ordinary.VALUE == "ordinary"
assert not hasattr(Ordinary, "__members__")

class Sample(StrEnum):
    FIRST = "first"
    SECOND = "second"

assert Sample.FIRST is Sample("first")
assert Sample.FIRST.value == "first"
assert Sample.FIRST.name == "FIRST"
assert Sample.FIRST == "first"
assert str(Sample.FIRST) == "first"
assert hash(Sample.FIRST) == hash("first")
assert isinstance(Sample.FIRST, Sample)

try:
    Sample("missing")
except ValueError:
    pass
else:
    raise AssertionError("unknown enum value was accepted")

class Record:
    value: int

dataclasses.FIELD_MANIFEST[(Record.__module__, Record.__qualname__)] = ("value",)
Record = dataclasses.dataclass(frozen=True)(Record)
assert Record(3).value == 3
assert builtins.__build_class__ is not original_builder
"""
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_overlay_rejects_duplicate_and_malformed_candidate_members():
    result = _run_forced_overlay(
        """
from enum import StrEnum

try:
    class Duplicate(StrEnum):
        FIRST = "same"
        SECOND = "same"
except (TypeError, ValueError):
    pass
else:
    raise AssertionError("duplicate enum values were accepted")

try:
    class Malformed(StrEnum):
        VALUE = 1
except (TypeError, ValueError):
    pass
else:
    raise AssertionError("non-string enum value was accepted")
"""
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_portable_dataclass_census_uses_unique_identities():
    result = _run_forced_overlay(
        """
import dataclasses

class Record:
    value: int

dataclasses.FIELD_MANIFEST[(Record.__module__, Record.__qualname__)] = ("value",)
before = dataclasses._dataclass_census()
Record = dataclasses.dataclass()(Record)
after_decorate = dataclasses._dataclass_census()
assert after_decorate[1] == before[1] + 1
Record(1)
Record(2)
after = dataclasses._dataclass_census()
assert after[1] == after_decorate[1]
assert after[2] == after_decorate[2] + 1
"""
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_forced_overlay_bootstrap_emits_dataclass_census():
    bootstrap = ROOT / "tools" / "micropython_probe_bootstrap.py"
    result = subprocess.run(
        [sys.executable, str(bootstrap), str(SRC_ROOT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "MYP|DATACLASS|EXPECTED|" in result.stdout
    assert "MYP|DATACLASS|DECORATED|" in result.stdout
    assert "MYP|DATACLASS|CONSTRUCTED|" in result.stdout
