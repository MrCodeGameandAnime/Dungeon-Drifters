import copy
from dataclasses import replace

import pytest

from app.game.alchemist import AlchemistService, AlchemistStatus
from app.combat.passive_effect import PassiveEffectKind
from app.items.armor_modifier import ArmorModifierInstance
from app.items.equipment import EquipmentInstance
from app.persistence.ports import SaveLoadResult
from app.persistence.save_document import build_save_document, reconstruct_game_state
from app.persistence.save_port_contract import SaveLoadStatus
from tests.game_test_support import completed_hub_game


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


def _armor(*, secured=True, rarity="uncommon", modifiers=None):
    return EquipmentInstance.create(
        instance_id="00000000-0000-4000-8000-000000000501",
        definition_id="field_chest",
        source_id="floor_two_reward_01",
        secured=secured,
        stat_bonuses={"constitution": 2, "spirit": 1},
        rarity=rarity,
        modifier_slots={"I": "bastion_grade_i"} if modifiers is None else modifiers,
    )


def _game_with_armor(*, secured=True, rarity="uncommon", modifiers=None):
    game = completed_hub_game()
    game.party_state.add_equipment_instance(
        _armor(secured=secured, rarity=rarity, modifiers=modifiers)
    )
    game.party_state.add_shared_gold(500)
    game.party_state.add_shared_items(
        {"grade_i_cores": 4, "grade_ii_cores": 4, "grade_i_metal": 4}
    )
    return game


def test_sale_confirmation_destroys_modified_armor_for_authored_gold_only():
    game = _game_with_armor()
    service = AlchemistService(save_port=MemorySavePort())
    item_id = "00000000-0000-4000-8000-000000000501"
    quote = service.preview_sale(game, instance_id=item_id)
    before_gold = game.party_state.shared_gold
    before_materials = game.party_state.shared_items
    before = copy.deepcopy(game.snapshot())

    required = service.sell(game, instance_id=item_id)
    assert required.status is AlchemistStatus.CONFIRMATION_REQUIRED
    assert game.snapshot() == before

    sold = service.sell(game, instance_id=item_id, confirmation=quote)

    assert sold.status is AlchemistStatus.SOLD
    assert sold.game_state.party_state.shared_gold == before_gold + quote.gold_award
    assert sold.game_state.party_state.shared_items == before_materials
    assert sold.game_state.party_state.equipment_instances == ()
    assert quote.destroyed_modifiers == ("bastion_grade_i",)
    assert quote.destroys_equipment is True
    assert sold.game_state.party_state.modifier_instances == ()
    restored = reconstruct_game_state(build_save_document(sold.game_state))
    assert restored.party_state.equipment_instances == ()
    assert restored.party_state.shared_gold == before_gold + quote.gold_award


def test_dismantle_confirmation_returns_salvage_but_no_gold_or_modifiers():
    game = _game_with_armor()
    service = AlchemistService(save_port=MemorySavePort())
    item_id = "00000000-0000-4000-8000-000000000501"
    quote = service.preview_dismantle(game, instance_id=item_id)
    before_gold = game.party_state.shared_gold
    before_materials = game.party_state.shared_items

    result = service.dismantle(game, instance_id=item_id, confirmation=quote)

    assert result.status is AlchemistStatus.DISMANTLED
    assert result.game_state.party_state.shared_gold == before_gold
    for material_id, amount in quote.material_yields:
        assert result.game_state.party_state.shared_items[material_id] == (
            before_materials.get(material_id, 0) + amount
        )
    assert result.game_state.party_state.modifier_instances == ()
    assert quote.destroyed_modifiers == ("bastion_grade_i",)
    restored = reconstruct_game_state(build_save_document(result.game_state))
    assert restored.party_state.equipment_instances == ()
    assert restored.party_state.shared_gold == before_gold
    assert restored.party_state.shared_items == result.game_state.party_state.shared_items


