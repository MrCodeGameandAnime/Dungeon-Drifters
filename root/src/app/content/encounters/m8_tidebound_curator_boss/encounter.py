from app.content.encounter_spec import EncounterSpec

ENCOUNTER = EncounterSpec(
    encounter_id="m8_tidebound_curator_boss",
    enemy_archetype_ids=("tidebound_curator", "reliquary_sentinel"),
)

__all__ = ["ENCOUNTER"]
