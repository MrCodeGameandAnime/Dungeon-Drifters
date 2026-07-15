"""Mechanical structured combat resolver."""

import random

from app.combat.combat_state import CombatState, HEAL_COOLDOWN_ACTIONS
from app.combat.combatant import Combatant
from app.combat.move import DamageType, MoveKind, ResourceType, ScalingAttribute, TargetType
from app.combat.result import MoveResult
from app.player import scaling


BASIS_POINTS = 10_000
MAX_ORDINARY_HIT_CHANCE = 95
MIN_ORDINARY_HIT_CHANCE = 5
BASE_ORDINARY_CRIT_CHANCE = 0
MAX_ORDINARY_CRIT_CHANCE = 35
CRITICAL_DAMAGE_MULTIPLIER_PERCENT = 150
SUPPORTED_MECHANICS = (None, "basic_attack", "heavy_attack")
SUPER_GAIN_PER_LANDED_NON_SUPER_DAMAGE = 10
HEALING_ROLL_MIN = 10
HEALING_ROLL_MAX = 16


class CombatResolver:
    def __init__(self, rng=random):
        self.rng = rng

    def resolve_move(self, actor, target, move_name, *, combat_state=None):
        result_move_name = move_name if isinstance(move_name, str) and move_name else "unknown"

        if not _is_valid_combatant(actor):
            return _rejected(result_move_name, "invalid_actor")
        if not actor.is_alive():
            return _rejected(result_move_name, "actor_defeated")

        if not _is_valid_combatant(target):
            return _rejected(result_move_name, "invalid_target")
        if not target.is_alive():
            return _rejected(result_move_name, "target_defeated")

        if not _is_valid_optional_combat_state(combat_state):
            return _rejected(result_move_name, "invalid_combat_state")

        move, reason = _resolve_owned_move(actor, move_name)
        if reason is not None:
            return _rejected(result_move_name, reason)

        if move.kind == MoveKind.UTILITY:
            if move.mechanic != "brace":
                reason = "unsupported_move_kind" if move.mechanic is None else "unsupported_mechanic"
                return _rejected(move.name, reason)
        elif not _is_supported_move_kind(move):
            return _rejected(move.name, "unsupported_move_kind")

        if move.kind != MoveKind.UTILITY and move.mechanic not in SUPPORTED_MECHANICS:
            return _rejected(move.name, "unsupported_mechanic")

        if not _is_valid_target_type(actor, target, move):
            return _rejected(move.name, "invalid_target_type")

        if move.kind == MoveKind.UTILITY and not isinstance(combat_state, CombatState):
            return _rejected(move.name, "invalid_combat_state")

        affordable, insufficient_reason = _can_afford(actor, move)
        if not affordable:
            return _rejected(move.name, insufficient_reason)

        resource_spent = _spend_resource(actor, move)

        if move.kind == MoveKind.UTILITY:
            combat_state.activate_brace(actor)
            return MoveResult(
                accepted=True,
                hit=True,
                move_name=move.name,
                resource_spent=resource_spent,
                damage=0,
                healing=0,
                statuses_applied=(),
                reason=None,
                critical=False,
            )

        follow_up_damage_bonus_percent = 0
        if move.mechanic == "heavy_attack" and combat_state is not None:
            follow_up_damage_bonus_percent = (
                combat_state.consume_brace_follow_up_damage_bonus_percent(
                    actor,
                    move.mechanic,
                )
            )

        roll = self.rng.randint(1, 100)
        hit = roll <= _final_hit_chance(actor, target, move)

        damage = 0
        healing = 0
        critical = False
        if hit:
            if move.kind == MoveKind.DAMAGE:
                critical = _rolled_critical_hit(actor, self.rng)
                damage = _apply_damage(
                    actor,
                    target,
                    move,
                    combat_state=combat_state,
                    critical=critical,
                    follow_up_damage_bonus_percent=follow_up_damage_bonus_percent,
                )
            elif move.kind == MoveKind.HEALING:
                healing = _apply_healing(actor, target, move)

        if hit and move.kind == MoveKind.DAMAGE and move.resource_type != ResourceType.SUPER:
            _grant_super_for_landed_non_super_damage(actor)

        return MoveResult(
            accepted=True,
            hit=hit,
            move_name=move.name,
            resource_spent=resource_spent,
            damage=damage,
            healing=healing,
            statuses_applied=(),
            reason=None,
            critical=critical,
        )

    def resolve_defend(self, actor, combat_state):
        if not _is_valid_combatant(actor):
            return _rejected("Defend", "invalid_actor")
        if not actor.is_alive():
            return _rejected("Defend", "actor_defeated")
        if not isinstance(combat_state, CombatState):
            return _rejected("Defend", "invalid_combat_state")
        if not actor.can_defend:
            return _rejected("Defend", "defend_not_available")

        combat_state.activate_defend(actor)

        return MoveResult(
            accepted=True,
            hit=False,
            move_name="Defend",
            resource_spent=0,
            damage=0,
            healing=0,
            statuses_applied=(),
            reason=None,
            critical=False,
        )

    def resolve_heal(self, actor, *, combat_state):
        if not _is_valid_combatant(actor):
            return _rejected("Heal", "invalid_actor")
        if not actor.is_alive():
            return _rejected("Heal", "actor_defeated")
        if not isinstance(combat_state, CombatState):
            return _rejected("Heal", "invalid_combat_state")
        if actor.health.current >= actor.health.maximum:
            return _rejected("Heal", "heal_at_full_health")
        if combat_state.heal_cooldown_remaining(actor) > 0:
            return _rejected("Heal", "heal_cooldown")

        rolled_healing = self.rng.randint(HEALING_ROLL_MIN, HEALING_ROLL_MAX)
        rolled_healing += actor.effective_stat("constitution")
        before = actor.health.current
        actor.health.heal(rolled_healing)
        actual_healing = actor.health.current - before
        combat_state.start_heal_cooldown(actor, HEAL_COOLDOWN_ACTIONS)

        return MoveResult(
            accepted=True,
            hit=True,
            move_name="Heal",
            resource_spent=0,
            damage=0,
            healing=actual_healing,
            statuses_applied=(),
            reason=None,
            critical=False,
        )


