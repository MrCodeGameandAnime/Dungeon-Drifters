from app.content.encounter_spec import EncounterSpec

ENCOUNTER = EncounterSpec(
    encounter_id="m8_floor_four_encounter_01",
    enemy_archetype_ids=("reliquary_sentinel", "drowned_stalker"),
)

__all__ = ["ENCOUNTER"]
