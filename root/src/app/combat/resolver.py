"""Mechanical structured combat resolver."""

import app.randomness as random

from app.combat.arcane import GRAVEMANTLE_RULES
from app.combat.infused_barb import INFUSED_BARB_MECHANIC
from app.combat.frost import FROST_ATTACK_MECHANIC, FROST_RULES
from app.combat.combat_state import CombatState, HEAL_COOLDOWN_ACTIONS
from app.combat.combatant import is_combatant
from app.combat.move import (
    DamageComponentIdentity,
    DamageDefenseClass,
    DamageType,
    MoveKind,
    ResourceType,
    ScalingAttribute,
    TargetType,
)
from app.combat.passive_effect import PassiveEffectCondition, PassiveEffectKind
from app.combat.result import (
    CombatOutcome,
    CombatOutcomeTarget,
    CombatOutcomeType,
    MoveResult,
)
from app.combat.storm import (
    HYDRO_WHIP_MECHANIC,
    LIGHTNING_PALM_MECHANIC,
    STORM_RULES,
    TEMPEST_SURGE_MECHANIC,
)
from app.player import scaling
from app.player.character_run_state import CharacterRunState, InfusionKind, PreparedPayloadId


BASIS_POINTS = 10_000
MAX_ORDINARY_HIT_CHANCE = 95
MIN_ORDINARY_HIT_CHANCE = 5
BASE_ORDINARY_CRIT_CHANCE = 0
MAX_ORDINARY_CRIT_CHANCE = 35
CRITICAL_DAMAGE_MULTIPLIER_PERCENT = 150
SUPPORTED_MECHANICS = (
    None,
    "basic_attack",
    "heavy_attack",
    "gravemantle_rupture",
    INFUSED_BARB_MECHANIC,
    HYDRO_WHIP_MECHANIC,
    LIGHTNING_PALM_MECHANIC,
    TEMPEST_SURGE_MECHANIC,
    FROST_ATTACK_MECHANIC,
)
SUPER_GAIN_PER_LANDED_NON_SUPER_DAMAGE = 10
HEALING_ROLL_MIN = 10
HEALING_ROLL_MAX = 16
_OWN_STATUS_KINDS = "target_has_own_status_kinds"


def authored_move_rejection_reason(move):
    """Return the resolver rejection for an authored move shape, if any."""
    if move.kind == MoveKind.UTILITY:
        if move.mechanic != "brace":
            return (
                "unsupported_move_kind"
                if move.mechanic is None
                else "unsupported_mechanic"
            )
    elif not _is_supported_move_kind(move):
        return "unsupported_move_kind"

    if move.kind != MoveKind.UTILITY and move.mechanic not in SUPPORTED_MECHANICS:
        return "unsupported_mechanic"
    if move.mechanic == "gravemantle_rupture" and not move.is_spell:
        return "unsupported_mechanic"
    if move.mechanic == INFUSED_BARB_MECHANIC and move.kind != MoveKind.DAMAGE:
        return "unsupported_mechanic"
    if (
        move.mechanic
        in (HYDRO_WHIP_MECHANIC, LIGHTNING_PALM_MECHANIC, TEMPEST_SURGE_MECHANIC)
        and move.kind != MoveKind.DAMAGE
    ):
        return "unsupported_mechanic"
    return None


