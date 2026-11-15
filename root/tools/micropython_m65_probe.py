"""Bounded M6.5 vendor and profession qualification after the M6 probe."""

import gc


_M65_STAGE_NAMES = (
    "M65_ALCHEMY_CRAFT_AND_RECONSTRUCTION",
    "M65_ENCHANTING_DISCOVERY_AND_APPLICATION",
    "M65_PROBE_TEARDOWN",
)
_M65_DONOR_ARMOR_ID = "00000000-0000-4000-8000-000000000709"
_M65_TARGET_ARMOR_ID = "00000000-0000-4000-8000-000000000708"


def _alchemy_craft_and_reconstruction(state):
    from app.game.alchemy import AlchemyService, AlchemyStatus

    game = state["route_game"]
    party = game.party_state
    economy = party.hub_economy_state
    if economy.current_hub_visit_id is None:
        raise AssertionError("M6.5 Alchemy probe did not begin at the Hub")
    party.add_shared_items({"magic_reagent": 1, "aether_dust": 1})
    experience_before = economy.alchemy_experience
    sequence = economy.transaction_sequence
    service = AlchemyService(save_port=state["route_battle_factory"])
    preview = service.preview_recipe(
        game,
        recipe_id="mana_potion",
        expected_transaction_sequence=sequence,
    )
    result = service.craft(
        game,
        recipe_id="mana_potion",
        expected_transaction_sequence=sequence,
    )
    if result.status is not AlchemyStatus.CRAFTED:
        raise AssertionError("M6.5 Mana Potion recipe did not craft")
    game = result.game_state
    if game.party_state.shared_items.get("mana_potion", 0) < 1:
        raise AssertionError("M6.5 Alchemy did not persist its output")
    if game.party_state.shared_items.get("magic_reagent", 0) != 0:
        raise AssertionError("M6.5 Alchemy did not consume its reagent")
    if game.party_state.shared_items.get("aether_dust", 0) != 0:
        raise AssertionError("M6.5 Alchemy did not consume its Aether Dust")
    if (
        game.party_state.hub_economy_state.alchemy_experience
        != experience_before + preview.experience_award
    ):
        raise AssertionError("M6.5 Alchemy progression was not awarded once")
    if game.party_state.hub_economy_state.transaction_sequence != sequence + 1:
        raise AssertionError("M6.5 Alchemy transaction was not sequenced once")
    restored = game.clone()
    if restored.snapshot() != game.snapshot():
        raise AssertionError("M6.5 Alchemy state changed after reconstruction")
    state["route_game"] = restored


def _enchanting_discovery_and_application(state):
    from app.game.alchemist import AlchemistService, AlchemistStatus
    from app.items.equipment import EquipmentInstance

    game = state["route_game"]
    party = game.party_state
    economy = party.hub_economy_state
    modifier_id = "vanguard_grade_i"
    armor = EquipmentInstance.create(
        instance_id=_M65_DONOR_ARMOR_ID,
        definition_id="field_helm",
        source_id="m65_micropython_extraction_source",
        secured=True,
        stat_bonuses={"constitution": 1},
        rarity="common",
        modifier_slots={"I": modifier_id},
    )
    party.add_equipment_instance(armor)
    party.add_shared_gold(100)
    party.add_shared_items({"grade_i_cores": 1})
    service = AlchemistService(save_port=state["route_battle_factory"])
    experience_before = economy.enchanting_experience
    preview = service.preview_extraction(
        game,
        instance_id=_M65_DONOR_ARMOR_ID,
    )
    if not preview.can_apply:
        raise AssertionError("M6.5 Enchanter could not extract the source affix")
    extracted = service.extract(
        game,
        instance_id=_M65_DONOR_ARMOR_ID,
        confirmation=preview,
    )
    if extracted.status is not AlchemistStatus.EXTRACTED:
        raise AssertionError("M6.5 Enchanter extraction did not commit")
    game = extracted.game_state
    party = game.party_state
    economy = party.hub_economy_state
    if any(
        item.instance_id == _M65_DONOR_ARMOR_ID
        for item in party.equipment_instances
    ):
        raise AssertionError("M6.5 extraction did not destroy donor armor")
    if not economy.knows_affix(modifier_id):
        raise AssertionError("M6.5 extraction did not record permanent knowledge")
    if not any(
        item.definition_id == modifier_id for item in party.modifier_instances
    ):
        raise AssertionError("M6.5 extraction lost the stored modifier instance")
    if economy.enchanting_experience <= experience_before:
        raise AssertionError("M6.5 extraction did not advance Enchanting")

    target = EquipmentInstance.create(
        instance_id=_M65_TARGET_ARMOR_ID,
        definition_id="field_helm",
        source_id="m65_micropython_learned_affix_target",
        secured=True,
        stat_bonuses={"constitution": 1},
        rarity="common",
        modifier_slots={},
    )
    party.add_equipment_instance(target)
    party.add_shared_gold(20)
    party.add_shared_items({"grade_i_magic_crystal": 2})
    preview = service.preview_learned_affix(
        game,
        instance_id=_M65_TARGET_ARMOR_ID,
        modifier_id=modifier_id,
    )
    if not preview.can_apply:
        raise AssertionError("M6.5 learned affix was not applicable")
    applied = service.apply_learned_affix(
        game,
        instance_id=_M65_TARGET_ARMOR_ID,
        modifier_id=modifier_id,
        confirmation=preview,
    )
    if applied.status is not AlchemistStatus.LEARNED_AFFIX_APPLIED:
        raise AssertionError("M6.5 learned affix did not commit")
    game = applied.game_state
    if (
        game.party_state.equipment_instance(_M65_TARGET_ARMOR_ID).modifier_slots
        != {"I": modifier_id}
    ):
        raise AssertionError("M6.5 learned affix installed the wrong modifier")
    if not game.party_state.hub_economy_state.knows_affix(modifier_id):
        raise AssertionError("M6.5 learned affix knowledge was not retained")
    if not any(
        item.definition_id == modifier_id
        for item in game.party_state.modifier_instances
    ):
        raise AssertionError("M6.5 learned application consumed the stored copy")
    restored = game.clone()
    if restored.snapshot() != game.snapshot():
        raise AssertionError("M6.5 Enchanting state changed after reconstruction")
    state["route_game"] = restored


def _teardown(state):
    gc.collect()


def run(state, run_stage):
    run_stage(
        _M65_STAGE_NAMES[0],
        lambda: _alchemy_craft_and_reconstruction(state),
    )
    run_stage(
        _M65_STAGE_NAMES[1],
        lambda: _enchanting_discovery_and_application(state),
    )
    run_stage(_M65_STAGE_NAMES[2], lambda: _teardown(state))


__all__ = ("run",)
