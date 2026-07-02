"""Enemy archetype registration contracts."""

from collections.abc import Callable
from dataclasses import dataclass

from app.enemies.definition import Enemy


@dataclass(frozen=True)
class EnemyArchetypeRegistration:
    archetype_id: str
    definition_factory: Callable[[], Enemy]
    scaling_policy: Callable[[Enemy, int], Enemy]

    def __post_init__(self):
        if not isinstance(self.archetype_id, str):
            raise TypeError("archetype_id must be a string")
        if not self.archetype_id:
            raise ValueError("archetype_id must not be empty")
        if not callable(self.definition_factory):
            raise TypeError("definition_factory must be callable")
        if not callable(self.scaling_policy):
            raise TypeError("scaling_policy must be callable")
