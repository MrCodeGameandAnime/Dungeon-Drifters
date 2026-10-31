import copy

import pytest

from app.game.game_state import GameState
from app.game.overworld_state import ContextualRoutePhase
from app.game.party_state import DungeonPhase
from app.persistence.save_document import (
    DISK_SCHEMA_VERSION,
    SaveStateValidationError,
    build_save_document,
    migrate_schema_7,
    reconstruct_game_state,
    validate_profile_payload,
    validate_save_document,
)
from app.content.catalog import create_weapon, get_route_spec
from app.player.character_run_state import (
    InfusionKind,
    PreparedPayloadId,
)
from app.player.player_state import PlayerState
from app.snapshot import STATE_SCHEMA_VERSION
from app.content.catalog import DRIFTER_SPECS
from tests.game_test_support import (
    advance_surface_to,
    completed_hub_game,
    enter_floor_one_rest,
    three_member_hub_game,
)


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
    advance_surface_to(game, get_route_spec("surface").nodes[-1].node_id)


def _game_at_floor_one_rest(rest_index=0):
    game = _create_populated_game("1")
    _move_game_to_dungeon_entrance(game)
    game.player_state.add_gold(58)
    assert game.party_state.arrive_at_hub(game.player_state)
    companion_profile = next(
        profile for profile in DRIFTER_SPECS if profile.choice == "2"
    )
    companion = PlayerState(companion_profile.create_character())
    assert game.party_state.recruit_companion(game.player_state, companion)
    party_members = (game.player_state, companion)
    assert game.party_state.begin_outing()
    assert game.party_state.begin_extraction(experience=0, gold=0)
    assert game.party_state.complete_extraction(party_members)
    enter_floor_one_rest(game, rest_index)
    game.party_state.add_floor_one_rewards(experience=70, gold=5)
    return game


def test_schema13_document_has_only_persistent_state_and_schema12_stays_runtime_only():
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


def test_new_saves_use_runtime_schema12_and_disk_schema13():
    game = GameState(PlayerState(DRIFTER_SPECS[0].create_character()))

    document = build_save_document(game)

    assert STATE_SCHEMA_VERSION == 12
    assert DISK_SCHEMA_VERSION == document["schema_version"] == 13
    assert document["overworld"]["active_route_id"] == "surface"
    assert document["party"]["floor_one_cleared"] is False
    assert document["party"]["floor_one_runs_started_after_clear"] == 0
    assert document["party"]["outing_xp_multiplier_percent"] == 100
    assert document["party"]["active_drifter_ids"] == ["branoc"]


def test_schema13_round_trip_preserves_four_member_roster_and_selected_pair():
    game = three_member_hub_game()
    zhaivra = next(profile for profile in DRIFTER_SPECS if profile.drifter_id == "zhaivra")
    assert game.party_state.recruit_companion(
        game.player_state,
        PlayerState(zhaivra.create_character()),
        cost=0,
    )
    recruited_ids = tuple(
        member.character.profile.drifter_id for member in game.recruited_members
    )
    game.party_state.select_active_pair(
        ("zhaivra", "azhvielle"),
        recruited_ids=recruited_ids,
    )
    for index, drifter_id in enumerate(recruited_ids, start=1):
        member = game.member_for_drifter_id(drifter_id)
        member.gain_experience(index * 100)
        slot_id = next(iter(member.signature_weapon_state.slot_progress))
        member.signature_weapon_state.set_slot_progress(slot_id, index * 3)

    document = build_save_document(game)
    restored = reconstruct_game_state(document)

    assert document["schema_version"] == 13
    assert document["party"]["active_drifter_ids"] == ["zhaivra", "azhvielle"]
    assert tuple(
        member.character.profile.drifter_id for member in restored.recruited_members
    ) == recruited_ids
    assert restored.party_state.active_drifter_ids == ("zhaivra", "azhvielle")
    assert restored.active_party_members == (
        restored.member_for_drifter_id("zhaivra"),
        restored.member_for_drifter_id("azhvielle"),
    )
    assert restored.player_state is restored.member_for_drifter_id("branoc")
    assert restored.member_for_drifter_id("branoc") is not game.player_state
    assert build_save_document(restored) == document


@pytest.mark.parametrize(
    "active_ids",
    (
        ["branoc", "branoc"],
        ["branoc", "zhaivra"],
        ["joruun"],
        ["branoc", "unrecruited"],
        [1, "azhvielle"],
        [],
        "branoc,azhvielle",
    ),
)
def test_schema13_rejects_invalid_active_member_selection(active_ids):
    game = three_member_hub_game()
    document = build_save_document(game)
    document["party"]["active_drifter_ids"] = active_ids

    with pytest.raises(SaveStateValidationError, match="active"):
        validate_profile_payload(document)


