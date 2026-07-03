import ast
from pathlib import Path
from types import MappingProxyType

import pytest

from app.enemies import (
    Enemy,
    EnemyBehavior,
    EnemyCapability,
    EnemyRank,
    EnemyRole,
    EnemyState,
    create_enemy_state,
)
from app.enemies.factory import create_enemy_state as factory_create_enemy_state
from app.enemies.goblin.definition import Goblin
from app.enemies.goblin.registration import GOBLIN_REGISTRATION
from app.enemies.registry import get_enemy_registration
import app.enemies.registry as registry_module


ROOT = Path(__file__).resolve().parents[1]


def imported_modules(path):
    tree = ast.parse(path.read_text())
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)

    return tuple(modules)


def test_enemy_domain_public_imports_are_available():
    assert Enemy
    assert EnemyRank.COMMON
    assert EnemyRole.MELEE_SKIRMISHER
    assert EnemyBehavior.AGGRESSIVE
    assert EnemyCapability.BASIC_ATTACKS
    assert EnemyState
    assert create_enemy_state is factory_create_enemy_state
    assert Goblin
    assert GOBLIN_REGISTRATION.archetype_id == "goblin"
    assert get_enemy_registration("goblin") is GOBLIN_REGISTRATION


def test_builtin_enemy_registry_is_private_and_read_only():
    assert not hasattr(registry_module, "ENEMY_REGISTRY")
    assert isinstance(registry_module._ENEMY_REGISTRY, MappingProxyType)

    with pytest.raises(TypeError):
        registry_module._ENEMY_REGISTRY["replacement"] = get_enemy_registration("goblin")


def test_enemy_factory_does_not_directly_import_goblin():
    modules = imported_modules(ROOT / "src" / "app" / "enemies" / "factory.py")

    assert "app.enemies.goblin.definition" not in modules
    assert "app.enemies.goblin.scaling" not in modules
    assert all(not module.startswith("app.enemies.goblin") for module in modules)


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
