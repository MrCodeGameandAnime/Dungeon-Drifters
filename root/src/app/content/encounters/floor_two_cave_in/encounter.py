"""Authored Floor II encounter with the first telegraphed cave-in."""

from app.content.encounter_spec import EncounterSpec


ENCOUNTER = EncounterSpec(
    encounter_id="floor_two_cave_in",
    enemy_archetype_ids=("goblin", "goblin_warrior"),
    cave_in_power=20,
)


__all__ = ["ENCOUNTER"]
