"""Persistent per-Drifter source state for a signature weapon."""

from app.content.weapon_progression_spec import WeaponProgressionSpec


class SignatureWeaponState:
    def __init__(self, weapon_id, progression):
        if not isinstance(weapon_id, str) or not weapon_id:
            raise ValueError("weapon_id must be a non-empty string")
        if not isinstance(progression, WeaponProgressionSpec):
            raise TypeError("progression must be a WeaponProgressionSpec")
        self._weapon_id = weapon_id
        self._slot_ids = tuple(slot.slot_id for slot in progression.slots)
        self._components = {
            slot.slot_id: slot.starting_component_id
            for slot in progression.slots
        }
        self._slot_progress = {slot_id: 0 for slot_id in self._slot_ids}
        self._learned_technique_ids = []

    @property
    def weapon_id(self):
        return self._weapon_id

    @property
    def slot_progress(self):
        return dict(self._slot_progress)

    @property
    def components(self):
        return dict(self._components)

    @property
    def learned_technique_ids(self):
        return tuple(self._learned_technique_ids)

    def set_slot_progress(self, slot_id, value):
        if slot_id not in self._slot_progress:
            raise ValueError(f"unknown signature weapon slot: {slot_id}")
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("slot progress must be an integer")
        if value < 0 or value > 100:
            raise ValueError("slot progress must be between 0 and 100")
        self._slot_progress[slot_id] = value
        return value

    def install_component(self, slot_id, component_id):
        if slot_id not in self._components:
            raise ValueError(f"unknown signature weapon slot: {slot_id}")
        if not isinstance(component_id, str) or not component_id:
            raise ValueError("component_id must be a non-empty string")
        self._components[slot_id] = component_id
        return component_id

    def snapshot(self):
        return {
            "weapon_id": self.weapon_id,
            "components": self.components,
            "slot_progress": self.slot_progress,
            "learned_technique_ids": list(self.learned_technique_ids),
        }

    @classmethod
    def from_snapshot(cls, snapshot, progression):
        if not isinstance(snapshot, dict):
            raise TypeError("signature weapon snapshot must be a mapping")
        expected_keys = {
            "weapon_id",
            "components",
            "slot_progress",
            "learned_technique_ids",
        }
        if set(snapshot) != expected_keys:
            raise ValueError("signature weapon snapshot has invalid fields")
        state = cls(snapshot["weapon_id"], progression)
        components = snapshot["components"]
        if not isinstance(components, dict) or set(components) != set(state._slot_ids):
            raise ValueError("signature weapon snapshot has invalid components")
        for slot_id, component_id in components.items():
            state.install_component(slot_id, component_id)
        progress = snapshot["slot_progress"]
        if not isinstance(progress, dict) or set(progress) != set(state._slot_ids):
            raise ValueError("signature weapon snapshot has invalid slots")
        for slot_id, value in progress.items():
            state.set_slot_progress(slot_id, value)
        techniques = snapshot["learned_technique_ids"]
        if not isinstance(techniques, list):
            raise TypeError("learned technique IDs must be a list")
        if not all(isinstance(technique_id, str) for technique_id in techniques):
            raise TypeError("learned technique IDs must be strings")
        if len(set(techniques)) != len(techniques):
            raise ValueError("learned technique IDs must be unique")
        state._learned_technique_ids = list(techniques)
        return state


__all__ = ("SignatureWeaponState",)
