import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.game.game_state import GameState
from app.player.character import Brawler
from app.player.player_state import PlayerState
from app.snapshot import STATE_SCHEMA_VERSION, to_plain_value, validate_plain_value


def assert_raises(error_type, action):
    try:
        action()
    except error_type as error:
        return error

    raise AssertionError(f"{error_type.__name__} was not raised")


def assert_strict_json(snapshot):
    validate_plain_value(snapshot)
    json.dumps(snapshot, allow_nan=False)


def create_populated_game_state():
    player_state = PlayerState(Brawler(), gold=12)
    game_state = GameState(player_state)

    game_state.set_metadata("run_id", "test-run")
    game_state.story_state.current_chapter = "chapter_one"
    game_state.story_state.current_scene = "opening"
    game_state.story_state.current_location = "ketlyv_woods"
    game_state.story_state.add_story_flag("heard_goblin")
    game_state.story_state.complete_event("opening_ambush")
    game_state.story_state.record_decision("first_choice", "attack")
    game_state.world_state.discover_location("ketlyv_woods")
    game_state.world_state.mark_encounter_defeated("goblin")
    game_state.world_state.mark_object_opened("old_chest")
    game_state.world_state.mark_object_consumed("campfire")
    game_state.world_state.set_dungeon_change("first_gate", "open")

    return player_state, game_state


def test_game_snapshot_has_required_shape_and_schema_version():
    player_state, game_state = create_populated_game_state()

    snapshot = game_state.snapshot()

    assert game_state.player_state is player_state
    assert snapshot["schema_version"] == STATE_SCHEMA_VERSION
    assert snapshot["schema_version"] == 1
    assert set(snapshot.keys()) == {
        "schema_version",
        "player",
        "story",
        "world",
        "metadata",
    }
    assert snapshot["player"]["gold"] == 12
    assert snapshot["metadata"] == {"run_id": "test-run"}
    assert_strict_json(snapshot)


def test_story_and_world_snapshot_content_is_owned_by_their_state_classes():
    _, game_state = create_populated_game_state()

    snapshot = game_state.snapshot()

    assert snapshot["story"] == {
        "current_chapter": "chapter_one",
        "current_scene": "opening",
        "current_location": "ketlyv_woods",
        "story_flags": ["heard_goblin"],
        "completed_events": ["opening_ambush"],
        "player_decisions": {"first_choice": "attack"},
    }
    assert snapshot["world"] == {
        "discovered_locations": ["ketlyv_woods"],
        "defeated_encounters": ["goblin"],
        "opened_objects": ["old_chest"],
        "consumed_objects": ["campfire"],
        "dungeon_changes": {"first_gate": "open"},
    }
    assert_strict_json(snapshot)


def test_game_snapshot_is_isolated_from_runtime_state():
    _, game_state = create_populated_game_state()

    first_snapshot = game_state.snapshot()
    second_snapshot = game_state.snapshot()

    assert first_snapshot == second_snapshot
    first_snapshot["metadata"]["run_id"] = "changed"
    first_snapshot["story"]["story_flags"].append("changed")
    first_snapshot["world"]["opened_objects"].append("changed")
    first_snapshot["player"]["gold"] = 999

    assert game_state.metadata == {"run_id": "test-run"}
    assert game_state.story_state.story_flags == ("heard_goblin",)
    assert game_state.world_state.opened_objects == ("old_chest",)
    assert game_state.player_state.gold == 12
    assert second_snapshot["metadata"] == {"run_id": "test-run"}
    assert second_snapshot["story"]["story_flags"] == ["heard_goblin"]
    assert second_snapshot["world"]["opened_objects"] == ["old_chest"]

    game_state.set_metadata("later", "mutation")
    game_state.story_state.add_story_flag("later_flag")
    game_state.world_state.mark_object_opened("later_chest")

    assert first_snapshot["metadata"] == {"run_id": "changed"}
    assert second_snapshot["metadata"] == {"run_id": "test-run"}
    assert game_state.snapshot()["metadata"] == {
        "run_id": "test-run",
        "later": "mutation",
    }


def test_independent_sessions_do_not_share_snapshot_containers():
    _, first = create_populated_game_state()
    _, second = create_populated_game_state()

    first.set_metadata("session", "first")
    first.story_state.add_story_flag("first_only")
    first.world_state.discover_location("first_only_location")

    first_snapshot = first.snapshot()
    second_snapshot = second.snapshot()

    assert first_snapshot is not second_snapshot
    assert first_snapshot["metadata"] is not second_snapshot["metadata"]
    assert first_snapshot["story"]["story_flags"] is not second_snapshot["story"]["story_flags"]
    assert first_snapshot["world"]["discovered_locations"] is not second_snapshot["world"]["discovered_locations"]
    assert "first_only" in first_snapshot["story"]["story_flags"]
    assert "first_only" not in second_snapshot["story"]["story_flags"]
    assert "first_only_location" in first_snapshot["world"]["discovered_locations"]
    assert "first_only_location" not in second_snapshot["world"]["discovered_locations"]
    assert_strict_json(first_snapshot)
    assert_strict_json(second_snapshot)


def test_unsupported_metadata_story_and_world_values_fail_clearly():
    _, game_state = create_populated_game_state()
    game_state.set_metadata("bad", object())

    metadata_error = assert_raises(TypeError, game_state.snapshot)
    assert "game.metadata.bad" in str(metadata_error)

    _, game_state = create_populated_game_state()
    game_state.story_state.record_decision("bad", object())

    story_error = assert_raises(TypeError, game_state.snapshot)
    assert "story.player_decisions.bad" in str(story_error)

    _, game_state = create_populated_game_state()
    game_state.world_state.set_dungeon_change("bad", object())

    world_error = assert_raises(TypeError, game_state.snapshot)
    assert "world.dungeon_changes.bad" in str(world_error)


def test_non_finite_floats_are_rejected_with_paths():
    non_finite_values = (
        ("nan", float("nan")),
        ("positive_inf", float("inf")),
        ("negative_inf", float("-inf")),
    )

    for name, value in non_finite_values:
        _, game_state = create_populated_game_state()
        game_state.set_metadata(name, value)

        error = assert_raises(TypeError, game_state.snapshot)
        assert f"game.metadata.{name}" in str(error)


def test_plain_value_conversion_and_validation_treat_tuples_differently():
    assert to_plain_value((1, 2)) == [1, 2]

    tuple_error = assert_raises(TypeError, lambda: validate_plain_value((1, 2)))
    assert "snapshot" in str(tuple_error)
    assert "tuple" in str(tuple_error)

    nested_error = assert_raises(
        TypeError,
        lambda: validate_plain_value({"outer": [{"inner": (1, 2)}]}),
    )
    assert "snapshot.outer[0].inner" in str(nested_error)


if __name__ == "__main__":
    test_game_snapshot_has_required_shape_and_schema_version()
    test_story_and_world_snapshot_content_is_owned_by_their_state_classes()
    test_game_snapshot_is_isolated_from_runtime_state()
    test_independent_sessions_do_not_share_snapshot_containers()
    test_unsupported_metadata_story_and_world_values_fail_clearly()
    test_non_finite_floats_are_rejected_with_paths()
    test_plain_value_conversion_and_validation_treat_tuples_differently()
    print("Game snapshot test passed.")
