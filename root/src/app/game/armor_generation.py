"""Materialize one authored armor reward using an injected random source."""

from app.content.armor_spec import (
    MODIFIER_DEFINITIONS,
    get_armor_rarity,
    get_floor_rarity_policy,
)
from app.content.equipment_spec import get_equipment_template
from app.items.equipment import EquipmentInstance


class ArmorGenerationService:
    def __init__(self, *, rng):
        if not callable(getattr(rng, "randrange", None)):
            raise TypeError("rng must provide randrange(stop)")
        self._rng = rng

    def _randrange(self, stop):
        value = self._rng.randrange(stop)
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("rng returned a non-integer armor result")
        if not 0 <= value < stop:
            raise ValueError("rng returned an out-of-range armor result")
        return value

    def generate(
        self,
        *,
        template_id,
        floor,
        source_id,
        instance_id,
        secured=False,
    ):
        template = get_equipment_template(template_id)
        if not template.is_armor:
            raise ValueError("procedural generation requires an armor template")
        policy = get_floor_rarity_policy(floor)
        rarity_id = self._weighted_rarity(policy.rarity_weights_bps)
        rarity = get_armor_rarity(rarity_id)
        stats = {
            stat: minimum + self._randrange(maximum - minimum + 1)
            for stat, minimum, maximum in template.stat_ranges
        }
        modifier_slots = {}
        for grade in rarity.modifier_grades:
            if self._randrange(100) >= policy.modifier_chance_percent:
                continue
            candidates = tuple(
                modifier
                for modifier in MODIFIER_DEFINITIONS
                if modifier.grade == grade
                and template.slot_id in modifier.compatible_slots
            )
            if not candidates:
                continue
            modifier_slots[grade] = candidates[
                self._randrange(len(candidates))
            ].modifier_id
        return EquipmentInstance.create(
            instance_id=instance_id,
            definition_id=template.definition_id,
            source_id=source_id,
            secured=secured,
            stat_bonuses=stats,
            rarity=rarity_id,
            modifier_slots=modifier_slots,
        )

    def _weighted_rarity(self, weights):
        roll = self._randrange(sum(weight for _, weight in weights))
        for rarity_id, weight in weights:
            if roll < weight:
                return rarity_id
            roll -= weight
        raise ValueError("rarity policy did not resolve a weighted outcome")


__all__ = ["ArmorGenerationService"]
