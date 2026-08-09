"""Authored Goblin Shaman encounter."""

from app.content.encounter_spec import EncounterSpec


ENCOUNTER = EncounterSpec(
    encounter_id="surface_shaman_solo",
    enemy_archetype_ids=("goblin_shaman",),
)


__all__ = ["ENCOUNTER"]
