"""Authored four-Goblin Floor 1 encounter."""

from app.content.encounter_spec import EncounterSpec


ENCOUNTER = EncounterSpec(
    encounter_id="dungeon_goblin_quad",
    enemy_archetype_ids=("goblin", "goblin", "goblin", "goblin"),
)


__all__ = ["ENCOUNTER"]