def test_extraction_destroys_donor_and_persists_its_modifier():
    game = _game_with_armor()
    save_port = MemorySavePort()
    service = AlchemistService(save_port=save_port)
    item_id = "00000000-0000-4000-8000-000000000501"
    quote = service.preview_extraction(game, instance_id=item_id)
    assert quote.destroys_equipment is True
    assert quote.extracted_modifiers == ("bastion_grade_i",)
    before_gold = game.party_state.shared_gold
    before_materials = game.party_state.shared_items

    result = service.extract(game, instance_id=item_id, confirmation=quote)

    assert result.status is AlchemistStatus.EXTRACTED
    assert result.game_state.party_state.shared_gold == before_gold - quote.gold_cost
    for material_id, quantity in quote.material_costs:
        assert result.game_state.party_state.shared_items[material_id] == (
            before_materials[material_id] - quantity
        )
    assert result.game_state.party_state.equipment_instances == ()
    modifiers = result.game_state.party_state.modifier_instances
    assert len(modifiers) == 1
    assert modifiers[0].definition_id == "bastion_grade_i"
    assert modifiers[0].source_id == (
        "alchemist_extract_00000000000040008000000000000501_i"
    )
    restored = reconstruct_game_state(build_save_document(save_port.saved_states[0]))
    assert restored.party_state.modifier_instances[0].snapshot() == modifiers[0].snapshot()


def test_affix_consumes_the_exact_modifier_and_replacement_confirms_permanent_loss():
    game = _game_with_armor()
    incoming = ArmorModifierInstance.create(
        instance_id="00000000-0000-4000-8000-000000000502",
        definition_id="vanguard_grade_i",
        source_id="alchemist_test_01",
        secured=True,
    )
    game.party_state.add_modifier_instance(incoming)
    save_port = MemorySavePort()
    service = AlchemistService(save_port=save_port)
    item_id = "00000000-0000-4000-8000-000000000501"

    quote = service.preview_affix(
        game,
        instance_id=item_id,
        modifier_instance_id=incoming.instance_id,
    )
    assert quote.displaced_modifiers == ("bastion_grade_i",)
    assert quote.destroys_equipment is False
    required = service.affix(
        game,
        instance_id=item_id,
        modifier_instance_id=incoming.instance_id,
    )
    assert required.status is AlchemistStatus.CONFIRMATION_REQUIRED
    assert required.game_state is game

    result = service.affix(
        game,
        instance_id=item_id,
        modifier_instance_id=incoming.instance_id,
        confirmation=quote,
    )

    assert result.status is AlchemistStatus.REPLACED
    armor = result.game_state.party_state.equipment_instance(item_id)
    assert armor.modifier_slots == {"I": "vanguard_grade_i"}
    assert result.game_state.party_state.modifier_instances == ()
    assert result.game_state.party_state.shared_gold == (
        game.party_state.shared_gold - quote.gold_cost
    )
    for material_id, quantity in quote.material_costs:
        assert result.game_state.party_state.shared_items[material_id] == (
            game.party_state.shared_items[material_id] - quantity
        )
    assert game.party_state.equipment_instance(item_id).modifier_slots == {
        "I": "bastion_grade_i"
    }
    restored = reconstruct_game_state(build_save_document(save_port.saved_states[0]))
    assert restored.party_state.equipment_instance(item_id).modifier_slots == {
        "I": "vanguard_grade_i"
    }
    assert restored.party_state.modifier_instances == ()


@pytest.mark.parametrize("operation", ("sell", "dismantle", "extract"))
def test_disposal_rejects_unsecured_or_equipped_armor_without_mutation(operation):
    game = _game_with_armor(secured=False)
    service = AlchemistService(save_port=MemorySavePort())
    item_id = "00000000-0000-4000-8000-000000000501"
    before = copy.deepcopy(game.snapshot())

    result = getattr(service, operation)(game, instance_id=item_id)

    assert result.status is AlchemistStatus.NOT_AVAILABLE
    assert game.snapshot() == before


@pytest.mark.parametrize("operation", ("sell", "dismantle", "extract"))
def test_disposal_rejects_equipped_armor_without_mutation(operation):
    game = _game_with_armor()
    item_id = "00000000-0000-4000-8000-000000000501"
    refs = game.player_state.equipped_equipment_ids
    refs["chest"] = item_id
    game.player_state._set_equipped_equipment_ids(refs)
    game._bind_equipment_state()
    service = AlchemistService(save_port=MemorySavePort())
    before = copy.deepcopy(game.snapshot())

    result = getattr(service, operation)(game, instance_id=item_id)

    assert result.status is AlchemistStatus.NOT_AVAILABLE
    assert game.snapshot() == before


