import ast
from pathlib import Path

import pytest

from app import randomness
from app.combat.battle import Battle
from app.combat.resolver import CombatResolver
from app.content.catalog import create_drifter, create_enemy_definition
from app.enemies.state import EnemyState
from app.player.player_state import PlayerState


APP_ROOT = Path(__file__).parents[1] / "src" / "app"
COMBAT_ROOT = APP_ROOT / "combat"


class _NativeBackend:
    def __init__(self):
        self.randint_calls = []
        self.choice_calls = []

    def randint(self, start, end):
        self.randint_calls.append((start, end))
        return "native-int"

    def choice(self, values):
        self.choice_calls.append(values)
        return "native-choice"


class _FallbackBackend:
    def __init__(self, values):
        self.values = iter(values)
        self.calls = []

    def getrandbits(self, bits):
        self.calls.append(bits)
        return next(self.values)


def test_native_backend_functions_are_delegated_without_fallback(monkeypatch):
    backend = _NativeBackend()
    monkeypatch.setattr(randomness, "_backend", backend)

    assert randomness.randint(2, 7) == "native-int"
    assert randomness.choice(("a", "b")) == "native-choice"
    assert backend.randint_calls == [(2, 7)]
    assert backend.choice_calls == [("a", "b")]


def test_fallback_randint_uses_rejection_sampling(monkeypatch):
    backend = _FallbackBackend((3, 2))
    monkeypatch.setattr(randomness, "_backend", backend)

    assert randomness.randint(1, 3) == 3
    assert backend.calls == [2, 2]


def test_fallback_randint_handles_degenerate_and_invalid_ranges(monkeypatch):
    backend = _FallbackBackend(())
    monkeypatch.setattr(randomness, "_backend", backend)

    assert randomness.randint(7, 7) == 7
    with pytest.raises(ValueError):
        randomness.randint(8, 7)


def test_fallback_choice_uses_rejection_sampling_and_preserves_sequence(monkeypatch):
    backend = _FallbackBackend((3, 1))
    monkeypatch.setattr(randomness, "_backend", backend)
    values = ("a", "b", "c")

    assert randomness.choice(values) == "b"
    assert backend.calls == [2, 2]

    with pytest.raises(IndexError):
        randomness.choice(())


def test_fallback_requires_getrandbits(monkeypatch):
    monkeypatch.setattr(randomness, "_backend", object())

    with pytest.raises(TypeError):
        randomness.randint(1, 2)
    with pytest.raises(TypeError):
        randomness.choice(("only", "value"))


def test_default_combat_resolver_uses_portable_randomness():
    assert CombatResolver().rng is randomness


def test_default_battle_uses_portable_randomness(monkeypatch):
    monkeypatch.setattr(randomness, "randint", lambda _start, _end: 1)
    monkeypatch.setattr(randomness, "choice", lambda values: values[0])

    battle = Battle(
        PlayerState(create_drifter("branoc")),
        EnemyState(create_enemy_definition("goblin")),
        ui=None,
    )

    assert battle.rng is randomness
    assert battle.resolver.rng is randomness


def _stdlib_random_imports(tree):
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "random":
                    imports.append(node)
        elif isinstance(node, ast.ImportFrom) and node.module == "random":
            imports.append(node)
    return imports


def test_combat_modules_do_not_import_stdlib_random():
    imports = []
    for path in sorted(COMBAT_ROOT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports.extend((path, node) for node in _stdlib_random_imports(tree))

    assert imports == []


@pytest.mark.parametrize(
    ("source", "targeted"),
    (
        ("import random", True),
        ("import random as rng", True),
        ("from random import randint", True),
        ("from random import choice", True),
        ("import app.randomness as random", False),
        ("from app import randomness", False),
    ),
)
def test_random_import_classifier_distinguishes_stdlib_from_adapter(source, targeted):
    tree = ast.parse(source)
    assert bool(_stdlib_random_imports(tree)) is targeted
