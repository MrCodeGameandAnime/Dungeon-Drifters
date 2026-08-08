"""Authored Goblin Warrior encounter."""

from app.content.encounter_spec import EncounterSpec


ENCOUNTER = EncounterSpec(
    encounter_id="surface_warrior_solo",
    enemy_archetype_ids=("goblin_warrior",),
)


__all__ = ["ENCOUNTER"]
