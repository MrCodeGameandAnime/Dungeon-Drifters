import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.game.story_state import StoryState


def test_story_state_initial_values_are_empty():
    story_state = StoryState()

    assert story_state.current_chapter is None
    assert story_state.current_scene is None
    assert story_state.current_location is None
    assert story_state.story_flags == ()
    assert story_state.completed_events == ()
    assert story_state.player_decisions == {}


def test_story_state_accepts_initial_location_values():
    story_state = StoryState(
        current_chapter="chapter_one",
        current_scene="opening",
        current_location="woods",
    )

    assert story_state.current_chapter == "chapter_one"
    assert story_state.current_scene == "opening"
    assert story_state.current_location == "woods"


def test_story_state_collection_views_cannot_mutate_internal_state():
    story_state = StoryState()
    story_state.add_story_flag("heard_goblin")
    story_state.complete_event("opening_ambush")
    story_state.record_decision("first_choice", "attack")

    flags = story_state.story_flags
    completed_events = story_state.completed_events
    decisions = story_state.player_decisions

    flags += ("changed",)
    completed_events += ("changed",)
    decisions["first_choice"] = "flee"

    assert story_state.story_flags == ("heard_goblin",)
    assert story_state.completed_events == ("opening_ambush",)
    assert story_state.player_decisions == {"first_choice": "attack"}


def test_story_state_instances_do_not_share_collections():
    first = StoryState()
    second = StoryState()

    first.add_story_flag("flag")
    first.complete_event("event")
    first.record_decision("choice", "attack")

    assert first.story_flags == ("flag",)
    assert first.completed_events == ("event",)
    assert first.player_decisions == {"choice": "attack"}
    assert second.story_flags == ()
    assert second.completed_events == ()
    assert second.player_decisions == {}


if __name__ == "__main__":
    test_story_state_initial_values_are_empty()
    test_story_state_accepts_initial_location_values()
    test_story_state_collection_views_cannot_mutate_internal_state()
    test_story_state_instances_do_not_share_collections()
    print("Story state test passed.")

