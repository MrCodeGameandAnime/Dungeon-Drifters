"""Persistent player state for one playthrough."""

from app.player.character import Character
from app.player.inventory import Inventory


class PlayerState:
    EQUIPMENT_SLOTS = (
        "weapon",
        "off_hand",
        "head",
        "body",
        "accessory",
    )

    def __init__(self, character: Character, gold: int = 0):
        if not isinstance(character, Character):
            raise TypeError("character must be a Character instance")

        self._character = character
        self._gold = self._validate_gold_amount(gold)
        self._inventory = Inventory()
        self._equipment = {
            slot: None
            for slot in self.EQUIPMENT_SLOTS
        }

    @property
    def character(self):
        return self._character

    @property
    def inventory(self):
        return self._inventory

    @property
    def gold(self):
        return self._gold

    @property
    def equipment(self):
        return dict(self._equipment)

    @property
    def health(self):
        return self.character.health

    @property
    def mana_resource(self):
        return self.character.mana_resource

    @property
    def level_state(self):
        return self.character.level_state

    @property
    def exp_state(self):
        return self.character.exp_state

    @property
    def stats(self):
        return self.character.stats

    @property
    def combat_moves(self):
        return self.character.combat_moves

    @property
    def class_mechanic(self):
        return self.character.class_mechanic

    def add_gold(self, amount):
        self._gold += self._validate_gold_amount(amount)
        return self.gold

    def can_afford(self, amount):
        amount = self._validate_gold_amount(amount)
        return self.gold >= amount

    def spend_gold(self, amount):
        amount = self._validate_gold_amount(amount)
        if not self.can_afford(amount):
            return False

        self._gold -= amount
        return True

    def equip(self, slot, item):
        self._validate_equipment_slot(slot)
        if item is None:
            raise ValueError("item must not be None")
        if not self.inventory.contains(item):
            raise ValueError("item must be in inventory before it can be equipped")

        removed = self.inventory.remove_item(item)
        if not removed:
            raise ValueError("item must be in inventory before it can be equipped")

        previous_item = self._equipment[slot]
        self._equipment[slot] = item

        if previous_item is not None:
            self.inventory.add_item(previous_item)

        return previous_item

    def unequip(self, slot):
        self._validate_equipment_slot(slot)
        equipped_item = self._equipment[slot]
        if equipped_item is None:
            return None

        self._equipment[slot] = None
        self.inventory.add_item(equipped_item)
        return equipped_item

    def get_equipped(self, slot):
        self._validate_equipment_slot(slot)
        return self._equipment[slot]

    @staticmethod
    def _validate_gold_amount(amount):
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError("gold amount must be an integer")
        if amount < 0:
            raise ValueError("gold amount must not be negative")

        return amount

    def _validate_equipment_slot(self, slot):
        if slot not in self.EQUIPMENT_SLOTS:
            raise ValueError(f"invalid equipment slot: {slot}")