def test_schema12_pair_history_migrates_without_mutating_or_adding_recruits():
    historical = copy.deepcopy(build_save_document(completed_hub_game()))
    historical["schema_version"] = 12
    historical["party"].pop("active_drifter_ids")
    original = copy.deepcopy(historical)

    assert validate_profile_payload(historical) == original
    migrated = validate_save_document(historical)
    restored = reconstruct_game_state(historical)

    assert historical == original
    assert migrated["schema_version"] == 13
    assert migrated["party"]["active_drifter_ids"] == ["branoc", "azhvielle"]
    assert tuple(
        member.character.profile.drifter_id for member in restored.recruited_members
    ) == ("branoc", "azhvielle")
    assert restored.party_state.active_drifter_ids == ("branoc", "azhvielle")


def test_schema12_solo_history_migrates_to_only_the_starting_drifter():
    historical = copy.deepcopy(build_save_document(_create_populated_game("1")))
    historical["schema_version"] = 12
    historical["party"].pop("active_drifter_ids")
    original = copy.deepcopy(historical)

    restored = reconstruct_game_state(historical)

    assert historical == original
    assert restored.party_state.active_drifter_ids == ("branoc",)
    assert tuple(
        member.character.profile.drifter_id for member in restored.recruited_members
    ) == ("branoc",)


@pytest.mark.parametrize("rest_index", (0, 1))
def test_current_schema_floor_one_rest_checkpoint_round_trips(rest_index):
    game = _game_at_floor_one_rest(rest_index)

    document = build_save_document(game)
    restored = reconstruct_game_state(document)

    route = get_route_spec("floor_one")
    rest_node = tuple(
        node for node in route.nodes if node.kind.value == "rest"
    )[rest_index]
    assert document["schema_version"] == 13
    assert document["overworld"]["active_route_id"] == "floor_one"
    assert document["overworld"]["current_route_node_id"] == rest_node.node_id
    assert document["party"]["phase"] == "outing"
    assert document["party"]["outing_rewards"] == {
        "experience": 70,
        "gold": 5,
        "items": {},
    }
    assert build_save_document(restored) == document


def test_schema9_disk_payload_migrates_with_verified_original_shape_unchanged():
    game = _create_populated_game("1")
    old_payload = copy.deepcopy(build_save_document(game))
    old_payload["schema_version"] = 9
    old_payload["player"].pop("signature_weapon")
    old_payload["party"].pop("active_drifter_ids")
    old_payload["overworld"].pop("active_route_id", None)
    for field in (
        "floor_one_cleared",
        "floor_one_runs_started_after_clear",
        "outing_xp_multiplier_percent",
        "crafting_experience",
    ):
        old_payload["party"].pop(field, None)
    original = copy.deepcopy(old_payload)

    restored = reconstruct_game_state(old_payload)
    upgraded = build_save_document(restored)

    assert old_payload == original
    assert upgraded["schema_version"] == 13
    assert upgraded["overworld"]["active_route_id"] == "surface"
    assert upgraded["party"]["floor_one_cleared"] is False
    assert upgraded["party"]["floor_one_runs_started_after_clear"] == 0
    assert upgraded["party"]["outing_xp_multiplier_percent"] == 100


def test_schema10_profile_history_stays_immutable_and_load_upgrades_to_schema13():
    historical = copy.deepcopy(
        build_save_document(
            GameState(PlayerState(DRIFTER_SPECS[0].create_character()))
        )
    )
    historical["schema_version"] = 10
    historical["player"].pop("signature_weapon")
    historical["party"].pop("active_drifter_ids")
    original = copy.deepcopy(historical)

    assert validate_profile_payload(historical) == original
    upgraded = validate_save_document(historical)

    assert historical == original
    assert upgraded["schema_version"] == 13
    assert upgraded["player"]["signature_weapon"]["weapon_id"] == "sunder_spire"
    assert set(upgraded["player"]["signature_weapon"]["slot_progress"].values()) == {0}


def test_schema11_profile_history_stays_immutable_and_migrates_tier_five_default():
    historical = copy.deepcopy(
        build_save_document(
            GameState(PlayerState(DRIFTER_SPECS[0].create_character()))
        )
    )
    historical["schema_version"] = 11
    historical["player"]["signature_weapon"].pop("tier_v_success")
    historical["party"].pop("active_drifter_ids")
    original = copy.deepcopy(historical)

    assert validate_profile_payload(historical) == original
    upgraded = validate_save_document(historical)

    assert historical == original
    assert upgraded["schema_version"] == 13
    assert upgraded["player"]["signature_weapon"]["tier_v_success"] is False


