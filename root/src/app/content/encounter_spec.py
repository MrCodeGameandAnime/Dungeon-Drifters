"""Immutable authored encounter specifications."""

from dataclasses import dataclass

from app.content.route_spec import validate_content_id


@dataclass(frozen=True)
class EncounterSpec:
    encounter_id: str
    enemy_archetype_ids: tuple[str, ...]
    cave_in_power: int | None = None

    def __post_init__(self):
        object.__setattr__(
            self,
            "encounter_id",
            validate_content_id("encounter_id", self.encounter_id),
        )
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
                validate_content_id("enemy archetype ID", archetype_id)
                for archetype_id in self.enemy_archetype_ids
            ),
        )
        if self.cave_in_power is not None:
            if isinstance(self.cave_in_power, bool) or not isinstance(
                self.cave_in_power,
                int,
            ):
                raise TypeError("cave_in_power must be a positive integer or None")
            if self.cave_in_power < 1:
                raise ValueError("cave_in_power must be positive")


__all__ = ["EncounterSpec"]
