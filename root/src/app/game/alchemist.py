"""Confirmed, atomic Hub operations for armor and its modifiers."""

from dataclasses import dataclass
from enum import StrEnum

from app.content.armor_spec import get_armor_modifier, get_armor_rarity
from app.content.equipment_spec import get_equipment_template
from app.game.game_state import GameState
from app.game.party_state import DungeonPhase
from app.items.armor_modifier import ArmorModifierInstance
from app.persistence.save_port_contract import (
    SaveLoadStatus,
    SavePortError,
    is_save_port,
)


class AlchemistStatus(StrEnum):
    READY = "ready"
    CONFIRMATION_REQUIRED = "confirmation_required"
    CANCELLED = "cancelled"
    SOLD = "sold"
    DISMANTLED = "dismantled"
    EXTRACTED = "extracted"
    AFFIXED = "affixed"
    REPLACED = "replaced"
    INVALID_INSTANCE = "invalid_instance"
    INVALID_MODIFIER = "invalid_modifier"
    NOT_ARMOR = "not_armor"
    NOT_AVAILABLE = "not_available"
    NOT_AUTHORIZED = "not_authorized"
    NO_MODIFIERS = "no_modifiers"
    INCOMPATIBLE = "incompatible"
    GRADE_LOCKED = "grade_locked"
    SAME_MODIFIER = "same_modifier"
    INSUFFICIENT_RESOURCES = "insufficient_resources"
    STALE_CONFIRMATION = "stale_confirmation"
    SAVE_FAILED = "save_failed"


@dataclass(frozen=True)
class AlchemistPreview:
    action: str
    status: AlchemistStatus
    equipment_instance_id: str | None
    modifier_instance_id: str | None
    gold_cost: int
    gold_award: int
    material_costs: tuple[tuple[str, int], ...]
    material_yields: tuple[tuple[str, int], ...]
    incoming_modifier: str | None
    displaced_modifiers: tuple[str, ...]
    destroyed_modifiers: tuple[str, ...]
    destroys_equipment: bool
    extracted_modifiers: tuple[str, ...]
    can_apply: bool


@dataclass(frozen=True)
class AlchemistResult:
    status: AlchemistStatus
    game_state: GameState
    preview: AlchemistPreview | None = None


