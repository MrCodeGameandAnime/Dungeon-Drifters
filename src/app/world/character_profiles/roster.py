"""Canonical playable character profile roster."""

from app.content.catalog import DRIFTER_SPECS, get_drifter_spec_by_choice
from app.content.drifter_spec import DrifterSpec
from app.world.character_profiles.profile import render_roster


CHARACTER_PROFILES: tuple[DrifterSpec, ...] = DRIFTER_SPECS


def get_character_profiles() -> tuple[DrifterSpec, ...]:
    return CHARACTER_PROFILES


def get_profile_by_choice(choice: str) -> DrifterSpec | None:
    return get_drifter_spec_by_choice(choice)


def render_character_roster() -> str:
    return render_roster(CHARACTER_PROFILES)
