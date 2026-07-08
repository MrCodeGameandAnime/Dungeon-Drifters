import builtins
import inspect

from app.enemies.definition import Enemy, EnemyBehavior, EnemyCapability, EnemyRank, EnemyRole
from app.enemies.goblin.definition import Goblin
from app.enemies.state import EnemyState
from app.combat.combat_state import CombatState
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
    def __init__(
            self,
            moves=(),
            generates_super=True,
            can_defend=False,
            effective_stats=None):
        self.display_name = "Simple"
        self.health = PlayerState(Brawler()).health
        self.mana_resource = PlayerState(Brawler()).mana_resource
        self.super_resource = PlayerState(Brawler()).super_resource
        self.generates_super = generates_super
        self.can_defend = can_defend
        self._combat_moves = tuple(moves)
        self._effective_stats = effective_stats or {
            "constitution": 8,
            "spirit": 8,
            "intelligence": 8,
            "strength": 8,
            "dexterity": 8,
            "intuition": 8,
        }

    @property
    def combat_moves(self):
        return self._combat_moves

    def effective_stat(self, name):
        return self._effective_stats[name]

    def defend_reduction_percent(self, damage_type):
        return 0

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


def create_super_capable_enemy_state():
    return create_enemy_state_with_capabilities(
        name="Test Super Enemy",
        archetype_id="test_super_enemy",
        rank=EnemyRank.BOSS,
        capabilities=(EnemyCapability.BASIC_ATTACKS, EnemyCapability.SUPER),
    )


def create_enemy_state_with_capabilities(
        capabilities,
        name="Test Enemy",
        archetype_id="test_enemy",
        rank=EnemyRank.ELITE):
    return EnemyState(
        Enemy(
            strn=3,
            con=2,
            intl=1,
            dex=1,
            hp=60,
            mana=0,
            name=name,
            archetype_id=archetype_id,
            rank=rank,
            role=EnemyRole.BOSS,
            behavior=EnemyBehavior.AGGRESSIVE,
            capabilities=capabilities,
            combat_moves=Goblin().combat_moves,
        )
    )


def test_owned_canonical_move_resolves_and_foreign_or_unknown_moves_are_rejected():
    actor = PlayerState(Brawler())
    target = EnemyState(Goblin())
    rng = ScriptedRng(1)

    result = CombatResolver(rng=rng).resolve_move(actor, target, "Crestgrave Reaping")

    assert result.accepted
    assert result.hit
    assert result.move_name == "Crestgrave Reaping"
    assert result.damage == 11
    assert target.health.current == 49
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
    assert CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, other, "Crestgrave Reaping").accepted
    assert (
        CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, actor, "Crestgrave Reaping").reason
        == "invalid_target_type"
    )


def test_invalid_and_defeated_combatants_are_rejected_before_resource_spend():
    actor = PlayerState(Brawler())
    target = EnemyState(Goblin())

    assert (
        CombatResolver(rng=ScriptedRng(1)).resolve_move(
            object(),
            target,
            "Crestgrave Reaping",
        ).reason
        == "invalid_actor"
    )
    assert (
        CombatResolver(rng=ScriptedRng(1)).resolve_move(
            actor,
            object(),
            "Crestgrave Reaping",
        ).reason
        == "invalid_target"
    )

    actor.health.take_damage(actor.health.maximum)
    assert (
        CombatResolver(rng=ScriptedRng(1)).resolve_move(
            actor,
            target,
            "Crestgrave Reaping",
        ).reason
        == "actor_defeated"
    )

    actor = PlayerState(Brawler())
    target.health.take_damage(target.health.maximum)
    mana_before = actor.mana_resource.current
    assert (
        CombatResolver(rng=ScriptedRng(1)).resolve_move(
            actor,
            target,
            "Ironwake Dismemberment",
        ).reason
        == "target_defeated"
    )
    assert actor.mana_resource.current == mana_before


