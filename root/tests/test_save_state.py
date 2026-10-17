import copy

import pytest

from app.game.game_state import GameState
from app.game.overworld_state import ContextualRoutePhase, OverworldState
from app.game.party_state import DungeonPhase
from app.persistence.save_document import (
    DISK_SCHEMA_VERSION,
    SaveStateValidationError,
    build_save_document,
    migrate_schema_7,
    reconstruct_game_state,
)
from app.content.catalog import create_weapon, get_route_spec
from app.player.character_run_state import (
    InfusionKind,
    PreparedPayloadId,
)
from app.player.player_state import PlayerState
from app.snapshot import STATE_SCHEMA_VERSION
from app.content.catalog import DRIFTER_SPECS


def get_character_profiles():
    return DRIFTER_SPECS


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
    player.inventory.add_item(create_weapon("sky_needle"))
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


def _move_game_to_dungeon_entrance(game):
    route = get_route_spec("surface")
    entrance = route.nodes[-1]
    for node in route.nodes[:-1]:
        if node.encounter_id is not None:
            game.world_state.mark_encounter_defeated(node.encounter_id)
    rests = [
        node.node_id for node in route.nodes[:-1] if node.kind.value == "rest"
    ]
    for rest_id in rests:
        game.overworld_state.record_resolved_rest_node(rest_id)
    game._overworld_state = OverworldState.from_snapshot(
        {
            "current_route_node_id": entrance.node_id,
            "surface_route_begun": True,
            "dungeon_entrance_reached": True,
            "route_complete": True,
            "resolved_rest_node_ids": rests,
            "current_contextual_route_phase": "none",
        }
    )


def test_schema9_document_has_only_persistent_state_and_schema8_stays_runtime_only():
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
        "party",
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
    schema7["schema_version"] = 7
    schema7.pop("party", None)
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
    schema7["schema_version"] = 7
    schema7.pop("party", None)
    del schema7["overworld"]

    migrated = migrate_schema_7(schema7)
    restored = reconstruct_game_state(schema7)

    assert migrated["overworld"]["current_route_node_id"] == "surface_goblin_solo"
    assert restored.overworld_state.current_route_node_id == "surface_goblin_solo"
    assert restored.overworld_state.resolved_rest_node_ids == ()
    assert restored.world_state.defeated_encounters == ()


def _old_schema8_document(game, *, at_dungeon_entrance=False):
    document = copy.deepcopy(game.snapshot())
    document["schema_version"] = 8
    document.pop("party", None)
    document["player"].pop("combat")
    if at_dungeon_entrance:
        route = get_route_spec("surface")
        entrance = route.nodes[-1]
        document["overworld"].update(
            current_route_node_id=entrance.node_id,
            surface_route_begun=True,
            dungeon_entrance_reached=True,
            route_complete=True,
            resolved_rest_node_ids=[
                node.node_id
                for node in route.nodes[:-1]
                if node.kind.value == "rest"
            ],
            current_contextual_route_phase="none",
        )
        document["world"]["defeated_encounters"] = [
            node.encounter_id
            for node in route.nodes[:-1]
            if node.encounter_id is not None
        ]
    return document


def test_old_schema8_disk_save_before_entrance_preserves_lead_gold():
    game = _create_populated_game("1")
    document = _old_schema8_document(game)

    restored = reconstruct_game_state(document)
    upgraded = build_save_document(restored)

    assert upgraded["schema_version"] == DISK_SCHEMA_VERSION == 9
    assert restored.player_state.gold == 17
    assert restored.party_state.shared_gold == 0
    assert restored.party_state.phase is DungeonPhase.OUTSIDE


def test_old_schema8_at_dungeon_entrance_moves_lead_gold_into_hub_once():
    game = _create_populated_game("1")
    game.player_state.add_gold(58)
    document = _old_schema8_document(game, at_dungeon_entrance=True)
    original = copy.deepcopy(document)

    restored = reconstruct_game_state(document)

    assert document == original
    assert restored.player_state.gold == 0
    assert restored.party_state.shared_gold == 75
    assert restored.party_state.phase is DungeonPhase.HUB
    assert build_save_document(restored)["party"]["shared_gold"] == 75


def test_schema8_runtime_party_snapshot_is_not_transferred_twice():
    game = _create_populated_game("1")
    game.player_state.add_gold(58)
    assert game.party_state.arrive_at_hub(game.player_state)
    document = _old_schema8_document(game, at_dungeon_entrance=True)
    document["party"] = game.party_state.snapshot()
    document["player"]["gold"] = 0

    restored = reconstruct_game_state(document)

    assert restored.player_state.gold == 0
    assert restored.party_state.shared_gold == 75
    assert restored.party_state.phase is DungeonPhase.HUB


