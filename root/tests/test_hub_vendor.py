import pytest

from app.game.hub_vendor import HubVendorService, HubVendorStatus
from app.game.alchemist import AlchemistService, AlchemistStatus
from app.items.equipment import EquipmentInstance
from app.persistence.save_document import (
    SaveStateValidationError,
    build_save_document,
    reconstruct_game_state,
    validate_save_document,
)
from app.persistence.ports import SaveLoadResult
from app.persistence.save_port_contract import SaveLoadStatus
from app.presentation.overworld_models import OverworldScreen
from app.presentation.overworld_presenter import OverworldPresenter
from tests.game_test_support import hub_game


class MemorySavePort:
    def __init__(self, status=SaveLoadStatus.SAVED):
        self.status = status
        self.saved_states = []

    def inspect(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def load(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def save(self, game_state):
        if self.status is SaveLoadStatus.SAVED:
            self.saved_states.append(game_state.clone())
        return SaveLoadResult(self.status)


def test_purchase_spends_authored_vendor_price_and_finite_stock_once():
    game = hub_game(gold=100)
    save_port = MemorySavePort()
    before = game.party_state.snapshot()

    result = HubVendorService(save_port=save_port).purchase(
        game,
        vendor_id="merchant",
        item_id="healing_potion",
        quantity=1,
        expected_transaction_sequence=0,
    )

    assert result.status is HubVendorStatus.PURCHASED
    assert result.game_state.party_state.shared_gold == 88
    assert result.game_state.party_state.shared_items == {"healing_potion": 1}
    assert result.game_state.party_state.hub_economy["vendor_stock"]["merchant"][
        "healing_potion"
    ] == 0
    assert result.game_state.party_state.hub_economy["transaction_sequence"] == 1
    assert game.party_state.snapshot() == before
    assert len(save_port.saved_states) == 1


def test_armor_purchase_creates_secured_equipment_and_survives_reload():
    game = hub_game(gold=100)
    service = HubVendorService(save_port=MemorySavePort())

    purchased = service.purchase(
        game,
        vendor_id="blacksmith",
        item_id="field_helm",
        quantity=1,
        expected_transaction_sequence=0,
    )

    assert purchased.status is HubVendorStatus.PURCHASED
    assert purchased.game_state.party_state.shared_gold == 76
    assert purchased.game_state.party_state.hub_economy_state.vendor_stock_quantity(
        "blacksmith", "field_helm"
    ) == 0
    assert len(purchased.game_state.party_state.equipment_instances) == 1
    armor = purchased.game_state.party_state.equipment_instances[0]
    assert armor.definition_id == "field_helm"
    assert armor.secured is True
    assert armor.stat_bonuses == {"constitution": 1}

    restored = reconstruct_game_state(build_save_document(purchased.game_state))
    assert restored.party_state.equipment_instances[0].snapshot() == armor.snapshot()


def test_purchase_rejects_stale_sequence_without_mutation_or_save():
    game = hub_game(gold=100)
    save_port = MemorySavePort()
    before = game.party_state.snapshot()

    result = HubVendorService(save_port=save_port).purchase(
        game,
        vendor_id="merchant",
        item_id="healing_potion",
        quantity=1,
        expected_transaction_sequence=1,
    )

    assert result.status is HubVendorStatus.STALE_TRANSACTION
    assert result.game_state is game
    assert game.party_state.snapshot() == before
    assert save_port.saved_states == []


def test_purchase_rejects_out_of_stock_and_wrong_vendor_without_mutation():
    game = hub_game(gold=100)
    save_port = MemorySavePort()
    service = HubVendorService(save_port=save_port)
    before = game.party_state.snapshot()

    wrong_vendor = service.purchase(
        game,
        vendor_id="blacksmith",
        item_id="healing_potion",
        quantity=1,
        expected_transaction_sequence=0,
    )

    assert wrong_vendor.status is HubVendorStatus.UNAVAILABLE_OFFER
    assert game.party_state.snapshot() == before
    assert save_port.saved_states == []


def test_sale_and_partial_buyback_preserve_exact_sale_price():
    game = hub_game(gold=100)
    game.party_state.add_shared_items({"medicinal_herb": 2})
    save_port = MemorySavePort()
    service = HubVendorService(save_port=save_port)

    sold = service.sell(
        game,
        vendor_id="alchemist",
        item_id="medicinal_herb",
        quantity=2,
        expected_transaction_sequence=0,
    )

    assert sold.status is HubVendorStatus.SOLD
    assert sold.gold_delta == 4
    assert sold.sale_id == "sale_1"
    assert sold.game_state.party_state.shared_items.get("medicinal_herb", 0) == 0
    assert sold.game_state.party_state.hub_economy["buyback_records"] == [
        {
            "sale_id": "sale_1",
            "vendor_id": "alchemist",
            "visit_id": "hub_visit_1",
            "item_id": "medicinal_herb",
            "remaining_quantity": 2,
            "original_unit_payout": 2,
        }
    ]

    recovered = service.buyback(
        sold.game_state,
        vendor_id="alchemist",
        sale_id="sale_1",
        quantity=1,
        expected_transaction_sequence=1,
    )

    assert recovered.status is HubVendorStatus.BOUGHT_BACK
    assert recovered.gold_delta == -2
    assert recovered.game_state.party_state.shared_gold == 102
    assert recovered.game_state.party_state.shared_items["medicinal_herb"] == 1
    assert recovered.game_state.party_state.hub_economy["buyback_records"][0][
        "remaining_quantity"
    ] == 1


def test_component_sale_buyback_and_expiry_conserve_inventory_and_future_stock():
    game = hub_game(gold=100)
    economy = game.party_state.hub_economy_state
    component_id = "sunder_spire_blade_reinforced"
    economy.add_component(component_id, 3)
    economy.spend_vendor_stock("blacksmith", component_id, 1)
    economy.spend_vendor_stock("merchant", component_id, 1)
    service = HubVendorService(save_port=MemorySavePort())

    sold = service.sell(
        game,
        vendor_id="blacksmith",
        item_id=component_id,
        quantity=2,
        expected_transaction_sequence=0,
    )
    assert sold.status is HubVendorStatus.SOLD
    assert sold.game_state.party_state.hub_economy["component_stacks"] == {
        component_id: 1
    }
    assert sold.game_state.party_state.shared_gold == 120

    recovered = service.buyback(
        sold.game_state,
        vendor_id="blacksmith",
        sale_id=sold.sale_id,
        quantity=1,
        expected_transaction_sequence=1,
    )
    assert recovered.game_state.party_state.hub_economy["component_stacks"] == {
        component_id: 2
    }
    assert recovered.game_state.party_state.hub_economy["buyback_records"][0][
        "remaining_quantity"
    ] == 1

    party = recovered.game_state.party_state
    party.hub_economy_state.leave_hub()
    assert party.hub_economy["buyback_records"] == []
    assert party.hub_economy["future_stock_queue"] == [
        {
            "sale_id": sold.sale_id,
            "specialist_id": "blacksmith",
            "item_id": component_id,
            "remaining_quantity": 1,
        }
    ]
    assert party.hub_economy_state.replenish_for_qualifying_return(
        {
            "outing_id": "outing_1",
            "floor_id": "floor_one",
            "has_encounter_progress": True,
        },
        recruited_drifter_ids=tuple(
            member.drifter_id for member in recovered.game_state.recruited_members
        ),
        floor_one_cleared=False,
        floor_two_cleared=False,
        floor_three_cleared=False,
    )
    assert party.hub_economy_state.vendor_stock_quantity(
        "blacksmith", component_id
    ) == 1
    assert party.hub_economy_state.vendor_stock_quantity(
        "merchant", component_id
    ) == 1
    assert party.hub_economy["future_stock_queue"] == []
    assert (
        party.hub_economy["component_stacks"][component_id]
        + party.hub_economy_state.vendor_stock_quantity("blacksmith", component_id)
        == 3
    )


def test_save_rejects_unknown_component_stack_and_malformed_buyback_quantity():
    unknown_component = build_save_document(hub_game())
    unknown_component["party"]["hub_economy"]["component_stacks"] = {
        "unrecognized_component": 1
    }
    with pytest.raises(SaveStateValidationError, match="unknown weapon component"):
        validate_save_document(unknown_component)

    game = hub_game()
    game.party_state.add_shared_items({"medicinal_herb": 1})
    sold = HubVendorService(save_port=MemorySavePort()).sell(
        game,
        vendor_id="alchemist",
        item_id="medicinal_herb",
        quantity=1,
        expected_transaction_sequence=0,
    )
    malformed_buyback = build_save_document(sold.game_state)
    malformed_buyback["party"]["hub_economy"]["buyback_records"][0][
        "remaining_quantity"
    ] = 0

    with pytest.raises(SaveStateValidationError, match="remaining_quantity"):
        validate_save_document(malformed_buyback)


def test_stack_sale_buyback_survives_save_reload_and_recovers_remaining_quantity():
    game = hub_game(gold=100)
    game.party_state.add_shared_items({"medicinal_herb": 2})
    service = HubVendorService(save_port=MemorySavePort())
    sold = service.sell(
        game,
        vendor_id="alchemist",
        item_id="medicinal_herb",
        quantity=2,
        expected_transaction_sequence=0,
    )

    restored = reconstruct_game_state(build_save_document(sold.game_state))
    recovered = service.buyback(
        restored,
        vendor_id="alchemist",
        sale_id="sale_1",
        quantity=2,
        expected_transaction_sequence=1,
    )

    assert recovered.status is HubVendorStatus.BOUGHT_BACK
    assert recovered.game_state.party_state.shared_items["medicinal_herb"] == 2
    assert recovered.game_state.party_state.shared_gold == 100
    assert recovered.game_state.party_state.hub_economy["buyback_records"] == []


def test_equipment_buyback_restores_exact_snapshot_after_save_reload():
    game = hub_game(gold=100)
    equipment = EquipmentInstance.create(
        instance_id="00000000-0000-4000-8000-000000000911",
        definition_id="field_helm",
        source_id="m65_buyback_review",
        secured=True,
        stat_bonuses={"constitution": 3},
        rarity="common",
        upgrade_rank=1,
    )
    game.party_state.add_equipment_instance(equipment)
    service = AlchemistService(save_port=MemorySavePort())
    preview = service.preview_sale(game, instance_id=equipment.instance_id)

    sold = service.sell(
        game,
        instance_id=equipment.instance_id,
        confirmation=preview,
    )

    assert sold.status is AlchemistStatus.SOLD
    restored = reconstruct_game_state(build_save_document(sold.game_state))
    buyback = HubVendorService(save_port=MemorySavePort()).buyback(
        restored,
        vendor_id="blacksmith",
        sale_id="sale_1",
        expected_transaction_sequence=1,
    )

    assert buyback.status is HubVendorStatus.BOUGHT_BACK
    assert buyback.game_state.party_state.equipment_instances[0].snapshot() == (
        equipment.snapshot()
    )


def test_vendor_views_expose_current_buybacks_and_installable_components():
    game = hub_game(gold=100)
    game.party_state.add_shared_items({"medicinal_herb": 1})
    sold = HubVendorService(save_port=MemorySavePort()).sell(
        game,
        vendor_id="alchemist",
        item_id="medicinal_herb",
        quantity=1,
        expected_transaction_sequence=0,
    )
    economy = sold.game_state.party_state.hub_economy_state
    economy.add_component("sunder_spire_blade_reinforced", 1)

    alchemist = OverworldPresenter().build(
        sold.game_state,
        screen=OverworldScreen.ALCHEMIST,
    ).hub_economy
    blacksmith = OverworldPresenter().build(
        sold.game_state,
        screen=OverworldScreen.BLACKSMITH,
    ).hub_economy
    component = next(
        item for item in blacksmith.items
        if item.item_id == "sunder_spire_blade_reinforced"
    )

    assert len(alchemist.buybacks) == 1
    assert alchemist.buybacks[0].sale_id == sold.sale_id
    assert alchemist.buybacks[0].remaining_quantity == 1
    assert blacksmith.buybacks == ()
    assert component.can_install_component is True


def test_failed_local_purchase_save_does_not_publish_gold_stock_or_items():
    game = hub_game(gold=100)
    save_port = MemorySavePort(SaveLoadStatus.INVALID)
    before = game.party_state.snapshot()

    result = HubVendorService(save_port=save_port).purchase(
        game,
        vendor_id="merchant",
        item_id="healing_potion",
        quantity=1,
        expected_transaction_sequence=0,
    )

    assert result.status is HubVendorStatus.SAVE_FAILED
    assert result.game_state is game
    assert game.party_state.snapshot() == before


def test_component_purchase_and_install_replace_with_conserved_stack():
    game = hub_game(gold=100)
    save_port = MemorySavePort()
    service = HubVendorService(save_port=save_port)
    weapon = game.player_state.signature_weapon_state
    slot_id, starter_id = next(iter(weapon.components.items()))
    component_id = "sunder_spire_blade_reinforced"

    bought = service.purchase(
        game,
        vendor_id="blacksmith",
        item_id=component_id,
        quantity=1,
        expected_transaction_sequence=0,
    )

    assert bought.status is HubVendorStatus.PURCHASED
    assert bought.game_state.party_state.hub_economy["component_stacks"] == {
        component_id: 1
    }

    installed = service.install_component(
        bought.game_state,
        target_drifter_id="branoc",
        component_id=component_id,
        expected_transaction_sequence=1,
    )

    assert installed.status is HubVendorStatus.COMPONENT_INSTALLED
    assert installed.game_state.player_state.signature_weapon_state.components[
        slot_id
    ] == component_id
    assert installed.game_state.party_state.hub_economy["component_stacks"] == {
        starter_id: 1
    }


def test_crafting_component_returns_displaced_part_and_keeps_progression_rules():
    game = hub_game(gold=100)
    game.party_state.add_shared_items({"grade_i_metal": 1})
    save_port = MemorySavePort()

    result = HubVendorService(save_port=save_port).craft_component(
        game,
        target_drifter_id="branoc",
        component_id="sunder_spire_blade_reinforced",
        expected_transaction_sequence=0,
    )

    assert result.status is HubVendorStatus.COMPONENT_CRAFTED
    assert result.game_state.party_state.hub_economy["component_stacks"] == {
        "sunder_spire_blade": 1
    }
    assert result.game_state.party_state.shared_items.get("grade_i_metal", 0) == 0
    assert result.game_state.party_state.crafting_experience == 10


def test_stale_component_operation_and_failed_save_leave_original_untouched():
    game = hub_game(gold=100)
    game.party_state.hub_economy_state.add_component("sunder_spire_blade_reinforced", 1)
    before = game.party_state.snapshot()
    save_port = MemorySavePort(SaveLoadStatus.INVALID)

    result = HubVendorService(save_port=save_port).install_component(
        game,
        target_drifter_id="branoc",
        component_id="sunder_spire_blade_reinforced",
        expected_transaction_sequence=0,
    )

    assert result.status is HubVendorStatus.SAVE_FAILED
    assert result.game_state is game
    assert game.party_state.snapshot() == before
