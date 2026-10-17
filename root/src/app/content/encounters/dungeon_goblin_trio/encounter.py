"""Authored first-floor tutorial encounter."""

from app.content.encounter_spec import EncounterSpec


ENCOUNTER = EncounterSpec(
    encounter_id="dungeon_goblin_trio",
    enemy_archetype_ids=("goblin", "goblin", "goblin"),
)


__all__ = ["ENCOUNTER"]