class CombatResolver:
    def __init__(self, rng=random):
        self.rng = rng

    def resolve_move(
        self,
        actor,
        target,
        move_name,
        *,
        combat_state=None,
        character_run_state=None,
    ):
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

        authored_rejection = authored_move_rejection_reason(move)
        if authored_rejection is not None:
            return _rejected(move.name, authored_rejection)

        if move.is_spell and not isinstance(combat_state, CombatState):
            return _rejected(move.name, "invalid_combat_state")

        if not _is_valid_target_type(actor, target, move):
            return _rejected(move.name, "invalid_target_type")

        if move.kind == MoveKind.UTILITY and not isinstance(combat_state, CombatState):
            return _rejected(move.name, "invalid_combat_state")

        if (
            move.mechanic == INFUSED_BARB_MECHANIC
            and not isinstance(combat_state, CombatState)
        ):
            return _rejected(move.name, "invalid_combat_state")

        actor_effect_context = _capture_passive_context(
            actor,
            target,
            move,
            combat_state,
        )
        target_effect_context = _capture_passive_context(
            target,
            actor,
            move,
            combat_state,
        )
        resource_cost = _effective_resource_cost(
            actor,
            target,
            move,
            combat_state,
            actor_effect_context,
        )
        affordable, insufficient_reason = _can_afford(actor, move, resource_cost)
        if not affordable:
            return _rejected(move.name, insufficient_reason)

        if move.mechanic == INFUSED_BARB_MECHANIC:
            if not isinstance(character_run_state, CharacterRunState):
                return _rejected(move.name, "invalid_character_run_state")
            if (
                not character_run_state.supports_payload(PreparedPayloadId.INFUSED_BARB)
                or character_run_state.prepared_infusion() is None
            ):
                return _rejected(move.name, "infused_barb_unprepared")

        resource_spent = _spend_resource(actor, move, resource_cost)

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

        outcomes = []
        infusion_kind = None
        if move.mechanic == INFUSED_BARB_MECHANIC:
            infusion_kind = character_run_state.consume_infusion()
            outcomes.append(
                CombatOutcome(
                    CombatOutcomeType.INFUSED_BARB_CONSUMED,
                    target=CombatOutcomeTarget.ACTOR,
                )
            )

        arcane_discharge = None
        if move.kind == MoveKind.DAMAGE and move.is_spell:
            arcane_discharge = combat_state.consume_arcane_discharge(actor)
            outcomes.extend(_outcomes_for_discharge(arcane_discharge))

        conductive_lightning = False
        turbulent_lightning = False
        lightning_storm = False
        if move.mechanic == LIGHTNING_PALM_MECHANIC:
            conductive = combat_state.conductive_active(actor, target)
            turbulence = combat_state.turbulence_active(actor, target)
            lightning_storm = conductive and turbulence
            conductive_lightning = conductive and not turbulence
            turbulent_lightning = turbulence and not conductive
            if lightning_storm:
                outcomes.append(
                    CombatOutcome(CombatOutcomeType.LIGHTNING_STORM_TRIGGERED)
                )
                outcomes.append(combat_state.consume_conductive(actor, target))
                outcomes.append(combat_state.consume_turbulence(actor, target))
            elif conductive_lightning:
                outcomes.append(combat_state.consume_conductive(actor, target))
            elif turbulent_lightning:
                outcomes.append(combat_state.consume_turbulence(actor, target))

        follow_up_damage_bonus_percent = 0
        if move.mechanic == "heavy_attack" and combat_state is not None:
            follow_up_damage_bonus_percent = (
                combat_state.consume_brace_follow_up_damage_bonus_percent(
                    actor,
                    move.mechanic,
                )
            )
            if follow_up_damage_bonus_percent:
                follow_up_damage_bonus_percent += _passive_effect_total(
                    actor,
                    target,
                    move,
                    combat_state,
                    actor_effect_context,
                    PassiveEffectKind.BRACE_FOLLOW_UP,
                )

        roll = self.rng.randint(1, 100)
        hit = roll <= _final_hit_chance(
            actor,
            target,
            move,
            actor_effect_context=actor_effect_context,
            target_effect_context=target_effect_context,
            combat_state=combat_state,
        )

        damage = 0
        healing = 0
        critical = False
        if hit:
            if move.kind == MoveKind.DAMAGE:
                critical = _rolled_critical_hit(
                    actor,
                    move,
                    self.rng,
                    condition_context=actor_effect_context,
                    target=target,
                    combat_state=combat_state,
                )
                damage = _apply_damage(
                    actor,
                    target,
                    move,
                    combat_state=combat_state,
                    critical=critical,
                    follow_up_damage_bonus_percent=follow_up_damage_bonus_percent,
                    arcane_discharge=arcane_discharge,
                    storm_damage_bonus_percent=(
                        STORM_RULES.lightning_storm_damage_bonus_percent
                        if lightning_storm
                        else (
                            STORM_RULES.conductive_damage_bonus_percent
                            if conductive_lightning
                            else (
                                STORM_RULES.turbulence_damage_bonus_percent
                                if turbulent_lightning
                                else 0
                            )
                        )
                    ),
                    actor_effect_context=actor_effect_context,
                    target_effect_context=target_effect_context,
                )

                if (
                    combat_state is not None
                    and arcane_discharge is None
                    and not target.is_alive()
                    and combat_state.clear_arcane_break_for_target(target)
                ):
                    outcomes.append(
                        CombatOutcome(
                            CombatOutcomeType.BREAK_CLEARED,
                            target=CombatOutcomeTarget.TARGET,
                        )
                    )
                if move.mechanic == INFUSED_BARB_MECHANIC and target.is_alive():
                    if infusion_kind == InfusionKind.FIRE:
                        outcomes.append(
                            combat_state.apply_burn(
                                actor,
                                target,
                                potency_bonus_bps=_status_potency_bonus_bps(
                                    actor,
                                    target,
                                    move,
                                    combat_state,
                                    actor_effect_context,
                                ),
                            )
                        )
                    elif infusion_kind == InfusionKind.POISON:
                        outcomes.append(
                            combat_state.apply_poison(
                                actor,
                                target,
                                potency_bonus_bps=_status_potency_bonus_bps(
                                    actor,
                                    target,
                                    move,
                                    combat_state,
                                    actor_effect_context,
                                ),
                            )
                        )
                if move.mechanic == HYDRO_WHIP_MECHANIC and target.is_alive():
                    outcomes.append(combat_state.apply_conductive(actor, target))
                if move.mechanic == TEMPEST_SURGE_MECHANIC and target.is_alive():
                    outcomes.append(combat_state.apply_turbulence(actor, target))
                if move.mechanic == FROST_ATTACK_MECHANIC and target.is_alive():
                    frost_outcomes = combat_state.apply_frost_charge(actor, target)
                    outcomes.extend(frost_outcomes)
                    if move.frost_backlash and any(
                        outcome.outcome_type == CombatOutcomeType.FROST_TRIGGERED
                        for outcome in frost_outcomes
                    ):
                        backlash_roll = self.rng.randint(1, 100)
                        if backlash_roll <= FROST_RULES.mournglass_backlash_chance_percent:
                            combat_state.apply_frozen(actor, actor)
                            outcomes.append(
                                CombatOutcome(
                                    CombatOutcomeType.FROST_BACKLASH_TRIGGERED,
                                    target=CombatOutcomeTarget.ACTOR,
                                )
                            )
                if conductive_lightning and target.is_alive():
                    stun_roll = self.rng.randint(1, 100)
                    if stun_roll <= STORM_RULES.stun_chance_percent:
                        outcomes.append(combat_state.apply_stun(actor, target))
            elif move.kind == MoveKind.HEALING:
                healing = _apply_healing(actor, target, move)

        if hit and move.kind == MoveKind.DAMAGE and move.resource_type != ResourceType.SUPER:
            _grant_super_for_landed_non_super_damage(
                actor,
                target,
                move,
                combat_state,
                actor_effect_context,
            )

        if move.mechanic == "gravemantle_rupture":
            linked_target = target if hit and target.is_alive() else None
            combat_state.activate_arcane_overcharge(
                actor,
                broken_target=linked_target,
            )
            if linked_target is not None:
                outcomes.append(
                    CombatOutcome(
                        CombatOutcomeType.BREAK_APPLIED,
                        target=CombatOutcomeTarget.TARGET,
                    )
                )
            outcomes.append(
                CombatOutcome(CombatOutcomeType.OVERCHARGE_GAINED)
            )

            backlash_roll = self.rng.randint(1, 100)
            if backlash_roll <= GRAVEMANTLE_RULES.backlash_chance_percent:
                rolled_backlash = self.rng.randint(
                    GRAVEMANTLE_RULES.backlash_damage_min,
                    GRAVEMANTLE_RULES.backlash_damage_max,
                )
                before_backlash = actor.health.current
                actor.health.take_damage(rolled_backlash)
                actual_backlash = before_backlash - actor.health.current
                outcomes.append(
                    CombatOutcome(
                        CombatOutcomeType.BACKLASH_DAMAGE,
                        amount=actual_backlash,
                        target=CombatOutcomeTarget.ACTOR,
                    )
                )
                if actor.is_alive():
                    combat_state.activate_arcane_instability(actor)
                    outcomes.append(
                        CombatOutcome(
                            CombatOutcomeType.INSTABILITY_APPLIED,
                            target=CombatOutcomeTarget.ACTOR,
                        )
                    )

        return MoveResult(
            accepted=True,
            hit=hit,
            move_name="Lightning Storm" if lightning_storm else move.name,
            resource_spent=resource_spent,
            damage=damage,
            healing=healing,
            statuses_applied=(),
            reason=None,
            critical=critical,
            outcomes=tuple(outcomes),
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

    def resolve_environmental_physical_damage(
        self,
        target,
        power,
        *,
        combat_state=None,
    ):
        if not _is_valid_combatant(target):
            return _rejected("Cave-in", "invalid_target")
        if not target.is_alive():
            return _rejected("Cave-in", "target_defeated")
        if isinstance(power, bool) or not isinstance(power, int) or power < 1:
            return _rejected("Cave-in", "invalid_power")
        if not _is_valid_optional_combat_state(combat_state):
            return _rejected("Cave-in", "invalid_combat_state")

        condition_context = _capture_passive_context(
            target,
            None,
            None,
            combat_state,
        )
        mitigation = _mitigation(target, DamageType.PHYSICAL)
        mitigation += _passive_mitigation_bonus(
            target,
            None,
            None,
            combat_state,
            condition_context,
            DamageType.PHYSICAL,
        )
        damage = max(1, power - mitigation)
        damage = _strength_negated_damage(
            target,
            DamageType.PHYSICAL,
            damage,
        )
        damage = _arcane_instability_damage(
            target,
            DamageType.PHYSICAL,
            damage,
            combat_state,
        )
        damage = _brace_reduced_damage(
            target,
            DamageType.PHYSICAL,
            damage,
            combat_state,
            additional_reduction_percent=_brace_incoming_bonus(
                target,
                None,
                None,
                combat_state,
                condition_context,
                DamageType.PHYSICAL,
            ),
        )
        damage = _defended_damage(
            target,
            DamageType.PHYSICAL,
            damage,
            combat_state,
        )
        before = target.health.current
        target.health.take_damage(damage)
        return MoveResult(
            accepted=True,
            hit=True,
            move_name="Cave-in",
            resource_spent=0,
            damage=before - target.health.current,
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
        outcomes=(),
    )


def _outcomes_for_discharge(discharge):
    if discharge is None:
        return ()

    outcomes = [CombatOutcome(CombatOutcomeType.OVERCHARGE_CONSUMED)]
    if discharge.broken_target is not None:
        outcomes.append(
            CombatOutcome(
                CombatOutcomeType.BREAK_CLEARED,
                target=CombatOutcomeTarget.TARGET,
            )
        )
    if discharge.instability_was_active:
        outcomes.append(
            CombatOutcome(
                CombatOutcomeType.INSTABILITY_CLEARED,
                target=CombatOutcomeTarget.ACTOR,
            )
        )
    return tuple(outcomes)


def _is_valid_combatant(value):
    if not is_combatant(value):
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
        if move.damage_components:
            return move.damage_type == DamageType.NONE
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


def _capture_passive_context(owner, opponent, move, combat_state):
    health = owner.health
    mana = owner.mana_resource
    context = {
        PassiveEffectCondition.ALWAYS: True,
        PassiveEffectCondition.LOW_HEALTH: health.current * 2 <= health.maximum,
        PassiveEffectCondition.HIGH_HEALTH: health.current * 4 >= health.maximum * 3,
        PassiveEffectCondition.LOW_MANA: mana.current * 4 <= mana.maximum,
        PassiveEffectCondition.HIGH_MANA: mana.current * 4 >= mana.maximum * 3,
    }
    if not isinstance(combat_state, CombatState):
        return context

    mechanic = move.mechanic if move is not None else None
    context[PassiveEffectCondition.BRACE_READY] = bool(
        mechanic == "heavy_attack"
        and combat_state.brace_follow_up_damage_bonus_percent(owner, mechanic)
    )
    context[PassiveEffectCondition.ARCANE_OVERCHARGE] = (
        combat_state.arcane_overcharge_active(owner)
    )
    has_target = opponent is not None
    context[PassiveEffectCondition.OWN_FROST] = bool(
        has_target and combat_state.frost_active(owner, opponent)
    )
    conductive = bool(
        has_target and combat_state.conductive_active(owner, opponent)
    )
    turbulence = bool(
        has_target and combat_state.turbulence_active(owner, opponent)
    )
    context[PassiveEffectCondition.OWN_CONDUCTIVE_OR_TURBULENCE] = (
        conductive or turbulence
    )
    context[PassiveEffectCondition.LIGHTNING_STORM] = conductive and turbulence
    owned_statuses = []
    if has_target:
        for status_name, status in (
            ("burn", combat_state.burn_status(opponent)),
            ("poison", combat_state.poison_status(opponent)),
        ):
            if status is not None and status.source is owner:
                owned_statuses.append(status_name)
    context[_OWN_STATUS_KINDS] = tuple(owned_statuses)
    context[PassiveEffectCondition.TARGET_HAS_OWN_STATUS] = bool(owned_statuses)
    return context


def _passive_effects(combatant):
    return getattr(combatant, "combat_passive_effects", ())


def _passive_effect_total(
    owner,
    opponent,
    move,
    combat_state,
    condition_context,
    kind,
    *,
    damage_class=None,
):
    total = 0
    for effect in _passive_effects(owner):
        if effect.kind is not kind:
            continue
        if effect.mechanic is not None and (
            move is None or effect.mechanic != move.mechanic
        ):
            continue
        if effect.damage_class is not None and effect.damage_class is not damage_class:
            continue
        if not _passive_condition_matches(effect, condition_context):
            continue
        total += effect.value
    return total


def _passive_condition_matches(effect, condition_context):
    if effect.condition is PassiveEffectCondition.TARGET_HAS_OWN_STATUS:
        return bool(
            set(effect.target_statuses)
            & set(condition_context.get(_OWN_STATUS_KINDS, ()))
        )
    return condition_context.get(effect.condition, False)


def _effective_resource_cost(
    actor,
    target,
    move,
    combat_state,
    condition_context,
):
    if move.resource_type is not ResourceType.MANA:
        return move.resource_cost
    discount = _passive_effect_total(
        actor,
        target,
        move,
        combat_state,
        condition_context,
        PassiveEffectKind.MANA_COST,
    )
    if not discount:
        return move.resource_cost
    return max(1, move.resource_cost - discount)


def _status_potency_bonus_bps(
    actor,
    target,
    move,
    combat_state,
    condition_context,
):
    effects = tuple(
        effect
        for effect in _passive_effects(actor)
        if effect.kind is PassiveEffectKind.STATUS_POTENCY
        and (effect.mechanic is None or effect.mechanic == move.mechanic)
        and _passive_condition_matches(effect, condition_context)
    )
    bonus_bps = sum(effect.value for effect in effects) * 100
    if any(effect.uses_intuition for effect in effects):
        bonus_bps += scaling.special_potency_bps_from_intuition(
            actor.effective_stat("intuition")
        )
    return bonus_bps


def _can_afford(actor, move, resource_cost=None):
    resource_cost = move.resource_cost if resource_cost is None else resource_cost
    if move.resource_type == ResourceType.NONE:
        return True, None
    if move.resource_type == ResourceType.MANA:
        if actor.mana_resource.can_afford(resource_cost):
            return True, None
        return False, "insufficient_mana"
    if move.resource_type == ResourceType.SUPER:
        if actor.super_resource.can_afford(resource_cost):
            return True, None
        return False, "insufficient_super"

    return False, "unsupported_move_kind"


def _spend_resource(actor, move, resource_cost=None):
    resource_cost = move.resource_cost if resource_cost is None else resource_cost
    if move.resource_type == ResourceType.NONE:
        return 0
    if move.resource_type == ResourceType.MANA:
        actor.mana_resource.spend(resource_cost)
        return resource_cost
    if move.resource_type == ResourceType.SUPER:
        actor.super_resource.spend(resource_cost)
        return resource_cost

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
        follow_up_damage_bonus_percent=0,
        arcane_discharge=None,
        storm_damage_bonus_percent=0,
        actor_effect_context=None,
        target_effect_context=None):
    final_damage = _landed_damage(
        actor,
        target,
        move,
        combat_state=combat_state,
        critical=critical,
        follow_up_damage_bonus_percent=follow_up_damage_bonus_percent,
        arcane_discharge=arcane_discharge,
        storm_damage_bonus_percent=storm_damage_bonus_percent,
        actor_effect_context=actor_effect_context,
        target_effect_context=target_effect_context,
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
        follow_up_damage_bonus_percent=0,
    arcane_discharge=None,
    storm_damage_bonus_percent=0,
    actor_effect_context=None,
    target_effect_context=None):
    if actor_effect_context is None:
        actor_effect_context = _capture_passive_context(
            actor, target, move, combat_state
        )
    if target_effect_context is None:
        target_effect_context = _capture_passive_context(
            target, actor, move, combat_state
        )
    if move.damage_components:
        total_authored_power = sum(
            component.power for component in move.damage_components
        )
        total_damage = sum(
            _landed_component_damage(
                actor,
                target,
                move,
                component,
                total_authored_power,
                combat_state=combat_state,
                follow_up_damage_bonus_percent=follow_up_damage_bonus_percent,
                arcane_discharge=arcane_discharge,
                storm_damage_bonus_percent=storm_damage_bonus_percent,
                actor_effect_context=actor_effect_context,
                target_effect_context=target_effect_context,
            )
            for component in move.damage_components
        )
        final_damage = max(1, total_damage)
        if critical:
            return max(
                1,
                final_damage * CRITICAL_DAMAGE_MULTIPLIER_PERCENT // 100,
            )
        return final_damage

    defense_class = _damage_defense_class(move.damage_type)
    output_bonus_bps = _passive_effect_total(
        actor,
        target,
        move,
        combat_state,
        actor_effect_context,
        PassiveEffectKind.DAMAGE_OUTPUT,
        damage_class=defense_class,
    ) * 100
    if move.damage_type is DamageType.HYBRID:
        output_bonus_bps = sum(
            _passive_effect_total(
                actor,
                target,
                move,
                combat_state,
                actor_effect_context,
                PassiveEffectKind.DAMAGE_OUTPUT,
                damage_class=damage_class,
            )
            for damage_class in (
                DamageDefenseClass.PHYSICAL,
                DamageDefenseClass.MAGICAL,
            )
        ) * 50
    scaled_power = _scaled_damage_power(actor, move, output_bonus_bps)
    if arcane_discharge is not None and move.is_spell:
        scaled_power = (
            scaled_power
            * (100 + arcane_discharge.spell_bonus_percent)
            // 100
        )
    if follow_up_damage_bonus_percent:
        scaled_power = (
            scaled_power
            * (100 + follow_up_damage_bonus_percent)
            // 100
        )
    if storm_damage_bonus_percent:
        scaled_power = (
            scaled_power
            * (100 + storm_damage_bonus_percent)
            // 100
        )
    mitigation = _mitigation(target, move.damage_type)
    mitigation += _passive_mitigation_bonus(
        target,
        actor,
        move,
        combat_state,
        target_effect_context,
        move.damage_type,
    )
    break_reduction_percent = 0
    if arcane_discharge is not None:
        if target is arcane_discharge.broken_target:
            break_reduction_percent = arcane_discharge.break_reduction_percent
    elif combat_state is not None:
        break_reduction_percent = combat_state.gravemantle_break_reduction_percent(target)
    mitigation = mitigation * (100 - break_reduction_percent) // 100
    normal_damage = max(1, scaled_power - mitigation)
    damage_after_strength_negation = _strength_negated_damage(
        target,
        move.damage_type,
        normal_damage,
    )
    damage_after_instability = _arcane_instability_damage(
        target,
        move.damage_type,
        damage_after_strength_negation,
        combat_state,
    )
    damage_after_brace = _brace_reduced_damage(
        target,
        move.damage_type,
        damage_after_instability,
        combat_state,
        additional_reduction_percent=_brace_incoming_bonus(
            target,
            actor,
            move,
            combat_state,
            target_effect_context,
            move.damage_type,
        ),
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


def _landed_component_damage(
    actor,
    target,
    move,
    component,
    total_authored_power,
    *,
    combat_state=None,
    follow_up_damage_bonus_percent=0,
    arcane_discharge=None,
    storm_damage_bonus_percent=0,
    actor_effect_context=None,
    target_effect_context=None,
):
    defense_type = (
        DamageType.PHYSICAL
        if component.defense_class is DamageDefenseClass.PHYSICAL
        else DamageType.MAGICAL
    )
    output_bonus_bps = _damage_output_bonus_bps(actor, component.scales_with)
    output_bonus_bps += _passive_effect_total(
        actor,
        target,
        move,
        combat_state,
        actor_effect_context,
        PassiveEffectKind.DAMAGE_OUTPUT,
        damage_class=component.defense_class,
    ) * 100
    scaled_power = component.power * (
        BASIS_POINTS + output_bonus_bps
    ) // BASIS_POINTS
    for bonus_percent in (
        arcane_discharge.spell_bonus_percent
        if arcane_discharge is not None and move.is_spell
        else 0,
        follow_up_damage_bonus_percent,
        storm_damage_bonus_percent,
    ):
        if bonus_percent:
            scaled_power = scaled_power * (100 + bonus_percent) // 100

    mitigation = _mitigation(target, defense_type)
    mitigation += _passive_mitigation_bonus(
        target,
        actor,
        move,
        combat_state,
        target_effect_context,
        defense_type,
    )
    break_reduction_percent = 0
    if arcane_discharge is not None:
        if target is arcane_discharge.broken_target:
            break_reduction_percent = arcane_discharge.break_reduction_percent
    elif combat_state is not None:
        break_reduction_percent = combat_state.gravemantle_break_reduction_percent(target)
    mitigation = mitigation * (100 - break_reduction_percent) // 100
    mitigation = mitigation * component.power // total_authored_power

    damage = max(0, scaled_power - mitigation)
    damage = _strength_negated_damage(
        target,
        defense_type,
        damage,
        minimum_damage=0,
    )
    damage = _damage_identity_modified_damage(target, component, damage)
    damage = _arcane_instability_damage(
        target,
        defense_type,
        damage,
        combat_state,
    )
    damage = _brace_reduced_damage(
        target,
        defense_type,
        damage,
        combat_state,
        minimum_damage=0,
        additional_reduction_percent=_brace_incoming_bonus(
            target,
            actor,
            move,
            combat_state,
            target_effect_context,
            defense_type,
        ),
    )
    return _defended_damage(
        target,
        defense_type,
        damage,
        combat_state,
        minimum_damage=0,
    )


def _arcane_instability_damage(target, damage_type, damage, combat_state):
    if combat_state is None or damage_type != DamageType.PHYSICAL:
        return damage

    vulnerability_percent = (
        combat_state.arcane_instability_physical_vulnerability_percent(target)
    )
    return damage * (100 + vulnerability_percent) // 100


def _damage_identity_modified_damage(target, component, damage):
    if component.identity not in {
        DamageComponentIdentity.ELEMENTAL,
        DamageComponentIdentity.ALCHEMICAL,
    }:
        return damage

    identity_key = (component.identity, component.subtype)
    if identity_key in getattr(target, "damage_resistances", ()):
        return damage * 75 // 100
    if identity_key in getattr(target, "damage_weaknesses", ()):
        return damage * 125 // 100
    return damage


def _scaled_damage_power(actor, move, passive_output_bonus_bps=0):
    output_bonus_bps = (
        _damage_output_bonus_bps(actor, move.scales_with)
        + passive_output_bonus_bps
    )
    return move.power * (BASIS_POINTS + output_bonus_bps) // BASIS_POINTS


def _damage_output_bonus_bps(actor, scales_with):
    bonuses = []

    for attribute in scales_with:
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


def _damage_defense_class(damage_type):
    if damage_type == DamageType.PHYSICAL:
        return DamageDefenseClass.PHYSICAL
    if damage_type == DamageType.MAGICAL:
        return DamageDefenseClass.MAGICAL
    return None


def _passive_mitigation_bonus(
    owner,
    opponent,
    move,
    combat_state,
    condition_context,
    damage_type,
):
    damage_class = _damage_defense_class(damage_type)
    if damage_class is not None:
        return _passive_effect_total(
            owner,
            opponent,
            move,
            combat_state,
            condition_context,
            PassiveEffectKind.MITIGATION,
            damage_class=damage_class,
        )
    if damage_type == DamageType.HYBRID:
        class_bonuses = tuple(
            _passive_effect_total(
                owner,
                opponent,
                move,
                combat_state,
                condition_context,
                PassiveEffectKind.MITIGATION,
                damage_class=defense_class,
            )
            for defense_class in (
                DamageDefenseClass.PHYSICAL,
                DamageDefenseClass.MAGICAL,
            )
        )
        return sum(class_bonuses) // 2
    return 0


def _brace_incoming_bonus(
    owner,
    opponent,
    move,
    combat_state,
    condition_context,
    damage_type,
):
    if damage_type != DamageType.PHYSICAL or combat_state is None:
        return 0
    if not combat_state.brace_incoming_protection_active(owner):
        return 0
    return _passive_effect_total(
        owner,
        opponent,
        move,
        combat_state,
        condition_context,
        PassiveEffectKind.BRACE_INCOMING,
    )


def _strength_physical_negation_bps(target, damage_type):
    if damage_type != DamageType.PHYSICAL:
        return 0

    return scaling.physical_negation_bps_from_strength(
        target.effective_stat("strength")
    )


def _strength_negated_damage(
    target,
    damage_type,
    normal_damage,
    *,
    minimum_damage=1,
):
    negation_bps = _strength_physical_negation_bps(target, damage_type)
    reduction_amount = normal_damage * negation_bps // BASIS_POINTS
    return max(minimum_damage, normal_damage - reduction_amount)


def _brace_reduced_damage(
    target,
    damage_type,
    normal_damage,
    combat_state,
    *,
    minimum_damage=1,
    additional_reduction_percent=0,
):
    if combat_state is None:
        return normal_damage

    reduction_percent = combat_state.brace_incoming_reduction_percent(
        target,
        damage_type,
    )
    reduction_percent = min(100, reduction_percent + additional_reduction_percent)
    reduction_amount = normal_damage * reduction_percent // 100
    return max(minimum_damage, normal_damage - reduction_amount)


def _defended_damage(
    target,
    damage_type,
    normal_damage,
    combat_state,
    *,
    minimum_damage=1,
):
    if combat_state is None or not combat_state.is_defending(target):
        return normal_damage

    reduction_percent = target.defend_reduction_percent(damage_type)
    reduction_amount = normal_damage * reduction_percent // 100
    return max(minimum_damage, normal_damage - reduction_amount)


def _grant_super_for_landed_non_super_damage(
    actor,
    target=None,
    move=None,
    combat_state=None,
    condition_context=None,
):
    if actor.generates_super:
        bonus_bps = scaling.super_gain_bonus_bps_from_intuition(
            actor.effective_stat("intuition")
        )
        if condition_context is None:
            condition_context = _capture_passive_context(
                actor, target, move, combat_state
            )
        bonus_bps += _passive_effect_total(
            actor,
            target,
            move,
            combat_state,
            condition_context,
            PassiveEffectKind.SUPER_GAIN,
        ) * 100
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


def _final_hit_chance(
    actor,
    target,
    move,
    *,
    actor_effect_context=None,
    target_effect_context=None,
    combat_state=None,
):
    if actor_effect_context is None:
        actor_effect_context = _capture_passive_context(
            actor, target, move, combat_state
        )
    if target_effect_context is None:
        target_effect_context = _capture_passive_context(
            target, actor, move, combat_state
        )
    accuracy_bonus = _passive_effect_total(
        actor,
        target,
        move,
        combat_state,
        actor_effect_context,
        PassiveEffectKind.ACCURACY,
    )
    dodge_bonus = _passive_effect_total(
        target,
        actor,
        move,
        combat_state,
        target_effect_context,
        PassiveEffectKind.DODGE,
    )
    raw_hit_chance = (
        move.accuracy
        + _dexterity_accuracy_bonus_percent(actor)
        - _dexterity_dodge_bonus_percent(target)
        + accuracy_bonus
        - dodge_bonus
    )
    final_hit_chance = min(MAX_ORDINARY_HIT_CHANCE, raw_hit_chance)
    return max(MIN_ORDINARY_HIT_CHANCE, final_hit_chance)


def _final_crit_chance(
    actor,
    move=None,
    target=None,
    combat_state=None,
    condition_context=None,
):
    raw_crit_chance = (
        BASE_ORDINARY_CRIT_CHANCE
        + scaling.crit_bonus_bps_from_intuition(
            actor.effective_stat("intuition")
        ) // 100
    )
    if move is not None:
        if condition_context is None:
            condition_context = _capture_passive_context(
                actor, target, move, combat_state
            )
        raw_crit_chance += _passive_effect_total(
            actor,
            target,
            move,
            combat_state,
            condition_context,
            PassiveEffectKind.CRITICAL,
        )
    return min(MAX_ORDINARY_CRIT_CHANCE, raw_crit_chance)


def _rolled_critical_hit(
    actor,
    move,
    rng,
    *,
    target=None,
    combat_state=None,
    condition_context=None,
):
    return rng.randint(1, 100) <= _final_crit_chance(
        actor,
        move,
        target,
        combat_state,
        condition_context,
    )
