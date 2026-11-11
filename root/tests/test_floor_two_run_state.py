import pytest

from app.game.game_state import GameState
from app.game.party_state import DungeonPhase, PartyState
from app.game.world_state import WorldState
from app.items.equipment import EquipmentInstance
from app.persistence.save_document import (
    build_save_document,
    reconstruct_game_state,
)
from tests.game_test_support import completed_hub_game, three_member_hub_game


def floor_one_cleared_game():
    game = completed_hub_game()
    party = game.party_state
    assert party.start_floor_one_run() == 100
    assert party.complete_floor_one_boss(game.active_party_members)
    return game


def floor_two_game_with_benched_lead(*, carry_talisman=False):
    game = three_member_hub_game()
    party = game.party_state
    party.select_active_pair(
        ("azhvielle", "joruun"),
        recruited_ids=("branoc", "azhvielle", "joruun"),
    )
    assert party.start_floor_one_run() == 100
    assert party.complete_floor_one_boss(game.active_party_members)
    if carry_talisman:
        party.add_shared_items({"return_talisman": 1})
        assert party.load_carried_supplies({"return_talisman": 1})
    assert party.start_floor_two_run(run_id_factory=lambda: "equipment-run") == 100
    game.overworld_state.begin_route("floor_two")
    return game


def add_test_armor(game, *, instance_id, definition_id, secured, owner_id):
    armor = EquipmentInstance.create(
        instance_id=instance_id,
        definition_id=definition_id,
        source_id="floor_two_armor_reward",
        secured=secured,
        stat_bonuses={"constitution": 1},
        rarity="uncommon",
        modifier_slots={"I": "bastion_grade_i"},
    )
    game.party_state.add_equipment_instance(armor)
    owner = game.member_for_drifter_id(owner_id)
    refs = owner.equipped_equipment_ids
    refs[armor.slot_id] = armor.instance_id
    owner._set_equipped_equipment_ids(refs)
    game._bind_equipment_state()
    return armor


def test_floor_two_run_identity_is_new_for_each_genuine_run():
    game = floor_one_cleared_game()
    first_party = game.party_state

    assert "floor_two_run_id" in first_party.snapshot()
    assert first_party.start_floor_two_run(run_id_factory=lambda: "run-one") == 100
    first_id = first_party.floor_two_run_id
    assert first_id == "run-one"
    assert first_party.phase is DungeonPhase.OUTING

    assert first_party.fail_floor_two_run(game.active_party_members)
    assert first_party.start_floor_two_run(run_id_factory=lambda: "run-two") == 100
    assert first_party.floor_two_run_id == "run-two"
    assert first_party.floor_two_run_id != first_id


def test_default_floor_two_run_factory_persists_a_canonical_uuid_string():
    game = floor_one_cleared_game()

    game.party_state.start_floor_two_run()

    run_id = game.party_state.floor_two_run_id
    assert isinstance(run_id, str)
    assert len(run_id) == 36
    assert run_id.count("-") == 4


def test_floor_two_safe_encounter_checkpoint_round_trips_run_and_route_cursor():
    game = floor_one_cleared_game()
    assert game.party_state.start_floor_two_run(
        run_id_factory=lambda: "floor-two-checkpoint"
    ) == 100
    game.overworld_state.begin_route("floor_two")

    restored = reconstruct_game_state(build_save_document(game))

    assert restored.party_state.floor_two_run_id == "floor-two-checkpoint"
    assert restored.overworld_state.active_route_id == "floor_two"
    assert restored.overworld_state.current_route_node_id == "floor_two_battle_01"
    assert restored.party_state.phase is DungeonPhase.OUTING


