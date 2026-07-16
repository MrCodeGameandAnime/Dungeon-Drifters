from dataclasses import FrozenInstanceError

import pytest

from app.presentation.battle_models import (
    ActionAvailabilityReason,
    ActionIntent,
    ActionOptionView,
    BattleEventType,
    BattleLogEntry,
    BattleView,
    BattleVisualView,
    CombatantView,
    InputRejectionReason,
    InteractionPhase,
    InventoryCommandOptionView,
    InventoryConfirmationView,
    InventoryAvailabilityReason,
    InventoryInspectionView,
    InventoryItemOptionView,
    MoveAvailabilityReason,
    MoveOptionView,
    SuperMeterView,
)
from app.player.run_items import InventoryCommand


def _combatant(**overrides):
    values = {
        "display_name": "Ser Branoc",
        "hp_current": 116,
        "hp_maximum": 116,
        "mana_current": 46,
        "mana_maximum": 46,
        "super_current": 10,
        "super_maximum": 100,
    }
    values.update(overrides)
    return CombatantView(**values)


def _meter(**overrides):
    values = {
        "current": 10,
        "maximum": 100,
        "fill_bps": 1000,
        "ready": False,
        "activation_key": "S",
        "activation_offered": False,
    }
    values.update(overrides)
    return SuperMeterView(**values)


def _view(**overrides):
    values = {
        "interaction_phase": InteractionPhase.ACTIONS,
        "player": _combatant(),
        "enemy": _combatant(
            display_name="Goblin",
            hp_current=60,
            hp_maximum=60,
            mana_current=None,
            mana_maximum=None,
            super_current=None,
            super_maximum=None,
        ),
        "super_meter": _meter(),
    }
    values.update(overrides)
    return BattleView(**values)


def test_models_are_frozen():
    models = [
        _combatant(),
        ActionOptionView(ActionIntent.ATTACK, 1, "Attack", True),
        MoveOptionView("Brace", 1, "Brace", ("Utility",), "Brace.", "5 Mana", True),
        InventoryItemOptionView("ember_shard", 1, "Ember Shard", 1, True),
        InventoryCommandOptionView(
            InventoryCommand.USE,
            1,
            "Use",
            False,
            InventoryAvailabilityReason.MISSING_COMPANION,
        ),
        InventoryInspectionView("ember_shard", "Ember Shard", "A hot mineral."),
        InventoryConfirmationView(
            "ember_shard",
            "Ember Shard",
            "deep_coal",
            "Deep Coal",
            "prepare_fire_infusion",
            "Infused Barb",
        ),
        _meter(),
        BattleLogEntry(BattleEventType.ENCOUNTER_START),
        BattleVisualView(("player",), ("enemy",)),
        _view(),
    ]

    for model in models:
        with pytest.raises(FrozenInstanceError):
            setattr(model, "unexpected", True)


def test_model_collections_require_tuples():
    with pytest.raises(TypeError):
        _combatant(temporary_labels=["Brace"])
    with pytest.raises(TypeError):
        MoveOptionView("Brace", 1, "Brace", ["Utility"], "Brace.", "5 Mana", True)
    with pytest.raises(TypeError):
        BattleVisualView(["player"], ())
    with pytest.raises(TypeError):
        _view(action_options=[])
    with pytest.raises(TypeError):
        _view(log_entries=[])
    with pytest.raises(TypeError):
        _view(inventory_items=[])


def test_resources_reject_negative_or_inconsistent_values():
    with pytest.raises(ValueError):
        _combatant(hp_current=-1)
    with pytest.raises(ValueError):
        _combatant(hp_current=117)
    with pytest.raises(ValueError):
        _combatant(mana_current=1, mana_maximum=None)
    with pytest.raises(ValueError):
        _meter(current=101)
    with pytest.raises(ValueError):
        _meter(maximum=0)
    with pytest.raises(ValueError):
        _meter(fill_bps=10_001)


def test_action_and_move_availability_are_explicit():
    disabled_action = ActionOptionView(
        ActionIntent.ITEMS,
        4,
        "Items",
        False,
        ActionAvailabilityReason.NOT_IMPLEMENTED,
    )
    disabled_move = MoveOptionView(
        "Cinderlung Vesper",
        2,
        "Cinderlung Vesper",
        ("Fire Magic", "3 Mana"),
        "A black war-breath erupts forward.",
        "3 Mana",
        False,
        MoveAvailabilityReason.INSUFFICIENT_RESOURCE,
    )

    assert disabled_action.disabled_reason == ActionAvailabilityReason.NOT_IMPLEMENTED
    assert disabled_move.disabled_reason == MoveAvailabilityReason.INSUFFICIENT_RESOURCE
    with pytest.raises(ValueError):
        ActionOptionView(ActionIntent.ITEMS, 4, "Items", False)
    with pytest.raises(ValueError):
        ActionOptionView(
            ActionIntent.ATTACK,
            1,
            "Attack",
            True,
            ActionAvailabilityReason.NO_REGULAR_MOVES,
        )


def test_input_rejection_is_structured_without_terminal_prose():
    entry = BattleLogEntry(
        event_type=BattleEventType.INPUT_REJECTED,
        rejection_reason=InputRejectionReason.ACTION_UNAVAILABLE,
    )

    assert entry.rejection_reason == InputRejectionReason.ACTION_UNAVAILABLE
    assert "not available" not in repr(entry)
    with pytest.raises(ValueError):
        BattleLogEntry(event_type=BattleEventType.INPUT_REJECTED)
    with pytest.raises(ValueError):
        BattleLogEntry(
            event_type=BattleEventType.DAMAGE,
            rejection_reason=InputRejectionReason.MOVE_UNAVAILABLE,
        )


def test_battle_log_entry_keeps_semantic_result_values():
    entry = BattleLogEntry(
        event_type=BattleEventType.DAMAGE,
        actor_name="Ser Branoc",
        target_name="Goblin",
        action_name="Ironwake Dismemberment",
        accepted=True,
        hit=True,
        amount=21,
        critical=True,
        resource_spent=0,
    )

    assert entry.amount == 21
    assert entry.critical is True
    with pytest.raises(ValueError):
        BattleLogEntry(BattleEventType.DAMAGE, amount=-1)


def test_battle_view_contains_only_presentation_values():
    action = ActionOptionView(ActionIntent.ATTACK, 1, "Attack", True)
    move = MoveOptionView("Brace", 1, "Brace", ("Utility",), "Brace.", "5 Mana", True)
    entry = BattleLogEntry(BattleEventType.UTILITY, action_name="Brace", accepted=True, hit=True)
    view = _view(
        interaction_phase=InteractionPhase.REGULAR_MOVES,
        action_options=(action,),
        move_options=(move,),
        log_entries=(entry,),
    )

    assert view.action_options == (action,)
    assert view.move_options == (move,)
    assert view.log_entries == (entry,)
    with pytest.raises(TypeError):
        _view(player=object())
    with pytest.raises(TypeError):
        _view(move_options=(object(),))


def test_super_activation_requires_ready_meter():
    ready = _meter(current=100, fill_bps=10_000, ready=True, activation_offered=True)

    assert ready.activation_key == "S"
    with pytest.raises(ValueError):
        _meter(activation_offered=True)
