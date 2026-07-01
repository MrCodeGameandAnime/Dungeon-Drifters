"""Mechanical structured combat resolver."""

import random

from app.combat.combatant import Combatant
from app.combat.move import DamageType, MoveKind, ResourceType, ScalingAttribute, TargetType
from app.combat.result import MoveResult


SUPPORTED_MECHANICS = (None, "basic_attack", "heavy_attack")
SUPER_GAIN_PER_ACCEPTED_NON_SUPER_ACTION = 10


class CombatResolver:
    def __init__(self, rng=random):
        self.rng = rng

    def resolve_move(self, actor, target, move_name):
        result_move_name = move_name if isinstance(move_name, str) and move_name else "unknown"

        if not _is_valid_combatant(actor):
            return _rejected(result_move_name, "invalid_actor")
        if not actor.is_alive():
            return _rejected(result_move_name, "actor_defeated")

        if not _is_valid_combatant(target):
            return _rejected(result_move_name, "invalid_target")
        if not target.is_alive():
            return _rejected(result_move_name, "target_defeated")

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
                damage = _apply_damage(actor, target, move)
            elif move.kind == MoveKind.HEALING:
                healing = _apply_healing(actor, target, move)

        if move.resource_type != ResourceType.SUPER:
            actor.super_resource.gain(SUPER_GAIN_PER_ACCEPTED_NON_SUPER_ACTION)

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
        value.combat_moves
        value.display_name
    except Exception:
        return False

    return callable(getattr(value, "effective_stat", None)) and callable(
        getattr(value, "is_alive", None)
    )


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


def _apply_damage(actor, target, move):
    raw_damage = move.power + _scaling_value(actor, move)
    mitigation = _mitigation(target, move.damage_type)
    final_damage = max(1, raw_damage - mitigation)

    before = target.health.current
    target.health.take_damage(final_damage)
    return before - target.health.current


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
