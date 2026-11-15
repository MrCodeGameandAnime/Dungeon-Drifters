"""Durable alchemical crafting and profession progression."""

from dataclasses import dataclass
from enum import StrEnum

from app.content.hub_economy import get_alchemy_recipe
from app.game.game_state import GameState
from app.game.party_state import DungeonPhase
from app.persistence.save_port_contract import (
    SaveLoadStatus,
    SavePortError,
    is_save_port,
)


class AlchemyStatus(StrEnum):
    READY = "ready"
    CRAFTED = "crafted"
    CONFIRMATION_REQUIRED = "confirmation_required"
    CANCELLED = "cancelled"
    STALE_CONFIRMATION = "stale_confirmation"
    STALE_TRANSACTION = "stale_transaction"
    INSUFFICIENT_INGREDIENTS = "insufficient_ingredients"
    UNKNOWN_RECIPE = "unknown_recipe"
    NOT_AVAILABLE = "not_available"
    SAVE_FAILED = "save_failed"


@dataclass(frozen=True)
class AlchemyCraftPreview:
    recipe_id: str
    ingredient_costs: tuple[tuple[str, int], ...]
    outputs: tuple[tuple[str, int], ...]
    experience_award: int
    transaction_sequence: int
    status: AlchemyStatus
    requires_confirmation: bool

    @property
    def can_apply(self):
        return self.status is AlchemyStatus.READY


@dataclass(frozen=True)
class AlchemyResult:
    status: AlchemyStatus
    game_state: GameState
    preview: AlchemyCraftPreview | None = None

    @property
    def success(self):
        return self.status is AlchemyStatus.CRAFTED


class AlchemyService:
    def __init__(self, *, save_port):
        if not is_save_port(save_port):
            raise TypeError("save_port must satisfy SavePort")
        self._save_port = save_port

    @staticmethod
    def preview_recipe(game_state, *, recipe_id, expected_transaction_sequence=None):
        if not isinstance(game_state, GameState):
            raise TypeError("game_state must be a GameState")
        if not isinstance(recipe_id, str) or not recipe_id:
            raise ValueError("recipe_id must be a nonempty string")
        recipe = get_alchemy_recipe(recipe_id)
        economy = game_state.party_state.hub_economy_state
        status = AlchemyStatus.READY
        if recipe is None:
            status = AlchemyStatus.UNKNOWN_RECIPE
            ingredient_costs = ()
            outputs = ()
            experience_award = 0
            requires_confirmation = False
        else:
            ingredient_costs = recipe.ingredient_costs
            output_count = _mastery_output_count(
                economy.alchemy_level if recipe.mastery_output else 1
            )
            outputs = tuple(
                (item_id, quantity * output_count)
                for item_id, quantity in recipe.outputs
            )
            experience_award = recipe.experience_award
            requires_confirmation = recipe.requires_confirmation
            if any(
                game_state.party_state.shared_items.get(item_id, 0) < quantity
                for item_id, quantity in ingredient_costs
            ):
                status = AlchemyStatus.INSUFFICIENT_INGREDIENTS
        if game_state.party_state.phase not in {
            DungeonPhase.HUB,
            DungeonPhase.PARTY_READY,
        } or economy.current_hub_visit_id is None:
            status = AlchemyStatus.NOT_AVAILABLE
        if (
            expected_transaction_sequence is not None
            and expected_transaction_sequence != economy.transaction_sequence
        ):
            status = AlchemyStatus.STALE_TRANSACTION
        return AlchemyCraftPreview(
            recipe_id,
            tuple(sorted(ingredient_costs)),
            tuple(sorted(outputs)),
            experience_award,
            economy.transaction_sequence,
            status,
            requires_confirmation,
        )

    def craft(self, game_state, *, recipe_id, expected_transaction_sequence):
        preview = self.preview_recipe(
            game_state,
            recipe_id=recipe_id,
            expected_transaction_sequence=expected_transaction_sequence,
        )
        if not preview.can_apply:
            return AlchemyResult(preview.status, game_state, preview)
        if preview.requires_confirmation:
            return AlchemyResult(
                AlchemyStatus.CONFIRMATION_REQUIRED,
                game_state,
                preview,
            )
        return self._commit_craft(game_state, preview)

    @staticmethod
    def preview_return_talisman(game_state, *, expected_transaction_sequence):
        return AlchemyService.preview_recipe(
            game_state,
            recipe_id="return_talisman",
            expected_transaction_sequence=expected_transaction_sequence,
        )

    def craft_return_talisman(
        self,
        game_state,
        *,
        expected_transaction_sequence,
        confirmation=None,
    ):
        preview = self.preview_return_talisman(
            game_state,
            expected_transaction_sequence=expected_transaction_sequence,
        )
        if not preview.can_apply:
            return AlchemyResult(preview.status, game_state, preview)
        if confirmation is None:
            return AlchemyResult(
                AlchemyStatus.CONFIRMATION_REQUIRED,
                game_state,
                preview,
            )
        if confirmation != preview:
            return AlchemyResult(
                AlchemyStatus.STALE_CONFIRMATION,
                game_state,
                preview,
            )
        return self._commit_craft(game_state, preview)

    @staticmethod
    def cancel_return_talisman(game_state, preview):
        return AlchemyResult(AlchemyStatus.CANCELLED, game_state, preview)

    def _commit_craft(self, game_state, preview):
        candidate = game_state.clone()
        party = candidate.party_state
        economy = party.hub_economy_state
        costs = dict(preview.ingredient_costs)
        if not party.spend_shared_items(costs):
            return AlchemyResult(
                AlchemyStatus.INSUFFICIENT_INGREDIENTS,
                game_state,
                preview,
            )
        party.add_shared_items(dict(preview.outputs))
        if preview.experience_award:
            economy.add_alchemy_experience(preview.experience_award)
        if not economy.advance_transaction(preview.transaction_sequence):
            return AlchemyResult(
                AlchemyStatus.STALE_TRANSACTION,
                game_state,
                preview,
            )
        try:
            saved = self._save_port.save(candidate)
        except (OSError, SavePortError, TypeError, ValueError):
            saved = None
        if saved is None or saved.status is not SaveLoadStatus.SAVED:
            return AlchemyResult(AlchemyStatus.SAVE_FAILED, game_state, preview)
        return AlchemyResult(AlchemyStatus.CRAFTED, candidate, preview)


def _mastery_output_count(level):
    if level >= 100:
        return 4
    if level >= 60:
        return 3
    if level >= 25:
        return 2
    return 1


__all__ = [
    "AlchemyCraftPreview",
    "AlchemyResult",
    "AlchemyService",
    "AlchemyStatus",
]
