"""Persistent unique armor and fixed-accessory instances."""

from uuid import UUID, uuid4

from app.content.armor_spec import MODIFIER_GRADES, get_armor_modifier, get_armor_rarity
from app.content.equipment_spec import (
    MAX_ARMOR_UPGRADE_RANK,
    get_equipment_template,
)


class EquipmentInstance:
    __slots__ = (
        "_instance_id",
        "_definition_id",
        "_source_id",
        "_secured",
        "_stat_bonus_pairs",
        "_rarity",
        "_upgrade_rank",
        "_modifier_pairs",
    )

    def __init__(
        self,
        *,
        instance_id,
        definition_id,
        source_id,
        secured,
        stat_bonuses,
        rarity=None,
        upgrade_rank=0,
        modifier_slots=None,
    ):
        spec = get_equipment_template(definition_id)
        _validate_instance_id(instance_id)
        _validate_source_id(source_id)
        if not isinstance(secured, bool):
            raise TypeError("equipment secured state must be a boolean")
        if not isinstance(stat_bonuses, dict):
            raise TypeError("equipment stat bonuses must be a mapping")
        ranges = {
            name: (minimum, maximum)
            for name, minimum, maximum in spec.stat_ranges
        }
        if any(name not in ranges for name in stat_bonuses):
            raise ValueError("equipment has a stat outside its authored template")
        normalized = []
        for name, value in stat_bonuses.items():
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError("equipment stat bonuses must be integers")
            minimum, maximum = ranges[name]
            if not minimum <= value <= maximum:
                raise ValueError("equipment stat bonus is outside its authored range")
            normalized.append((name, value))

        self._instance_id = instance_id
        self._definition_id = definition_id
        self._source_id = source_id
        self._secured = secured
        self._stat_bonus_pairs = tuple(sorted(normalized))
        if spec.is_armor:
            rarity = "common" if rarity is None else rarity
            get_armor_rarity(rarity)
        elif rarity is not None:
            raise ValueError("static accessories cannot have armor rarity")
        if isinstance(upgrade_rank, bool) or not isinstance(upgrade_rank, int):
            raise TypeError("equipment upgrade rank must be an integer")
        if not 0 <= upgrade_rank <= MAX_ARMOR_UPGRADE_RANK:
            raise ValueError(
                "equipment upgrade rank exceeds the authored armor maximum"
            )
        if spec.is_static_accessory and upgrade_rank != 0:
            raise ValueError("static accessories cannot have armor upgrades")
        if modifier_slots is None:
            modifier_slots = {}
        if not isinstance(modifier_slots, dict):
            raise TypeError("equipment modifier slots must be a mapping")
        modifier_pairs = []
        if modifier_slots and not spec.is_armor:
            raise ValueError("static accessories cannot have modifier slots")
        rarity_capacity = (
            0 if rarity is None else get_armor_rarity(rarity).modifier_capacity
        )
        for grade in MODIFIER_GRADES:
            modifier_id = modifier_slots.get(grade)
            if modifier_id is None:
                continue
            modifier = get_armor_modifier(modifier_id)
            if modifier.grade != grade:
                raise ValueError("modifier grade does not match its armor slot")
            if spec.slot_id not in modifier.compatible_slots:
                raise ValueError("modifier is incompatible with armor slot")
            if MODIFIER_GRADES.index(grade) >= rarity_capacity:
                raise ValueError("modifier exceeds armor rarity capacity")
            modifier_pairs.append((grade, modifier_id))
        if set(modifier_slots) - set(MODIFIER_GRADES):
            raise ValueError("equipment contains an unknown modifier grade slot")
        self._rarity = rarity
        self._upgrade_rank = upgrade_rank
        self._modifier_pairs = tuple(modifier_pairs)

    @classmethod
    def create(
        cls,
        *,
        definition_id,
        source_id,
        secured,
        stat_bonuses,
        instance_id=None,
        rarity=None,
        upgrade_rank=0,
        modifier_slots=None,
    ):
        return cls(
            instance_id=str(uuid4()) if instance_id is None else instance_id,
            definition_id=definition_id,
            source_id=source_id,
            secured=secured,
            stat_bonuses=stat_bonuses,
            rarity=rarity,
            upgrade_rank=upgrade_rank,
            modifier_slots={} if modifier_slots is None else modifier_slots,
        )

    @property
    def instance_id(self):
        return self._instance_id

    @property
    def definition_id(self):
        return self._definition_id

    @property
    def source_id(self):
        return self._source_id

    @property
    def secured(self):
        return self._secured

    @property
    def stat_bonuses(self):
        bonuses = self.base_stat_bonuses
        template = get_equipment_template(self.definition_id)
        for stat, value in template.upgrade_stat_bonuses:
            bonuses[stat] = bonuses.get(stat, 0) + value * self.upgrade_rank
        return bonuses

    @property
    def base_stat_bonuses(self):
        return dict(self._stat_bonus_pairs)

    @property
    def rarity(self):
        return self._rarity

    @property
    def upgrade_rank(self):
        return self._upgrade_rank

    @property
    def modifier_slots(self):
        return dict(self._modifier_pairs)

    @property
    def combat_effects(self):
        effects = []
        for _, modifier_id in self._modifier_pairs:
            effects.extend(get_armor_modifier(modifier_id).effects)
        return tuple(effects)

    @property
    def slot_id(self):
        return get_equipment_template(self.definition_id).slot_id

    @property
    def category(self):
        return get_equipment_template(self.definition_id).category

    def snapshot(self):
        return {
            "instance_id": self.instance_id,
            "definition_id": self.definition_id,
            "source_id": self.source_id,
            "secured": self.secured,
            "stat_bonuses": self.base_stat_bonuses,
            "rarity": self.rarity,
            "upgrade_rank": self.upgrade_rank,
            "modifier_slots": self.modifier_slots,
        }

    @classmethod
    def from_snapshot(cls, snapshot):
        if not isinstance(snapshot, dict):
            raise TypeError("equipment instance snapshot must be a mapping")
        expected = {
            "instance_id",
            "definition_id",
            "source_id",
            "secured",
            "stat_bonuses",
            "rarity",
            "upgrade_rank",
            "modifier_slots",
        }
        if set(snapshot) != expected:
            raise ValueError("equipment instance snapshot has an invalid shape")
        return cls(**snapshot)

    def with_progression(self, *, rarity=None, upgrade_rank=None):
        return EquipmentInstance(
            instance_id=self.instance_id,
            definition_id=self.definition_id,
            source_id=self.source_id,
            secured=self.secured,
            stat_bonuses=self.base_stat_bonuses,
            rarity=self.rarity if rarity is None else rarity,
            upgrade_rank=(
                self.upgrade_rank if upgrade_rank is None else upgrade_rank
            ),
            modifier_slots=self.modifier_slots,
        )

    def with_security(self, *, secured):
        return EquipmentInstance(
            instance_id=self.instance_id,
            definition_id=self.definition_id,
            source_id=self.source_id,
            secured=secured,
            stat_bonuses=self.base_stat_bonuses,
            rarity=self.rarity,
            upgrade_rank=self.upgrade_rank,
            modifier_slots=self.modifier_slots,
        )

    def with_modifier(self, *, grade, modifier_id):
        slots = self.modifier_slots
        if modifier_id is None:
            slots.pop(grade, None)
        else:
            slots[grade] = modifier_id
        return EquipmentInstance(
            instance_id=self.instance_id,
            definition_id=self.definition_id,
            source_id=self.source_id,
            secured=self.secured,
            stat_bonuses=self.base_stat_bonuses,
            rarity=self.rarity,
            upgrade_rank=self.upgrade_rank,
            modifier_slots=slots,
        )


def _validate_instance_id(value):
    if not isinstance(value, str):
        raise TypeError("equipment instance ID must be a UUID string")
    try:
        parsed = UUID(value)
    except (TypeError, ValueError, AttributeError) as error:
        raise ValueError("equipment instance ID must be a canonical UUID") from error
    if str(parsed) != value:
        raise ValueError("equipment instance ID must be a canonical UUID")


def _validate_source_id(value):
    if not isinstance(value, str) or not value or len(value) > 96:
        raise ValueError("equipment source ID must be a non-empty bounded string")
    if any(not (character.islower() or character.isdigit() or character in "_-") for character in value):
        raise ValueError("equipment source ID must be a lowercase authored ID")


__all__ = ("EquipmentInstance",)
