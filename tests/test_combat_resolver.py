import builtins
import inspect

from app.combat.enemy import Goblin
from app.combat.enemy_state import EnemyState
from app.combat.move import DamageType, Move, MoveKind, ResourceType, ScalingAttribute, TargetType
from app.combat.resolver import CombatResolver
from app.player.character import BlackMage, Brawler
from app.player.player_state import PlayerState


class ScriptedRng:
    def __init__(self, *rolls):
        self.rolls = list(rolls)
        self.calls = []

    def randint(self, start, end):
        self.calls.append((start, end))
        return self.rolls.pop(0)


class SimpleCombatant:
    def __init__(self, moves=()):
        self.display_name = "Simple"
        self.health = PlayerState(Brawler()).health
        self.mana_resource = PlayerState(Brawler()).mana_resource
        self.super_resource = PlayerState(Brawler()).super_resource
        self._combat_moves = tuple(moves)

    @property
    def combat_moves(self):
        return self._combat_moves

    def effective_stat(self, name):
        return {
            "constitution": 8,
            "spirit": 8,
            "intelligence": 8,
            "strength": 8,
            "dexterity": 8,
            "intuition": 8,
        }[name]

    def is_alive(self):
        return self.health.is_alive()


def make_move(
        name="test move",
        kind=MoveKind.DAMAGE,
        resource_type=ResourceType.NONE,
        resource_cost=0,
        power=10,
        scales_with=(ScalingAttribute.STRENGTH,),
        accuracy=100,
        target=TargetType.ENEMY,
        damage_type=DamageType.PHYSICAL,
        mechanic=None):
    return Move(
        name=name,
        kind=kind,
        resource_type=resource_type,
        resource_cost=resource_cost,
        power=power,
        scales_with=scales_with,
        accuracy=accuracy,
        target=target,
        damage_type=damage_type,
        mechanic=mechanic,
        description="A test move.",
    )


def add_move(actor, move):
    actor.character.combat_moves.append(move)
    return move


def test_owned_canonical_move_resolves_and_foreign_or_unknown_moves_are_rejected():
    actor = PlayerState(Brawler())
    target = EnemyState(Goblin())
    rng = ScriptedRng(1)

    result = CombatResolver(rng=rng).resolve_move(actor, target, "slash")

    assert result.accepted
    assert result.hit
    assert result.move_name == "slash"
    assert result.damage == 27
    assert target.health.current == 33
    assert actor.super_resource.current == 10
    assert rng.calls == [(1, 100)]

    foreign_move_name = PlayerState(BlackMage()).combat_moves[0].name
    actor_mana = actor.mana_resource.current
    actor_super = actor.super_resource.current
    target_hp = target.health.current
    rng = ScriptedRng(1)

    result = CombatResolver(rng=rng).resolve_move(actor, target, foreign_move_name)

    assert result.reason == "move_not_owned"
    assert not result.accepted
    assert actor.mana_resource.current == actor_mana
    assert actor.super_resource.current == actor_super
    assert target.health.current == target_hp
    assert rng.calls == []

    result = CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, target, "not a move")

    assert result.reason == "move_not_owned"


def test_duplicate_canonical_move_names_are_rejected_without_selecting_one():
    duplicate = make_move(name="duplicate")
    actor = SimpleCombatant(moves=(duplicate, duplicate))
    target = EnemyState(Goblin())
    rng = ScriptedRng(1)

    result = CombatResolver(rng=rng).resolve_move(actor, target, "duplicate")

    assert result.reason == "duplicate_move_name"
    assert not result.accepted
    assert rng.calls == []


def test_unsupported_kind_and_specialized_mechanic_are_rejected_before_mutation():
    utility = make_move(
        name="guard",
        kind=MoveKind.UTILITY,
        damage_type=DamageType.NONE,
        target=TargetType.SELF,
    )
    specialized = make_move(name="suplex", mechanic="stagger")
    actor = SimpleCombatant(moves=(utility, specialized))
    target = EnemyState(Goblin())

    for move_name, reason in (("guard", "unsupported_move_kind"), ("suplex", "unsupported_mechanic")):
        rng = ScriptedRng(1)
        actor_super = actor.super_resource.current
        target_hp = target.health.current

        result = CombatResolver(rng=rng).resolve_move(actor, target, move_name)

        assert result.reason == reason
        assert result.resource_spent == 0
        assert actor.super_resource.current == actor_super
        assert target.health.current == target_hp
        assert rng.calls == []


