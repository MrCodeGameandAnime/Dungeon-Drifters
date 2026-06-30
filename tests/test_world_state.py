from app.game.world_state import WorldState


def test_world_state_initial_values_are_empty():
    world_state = WorldState()

    assert world_state.discovered_locations == ()
    assert world_state.defeated_encounters == ()
    assert world_state.opened_objects == ()
    assert world_state.consumed_objects == ()
    assert world_state.dungeon_changes == {}


def test_world_state_collection_views_cannot_mutate_internal_state():
    world_state = WorldState()
    world_state.discover_location("woods")
    world_state.mark_encounter_defeated("goblin")
    world_state.mark_object_opened("chest")
    world_state.mark_object_consumed("campfire")
    world_state.set_dungeon_change("first_gate", "open")

    locations = world_state.discovered_locations
    encounters = world_state.defeated_encounters
    opened_objects = world_state.opened_objects
    consumed_objects = world_state.consumed_objects
    changes = world_state.dungeon_changes

    locations += ("changed",)
    encounters += ("changed",)
    opened_objects += ("changed",)
    consumed_objects += ("changed",)
    changes["first_gate"] = "closed"

    assert world_state.discovered_locations == ("woods",)
    assert world_state.defeated_encounters == ("goblin",)
    assert world_state.opened_objects == ("chest",)
    assert world_state.consumed_objects == ("campfire",)
    assert world_state.dungeon_changes == {"first_gate": "open"}


def test_world_state_instances_do_not_share_collections():
    first = WorldState()
    second = WorldState()

    first.discover_location("woods")
    first.mark_encounter_defeated("goblin")
    first.mark_object_opened("chest")
    first.mark_object_consumed("campfire")
    first.set_dungeon_change("first_gate", "open")

    assert first.discovered_locations == ("woods",)
    assert first.defeated_encounters == ("goblin",)
    assert first.opened_objects == ("chest",)
    assert first.consumed_objects == ("campfire",)
    assert first.dungeon_changes == {"first_gate": "open"}
    assert second.discovered_locations == ()
    assert second.defeated_encounters == ()
    assert second.opened_objects == ()
    assert second.consumed_objects == ()
    assert second.dungeon_changes == {}


def test_world_state_collection_methods_prevent_duplicates():
    world_state = WorldState()

    world_state.discover_location("woods")
    world_state.discover_location("woods")
    world_state.mark_encounter_defeated("goblin")
    world_state.mark_encounter_defeated("goblin")
    world_state.mark_object_opened("chest")
    world_state.mark_object_opened("chest")
    world_state.mark_object_consumed("campfire")
    world_state.mark_object_consumed("campfire")

    assert world_state.discovered_locations == ("woods",)
    assert world_state.defeated_encounters == ("goblin",)
    assert world_state.opened_objects == ("chest",)
    assert world_state.consumed_objects == ("campfire",)


if __name__ == "__main__":
    test_world_state_initial_values_are_empty()
    test_world_state_collection_views_cannot_mutate_internal_state()
    test_world_state_instances_do_not_share_collections()
    test_world_state_collection_methods_prevent_duplicates()
    print("World state test passed.")