def test_party_state_and_companion_round_trip_in_schema9_document():
    game = _create_populated_game("1")
    _move_game_to_dungeon_entrance(game)
    game.player_state.add_gold(58)
    assert game.party_state.arrive_at_hub(game.player_state)
    companion = next(profile for profile in DRIFTER_SPECS if profile.choice == "2")
    assert game.party_state.recruit_companion(
        game.player_state,
        PlayerState(companion.create_character()),
    )
    game.party_state.add_shared_gold(7)

    document = build_save_document(game)
    restored = reconstruct_game_state(document)

    assert document["schema_version"] == 9
    assert document["party"]["shared_gold"] == 17
    assert "combat" not in document["player"]
    assert all("combat" not in member for member in document["party"]["companions"])
    assert len(restored.party_state.companions) == 1
    assert restored.party_state.companions[0].character.profile.choice == "2"
    assert build_save_document(restored) == document


def test_party_hub_and_pending_outing_snapshot_round_trip():
    game = _create_populated_game("1")
    _move_game_to_dungeon_entrance(game)
    game.player_state.add_gold(58)
    assert game.party_state.arrive_at_hub(game.player_state)
    companion = next(profile for profile in DRIFTER_SPECS if profile.choice == "2")
    game.party_state.recruit_companion(
        game.player_state,
        PlayerState(companion.create_character()),
    )
    document = build_save_document(game)
    document["party"].update(
        phase="extraction",
        outing_rewards={
            "experience": 120,
            "gold": 9,
            "items": {"tonic": 2},
        },
    )

    restored = reconstruct_game_state(document)

    assert restored.party_state.phase is DungeonPhase.EXTRACTION
    assert restored.party_state.outing_rewards.snapshot() == {
        "experience": 120,
        "gold": 9,
        "items": {"tonic": 2},
    }
    assert build_save_document(restored) == document


@pytest.mark.parametrize(
    "mutator",
    (
        lambda party: party.update(shared_gold=True),
        lambda party: party["shared_items"].update({"tonic": 0}),
        lambda party: party["shared_items"].update({"": 1}),
        lambda party: party["companions"].append(copy.deepcopy(party["companions"][0])),
        lambda party: party.update(phase="unknown"),
        lambda party: party.update(phase="outing", companions=[]),
        lambda party: party.update(phase="outing"),
        lambda party: party.update(
            phase="hub",
            companions=[],
            tutorial_complete=True,
        ),
        lambda party: party.update(phase="hub", tutorial_complete=False),
        lambda party: party.update(
            phase="extraction",
            outing_rewards={"experience": 121, "gold": 9, "items": {}},
        ),
        lambda party: party["companions"].__setitem__(
            0, _create_populated_game("1").player_state.snapshot()
        ),
    ),
)
def test_invalid_party_documents_are_rejected(mutator):
    game = _create_populated_game("1")
    _move_game_to_dungeon_entrance(game)
    game.player_state.add_gold(58)
    assert game.party_state.arrive_at_hub(game.player_state)
    companion = next(profile for profile in DRIFTER_SPECS if profile.choice == "2")
    game.party_state.recruit_companion(
        game.player_state,
        PlayerState(companion.create_character()),
    )
    document = build_save_document(game)
    mutator(document["party"])

    with pytest.raises(SaveStateValidationError):
        reconstruct_game_state(document)


@pytest.mark.parametrize(
    "mutator",
    (
        lambda document: document.update(schema_version=6),
        lambda document: document.update(schema_version=10),
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


@pytest.mark.parametrize(
    "mutator",
    (
        lambda document: document["player"]["progression"].pop("exp"),
        lambda document: document["player"]["progression"].update(extra=0),
        lambda document: document["overworld"].update(
            current_route_node_id="surface_elite_patrol",
            surface_route_begun=True,
            current_contextual_route_phase="enter_encounter",
        ),
        lambda document: document["overworld"].update(
            current_route_node_id="surface_warrior_pair",
            surface_route_begun=True,
            current_contextual_route_phase="enter_encounter",
        ),
        lambda document: document["overworld"].update(
            current_contextual_route_phase="none",
        ),
    ),
)
def test_impossible_route_or_nested_shapes_fail_as_save_validation_errors(mutator):
    document = build_save_document(_create_populated_game("1"))
    mutator(document)

    with pytest.raises(SaveStateValidationError):
        reconstruct_game_state(document)


def test_snapshot_and_save_document_are_defensive():
    game = _create_populated_game("4")
    document = build_save_document(game)

    document["player"]["attributes"]["strength"] = 100
    document["world"]["defeated_encounters"].append("changed")
    document["metadata"]["run_id"] = "changed"

    assert game.player_state.stats.strength != 100
    assert game.world_state.defeated_encounters == ("surface_goblin_solo",)
    assert game.metadata == {"run_id": "run-4"}
