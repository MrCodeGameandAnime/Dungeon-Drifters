"""Authored Goblin Lord encounter."""

from app.content.encounter_spec import EncounterSpec


ENCOUNTER = EncounterSpec(
    encounter_id="surface_goblin_lord",
    enemy_archetype_ids=("goblin_lord", "goblin", "goblin_warrior"),
)


__all__ = ["ENCOUNTER"]
