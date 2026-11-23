from dataclasses import replace

import pytest

from app.content.catalog import WEAPON_SPECS
from app.content.equipment_spec import EQUIPMENT_TEMPLATES
from app.content.hub_economy import get_supply_item
from app.content.vendor_catalog import (
    FIRST_CLEAR_REWARDS,
    RESERVED_MAGIC_CRYSTAL_GRADES,
    VENDOR_MERCHANDISE,
    FirstClearRewardSpec,
    validate_vendor_catalog,
)
from app.content.weapon_progression_spec import MATERIAL_SPECS


def _merchandise(item_id):
    return next(spec for spec in VENDOR_MERCHANDISE if spec.item_id == item_id)


def _offer(item_id, vendor_id):
    return next(
        offer
        for offer in _merchandise(item_id).offers
        if offer.vendor_id == vendor_id
    )


def test_vendor_catalog_references_authored_items_and_unique_vendor_offers():
    validate_vendor_catalog(VENDOR_MERCHANDISE, FIRST_CLEAR_REWARDS)

    item_ids = [spec.item_id for spec in VENDOR_MERCHANDISE]
    assert len(item_ids) == len(set(item_ids))
    for spec in VENDOR_MERCHANDISE:
        vendor_ids = [offer.vendor_id for offer in spec.offers]
        assert len(vendor_ids) == len(set(vendor_ids))


def test_alchemist_prices_use_the_approved_exact_whole_gold_schedule():
    expected = {
        "medicinal_herb": (4, 3, 2),
        "clean_water": (4, 3, 2),
        "charcoal_dust": (4, 3, 2),
        "sulfur": (4, 3, 2),
        "magic_reagent": (8, 6, 4),
        "aether_dust": (8, 6, 4),
        "healing_potion": (12, 9, None),
        "mana_potion": (20, 15, None),
        "smoke_bomb": (12, 9, None),
    }

    for item_id, (base_price, alchemist_price, resale_price) in expected.items():
        item = get_supply_item(item_id)
        merchandise = _merchandise(item_id)
        assert item.base_price == base_price
        assert _offer(item_id, "alchemist").unit_price == alchemist_price
        assert _offer(item_id, "merchant").unit_price == base_price
        assert merchandise.resale_price == resale_price
        assert base_price * 3 == alchemist_price * 4


def test_authored_stock_capacities_and_initial_quantities_match_schedule():
    alchemical_ingredients = {
        "medicinal_herb",
        "clean_water",
        "charcoal_dust",
        "sulfur",
        "magic_reagent",
        "aether_dust",
    }
    for spec in VENDOR_MERCHANDISE:
        for offer in spec.offers:
            expected_cap = (
                2
                if spec.category == "alchemical"
                and offer.vendor_id == "alchemist"
                and spec.item_id in alchemical_ingredients
                else 1
            )
            if spec.category == "smith_material" and offer.vendor_id == "blacksmith":
                material = next(
                    material
                    for material in MATERIAL_SPECS
                    if material.item_id == spec.item_id
                )
                if material.grade == 1:
                    expected_cap = 2
            assert offer.stock_cap == expected_cap
            higher_grade_component = (
                spec.category == "component" and spec.item_id.startswith("m8_")
            )
            sale_fed = offer.sale_fed_only or higher_grade_component
            assert offer.initial_stock == (
                0 if offer.future_content or sale_fed else expected_cap
            )
            assert offer.refill_per_qualifying_return == (
                0 if sale_fed else expected_cap
            )

    for material in MATERIAL_SPECS:
        expected_cap = 2 if material.grade == 1 else 1
        expected_unlock = {
            1: None,
            2: "floor_one",
            3: "floor_two",
            4: "floor_three",
        }[material.grade]
        for vendor_id in ("blacksmith", "merchant"):
            offer = _offer(material.item_id, vendor_id)
            vendor_cap = expected_cap if vendor_id == "blacksmith" else 1
            assert offer.stock_cap == vendor_cap
            assert offer.initial_stock == vendor_cap
            assert offer.unlock_after_floor == expected_unlock


def test_finished_alchemy_consumables_are_not_sellable_or_stocked_in_legacy_shop():
    for item_id in ("healing_potion", "mana_potion", "smoke_bomb"):
        item = get_supply_item(item_id)
        assert item is not None
        assert item.sellable is False
        if item_id != "healing_potion":
            assert item.shop_stocked is False