def test_failed_floor_two_run_discards_its_event_evidence():
    game = floor_one_cleared_game()
    party = game.party_state
    assert party.start_floor_two_run(
        run_id_factory=lambda: "reused-floor-two-run"
    ) == 100
    party.record_run_event(
        {
            "event_key": (
                "floor_two:reused-floor-two-run:floor_two_pre_boss_rest:"
                "discovery_search"
            ),
            "run_id": "reused-floor-two-run",
            "floor_id": "floor_two",
            "node_id": "floor_two_pre_boss_rest",
            "kind": "discovery_search",
            "position": None,
            "result": {
                "source_id": "ancient_well_floor2_01",
                "searcher_drifter_id": "branoc",
                "effective_chance_bps": 1000,
                "roll": 10000,
                "found": False,
            },
        }
    )
    assert party.fail_floor_two_run(game.active_party_members)

    assert party.resolved_run_events == ()
    assert party.start_floor_two_run(
        run_id_factory=lambda: "retry-floor-two-run"
    ) == 100
    assert party.floor_two_run_id == "retry-floor-two-run"
    assert party.floor_two_run_id != "reused-floor-two-run"


def test_floor_two_event_evidence_is_kept_until_each_run_settlement():
    def add_search_evidence(party, run_id):
        party.record_run_event({
            "event_key": (
                f"floor_two:{run_id}:floor_two_pre_boss_rest:discovery_search"
            ),
            "run_id": run_id,
            "floor_id": "floor_two",
            "node_id": "floor_two_pre_boss_rest",
            "kind": "discovery_search",
            "position": None,
            "result": {
                "source_id": "ancient_well_floor2_01",
                "searcher_drifter_id": "branoc",
                "effective_chance_bps": 1000,
                "roll": 10000,
                "found": False,
            },
        })

    game = floor_one_cleared_game()
    party = game.party_state
    assert party.start_floor_two_run(run_id_factory=lambda: "retained-search") == 100
    add_search_evidence(party, "retained-search")
    assert len(party.resolved_run_events) == 1
    assert party.fail_floor_two_run(game.active_party_members)
    assert party.resolved_run_events == ()

    assert party.start_floor_two_run(run_id_factory=lambda: "extract-search") == 100
    add_search_evidence(party, "extract-search")
    assert party.begin_floor_two_extraction(partial=True)
    assert len(party.resolved_run_events) == 1
    restored = reconstruct_game_state(build_save_document(game))
    assert len(restored.party_state.resolved_run_events) == 1
    assert party.complete_floor_two_extraction(game.active_party_members)
    assert party.resolved_run_events == ()

    party.add_shared_items({"return_talisman": 1})
    assert party.load_carried_supplies({"return_talisman": 1})
    assert party.start_floor_two_run(run_id_factory=lambda: "talisman-search") == 100
    add_search_evidence(party, "talisman-search")
    assert party.return_with_talisman(game.active_party_members)
    assert party.resolved_run_events == ()

    assert party.start_floor_two_run(run_id_factory=lambda: "boss-search") == 100
    add_search_evidence(party, "boss-search")
    assert party.resolved_run_events
    assert party.complete_floor_two_boss(game.active_party_members)
    assert party.resolved_run_events == ()


def test_floor_two_run_identity_requires_the_floor_one_unlock():
    game = completed_hub_game()

    try:
        game.party_state.start_floor_two_run(run_id_factory=lambda: "locked-run")
    except ValueError as error:
        assert "Floor 1" in str(error)
    else:
        raise AssertionError("Floor II started before Floor I was cleared")


def test_floor_two_partial_extraction_banks_half_rewards_and_returns_supplies():
    game = floor_one_cleared_game()
    party = game.party_state
    initial_gold = party.shared_gold
    party.add_shared_items({"smoke_bomb": 1})
    assert party.load_carried_supplies({"smoke_bomb": 1})
    assert party.start_floor_two_run(run_id_factory=lambda: "extract-run") == 100
    party.add_floor_two_rewards(
        experience=100,
        gold=11,
        items={"goblin_scrap": 2},
    )
    members = game.active_party_members
    initial_xp = tuple(member.exp_state.current for member in members)
    expected_awards = party.secured_xp_awards(members, 50)

    assert party.begin_floor_two_extraction(partial=True)
    assert party.phase is DungeonPhase.EXTRACTION
    assert party.outing_rewards.snapshot() == {
        "experience": 50,
        "gold": 6,
        "items": {"goblin_scrap": 2},
    }

    restored = reconstruct_game_state(build_save_document(game))
    assert restored.party_state.floor_two_run_id == "extract-run"
    assert restored.party_state.phase is DungeonPhase.EXTRACTION

    assert party.complete_floor_two_extraction(members)
    assert party.phase is DungeonPhase.HUB
    assert party.floor_two_run_id is None
    assert party.shared_gold == initial_gold + 6
    assert party.shared_items == {"goblin_scrap": 2, "smoke_bomb": 1}
    assert party.carried_items == {}
    assert tuple(
        member.exp_state.current - old for member, old in zip(members, initial_xp)
    ) == expected_awards


