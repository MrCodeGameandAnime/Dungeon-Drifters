import pytest

from app.content.catalog import get_drifter_spec
from app.game.game_state import GameState
from app.game.party_state import DungeonPhase, PartyState
from app.player.player_state import PlayerState
from app.player.progression import xp_required_for_next_level
from game_test_support import completed_hub_game


def _player(drifter_id, *, gold=0):
    return PlayerState(
        get_drifter_spec(drifter_id).create_character(),
        gold=gold,
    )


def _total_xp(member):
    return sum(
        xp_required_for_next_level(level)
        for level in range(1, member.level_state.current)
    ) + member.exp_state.current


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


def test_carried_supplies_load_from_secured_storage_with_six_unit_capacity():
    lead = _player("branoc", gold=75)
    party = PartyState()
    party.arrive_at_hub(lead)
    party.add_shared_items({"healing_potion": 4, "smoke_bomb": 2, "return_talisman": 1})

    assert party.load_carried_supplies(
        {"healing_potion": 3, "smoke_bomb": 2, "return_talisman": 1}
    ) is True
    assert party.carried_items == {
        "healing_potion": 3,
        "smoke_bomb": 2,
        "return_talisman": 1,
    }
    assert party.carried_item_units == 6
    assert party.shared_items == {"healing_potion": 1}


def test_carried_supply_load_rejects_over_capacity_or_missing_items_atomically():
    lead = _player("branoc", gold=75)
    party = PartyState()
    party.arrive_at_hub(lead)
    party.add_shared_items({"healing_potion": 8})
    before = party.snapshot()

    assert party.load_carried_supplies({"healing_potion": 7}) is False
    assert party.load_carried_supplies({"healing_potion": 2, "smoke_bomb": 1}) is False
    assert party.snapshot() == before


def test_pack_only_accepts_authored_carryable_supplies_and_can_unload_at_hub():
    lead = _player("branoc", gold=75)
    party = PartyState()
    party.arrive_at_hub(lead)
    party.add_shared_items({"healing_potion": 2, "grade_i_metal": 1})

    assert party.load_carried_supplies({"grade_i_metal": 1}) is False
    assert party.load_carried_supplies({"unknown_supply": 1}) is False
    assert party.shared_items == {"healing_potion": 2, "grade_i_metal": 1}

    assert party.load_carried_supplies({"healing_potion": 2}) is True
    assert party.unload_carried_supplies({"healing_potion": 1}) is True
    assert party.shared_items == {"healing_potion": 1, "grade_i_metal": 1}
    assert party.carried_items == {"healing_potion": 1}


def test_pack_unload_rejects_missing_items_and_outing_mutation():
    party = completed_hub_game().party_state
    party.add_shared_items({"healing_potion": 1})
    assert party.load_carried_supplies({"healing_potion": 1})
    before = party.snapshot()

    assert party.unload_carried_supplies({"healing_potion": 2}) is False
    assert party.snapshot() == before
    assert party.start_floor_one_run() == 100
    before = party.snapshot()
    assert party.unload_carried_supplies({"healing_potion": 1}) is False
    assert party.snapshot() == before


def test_carried_supplies_consume_return_and_discard_without_duplication():
    lead = _player("branoc", gold=75)
    party = PartyState()
    party.arrive_at_hub(lead)
    party.add_shared_items({"healing_potion": 3, "smoke_bomb": 2})
    assert party.load_carried_supplies({"healing_potion": 2, "smoke_bomb": 1})

    assert party.consume_carried_supplies({"healing_potion": 1}) is True
    assert party.consume_carried_supplies({"healing_potion": 2}) is False
    assert party.carried_items == {"healing_potion": 1, "smoke_bomb": 1}

    party.return_carried_supplies()
    assert party.shared_items == {"healing_potion": 2, "smoke_bomb": 2}
    assert party.carried_items == {}

    assert party.load_carried_supplies({"healing_potion": 1})
    party.discard_carried_supplies()
    assert party.shared_items == {"healing_potion": 1, "smoke_bomb": 2}
    assert party.carried_items == {}


