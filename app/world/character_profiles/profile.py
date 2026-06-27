"""Structured character profile data and rendering helpers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CharacterProfile:
    choice: str
    display_name: str
    character_factory: type
    ascii_art: str
    origin_title: str
    biography: str
    dungeon_motive: str
    combat_role: str
    combat_summary: str
    strengths: str
    weaknesses: str
    weapon: str
    discipline: str
    quote: str

    def create_character(self):
        return self.character_factory()


def render_profile(profile: CharacterProfile) -> str:
    profile_details = "\n".join(
        (
            f"Strengths: {profile.strengths}",
            f"Weaknesses: {profile.weaknesses}",
            f"Weapon: {profile.weapon}",
            f"Discipline: {profile.discipline}",
        )
    )
    sections = (
        f"{profile.choice}. {profile.display_name}",
        profile.ascii_art,
        profile.origin_title,
        profile.biography,
        profile.dungeon_motive,
        profile.combat_role,
        profile.combat_summary,
        profile_details,
        profile.quote,
    )
    return "\n\n".join(section.rstrip("\n") for section in sections)


def render_roster(profiles: tuple[CharacterProfile, ...]) -> str:
    intro = "You have four warriors to choose from who will adventure in the land of Ketlyv."
    return "\n\n".join((intro, *(render_profile(profile) for profile in profiles)))