@pytest.mark.parametrize("invalid_value", (None, 1, "false"))
def test_current_profile_payload_rejects_non_boolean_tier_five_state(invalid_value):
    document = build_save_document(
        GameState(PlayerState(DRIFTER_SPECS[0].create_character()))
    )
    document["player"]["signature_weapon"]["tier_v_success"] = invalid_value

    with pytest.raises(SaveStateValidationError, match="tier_v_success"):
        validate_profile_payload(document)


def test_floor_one_save_is_rejected_away_from_an_unresolved_rest():
    game = _game_at_floor_one_rest()
    game.overworld_state.record_resolved_rest_node("floor_one_midway_rest")
    route = get_route_spec("floor_one")
    second_battle = next(
        node for node in route.nodes if node.node_id == "floor_one_battle_06"
    )
    game.overworld_state.advance_to(
        second_battle.node_id,
        contextual_phase=ContextualRoutePhase.ENTER_ENCOUNTER,
    )

    with pytest.raises(SaveStateValidationError, match="only a Floor 1 Rest"):
        build_save_document(game)


@pytest.mark.parametrize(
    "mutator",
    (
        lambda document: document["party"].update(
            floor_one_runs_started_after_clear=1
        ),
        lambda document: document["party"].update(
            floor_one_cleared=True,
            floor_one_runs_started_after_clear=1,
            outing_xp_multiplier_percent=40,
        ),
        lambda document: document["overworld"].update(
            active_route_id="floor_one",
            current_route_node_id="floor_one_battle_06",
        ),
        lambda document: document["overworld"].update(
            resolved_rest_node_ids=["floor_one_midway_rest"],
        ),
        lambda document: document["party"].update(
            floor_one_cleared=True,
            tutorial_complete=False,
        ),
    ),
)
def test_invalid_floor_one_run_and_cursor_combinations_are_rejected(mutator):
    document = build_save_document(_game_at_floor_one_rest())
    mutator(document)

    with pytest.raises(SaveStateValidationError):
        reconstruct_game_state(document)


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
    schema7["player"].pop("signature_weapon")
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
    schema7["player"].pop("signature_weapon")
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
    document["overworld"].pop("active_route_id", None)
    document["player"].pop("combat")
    document["player"].pop("signature_weapon")
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

    assert upgraded["schema_version"] == DISK_SCHEMA_VERSION == 13
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
    for field in (
        "floor_one_cleared",
        "floor_one_runs_started_after_clear",
        "outing_xp_multiplier_percent",
        "crafting_experience",
    ):
        document["party"].pop(field)
    document["party"].pop("active_drifter_ids")
    document["player"]["gold"] = 0

    restored = reconstruct_game_state(document)

    assert restored.player_state.gold == 0
    assert restored.party_state.shared_gold == 75
    assert restored.party_state.phase is DungeonPhase.HUB


def test_party_state_and_companion_round_trip_in_schema13_document():
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

    assert document["schema_version"] == 13
    assert document["party"]["shared_gold"] == 17
    assert "combat" not in document["player"]
    assert all("combat" not in member for member in document["party"]["companions"])
    assert len(restored.party_state.companions) == 1
    assert restored.party_state.companions[0].character.profile.choice == "2"
    assert build_save_document(restored) == document


@pytest.mark.parametrize("member", ("lead", "companion"))
@pytest.mark.parametrize("invalid_component", ("unknown", "wrong_slot"))
def test_profile_payload_rejects_invalid_signature_weapon_components(
    member,
    invalid_component,
):
    game = _create_populated_game("1")
    if member == "companion":
        _move_game_to_dungeon_entrance(game)
        game.player_state.add_gold(58)
        assert game.party_state.arrive_at_hub(game.player_state)
        companion_profile = next(
            profile for profile in DRIFTER_SPECS if profile.choice == "2"
        )
        assert game.party_state.recruit_companion(
            game.player_state,
            PlayerState(companion_profile.create_character()),
        )

    document = build_save_document(game)
    player = (
        document["player"]
        if member == "lead"
        else document["party"]["companions"][0]
    )
    components = player["signature_weapon"]["components"]
    slot_ids = tuple(components)
    if invalid_component == "unknown":
        components[slot_ids[0]] = "definitely_not_a_component"
    else:
        components[slot_ids[0]] = components[slot_ids[1]]

    with pytest.raises(SaveStateValidationError, match="component"):
        validate_profile_payload(document)


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
            phase="complete",
            tutorial_complete=True,
        ),
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
        lambda document: document.update(schema_version=14),
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
