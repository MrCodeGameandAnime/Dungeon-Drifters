import ast
from pathlib import Path
from types import MappingProxyType

import pytest

from app.content import EnemySpec, StatBlockSpec
from app.content.catalog import ENEMY_SPECS, create_enemy_state, get_enemy_spec
import app.content.catalog as catalog_module
from app.enemies import (
    Enemy,
    EnemyBehavior,
    EnemyCapability,
    EnemyRank,
    EnemyRole,
    EnemyState,
)


ROOT = Path(__file__).resolve().parents[1]


def imported_modules(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)

    return tuple(modules)


def test_enemy_domain_public_imports_are_available():
    assert EnemySpec
    assert StatBlockSpec
    assert len(ENEMY_SPECS) == 5
    assert Enemy
    assert EnemyRank.COMMON
    assert EnemyRole.MELEE_SKIRMISHER
    assert EnemyBehavior.AGGRESSIVE
    assert EnemyCapability.BASIC_ATTACKS
    assert EnemyState
    assert create_enemy_state("goblin").archetype_id == "goblin"
    assert get_enemy_spec("goblin").name == "Goblin"


def test_builtin_enemy_catalog_is_private_and_read_only():
    assert not hasattr(catalog_module, "ENEMY_CATALOG")
    assert isinstance(catalog_module._ENEMY_CATALOG, MappingProxyType)

    with pytest.raises(TypeError):
        catalog_module._ENEMY_CATALOG["replacement"] = get_enemy_spec("goblin")


def test_runtime_catalog_does_not_scan_or_dynamically_import_content():
    modules = imported_modules(ROOT / "src" / "app" / "content" / "catalog.py")

    assert "pathlib" not in modules
    assert "pkgutil" not in modules
    assert "importlib" not in modules


def test_only_generated_catalog_imports_concrete_enemy_content():
    source_root = ROOT / "src" / "app"
    allowed = source_root / "content" / "_generated_catalog.py"
    content_root = source_root / "content" / "enemies"

    for path in source_root.rglob("*.py"):
        if path == allowed or content_root in path.parents:
            continue
        assert all(
            not module.startswith("app.content.enemies")
            for module in imported_modules(path)
        ), path


def test_combat_package_does_not_import_enemy_domain_or_concrete_archetypes():
    combat_paths = (
        ROOT / "src" / "app" / "combat" / "battle.py",
        ROOT / "src" / "app" / "combat" / "combat_state.py",
        ROOT / "src" / "app" / "combat" / "combatant.py",
        ROOT / "src" / "app" / "combat" / "move.py",
        ROOT / "src" / "app" / "combat" / "resolver.py",
        ROOT / "src" / "app" / "combat" / "result.py",
    )

    for path in combat_paths:
        modules = imported_modules(path)
        assert all(not module.startswith("app.enemies") for module in modules)