def test_invalid_combat_state_precedence_follows_actor_and_target_validation():
    actor = PlayerState(Brawler())
    target = EnemyState(Goblin())
    invalid_combat_state = object()

    assert (
        CombatResolver(rng=ScriptedRng(1)).resolve_move(
            object(),
            target,
            "Crestgrave Reaping",
            combat_state=invalid_combat_state,
        ).reason
        == "invalid_actor"
    )

    defeated_actor = PlayerState(Brawler())
    defeated_actor.health.take_damage(defeated_actor.health.maximum)

    assert (
        CombatResolver(rng=ScriptedRng(1)).resolve_move(
            defeated_actor,
            target,
            "Crestgrave Reaping",
            combat_state=invalid_combat_state,
        ).reason
        == "actor_defeated"
    )

    assert (
        CombatResolver(rng=ScriptedRng(1)).resolve_move(
            actor,
            object(),
            "Crestgrave Reaping",
            combat_state=invalid_combat_state,
        ).reason
        == "invalid_target"
    )

    defeated_target = EnemyState(Goblin())
    defeated_target.health.take_damage(defeated_target.health.maximum)

    assert (
        CombatResolver(rng=ScriptedRng(1)).resolve_move(
            actor,
            defeated_target,
            "Crestgrave Reaping",
            combat_state=invalid_combat_state,
        ).reason
        == "target_defeated"
    )

    rng = ScriptedRng(1)
    mana_before = actor.mana_resource.current
    super_before = actor.super_resource.current
    target_hp_before = target.health.current

    result = CombatResolver(rng=rng).resolve_move(
        actor,
        target,
        "Crestgrave Reaping",
        combat_state=invalid_combat_state,
    )

    assert result.reason == "invalid_combat_state"
    assert actor.mana_resource.current == mana_before
    assert actor.super_resource.current == super_before
    assert target.health.current == target_hp_before
    assert rng.calls == []


def test_mana_spending_affordability_and_miss_behavior():
    actor = PlayerState(Brawler())
    target = EnemyState(Goblin())

    result = CombatResolver(rng=ScriptedRng(100)).resolve_move(
        actor,
        target,
        "Ghalmour Compression",
    )

    assert result.accepted
    assert not result.hit
    assert result.resource_spent == 5
    assert actor.mana_resource.current == 41
    assert target.health.current == target.health.maximum
    assert actor.super_resource.current == 0

    actor = PlayerState(Brawler())
    target = EnemyState(Goblin())
    actor.mana_resource.spend(42)
    rng = ScriptedRng(1)

    result = CombatResolver(rng=rng).resolve_move(actor, target, "Ghalmour Compression")

    assert result.reason == "insufficient_mana"
    assert actor.mana_resource.current == 4
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


def test_super_move_does_not_gain_non_super_action_bonus():
    actor = PlayerState(Brawler())
    target = EnemyState(Goblin())
    super_move = add_move(
        actor,
        make_move(
            name="certain finisher",
            resource_type=ResourceType.SUPER,
            resource_cost=100,
            accuracy=100,
        ),
    )
    actor.super_resource.gain(100)

    result = CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, target, super_move.name)

    assert result.accepted
    assert result.hit
    assert actor.super_resource.current == 0


def test_super_generation_clamps_occurs_after_landed_damage_hit():
    actor = PlayerState(Brawler())
    target = EnemyState(Goblin())
    actor.super_resource.gain(95)

    result = CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, target, "Crestgrave Reaping")

    assert result.damage == 11
    assert target.health.current == 49
    assert actor.super_resource.current == 100


def test_healing_action_does_not_generate_super():
    healer = PlayerState(Brawler())
    healer.health.take_damage(10)
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
    assert result.healing == 10
    assert healer.super_resource.current == 0


def test_battle_ending_damage_still_generates_super():
    actor = PlayerState(Brawler())
    target = EnemyState(Goblin())
    target.health.take_damage(59)

    result = CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, target, "Crestgrave Reaping")

    assert result.damage == 1
    assert not target.is_alive()
    assert actor.super_resource.current == 10


