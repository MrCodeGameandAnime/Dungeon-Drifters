"""Atomic Hub purchases, sales, and shared-inventory Alchemy."""

from dataclasses import dataclass

from app.content.hub_economy import get_alchemy_recipe, get_supply_item
from app.game.game_state import GameState
from app.game.party_state import DungeonPhase, MAX_CARRIED_SUPPLY_UNITS


@dataclass(frozen=True)
class HubEconomyResult:
    success: bool
    reason: str | None = None
    item_id: str | None = None
    quantity: int = 0
    gold_delta: int = 0


class HubEconomyService:
    def __init__(self, game_state):
        if not isinstance(game_state, GameState):
            raise TypeError("game_state must be a GameState")
        self._game_state = game_state

    def buy(self, *, item_id, quantity):
        self._require_item_id(item_id)
        quantity = _positive_quantity(quantity)
        if not self._at_hub():
            return self._rejected("hub_only", item_id, quantity)
        item = get_supply_item(item_id)
        if item is None or not item.shop_stocked:
            return self._rejected("unknown_item", item_id, quantity)
        cost = item.base_price * quantity
        party = self._game_state.party_state
        if party.shared_gold < cost:
            return self._rejected("insufficient_gold", item_id, quantity)
        if not party.spend_shared_gold(cost):
            return self._rejected("insufficient_gold", item_id, quantity)
        party.add_shared_items({item_id: quantity})
        return HubEconomyResult(True, item_id=item_id, quantity=quantity, gold_delta=-cost)

    def sell(self, *, item_id, quantity):
        self._require_item_id(item_id)
        quantity = _positive_quantity(quantity)
        if not self._at_hub():
            return self._rejected("hub_only", item_id, quantity)
        item = get_supply_item(item_id)
        if item is None:
            return self._rejected("unknown_item", item_id, quantity)
        if not item.sellable:
            return self._rejected("not_sellable", item_id, quantity)
        party = self._game_state.party_state
        if party.shared_items.get(item_id, 0) < quantity:
            return self._rejected("insufficient_items", item_id, quantity)
        proceeds = (item.base_price // 2) * quantity
        if not party.spend_shared_items({item_id: quantity}):
            return self._rejected("insufficient_items", item_id, quantity)
        party.add_shared_gold(proceeds)
        return HubEconomyResult(True, item_id=item_id, quantity=quantity, gold_delta=proceeds)

    def load(self, *, item_id, quantity):
        self._require_item_id(item_id)
        quantity = _positive_quantity(quantity)
        if not self._at_hub():
            return self._rejected("hub_only", item_id, quantity)
        item = get_supply_item(item_id)
        if item is None or not item.carryable:
            return self._rejected("not_carryable", item_id, quantity)
        party = self._game_state.party_state
        if party.shared_items.get(item_id, 0) < quantity:
            return self._rejected("insufficient_items", item_id, quantity)
        if party.carried_item_units + quantity > MAX_CARRIED_SUPPLY_UNITS:
            return self._rejected("pack_full", item_id, quantity)
        if not party.load_carried_supplies({item_id: quantity}):
            return self._rejected("transfer_rejected", item_id, quantity)
        return HubEconomyResult(True, item_id=item_id, quantity=quantity)

    def unload(self, *, item_id, quantity):
        self._require_item_id(item_id)
        quantity = _positive_quantity(quantity)
        if not self._at_hub():
            return self._rejected("hub_only", item_id, quantity)
        item = get_supply_item(item_id)
        if item is None or not item.carryable:
            return self._rejected("not_carryable", item_id, quantity)
        party = self._game_state.party_state
        if party.carried_items.get(item_id, 0) < quantity:
            return self._rejected("insufficient_items", item_id, quantity)
        if not party.unload_carried_supplies({item_id: quantity}):
            return self._rejected("transfer_rejected", item_id, quantity)
        return HubEconomyResult(True, item_id=item_id, quantity=quantity)

    def craft_alchemy(self, recipe_id):
        if not isinstance(recipe_id, str) or not recipe_id:
            raise ValueError("recipe_id must be a nonempty string")
        if not self._at_hub():
            return self._rejected("hub_only", recipe_id)
        recipe = get_alchemy_recipe(recipe_id)
        if recipe is None:
            return self._rejected("unknown_recipe", recipe_id)
        party = self._game_state.party_state
        costs = dict(recipe.ingredient_costs)
        if any(party.shared_items.get(item_id, 0) < quantity
               for item_id, quantity in costs.items()):
            return self._rejected("missing_ingredients", recipe_id)
        if not party.spend_shared_items(costs):
            return self._rejected("missing_ingredients", recipe_id)
        party.add_shared_items(dict(recipe.outputs))
        return HubEconomyResult(True, item_id=recipe_id)

    def _at_hub(self):
        return self._game_state.party_state.phase in {
            DungeonPhase.HUB,
            DungeonPhase.PARTY_READY,
        }

    @staticmethod
    def _require_item_id(item_id):
        if not isinstance(item_id, str) or not item_id:
            raise ValueError("item_id must be a nonempty string")

    @staticmethod
    def _rejected(reason, item_id=None, quantity=0):
        return HubEconomyResult(
            False,
            reason=reason,
            item_id=item_id,
            quantity=quantity,
        )


def _positive_quantity(quantity):
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise TypeError("quantity must be an integer")
    if quantity < 1:
        raise ValueError("quantity must be positive")
    return quantity
