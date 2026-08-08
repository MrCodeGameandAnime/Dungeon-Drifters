import ast
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from app.content.catalog import create_drifter, create_enemy_definition, create_enemy_state
from tools import scaffold_content as scaffolder
from tools.validate_content import TODO_MARKER


ROOT = Path(__file__).resolve().parents[1]
CONTENT_ROOT = ROOT / "src" / "app" / "content"
OBSOLETE_PATHS = (
    "src/app/enemies/factory.py",
    "src/app/game/encounter_manifest.py",
    "src/app/game/overworld_route.py",
    "src/app/world/character_profiles/__init__.py",
    "src/app/world/character_profiles/profile.py",
    "src/app/world/character_profiles/roster.py",
)
CONCRETE_CONTENT_PREFIXES = (
    "app.content.enemies.",
    "app.content.weapons.",
    "app.content.drifters.",
    "app.content.encounters.",
    "app.content.routes.",
)
FORBIDDEN_CONTENT_PREFIXES = (
    "app.game",
    "app.presentation",
    "app.ui",
)


def _imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    return tuple(imported)


def _tooling_root(tmp_path):
    root = tmp_path / "project"
    shutil.copytree(ROOT / "src" / "app", root / "src" / "app")
    (root / "tests").mkdir(parents=True)
    (root / "tools").mkdir()
    for name in (
        "generate_content_catalog.py",
        "scaffold_content.py",
        "validate_content.py",
    ):
        shutil.copy2(ROOT / "tools" / name, root / "tools" / name)
    return root


def _run_validator(root):
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(root / "src")
    return subprocess.run(
        [sys.executable, "-m", "tools.validate_content"],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_obsolete_authoring_and_compatibility_paths_are_removed():
    assert all(not (ROOT / relative).exists() for relative in OBSOLETE_PATHS)


def test_runtime_objects_expose_only_canonical_combat_moves():
    character = create_drifter("branoc")
    definition = create_enemy_definition("goblin")
    enemy = create_enemy_state("goblin")

    assert character.combat_moves
    assert definition.combat_moves
    assert enemy.combat_moves
    assert not hasattr(character, "moves")
    assert not hasattr(definition, "moves")
    assert not hasattr(enemy, "moves")


def test_engine_and_presentation_never_import_concrete_content_packages():
    offenders = []
    for path in sorted((ROOT / "src" / "app").rglob("*.py")):
        if path.is_relative_to(CONTENT_ROOT):
            continue
        concrete = tuple(
            name
            for name in _imports(path)
            if name.startswith(CONCRETE_CONTENT_PREFIXES)
        )
        if concrete:
            offenders.append((path.relative_to(ROOT).as_posix(), concrete))

    assert offenders == []


def test_authored_content_never_imports_runtime_or_platform_orchestration():
    offenders = []
    for path in sorted(CONTENT_ROOT.rglob("*.py")):
        forbidden = tuple(
            name
            for name in _imports(path)
            if name.startswith(FORBIDDEN_CONTENT_PREFIXES)
        )
        if forbidden:
            offenders.append((path.relative_to(ROOT).as_posix(), forbidden))

    assert offenders == []


def test_runtime_content_catalog_performs_no_filesystem_discovery():
    for relative in (
        "src/app/content/catalog.py",
        "src/app/content/_generated_catalog.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert ".glob(" not in source
        assert ".rglob(" not in source
        assert "os.walk" not in source
        assert "importlib" not in source


@pytest.mark.parametrize(
    ("content_type", "content_id"),
    (
        ("enemy", "flat6_enemy"),
        ("weapon", "flat6_weapon"),
        ("drifter", "flat6_drifter"),
        ("encounter", "flat6_encounter"),
        ("route", "flat6_route"),
    ),
)
def test_every_scaffolder_produces_content_accepted_after_authoring(
    tmp_path,
    content_type,
    content_id,
):
    root = _tooling_root(tmp_path)
    primary, _, _ = scaffolder.scaffold_content(content_type, content_id, root=root)
    primary.write_text(
        primary.read_text(encoding="utf-8").replace(TODO_MARKER, "AUTHORED"),
        encoding="utf-8",
    )

    result = _run_validator(root)

    assert result.returncode == 0, result.stderr
    assert "content valid:" in result.stdout
