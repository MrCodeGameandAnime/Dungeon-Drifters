"""Generate the MicroPython dataclass field manifest from DD source."""

import argparse
import ast
import dataclasses
import importlib
import inspect
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"
APP_ROOT = SOURCE_ROOT / "app"
MANIFEST_PATH = ROOT / "portability" / "micropython" / "_dataclass_fields.py"


class UnsafeImportError(RuntimeError):
    """Raised when native discovery would require an unacceptable side effect."""


def _module_name(path):
    relative = path.relative_to(SOURCE_ROOT).with_suffix("")
    return ".".join(relative.parts)


def _contains_dataclass_decorator(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
                return True
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Name)
                and decorator.func.id == "dataclass"
            ):
                return True
    return False


def _calls_builtin_input(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "input"
        for node in ast.walk(tree)
    )


def _candidate_modules():
    return tuple(
        (_module_name(path), path)
        for path in sorted(APP_ROOT.rglob("*.py"))
        if "__pycache__" not in path.parts and _contains_dataclass_decorator(path)
    )


def _import_candidates():
    if str(SOURCE_ROOT) not in sys.path:
        sys.path.insert(0, str(SOURCE_ROOT))

    modules = []
    for module_name, path in _candidate_modules():
        if _calls_builtin_input(path):
            raise UnsafeImportError(
                f"native dataclass discovery would import terminal input: {path}"
            )
        modules.append(importlib.import_module(module_name))
    return tuple(modules)


def discover_native_dataclasses():
    records = []
    for module in _import_candidates():
        module_name = module.__name__
        for _, value in inspect.getmembers(module, inspect.isclass):
            if value.__module__ != module_name:
                continue
            if not dataclasses.is_dataclass(value):
                continue
            qualified_name = getattr(value, "__qualname__", value.__name__)
            field_names = tuple(value.__dataclass_fields__)
            records.append(((module_name, qualified_name), field_names))
    return tuple(sorted(records))


def build_manifest(records):
    manifest = {}
    for key, field_names in records:
        if key in manifest:
            raise ValueError(f"duplicate dataclass manifest key: {key!r}")
        if len(field_names) != len(set(field_names)):
            raise ValueError(f"invalid field names for manifest key: {key!r}")
        manifest[key] = tuple(field_names)
    return manifest


def render_manifest(records):
    manifest = build_manifest(records)
    lines = [
        '"""Generated MicroPython dataclass field metadata. Do not edit by hand."""',
        "",
        'IDENTITY_MODE = "qualified_name"',
        "",
        "FIELD_MANIFEST = {",
    ]
    for (module_name, qualified_name), field_names in sorted(manifest.items()):
        lines.append(
            f"    ({module_name!r}, {qualified_name!r}): {field_names!r},"
        )
    lines.extend(("}", ""))
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    records = discover_native_dataclasses()
    expected = render_manifest(records)
    actual = MANIFEST_PATH.read_text(encoding="utf-8") if MANIFEST_PATH.exists() else None
    if args.check:
        if actual != expected:
            print(f"stale dataclass manifest: {MANIFEST_PATH}")
            return 1
        print(f"dataclass manifest is current: {len(records)} entries")
        return 0

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(expected, encoding="utf-8", newline="\n")
    print(f"generated dataclass manifest: {len(records)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
