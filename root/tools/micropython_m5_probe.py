"""Bounded M5 equipment qualification after the cleared Floor II route."""

import gc


_M5_STAGE_NAMES = (
    "M5_ARMOR_GENERATION",
    "M5_ARMOR_UPGRADE",
    "M5_MODIFIER_REPLACEMENT",
    "M5_EQUIPMENT_RECONSTRUCTION",
    "M5_STATIC_ACCESSORY_BOUNDARY",
    "M5_PROBE_TEARDOWN",
)
_ARMOR_INSTANCE_ID = "00000000-0000-4000-8000-000000000701"
_MODIFIER_INSTANCE_ID = "00000000-0000-4000-8000-000000000702"
_ACCESSORY_INSTANCE_ID = "00000000-0000-4000-8000-000000000703"


class _ZeroRng:
    def randrange(self, stop):
        if stop < 1:
            raise ValueError("probe RNG received an invalid range")
        return 0


def _generate_armor(state):
    from app.game.armor_generation import ArmorGenerationService

    game = state["route_game"]
    armor = ArmorGenerationService(rng=_ZeroRng()).generate(
        template_id="field_helm",
        floor=2,
        source_id="m5_probe_floor2_armor",
        instance_id=_ARMOR_INSTANCE_ID,
        secured=True,
    )
    if armor.rarity != "common" or armor.modifier_slots != {"I": "bastion_grade_i"}:
        raise AssertionError("M5 deterministic armor generation changed")
    game.party_state.add_equipment_instance(armor)
    game.party_state.add_shared_gold(100)
    game.party_state.add_shared_items({"grade_i_metal": 1})
    state["m5_armor_instance_id"] = armor.instance_id


def _upgrade_armor(state):
    from app.game.armor_progression import (
        ArmorProgressionService,
        ArmorProgressionStatus,
    )

    game = state["route_game"]
    service = ArmorProgressionService(save_port=state["route_battle_factory"])
    result = service.upgrade_stat(
        game,
        instance_id=state["m5_armor_instance_id"],
    )
    if result.status is not ArmorProgressionStatus.UPGRADED:
        raise AssertionError("M5 armor upgrade did not commit")
    upgraded = result.game_state.party_state.equipment_instance(
        state["m5_armor_instance_id"]
    )
    if upgraded.upgrade_rank != 1 or upgraded.stat_bonuses["constitution"] < 2:
        raise AssertionError("M5 armor upgrade result was not persisted")
    state["route_game"] = result.game_state


def _replace_modifier(state):
    from app.game.alchemist import AlchemistService, AlchemistStatus
    from app.items.armor_modifier import ArmorModifierInstance

    game = state["route_game"]
    party = game.party_state
    incoming = ArmorModifierInstance.create(
        instance_id=_MODIFIER_INSTANCE_ID,
        definition_id="vanguard_grade_i",
        source_id="m5_probe_modifier",
        secured=True,
    )
    party.add_modifier_instance(incoming)
    party.add_shared_gold(3)
    party.add_shared_items({"grade_i_cores": 1})
    service = AlchemistService(save_port=state["route_battle_factory"])
    preview = service.preview_affix(
        game,
        instance_id=state["m5_armor_instance_id"],
        modifier_instance_id=_MODIFIER_INSTANCE_ID,
    )
    if not preview.can_apply or preview.displaced_modifiers != ("bastion_grade_i",):
        raise AssertionError("M5 replacement did not identify the lost modifier")
    result = service.affix(
        game,
        instance_id=state["m5_armor_instance_id"],
        modifier_instance_id=_MODIFIER_INSTANCE_ID,
        confirmation=preview,
    )
    if result.status is not AlchemistStatus.REPLACED:
        raise AssertionError("M5 confirmed modifier replacement did not commit")
    armor = result.game_state.party_state.equipment_instance(
        state["m5_armor_instance_id"]
    )
    if armor.modifier_slots != {"I": "vanguard_grade_i"}:
        raise AssertionError("M5 replacement installed the wrong modifier")
    if any(
        item.instance_id == _MODIFIER_INSTANCE_ID
        for item in result.game_state.party_state.modifier_instances
    ):
        raise AssertionError("M5 replacement did not consume its incoming modifier")
    state["route_game"] = result.game_state


def _reconstruct_equipment(state):
    from app.game.game_state import GameState
    from app.items.equipment import EquipmentInstance

    game = state["route_game"]
    restored = game.clone()
    if not isinstance(restored, GameState):
        raise AssertionError("M5 snapshot reconstruction returned the wrong state")
    if restored.snapshot() != game.snapshot():
        raise AssertionError("M5 equipment changed across snapshot reconstruction")
    armor = restored.party_state.equipment_instance(state["m5_armor_instance_id"])
    if EquipmentInstance.from_snapshot(armor.snapshot()).snapshot() != armor.snapshot():
        raise AssertionError("M5 armor instance changed on reconstruction")
    modifiers = restored.party_state.modifier_instances
    if len(modifiers) != 0:
        raise AssertionError("M5 replacement left a loose modifier instance")
    state["m5_reconstructed_game"] = restored


def _check_static_accessory_boundary(state):
    from app.content.equipment_spec import get_equipment_template
    from app.game.alchemist import AlchemistService, AlchemistStatus
    from app.game.armor_generation import ArmorGenerationService
    from app.game.armor_progression import (
        ArmorProgressionService,
        ArmorProgressionStatus,
    )
    from app.items.equipment import EquipmentInstance

    game = state["route_game"]
    ring_spec = get_equipment_template("iron_ring")
    if not ring_spec.is_static_accessory or ring_spec.is_armor:
        raise AssertionError("M5 Ring was not authored as fixed equipment")
    ring = EquipmentInstance.create(
        instance_id=_ACCESSORY_INSTANCE_ID,
        definition_id="iron_ring",
        source_id="m5_probe_static_ring",
        secured=True,
        stat_bonuses={"intuition": 1},
    )
    game.party_state.add_equipment_instance(ring)
    if ArmorProgressionService.preview_stat_upgrade(
        game,
        instance_id=_ACCESSORY_INSTANCE_ID,
    ).status is not ArmorProgressionStatus.NOT_ARMOR:
        raise AssertionError("M5 Ring incorrectly allowed armor upgrades")
    if AlchemistService.preview_extraction(
        game,
        instance_id=_ACCESSORY_INSTANCE_ID,
    ).status is not AlchemistStatus.NOT_ARMOR:
        raise AssertionError("M5 Ring incorrectly allowed modifier extraction")
    try:
        ArmorGenerationService(rng=_ZeroRng()).generate(
            template_id="iron_ring",
            floor=2,
            source_id="m5_probe_static_ring",
            instance_id=_ACCESSORY_INSTANCE_ID,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("M5 Ring incorrectly allowed procedural generation")


def _teardown(state):
    for key in ("m5_armor_instance_id", "m5_reconstructed_game"):
        state.pop(key, None)
    gc.collect()


def run(state, run_stage):
    run_stage(_M5_STAGE_NAMES[0], lambda: _generate_armor(state))
    run_stage(_M5_STAGE_NAMES[1], lambda: _upgrade_armor(state))
    run_stage(_M5_STAGE_NAMES[2], lambda: _replace_modifier(state))
    run_stage(_M5_STAGE_NAMES[3], lambda: _reconstruct_equipment(state))
    run_stage(_M5_STAGE_NAMES[4], lambda: _check_static_accessory_boundary(state))
    run_stage(_M5_STAGE_NAMES[5], lambda: _teardown(state))


__all__ = ("run",)
