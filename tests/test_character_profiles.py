import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.player.character import BlackMage, Brawler, Monk, RogueArcher
from app.world.character_profiles.profile import render_compact_profile, render_full_profile
from app.world.character_profiles.roster import (
    get_character_profiles,
    get_profile_by_choice,
    render_character_roster,
)


def test_roster_choices_are_unique_and_ordered():
    profiles = get_character_profiles()

    choices = tuple(profile.choice for profile in profiles)

    assert choices == ("1", "2", "3", "4")
    assert len(set(choices)) == len(choices)


def test_choice_lookup_returns_canonical_profile_objects():
    profiles = get_character_profiles()

    for profile in profiles:
        assert get_profile_by_choice(profile.choice) is profile

    assert get_profile_by_choice("5") is None


def test_each_profile_creates_expected_character_class():
    expected_classes = (Brawler, BlackMage, RogueArcher, Monk)

    for profile, expected_class in zip(get_character_profiles(), expected_classes):
        character = profile.create_character()

        assert isinstance(character, expected_class)
        assert character.profile is profile
        assert character.name == character.archetype_name
        assert character.display_name == profile.short_name
        assert character.full_display_name == profile.display_name


def test_profile_names_are_canonical():
    profiles = get_character_profiles()

    assert tuple(profile.short_name for profile in profiles) == (
        "Ser Branoc",
        "Azhvielle",
        "Zhaivra Kelyth",
        "Joruun Veyr",
    )
    assert tuple(profile.display_name for profile in profiles) == (
        "Ser Branoc, the Unbroken Crest",
        "Azhvielle, the Unconfessed",
        "Zhaivra Kelyth, the Uncontrolled Reagent",
        "Joruun Veyr, the Bloody Storm Monk",
    )


def test_profiles_have_required_player_facing_fields():
    required_fields = (
        "choice",
        "display_name",
        "short_name",
        "ascii_art",
        "origin_title",
        "biography",
        "dungeon_motive",
        "combat_role",
        "combat_summary",
        "strengths",
        "weaknesses",
        "weapon",
        "discipline",
        "quote",
        "selection_summary",
    )

    for profile in get_character_profiles():
        for field_name in required_fields:
            assert getattr(profile, field_name)
        assert render_full_profile(profile)
        assert render_compact_profile(profile)


def test_compact_roster_contains_each_display_name_once_and_in_order():
    rendered_roster = render_character_roster()
    expected_names = (
        "Ser Branoc, the Unbroken Crest",
        "Azhvielle, the Unconfessed",
        "Zhaivra Kelyth, the Uncontrolled Reagent",
        "Joruun Veyr, the Bloody Storm Monk",
    )

    for name in expected_names:
        assert rendered_roster.count(name) == 1

    positions = [rendered_roster.index(name) for name in expected_names]
    assert positions == sorted(positions)


def test_compact_roster_has_four_entries_and_excludes_full_profile_content():
    rendered_roster = render_character_roster()

    assert rendered_roster.count("\n1. ") == 1
    assert rendered_roster.count("\n2. ") == 1
    assert rendered_roster.count("\n3. ") == 1
    assert rendered_roster.count("\n4. ") == 1
    assert "Choose your Drifter:" in rendered_roster
    assert "Heavy Vanguard — durable, relentless, slow" in rendered_roster
    assert "Elemental Controller — versatile, dangerous, unpredictable" in rendered_roster
    assert "Alchemical Marksman — precise, prepared, resource-limited" in rendered_roster
    assert "Elemental Skirmisher — mobile, adaptable, physically costly" in rendered_roster
    assert "Rhom-Ghalian Lung, a punishing" not in rendered_roster
    assert "THE UNBROKEN" not in rendered_roster
    assert "Sunder-Spire" not in rendered_roster


def test_full_profile_render_shows_only_one_selected_character():
    branoc = get_profile_by_choice("1")
    rendered_profile = render_full_profile(branoc)

    assert rendered_profile.startswith("Ser Branoc, the Unbroken Crest")
    assert "1. Ser Branoc" not in rendered_profile
    assert "Azhvielle, the Unconfessed" not in rendered_profile
    assert "Zhaivra Kelyth, the Uncontrolled Reagent" not in rendered_profile
    assert "Joruun Veyr, the Bloody Storm Monk" not in rendered_profile


def test_full_profile_includes_representative_profile_anchors():
    expected_anchors = (
        "Sunder-Spire",
        "Rhom-Ghalian Lung",
        "Endurance is merely suffering with direction.",
        "Needle of Plain Iron*",
        "Vharosynian Causal Sorcery",
        "That does not make it sensible.",
        "Sathren",
        "Ashvein Alchemy",
        "worst mistake of your life.",
        "Sky-Needle",
        "Law of the Single Current",
        "brewery provides salvation.",
    )
    rendered_profiles = "\n".join(render_full_profile(profile) for profile in get_character_profiles())

    for anchor in expected_anchors:
        assert anchor in rendered_profiles

    assert "**" not in rendered_profiles


if __name__ == "__main__":
    test_roster_choices_are_unique_and_ordered()
    test_choice_lookup_returns_canonical_profile_objects()
    test_each_profile_creates_expected_character_class()
    test_profile_names_are_canonical()
    test_profiles_have_required_player_facing_fields()
    test_compact_roster_contains_each_display_name_once_and_in_order()
    test_compact_roster_has_four_entries_and_excludes_full_profile_content()
    test_full_profile_render_shows_only_one_selected_character()
    test_full_profile_includes_representative_profile_anchors()
    print("Character profile tests passed.")
