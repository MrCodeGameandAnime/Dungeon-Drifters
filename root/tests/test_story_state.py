import pytest

from app.game.story_state import KnowledgeStatus, StoryState


def test_story_state_initial_values_are_empty():
    story_state = StoryState()

    assert story_state.current_chapter is None
    assert story_state.current_scene is None
    assert story_state.current_location is None
    assert story_state.story_flags == ()
    assert story_state.completed_events == ()
    assert story_state.player_decisions == {}
    assert story_state.knowledge_facts == {}
    assert (
        story_state.knowledge_status("m8_fact_drowned_reliquary")
        is KnowledgeStatus.UNKNOWN
    )


def test_knowledge_facts_advance_monotonically_and_survive_snapshot_round_trip():
    story_state = StoryState()

    assert story_state.reveal_knowledge_fact(
        "m8_fact_drowned_reliquary",
        KnowledgeStatus.RUMORED,
    ) is True
    assert story_state.reveal_knowledge_fact(
        "m8_fact_drowned_reliquary",
        KnowledgeStatus.RUMORED,
    ) is False
    assert story_state.reveal_knowledge_fact(
        "m8_fact_drowned_reliquary",
        KnowledgeStatus.CONFIRMED,
    ) is True
    assert story_state.reveal_knowledge_fact(
        "m8_fact_drowned_reliquary",
        KnowledgeStatus.RUMORED,
    ) is False

    restored = StoryState.from_snapshot(story_state.snapshot())
    assert restored.knowledge_status(
        "m8_fact_drowned_reliquary"
    ) is KnowledgeStatus.CONFIRMED
    assert restored.snapshot()["knowledge_facts"] == {
        "m8_fact_drowned_reliquary": "confirmed",
    }


def test_knowledge_state_rejects_unknown_fact_ids_and_unknown_status():
    story_state = StoryState()

    with pytest.raises(ValueError, match="unknown knowledge fact"):
        story_state.knowledge_status("unapproved_fact")
    with pytest.raises(ValueError, match="unknown knowledge fact"):
        story_state.reveal_knowledge_fact("unapproved_fact", "rumored")
    with pytest.raises(ValueError, match="unknown knowledge fact"):
        story_state.knowledge_status(["unapproved_fact"])
    with pytest.raises(ValueError, match="knowledge status"):
        story_state.reveal_knowledge_fact(
            "m8_fact_drowned_reliquary",
            "discovered",
        )


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
    assert first.knowledge_facts == {}
    assert second.knowledge_facts == {}