@pytest.mark.parametrize("operation", ("sell", "dismantle", "extract"))
def test_disposal_rejects_unknown_instance_without_mutation(operation):
    game = _game_with_armor()
    service = AlchemistService(save_port=MemorySavePort())
    before = copy.deepcopy(game.snapshot())

    result = getattr(service, operation)(
        game, instance_id="00000000-0000-4000-8000-000000009999"
    )

    assert result.status is AlchemistStatus.INVALID_INSTANCE
    assert game.snapshot() == before


def test_failed_extraction_save_does_not_destroy_armor_or_spend_resources():
    game = _game_with_armor()
    before = copy.deepcopy(game.snapshot())
    service = AlchemistService(save_port=MemorySavePort(SaveLoadStatus.INVALID))
    quote = service.preview_extraction(
        game, instance_id="00000000-0000-4000-8000-000000000501"
    )

    result = service.extract(
        game,
        instance_id="00000000-0000-4000-8000-000000000501",
        confirmation=quote,
    )

    assert result.status is AlchemistStatus.SAVE_FAILED
    assert result.game_state is game
    assert game.snapshot() == before


def test_affix_allows_equipped_armor_and_rebinds_its_combat_effect():
    game = _game_with_armor()
    item_id = "00000000-0000-4000-8000-000000000501"
    modifier = ArmorModifierInstance.create(
        instance_id="00000000-0000-4000-8000-000000000503",
        definition_id="vanguard_grade_i",
        source_id="alchemist_equipped_test",
        secured=True,
    )
    game.party_state.add_modifier_instance(modifier)
    refs = game.player_state.equipped_equipment_ids
    refs["chest"] = item_id
    game.player_state._set_equipped_equipment_ids(refs)
    game._bind_equipment_state()
    service = AlchemistService(save_port=MemorySavePort())

    quote = service.preview_affix(
        game, instance_id=item_id, modifier_instance_id=modifier.instance_id
    )
    result = service.affix(
        game,
        instance_id=item_id,
        modifier_instance_id=modifier.instance_id,
        confirmation=quote,
    )

    assert quote.can_apply
    assert result.status is AlchemistStatus.REPLACED
    assert len(result.game_state.player_state.combat_passive_effects) == 1
    assert result.game_state.player_state.combat_passive_effects[0].kind is (
        PassiveEffectKind.DAMAGE_OUTPUT
    )


@pytest.mark.parametrize("operation", ("sell", "dismantle", "extract"))
def test_disposal_preview_requires_confirmation_and_cancellation_is_inert(operation):
    game = _game_with_armor()
    service = AlchemistService(save_port=MemorySavePort())
    item_id = "00000000-0000-4000-8000-000000000501"
    preview_name = {
        "sell": "preview_sale",
        "dismantle": "preview_dismantle",
        "extract": "preview_extraction",
    }[operation]
    preview = getattr(service, preview_name)(game, instance_id=item_id)
    before = copy.deepcopy(game.snapshot())

    required = getattr(service, operation)(game, instance_id=item_id)
    cancelled = service.cancel(game, preview)

    assert required.status is AlchemistStatus.CONFIRMATION_REQUIRED
    assert required.game_state is game
    assert cancelled.status is AlchemistStatus.CANCELLED
    assert game.snapshot() == before


@pytest.mark.parametrize("operation", ("sell", "dismantle", "extract", "affix"))
def test_failed_alchemist_save_rolls_back_entire_transaction(operation):
    game = _game_with_armor()
    service = AlchemistService(save_port=MemorySavePort(SaveLoadStatus.INVALID))
    item_id = "00000000-0000-4000-8000-000000000501"
    kwargs = {"instance_id": item_id}
    if operation == "affix":
        modifier = ArmorModifierInstance.create(
            instance_id="00000000-0000-4000-8000-000000000504",
            definition_id="vanguard_grade_i",
            source_id="alchemist_failure_test",
            secured=True,
        )
        game.party_state.add_modifier_instance(modifier)
        kwargs["modifier_instance_id"] = modifier.instance_id
        preview = service.preview_affix(game, **kwargs)
    elif operation == "extract":
        preview = service.preview_extraction(game, **kwargs)
    else:
        preview_name = "preview_sale" if operation == "sell" else "preview_dismantle"
        preview = getattr(service, preview_name)(game, **kwargs)
    before = copy.deepcopy(game.snapshot())

    result = getattr(service, operation)(game, **kwargs, confirmation=preview)

    assert result.status is AlchemistStatus.SAVE_FAILED
    assert result.game_state is game
    assert game.snapshot() == before