def _rejected(move_name, reason):
    return MoveResult(
        accepted=False,
        hit=False,
        move_name=move_name,
        resource_spent=0,
        damage=0,
        healing=0,
        statuses_applied=(),
        reason=reason,
        critical=False,
    )


def _is_valid_combatant(value):
    if not isinstance(value, Combatant):
        return False

    try:
        value.health
        value.mana_resource
        value.super_resource
        value.generates_super
        value.can_defend
        value.combat_moves
        value.display_name
    except Exception:
        return False

    return (
        callable(getattr(value, "effective_stat", None))
        and callable(getattr(value, "defend_reduction_percent", None))
        and callable(getattr(value, "is_alive", None))
    )


def _is_valid_optional_combat_state(value):
    return value is None or isinstance(value, CombatState)


def _resolve_owned_move(actor, move_name):
    if not isinstance(move_name, str) or not move_name:
        return None, "move_not_owned"

    matches = [move for move in actor.combat_moves if move.name == move_name]
    if not matches:
        return None, "move_not_owned"
    if len(matches) > 1:
        return None, "duplicate_move_name"

    return matches[0], None


def _is_supported_move_kind(move):
    if move.kind == MoveKind.DAMAGE:
        return move.damage_type in {
            DamageType.PHYSICAL,
            DamageType.MAGICAL,
            DamageType.HYBRID,
        }
    if move.kind == MoveKind.HEALING:
        return move.damage_type == DamageType.HEALING
    return False


def _is_valid_target_type(actor, target, move):
    if move.target == TargetType.SELF:
        return target is actor
    if move.target == TargetType.ENEMY:
        return target is not actor

    return False


def _can_afford(actor, move):
    if move.resource_type == ResourceType.NONE:
        return True, None
    if move.resource_type == ResourceType.MANA:
        if actor.mana_resource.can_afford(move.resource_cost):
            return True, None
        return False, "insufficient_mana"
    if move.resource_type == ResourceType.SUPER:
        if actor.super_resource.can_afford(move.resource_cost):
            return True, None
        return False, "insufficient_super"

    return False, "unsupported_move_kind"


def _spend_resource(actor, move):
    if move.resource_type == ResourceType.NONE:
        return 0
    if move.resource_type == ResourceType.MANA:
        actor.mana_resource.spend(move.resource_cost)
        return move.resource_cost
    if move.resource_type == ResourceType.SUPER:
        actor.super_resource.spend(move.resource_cost)
        return move.resource_cost

    return 0


def _scaling_value(actor, move):
    scaling_attributes = tuple(
        attribute for attribute in move.scales_with if attribute != ScalingAttribute.NONE
    )
    if not scaling_attributes:
        return 0

    values = [actor.effective_stat(attribute.value) for attribute in scaling_attributes]
    return sum(values) // len(values)


def _apply_damage(
        actor,
        target,
        move,
        *,
        combat_state=None,
        critical=False,
        follow_up_damage_bonus_percent=0):
    final_damage = _landed_damage(
        actor,
        target,
        move,
        combat_state=combat_state,
        critical=critical,
        follow_up_damage_bonus_percent=follow_up_damage_bonus_percent,
    )

    before = target.health.current
    target.health.take_damage(final_damage)
    return before - target.health.current


def _landed_damage(
        actor,
        target,
        move,
        *,
        combat_state=None,
        critical=False,
        follow_up_damage_bonus_percent=0):
    scaled_power = _scaled_damage_power(actor, move)
    if follow_up_damage_bonus_percent:
        scaled_power = (
            scaled_power
            * (100 + follow_up_damage_bonus_percent)
            // 100
        )
    mitigation = _mitigation(target, move.damage_type)
    normal_damage = max(1, scaled_power - mitigation)
    damage_after_strength_negation = _strength_negated_damage(
        target,
        move.damage_type,
        normal_damage,
    )
    damage_after_brace = _brace_reduced_damage(
        target,
        move.damage_type,
        damage_after_strength_negation,
        combat_state,
    )
    final_damage = _defended_damage(
        target,
        move.damage_type,
        damage_after_brace,
        combat_state,
    )
    if critical:
        return max(
            1,
            final_damage * CRITICAL_DAMAGE_MULTIPLIER_PERCENT // 100,
        )

    return final_damage


