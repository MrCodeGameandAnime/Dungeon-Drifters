from dataclasses import dataclass

from app.combat.brace import BRACE_RULES
from app.combat.move import DamageType
from app.combat.combat_state import CombatState


@dataclass(eq=True, frozen=False)
class UnhashableCombatant:
    name: str


def test_brace_rules_are_the_approved_shared_values():
    assert BRACE_RULES.incoming_reduction_percent == 40
    assert BRACE_RULES.follow_up_damage_bonus_percent == 30
    assert BRACE_RULES.follow_up_mechanic == "heavy_attack"


def test_combat_state_starts_with_empty_temporary_state():
    combat_state = CombatState()

    assert combat_state.turn_count == 0
    assert not combat_state.is_defending(object())
    assert not hasattr(combat_state, "defending")
    assert not hasattr(combat_state, "set_defending")
    assert not hasattr(combat_state, "clear_turn_flags")
    assert combat_state.statuses == {}
    assert combat_state.buffs == {}
    assert combat_state.debuffs == {}


def test_mutable_containers_are_per_instance():
    first_state = CombatState()
    second_state = CombatState()

    first_state.statuses["burn"] = 2
    first_state.buffs["attack"] = 1
    first_state.debuffs["defense"] = 1
    first_state.activate_defend(object())

    assert second_state.statuses == {}
    assert second_state.buffs == {}
    assert second_state.debuffs == {}
    assert not second_state.is_defending(object())


def test_advance_turn_increments_and_returns_turn_count():
    combat_state = CombatState()

    assert combat_state.advance_turn() == 1
    assert combat_state.turn_count == 1
    assert combat_state.advance_turn() == 2
    assert combat_state.turn_count == 2


def test_defend_tracking_is_per_combatant_identity_based_and_unhashable_safe():
    combat_state = CombatState()
    first = UnhashableCombatant("same")
    second = UnhashableCombatant("same")

    combat_state.activate_defend(first)
    combat_state.activate_defend(first)

    assert combat_state.is_defending(first)
    assert not combat_state.is_defending(second)

    combat_state.clear_defend(second)

    assert combat_state.is_defending(first)

    combat_state.clear_defend(first)

    assert not combat_state.is_defending(first)


def test_clear_defend_missing_entry_is_harmless():
    combat_state = CombatState()
    combatant = object()

    combat_state.clear_defend(combatant)

    assert not combat_state.is_defending(combatant)


def test_complete_accepted_action_clears_opponents_and_preserves_actor():
    combat_state = CombatState()
    actor = object()
    first_opponent = object()
    second_opponent = object()

    combat_state.activate_defend(actor)
    combat_state.activate_defend(first_opponent)
    combat_state.activate_defend(second_opponent)

    result = combat_state.complete_accepted_action(
        actor,
        opposing_combatants=(actor, first_opponent, first_opponent),
    )

    assert result == 1
    assert combat_state.turn_count == 1
    assert combat_state.is_defending(actor)
    assert not combat_state.is_defending(first_opponent)
    assert combat_state.is_defending(second_opponent)


def test_complete_accepted_action_with_empty_opponents_still_advances_once():
    combat_state = CombatState()
    actor = object()

    combat_state.activate_defend(actor)

    result = combat_state.complete_accepted_action(actor, opposing_combatants=())

    assert result == 1
    assert combat_state.turn_count == 1
    assert combat_state.is_defending(actor)


def test_rejected_action_without_completion_does_not_clear_or_advance():
    combat_state = CombatState()
    defender = object()

    combat_state.activate_defend(defender)

    assert combat_state.is_defending(defender)
    assert combat_state.turn_count == 0


def test_defend_completion_does_not_delete_existing_containers():
    combat_state = CombatState()
    actor = object()
    opponent = object()
    combat_state.activate_defend(opponent)
    combat_state.statuses["burn"] = 2
    combat_state.buffs["attack"] = 1
    combat_state.debuffs["defense"] = 1

    combat_state.complete_accepted_action(actor, opposing_combatants=(opponent,))

    assert not combat_state.is_defending(opponent)
    assert combat_state.statuses == {"burn": 2}
    assert combat_state.buffs == {"attack": 1}
    assert combat_state.debuffs == {"defense": 1}


def test_brace_activates_for_owner_and_returns_physical_reduction():
    combat_state = CombatState()
    owner = object()

    combat_state.activate_brace(owner)

    assert combat_state.brace_incoming_reduction_percent(owner, DamageType.PHYSICAL) == 40


def test_brace_query_returns_zero_for_magical_hybrid_or_missing_state():
    combat_state = CombatState()
    owner = object()
    other = object()
    combat_state.activate_brace(owner)

    assert combat_state.brace_incoming_reduction_percent(owner, DamageType.MAGICAL) == 0
    assert combat_state.brace_incoming_reduction_percent(owner, DamageType.HYBRID) == 0
    assert combat_state.brace_incoming_reduction_percent(other, DamageType.PHYSICAL) == 0


def test_brace_incoming_reduction_query_does_not_consume_state():
    combat_state = CombatState()
    owner = object()
    combat_state.activate_brace(owner)

    assert combat_state.brace_incoming_reduction_percent(owner, DamageType.PHYSICAL) == 40
    assert combat_state.brace_incoming_reduction_percent(owner, DamageType.PHYSICAL) == 40