def test_accuracy_uses_randint_one_to_one_hundred_and_roll_less_or_equal_hits():
    hit_actor = PlayerState(Brawler())
    target = EnemyState(Goblin())
    rng = ScriptedRng(92)

    result = CombatResolver(rng=rng).resolve_move(hit_actor, target, "Crestgrave Reaping")

    assert result.hit
    assert rng.calls == [(1, 100)]

    miss_actor = PlayerState(Brawler())
    rng = ScriptedRng(93)

    result = CombatResolver(rng=rng).resolve_move(
        miss_actor,
        EnemyState(Goblin()),
        "Crestgrave Reaping",
    )

    assert not result.hit
    assert rng.calls == [(1, 100)]


def test_dexterity_accuracy_bonus_applies_to_final_hit_chance():
    examples = (
        (10, 50, 50, True),
        (10, 50, 51, False),
        (20, 50, 54, True),
        (20, 50, 55, False),
        (40, 50, 60, True),
        (40, 50, 61, False),
        (100, 70, 90, True),
        (100, 70, 91, False),
    )

    for dexterity, accuracy, roll, expected_hit in examples:
        move = make_move(
            name=f"dex {dexterity} acc {accuracy}",
            accuracy=accuracy,
            scales_with=(ScalingAttribute.NONE,),
        )
        actor = SimpleCombatant(
            moves=(move,),
            effective_stats={
                "constitution": 8,
                "spirit": 8,
                "intelligence": 8,
                "strength": 8,
                "dexterity": dexterity,
                "intuition": 8,
            },
        )

        result = CombatResolver(rng=ScriptedRng(roll)).resolve_move(
            actor,
            no_mitigation_target(),
            move.name,
        )

        assert result.hit is expected_hit


def test_dexterity_accuracy_bonus_caps_final_hit_chance_at_ninety_five():
    move = make_move(
        name="cap test",
        accuracy=90,
        scales_with=(ScalingAttribute.NONE,),
    )
    actor = SimpleCombatant(
        moves=(move,),
        effective_stats={
            "constitution": 8,
            "spirit": 8,
            "intelligence": 8,
            "strength": 8,
            "dexterity": 100,
            "intuition": 8,
        },
    )

    hit_result = CombatResolver(rng=ScriptedRng(95)).resolve_move(
        actor,
        no_mitigation_target(),
        move.name,
    )
    miss_result = CombatResolver(rng=ScriptedRng(96)).resolve_move(
        actor,
        no_mitigation_target(),
        move.name,
    )

    assert hit_result.hit
    assert not miss_result.hit


def test_low_dexterity_negative_accuracy_bonus_is_preserved():
    move = make_move(
        name="low dex test",
        accuracy=50,
        scales_with=(ScalingAttribute.NONE,),
    )
    actor = SimpleCombatant(
        moves=(move,),
        effective_stats={
            "constitution": 8,
            "spirit": 8,
            "intelligence": 8,
            "strength": 8,
            "dexterity": 5,
            "intuition": 8,
        },
    )

    hit_result = CombatResolver(rng=ScriptedRng(48)).resolve_move(
        actor,
        no_mitigation_target(),
        move.name,
    )
    miss_result = CombatResolver(rng=ScriptedRng(49)).resolve_move(
        actor,
        no_mitigation_target(),
        move.name,
    )

    assert hit_result.hit
    assert not miss_result.hit


def test_accuracy_zero_and_one_hundred_still_roll_exactly_once():
    actor = PlayerState(Brawler())
    certain = add_move(actor, make_move(name="certain", accuracy=100))
    impossible = add_move(actor, make_move(name="impossible", accuracy=0))

    rng = ScriptedRng(95)
    assert CombatResolver(rng=rng).resolve_move(actor, EnemyState(Goblin()), certain.name).hit
    assert rng.calls == [(1, 100)]

    rng = ScriptedRng(1)
    assert not CombatResolver(rng=rng).resolve_move(actor, EnemyState(Goblin()), impossible.name).hit
    assert rng.calls == [(1, 100)]


