from app.content.encounter_spec import EncounterSpec

ENCOUNTER = EncounterSpec(
    encounter_id="m8_floor_five_encounter_05",
    enemy_archetype_ids=(
        "reliquary_sentinel",
        "brine_oracle",
        "drowned_stalker",
    ),
)

__all__ = ["ENCOUNTER"]
