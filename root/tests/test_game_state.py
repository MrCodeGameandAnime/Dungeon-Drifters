import pytest

from app.content.catalog import create_drifter, get_drifter_spec
from app.game.game_state import GameState
from app.game.overworld_state import OverworldState
from app.game.story_state import StoryState
from app.game.world_state import WorldState
from app.player.player_state import PlayerState



def test_valid_player_state_constructs_game_state():
    player_state = PlayerState(create_drifter("branoc"))
    game_state = GameState(player_state)

    assert game_state.player_state is player_state
    assert isinstance(game_state.story_state, StoryState)
    assert isinstance(game_state.world_state, WorldState)
    assert isinstance(game_state.overworld_state, OverworldState)
    assert game_state.metadata == {}


def test_new_game_has_empty_dungeon_party_progress():
    game_state = GameState(PlayerState(create_drifter("branoc")))

    party = game_state.party_state

    assert party.companions == ()
    assert party.shared_gold == 0
    assert party.shared_items == {}
    assert party.tutorial_complete is False
    assert party.phase.value == "outside"
    assert party.outing_rewards.experience == 0
    assert party.outing_rewards.gold == 0
    assert party.outing_rewards.items == {}


def test_invalid_player_state_is_rejected():
    with pytest.raises(TypeError):
        GameState(create_drifter("branoc"))
    with pytest.raises(TypeError):
        GameState(None)


def test_ownership_properties_cannot_be_replaced():
    game_state = GameState(PlayerState(create_drifter("branoc")))

    with pytest.raises(AttributeError):
        setattr(game_state, "player_state", None)
    with pytest.raises(AttributeError):
        setattr(game_state, "story_state", None)
    with pytest.raises(AttributeError):
        setattr(game_state, "world_state", None)
    with pytest.raises(AttributeError):
        setattr(game_state, "overworld_state", None)
    with pytest.raises(AttributeError):
        setattr(game_state, "party_state", None)
    with pytest.raises(AttributeError):
        setattr(game_state, "metadata", {})


def test_metadata_snapshot_cannot_mutate_internal_metadata():
    game_state = GameState(PlayerState(create_drifter("branoc")))
    game_state.set_metadata("run_mode", "test")

    metadata = game_state.metadata
    metadata["run_mode"] = "changed"
    metadata["extra"] = True

    assert game_state.metadata == {"run_mode": "test"}


def test_game_state_instances_do_not_share_state_containers():
    first = GameState(PlayerState(create_drifter("branoc")))
    second = GameState(PlayerState(create_drifter("branoc")))

    first.set_metadata("session", "first")
    first.story_state.add_story_flag("met_goblin")
    first.world_state.discover_location("woods")
    first.party_state.add_shared_gold(12)

    assert first.metadata == {"session": "first"}
    assert second.metadata == {}
    assert first.story_state is not second.story_state
    assert first.world_state is not second.world_state
    assert first.overworld_state is not second.overworld_state
    assert first.party_state is not second.party_state
    assert first.story_state.story_flags == ("met_goblin",)
    assert second.story_state.story_flags == ()
    assert first.world_state.discovered_locations == ("woods",)
    assert second.world_state.discovered_locations == ()
    assert first.party_state.shared_gold == 12
    assert second.party_state.shared_gold == 0


def _three_member_hub_game():
    lead = PlayerState(
        get_drifter_spec("branoc").create_character(),
        gold=75,
    )
    game = GameState(lead)
    party = game.party_state
    companion = PlayerState(get_drifter_spec("azhvielle").create_character())

    assert party.arrive_at_hub(lead)
    assert party.recruit_companion(lead, companion)
    assert party.begin_outing()
    assert party.begin_extraction(experience=120, gold=9)
    assert party.complete_extraction((lead, companion))
    assert party.recruit_companion(
        lead,
        PlayerState(get_drifter_spec("joruun").create_character()),
        cost=0,
    )
    return game


def test_recruited_members_are_unique_and_active_ids_resolve_canonical_objects():
    game = _three_member_hub_game()

    assert tuple(
        member.character.profile.drifter_id
        for member in game.recruited_members
    ) == ("branoc", "azhvielle", "joruun")
    assert game.member_for_drifter_id("branoc") is game.player_state
    assert game.member_for_drifter_id("azhvielle") is game.party_state.companions[0]
    assert game.member_for_drifter_id("joruun") is game.party_state.companions[1]
    assert game.active_party_members == (
        game.member_for_drifter_id("branoc"),
        game.member_for_drifter_id("azhvielle"),
    )

    with pytest.raises(ValueError, match="not recruited"):
        game.member_for_drifter_id("zhaivra")


@pytest.mark.parametrize(
    "selection",
    (("azhvielle", "azhvielle"), ("azhvielle", "zhaivra")),
)
def test_selection_rejects_duplicate_or_unrecruited_ids_without_mutation(selection):
    game = _three_member_hub_game()
    party = game.party_state
    before_snapshot = party.snapshot()
    before_active_ids = party.active_drifter_ids

    with pytest.raises(ValueError):
        party.select_active_pair(
            selection,
            recruited_ids=tuple(
                member.character.profile.drifter_id
                for member in game.recruited_members
            ),
        )

    assert party.snapshot() == before_snapshot
    assert party.active_drifter_ids == before_active_ids


def test_original_identity_does_not_change_when_active_order_changes():
    game = _three_member_hub_game()
    original = game.player_state

    game.party_state.select_active_pair(
        ("joruun", "azhvielle"),
        recruited_ids=tuple(
            member.character.profile.drifter_id
            for member in game.recruited_members
        ),
    )

    assert game.player_state is original
    assert game.player_state.character.profile.drifter_id == "branoc"
    assert game.party_state.active_drifter_ids == ("joruun", "azhvielle")
    assert game.active_party_members == (
        game.member_for_drifter_id("joruun"),
        game.member_for_drifter_id("azhvielle"),
    )


def test_game_clone_preserves_active_order_and_canonical_roster_identity():
    game = _three_member_hub_game()
    game.party_state.select_active_pair(
        ("joruun", "azhvielle"),
        recruited_ids=tuple(
            member.character.profile.drifter_id
            for member in game.recruited_members
        ),
    )

    clone = game.clone()

    assert clone.party_state.active_drifter_ids == ("joruun", "azhvielle")
    assert clone.active_party_members == (
        clone.member_for_drifter_id("joruun"),
        clone.member_for_drifter_id("azhvielle"),
    )
    assert clone.player_state is not game.player_state
    assert clone.member_for_drifter_id("joruun") is not game.member_for_drifter_id("joruun")
