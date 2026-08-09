"""Authored Goblin Ambush encounter."""

from app.content.encounter_spec import EncounterSpec


ENCOUNTER = EncounterSpec(
    encounter_id="surface_goblin_solo",
    enemy_archetype_ids=("goblin",),
)


__all__ = ["ENCOUNTER"]
