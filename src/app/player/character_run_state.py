"""Character-owned mutable state that persists for one run."""

from enum import StrEnum


class RunItemId(StrEnum):
    EMBER_SHARD = "ember_shard"
    DEEP_COAL = "deep_coal"
    NIGHT_BERRY = "night_berry"


class PreparedPayloadId(StrEnum):
    INFUSED_BARB = "infused_barb"
    CINDERWRIT = "infused_barb"


class InfusionKind(StrEnum):
    FIRE = "fire"
    POISON = "poison"


class InventoryActionId(StrEnum):
    PREPARE_CINDERWRIT = "prepare_cinderwrit"


CINDERWRIT_PREPARATION_COST = {
    RunItemId.EMBER_SHARD: 1,
    RunItemId.DEEP_COAL: 1,
}


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
        return self._prepared_payloads.get(payload_id) is not None

    def prepared_infusion(self):
        if PreparedPayloadId.INFUSED_BARB not in self._prepared_payloads:
            return None
        return self._prepared_payloads[PreparedPayloadId.INFUSED_BARB]

    def has_items(self, requirements):
        requirements = self._validated_requirements(requirements)
        return all(
            self._inventory.get(item_id, 0) >= quantity
            for item_id, quantity in requirements.items()
        )

    def prepare_payload(self, payload_id, requirements):
        payload_id = self._validate_payload_id(payload_id)
        if payload_id != PreparedPayloadId.INFUSED_BARB:
            raise ValueError("prepared payload is not supported")
        self.prepare_infusion(InfusionKind.FIRE, requirements)

    def prepare_infusion(self, infusion_kind, requirements):
        infusion_kind = self._validate_infusion_kind(infusion_kind)
        requirements = self._validated_requirements(requirements)
        payload_id = PreparedPayloadId.INFUSED_BARB
        if payload_id not in self._prepared_payloads:
            raise ValueError("prepared payload is not supported")
        if self._prepared_payloads[payload_id] is not None:
            raise ValueError("prepared payload is already active")
        if not self.has_items(requirements):
            raise ValueError("required inventory items are unavailable")

        for item_id, quantity in requirements.items():
            self._inventory[item_id] -= quantity
        self._prepared_payloads[payload_id] = infusion_kind

    def consume_payload(self, payload_id):
        payload_id = self._validate_payload_id(payload_id)
        if payload_id != PreparedPayloadId.INFUSED_BARB:
            raise ValueError("prepared payload is not supported")
        self.consume_infusion()

    def consume_infusion(self):
        payload_id = PreparedPayloadId.INFUSED_BARB
        if payload_id not in self._prepared_payloads:
            raise ValueError("prepared payload is not supported")
        infusion_kind = self._prepared_payloads[payload_id]
        if infusion_kind is None:
            raise ValueError("prepared payload is not active")

        self._prepared_payloads[payload_id] = None
        return infusion_kind

    def snapshot(self):
        return {
            "inventory": {
                item_id.value: self._inventory[item_id]
                for item_id in sorted(self._inventory, key=lambda value: value.value)
            },
            "prepared_payloads": {
                payload_id.value: (
                    None
                    if self._prepared_payloads[payload_id] is None
                    else self._prepared_payloads[payload_id].value
                )
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
        for payload_id, infusion_kind in payloads.items():
            payload_id = cls._validate_payload_id(payload_id)
            if infusion_kind is not None:
                infusion_kind = cls._validate_infusion_kind(infusion_kind)
            validated[payload_id] = infusion_kind
        return validated

    @classmethod
    def _validated_requirements(cls, requirements):
        validated = cls._validated_quantities(requirements)
        if any(quantity == 0 for quantity in validated.values()):
            raise ValueError("inventory requirements must be positive")
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
    def _validate_infusion_kind(infusion_kind):
        try:
            return InfusionKind(infusion_kind)
        except (TypeError, ValueError) as error:
            raise ValueError(f"invalid infusion kind: {infusion_kind!r}") from error

    @staticmethod
    def _validate_quantity(quantity):
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise TypeError("inventory quantity must be an integer")
        if quantity < 0:
            raise ValueError("inventory quantity must not be negative")
        return quantity