def _scaled_damage_power(actor, move):
    output_bonus_bps = _damage_output_bonus_bps(actor, move)
    return move.power * (BASIS_POINTS + output_bonus_bps) // BASIS_POINTS


def _damage_output_bonus_bps(actor, move):
    bonuses = []

    for attribute in move.scales_with:
        bonus = _output_bonus_bps_for_attribute(actor, attribute)
        if bonus is not None:
            bonuses.append(bonus)

    if not bonuses:
        return 0

    return sum(bonuses) // len(bonuses)


def _output_bonus_bps_for_attribute(actor, attribute):
    if attribute == ScalingAttribute.STRENGTH:
        return scaling.physical_output_bonus_bps_from_strength(
            actor.effective_stat("strength")
        )
    if attribute == ScalingAttribute.DEXTERITY:
        return scaling.physical_output_bonus_bps_from_dexterity(
            actor.effective_stat("dexterity")
        )
    if attribute == ScalingAttribute.INTELLIGENCE:
        return scaling.magical_output_bonus_bps_from_intelligence(
            actor.effective_stat("intelligence")
        )

    return None


def _apply_healing(actor, target, move):
    calculated_healing = move.power + _scaling_value(actor, move)

    before = target.health.current
    target.health.heal(calculated_healing)
    return target.health.current - before


def _mitigation(target, damage_type):
    if damage_type == DamageType.PHYSICAL:
        defense_value = target.effective_stat("constitution")
    elif damage_type == DamageType.MAGICAL:
        defense_value = target.effective_stat("spirit")
    elif damage_type == DamageType.HYBRID:
        defense_value = (
            target.effective_stat("constitution") + target.effective_stat("spirit")
        ) // 2
    else:
        defense_value = 0

    return defense_value // 4


def _strength_physical_negation_bps(target, damage_type):
    if damage_type != DamageType.PHYSICAL:
        return 0

    return scaling.physical_negation_bps_from_strength(
        target.effective_stat("strength")
    )


def _strength_negated_damage(target, damage_type, normal_damage):
    negation_bps = _strength_physical_negation_bps(target, damage_type)
    reduction_amount = normal_damage * negation_bps // BASIS_POINTS
    return max(1, normal_damage - reduction_amount)


def _brace_reduced_damage(target, damage_type, normal_damage, combat_state):
    if combat_state is None:
        return normal_damage

    reduction_percent = combat_state.brace_incoming_reduction_percent(
        target,
        damage_type,
    )
    reduction_amount = normal_damage * reduction_percent // 100
    return max(1, normal_damage - reduction_amount)


def _defended_damage(target, damage_type, normal_damage, combat_state):
    if combat_state is None or not combat_state.is_defending(target):
        return normal_damage

    reduction_percent = target.defend_reduction_percent(damage_type)
    reduction_amount = normal_damage * reduction_percent // 100
    return max(1, normal_damage - reduction_amount)


def _grant_super_for_landed_non_super_damage(actor):
    if actor.generates_super:
        bonus_bps = scaling.super_gain_bonus_bps_from_intuition(
            actor.effective_stat("intuition")
        )
        gained_super = (
            SUPER_GAIN_PER_LANDED_NON_SUPER_DAMAGE
            * (BASIS_POINTS + bonus_bps)
            // BASIS_POINTS
        )
        actor.super_resource.gain(gained_super)


def _dexterity_accuracy_bonus_percent(actor):
    return scaling.accuracy_bonus_bps_from_dexterity(
        actor.effective_stat("dexterity")
    ) // 100


def _dexterity_dodge_bonus_percent(target):
    return scaling.dodge_bonus_bps_from_dexterity(
        target.effective_stat("dexterity")
    ) // 100


def _final_hit_chance(actor, target, move):
    raw_hit_chance = (
        move.accuracy
        + _dexterity_accuracy_bonus_percent(actor)
        - _dexterity_dodge_bonus_percent(target)
    )
    final_hit_chance = min(MAX_ORDINARY_HIT_CHANCE, raw_hit_chance)
    return max(MIN_ORDINARY_HIT_CHANCE, final_hit_chance)


def _final_crit_chance(actor):
    raw_crit_chance = (
        BASE_ORDINARY_CRIT_CHANCE
        + scaling.crit_bonus_bps_from_intuition(
            actor.effective_stat("intuition")
        ) // 100
    )
    return min(MAX_ORDINARY_CRIT_CHANCE, raw_crit_chance)


def _rolled_critical_hit(actor, rng):
    return rng.randint(1, 100) <= _final_crit_chance(actor)
