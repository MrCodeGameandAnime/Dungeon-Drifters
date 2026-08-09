import ast
import hashlib
import os
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from app.combat.move import MoveKind
from app.combat.resolver import authored_move_rejection_reason
from app.content.catalog import DRIFTER_SPECS, ENEMY_SPECS
from tools import scaffold_content as scaffolder
from tools.generate_content_catalog import render_discovered_catalog
from tools.validate_content import TODO_MARKER, validate_content


ROOT = Path(__file__).resolve().parents[1]


def _tooling_root(tmp_path):
    root = tmp_path / "project"
    shutil.copytree(ROOT / "src" / "app", root / "src" / "app")
    (root / "tests").mkdir(parents=True)
    return root


def _copy_validation_tools(root):
    (root / "tools").mkdir()
    for name in ("generate_content_catalog.py", "validate_content.py"):
        shutil.copy2(ROOT / "tools" / name, root / "tools" / name)


def _run_fixture_validator(root):
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


@pytest.mark.parametrize(
    ("content_type", "content_id", "directory", "primary_name", "symbol"),
    (
        ("enemy", "ashen_guard", "enemies", "enemy.py", "ENEMY"),
        ("weapon", "ashen_blade", "weapons", "weapon.py", "WEAPON"),
        ("drifter", "ashen_walker", "drifters", "drifter.py", "DRIFTER"),
        ("encounter", "ashen_ambush", "encounters", "encounter.py", "ENCOUNTER"),
        ("route", "ashen_road", "routes", "route.py", "ROUTE"),
    ),
)
def test_every_content_type_scaffolds_conventional_importable_output(
    tmp_path,
    content_type,
    content_id,
    directory,
    primary_name,
    symbol,
):
    root = _tooling_root(tmp_path)

    primary, test_path, catalog_path = scaffolder.scaffold_content(
        content_type,
        content_id,
        root=root,
    )

    assert primary == root / "src/app/content" / directory / content_id / primary_name
    assert test_path == root / "tests" / f"test_content_{content_type}_{content_id}.py"
    assert TODO_MARKER in primary.read_text(encoding="utf-8")
    assert f'__all__ = ["{symbol}"]' in primary.read_text(encoding="utf-8")
    assert b"\r\n" not in primary.read_bytes()
    assert b"\r\n" not in test_path.read_bytes()
    ast.parse(primary.read_text(encoding="utf-8"))
    ast.parse(test_path.read_text(encoding="utf-8"))
    ast.parse(catalog_path.read_text(encoding="utf-8"))
    assert catalog_path.read_text(encoding="utf-8") == render_discovered_catalog(
        **scaffolder._content_roots(root)
    )

    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(root / "src")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_path), "-q"],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "1 passed" in result.stdout


def test_scaffold_output_is_deterministic_across_independent_roots(tmp_path):
    roots = (_tooling_root(tmp_path / "first"), _tooling_root(tmp_path / "second"))
    outputs = []
    for root in roots:
        primary, test_path, catalog = scaffolder.scaffold_content(
            "enemy", "ashen_guard", root=root
        )
        outputs.append(
            (
                primary.read_bytes(),
                test_path.read_bytes(),
                catalog.read_bytes(),
            )
        )
    assert outputs[0] == outputs[1]


@pytest.mark.parametrize("content_id", ("UpperCase", "has-dash", "two words", "class", "_leading"))
def test_invalid_or_keyword_ids_refuse_without_mutation(tmp_path, content_id):
    root = _tooling_root(tmp_path)
    before = (root / "src/app/content/_generated_catalog.py").read_bytes()

    with pytest.raises(ValueError):
        scaffolder.scaffold_content("enemy", content_id, root=root)

    assert (root / "src/app/content/_generated_catalog.py").read_bytes() == before
    assert not (root / "tests" / f"test_content_enemy_{content_id}.py").exists()


def test_unknown_type_and_every_preflight_collision_refuse_without_overwrite(
    tmp_path,
    monkeypatch,
):
    root = _tooling_root(tmp_path)
    with pytest.raises(ValueError, match="unknown content type"):
        scaffolder.scaffold_content("item", "ashen_item", root=root)

    primary, test_path, catalog = scaffolder.scaffold_content(
        "weapon", "ashen_blade", root=root
    )
    original = (primary.read_bytes(), test_path.read_bytes(), catalog.read_bytes())
    with pytest.raises(FileExistsError):
        scaffolder.scaffold_content("weapon", "ashen_blade", root=root)
    assert (primary.read_bytes(), test_path.read_bytes(), catalog.read_bytes()) == original

    with pytest.raises(FileExistsError, match="persistence-key"):
        scaffolder.scaffold_content("weapon", "ashen__blade", root=root)

    monkeypatch.setattr(scaffolder, "_next_drifter_choice", lambda _root: "1")
    with pytest.raises(FileExistsError, match="choice collision"):
        scaffolder.scaffold_content("drifter", "choice_collision", root=root)

    monkeypatch.setattr(
        scaffolder,
        "_existing_route_node_ids",
        lambda _root: {"blocked_route_start"},
    )
    with pytest.raises(FileExistsError, match="route-node"):
        scaffolder.scaffold_content("route", "blocked_route", root=root)