def test_healing_potion_targets_deployed_drifter_with_floor_rounding():
    game = completed_hub_game()
    party = game.party_state
    lead, companion = game.active_party_members
    party.add_shared_items({"healing_potion": 2})
    assert party.load_carried_supplies({"healing_potion": 2})
    assert party.start_floor_one_run() == 100
    lead.health.take_damage(90)
    companion.health.take_damage(30)

    assert party.use_healing_potion(lead, deployed_members=(lead, companion)) is True

    assert lead.health.current == 26 + (lead.health.maximum * 40 // 100)
    assert companion.health.current == companion.health.maximum - 30
    assert party.carried_items == {"healing_potion": 1}


@pytest.mark.parametrize("target_kind", ("full", "dead", "undeployed"))
def test_healing_potion_rejection_does_not_mutate_state(target_kind):
    game = completed_hub_game()
    party = game.party_state
    lead, companion = game.active_party_members
    party.add_shared_items({"healing_potion": 1})
    assert party.load_carried_supplies({"healing_potion": 1})
    assert party.start_floor_one_run() == 100
    if target_kind == "full":
        target = companion
    elif target_kind == "dead":
        companion.health.take_damage(companion.health.maximum)
        target = companion
    else:
        target = PlayerState(get_drifter_spec("joruun").create_character())
        target.health.take_damage(10)
    before = party.snapshot()
    before_hp = tuple(member.health.current for member in game.recruited_members)

    assert party.use_healing_potion(target, deployed_members=(lead, companion)) is False

    assert party.snapshot() == before
    assert tuple(member.health.current for member in game.recruited_members) == before_hp


def test_carried_supplies_round_trip_and_snapshot_validation():
    lead = _player("branoc", gold=75)
    party = GameState(lead).party_state
    party.arrive_at_hub(lead)
    party.add_shared_items({"healing_potion": 2})
    assert party.load_carried_supplies({"healing_potion": 1})

    restored = PartyState.from_snapshot(
        party.snapshot(), companions=(), active_drifter_ids=party.active_drifter_ids
    )
    assert restored.carried_items == {"healing_potion": 1}

    invalid = party.snapshot()
    invalid["carried_items"] = {"healing_potion": 7}
    with pytest.raises(ValueError, match="capacity"):
        PartyState.from_snapshot(invalid, companions=())

    invalid["carried_items"] = {"grade_i_metal": 1}
    with pytest.raises(ValueError, match="carryable"):
        PartyState.from_snapshot(invalid, companions=())


def test_floor_one_safe_boss_return_banks_pack_and_death_discards_it():
    game = completed_hub_game()
    party = game.party_state
    members = game.active_party_members
    party.add_shared_items({"healing_potion": 2})
    assert party.load_carried_supplies({"healing_potion": 1})
    assert party.start_floor_one_run() == 100
    party.add_floor_one_rewards(experience=20, gold=5)

    assert party.complete_floor_one_boss(members)
    assert party.shared_items == {"healing_potion": 2}
    assert party.carried_items == {}

    party.add_shared_items({"healing_potion": 1})
    assert party.load_carried_supplies({"healing_potion": 1})
    assert party.start_floor_one_run() == 50
    party.add_floor_one_rewards(experience=20, gold=5)

    assert party.fail_floor_one_run(members)
    assert party.shared_items == {"healing_potion": 2}
    assert party.carried_items == {}


def test_return_talisman_banks_adjusted_xp_only_and_returns_unused_supplies():
    game = completed_hub_game()
    party = game.party_state
    members = game.active_party_members
    party.add_shared_items(
        {"return_talisman": 1, "healing_potion": 2, "smoke_bomb": 1}
    )
    assert party.load_carried_supplies(
        {"return_talisman": 1, "healing_potion": 1, "smoke_bomb": 1}
    )
    assert party.start_floor_one_run() == 100
    party.add_floor_one_rewards(
        experience=101,
        gold=25,
        items={"goblin_scrap": 2},
    )
    xp_before = tuple(_total_xp(member) for member in members)

    assert party.return_with_talisman(members) is True

    assert tuple(_total_xp(member) for member in members) == tuple(
        total + 50 for total in xp_before
    )
    assert party.shared_gold == 10
    assert party.shared_items == {
        "healing_potion": 2,
        "smoke_bomb": 1,
    }
    assert party.carried_items == {}
    assert party.outing_rewards.experience == 0
    assert party.phase is DungeonPhase.HUB
    assert party.return_with_talisman(members) is False
    assert tuple(_total_xp(member) for member in members) == tuple(
        total + 50 for total in xp_before
    )


def test_return_talisman_rejects_without_talisman_or_outing_without_mutation():
    game = completed_hub_game()
    party = game.party_state
    members = game.active_party_members
    assert party.start_floor_one_run() == 100
    party.add_floor_one_rewards(experience=20, gold=5, items={"goblin_scrap": 1})
    before = party.snapshot()
    xp_before = tuple(_total_xp(member) for member in members)

    assert party.return_with_talisman(members) is False
    assert party.snapshot() == before
    assert tuple(_total_xp(member) for member in members) == xp_before


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