def test_self_and_enemy_target_rules_are_identity_based():
    actor = PlayerState(Brawler())
    other = EnemyState(Goblin())
    self_heal = add_move(
        actor,
        make_move(
            name="patch up",
            kind=MoveKind.HEALING,
            resource_type=ResourceType.NONE,
            damage_type=DamageType.HEALING,
            target=TargetType.SELF,
            scales_with=(ScalingAttribute.NONE,),
        ),
    )

    actor.health.take_damage(10)

    assert CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, actor, self_heal.name).accepted
    assert (
        CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, other, self_heal.name).reason
        == "invalid_target_type"
    )
    assert CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, other, "slash").accepted
    assert (
        CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, actor, "slash").reason
        == "invalid_target_type"
    )


def test_invalid_and_defeated_combatants_are_rejected_before_resource_spend():
    actor = PlayerState(Brawler())
    target = EnemyState(Goblin())

    assert CombatResolver(rng=ScriptedRng(1)).resolve_move(object(), target, "slash").reason == "invalid_actor"
    assert CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, object(), "slash").reason == "invalid_target"

    actor.health.take_damage(actor.health.maximum)
    assert CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, target, "slash").reason == "actor_defeated"

    actor = PlayerState(Brawler())
    target.health.take_damage(target.health.maximum)
    mana_before = actor.mana_resource.current
    assert CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, target, "jumping slash").reason == "target_defeated"
    assert actor.mana_resource.current == mana_before


def test_mana_spending_affordability_and_miss_behavior():
    actor = PlayerState(Brawler())
    target = EnemyState(Goblin())

    result = CombatResolver(rng=ScriptedRng(100)).resolve_move(actor, target, "jumping slash")

    assert result.accepted
    assert not result.hit
    assert result.resource_spent == 3
    assert actor.mana_resource.current == 7
    assert target.health.current == target.health.maximum
    assert actor.super_resource.current == 10

    actor = PlayerState(Brawler())
    target = EnemyState(Goblin())
    actor.mana_resource.spend(8)
    rng = ScriptedRng(1)

    result = CombatResolver(rng=rng).resolve_move(actor, target, "jumping slash")

    assert result.reason == "insufficient_mana"
    assert actor.mana_resource.current == 2
    assert actor.super_resource.current == 0
    assert rng.calls == []


def test_super_spending_affordability_and_generation_rules():
    actor = PlayerState(Brawler())
    target = EnemyState(Goblin())
    super_move = add_move(
        actor,
        make_move(
            name="finisher",
            resource_type=ResourceType.SUPER,
            resource_cost=100,
            accuracy=50,
            power=99,
        ),
    )

    assert (
        CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, target, super_move.name).reason
        == "insufficient_super"
    )
    assert actor.super_resource.current == 0

    actor.super_resource.gain(100)
    result = CombatResolver(rng=ScriptedRng(100)).resolve_move(actor, target, super_move.name)

    assert result.accepted
    assert not result.hit
    assert result.resource_spent == 100
    assert actor.super_resource.current == 0
    assert target.health.current == target.health.maximum


def test_super_generation_clamps_occurs_after_resolution_and_includes_zero_healing():
    actor = PlayerState(Brawler())
    target = EnemyState(Goblin())
    actor.super_resource.gain(95)

    result = CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, target, "slash")

    assert result.damage == 27
    assert target.health.current == 33
    assert actor.super_resource.current == 100

    healer = PlayerState(Brawler())
    heal = add_move(
        healer,
        make_move(
            name="steady breath",
            kind=MoveKind.HEALING,
            resource_type=ResourceType.NONE,
            damage_type=DamageType.HEALING,
            target=TargetType.SELF,
            scales_with=(ScalingAttribute.NONE,),
            power=10,
        ),
    )

    result = CombatResolver(rng=ScriptedRng(1)).resolve_move(healer, healer, heal.name)

    assert result.accepted
    assert result.healing == 0
    assert healer.super_resource.current == 10


def test_battle_ending_damage_still_generates_super():
    actor = PlayerState(Brawler())
    target = EnemyState(Goblin())
    target.health.take_damage(59)

    result = CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, target, "slash")

    assert result.damage == 1
    assert not target.is_alive()
    assert actor.super_resource.current == 10


def test_accuracy_uses_randint_one_to_one_hundred_and_roll_less_or_equal_hits():
    hit_actor = PlayerState(Brawler())
    target = EnemyState(Goblin())
    rng = ScriptedRng(92)

    result = CombatResolver(rng=rng).resolve_move(hit_actor, target, "slash")

    assert result.hit
    assert rng.calls == [(1, 100)]

    miss_actor = PlayerState(Brawler())
    rng = ScriptedRng(93)

    result = CombatResolver(rng=rng).resolve_move(miss_actor, EnemyState(Goblin()), "slash")

    assert not result.hit
    assert rng.calls == [(1, 100)]