def test_m8_component_offers_are_recruitment_and_clear_gated_sale_fed_stock():
    components_by_id = {
        component.component_id: weapon.intended_wielder.lower()
        for weapon in WEAPON_SPECS
        for component in weapon.progression.components
        if component.component_id.startswith("m8_")
    }
    assert len(components_by_id) == 48
    for item_id, wielder_id in components_by_id.items():
        grade = next(
            grade
            for suffix, grade in (
                ("_grade_ii", 2),
                ("_grade_iii", 3),
                ("_grade_iv", 4),
            )
            if item_id.endswith(suffix)
        )
        expected_floor = {
            2: "floor_two",
            3: "floor_three",
            4: "floor_four",
        }[grade]
        merchandise = _merchandise(item_id)
        assert merchandise.base_price == 20
        assert merchandise.resale_price == 10
        assert merchandise.sale_vendor_id == "blacksmith"
        assert merchandise.future_stock_eligible is True
        for vendor_id in ("blacksmith", "merchant"):
            offer = _offer(item_id, vendor_id)
            assert offer.unit_price == 20
            assert offer.stock_cap == 1
            assert offer.initial_stock == 0
            assert offer.refill_per_qualifying_return == 0
            assert offer.sale_fed_only is True
            assert offer.unlock_drifter_id == wielder_id
            assert offer.unlock_after_floor == expected_floor


def test_mana_potion_and_new_ingredients_are_catalog_only_until_later_slices():
    mana_potion = get_supply_item("mana_potion")
    assert mana_potion.mana_restore_percent == 30
    assert mana_potion.carryable is True
    for item_id in (
        "sulfur",
        "magic_reagent",
        "aether_dust",
        "grade_i_magic_crystal",
        "grade_ii_magic_crystal",
        "grade_iii_magic_crystal",
        "grade_iv_magic_crystal",
        "mythril_plate",
    ):
        item = get_supply_item(item_id)
        assert item is not None
        assert item.shop_stocked is False
        assert item.carryable is False


def test_crystals_are_progression_gated_and_grade_v_has_no_item_or_offer():
    for grade, floor_id, price in (
        ("i", "floor_one", 12),
        ("ii", "floor_two", 24),
        ("iii", "floor_three", 48),
    ):
        item_id = f"grade_{grade}_magic_crystal"
        offer = _offer(item_id, "merchant")
        assert offer.unit_price == price
        assert offer.unlock_after_floor == floor_id
        assert offer.initial_stock == 1
        assert offer.stock_cap == 1
        assert any(
            reward.item_id == item_id and reward.floor_id == floor_id
            for reward in FIRST_CLEAR_REWARDS
        )

    grade_four = _offer("grade_iv_magic_crystal", "merchant")
    assert grade_four.unlock_after_floor == "floor_four"
    assert grade_four.initial_stock == 0
    assert grade_four.future_content is True
    assert RESERVED_MAGIC_CRYSTAL_GRADES == (5,)
    assert get_supply_item("grade_v_magic_crystal") is None
    assert all(spec.item_id != "grade_v_magic_crystal" for spec in VENDOR_MERCHANDISE)


def test_first_clear_rewards_are_one_time_and_floor_scoped():
    assert {
        (reward.source_id, reward.floor_id, reward.item_id, reward.quantity)
        for reward in FIRST_CLEAR_REWARDS
    } == {
        ("m65_floor_one_crystal", "floor_one", "grade_i_magic_crystal", 1),
        ("m65_floor_two_crystal", "floor_two", "grade_ii_magic_crystal", 1),
        ("m65_floor_two_mythril", "floor_two", "mythril_plate", 1),
        ("m65_floor_three_crystal", "floor_three", "grade_iii_magic_crystal", 1),
    }


def test_first_clear_reward_source_ids_are_unique():
    duplicate_source = replace(
        FIRST_CLEAR_REWARDS[1],
        source_id=FIRST_CLEAR_REWARDS[0].source_id,
    )
    rewards = (FIRST_CLEAR_REWARDS[0], duplicate_source, *FIRST_CLEAR_REWARDS[2:])

    with pytest.raises(ValueError, match="source IDs must be unique"):
        validate_vendor_catalog(VENDOR_MERCHANDISE, rewards)


def test_first_clear_reward_source_id_uses_authored_identifier_format():
    with pytest.raises(ValueError, match="source ID"):
        FirstClearRewardSpec("invalid source", "floor_one", "grade_i_magic_crystal", 1)