def test_existing_generated_test_refuses_before_creating_package(tmp_path):
    root = _tooling_root(tmp_path)
    test_path = root / "tests/test_content_enemy_ashen_guard.py"
    test_path.write_text("owned by author\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        scaffolder.scaffold_content("enemy", "ashen_guard", root=root)

    assert test_path.read_text(encoding="utf-8") == "owned by author\n"
    assert not (root / "src/app/content/enemies/ashen_guard").exists()


def test_generation_failure_rolls_back_new_files_and_catalog(tmp_path, monkeypatch):
    root = _tooling_root(tmp_path)
    catalog = root / "src/app/content/_generated_catalog.py"
    before = catalog.read_bytes()

    def fail_write(*_args, **_kwargs):
        raise OSError("simulated catalog failure")

    monkeypatch.setattr(scaffolder, "write_catalog", fail_write)
    with pytest.raises(OSError, match="simulated catalog failure"):
        scaffolder.scaffold_content("enemy", "ashen_guard", root=root)

    assert catalog.read_bytes() == before
    assert not (root / "src/app/content/enemies/ashen_guard").exists()
    assert not (root / "tests/test_content_enemy_ashen_guard.py").exists()


def test_builtin_validation_is_read_only_and_has_no_todo_markers():
    tracked = tuple(
        sorted(
            (ROOT / "src/app/content").glob("**/*.py"),
            key=lambda path: path.as_posix(),
        )
    )
    before = {path: hashlib.sha256(path.read_bytes()).digest() for path in tracked}

    errors, records = validate_content()

    after = {path: hashlib.sha256(path.read_bytes()).digest() for path in tracked}
    assert errors == ()
    assert before == after
    assert {name: len(values) for name, values in records.items()} == {
        "enemy": 5,
        "weapon": 4,
        "drifter": 4,
        "encounter": 8,
        "route": 1,
    }


def test_todo_marker_is_actionable_and_removed_content_is_clear(tmp_path):
    root = _tooling_root(tmp_path)
    _copy_validation_tools(root)
    primary, _, _ = scaffolder.scaffold_content("enemy", "ashen_guard", root=root)
    unfinished = _run_fixture_validator(root)
    assert unfinished.returncode == 1
    assert "unfinished TODO(CONTENT-AUTHORING) marker" in unfinished.stderr
    assert "ashen_guard/enemy.py" in unfinished.stderr.replace("\\", "/")
    assert "Traceback" not in unfinished.stderr

    source = primary.read_text(encoding="utf-8")
    completed = source.replace(TODO_MARKER, "AUTHORED")
    primary.write_text(completed, encoding="utf-8")
    finished = _run_fixture_validator(root)
    assert finished.returncode == 0, finished.stderr
    assert "content valid: 6 enemies" in finished.stdout


def test_invalid_cross_reference_reports_without_traceback(tmp_path):
    root = _tooling_root(tmp_path)
    _copy_validation_tools(root)
    encounter = root / "src/app/content/encounters/surface_goblin_solo/encounter.py"
    encounter.write_text(
        encounter.read_text(encoding="utf-8").replace(
            'enemy_archetype_ids=("goblin",)',
            'enemy_archetype_ids=("missing_enemy",)',
        ),
        encoding="utf-8",
    )
    catalog = render_discovered_catalog(**scaffolder._content_roots(root))
    scaffolder.write_catalog(
        catalog,
        root / "src/app/content/_generated_catalog.py",
    )

    result = _run_fixture_validator(root)

    assert result.returncode == 1
    assert "unknown enemy archetype ID 'missing_enemy'" in result.stderr
    assert "surface_goblin_solo/encounter.py" in result.stderr.replace("\\", "/")
    assert "Traceback" not in result.stderr


def test_validator_and_resolver_share_authored_move_shape_authority():
    for spec in (*ENEMY_SPECS, *DRIFTER_SPECS):
        moves = spec.moves if hasattr(spec, "moves") else spec.combat_moves
        assert all(authored_move_rejection_reason(move) is None for move in moves)

    sample = DRIFTER_SPECS[0].combat_moves[0]
    unsupported = replace(sample, kind=MoveKind.UTILITY, mechanic="unknown_utility")
    assert authored_move_rejection_reason(unsupported) == "unsupported_mechanic"


def test_runtime_catalogs_contain_no_filesystem_discovery():
    for relative in (
        "src/app/content/catalog.py",
        "src/app/content/_generated_catalog.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert ".glob(" not in source
        assert "os.walk" not in source
        assert "importlib" not in source