@pytest.mark.parametrize("settlement", ("extraction", "boss"))
def test_safe_floor_two_settlement_secures_generated_armor_and_preserves_loadout(
    settlement,
):
    game = floor_two_game_with_benched_lead()
    party = game.party_state
    active = game.active_party_members
    found = add_test_armor(
        game,
        instance_id="00000000-0000-4000-8000-000000000801",
        definition_id="field_helm",
        secured=False,
        owner_id="azhvielle",
    )
    preexisting = add_test_armor(
        game,
        instance_id="00000000-0000-4000-8000-000000000802",
        definition_id="field_chest",
        secured=True,
        owner_id="branoc",
    )

    if settlement == "extraction":
        party.add_floor_two_rewards(experience=40, gold=5)
        assert party.begin_floor_two_extraction(partial=True)
        assert party.complete_floor_two_extraction(
            active,
        )
    else:
        party.add_floor_two_rewards(experience=40, gold=5)
        assert party.complete_floor_two_boss(
            active,
        )

    banked = party.equipment_instance(found.instance_id)
    kept = party.equipment_instance(preexisting.instance_id)
    assert banked.secured is True
    assert banked.modifier_slots == {"I": "bastion_grade_i"}
    assert kept.snapshot() == preexisting.snapshot()
    assert game.member_for_drifter_id("azhvielle").equipped_equipment_ids[
        "helm"
    ] == found.instance_id
    assert game.member_for_drifter_id("branoc").equipped_equipment_ids[
        "chest"
    ] == preexisting.instance_id


@pytest.mark.parametrize("exit_kind", ("defeat", "talisman"))
def test_dangerous_floor_two_exit_discards_only_unsecured_armor_and_clears_roster_refs(
    exit_kind,
):
    game = floor_two_game_with_benched_lead(
        carry_talisman=exit_kind == "talisman"
    )
    party = game.party_state
    active = game.active_party_members
    lost = add_test_armor(
        game,
        instance_id="00000000-0000-4000-8000-000000000811",
        definition_id="field_helm",
        secured=False,
        owner_id="branoc",
    )
    kept = add_test_armor(
        game,
        instance_id="00000000-0000-4000-8000-000000000812",
        definition_id="field_chest",
        secured=True,
        owner_id="azhvielle",
    )
    party.add_floor_two_rewards(
        experience=40,
        gold=5,
        items={"goblin_scrap": 2},
    )

    if exit_kind == "defeat":
        assert party.fail_floor_two_run(
            active,
            recruited_members=game.recruited_members,
        )
    else:
        assert party.return_with_talisman(
            active,
            recruited_members=game.recruited_members,
        )

    assert tuple(item.instance_id for item in party.equipment_instances) == (
        kept.instance_id,
    )
    assert party.equipment_instance(kept.instance_id).snapshot() == kept.snapshot()
    assert game.member_for_drifter_id("branoc").equipped_equipment_ids[
        "helm"
    ] is None
    assert game.member_for_drifter_id("azhvielle").equipped_equipment_ids[
        "chest"
    ] == kept.instance_id
    assert lost.instance_id != kept.instance_id


