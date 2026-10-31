import pytest

from app.content.catalog import get_drifter_spec
from app.game.game_state import GameState
from app.game.party_state import DungeonPhase, PartyState
from app.player.player_state import PlayerState


def _player(drifter_id, *, gold=0):
    return PlayerState(
        get_drifter_spec(drifter_id).create_character(),
        gold=gold,
    )


def test_hub_entry_transfers_route_gold_once():
    lead = _player("branoc", gold=75)
    party = PartyState()

    assert party.arrive_at_hub(lead) is True
    assert party.shared_gold == 75
    assert lead.gold == 0
    assert party.phase is DungeonPhase.HUB

    assert party.arrive_at_hub(lead) is False
    assert party.shared_gold == 75
    assert lead.gold == 0


def test_crafting_progress_is_shared_and_levels_up_from_authored_points():
    party = PartyState()

    assert party.crafting_level == 1
    assert party.crafting_experience == 0
    assert party.add_crafting_experience(20) == 2
    assert party.crafting_level == 3
    assert party.snapshot()["crafting_experience"] == 20


def test_crafting_progress_survives_party_snapshot_round_trip():
    party = GameState(_player("branoc")).party_state
    party.add_crafting_experience(245)

    restored = PartyState.from_snapshot(
        party.snapshot(),
        companions=(),
        active_drifter_ids=party.active_drifter_ids,
    )

    assert restored.crafting_experience == 245
    assert restored.crafting_level == 25


def test_shared_material_spending_is_atomic_and_removes_empty_stacks():
    party = PartyState()
    party.add_shared_items({"grade_i_metal": 2, "grade_i_fiber": 1})

    assert party.spend_shared_items({"grade_i_metal": 1}) is True
    assert party.shared_items == {"grade_i_metal": 1, "grade_i_fiber": 1}
    before = party.shared_items

    assert party.spend_shared_items({"grade_i_metal": 2}) is False
    assert party.shared_items == before
    assert party.spend_shared_items({"grade_i_fiber": 1}) is True
    assert party.shared_items == {"grade_i_metal": 1}


@pytest.mark.parametrize("invalid", (-1, 991, True, "10"))
def test_party_snapshot_rejects_invalid_crafting_experience(invalid):
    snapshot = PartyState().snapshot()
    snapshot["crafting_experience"] = invalid

    with pytest.raises((TypeError, ValueError)):
        PartyState.from_snapshot(snapshot, companions=())


def test_recruiting_companion_spends_65_shared_gold_once():
    lead = _player("branoc", gold=75)
    companion = _player("azhvielle")
    party = PartyState()
    party.arrive_at_hub(lead)

    assert party.recruit_companion(lead, companion) is True

    assert party.companions == (companion,)
    assert party.shared_gold == 10
    assert lead.gold == 0
    assert party.phase is DungeonPhase.PARTY_READY


def test_recruitment_rejects_lead_and_duplicate_drifters_without_charging_again():
    lead = _player("branoc", gold=75)
    companion = _player("azhvielle")
    party = PartyState()
    party.arrive_at_hub(lead)
    before_lead = lead.snapshot()

    with pytest.raises(ValueError, match="lead Drifter"):
        party.recruit_companion(lead, lead)

    assert lead.snapshot() == before_lead
    assert party.shared_gold == 75
    assert party.companions == ()

    assert party.recruit_companion(lead, companion) is True
    before_duplicate = party.snapshot()

    with pytest.raises(ValueError, match="already recruited"):
        party.recruit_companion(
            lead,
            _player("azhvielle"),
        )

    assert party.snapshot() == before_duplicate


def test_unaffordable_recruitment_does_not_partially_mutate_state():
    lead = _player("branoc")
    companion = _player("joruun")
    party = PartyState()
    party.arrive_at_hub(lead)
    before = party.snapshot()

    assert party.recruit_companion(lead, companion) is False

    assert party.snapshot() == before
    assert lead.gold == 0
    assert companion not in party.companions


def test_from_snapshot_rejects_extraction_experience_not_divisible_by_party_size():
    lead = _player("branoc", gold=75)
    companion = _player("azhvielle")
    party = PartyState()
    party.arrive_at_hub(lead)
    assert party.recruit_companion(lead, companion)
    assert party.begin_outing()
    assert party.begin_extraction(experience=120, gold=9)
    snapshot = party.snapshot()
    snapshot["outing_rewards"]["experience"] = 121

    with pytest.raises(ValueError, match="divide evenly"):
        PartyState.from_snapshot(snapshot, companions=(companion,))