def test_accuracy_zero_and_one_hundred_still_roll_exactly_once():
    actor = PlayerState(Brawler())
    certain = add_move(actor, make_move(name="certain", accuracy=100))
    impossible = add_move(actor, make_move(name="impossible", accuracy=0))

    rng = ScriptedRng(100)
    assert CombatResolver(rng=rng).resolve_move(actor, EnemyState(Goblin()), certain.name).hit
    assert rng.calls == [(1, 100)]

    rng = ScriptedRng(1)
    assert not CombatResolver(rng=rng).resolve_move(actor, EnemyState(Goblin()), impossible.name).hit
    assert rng.calls == [(1, 100)]


def test_scaling_uses_effective_stat_mean_weapon_bonuses_and_does_not_mutate_stats():
    actor = PlayerState(Brawler())
    target = EnemyState(Goblin())
    permanent_before = actor.character.permanent_stats.as_dict()
    hybrid = add_move(
        actor,
        make_move(
            name="hybrid mean",
            damage_type=DamageType.HYBRID,
            scales_with=(ScalingAttribute.STRENGTH, ScalingAttribute.DEXTERITY),
            power=10,
        ),
    )
    no_scale = add_move(
        actor,
        make_move(
            name="flat",
            scales_with=(ScalingAttribute.NONE,),
            power=10,
        ),
    )

    result = CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, target, hybrid.name)

    assert result.damage == 24
    assert actor.character.permanent_stats.as_dict() == permanent_before

    target = EnemyState(Goblin())
    result = CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, target, no_scale.name)

    assert result.damage == 10


def test_damage_formulas_for_physical_magical_hybrid_minimum_and_overkill():
    actor = PlayerState(Brawler())
    target = EnemyState(Goblin())
    magical = add_move(
        actor,
        make_move(
            name="magic",
            damage_type=DamageType.MAGICAL,
            scales_with=(ScalingAttribute.INTELLIGENCE,),
            power=10,
        ),
    )
    hybrid = add_move(
        actor,
        make_move(
            name="hybrid",
            damage_type=DamageType.HYBRID,
            scales_with=(ScalingAttribute.STRENGTH, ScalingAttribute.DEXTERITY),
            power=10,
        ),
    )

    assert CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, target, "slash").damage == 27
    assert CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, EnemyState(Goblin()), magical.name).damage == 15
    assert CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, EnemyState(Goblin()), hybrid.name).damage == 24

    weak = add_move(
        actor,
        make_move(
            name="tap",
            power=0,
            scales_with=(ScalingAttribute.NONE,),
        ),
    )
    sturdy_target = PlayerState(Brawler())

    assert CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, sturdy_target, weak.name).damage == 1

    nearly_defeated = EnemyState(Goblin())
    nearly_defeated.health.take_damage(59)

    assert CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, nearly_defeated, "slash").damage == 1
    assert nearly_defeated.health.current == 0


def test_healing_formula_clamps_and_reports_actual_restored_amount():
    actor = PlayerState(BlackMage())
    heal = add_move(
        actor,
        make_move(
            name="plain heal",
            kind=MoveKind.HEALING,
            resource_type=ResourceType.NONE,
            damage_type=DamageType.HEALING,
            target=TargetType.SELF,
            scales_with=(ScalingAttribute.INTELLIGENCE,),
            power=12,
        ),
    )

    actor.health.take_damage(9)
    result = CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, actor, heal.name)

    assert result.healing == 9
    assert actor.health.current == actor.health.maximum

    result = CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, actor, heal.name)

    assert result.healing == 0


def test_equivalent_player_and_enemy_runtime_combatants_resolve_without_type_branches():
    player = PlayerState(Brawler())
    enemy = EnemyState(Goblin())

    player_result = CombatResolver(rng=ScriptedRng(1)).resolve_move(player, enemy, "slash")
    enemy_result = CombatResolver(rng=ScriptedRng(1)).resolve_move(enemy, player, "slash")

    assert player_result.accepted
    assert enemy_result.accepted
    assert player_result.damage == 27
    assert enemy_result.damage == 8
    assert player.super_resource.current == 10
    assert enemy.super_resource.current == 10


def test_resolver_does_not_print_or_read_input(monkeypatch):
    actor = PlayerState(Brawler())
    target = EnemyState(Goblin())

    def fail(*args, **kwargs):
        raise AssertionError("interactive IO is not allowed")

    monkeypatch.setattr(builtins, "print", fail)
    monkeypatch.setattr(builtins, "input", fail)

    result = CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, target, "slash")

    assert result.accepted


def test_resolver_is_isolated_from_world_story_profile_and_duplicate_resources():
    import app.combat.resolver as resolver_module

    source = inspect.getsource(resolver_module)

    assert "StoryState" not in source
    assert "WorldState" not in source
    assert "profile" not in source
    assert "PlayerState" not in source
    assert "EnemyState" not in source
    assert "Health(" not in source
    assert "Mana(" not in source
    assert "Super(" not in source
