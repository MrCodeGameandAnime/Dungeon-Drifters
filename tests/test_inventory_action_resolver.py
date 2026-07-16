from dataclasses import FrozenInstanceError

import pytest

from app.combat.result import CombatOutcome, CombatOutcomeTarget, CombatOutcomeType
from app.player.character import Brawler, RogueArcher
from app.player.character_run_state import (
    CharacterRunState,
    InfusionKind,
    InventoryActionId,
    PreparedPayloadId,
    RunItemId,
)
from app.player.inventory_action import (
    InventoryActionRejectionReason,
    InventoryActionResolver,
    InventoryActionResult,
)
from app.player.player_state import PlayerState


def test_preparation_atomically_consumes_both_compounds_and_creates_one_payload():
    run_state = PlayerState(RogueArcher()).character_run_state

    result = InventoryActionResolver().resolve(
        InventoryActionId.PREPARE_FIRE_INFUSION,
        run_state,
    )

    assert result.accepted is True
    assert result.reason is None
    assert run_state.item_quantity(RunItemId.EMBER_SHARD) == 0
    assert run_state.item_quantity(RunItemId.DEEP_COAL) == 0
    assert run_state.payload_prepared(PreparedPayloadId.INFUSED_BARB) is True
    assert tuple(outcome.outcome_type for outcome in result.outcomes) == (
        CombatOutcomeType.COMPOUNDS_CONSUMED,
        CombatOutcomeType.FIRE_INFUSION_PREPARED,
    )
    assert all(
        outcome.target == CombatOutcomeTarget.ACTOR
        and outcome.amount == 0
        for outcome in result.outcomes
    )


def test_poison_preparation_consumes_deep_coal_and_night_berry_only():
    run_state = PlayerState(RogueArcher()).character_run_state

    result = InventoryActionResolver().resolve(
        InventoryActionId.PREPARE_POISON_INFUSION,
        run_state,
    )

    assert result.accepted is True
    assert run_state.item_quantity(RunItemId.DEEP_COAL) == 0
    assert run_state.item_quantity(RunItemId.NIGHT_BERRY) == 0
    assert run_state.item_quantity(RunItemId.EMBER_SHARD) == 1
    assert run_state.prepared_infusion() is InfusionKind.POISON
    assert tuple(outcome.outcome_type for outcome in result.outcomes) == (
        CombatOutcomeType.COMPOUNDS_CONSUMED,
        CombatOutcomeType.POISON_INFUSION_PREPARED,
    )


def test_poison_preparation_is_rejected_when_fire_payload_is_already_prepared():
    run_state = PlayerState(RogueArcher()).character_run_state
    fire = InventoryActionResolver().resolve(
        InventoryActionId.PREPARE_FIRE_INFUSION,
        run_state,
    )
    before = run_state.snapshot()

    poison = InventoryActionResolver().resolve(
        InventoryActionId.PREPARE_POISON_INFUSION,
        run_state,
    )

    assert fire.accepted is True
    assert poison.accepted is False
    assert poison.reason == InventoryActionRejectionReason.ALREADY_PREPARED
    assert poison.outcomes == ()
    assert run_state.snapshot() == before


@pytest.mark.parametrize(
    "inventory",
    (
        {RunItemId.EMBER_SHARD: 1},
        {RunItemId.DEEP_COAL: 1},
        {},
    ),
)
def test_missing_ingredient_rejects_without_partial_consumption(inventory):
    run_state = CharacterRunState(
        inventory=inventory,
        prepared_payloads={PreparedPayloadId.INFUSED_BARB: None},
    )
    before = run_state.snapshot()

    result = InventoryActionResolver().resolve(
        InventoryActionId.PREPARE_FIRE_INFUSION,
        run_state,
    )

    assert result.accepted is False
    assert result.reason == InventoryActionRejectionReason.MISSING_INGREDIENTS
    assert result.outcomes == ()
    assert run_state.snapshot() == before


def test_character_without_authored_payload_cannot_prepare_zhaivra_resource():
    run_state = PlayerState(Brawler()).character_run_state
    before = run_state.snapshot()

    result = InventoryActionResolver().resolve(
        InventoryActionId.PREPARE_FIRE_INFUSION,
        run_state,
    )

    assert result.accepted is False
    assert result.reason == InventoryActionRejectionReason.ACTION_UNAVAILABLE
    assert run_state.snapshot() == before


def test_repeated_preparation_is_rejected_without_stacking_or_mutation():
    run_state = PlayerState(RogueArcher()).character_run_state
    resolver = InventoryActionResolver()
    first = resolver.resolve(InventoryActionId.PREPARE_FIRE_INFUSION, run_state)
    after_first = run_state.snapshot()

    second = resolver.resolve(InventoryActionId.PREPARE_FIRE_INFUSION, run_state)

    assert first.accepted is True
    assert second.accepted is False
    assert second.reason == InventoryActionRejectionReason.ALREADY_PREPARED
    assert second.outcomes == ()
    assert run_state.snapshot() == after_first


def test_inventory_action_result_is_immutable_and_validates_rejection_contract():
    result = InventoryActionResult(
        InventoryActionId.PREPARE_FIRE_INFUSION,
        accepted=False,
        reason=InventoryActionRejectionReason.MISSING_INGREDIENTS,
    )

    with pytest.raises(FrozenInstanceError):
        result.accepted = True
    with pytest.raises(ValueError):
        InventoryActionResult(
            InventoryActionId.PREPARE_FIRE_INFUSION,
            accepted=False,
        )
    with pytest.raises(ValueError):
        InventoryActionResult(
            InventoryActionId.PREPARE_FIRE_INFUSION,
            accepted=False,
            reason=InventoryActionRejectionReason.MISSING_INGREDIENTS,
            outcomes=(CombatOutcome(CombatOutcomeType.FIRE_INFUSION_PREPARED),),
        )
    with pytest.raises(TypeError):
        InventoryActionResult(
            InventoryActionId.PREPARE_FIRE_INFUSION,
            accepted=True,
            outcomes=[],
        )


def test_prepare_payload_mutation_revalidates_entire_cost_before_mutating():
    run_state = CharacterRunState(
        inventory={RunItemId.EMBER_SHARD: 1},
        prepared_payloads={PreparedPayloadId.INFUSED_BARB: None},
    )
    before = run_state.snapshot()

    with pytest.raises(ValueError):
        run_state.prepare_payload(
            PreparedPayloadId.INFUSED_BARB,
            {
                RunItemId.EMBER_SHARD: 1,
                RunItemId.DEEP_COAL: 1,
            },
        )

    assert run_state.snapshot() == before
