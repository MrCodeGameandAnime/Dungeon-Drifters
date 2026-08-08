"""Immutable authored encounter specifications."""

from dataclasses import dataclass

from app.content.route_spec import validate_content_id


@dataclass(frozen=True)
class EncounterSpec:
    encounter_id: str
    enemy_archetype_ids: tuple[str, ...]

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


__all__ = ["EncounterSpec"]