def combatant_with_primary_stat(move, stat_name, value):
    effective_stats = {
        "constitution": 1,
        "spirit": 1,
        "intelligence": 10,
        "strength": 10,
        "dexterity": 10,
        "intuition": 10,
    }
    effective_stats[stat_name] = value
    return SimpleCombatant(moves=(move,), effective_stats=effective_stats)


def no_mitigation_target():
    return SimpleCombatant(
        effective_stats={
            "constitution": 1,
            "spirit": 1,
            "intelligence": 10,
            "strength": 10,
            "dexterity": 10,
            "intuition": 10,
        }
    )


def test_damage_output_uses_basis_point_primary_stat_scaling():
    examples = (
        (ScalingAttribute.STRENGTH, "strength", 10, 20),
        (ScalingAttribute.STRENGTH, "strength", 20, 25),
        (ScalingAttribute.DEXTERITY, "dexterity", 20, 25),
        (ScalingAttribute.INTELLIGENCE, "intelligence", 20, 25),
        (ScalingAttribute.STRENGTH, "strength", 5, 17),
    )

    for attribute, stat_name, stat_value, expected_damage in examples:
        move = make_move(
            name=f"{attribute.value} {stat_value}",
            power=20,
            scales_with=(attribute,),
        )
        actor = combatant_with_primary_stat(move, stat_name, stat_value)

        result = CombatResolver(rng=ScriptedRng(1)).resolve_move(
            actor,
            no_mitigation_target(),
            move.name,
        )

        assert result.damage == expected_damage


def test_damage_output_averages_supported_scaling_and_ignores_unsupported_attributes():
    supported_average = make_move(
        name="supported average",
        power=20,
        scales_with=(ScalingAttribute.STRENGTH, ScalingAttribute.DEXTERITY),
    )
    supported_actor = SimpleCombatant(
        moves=(supported_average,),
        effective_stats={
            "constitution": 1,
            "spirit": 1,
            "intelligence": 10,
            "strength": 20,
            "dexterity": 10,
            "intuition": 10,
        },
    )

    assert (
        CombatResolver(rng=ScriptedRng(1)).resolve_move(
            supported_actor,
            no_mitigation_target(),
            supported_average.name,
        ).damage
        == 22
    )

    intelligence_and_spirit = make_move(
        name="intelligence and spirit",
        power=20,
        scales_with=(ScalingAttribute.INTELLIGENCE, ScalingAttribute.SPIRIT),
    )
    intelligence_actor = SimpleCombatant(
        moves=(intelligence_and_spirit,),
        effective_stats={
            "constitution": 1,
            "spirit": 1,
            "intelligence": 20,
            "strength": 10,
            "dexterity": 10,
            "intuition": 10,
        },
    )

    assert (
        CombatResolver(rng=ScriptedRng(1)).resolve_move(
            intelligence_actor,
            no_mitigation_target(),
            intelligence_and_spirit.name,
        ).damage
        == 25
    )

    for scales_with in (
            (ScalingAttribute.SPIRIT,),
            (ScalingAttribute.NONE,),
    ):
        move = make_move(
            name=f"unsupported {scales_with[0].value}",
            power=20,
            scales_with=scales_with,
        )
        actor = SimpleCombatant(moves=(move,))

        assert (
            CombatResolver(rng=ScriptedRng(1)).resolve_move(
                actor,
                no_mitigation_target(),
                move.name,
            ).damage
            == 20
        )


