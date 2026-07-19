from dataclasses import FrozenInstanceError

import pytest

import app.combat.battle as battle_module
from app.combat.battle import Battle
from app.combat.resolver import CombatResolver
from app.combat.result import MoveResult
from app.enemies.goblin.definition import Goblin
from app.enemies.goblin_shaman.definition import GoblinShaman
from app.enemies.goblin_warrior.definition import GoblinWarrior
from app.enemies.state import EnemyState
from app.player.character import Brawler
from app.player.player_state import PlayerState
from app.presentation.battle_models import EnemyCombatantView


class RecordingRng:
    def __init__(self):
        self.randint_calls = []
        self.choice_calls = []

    def randint(self, start, end):
        self.randint_calls.append((start, end))
        return start

    def choice(self, options):
        options = tuple(options)
        self.choice_calls.append(options)
        return options[0]


class AcceptingResolver:
    def __init__(self):
        self.calls = []

    def resolve_move(self, actor, target, move_name, **kwargs):
        self.calls.append((actor, target, move_name, kwargs))
        return MoveResult(
            accepted=True,
            hit=True,
            move_name=move_name,
            resource_spent=0,
            damage=0,
            healing=0,
            statuses_applied=(),
            reason=None,
        )


class NoInputUI:
    def render(self, _view):
        pass

    def read_input(self, _view):
        raise AssertionError("input is not expected")


def _battle(enemies, **kwargs):
    return Battle(
        PlayerState(Brawler()),
        enemies,
        ui=NoInputUI(),
        **kwargs,
    )


def _goblins(count):
    return tuple(EnemyState(Goblin()) for _ in range(count))


def test_battle_normalizes_one_to_four_ordered_enemies():
    single = EnemyState(Goblin())
    assert _battle(single).enemies == (single,)

    for count in range(1, 5):
        enemies = list(_goblins(count))
        battle = _battle(enemies)

        assert isinstance(battle.enemies, tuple)
        assert battle.enemies == tuple(enemies)
        enemies.clear()
        assert len(battle.enemies) == count


@pytest.mark.parametrize(
    ("participants", "error_type"),
    [
        ([], ValueError),
        (_goblins(5), ValueError),
        ({EnemyState(Goblin())}, TypeError),
        ((enemy for enemy in _goblins(2)), TypeError),
        ([EnemyState(Goblin()), object()], TypeError),
    ],
)
def test_battle_rejects_invalid_participant_collections(participants, error_type):
    with pytest.raises(error_type):
        _battle(participants)


def test_battle_rejects_the_same_runtime_enemy_twice():
    enemy = EnemyState(Goblin())

    with pytest.raises(ValueError, match="same EnemyState"):
        _battle((enemy, enemy))


def test_target_ids_and_duplicate_labels_are_stable_from_authored_positions():
    enemies = (
        EnemyState(Goblin()),
        EnemyState(Goblin()),
        EnemyState(GoblinWarrior()),
        EnemyState(Goblin()),
    )
    battle = _battle(enemies)

    assert battle.enemy_target_ids == (
        "enemy_1",
        "enemy_2",
        "enemy_3",
        "enemy_4",
    )
    assert battle.enemy_display_labels == (
        "Goblin 1",
        "Goblin 2",
        "Goblin Warrior",
        "Goblin 3",
    )

    enemies[0].health.take_damage(enemies[0].health.maximum)
    assert battle.enemy_target_ids == (
        "enemy_1",
        "enemy_2",
        "enemy_3",
        "enemy_4",
    )
    assert battle.enemy_display_labels[1] == "Goblin 2"


def test_duplicate_archetypes_remain_independent_runtime_states():
    first, second = _goblins(2)
    battle = _battle((first, second))

    first.health.take_damage(10)
    first.mana_resource.set_maximum(5)
    first.mana_resource.restore(3)

    assert battle.enemies == (first, second)
    assert second.health.current == second.health.maximum
    assert second.mana_resource.maximum == 0


def test_single_enemy_compatibility_accessors_refuse_multi_enemy_fallback():
    single = _battle(EnemyState(Goblin()))
    single_view = single._build_view()
    assert single.foe is single.enemies[0]
    assert single_view.enemy is single_view.enemies[0]

    multi = _battle(_goblins(2))
    with pytest.raises(ValueError, match="single-enemy"):
        _ = multi.foe
    with pytest.raises(ValueError, match="single-enemy"):
        _ = multi._build_view().enemy


def test_multi_enemy_view_preserves_authored_identity_and_resources():
    goblin = EnemyState(Goblin())
    shaman = EnemyState(GoblinShaman())
    shaman.mana_resource.spend(5)
    battle = _battle((goblin, shaman))

    view = battle._build_view()

    assert tuple(enemy.target_id for enemy in view.enemies) == (
        "enemy_1",
        "enemy_2",
    )
    assert tuple(enemy.display_label for enemy in view.enemies) == (
        "Goblin",
        "Goblin Shaman",
    )
    assert view.enemies[0].mana_current is None
    assert view.enemies[1].mana_current == 20


def test_enemy_presentation_contract_is_immutable():
    view = _battle(EnemyState(Goblin()))._build_view().enemy

    assert isinstance(view, EnemyCombatantView)
    with pytest.raises(FrozenInstanceError):
        view.display_label = "Changed"


def test_battle_default_resolver_shares_the_explicit_rng():
    rng = RecordingRng()
    battle = _battle(EnemyState(Goblin()), rng=rng)

    assert isinstance(battle.resolver, CombatResolver)
    assert battle.resolver.rng is rng


def test_injected_resolver_retains_its_own_behavior():
    rng = RecordingRng()
    resolver = AcceptingResolver()
    battle = _battle(EnemyState(Goblin()), rng=rng, resolver=resolver)

    assert battle.resolver is resolver


def test_enemy_selection_uses_the_battle_rng_without_mutating_selection_state():
    rng = RecordingRng()
    resolver = AcceptingResolver()
    enemy = EnemyState(Goblin())
    battle = _battle(enemy, rng=rng, resolver=resolver)
    hp_before = enemy.health.current
    mana_before = enemy.mana_resource.current

    assert battle.enemy_action() is True

    assert rng.choice_calls == [enemy.combat_moves]
    assert enemy.health.current == hp_before
    assert enemy.mana_resource.current == mana_before
    assert resolver.calls[0][0] is enemy


def test_run_uses_the_injected_battle_rng_for_the_first_initiative_roll(
    monkeypatch,
):
    rng = RecordingRng()
    enemy = EnemyState(Goblin())
    battle = _battle(enemy, rng=rng)
    opportunities = []

    def accept_player_opportunity():
        opportunities.append("player")
        enemy.health.take_damage(enemy.health.maximum)
        return True

    def reject_enemy_opportunity():
        raise AssertionError("the injected initiative roll must select the player")

    battle.player_action = accept_player_opportunity
    battle.enemy_action = reject_enemy_opportunity
    monkeypatch.setattr(battle_module, "random", object())

    assert battle.run() == "player"
    assert rng.randint_calls == [(1, 2)]
    assert opportunities == ["player"]


@pytest.mark.parametrize("rng", [object(), type("OnlyRandint", (), {"randint": lambda *_: 1})()])
def test_battle_rejects_rngs_without_the_complete_boundary(rng):
    with pytest.raises(TypeError, match="rng must provide"):
        _battle(EnemyState(Goblin()), rng=rng)
