"""Immutable authored Drifter specifications."""

import keyword
import re
from dataclasses import dataclass

from app.combat.move import Move
from app.player.character_run_state import PreparedPayloadId, RunItemId


_CONTENT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def _nonempty_string(name, value):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value


def _positive_stat(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 1 or value > 100:
        raise ValueError(f"{name} must be between 1 and 100")
    return value


@dataclass(frozen=True)
class DrifterStatSpec:
    constitution: int
    spirit: int
    intelligence: int
    strength: int
    dexterity: int
    intuition: int

    def __post_init__(self):
        for name in self.__dataclass_fields__:
            object.__setattr__(self, name, _positive_stat(name, getattr(self, name)))
        if sum(getattr(self, name) for name in self.__dataclass_fields__) != 60:
            raise ValueError("Level 1 Drifter stat total must be 60")

    def as_dict(self):
        return {
            name: getattr(self, name)
            for name in self.__dataclass_fields__
        }


@dataclass(frozen=True)
class ClassMechanicSpec:
    name: str
    description: str

    def __post_init__(self):
        object.__setattr__(self, "name", _nonempty_string("name", self.name))
        object.__setattr__(
            self,
            "description",
            _nonempty_string("description", self.description),
        )

    def as_dict(self):
        return {"name": self.name, "description": self.description}


@dataclass(frozen=True)
class DrifterSpec:
    drifter_id: str
    choice: str
    archetype_name: str
    stats: DrifterStatSpec
    combat_moves: tuple[Move, ...]
    class_mechanic: ClassMechanicSpec
    starting_weapon_id: str
    short_name: str
    display_name: str
    ascii_art: str
    origin_title: str
    biography: str
    dungeon_motive: str
    combat_role: str
    combat_summary: str
    strengths: str
    weaknesses: str
    weapon: str
    discipline: str
    quote: str
    selection_summary: str
    starting_run_inventory: tuple[tuple[RunItemId, int], ...] = ()
    starting_prepared_payloads: tuple[tuple[PreparedPayloadId, None], ...] = ()

    def __post_init__(self):
        drifter_id = _nonempty_string("drifter_id", self.drifter_id)
        if (
            _CONTENT_ID_PATTERN.fullmatch(drifter_id) is None
            or keyword.iskeyword(drifter_id)
        ):
            raise ValueError(
                "drifter_id must be a lowercase snake-case Python module name"
            )
        object.__setattr__(self, "drifter_id", drifter_id)

        for name in (
            "archetype_name",
            "starting_weapon_id",
            "short_name",
            "display_name",
            "ascii_art",
            "origin_title",
            "biography",
            "dungeon_motive",
            "combat_role",
            "combat_summary",
            "strengths",
            "weaknesses",
            "weapon",
            "discipline",
            "quote",
            "selection_summary",
        ):
            object.__setattr__(self, name, _nonempty_string(name, getattr(self, name)))
        choice = _nonempty_string("choice", self.choice)
        if not choice.isascii() or not choice.isdecimal() or int(choice) < 1:
            raise ValueError("choice must be a positive ASCII integer string")
        object.__setattr__(self, "choice", choice)
        if (
            _CONTENT_ID_PATTERN.fullmatch(self.starting_weapon_id) is None
            or keyword.iskeyword(self.starting_weapon_id)
        ):
            raise ValueError("starting_weapon_id must be a lowercase snake-case ID")

        if not isinstance(self.stats, DrifterStatSpec):
            raise TypeError("stats must be a DrifterStatSpec")
        if not isinstance(self.class_mechanic, ClassMechanicSpec):
            raise TypeError("class_mechanic must be a ClassMechanicSpec")
        if not isinstance(self.combat_moves, tuple):
            raise TypeError("combat_moves must be a tuple")
        if not self.combat_moves:
            raise ValueError("combat_moves must not be empty")
        if any(not isinstance(move, Move) for move in self.combat_moves):
            raise TypeError("combat_moves must contain only Move values")
        names = tuple(move.name for move in self.combat_moves)
        if len(names) != len(set(names)):
            raise ValueError("combat moves must use unique names")

        inventory = self._validate_inventory(self.starting_run_inventory)
        payloads = self._validate_payloads(self.starting_prepared_payloads)
        object.__setattr__(self, "starting_run_inventory", inventory)
        object.__setattr__(self, "starting_prepared_payloads", payloads)

    @staticmethod
    def _validate_inventory(values):
        if not isinstance(values, tuple):
            raise TypeError("starting_run_inventory must be a tuple")
        validated = []
        for entry in values:
            if not isinstance(entry, tuple) or len(entry) != 2:
                raise TypeError("starting run-item entries must be pairs")
            item_id, quantity = entry
            item_id = RunItemId(item_id)
            if isinstance(quantity, bool) or not isinstance(quantity, int):
                raise TypeError("run-item quantities must be integers")
            if quantity < 0:
                raise ValueError("run-item quantities must not be negative")
            validated.append((item_id, quantity))
        if len({item_id for item_id, _ in validated}) != len(validated):
            raise ValueError("starting run-item IDs must be unique")
        return tuple(validated)

    @staticmethod
    def _validate_payloads(values):
        if not isinstance(values, tuple):
            raise TypeError("starting_prepared_payloads must be a tuple")
        validated = []
        for entry in values:
            if not isinstance(entry, tuple) or len(entry) != 2:
                raise TypeError("starting prepared-payload entries must be pairs")
            payload_id, value = entry
            payload_id = PreparedPayloadId(payload_id)
            if value is not None:
                raise ValueError("starting prepared payloads must be empty")
            validated.append((payload_id, None))
        if len({payload_id for payload_id, _ in validated}) != len(validated):
            raise ValueError("starting prepared-payload IDs must be unique")
        return tuple(validated)

    def _create_character(self, *, attach_profile):
        from app.content.catalog import create_weapon
        from app.player.character import Character

        character = Character(
            **self.stats.as_dict(),
            name=self.archetype_name,
            combat_moves=tuple(move for move in self.combat_moves),
            class_mechanic=self.class_mechanic.as_dict(),
            starting_equipment={"weapon": create_weapon(self.starting_weapon_id)},
            starting_run_inventory=dict(self.starting_run_inventory),
            starting_prepared_payloads=dict(self.starting_prepared_payloads),
        )
        if attach_profile:
            character.profile = self
        return character

    def create_character(self):
        return self._create_character(attach_profile=True)

    def create_unselected_character(self):
        return self._create_character(attach_profile=False)


__all__ = ["ClassMechanicSpec", "DrifterSpec", "DrifterStatSpec"]