def test_damage_scaling_uses_effective_stat_weapon_bonuses_and_does_not_mutate_stats():
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

    assert result.damage == 11
    assert actor.character.permanent_stats.as_dict() == permanent_before

    target = EnemyState(Goblin())
    result = CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, target, no_scale.name)

    assert result.damage == 11


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

    assert (
        CombatResolver(rng=ScriptedRng(1)).resolve_move(
            actor,
            target,
            "Crestgrave Reaping",
        ).damage
        == 11
    )
    assert CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, EnemyState(Goblin()), magical.name).damage == 8
    assert CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, EnemyState(Goblin()), hybrid.name).damage == 11

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

    assert (
        CombatResolver(rng=ScriptedRng(1)).resolve_move(
            actor,
            nearly_defeated,
            "Crestgrave Reaping",
        ).damage
        == 1
    )
    assert nearly_defeated.health.current == 0


def test_non_defended_resolver_results_remain_unchanged_with_optional_combat_state():
    actor = PlayerState(Brawler())
    target_without_state = EnemyState(Goblin())
    target_with_state = EnemyState(Goblin())

    without_state = CombatResolver(rng=ScriptedRng(1)).resolve_move(
        actor,
        target_without_state,
        "Crestgrave Reaping",
    )
    actor = PlayerState(Brawler())
    with_state = CombatResolver(rng=ScriptedRng(1)).resolve_move(
        actor,
        target_with_state,
        "Crestgrave Reaping",
        combat_state=CombatState(),
    )

    assert without_state.damage == 11
    assert with_state.damage == 11
    assert without_state.hit == with_state.hit


def test_strength_physical_negation_applies_only_to_incoming_physical_damage():
    actor = SimpleCombatant(
        moves=(
            make_move(
                name="physical",
                power=20,
                damage_type=DamageType.PHYSICAL,
                scales_with=(ScalingAttribute.NONE,),
            ),
            make_move(
                name="magical",
                power=20,
                damage_type=DamageType.MAGICAL,
                scales_with=(ScalingAttribute.NONE,),
            ),
        ),
    )

    examples = (
        (10, 20),
        (20, 19),
        (40, 17),
        (100, 14),
    )

    for strength, expected_physical_damage in examples:
        target = SimpleCombatant(
            effective_stats={
                "constitution": 1,
                "spirit": 1,
                "intelligence": 8,
                "strength": strength,
                "dexterity": 8,
                "intuition": 8,
            },
        )

        physical_result = CombatResolver(rng=ScriptedRng(1)).resolve_move(
            actor,
            target,
            "physical",
        )
        magical_result = CombatResolver(rng=ScriptedRng(1)).resolve_move(
            actor,
            target,
            "magical",
        )

        assert physical_result.damage == expected_physical_damage
        assert magical_result.damage == 20


def test_low_strength_targets_can_take_extra_physical_damage_per_helper_contract():
    actor = SimpleCombatant(
        moves=(
            make_move(
                name="physical",
                power=20,
                damage_type=DamageType.PHYSICAL,
                scales_with=(ScalingAttribute.NONE,),
            ),
        ),
    )
    target = SimpleCombatant(
        effective_stats={
            "constitution": 1,
            "spirit": 1,
            "intelligence": 8,
            "strength": 3,
            "dexterity": 8,
            "intuition": 8,
        },
    )

    result = CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, target, "physical")

    assert result.damage == 21


def test_strength_physical_negation_preserves_minimum_landed_damage_of_one():
    actor = SimpleCombatant(
        moves=(
            make_move(
                name="tap",
                power=0,
                damage_type=DamageType.PHYSICAL,
                scales_with=(ScalingAttribute.NONE,),
            ),
        ),
    )
    target = SimpleCombatant(
        effective_stats={
            "constitution": 100,
            "spirit": 8,
            "intelligence": 8,
            "strength": 100,
            "dexterity": 8,
            "intuition": 8,
        },
    )

    result = CombatResolver(rng=ScriptedRng(1)).resolve_move(actor, target, "tap")

    assert result.damage == 1


