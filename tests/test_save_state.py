import copy

import pytest

from app.game.game_state import GameState
from app.game.overworld_state import ContextualRoutePhase
from app.game.save_state import (
    DISK_SCHEMA_VERSION,
    SaveStateValidationError,
    build_save_document,
    migrate_schema_7,
    reconstruct_game_state,
)
from app.items.weapon import SkyNeedle
from app.player.character_run_state import (
    InfusionKind,
    PreparedPayloadId,
)
from app.player.player_state import PlayerState
from app.snapshot import STATE_SCHEMA_VERSION
from app.world.character_profiles.roster import get_character_profiles


def _create_populated_game(choice):
    profile = next(
        profile
        for profile in get_character_profiles()
        if profile.choice == choice
    )
    player = PlayerState(profile.create_character(), gold=17)
    game = GameState(player)
    player.health.take_damage(11)
    player.mana_resource.spend(7)
    player.super_resource.gain(44)
    player.gain_experience(100)
    player.increase_permanent_stat("strength")
    player.inventory.add_item("tonic")
    player.inventory.add_item(SkyNeedle())
    player.character_run_state._prepared_payloads[PreparedPayloadId.INFUSED_BARB] = (
        InfusionKind.POISON
    ) if choice == "3" else None
    game.set_metadata("run_id", f"run-{choice}")
    game.story_state.current_chapter = "chapter_one"
    game.story_state.add_story_flag("opened")
    game.story_state.record_decision("route", "surface")
    game.world_state.discover_location("ketlyv_woods")
    game.world_state.mark_encounter_defeated("surface_goblin_solo")
    game.overworld_state.begin_surface_route()
    game.overworld_state.advance_to(
        "surface_goblin_pair",
        contextual_phase=ContextualRoutePhase.ENTER_ENCOUNTER,
    )
    return game


def test_schema8_document_has_only_persistent_state_and_schema7_stays_7():
    game = _create_populated_game("1")

    document = build_save_document(game)

    assert document["schema_version"] == DISK_SCHEMA_VERSION
    assert document["schema_version"] != STATE_SCHEMA_VERSION
    assert set(document) == {
        "schema_version",
        "player",
        "story",
        "world",
        "overworld",
        "metadata",
    }
    assert "combat" not in document["player"]
    assert game.snapshot()["schema_version"] == STATE_SCHEMA_VERSION
    assert "combat" in game.snapshot()["player"]


@pytest.mark.parametrize("choice", ("1", "2", "3", "4"))
def test_all_canonical_drifters_round_trip_persistent_state(choice):
    game = _create_populated_game(choice)
    document = build_save_document(game)

    restored = reconstruct_game_state(document)

    assert restored.snapshot()["schema_version"] == STATE_SCHEMA_VERSION
    assert build_save_document(restored) == document
    assert restored.player_state.character.profile.choice == choice
    assert restored.player_state.health.current == game.player_state.health.current
    assert restored.player_state.mana_resource.current == game.player_state.mana_resource.current
    assert restored.player_state.super_resource.current == game.player_state.super_resource.current
    assert restored.player_state.gold == game.player_state.gold
    assert restored.overworld_state.snapshot() == game.overworld_state.snapshot()
    assert restored.story_state.snapshot() == game.story_state.snapshot()
    assert restored.world_state.snapshot() == game.world_state.snapshot()


def test_reconstruction_creates_fresh_isolated_runtime_objects():
    document = build_save_document(_create_populated_game("1"))

    first = reconstruct_game_state(document)
    second = reconstruct_game_state(document)

    assert first is not second
    assert first.player_state is not second.player_state
    assert first.player_state.character is not second.player_state.character
    assert first.player_state.health is not second.player_state.health
    assert first.player_state.mana_resource is not second.player_state.mana_resource
    assert first.player_state.super_resource is not second.player_state.super_resource
    assert first.player_state.inventory is not second.player_state.inventory
    assert first.player_state.character_run_state is not second.player_state.character_run_state
    assert first.player_state.get_equipped("weapon") is not second.player_state.get_equipped("weapon")

    first.player_state.health.take_damage(5)
    first.player_state.inventory.add_item("first-only")
    first.player_state.character.permanent_stats.increase_stat("strength", 1)

    assert second.player_state.health.current != first.player_state.health.current
    assert "first-only" not in second.player_state.inventory.items
    assert second.player_state.stats.strength != first.player_state.stats.strength


def test_schema7_migration_preserves_state_and_ignores_combat_payload():
    game = _create_populated_game("2")
    schema7 = copy.deepcopy(game.snapshot())
    schema7["player"]["combat"]["moves"][0]["name"] = "forged move"
    schema7["overworld"]["current_route_node_id"] = "surface_goblin_pair"

    migrated = migrate_schema_7(schema7)

    assert migrated["schema_version"] == DISK_SCHEMA_VERSION
    assert "combat" not in migrated["player"]
    restored = reconstruct_game_state(schema7)
    assert restored.player_state.combat_moves[0].name != "forged move"
    assert restored.overworld_state.current_route_node_id == "surface_goblin_pair"
    assert restored.world_state.defeated_encounters == ("surface_goblin_solo",)


def test_schema7_migration_defaults_missing_overworld_fields_without_disk_io():
    game = _create_populated_game("1")
    schema7 = copy.deepcopy(game.snapshot())
    del schema7["overworld"]

    migrated = migrate_schema_7(schema7)
    restored = reconstruct_game_state(schema7)

    assert migrated["overworld"]["current_route_node_id"] == "surface_goblin_solo"
    assert restored.overworld_state.current_route_node_id == "surface_goblin_solo"
    assert restored.overworld_state.resolved_rest_node_ids == ()
    assert restored.world_state.defeated_encounters == ()


@pytest.mark.parametrize(
    "mutator",
    (
        lambda document: document.update(schema_version=6),
        lambda document: document.update(schema_version=9),
        lambda document: document["player"]["progression"].update(exp=True),
        lambda document: document["player"]["resources"]["health"].update(current=9999),
        lambda document: document["player"]["equipment"].update(
            weapon={"type": "UnknownWeapon"}
        ),
        lambda document: document["overworld"].update(
            resolved_rest_node_ids=["surface_rest_after_shaman_pair"]
        ),
        lambda document: document["overworld"].update(
            current_route_node_id="not_a_route_node"
        ),
    ),
)
def test_invalid_documents_are_rejected_before_reconstruction(mutator):
    document = build_save_document(_create_populated_game("1"))
    mutator(document)

    with pytest.raises(SaveStateValidationError):
        reconstruct_game_state(document)


def test_invalid_reconstruction_does_not_mutate_an_existing_session():
    game = _create_populated_game("1")
    before = game.snapshot()
    invalid = build_save_document(game)
    invalid["player"]["gold"] = -1

    with pytest.raises(SaveStateValidationError):
        reconstruct_game_state(invalid)

    assert game.snapshot() == before


def test_snapshot_and_save_document_are_defensive():
    game = _create_populated_game("4")
    document = build_save_document(game)

    document["player"]["attributes"]["strength"] = 100
    document["world"]["defeated_encounters"].append("changed")
    document["metadata"]["run_id"] = "changed"

    assert game.player_state.stats.strength != 100
    assert game.world_state.defeated_encounters == ("surface_goblin_solo",)
    assert game.metadata == {"run_id": "run-4"}
