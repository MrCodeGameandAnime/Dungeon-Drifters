from itertools import combinations

from app.content.catalog import DRIFTER_SPECS
from app.content.region_progression_spec import M8_ASHEN_ARENA_REVEALED_EVENT_ID
from app.game.region_progression import (
    destination_availability,
    confirm_destination_entry,
    is_drowned_reliquary_briefing_available,
    is_reunion_boss_eligible,
    portal_regions,
    reunion_boss_unavailable_reason,
    visible_destinations,
)
from app.game.story_state import KnowledgeStatus
from tests.game_test_support import completed_hub_game
from app.player.player_state import PlayerState


def _four_member_game():
    game = completed_hub_game()
    recruited_ids = {
        member.character.profile.drifter_id for member in game.recruited_members
    }
    for profile in DRIFTER_SPECS:
        if profile.drifter_id in recruited_ids:
            continue
        assert game.party_state.recruit_companion(
            game.player_state,
            PlayerState(profile.create_character()),
            cost=0,
        )
    return game


def test_region_two_is_hidden_until_durable_unlock_then_visible_unavailable():
    game = completed_hub_game()

    assert tuple(region.region_id for region in portal_regions(game)) == ("region_1",)

    game.party_state._floor_four_cleared = True
    assert game.party_state.record_floor_five_clear()
    assert game.party_state.unlock_region_two()
    region_two = portal_regions(game)[1]

    assert region_two.region_id == "region_2"
    assert region_two.unlocked
    assert not region_two.selectable
    assert "no playable" in region_two.message.lower()
    assert visible_destinations(game, "region_2") == ()


def test_unknown_destinations_are_not_named_until_their_rumor_is_revealed():
    game = _four_member_game()
    game.party_state._floor_three_cleared = True

    assert tuple(
        destination.destination_id
        for destination in visible_destinations(game, "region_1")
    ) == ("floor_one", "floor_two", "floor_three")

    game.story_state.reveal_knowledge_fact(
        "m8_fact_drowned_reliquary",
        KnowledgeStatus.RUMORED,
    )
    visible = visible_destinations(game, "region_1")

    assert tuple(destination.destination_id for destination in visible) == (
        "floor_one",
        "floor_two",
        "floor_three",
        "drowned_reliquary",
    )
    drowned = destination_availability(game, "drowned_reliquary")
    assert drowned.knowledge_status is KnowledgeStatus.RUMORED
    assert drowned.enabled


def test_confirmed_destination_fact_advances_only_when_route_is_enterable():
    game = _four_member_game()
    game.story_state.reveal_knowledge_fact(
        "m8_fact_drowned_reliquary",
        KnowledgeStatus.RUMORED,
    )

    assert not confirm_destination_entry(game, "drowned_reliquary")
    assert game.story_state.knowledge_status(
        "m8_fact_drowned_reliquary"
    ) is KnowledgeStatus.RUMORED

    game.party_state._floor_three_cleared = True
    assert confirm_destination_entry(game, "drowned_reliquary")
    assert game.story_state.knowledge_status(
        "m8_fact_drowned_reliquary"
    ) is KnowledgeStatus.CONFIRMED
    assert not confirm_destination_entry(game, "drowned_reliquary")


def test_existing_floor_prerequisites_and_route_availability_are_authoritative():
    game = completed_hub_game()

    assert destination_availability(game, "floor_one").enabled
    assert not destination_availability(game, "floor_two").enabled
    assert not destination_availability(game, "floor_three").enabled

    game.party_state._floor_one_cleared = True
    assert destination_availability(game, "floor_two").enabled
    game.party_state._floor_two_cleared = True
    assert "recruit" in destination_availability(game, "floor_three").reason.lower()

    four_member = _four_member_game()
    four_member.party_state._floor_one_cleared = True
    four_member.party_state._floor_two_cleared = True
    assert destination_availability(four_member, "floor_three").enabled


def test_ashen_vault_requires_floor_four_clear_and_rumored_knowledge():
    game = _four_member_game()
    party = game.party_state
    party._floor_three_cleared = True
    game.story_state.reveal_knowledge_fact(
        "m8_fact_drowned_reliquary", KnowledgeStatus.RUMORED
    )

    recruited_ids = tuple(
        member.character.profile.drifter_id for member in game.recruited_members
    )
    for pair in combinations(recruited_ids, 2):
        party.select_active_pair(pair, recruited_ids=recruited_ids)
        destination = destination_availability(game, "drowned_reliquary")
        assert destination.enabled

    game.story_state.reveal_knowledge_fact(
        "m8_fact_ashen_vault", KnowledgeStatus.RUMORED
    )
    ashen_vault = destination_availability(game, "ashen_vault")
    assert not ashen_vault.enabled
    assert "floor iv" in ashen_vault.reason.lower()

    party._floor_four_cleared = True
    ashen_vault = destination_availability(game, "ashen_vault")
    assert ashen_vault.enabled

    game.story_state._knowledge_facts.pop("m8_fact_ashen_vault")
    assert not destination_availability(game, "ashen_vault").visible


def test_briefing_requires_floor_three_clear_and_four_permanent_recruits():
    game = _four_member_game()

    assert not is_drowned_reliquary_briefing_available(game)
    game.party_state._floor_three_cleared = True
    assert is_drowned_reliquary_briefing_available(game)
    game.story_state.complete_event("m8_drowned_reliquary_briefing")
    assert not is_drowned_reliquary_briefing_available(game)

    two_member = completed_hub_game()
    two_member.party_state._floor_three_cleared = True
    assert not is_drowned_reliquary_briefing_available(two_member)


def test_floor_three_destination_is_blocked_while_expedition_is_active():
    game = _four_member_game()
    game.party_state._floor_two_cleared = True
    game.expedition_state._active_assignment = {
        "category": "training",
        "destination_floor_id": "floor_one",
        "expedition_drifter_ids": ["joruun", "zhaivra"],
        "started_at_utc": "2026-11-23T12:00:00+00:00",
        "duration_seconds": 1200,
    }

    destination = destination_availability(game, "floor_three")

    assert not destination.enabled
    assert "assignment" in destination.reason.lower()


def test_reunion_requires_arena_reveal_four_recruits_and_no_assignment():
    game = _four_member_game()
    assert not is_reunion_boss_eligible(game)
    assert "arena" in reunion_boss_unavailable_reason(game).lower()

    game.party_state._floor_three_cleared = True
    game.party_state._floor_four_cleared = True
    game.story_state.complete_event(M8_ASHEN_ARENA_REVEALED_EVENT_ID)
    assert not is_reunion_boss_eligible(game)
    assert "route" in reunion_boss_unavailable_reason(game).lower()

    game.expedition_state._active_assignment = {
        "category": "training",
        "destination_floor_id": "floor_one",
        "expedition_drifter_ids": ["joruun", "zhaivra"],
        "started_at_utc": "2026-11-23T12:00:00+00:00",
        "duration_seconds": 1200,
    }
    assert not is_reunion_boss_eligible(game)
    assert "assignment" in reunion_boss_unavailable_reason(game).lower()