class AlchemistService:
    def __init__(self, *, save_port):
        if not is_save_port(save_port):
            raise TypeError("save_port must satisfy SavePort")
        self._save_port = save_port

    @staticmethod
    def preview_sale(game_state, *, instance_id):
        item, status = AlchemistService._disposable(game_state, instance_id)
        if status is not None:
            return _blocked("sell", status, instance_id)
        spec = get_equipment_template(item.definition_id)
        if spec.sale_value_gold is None:
            return _blocked("sell", AlchemistStatus.NOT_AUTHORIZED, instance_id)
        return _preview(
            "sell", item, gold_award=spec.sale_value_gold,
            destroyed_modifiers=tuple(item.modifier_slots.values()),
            destroys_equipment=True,
        )

    @staticmethod
    def preview_dismantle(game_state, *, instance_id):
        item, status = AlchemistService._disposable(game_state, instance_id)
        if status is not None:
            return _blocked("dismantle", status, instance_id)
        spec = get_equipment_template(item.definition_id)
        if not spec.dismantle_yields:
            return _blocked("dismantle", AlchemistStatus.NOT_AUTHORIZED, instance_id)
        return _preview(
            "dismantle", item, material_yields=spec.dismantle_yields,
            destroyed_modifiers=tuple(item.modifier_slots.values()),
            destroys_equipment=True,
        )

    @staticmethod
    def preview_extraction(game_state, *, instance_id):
        item, status = AlchemistService._disposable(game_state, instance_id)
        if status is not None:
            return _blocked("extract", status, instance_id)
        if item.category != "armor":
            return _blocked("extract", AlchemistStatus.NOT_ARMOR, instance_id)
        modifiers = tuple(item.modifier_slots.values())
        if not modifiers:
            return _blocked("extract", AlchemistStatus.NO_MODIFIERS, instance_id)
        gold, materials = _aggregate_modifier_costs(modifiers, "extraction")
        return _priced_preview(
            game_state,
            "extract",
            item,
            gold_cost=gold,
            material_costs=materials,
            destroyed_modifiers=(),
            incoming_modifier=None,
            modifier_instance_id=None,
            destroys_equipment=True,
            extracted_modifiers=modifiers,
        )

    @staticmethod
    def preview_affix(game_state, *, instance_id, modifier_instance_id):
        item, status = AlchemistService._manageable_armor(game_state, instance_id)
        if status is not None:
            return _blocked("affix", status, instance_id, modifier_instance_id)
        try:
            modifier = game_state.party_state.modifier_instance(modifier_instance_id)
        except ValueError:
            return _blocked(
                "affix", AlchemistStatus.INVALID_MODIFIER,
                instance_id, modifier_instance_id,
            )
        if not modifier.secured:
            return _blocked("affix", AlchemistStatus.NOT_AVAILABLE, instance_id, modifier_instance_id)
        definition = get_armor_modifier(modifier.definition_id)
        if item.slot_id not in definition.compatible_slots:
            return _blocked("affix", AlchemistStatus.INCOMPATIBLE, instance_id, modifier_instance_id)
        if definition.grade not in get_armor_rarity(item.rarity).modifier_grades:
            return _blocked("affix", AlchemistStatus.GRADE_LOCKED, instance_id, modifier_instance_id)
        displaced = item.modifier_slots.get(definition.grade)
        if displaced == definition.modifier_id:
            return _blocked("affix", AlchemistStatus.SAME_MODIFIER, instance_id, modifier_instance_id)
        return _priced_preview(
            game_state,
            "affix",
            item,
            gold_cost=definition.affix_gold_cost,
            material_costs=definition.affix_material_costs,
            incoming_modifier=definition.modifier_id,
            displaced_modifiers=() if displaced is None else (displaced,),
            destroyed_modifiers=() if displaced is None else (displaced,),
            modifier_instance_id=modifier_instance_id,
        )

    def sell(self, game_state, *, instance_id, confirmation=None):
        return self._run_confirmed(
            game_state, instance_id, confirmation, self.preview_sale,
            self._apply_sale, AlchemistStatus.SOLD,
        )

    def dismantle(self, game_state, *, instance_id, confirmation=None):
        return self._run_confirmed(
            game_state, instance_id, confirmation, self.preview_dismantle,
            self._apply_dismantle, AlchemistStatus.DISMANTLED,
        )

    def extract(self, game_state, *, instance_id, confirmation=None):
        return self._run_confirmed(
            game_state, instance_id, confirmation, self.preview_extraction,
            self._apply_extraction, AlchemistStatus.EXTRACTED,
        )

    def affix(
        self,
        game_state,
        *,
        instance_id,
        modifier_instance_id,
        confirmation=None,
    ):
        preview = self.preview_affix(
            game_state,
            instance_id=instance_id,
            modifier_instance_id=modifier_instance_id,
        )
        if not preview.can_apply:
            return AlchemistResult(preview.status, game_state, preview)
        if confirmation is None:
            return AlchemistResult(
                AlchemistStatus.CONFIRMATION_REQUIRED, game_state, preview
            )
        if confirmation != preview:
            return AlchemistResult(
                AlchemistStatus.STALE_CONFIRMATION, game_state, preview
            )
        candidate = game_state.clone()
        party = candidate.party_state
        if not _spend(party, preview.gold_cost, preview.material_costs):
            return AlchemistResult(AlchemistStatus.INSUFFICIENT_RESOURCES, game_state, preview)
        incoming = party.remove_modifier_instance(modifier_instance_id)
        armor = party.equipment_instance(instance_id)
        updated = armor.with_modifier(
            grade=incoming.grade,
            modifier_id=incoming.definition_id,
        )
        party.replace_equipment_instance(updated)
        candidate._bind_equipment_state()
        return self._commit(candidate, game_state, AlchemistStatus.REPLACED if preview.displaced_modifiers else AlchemistStatus.AFFIXED, preview)

    @staticmethod
    def cancel(game_state, preview):
        return AlchemistResult(AlchemistStatus.CANCELLED, game_state, preview)

    def _run_confirmed(self, game_state, instance_id, confirmation, preview_fn, apply_fn, success):
        preview = preview_fn(game_state, instance_id=instance_id)
        if not preview.can_apply:
            return AlchemistResult(preview.status, game_state, preview)
        if confirmation is None:
            return AlchemistResult(
                AlchemistStatus.CONFIRMATION_REQUIRED, game_state, preview
            )
        if confirmation != preview:
            return AlchemistResult(
                AlchemistStatus.STALE_CONFIRMATION, game_state, preview
            )
        candidate = game_state.clone()
        party = candidate.party_state
        if not _spend(party, preview.gold_cost, preview.material_costs):
            return AlchemistResult(AlchemistStatus.INSUFFICIENT_RESOURCES, game_state, preview)
        apply_fn(candidate, preview)
        return self._commit(candidate, game_state, success, preview)

    @staticmethod
    def _apply_sale(candidate, preview):
        candidate.party_state.remove_equipment_instance(preview.equipment_instance_id)
        candidate.party_state.add_shared_gold(preview.gold_award)

    @staticmethod
    def _apply_dismantle(candidate, preview):
        candidate.party_state.remove_equipment_instance(preview.equipment_instance_id)
        candidate.party_state.add_shared_items(dict(preview.material_yields))

    @staticmethod
    def _apply_extraction(candidate, preview):
        party = candidate.party_state
        armor = party.remove_equipment_instance(preview.equipment_instance_id)
        for grade, definition_id in armor.modifier_slots.items():
            party.add_modifier_instance(
                ArmorModifierInstance.create(
                    definition_id=definition_id,
                    source_id=f"alchemist_extract_{armor.instance_id.replace('-', '')}_{grade.lower()}",
                    secured=True,
                )
            )

    @staticmethod
    def _manageable_armor(game_state, instance_id):
        if not isinstance(game_state, GameState):
            raise TypeError("game_state must be a GameState")
        if game_state.party_state.phase is not DungeonPhase.HUB:
            return None, AlchemistStatus.NOT_AVAILABLE
        try:
            item = game_state.party_state.equipment_instance(instance_id)
        except ValueError:
            return None, AlchemistStatus.INVALID_INSTANCE
        if not item.secured:
            return None, AlchemistStatus.NOT_AVAILABLE
        if item.category != "armor":
            return None, AlchemistStatus.NOT_ARMOR
        return item, None

    @staticmethod
    def _disposable(game_state, instance_id):
        if not isinstance(game_state, GameState):
            raise TypeError("game_state must be a GameState")
        if game_state.party_state.phase is not DungeonPhase.HUB:
            return None, AlchemistStatus.NOT_AVAILABLE
        try:
            item = game_state.party_state.equipment_instance(instance_id)
        except ValueError:
            return None, AlchemistStatus.INVALID_INSTANCE
        if not item.secured:
            return None, AlchemistStatus.NOT_AVAILABLE
        if any(
            reference == item.instance_id
            for member in game_state.recruited_members
            for reference in member.equipped_equipment_ids.values()
        ):
            return None, AlchemistStatus.NOT_AVAILABLE
        return item, None

    def _commit(self, candidate, original, success, preview):
        try:
            result = self._save_port.save(candidate)
        except (OSError, SavePortError, TypeError, ValueError):
            result = None
        if result is None or result.status is not SaveLoadStatus.SAVED:
            return AlchemistResult(AlchemistStatus.SAVE_FAILED, original, preview)
        return AlchemistResult(success, candidate, preview)


