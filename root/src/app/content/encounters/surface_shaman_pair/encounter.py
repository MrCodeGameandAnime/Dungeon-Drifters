"""Authored Shaman Pair encounter."""

from app.content.encounter_spec import EncounterSpec


ENCOUNTER = EncounterSpec(
    encounter_id="surface_shaman_pair",
    enemy_archetype_ids=("goblin_shaman", "goblin_shaman"),
)


__all__ = ["ENCOUNTER"]
