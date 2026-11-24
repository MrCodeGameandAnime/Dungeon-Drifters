from app.content.encounter_spec import EncounterSpec

ENCOUNTER = EncounterSpec(
    encounter_id="m8_floor_four_encounter_08",
    enemy_archetype_ids=("reliquary_sentinel", "ashbound_hound", "brine_oracle"),
)

__all__ = ["ENCOUNTER"]
