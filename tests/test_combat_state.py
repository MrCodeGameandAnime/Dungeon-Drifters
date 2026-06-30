from app.combat.combat_state import CombatState


def test_combat_state_starts_with_empty_temporary_state():
    combat_state = CombatState()

    assert combat_state.turn_count == 0
    assert combat_state.defending is False
    assert combat_state.statuses == {}
    assert combat_state.buffs == {}
    assert combat_state.debuffs == {}


def test_mutable_containers_are_per_instance():
    first_state = CombatState()
    second_state = CombatState()

    first_state.statuses["burn"] = 2
    first_state.buffs["attack"] = 1
    first_state.debuffs["defense"] = 1

    assert second_state.statuses == {}
    assert second_state.buffs == {}
    assert second_state.debuffs == {}


def test_advance_turn_increments_and_returns_turn_count():
    combat_state = CombatState()

    assert combat_state.advance_turn() == 1
    assert combat_state.turn_count == 1
    assert combat_state.advance_turn() == 2
    assert combat_state.turn_count == 2


def test_set_defending_toggles_defending():
    combat_state = CombatState()

    combat_state.set_defending()
    assert combat_state.defending is True

    combat_state.set_defending(False)
    assert combat_state.defending is False


def test_clear_turn_flags_clears_defending_without_deleting_containers():
    combat_state = CombatState()
    combat_state.set_defending()
    combat_state.statuses["burn"] = 2
    combat_state.buffs["attack"] = 1
    combat_state.debuffs["defense"] = 1

    combat_state.clear_turn_flags()

    assert combat_state.defending is False
    assert combat_state.statuses == {"burn": 2}
    assert combat_state.buffs == {"attack": 1}
    assert combat_state.debuffs == {"defense": 1}
