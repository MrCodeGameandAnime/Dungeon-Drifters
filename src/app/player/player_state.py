"""Persistent player state for one playthrough."""

from dataclasses import dataclass

from app.items.weapon import Weapon
from app.combat.move import DamageType
from app.player import resources
from app.player import progression
from app.snapshot import to_plain_value
from app.player.character import Character
from app.player.character_run_state import (
    CharacterRunCheckpoint,
    CharacterRunState,
)
from app.player.inventory import Inventory


@dataclass(frozen=True)
class PlayerBattleCheckpoint:
    health_current: int
    mana_current: int
    super_current: int
    character_run_state: CharacterRunCheckpoint


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
        self._growth_points = 0
        self._inventory = Inventory()
        self._character_run_state = CharacterRunState(
            inventory=character.starting_run_inventory,
            prepared_payloads=character.starting_prepared_payloads,
        )
        self._super_resource = resources.Super()
        self._equipment = {
            slot: None
            for slot in self.EQUIPMENT_SLOTS
        }
        for slot, item in getattr(character, "starting_equipment", {}).items():
            self._validate_equipment_slot(slot)
            self._equipment[slot] = item

    @property
    def character(self):
        return self._character

    @property
    def inventory(self):
        return self._inventory

    @property
    def character_run_state(self):
        return self._character_run_state

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
    def super_resource(self):
        return self._super_resource

    @property
    def generates_super(self):
        return True

    @property
    def can_defend(self):
        return True

    @property
    def level_state(self):
        return self.character.level_state

    @property
    def exp_state(self):
        return self.character.exp_state

    @property
    def growth_points(self):
        return self._growth_points

    @property
    def stats(self):
        return self.character.stats

    @property
    def combat_moves(self):
        return self.character.combat_moves

    @property
    def class_mechanic(self):
        return self.character.class_mechanic

    @property
    def display_name(self):
        return self.character.display_name

    def effective_stat(self, name):
        base_value = self.stats.effective_stat(name)
        weapon = self.get_equipped("weapon")
        if isinstance(weapon, Weapon):
            return base_value + weapon.stat_bonuses.get(name, 0)

        return base_value

    def defend_reduction_percent(self, damage_type):
        if damage_type == DamageType.PHYSICAL:
            return min(70, 30 + self.effective_stat("strength"))
        if damage_type == DamageType.MAGICAL:
            return min(60, 20 + self.effective_stat("spirit"))
        if damage_type == DamageType.HYBRID:
            return min(50, 10 + self.effective_stat("dexterity"))

        return 0

    def is_alive(self):
        return self.health.is_alive()

    def gain_experience(self, amount):
        amount = self.exp_state.validate_gain_amount(amount)
        levels_gained = self.exp_state.gain(amount)
        if levels_gained:
            self._growth_points += (
                levels_gained * progression.GROWTH_POINTS_PER_LEVEL
            )
            self.character.recalculate_resource_maximums(
                increase_current=True,
            )

        return levels_gained

    def apply_encounter_reward(self, exp_reward, gold_reward):
        exp_reward = self.exp_state.validate_gain_amount(exp_reward)
        gold_reward = self._validate_gold_amount(gold_reward)

        levels_gained = self.gain_experience(exp_reward)
        self._gold += gold_reward
        return levels_gained

    def increase_permanent_stat(self, stat_name):
        current_value = self.character.permanent_stats.get_stat(stat_name)
        if self._growth_points <= 0:
            raise ValueError("no Growth Points available")
        if current_value >= self.character.permanent_stats.MAXIMUM:
            raise ValueError("stat is already at its maximum")

        new_value = self.character.permanent_stats.increase_stat(
            stat_name,
            1,
        )
        self._growth_points -= 1
        if stat_name in {"constitution", "spirit"}:
            self.character.recalculate_resource_maximums(
                increase_current=True,
            )

        return new_value

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

    def create_battle_checkpoint(self):
        return PlayerBattleCheckpoint(
            health_current=self.health.current,
            mana_current=self.mana_resource.current,
            super_current=self.super_resource.current,
            character_run_state=self.character_run_state.create_checkpoint(),
        )

    def restore_battle_checkpoint(self, checkpoint):
        if not isinstance(checkpoint, PlayerBattleCheckpoint):
            raise TypeError("checkpoint must be a PlayerBattleCheckpoint")
        self.health.current = self.health.clamp(checkpoint.health_current)
        self.mana_resource.current = self.mana_resource.clamp(
            checkpoint.mana_current
        )
        self.super_resource.current = self.super_resource._validate_current(
            checkpoint.super_current
        )
        self.character_run_state.restore_checkpoint(
            checkpoint.character_run_state
        )

    def snapshot(self):
        profile = self._snapshot_profile()
        snapshot = {
            "identity": {
                "display_name": self.character.display_name,
                "full_display_name": self.character.full_display_name,
                "archetype_name": self.character.archetype_name,
                "profile": profile,
            },
            "attributes": self.character.permanent_stats.as_dict(),
            "resources": {
                "health": {
                    "current": self.health.current,
                    "maximum": self.health.maximum,
                },
                "mana": {
                    "current": self.mana_resource.current,
                    "maximum": self.mana_resource.maximum,
                },
                "super": {
                    "current": self.super_resource.current,
                    "maximum": self.super_resource.maximum,
                },
            },
            "progression": {
                "level": self.level_state.current,
                "exp": self.exp_state.current,
                "growth_points": self.growth_points,
            },
            "gold": self.gold,
            "inventory": [
                self._snapshot_item(item, f"player.inventory[{index}]")
                for index, item in enumerate(self.inventory.items)
            ],
            "run_state": self.character_run_state.snapshot(),
            "equipment": {
                slot: self._snapshot_item(item, f"player.equipment.{slot}")
                for slot, item in self.equipment.items()
            },
            "combat": {
                "moves": [
                    self._snapshot_move(move)
                    for move in self.combat_moves
                ],
                "class_mechanic": to_plain_value(
                    self.class_mechanic,
                    "player.combat.class_mechanic",
                ),
            },
        }
        return to_plain_value(snapshot, "player")

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

    def _snapshot_profile(self):
        profile = self.character.profile
        if profile is None:
            return None

        return {
            "choice": profile.choice,
            "short_name": profile.short_name,
            "display_name": profile.display_name,
        }

    def _snapshot_move(self, move):
        return to_plain_value(
            {
                "name": move.name,
                "kind": move.kind.value,
                "resource_type": move.resource_type.value,
                "resource_cost": move.resource_cost,
                "power": move.power,
                "scales_with": [
                    attribute.value
                    for attribute in move.scales_with
                ],
                "accuracy": move.accuracy,
                "target": move.target.value,
                "damage_type": move.damage_type.value,
                "mechanic": move.mechanic,
                "description": move.description,
            },
            f"player.combat.moves.{move.name}",
        )

    def _snapshot_item(self, item, path):
        if item is None:
            return None

        if self._is_supported_weapon_item(item):
            return to_plain_value(
                {
                    "type": item.__class__.__name__,
                    "name": item.name,
                    "weapon_type": item.weapon_type,
                    "intended_wielder": item.intended_wielder,
                    "stat_bonuses": item.stat_bonuses,
                    "value": item.value,
                    "description": item.description,
                },
                path,
            )

        return to_plain_value(item, path)

    @staticmethod
    def _is_supported_weapon_item(item):
        return isinstance(item, Weapon)