def test_defended_damage_uses_enemy_fixed_reductions_and_floors_reduction_amount():
    examples = (
        (DamageType.PHYSICAL, 5, 3),
        (DamageType.MAGICAL, 5, 3),
        (DamageType.HYBRID, 5, 4),
        (DamageType.PHYSICAL, 20, 11),
        (DamageType.MAGICAL, 20, 12),
        (DamageType.HYBRID, 20, 14),
    )

    for damage_type, power, expected_damage in examples:
        move = make_move(
            name=f"{damage_type.value} {power}",
            power=power,
            damage_type=damage_type,
            scales_with=(ScalingAttribute.NONE,),
        )
        actor = SimpleCombatant(moves=(move,))
        target = create_enemy_state_with_capabilities(
            capabilities=(EnemyCapability.BASIC_ATTACKS, EnemyCapability.DEFEND),
        )
        combat_state = CombatState()
        combat_state.activate_defend(target)

        result = CombatResolver(rng=ScriptedRng(1)).resolve_move(
            actor,
            target,
            move.name,
            combat_state=combat_state,
        )

        assert result.damage == expected_damage


def test_defend_still_reduces_damage_after_strength_negation():
    move = make_move(
        name="physical 20",
        power=20,
        damage_type=DamageType.PHYSICAL,
        scales_with=(ScalingAttribute.NONE,),
    )
    actor = SimpleCombatant(moves=(move,))
    target = create_enemy_state_with_capabilities(
        capabilities=(EnemyCapability.BASIC_ATTACKS, EnemyCapability.DEFEND),
    )

    without_defend = CombatResolver(rng=ScriptedRng(1)).resolve_move(
        actor,
        target,
        move.name,
    )

    combat_state = CombatState()
    combat_state.activate_defend(target)
    with_defend = CombatResolver(rng=ScriptedRng(1)).resolve_move(
        actor,
        target,
        move.name,
        combat_state=combat_state,
    )

    assert without_defend.damage == 21
    assert with_defend.damage == 11


def test_defended_damage_uses_player_stat_scaled_reductions_and_minimum_one():
    attacker = EnemyState(Goblin())
    defender = PlayerState(Brawler())
    combat_state = CombatState()
    combat_state.activate_defend(defender)

    result = CombatResolver(rng=ScriptedRng(1)).resolve_move(
        attacker,
        defender,
        "slash",
        combat_state=combat_state,
    )

    assert result.damage == 2

    magical = make_move(
        name="magic",
        power=20,
        damage_type=DamageType.MAGICAL,
        scales_with=(ScalingAttribute.NONE,),
    )
    hybrid = make_move(
        name="hybrid",
        power=20,
        damage_type=DamageType.HYBRID,
        scales_with=(ScalingAttribute.NONE,),
    )
    attacker = SimpleCombatant(moves=(magical, hybrid))

    expected = {
        magical.name: 15,
        hybrid.name: 15,
    }

    for move_name, expected_damage in expected.items():
        defender = PlayerState(Brawler())
        combat_state = CombatState()
        combat_state.activate_defend(defender)

        result = CombatResolver(rng=ScriptedRng(1)).resolve_move(
            attacker,
            defender,
            move_name,
            combat_state=combat_state,
        )

        assert result.damage == expected_damage

    weak = make_move(
        name="weak",
        power=0,
        scales_with=(ScalingAttribute.NONE,),
    )
    attacker = SimpleCombatant(moves=(weak,))
    defender = PlayerState(Brawler())
    combat_state = CombatState()
    combat_state.activate_defend(defender)

    result = CombatResolver(rng=ScriptedRng(1)).resolve_move(
        attacker,
        defender,
        weak.name,
        combat_state=combat_state,
    )

    assert result.damage == 1


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


