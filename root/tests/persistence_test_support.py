"""Helpers for exercising the production local-first save coordinator."""

from pathlib import Path
from uuid import UUID

from app.persistence.bootstrap import build_default_save_port


TEST_PROFILE_ID = UUID("00000000-0000-4000-8000-000000000001")
REGION_PROGRESS_PARTY_FIELDS = (
    "floor_four_cleared",
    "floor_five_cleared",
    "region_two_unlocked",
)
FLOOR_FOUR_RUN_PARTY_FIELDS = (
    "floor_four_runs_started_after_clear",
    "floor_four_run_id",
    "floor_four_outing_xp_multiplier_percent",
)
FLOOR_FIVE_RUN_PARTY_FIELDS = (
    "floor_five_approach_run_id",
    "floor_five_reunion_run_id",
)


def remove_floor_four_run_state(payload):
    party = payload.get("party")
    if isinstance(party, dict):
        for field in FLOOR_FOUR_RUN_PARTY_FIELDS:
            party.pop(field, None)
    return payload


def remove_floor_five_run_state(payload):
    party = payload.get("party")
    if isinstance(party, dict):
        for field in FLOOR_FIVE_RUN_PARTY_FIELDS:
            party.pop(field, None)
    return payload


def remove_region_progression_state(payload):
    party = payload.get("party")
    if isinstance(party, dict):
        for field in REGION_PROGRESS_PARTY_FIELDS:
            party.pop(field, None)
    story = payload.get("story")
    if isinstance(story, dict):
        story.pop("knowledge_facts", None)
    remove_floor_four_run_state(payload)
    return remove_floor_five_run_state(payload)


def make_test_save_port(legacy_path):
    legacy_path = Path(legacy_path)
    return build_default_save_port(
        storage_root=storage_root_for(legacy_path),
        legacy_path=legacy_path,
        profile_id_factory=lambda: TEST_PROFILE_ID,
    )


def storage_root_for(legacy_path):
    legacy_path = Path(legacy_path)
    return legacy_path.with_name(f"{legacy_path.stem}.profiles")


def profile_path_for(legacy_path, profile_id=TEST_PROFILE_ID):
    return storage_root_for(legacy_path) / "profiles" / f"{profile_id}.json"
