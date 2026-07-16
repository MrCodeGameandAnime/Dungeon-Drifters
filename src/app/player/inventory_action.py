"""Resolver-backed actions for character-owned run inventory."""

from dataclasses import dataclass
from enum import StrEnum

from app.combat.result import CombatOutcome, CombatOutcomeTarget, CombatOutcomeType
from app.player.character_run_state import (
    CINDERWRIT_PREPARATION_COST,
    CharacterRunState,
    InventoryActionId,
    PreparedPayloadId,
)


class InventoryActionRejectionReason(StrEnum):
    ACTION_UNAVAILABLE = "action_unavailable"
    ALREADY_PREPARED = "already_prepared"
    MISSING_INGREDIENTS = "missing_ingredients"


@dataclass(frozen=True)
class InventoryActionResult:
    action_id: InventoryActionId
    accepted: bool
    reason: InventoryActionRejectionReason | None = None
    outcomes: tuple[CombatOutcome, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "action_id", _validate_action_id(self.action_id))
        if not isinstance(self.accepted, bool):
            raise TypeError("accepted must be a boolean")
        object.__setattr__(self, "reason", _validate_optional_reason(self.reason))
        object.__setattr__(self, "outcomes", _validate_outcomes(self.outcomes))
        if self.accepted and self.reason is not None:
            raise ValueError("accepted inventory actions must not have a reason")
        if not self.accepted and self.reason is None:
            raise ValueError("rejected inventory actions require a reason")
        if not self.accepted and self.outcomes:
            raise ValueError("rejected inventory actions must not have outcomes")


class InventoryActionResolver:
    def resolve(self, action_id, character_run_state):
        action_id = _validate_action_id(action_id)
        if not isinstance(character_run_state, CharacterRunState):
            raise TypeError("character_run_state must be CharacterRunState")
        if action_id != InventoryActionId.PREPARE_CINDERWRIT:
            return self._rejected(
                action_id,
                InventoryActionRejectionReason.ACTION_UNAVAILABLE,
            )
        return self._prepare_cinderwrit(character_run_state)

    def _prepare_cinderwrit(self, character_run_state):
        action_id = InventoryActionId.PREPARE_CINDERWRIT
        if not character_run_state.supports_payload(PreparedPayloadId.CINDERWRIT):
            return self._rejected(
                action_id,
                InventoryActionRejectionReason.ACTION_UNAVAILABLE,
            )
        if character_run_state.payload_prepared(PreparedPayloadId.CINDERWRIT):
            return self._rejected(
                action_id,
                InventoryActionRejectionReason.ALREADY_PREPARED,
            )
        if not character_run_state.has_items(CINDERWRIT_PREPARATION_COST):
            return self._rejected(
                action_id,
                InventoryActionRejectionReason.MISSING_INGREDIENTS,
            )

        character_run_state.prepare_payload(
            PreparedPayloadId.CINDERWRIT,
            CINDERWRIT_PREPARATION_COST,
        )
        return InventoryActionResult(
            action_id=action_id,
            accepted=True,
            outcomes=(
                CombatOutcome(
                    CombatOutcomeType.COMPOUNDS_CONSUMED,
                    target=CombatOutcomeTarget.ACTOR,
                ),
                CombatOutcome(
                    CombatOutcomeType.CINDERWRIT_PREPARED,
                    target=CombatOutcomeTarget.ACTOR,
                ),
            ),
        )

    @staticmethod
    def _rejected(action_id, reason):
        return InventoryActionResult(
            action_id=action_id,
            accepted=False,
            reason=reason,
        )


def _validate_action_id(action_id):
    try:
        return InventoryActionId(action_id)
    except (TypeError, ValueError) as error:
        raise ValueError(f"invalid inventory action identifier: {action_id!r}") from error


def _validate_optional_reason(reason):
    if reason is None:
        return None
    try:
        return InventoryActionRejectionReason(reason)
    except (TypeError, ValueError) as error:
        raise ValueError(f"invalid inventory action rejection reason: {reason!r}") from error


def _validate_outcomes(outcomes):
    if not isinstance(outcomes, tuple):
        raise TypeError("outcomes must be a tuple")
    if not all(isinstance(outcome, CombatOutcome) for outcome in outcomes):
        raise TypeError("outcomes must contain CombatOutcome values")
    return outcomes
