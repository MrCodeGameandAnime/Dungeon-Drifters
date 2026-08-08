"""Immutable authored route specifications."""

import keyword
import re
from dataclasses import dataclass
from enum import StrEnum


_CONTENT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def _content_id(name, value):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if _CONTENT_ID_PATTERN.fullmatch(value) is None or keyword.iskeyword(value):
        raise ValueError(f"{name} must be a lowercase snake-case ID")
    return value


def _nonempty_text(name, value):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value


class RouteNodeKind(StrEnum):
    COMBAT = "combat"
    REST = "rest"
    BOSS = "boss"
    DUNGEON_ENTRANCE = "dungeon_entrance"


@dataclass(frozen=True)
class EncounterSpec:
    enemy_archetype_ids: tuple[str, ...]

    def __post_init__(self):
        if not isinstance(self.enemy_archetype_ids, tuple):
            raise TypeError("enemy_archetype_ids must be a tuple")
        if not self.enemy_archetype_ids:
            raise ValueError("enemy_archetype_ids must not be empty")
        if len(self.enemy_archetype_ids) > 4:
            raise ValueError("encounters support at most four enemies")
        object.__setattr__(
            self,
            "enemy_archetype_ids",
            tuple(
                _content_id("enemy archetype ID", archetype_id)
                for archetype_id in self.enemy_archetype_ids
            ),
        )


@dataclass(frozen=True)
class RouteNodeSpec:
    node_id: str
    display_label: str
    kind: RouteNodeKind
    encounter: EncounterSpec | None = None

    def __post_init__(self):
        object.__setattr__(self, "node_id", _content_id("node_id", self.node_id))
        object.__setattr__(
            self,
            "display_label",
            _nonempty_text("display_label", self.display_label),
        )
        if not isinstance(self.kind, RouteNodeKind):
            raise TypeError("kind must be a RouteNodeKind")
        if self.encounter is not None and not isinstance(
            self.encounter,
            EncounterSpec,
        ):
            raise TypeError("encounter must be an EncounterSpec or None")

        requires_encounter = self.kind in {RouteNodeKind.COMBAT, RouteNodeKind.BOSS}
        if requires_encounter != (self.encounter is not None):
            raise ValueError("only combat and Boss route nodes define encounters")


@dataclass(frozen=True)
class RouteSpec:
    route_id: str
    nodes: tuple[RouteNodeSpec, ...]

    def __post_init__(self):
        object.__setattr__(self, "route_id", _content_id("route_id", self.route_id))
        if not isinstance(self.nodes, tuple):
            raise TypeError("nodes must be a tuple")
        if not self.nodes:
            raise ValueError("nodes must not be empty")
        if any(not isinstance(node, RouteNodeSpec) for node in self.nodes):
            raise TypeError("nodes must contain only RouteNodeSpec values")
        node_ids = tuple(node.node_id for node in self.nodes)
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("route node IDs must be unique")
        dungeon_indices = tuple(
            index
            for index, node in enumerate(self.nodes)
            if node.kind is RouteNodeKind.DUNGEON_ENTRANCE
        )
        if dungeon_indices and dungeon_indices != (len(self.nodes) - 1,):
            raise ValueError("a dungeon entrance must be unique and final")


__all__ = ["EncounterSpec", "RouteNodeKind", "RouteNodeSpec", "RouteSpec"]
