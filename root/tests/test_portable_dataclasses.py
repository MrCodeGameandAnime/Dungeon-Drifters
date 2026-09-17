import importlib.util
import runpy
import subprocess
import sys
from enum import Enum
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
OVERLAY_ROOT = ROOT / "portability" / "micropython"
OVERLAY_PATH = OVERLAY_ROOT / "dataclasses.py"
BOOTSTRAP_PATH = ROOT / "tools" / "micropython_probe_bootstrap.py"
GENERATOR_PATH = ROOT / "tools" / "generate_dataclass_manifest.py"


def _load_overlay(monkeypatch):
    monkeypatch.syspath_prepend(str(OVERLAY_ROOT))
    spec = importlib.util.spec_from_file_location(
        "portable_dataclasses_under_test",
        OVERLAY_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _decorate(portable, cls, field_names, *, frozen=False):
    portable.FIELD_MANIFEST[(cls.__module__, cls.__qualname__)] = tuple(field_names)
    return portable.dataclass(frozen=frozen)(cls)


def test_native_cpython_dataclasses_are_not_shadowed():
    import dataclasses

    assert Path(dataclasses.__file__).resolve().parent != OVERLAY_ROOT.resolve()


def test_overlay_supports_positional_keyword_and_mixed_initialization(monkeypatch):
    portable = _load_overlay(monkeypatch)

    class Record:
        first: int
        second: str = "default"

    Record = _decorate(portable, Record, ("first", "second"))

    assert Record(1) == Record(first=1)
    assert Record(1, "value").second == "value"
    assert Record(first=1, second="value").first == 1

    with pytest.raises(TypeError):
        Record()
    with pytest.raises(TypeError):
        Record(1, 2, 3)
    with pytest.raises(TypeError):
        Record(1, first=2)
    with pytest.raises(TypeError):
        Record(first=1, unknown=2)


def test_overlay_preserves_ordered_fields_and_default_factory_isolation(monkeypatch):
    portable = _load_overlay(monkeypatch)

    class Record:
        required: int
        values: list = portable.field(default_factory=list)

    Record = _decorate(portable, Record, ("required", "values"))
    first = Record(1)
    second = Record(2)
    first.values.append("only-first")

    assert tuple(first.__dataclass_fields__) == ("required", "values")
    assert first.values == ["only-first"]
    assert second.values == []
    assert first.values is not second.values


def test_overlay_structural_equality_and_frozen_assignment_rejection(monkeypatch):
    portable = _load_overlay(monkeypatch)

    class Record:
        value: int

    Record = _decorate(portable, Record, ("value",), frozen=True)

    assert Record(3) == Record(value=3)
    assert Record(3) != Record(4)
    with pytest.raises((AttributeError, TypeError)):
        Record(3).value = 4
    with pytest.raises((AttributeError, TypeError)):
        del Record(3).value


def test_overlay_supports_zero_field_records(monkeypatch):
    portable = _load_overlay(monkeypatch)

    class Empty:
        pass

    Empty = _decorate(portable, Empty, ())

    assert Empty() == Empty()
    assert tuple(Empty.__dataclass_fields__) == ()


def test_overlay_calls_post_init_and_allows_object_setattr_normalization(monkeypatch):
    portable = _load_overlay(monkeypatch)
    calls = []

    class Normalized:
        value: int

        def __post_init__(self):
            calls.append(self.value)
            object.__setattr__(self, "value", self.value + 1)

    Normalized = _decorate(portable, Normalized, ("value",), frozen=True)
    result = Normalized(4)

    assert result.value == 5
    assert calls == [4]


def test_overlay_preserves_post_init_validation_failures(monkeypatch):
    portable = _load_overlay(monkeypatch)

    class Validated:
        value: int

        def __post_init__(self):
            if self.value < 0:
                raise ValueError("value must not be negative")

    Validated = _decorate(portable, Validated, ("value",))

    with pytest.raises(ValueError, match="must not be negative"):
        Validated(-1)


def test_overlay_preserves_nested_tuple_mapping_enum_optional_and_records(monkeypatch):
    portable = _load_overlay(monkeypatch)

    class Kind(Enum):
        TEST = "test"

    class Child:
        name: str

    Child = _decorate(portable, Child, ("name",), frozen=True)

    class Parent:
        child: Child
        values: tuple
        metadata: dict
        kind: Kind
        optional: object = None

    Parent = _decorate(
        portable,
        Parent,
        ("child", "values", "metadata", "kind", "optional"),
        frozen=True,
    )
    child = Child("nested")
    result = Parent(child, (1, 2), {"key": "value"}, Kind.TEST)

    assert result.child == child
    assert result.values == (1, 2)
    assert result.metadata == {"key": "value"}
    assert result.kind is Kind.TEST
    assert result.optional is None


def test_overlay_requires_exact_manifest_identity(monkeypatch):
    portable = _load_overlay(monkeypatch)

    class Missing:
        value: int

    with pytest.raises(RuntimeError, match="missing portable dataclass metadata"):
        portable.dataclass(Missing)


def test_generated_manifest_matches_native_dataclass_discovery():
    result = subprocess.run(
        [sys.executable, str(GENERATOR_PATH), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_generated_manifest_set_and_field_order_match_native_discovery():
    generator = runpy.run_path(str(GENERATOR_PATH))
    manifest_module = runpy.run_path(str(OVERLAY_ROOT / "_dataclass_fields.py"))

    records = dict(generator["discover_native_dataclasses"]())
    manifest = manifest_module["FIELD_MANIFEST"]

    assert set(manifest) == set(records)
    assert manifest == records


def test_manifest_generation_rejects_duplicate_identity():
    generator = runpy.run_path(str(GENERATOR_PATH))

    with pytest.raises(ValueError, match="duplicate dataclass manifest key"):
        generator["build_manifest"](
            (
                (("app.example", "Record"), ("first",)),
                (("app.example", "Record"), ("second",)),
            )
        )


def test_forced_overlay_cpython_probe_completes_without_shadowing_normal_imports():
    result = subprocess.run(
        [sys.executable, str(BOOTSTRAP_PATH), str(ROOT / "src")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "MYP|RESULT|RAW_PROBE_STAGES_COMPLETE" in result.stdout
    assert "MYP|CATALOG_IMPORT|PASS" in result.stdout
