"""Canonical playable character profile roster."""

from app.world.character_profiles.azhvielle import PROFILE as AZHVIELLE_PROFILE
from app.world.character_profiles.branoc import PROFILE as BRANOC_PROFILE
from app.world.character_profiles.joruun import PROFILE as JORUUN_PROFILE
from app.world.character_profiles.profile import CharacterProfile, render_roster
from app.world.character_profiles.zhaivra import PROFILE as ZHAIVRA_PROFILE


CHARACTER_PROFILES: tuple[CharacterProfile, ...] = (
    BRANOC_PROFILE,
    AZHVIELLE_PROFILE,
    ZHAIVRA_PROFILE,
    JORUUN_PROFILE,
)

_PROFILES_BY_CHOICE = {profile.choice: profile for profile in CHARACTER_PROFILES}


def get_character_profiles() -> tuple[CharacterProfile, ...]:
    return CHARACTER_PROFILES


def get_profile_by_choice(choice: str) -> CharacterProfile | None:
    return _PROFILES_BY_CHOICE.get(choice)


def render_character_roster() -> str:
    return render_roster(CHARACTER_PROFILES)