def test_floor_two_return_talisman_banks_only_full_adjusted_xp():
    game = floor_one_cleared_game()
    party = game.party_state
    party.add_shared_gold(20)
    secured_gold = party.shared_gold
    party.add_shared_items({"smoke_bomb": 1, "return_talisman": 1})
    assert party.load_carried_supplies(
        {"smoke_bomb": 1, "return_talisman": 1}
    )
    assert party.start_floor_two_run(run_id_factory=lambda: "talisman-run") == 100
    party.add_floor_two_rewards(
        experience=100,
        gold=15,
        items={"goblin_scrap": 2},
    )
    members = game.active_party_members
    initial_xp = tuple(member.exp_state.current for member in members)
    expected_awards = party.secured_xp_awards(members, 100)

    assert party.return_with_talisman(members)

    assert party.phase is DungeonPhase.HUB
    assert party.floor_two_run_id is None
    assert party.shared_gold == secured_gold
    assert party.shared_items == {"smoke_bomb": 1}
    assert party.carried_items == {}
    assert tuple(
        member.exp_state.current - old for member, old in zip(members, initial_xp)
    ) == expected_awards
    assert party.outing_rewards.snapshot() == {
        "experience": 0,
        "gold": 0,
        "items": {},
    }
    assert not party.return_with_talisman(members)


def test_run_event_outcomes_and_found_sources_round_trip():
    game = floor_one_cleared_game()
    party = game.party_state
    assert party.start_floor_two_run(run_id_factory=lambda: "floor-two-run") == 100
    assert "resolved_run_events" in party.snapshot()
    assert "discovered_permanent_discovery_sources" in game.world_state.snapshot()

    event = {
        "event_key": "floor_two:floor-two-run:floor_two_pre_boss_rest:discovery_search",
        "run_id": "floor-two-run",
        "floor_id": "floor_two",
        "node_id": "floor_two_pre_boss_rest",
        "kind": "discovery_search",
        "position": None,
        "result": {
            "source_id": "ancient_well_floor2_01",
            "searcher_drifter_id": "branoc",
            "effective_chance_bps": 1000,
            "roll": 500,
            "found": True,
        },
    }
    party.record_run_event(event)
    game.world_state.discover_permanent_discovery_source(
        "ancient_well_floor2_01"
    )

    restored_party = PartyState.from_snapshot(
        party.snapshot(),
        companions=party.companions,
    )
    restored_world = WorldState.from_snapshot(game.world_state.snapshot())

    assert restored_party.resolved_run_events == (event,)
    assert restored_party.run_event(event["event_key"]) == event
    assert restored_world.discovered_permanent_discovery_sources == (
        "ancient_well_floor2_01",
    )


def test_run_event_rejects_outcome_that_disagrees_with_its_roll():
    game = floor_one_cleared_game()
    party = game.party_state
    party.start_floor_two_run(run_id_factory=lambda: "floor-two-run")
    event = {
        "event_key": "floor_two:floor-two-run:floor_two_pre_boss_rest:discovery_search",
        "run_id": "floor-two-run",
        "floor_id": "floor_two",
        "node_id": "floor_two_pre_boss_rest",
        "kind": "discovery_search",
        "position": None,
        "result": {
            "source_id": "ancient_well_floor2_01",
            "searcher_drifter_id": "branoc",
            "effective_chance_bps": 1000,
            "roll": 1000,
            "found": False,
        },
    }

    try:
        party.record_run_event(event)
    except ValueError as error:
        assert "outcome" in str(error) or "roll" in str(error)
    else:
        raise AssertionError("search record accepted a result contradicting its roll")


def test_run_event_rejects_malformed_discovery_source_id():
    game = floor_one_cleared_game()
    party = game.party_state
    party.start_floor_two_run(run_id_factory=lambda: "floor-two-run")
    event = {
        "event_key": "floor_two:floor-two-run:floor_two_pre_boss_rest:discovery_search",
        "run_id": "floor-two-run",
        "floor_id": "floor_two",
        "node_id": "floor_two_pre_boss_rest",
        "kind": "discovery_search",
        "position": None,
        "result": {
            "source_id": "ab",
            "searcher_drifter_id": "branoc",
            "effective_chance_bps": 1000,
            "roll": 500,
            "found": True,
        },
    }

    try:
        party.record_run_event(event)
    except ValueError as error:
        assert "source ID" in str(error)
    else:
        raise AssertionError("search record accepted a malformed discovery source ID")