def test_accepted_action_completion_consumes_opposing_defend_for_hits_misses_heals_and_defend():
    defender = EnemyState(Goblin())
    attacker = PlayerState(Brawler())
    combat_state = CombatState()
    combat_state.activate_defend(defender)

    hit = CombatResolver(rng=ScriptedRng(1)).resolve_move(
        attacker,
        defender,
        "Crestgrave Reaping",
        combat_state=combat_state,
    )
    assert hit.accepted
    combat_state.complete_accepted_action(attacker, opposing_combatants=(defender,))
    assert not combat_state.is_defending(defender)

    defender = EnemyState(Goblin())
    attacker = PlayerState(Brawler())
    miss_move = add_move(attacker, make_move(name="miss", accuracy=0))
    combat_state = CombatState()
    combat_state.activate_defend(defender)

    miss = CombatResolver(rng=ScriptedRng(1)).resolve_move(
        attacker,
        defender,
        miss_move.name,
        combat_state=combat_state,
    )
    assert miss.accepted
    assert not miss.hit
    combat_state.complete_accepted_action(attacker, opposing_combatants=(defender,))
    assert not combat_state.is_defending(defender)

    opponent = EnemyState(Goblin())
    healer = PlayerState(Brawler())
    heal = add_move(
        healer,
        make_move(
            name="heal self",
            kind=MoveKind.HEALING,
            damage_type=DamageType.HEALING,
            target=TargetType.SELF,
            scales_with=(ScalingAttribute.NONE,),
        ),
    )
    combat_state = CombatState()
    combat_state.activate_defend(opponent)

    healing = CombatResolver(rng=ScriptedRng(1)).resolve_move(
        healer,
        healer,
        heal.name,
        combat_state=combat_state,
    )
    assert healing.accepted
    combat_state.complete_accepted_action(healer, opposing_combatants=(opponent,))
    assert not combat_state.is_defending(opponent)

    actor = PlayerState(Brawler())
    opponent = EnemyState(Goblin())
    combat_state = CombatState()
    combat_state.activate_defend(opponent)

    defend = CombatResolver(rng=ScriptedRng(1)).resolve_defend(actor, combat_state)
    assert defend.accepted
    combat_state.complete_accepted_action(actor, opposing_combatants=(opponent,))
    assert combat_state.is_defending(actor)
    assert not combat_state.is_defending(opponent)


def test_rejected_action_does_not_consume_defend_or_advance_turn():
    actor = PlayerState(Brawler())
    defender = EnemyState(Goblin())
    combat_state = CombatState()
    combat_state.activate_defend(defender)

    result = CombatResolver(rng=ScriptedRng(1)).resolve_move(
        actor,
        defender,
        "unknown",
        combat_state=combat_state,
    )

    assert not result.accepted
    assert combat_state.is_defending(defender)
    assert combat_state.turn_count == 0


def test_resolve_defend_validation_mutation_and_no_super_gain():
    actor = PlayerState(Brawler())
    combat_state = CombatState()

    result = CombatResolver(rng=ScriptedRng(1)).resolve_defend(actor, combat_state)

    assert result.accepted
    assert not result.hit
    assert result.move_name == "Defend"
    assert result.resource_spent == 0
    assert result.damage == 0
    assert result.healing == 0
    assert result.statuses_applied == ()
    assert result.reason is None
    assert combat_state.is_defending(actor)
    assert combat_state.turn_count == 0
    assert actor.super_resource.current == 0


def test_rejected_defend_does_not_mutate_state_or_gain_super():
    actor = PlayerState(Brawler())
    combat_state = CombatState()

    result = CombatResolver(rng=ScriptedRng(1)).resolve_defend(object(), combat_state)

    assert result.reason == "invalid_actor"
    assert actor.super_resource.current == 0
    assert combat_state.turn_count == 0

    actor.health.take_damage(actor.health.maximum)
    result = CombatResolver(rng=ScriptedRng(1)).resolve_defend(actor, combat_state)

    assert result.reason == "actor_defeated"
    assert not combat_state.is_defending(actor)
    assert actor.super_resource.current == 0

    actor = PlayerState(Brawler())
    result = CombatResolver(rng=ScriptedRng(1)).resolve_defend(actor, object())

    assert result.reason == "invalid_combat_state"
    assert actor.super_resource.current == 0