def test_component_offers_cover_each_authored_part_for_its_wielder():
    components = {
        component.component_id: weapon.intended_wielder.lower()
        for weapon in WEAPON_SPECS
        for component in weapon.progression.components
    }
    offered_components = {
        spec.item_id: _offer(spec.item_id, "blacksmith").unlock_drifter_id
        for spec in VENDOR_MERCHANDISE
        if spec.category == "component"
    }

    assert offered_components == components
    for component_id, drifter_id in components.items():
        assert _offer(component_id, "blacksmith").unlock_drifter_id == drifter_id
        assert _offer(component_id, "merchant").unlock_drifter_id == drifter_id
        component = next(
            component
            for weapon in WEAPON_SPECS
            for component in weapon.progression.components
            if component.component_id == component_id
        )
        price = 8 if component.is_starting else 20
        higher_grade = component.component_id.startswith("m8_")
        expected_floor = None
        if higher_grade:
            suffix_floor = {
                "grade_ii": "floor_two",
                "grade_iii": "floor_three",
                "grade_iv": "floor_four",
            }
            expected_floor = next(
                floor_id
                for suffix, floor_id in suffix_floor.items()
                if component.component_id.endswith(suffix)
            )
        for vendor_id in ("blacksmith", "merchant"):
            assert _offer(component_id, vendor_id).unit_price == price
            assert _offer(component_id, vendor_id).stock_cap == 1
            assert _offer(component_id, vendor_id).initial_stock == (
                0 if higher_grade else 1
            )
            assert _offer(component_id, vendor_id).refill_per_qualifying_return == (
                0 if higher_grade else 1
            )
            assert _offer(component_id, vendor_id).sale_fed_only is higher_grade
            assert _offer(component_id, vendor_id).unlock_after_floor == expected_floor


def test_equipment_offers_resolve_to_all_fixed_templates_with_authored_roll_policy():
    prices = {
        "field_helm": 24,
        "field_chest": 40,
        "field_gloves": 24,
        "field_boots": 24,
        "iron_ring": 20,
        "wayfinder_pendant": 20,
    }
    equipment = {
        spec.item_id: spec
        for spec in VENDOR_MERCHANDISE
        if spec.category in {"armor", "accessory"}
    }
    assert set(equipment) == {template.definition_id for template in EQUIPMENT_TEMPLATES}

    for template_id, template in equipment.items():
        assert equipment[template_id].base_price == prices[template_id]
        offers = {offer.vendor_id: offer for offer in template.offers}
        if template.category == "armor":
            assert set(offers) == {"blacksmith", "merchant"}
            assert template.equipment_rarity_id == "common"
            assert template.equipment_stat_policy == "minimum"
        else:
            assert set(offers) == {"merchant"}
            assert template.equipment_rarity_id is None
            assert template.equipment_stat_policy == "fixed_authored"
        assert template.equipment_modifier_ids == ()


def test_return_talisman_markup_and_mythril_source_match_approved_values():
    talisman = _merchandise("return_talisman")
    assert talisman.base_price == 80
    assert _offer("return_talisman", "merchant").unit_price == 100
    assert 100 * 4 == 80 * 5
    assert {offer.vendor_id for offer in talisman.offers} == {"merchant"}

    mythril = _merchandise("mythril_plate")
    assert mythril.base_price == 80
    assert mythril.resale_price == 40
    assert mythril.future_stock_eligible is True
    assert {offer.vendor_id for offer in mythril.offers} == {"blacksmith"}
    assert _offer("mythril_plate", "blacksmith").sale_fed_only is True


@pytest.mark.parametrize(
    "mutate",
    (
        lambda specs: (replace(specs[0], item_id="missing_catalog_item"), *specs[1:]),
        lambda specs: (replace(specs[0], offers=()), *specs[1:]),
    ),
)
def test_catalog_validator_rejects_unknown_items_and_empty_offer_sets(mutate):
    with pytest.raises((TypeError, ValueError)):
        validate_vendor_catalog(mutate(VENDOR_MERCHANDISE), FIRST_CLEAR_REWARDS)


def test_weapon_material_offers_use_valid_progression_materials_and_unlocks():
    offered = {
        spec.item_id
        for spec in VENDOR_MERCHANDISE
        if spec.category == "smith_material"
    }
    assert offered == {material.item_id for material in MATERIAL_SPECS}
