"""Player-facing Drifter profile rendering helpers."""

from app.content.drifter_spec import DrifterSpec


def render_compact_profile(profile: DrifterSpec) -> str:
    return "\n".join(
        (
            f"{profile.choice}. {profile.display_name}",
            f"   {profile.combat_role} — {profile.selection_summary}",
        )
    )


def render_full_profile(profile: DrifterSpec) -> str:
    profile_details = "\n".join(
        (
            f"Strengths: {profile.strengths}",
            f"Weaknesses: {profile.weaknesses}",
            f"Weapon: {profile.weapon}",
            f"Discipline: {profile.discipline}",
        )
    )
    sections = (
        profile.display_name,
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


def render_profile(profile: DrifterSpec) -> str:
    return render_full_profile(profile)


def render_roster(profiles: tuple[DrifterSpec, ...]) -> str:
    return "\n\n".join(("Choose your Drifter:", *(render_compact_profile(profile) for profile in profiles)))


__all__ = ["render_compact_profile", "render_full_profile", "render_profile", "render_roster"]
