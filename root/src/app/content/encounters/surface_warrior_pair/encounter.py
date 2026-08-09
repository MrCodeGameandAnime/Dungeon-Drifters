"""Authored Warrior Patrol encounter."""

from app.content.encounter_spec import EncounterSpec


ENCOUNTER = EncounterSpec(
    encounter_id="surface_warrior_pair",
    enemy_archetype_ids=("goblin_warrior", "goblin_warrior"),
)


__all__ = ["ENCOUNTER"]