def test_fixed_accessories_have_no_default_alchemist_disposal_or_extraction():
    game = _game_with_armor()
    accessory = EquipmentInstance.create(
        instance_id="00000000-0000-4000-8000-000000000505",
        definition_id="iron_ring",
        source_id="alchemist_accessory_test",
        secured=True,
        stat_bonuses={"intuition": 1},
    )
    game.party_state.add_equipment_instance(accessory)
    service = AlchemistService(save_port=MemorySavePort())

    assert service.preview_sale(game, instance_id=accessory.instance_id).status is (
        AlchemistStatus.NOT_AUTHORIZED
    )
    assert service.preview_dismantle(game, instance_id=accessory.instance_id).status is (
        AlchemistStatus.NOT_AUTHORIZED
    )
    assert service.preview_extraction(game, instance_id=accessory.instance_id).status is (
        AlchemistStatus.NOT_ARMOR
    )


def test_affix_confirmation_is_rejected_when_the_quote_becomes_stale():
    game = _game_with_armor()
    item_id = "00000000-0000-4000-8000-000000000501"
    modifier = ArmorModifierInstance.create(
        instance_id="00000000-0000-4000-8000-000000000506",
        definition_id="vanguard_grade_i",
        source_id="alchemist_stale_test",
        secured=True,
    )
    game.party_state.add_modifier_instance(modifier)
    service = AlchemistService(save_port=MemorySavePort())
    quote = service.preview_affix(
        game, instance_id=item_id, modifier_instance_id=modifier.instance_id
    )
    armor = game.party_state.equipment_instance(item_id)
    game.party_state.replace_equipment_instance(
        armor.with_modifier(grade="I", modifier_id=None)
    )
    current = service.preview_affix(
        game, instance_id=item_id, modifier_instance_id=modifier.instance_id
    )
    before = copy.deepcopy(game.snapshot())

    result = service.affix(
        game,
        instance_id=item_id,
        modifier_instance_id=modifier.instance_id,
        confirmation=quote,
    )

    assert current.displaced_modifiers == ()
    assert result.status is AlchemistStatus.STALE_CONFIRMATION
    assert game.snapshot() == before


def test_sale_confirmation_is_rejected_when_attached_modifiers_change():
    game = _game_with_armor()
    service = AlchemistService(save_port=MemorySavePort())
    item_id = "00000000-0000-4000-8000-000000000501"
    quote = service.preview_sale(game, instance_id=item_id)
    armor = game.party_state.equipment_instance(item_id)
    game.party_state.replace_equipment_instance(
        armor.with_modifier(grade="I", modifier_id=None)
    )
    before = copy.deepcopy(game.snapshot())

    result = service.sell(game, instance_id=item_id, confirmation=quote)

    assert result.status is AlchemistStatus.STALE_CONFIRMATION
    assert game.snapshot() == before


@pytest.mark.parametrize(
    ("operation", "resource"),
    (("extract", "gold"), ("extract", "material"), ("affix", "gold"), ("affix", "material")),
)
def test_affix_and_extraction_reject_insufficient_authored_resources(operation, resource):
    game = _game_with_armor()
    if resource == "gold":
        assert game.party_state.spend_shared_gold(game.party_state.shared_gold)
    else:
        assert game.party_state.spend_shared_items(
            {"grade_i_cores": game.party_state.shared_items["grade_i_cores"]}
        )
    service = AlchemistService(save_port=MemorySavePort())
    item_id = "00000000-0000-4000-8000-000000000501"
    kwargs = {"instance_id": item_id}
    if operation == "extract":
        preview = service.preview_extraction(game, **kwargs)
    else:
        modifier = ArmorModifierInstance.create(
            instance_id="00000000-0000-4000-8000-000000000507",
            definition_id="vanguard_grade_i",
            source_id="alchemist_insufficient_test",
            secured=True,
        )
        game.party_state.add_modifier_instance(modifier)
        kwargs["modifier_instance_id"] = modifier.instance_id
        preview = service.preview_affix(game, **kwargs)
    before = copy.deepcopy(game.snapshot())

    result = getattr(service, operation)(game, **kwargs, confirmation=preview)

    assert preview.status is AlchemistStatus.INSUFFICIENT_RESOURCES
    assert result.status is AlchemistStatus.INSUFFICIENT_RESOURCES
    assert game.snapshot() == before


