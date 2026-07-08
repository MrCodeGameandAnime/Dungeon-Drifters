"""Mechanical structured combat resolver."""

import random

from app.combat.combat_state import CombatState
from app.combat.combatant import Combatant
from app.combat.move import DamageType, MoveKind, ResourceType, ScalingAttribute, TargetType
from app.combat.result import MoveResult
from app.player import scaling


BASIS_POINTS = 10_000
SUPPORTED_MECHANICS = (None, "basic_attack", "heavy_attack")
SUPER_GAIN_PER_LANDED_NON_SUPER_DAMAGE = 10


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

        if not _is_supported_move_kind(move):
            return _rejected(move.name, "unsupported_move_kind")

        if move.mechanic not in SUPPORTED_MECHANICS:
            return _rejected(move.name, "unsupported_mechanic")

        if not _is_valid_target_type(actor, target, move):
            return _rejected(move.name, "invalid_target_type")

        affordable, insufficient_reason = _can_afford(actor, move)
        if not affordable:
            return _rejected(move.name, insufficient_reason)

        resource_spent = _spend_resource(actor, move)
        roll = self.rng.randint(1, 100)
        hit = roll <= move.accuracy

        damage = 0
        healing = 0
        if hit:
            if move.kind == MoveKind.DAMAGE:
                damage = _apply_damage(actor, target, move, combat_state=combat_state)
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


def _apply_damage(actor, target, move, *, combat_state=None):
    scaled_power = _scaled_damage_power(actor, move)
    mitigation = _mitigation(target, move.damage_type)
    normal_damage = max(1, scaled_power - mitigation)
    final_damage = _defended_damage(target, move.damage_type, normal_damage, combat_state)

    before = target.health.current
    target.health.take_damage(final_damage)
    return before - target.health.current


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


def _defended_damage(target, damage_type, normal_damage, combat_state):
    if combat_state is None or not combat_state.is_defending(target):
        return normal_damage

    reduction_percent = target.defend_reduction_percent(damage_type)
    reduction_amount = normal_damage * reduction_percent // 100
    return max(1, normal_damage - reduction_amount)


def _grant_super_for_landed_non_super_damage(actor):
    if actor.generates_super:
        actor.super_resource.gain(SUPER_GAIN_PER_LANDED_NON_SUPER_DAMAGE)
