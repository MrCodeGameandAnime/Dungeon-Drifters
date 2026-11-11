import pytest

from app.game.hub_economy import HubEconomyService
from game_test_support import completed_hub_game, hub_game


def test_purchase_uses_shared_gold_and_adds_only_to_secured_storage():
    game = hub_game(gold=75)
    service = HubEconomyService(game)

    result = service.buy(item_id="healing_potion", quantity=2)

    assert result.success is True
    assert result.gold_delta == -16
    assert game.party_state.shared_gold == 59
    assert game.party_state.shared_items == {"healing_potion": 2}
    assert game.party_state.carried_items == {}


@pytest.mark.parametrize("quantity", (0, -1, True, 1.5))
def test_purchase_rejects_invalid_quantity_without_mutation(quantity):
    game = hub_game(gold=75)
    before = game.party_state.snapshot()

    with pytest.raises((TypeError, ValueError)):
        HubEconomyService(game).buy(item_id="healing_potion", quantity=quantity)

    assert game.party_state.snapshot() == before


def test_unaffordable_or_unknown_purchase_is_atomic():
    game = hub_game(gold=3)
    before = game.party_state.snapshot()
    service = HubEconomyService(game)

    assert service.buy(item_id="healing_potion", quantity=1).reason == "insufficient_gold"
    assert service.buy(item_id="not_an_item", quantity=1).reason == "unknown_item"
    assert game.party_state.snapshot() == before


def test_sale_uses_only_stored_sellable_items_and_floors_half_price():
    game = hub_game(gold=0)
    game.party_state.add_shared_items({"goblin_scrap": 2, "goblin_lord_core": 1})
    service = HubEconomyService(game)

    result = service.sell(item_id="goblin_scrap", quantity=1)

    assert result.success is True
    assert result.gold_delta == 1
    assert game.party_state.shared_gold == 1
    assert game.party_state.shared_items == {"goblin_scrap": 1, "goblin_lord_core": 1}
    assert service.sell(item_id="goblin_lord_core", quantity=1).reason == "not_sellable"
    assert game.party_state.shared_items["goblin_lord_core"] == 1


def test_pack_transfer_loads_and_unloads_without_changing_gold():
    game = hub_game(gold=75)
    party = game.party_state
    party.add_shared_items({"healing_potion": 2})
    service = HubEconomyService(game)

    assert service.load(item_id="healing_potion", quantity=1).success
    assert party.shared_items == {"healing_potion": 1}
    assert party.carried_items == {"healing_potion": 1}
    assert service.unload(item_id="healing_potion", quantity=1).success
    assert party.shared_items == {"healing_potion": 2}
    assert party.carried_items == {}
    assert party.shared_gold == 75


def test_pack_transfer_rejects_materials_or_wrong_phase_without_mutation():
    game = completed_hub_game()
    party = game.party_state
    party.add_shared_items({"grade_i_metal": 1, "healing_potion": 1})
    service = HubEconomyService(game)
    before = party.snapshot()

    assert service.load(item_id="grade_i_metal", quantity=1).reason == "not_carryable"
    assert party.snapshot() == before
    assert party.start_floor_one_run() == 100
    before = party.snapshot()
    assert service.unload(item_id="healing_potion", quantity=1).reason == "hub_only"
    assert party.snapshot() == before


def test_alchemy_consumes_inputs_and_credits_output_atomically_without_crafting_xp():
    game = hub_game(gold=75)
    party = game.party_state
    party.add_shared_items({"medicinal_herb": 1, "clean_water": 1})
    before_xp = party.crafting_experience

    result = HubEconomyService(game).craft_alchemy("healing_potion")

    assert result.success is True
    assert party.shared_items == {"healing_potion": 1}
    assert party.crafting_experience == before_xp


def test_alchemy_rejects_missing_inputs_without_partial_mutation():
    game = hub_game(gold=75)
    game.party_state.add_shared_items({"medicinal_herb": 2})
    before = game.party_state.snapshot()

    result = HubEconomyService(game).craft_alchemy("healing_potion")

    assert result.success is False
    assert result.reason == "missing_ingredients"
    assert game.party_state.snapshot() == before