def _preview(
    action,
    item,
    *,
    gold_cost=0,
    gold_award=0,
    material_costs=(),
    material_yields=(),
    incoming_modifier=None,
    displaced_modifiers=(),
    destroyed_modifiers=(),
    destroys_equipment=False,
    extracted_modifiers=(),
    modifier_instance_id=None,
):
    return AlchemistPreview(
        action,
        AlchemistStatus.READY,
        item.instance_id,
        modifier_instance_id,
        gold_cost,
        gold_award,
        tuple(sorted(material_costs)),
        tuple(sorted(material_yields)),
        incoming_modifier,
        tuple(displaced_modifiers),
        tuple(destroyed_modifiers),
        destroys_equipment,
        tuple(extracted_modifiers),
        True,
    )


def _blocked(action, status, instance_id, modifier_instance_id=None):
    return AlchemistPreview(
        action, status, instance_id, modifier_instance_id, 0, 0,
        (), (), None, (), (), False, (), False,
    )


def _priced_preview(
    game_state,
    action,
    item,
    *,
    gold_cost,
    material_costs,
    incoming_modifier=None,
    displaced_modifiers=(),
    destroyed_modifiers=(),
    modifier_instance_id=None,
    destroys_equipment=False,
    extracted_modifiers=(),
):
    can_pay = _has_resources(
        game_state.party_state, gold_cost, material_costs
    )
    preview = _preview(
        action,
        item,
        gold_cost=gold_cost,
        material_costs=material_costs,
        incoming_modifier=incoming_modifier,
        displaced_modifiers=displaced_modifiers,
        destroyed_modifiers=destroyed_modifiers,
        destroys_equipment=destroys_equipment,
        extracted_modifiers=extracted_modifiers,
        modifier_instance_id=modifier_instance_id,
    )
    if can_pay:
        return preview
    return AlchemistPreview(
        preview.action,
        AlchemistStatus.INSUFFICIENT_RESOURCES,
        preview.equipment_instance_id,
        preview.modifier_instance_id,
        preview.gold_cost,
        preview.gold_award,
        preview.material_costs,
        preview.material_yields,
        preview.incoming_modifier,
        preview.displaced_modifiers,
        preview.destroyed_modifiers,
        preview.destroys_equipment,
        preview.extracted_modifiers,
        False,
    )


def _aggregate_modifier_costs(modifier_ids, operation):
    gold = 0
    materials = {}
    for modifier_id in modifier_ids:
        modifier = get_armor_modifier(modifier_id)
        gold += modifier.extraction_gold_cost
        for material_id, quantity in modifier.extraction_material_costs:
            materials[material_id] = materials.get(material_id, 0) + quantity
    return gold, tuple(sorted(materials.items()))


def _has_resources(party, gold, materials):
    return party.shared_gold >= gold and all(
        party.shared_items.get(material_id, 0) >= quantity
        for material_id, quantity in materials
    )


def _spend(party, gold, materials):
    if not _has_resources(party, gold, materials):
        return False
    return party.spend_shared_gold(gold) and party.spend_shared_items(dict(materials))


__all__ = [
    "AlchemistPreview",
    "AlchemistResult",
    "AlchemistService",
    "AlchemistStatus",
]
