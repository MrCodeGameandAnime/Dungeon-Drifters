"""Persistent loose armor-modifier instances owned by the party."""

from uuid import UUID, uuid4

from app.content.armor_spec import get_armor_modifier


class ArmorModifierInstance:
    __slots__ = ("_instance_id", "_definition_id", "_source_id", "_secured")

    def __init__(self, *, instance_id, definition_id, source_id, secured):
        _validate_uuid(instance_id)
        get_armor_modifier(definition_id)
        _validate_source_id(source_id)
        if not isinstance(secured, bool):
            raise TypeError("modifier secured state must be a boolean")
        self._instance_id = instance_id
        self._definition_id = definition_id
        self._source_id = source_id
        self._secured = secured

    @classmethod
    def create(cls, *, instance_id=None, definition_id, source_id, secured):
        return cls(
            instance_id=str(uuid4()) if instance_id is None else instance_id,
            definition_id=definition_id,
            source_id=source_id,
            secured=secured,
        )

    @classmethod
    def from_snapshot(cls, snapshot):
        if not isinstance(snapshot, dict) or set(snapshot) != {
            "instance_id", "definition_id", "source_id", "secured"
        }:
            raise ValueError("armor modifier snapshot has an invalid shape")
        return cls(**snapshot)

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
    def grade(self):
        return get_armor_modifier(self.definition_id).grade

    @property
    def compatible_slots(self):
        return get_armor_modifier(self.definition_id).compatible_slots

    def snapshot(self):
        return {
            "instance_id": self.instance_id,
            "definition_id": self.definition_id,
            "source_id": self.source_id,
            "secured": self.secured,
        }


def _validate_uuid(value):
    if not isinstance(value, str):
        raise TypeError("modifier instance ID must be a UUID string")
    try:
        parsed = UUID(value)
    except (TypeError, ValueError, AttributeError) as error:
        raise ValueError("modifier instance ID must be a canonical UUID") from error
    if str(parsed) != value:
        raise ValueError("modifier instance ID must be a canonical UUID")


def _validate_source_id(value):
    if not isinstance(value, str) or not value or len(value) > 96:
        raise ValueError("modifier source ID must be a non-empty bounded string")
    if any(not (char.islower() or char.isdigit() or char in "_-") for char in value):
        raise ValueError("modifier source ID must be a lowercase authored ID")


__all__ = ("ArmorModifierInstance",)