@pytest.mark.parametrize("operation", ("sell", "dismantle", "extract", "affix"))
def test_repeated_submission_cannot_duplicate_alchemist_outputs(operation):
    game = _game_with_armor()
    service = AlchemistService(save_port=MemorySavePort())
    item_id = "00000000-0000-4000-8000-000000000501"
    kwargs = {"instance_id": item_id}
    if operation == "extract":
        preview = service.preview_extraction(game, **kwargs)
    elif operation == "affix":
        modifier = ArmorModifierInstance.create(
            instance_id="00000000-0000-4000-8000-000000000509",
            definition_id="vanguard_grade_i",
            source_id="alchemist_repeat_test",
            secured=True,
        )
        game.party_state.add_modifier_instance(modifier)
        kwargs["modifier_instance_id"] = modifier.instance_id
        preview = service.preview_affix(game, **kwargs)
    else:
        preview_name = "preview_sale" if operation == "sell" else "preview_dismantle"
        preview = getattr(service, preview_name)(game, **kwargs)
    first = getattr(service, operation)(game, **kwargs, confirmation=preview)
    repeated = getattr(service, operation)(
        first.game_state, **kwargs, confirmation=preview
    )

    expected_repeat_status = (
        AlchemistStatus.INVALID_MODIFIER
        if operation == "affix"
        else AlchemistStatus.INVALID_INSTANCE
    )
    assert first.status in {
        AlchemistStatus.SOLD,
        AlchemistStatus.DISMANTLED,
        AlchemistStatus.EXTRACTED,
        AlchemistStatus.REPLACED,
    }
    assert repeated.status is expected_repeat_status
    assert repeated.game_state.snapshot() == first.game_state.snapshot()


def test_affix_rejects_incompatible_authored_modifier(monkeypatch):
    import app.game.alchemist as alchemist_module

    game = _game_with_armor()
    modifier = ArmorModifierInstance.create(
        instance_id="00000000-0000-4000-8000-000000000508",
        definition_id="vanguard_grade_i",
        source_id="alchemist_compatibility_test",
        secured=True,
    )
    game.party_state.add_modifier_instance(modifier)
    original = alchemist_module.get_armor_modifier
    monkeypatch.setattr(
        alchemist_module,
        "get_armor_modifier",
        lambda modifier_id: replace(
            original(modifier_id), compatible_slots=("boots",)
        ),
    )
    service = AlchemistService(save_port=MemorySavePort())

    preview = service.preview_affix(
        game,
        instance_id="00000000-0000-4000-8000-000000000501",
        modifier_instance_id=modifier.instance_id,
    )

    assert preview.status is AlchemistStatus.INCOMPATIBLE
    assert not preview.can_apply


def test_extraction_preserves_modifier_payout_and_adds_first_discovery_xp():
    game = _game_with_armor(
        rarity="rare",
        modifiers={"I": "bastion_grade_i", "III": "force_grade_iii"},
    )
    game.party_state.add_shared_items({"grade_iii_cores": 2})
    service = AlchemistService(save_port=MemorySavePort())
    item_id = "00000000-0000-4000-8000-000000000501"
    preview = service.preview_extraction(game, instance_id=item_id)

    result = service.extract(game, instance_id=item_id, confirmation=preview)

    economy = result.game_state.party_state.hub_economy_state
    assert result.status is AlchemistStatus.EXTRACTED
    assert {item.definition_id for item in result.game_state.party_state.modifier_instances} == {
        "bastion_grade_i",
        "force_grade_iii",
    }
    assert economy.known_affix_ids == ("bastion_grade_i", "force_grade_iii")
    assert economy.enchanting_experience == 50
    assert economy.enchanting_level == 3