def test_enemy_defend_capability_does_not_generate_super():
    goblin = EnemyState(Goblin())
    combat_state = CombatState()

    result = CombatResolver(rng=ScriptedRng(1)).resolve_defend(goblin, combat_state)

    assert result.reason == "defend_not_available"
    assert not goblin.can_defend
    assert goblin.super_resource.current == 0
    assert not combat_state.is_defending(goblin)

    defender_without_super = create_enemy_state_with_capabilities(
        capabilities=(EnemyCapability.BASIC_ATTACKS, EnemyCapability.DEFEND),
    )
    result = CombatResolver(rng=ScriptedRng(1)).resolve_defend(
        defender_without_super,
        combat_state,
    )

    assert result.accepted
    assert defender_without_super.can_defend
    assert defender_without_super.super_resource.current == 0

    defender_with_super = create_enemy_state_with_capabilities(
        capabilities=(
            EnemyCapability.BASIC_ATTACKS,
            EnemyCapability.DEFEND,
            EnemyCapability.SUPER,
        ),
        name="Defending Boss",
        archetype_id="defending_boss",
        rank=EnemyRank.BOSS,
    )
    result = CombatResolver(rng=ScriptedRng(1)).resolve_defend(
        defender_with_super,
        CombatState(),
    )

    assert result.accepted
    assert defender_with_super.super_resource.current == 0


def test_equivalent_player_and_enemy_runtime_combatants_resolve_without_type_branches():
    player = PlayerState(Brawler())
    enemy = EnemyState(Goblin())

    player_result = CombatResolver(rng=ScriptedRng(1)).resolve_move(
        player,
        enemy,
        "Crestgrave Reaping",
    )
    enemy_result = CombatResolver(rng=ScriptedRng(1)).resolve_move(enemy, player, "slash")

    assert player_result.accepted
    assert enemy_result.accepted
    assert player_result.damage == 11
    assert enemy_result.damage == 3
    assert player.super_resource.current == 10
    assert enemy.super_resource.current == 0


def test_common_goblin_non_super_actions_do_not_generate_super_on_hit_or_miss():
    target = PlayerState(Brawler())
    hit_actor = EnemyState(Goblin())

    hit_result = CombatResolver(rng=ScriptedRng(1)).resolve_move(hit_actor, target, "slash")

    assert hit_result.accepted
    assert hit_result.hit
    assert hit_actor.super_resource.current == 0

    miss_actor = EnemyState(Goblin())

    miss_result = CombatResolver(rng=ScriptedRng(100)).resolve_move(
        miss_actor,
        PlayerState(Brawler()),
        "slash",
    )

    assert miss_result.accepted
    assert not miss_result.hit
    assert miss_actor.super_resource.current == 0


def test_enemy_with_explicit_super_capability_generates_super():
    actor = create_super_capable_enemy_state()
    target = PlayerState(Brawler())

    result = CombatResolver(rng=ScriptedRng(1)).resolve_move(
        actor,
        target,
        "slash",
    )

    assert result.accepted
    assert actor.generates_super
    assert actor.super_resource.current == 10


def test_every_ordinary_goblin_move_is_resolver_supported_without_filtering():
    move_names = tuple(move.name for move in Goblin().combat_moves)

    assert move_names == ("slash", "jumping slash")

    for move_name in move_names:
        result = CombatResolver(rng=ScriptedRng(1)).resolve_move(
            EnemyState(Goblin()),
            PlayerState(Brawler()),
            move_name,
        )

        assert result.accepted
        assert result.reason is None


def test_resolver_does_not_print_or_read_input(monkeypatch):
    actor = PlayerState(Brawler())
    target = EnemyState(Goblin())

    def fail(*args, **kwargs):
        raise AssertionError("interactive IO is not allowed")

    monkeypatch.setattr(builtins, "print", fail)
    monkeypatch.setattr(builtins, "input", fail)

    result = CombatResolver(rng=ScriptedRng(1)).resolve_move(
        actor,
        target,
        "Crestgrave Reaping",
    )

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