def test_brace_incoming_protection_query_reports_state_without_consuming_it():
    combat_state = CombatState()
    owner = object()
    opponent = object()

    assert not combat_state.brace_incoming_protection_active(owner)

    combat_state.activate_brace(owner)

    assert combat_state.brace_incoming_protection_active(owner)
    assert combat_state.brace_incoming_protection_active(owner)

    combat_state.complete_accepted_action(opponent, opposing_combatants=(owner,))

    assert not combat_state.brace_incoming_protection_active(owner)


def test_brace_activation_does_not_expire_itself_through_complete_accepted_action():
    combat_state = CombatState()
    owner = object()
    opponent = object()

    combat_state.activate_brace(owner)
    result = combat_state.complete_accepted_action(owner, opposing_combatants=(opponent,))

    assert result == 1
    assert combat_state.brace_incoming_reduction_percent(owner, DamageType.PHYSICAL) == 40


def test_brace_incoming_protection_expires_after_next_accepted_opposing_action():
    combat_state = CombatState()
    owner = object()
    opponent = object()

    combat_state.activate_brace(owner)
    combat_state.complete_accepted_action(owner, opposing_combatants=(opponent,))
    combat_state.complete_accepted_action(opponent, opposing_combatants=(owner,))

    assert combat_state.brace_incoming_reduction_percent(owner, DamageType.PHYSICAL) == 0


def test_opposing_action_expiry_clears_only_incoming_protection_and_not_heavy_payoff():
    combat_state = CombatState()
    owner = object()
    opponent = object()

    combat_state.activate_brace(owner)
    combat_state.complete_accepted_action(owner, opposing_combatants=(opponent,))
    combat_state.complete_accepted_action(opponent, opposing_combatants=(owner,))

    assert combat_state.brace_incoming_reduction_percent(owner, DamageType.PHYSICAL) == 0
    assert (
        combat_state.consume_brace_follow_up_damage_bonus_percent(owner, "heavy_attack")
        == 30
    )
    assert (
        combat_state.consume_brace_follow_up_damage_bonus_percent(owner, "heavy_attack")
        == 0
    )


def test_heavy_payoff_does_not_consume_for_nonmatching_mechanics():
    combat_state = CombatState()
    owner = object()
    combat_state.activate_brace(owner)

    assert (
        combat_state.consume_brace_follow_up_damage_bonus_percent(owner, "basic_attack")
        == 0
    )
    assert (
        combat_state.consume_brace_follow_up_damage_bonus_percent(owner, None)
        == 0
    )
    assert (
        combat_state.consume_brace_follow_up_damage_bonus_percent(owner, "heavy_attack")
        == 30
    )


def test_brace_follow_up_query_is_non_consuming_and_mechanic_specific():
    combat_state = CombatState()
    owner = object()
    combat_state.activate_brace(owner)

    assert combat_state.brace_follow_up_damage_bonus_percent(owner, "basic_attack") == 0
    assert combat_state.brace_follow_up_damage_bonus_percent(owner, None) == 0
    assert combat_state.brace_follow_up_damage_bonus_percent(owner, "heavy_attack") == 30
    assert combat_state.brace_follow_up_damage_bonus_percent(owner, "heavy_attack") == 30
    assert (
        combat_state.consume_brace_follow_up_damage_bonus_percent(owner, "heavy_attack")
        == 30
    )
    assert combat_state.brace_follow_up_damage_bonus_percent(owner, "heavy_attack") == 0


def test_heavy_payoff_returns_zero_when_no_active_payoff_exists():
    combat_state = CombatState()
    owner = object()

    assert (
        combat_state.consume_brace_follow_up_damage_bonus_percent(owner, "heavy_attack")
        == 0
    )


def test_repeated_brace_refreshes_without_stacking_bonus_or_reduction():
    combat_state = CombatState()
    owner = object()
    opponent = object()

    combat_state.activate_brace(owner)
    combat_state.consume_brace_follow_up_damage_bonus_percent(owner, "heavy_attack")
    combat_state.complete_accepted_action(opponent, opposing_combatants=(owner,))

    assert combat_state.brace_incoming_reduction_percent(owner, DamageType.PHYSICAL) == 0
    assert (
        combat_state.consume_brace_follow_up_damage_bonus_percent(owner, "heavy_attack")
        == 0
    )

    combat_state.activate_brace(owner)

    assert combat_state.brace_incoming_reduction_percent(owner, DamageType.PHYSICAL) == 40
    assert (
        combat_state.consume_brace_follow_up_damage_bonus_percent(owner, "heavy_attack")
        == 30
    )
    assert (
        combat_state.consume_brace_follow_up_damage_bonus_percent(owner, "heavy_attack")
        == 0
    )


def test_brace_ownership_is_identity_based_and_unhashable_safe():
    combat_state = CombatState()
    first = UnhashableCombatant("same")
    second = UnhashableCombatant("same")

    combat_state.activate_brace(first)

    assert combat_state.brace_incoming_protection_active(first)
    assert not combat_state.brace_incoming_protection_active(second)
    assert combat_state.brace_follow_up_damage_bonus_percent(first, "heavy_attack") == 30
    assert combat_state.brace_follow_up_damage_bonus_percent(second, "heavy_attack") == 0
    assert combat_state.brace_incoming_reduction_percent(first, DamageType.PHYSICAL) == 40
    assert combat_state.brace_incoming_reduction_percent(second, DamageType.PHYSICAL) == 0
    assert (
        combat_state.consume_brace_follow_up_damage_bonus_percent(second, "heavy_attack")
        == 0
    )
    assert (
        combat_state.consume_brace_follow_up_damage_bonus_percent(first, "heavy_attack")
        == 30
    )
