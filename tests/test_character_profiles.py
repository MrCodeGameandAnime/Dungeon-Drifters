import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.player.character import BlackMage, Brawler, Monk, RogueArcher
from app.world.character_profiles.profile import render_profile
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
        assert isinstance(profile.create_character(), expected_class)


def test_profiles_have_required_player_facing_fields():
    required_fields = (
        "choice",
        "display_name",
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
    )

    for profile in get_character_profiles():
        for field_name in required_fields:
            assert getattr(profile, field_name)
        assert render_profile(profile)


def test_rendered_roster_contains_each_display_name_once_and_in_order():
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


def test_rendered_roster_includes_representative_profile_anchors():
    rendered_roster = render_character_roster()
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

    for anchor in expected_anchors:
        assert anchor in rendered_roster


if __name__ == "__main__":
    test_roster_choices_are_unique_and_ordered()
    test_choice_lookup_returns_canonical_profile_objects()
    test_each_profile_creates_expected_character_class()
    test_profiles_have_required_player_facing_fields()
    test_rendered_roster_contains_each_display_name_once_and_in_order()
    test_rendered_roster_includes_representative_profile_anchors()
    print("Character profile tests passed.")
