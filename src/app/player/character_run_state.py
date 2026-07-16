"""Character-owned mutable state that persists for one run."""

from enum import StrEnum


class RunItemId(StrEnum):
    EMBER_SHARD = "ember_shard"
    DEEP_COAL = "deep_coal"


class PreparedPayloadId(StrEnum):
    CINDERWRIT = "cinderwrit_payload"


class InventoryActionId(StrEnum):
    PREPARE_CINDERWRIT = "prepare_cinderwrit"


class CharacterRunState:
    def __init__(self, *, inventory=None, prepared_payloads=None):
        self._inventory = self._validated_quantities(inventory or {})
        self._prepared_payloads = self._validated_payloads(prepared_payloads or {})

    def item_quantity(self, item_id):
        item_id = self._validate_item_id(item_id)
        return self._inventory.get(item_id, 0)

    def supports_payload(self, payload_id):
        payload_id = self._validate_payload_id(payload_id)
        return payload_id in self._prepared_payloads

    def payload_prepared(self, payload_id):
        payload_id = self._validate_payload_id(payload_id)
        return self._prepared_payloads.get(payload_id, False)

    def snapshot(self):
        return {
            "inventory": {
                item_id.value: self._inventory[item_id]
                for item_id in sorted(self._inventory, key=lambda value: value.value)
            },
            "prepared_payloads": {
                payload_id.value: self._prepared_payloads[payload_id]
                for payload_id in sorted(
                    self._prepared_payloads,
                    key=lambda value: value.value,
                )
            },
        }

    @classmethod
    def _validated_quantities(cls, quantities):
        if not isinstance(quantities, dict):
            raise TypeError("inventory must be a dictionary")
        return {
            cls._validate_item_id(item_id): cls._validate_quantity(quantity)
            for item_id, quantity in quantities.items()
        }

    @classmethod
    def _validated_payloads(cls, payloads):
        if not isinstance(payloads, dict):
            raise TypeError("prepared_payloads must be a dictionary")
        validated = {}
        for payload_id, prepared in payloads.items():
            if not isinstance(prepared, bool):
                raise TypeError("prepared payload state must be a boolean")
            validated[cls._validate_payload_id(payload_id)] = prepared
        return validated

    @staticmethod
    def _validate_item_id(item_id):
        try:
            return RunItemId(item_id)
        except (TypeError, ValueError) as error:
            raise ValueError(f"invalid run item identifier: {item_id!r}") from error

    @staticmethod
    def _validate_payload_id(payload_id):
        try:
            return PreparedPayloadId(payload_id)
        except (TypeError, ValueError) as error:
            raise ValueError(f"invalid prepared payload identifier: {payload_id!r}") from error

    @staticmethod
    def _validate_quantity(quantity):
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise TypeError("inventory quantity must be an integer")
        if quantity < 0:
            raise ValueError("inventory quantity must not be negative")
        return quantity
