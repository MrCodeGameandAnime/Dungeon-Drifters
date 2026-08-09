"""Authored Elite Patrol encounter."""

from app.content.encounter_spec import EncounterSpec


ENCOUNTER = EncounterSpec(
    encounter_id="surface_elite_patrol",
    enemy_archetype_ids=("goblin_elite", "goblin"),
)


__all__ = ["ENCOUNTER"]