def test_repeated_affix_discovery_keeps_instance_payout_without_duplicate_bonus():
    game = _game_with_armor(
        rarity="rare",
        modifiers={"III": "force_grade_iii"},
    )
    game.party_state.add_shared_items({"grade_iii_cores": 2})
    second = EquipmentInstance.create(
        instance_id="00000000-0000-4000-8000-000000000510",
        definition_id="field_chest",
        source_id="floor_two_reward_02",
        secured=True,
        stat_bonuses={"constitution": 2},
        rarity="rare",
        modifier_slots={"III": "force_grade_iii"},
    )
    game.party_state.add_equipment_instance(second)
    service = AlchemistService(save_port=MemorySavePort())
    first_id = "00000000-0000-4000-8000-000000000501"

    first_preview = service.preview_extraction(game, instance_id=first_id)
    first = service.extract(game, instance_id=first_id, confirmation=first_preview)
    second_preview = service.preview_extraction(
        first.game_state,
        instance_id=second.instance_id,
    )
    repeated = service.extract(
        first.game_state,
        instance_id=second.instance_id,
        confirmation=second_preview,
    )

    assert first.game_state.party_state.hub_economy_state.enchanting_experience == 45
    assert repeated.game_state.party_state.hub_economy_state.enchanting_experience == 75
    assert repeated.game_state.party_state.hub_economy_state.known_affix_ids == (
        "force_grade_iii",
    )
    assert len(repeated.game_state.party_state.modifier_instances) == 2


def test_stored_affix_application_awards_grade_xp_without_learning_recipe():
    game = _game_with_armor(modifiers={})
    modifier = ArmorModifierInstance.create(
        instance_id="00000000-0000-4000-8000-000000000511",
        definition_id="bastion_grade_i",
        source_id="stored_affix_xp_test",
        secured=True,
    )
    game.party_state.add_modifier_instance(modifier)
    service = AlchemistService(save_port=MemorySavePort())
    item_id = "00000000-0000-4000-8000-000000000501"
    preview = service.preview_affix(
        game,
        instance_id=item_id,
        modifier_instance_id=modifier.instance_id,
    )

    result = service.affix(
        game,
        instance_id=item_id,
        modifier_instance_id=modifier.instance_id,
        confirmation=preview,
    )

    economy = result.game_state.party_state.hub_economy_state
    assert result.status is AlchemistStatus.AFFIXED
    assert economy.enchanting_experience == 10
    assert economy.known_affix_ids == ()


def test_learned_affix_application_uses_mastery_cost_and_durable_transaction():
    game = _game_with_armor(modifiers={})
    game.party_state.add_shared_items({"grade_i_magic_crystal": 2})
    game.party_state.hub_economy_state.learn_affix("bastion_grade_i")
    service = AlchemistService(save_port=MemorySavePort())
    item_id = "00000000-0000-4000-8000-000000000501"
    preview = service.preview_learned_affix(
        game,
        instance_id=item_id,
        modifier_id="bastion_grade_i",
    )

    required = service.apply_learned_affix(
        game,
        instance_id=item_id,
        modifier_id="bastion_grade_i",
    )
    result = service.apply_learned_affix(
        game,
        instance_id=item_id,
        modifier_id="bastion_grade_i",
        confirmation=preview,
    )

    assert required.status is AlchemistStatus.CONFIRMATION_REQUIRED
    assert preview.gold_cost == 8
    assert preview.material_costs == (("grade_i_magic_crystal", 2),)
    assert result.status is AlchemistStatus.LEARNED_AFFIX_APPLIED
    assert result.game_state.party_state.equipment_instance(item_id).modifier_slots == {
        "I": "bastion_grade_i",
    }
    assert result.game_state.party_state.shared_items.get("grade_i_magic_crystal", 0) == 0
    assert result.game_state.party_state.hub_economy_state.enchanting_experience == 10
    assert result.game_state.party_state.hub_economy_state.known_affix_ids == (
        "bastion_grade_i",
    )


