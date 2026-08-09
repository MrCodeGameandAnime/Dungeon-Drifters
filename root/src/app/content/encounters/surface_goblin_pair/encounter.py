"""Authored Goblin Pair encounter."""

from app.content.encounter_spec import EncounterSpec


ENCOUNTER = EncounterSpec(
    encounter_id="surface_goblin_pair",
    enemy_archetype_ids=("goblin", "goblin"),
)


__all__ = ["ENCOUNTER"]