def test_learned_affix_replacement_requires_confirming_permanent_loss():
    game = _game_with_armor(modifiers={"I": "bastion_grade_i"})
    game.party_state.add_shared_items({"grade_i_magic_crystal": 2})
    game.party_state.hub_economy_state.learn_affix("vanguard_grade_i")
    service = AlchemistService(save_port=MemorySavePort())
    item_id = "00000000-0000-4000-8000-000000000501"
    preview = service.preview_learned_affix(
        game,
        instance_id=item_id,
        modifier_id="vanguard_grade_i",
    )

    result = service.apply_learned_affix(
        game,
        instance_id=item_id,
        modifier_id="vanguard_grade_i",
        confirmation=preview,
    )

    assert preview.displaced_modifiers == ("bastion_grade_i",)
    assert preview.destroyed_modifiers == ("bastion_grade_i",)
    assert result.status is AlchemistStatus.REPLACED
    assert result.game_state.party_state.equipment_instance(item_id).modifier_slots == {
        "I": "vanguard_grade_i",
    }


def test_learned_affix_save_failure_rolls_back_crystals_equipment_and_xp():
    game = _game_with_armor(modifiers={})
    game.party_state.add_shared_items({"grade_i_magic_crystal": 2})
    game.party_state.hub_economy_state.learn_affix("bastion_grade_i")
    service = AlchemistService(save_port=MemorySavePort(SaveLoadStatus.INVALID))
    item_id = "00000000-0000-4000-8000-000000000501"
    preview = service.preview_learned_affix(
        game,
        instance_id=item_id,
        modifier_id="bastion_grade_i",
    )
    before = copy.deepcopy(game.snapshot())

    result = service.apply_learned_affix(
        game,
        instance_id=item_id,
        modifier_id="bastion_grade_i",
        confirmation=preview,
    )

    assert result.status is AlchemistStatus.SAVE_FAILED
    assert result.game_state is game
    assert game.snapshot() == before


@pytest.mark.parametrize(
    ("experience", "crystals", "gold"),
    ((0, 2, 24), (600, 2, 21), (1225, 2, 18), (1850, 1, 15), (2475, 1, 12)),
)
def test_learned_grade_three_costs_follow_each_enchanting_level_band(
    experience,
    crystals,
    gold,
):
    game = _game_with_armor(rarity="rare", modifiers={})
    game.party_state.hub_economy_state.add_enchanting_experience(experience)
    game.party_state.hub_economy_state.learn_affix("force_grade_iii")
    game.party_state.add_shared_items({"grade_iii_magic_crystal": crystals})

    preview = AlchemistService.preview_learned_affix(
        game,
        instance_id="00000000-0000-4000-8000-000000000501",
        modifier_id="force_grade_iii",
    )

    assert preview.can_apply
    assert preview.gold_cost == gold
    assert preview.material_costs == (("grade_iii_magic_crystal", crystals),)


def test_grade_five_learned_affix_is_unavailable_without_grade_five_content():
    game = _game_with_armor(rarity="legendary", modifiers={})
    game.party_state.hub_economy_state.learn_affix("resolve_grade_v")

    preview = AlchemistService.preview_learned_affix(
        game,
        instance_id="00000000-0000-4000-8000-000000000501",
        modifier_id="resolve_grade_v",
    )

    assert preview.status is AlchemistStatus.NOT_AVAILABLE
    assert not preview.can_apply


def test_learned_affix_preview_goes_stale_after_another_hub_transaction():
    game = _game_with_armor(modifiers={})
    game.party_state.add_shared_items({"grade_i_magic_crystal": 2})
    game.party_state.hub_economy_state.learn_affix("bastion_grade_i")
    service = AlchemistService(save_port=MemorySavePort())
    item_id = "00000000-0000-4000-8000-000000000501"
    preview = service.preview_learned_affix(
        game,
        instance_id=item_id,
        modifier_id="bastion_grade_i",
    )
    game.party_state.hub_economy_state.advance_transaction(0)
    before = copy.deepcopy(game.snapshot())

    result = service.apply_learned_affix(
        game,
        instance_id=item_id,
        modifier_id="bastion_grade_i",
        confirmation=preview,
    )

    assert result.status is AlchemistStatus.STALE_CONFIRMATION
    assert game.snapshot() == before
