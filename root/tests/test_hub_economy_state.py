import json

import pytest

from app.content.catalog import get_drifter_spec
from app.game.game_state import GameState
from app.game.overworld_state import ContextualRoutePhase
from app.game.overworld_session import OverworldSession
from app.game.party_state import DungeonPhase
from app.game.hub_economy_state import HubEconomyState, new_hub_economy_snapshot
from app.persistence.ports import SaveLoadResult
from app.persistence.save_document import (
    DISK_SCHEMA_VERSION,
    SaveStateValidationError,
    build_save_document,
    reconstruct_game_state,
    validate_profile_payload,
    validate_save_document,
)
from app.persistence.save_port_contract import SaveLoadStatus
from app.player.player_state import PlayerState
from app.presentation.overworld_models import (
    OverworldAction,
    OverworldScreen,
)
from app.ui.overworld_ui import ChooseOverworldAction
from tests.game_test_support import (
    completed_hub_game,
    floor_one_rest_game,
    hub_game,
)
from tests.test_floor_one_run import make_session


def _schema24(document):
    legacy = json.loads(json.dumps(document))
    legacy["schema_version"] = 24
    legacy["party"].pop("hub_economy")
    for key in (
        "floor_four_cleared",
        "floor_five_cleared",
        "region_two_unlocked",
        "floor_four_runs_started_after_clear",
        "floor_four_run_id",
        "floor_four_outing_xp_multiplier_percent",
        "floor_five_approach_run_id",
        "floor_five_reunion_run_id",
    ):
        legacy["party"].pop(key)
    legacy["story"].pop("knowledge_facts")
    return legacy


def _progressed_floor_one_rest_game():
    game = floor_one_rest_game()
    game.party_state._mark_encounter_progress()
    return game


def test_hub_economy_state_round_trips_with_current_save():
    game = hub_game()
    document = build_save_document(game)

    restored = reconstruct_game_state(document)

    assert document["schema_version"] == DISK_SCHEMA_VERSION == 31
    assert set(restored.party_state.hub_economy["vendor_stock"]) == {
        "merchant",
        "blacksmith",
        "alchemist",
    }
    assert restored.party_state.hub_economy == game.party_state.hub_economy


def test_sale_fed_mythril_keeps_its_existing_zero_stock_snapshot_entry():
    snapshot = new_hub_economy_snapshot()

    assert snapshot["vendor_stock"]["blacksmith"]["mythril_plate"] == 0


def test_m8_component_stacks_round_trip_without_a_save_schema_change():
    game = hub_game()
    component_id = "m8_sunder_spire_blade_reinforced_grade_iv"
    game.party_state.hub_economy_state.add_component(component_id, 2)

    document = build_save_document(game)
    restored = reconstruct_game_state(document)

    assert document["schema_version"] == DISK_SCHEMA_VERSION == 31
    assert restored.party_state.hub_economy_state.component_quantity(component_id) == 2


@pytest.mark.parametrize(
    "component_id,clear_name,clear_value",
    (
        ("m8_sunder_spire_blade_reinforced_grade_ii", "floor_two_cleared", True),
        ("m8_sunder_spire_blade_reinforced_grade_iii", "floor_three_cleared", True),
        ("m8_sunder_spire_blade_reinforced_grade_iv", "floor_four_cleared", True),
    ),
)
def test_m8_component_stock_initializes_only_after_wielder_and_floor_unlock(
    component_id,
    clear_name,
    clear_value,
):
    clear_inputs = {
        "floor_one_cleared": False,
        "floor_two_cleared": False,
        "floor_three_cleared": False,
        "floor_four_cleared": False,
    }
    locked_by_floor = new_hub_economy_snapshot(
        recruited_drifter_ids=("branoc",),
        **clear_inputs,
    )
    assert component_id not in locked_by_floor["vendor_stock"]["blacksmith"]

    clear_inputs[clear_name] = clear_value
    locked_by_roster = new_hub_economy_snapshot(
        recruited_drifter_ids=("azhvielle",),
        **clear_inputs,
    )
    assert component_id not in locked_by_roster["vendor_stock"]["blacksmith"]

    unlocked = new_hub_economy_snapshot(
        recruited_drifter_ids=("branoc",),
        **clear_inputs,
    )
    assert component_id not in unlocked["vendor_stock"]["blacksmith"]
    assert component_id not in unlocked["vendor_stock"]["merchant"]
    economy = HubEconomyState(unlocked)
    assert economy.vendor_stock_quantity("blacksmith", component_id) == 0
    assert economy.vendor_stock_quantity("merchant", component_id) == 0


def test_qualifying_return_does_not_replenish_unsold_higher_grade_components():
    component_id = "m8_sunder_spire_blade_reinforced_grade_ii"
    economy = HubEconomyState(
        new_hub_economy_snapshot(
            recruited_drifter_ids=("branoc",),
            floor_one_cleared=True,
            floor_two_cleared=True,
        )
    )
    economy.begin_hub_visit()
    economy.begin_outing("floor_one")
    economy.mark_encounter_progress()
    settled = economy.settle_outing()

    assert economy.replenish_for_qualifying_return(
        settled,
        recruited_drifter_ids=("branoc",),
        floor_one_cleared=True,
        floor_two_cleared=True,
        floor_three_cleared=False,
    )
    assert economy.vendor_stock_quantity("blacksmith", component_id) == 0
    assert economy.vendor_stock_quantity("merchant", component_id) == 0


def test_schema24_migration_backfills_clears_and_converts_smoke_powder_once():
    legacy = _schema24(build_save_document(completed_hub_game()))
    party = legacy["party"]
    party["floor_one_cleared"] = True
    party["floor_two_cleared"] = True
    party["shared_items"] = {"smoke_powder": 2, "charcoal_dust": 3}
    original = json.loads(json.dumps(legacy))

    migrated = validate_save_document(legacy)
    restored = reconstruct_game_state(legacy)
    normalized_again = validate_save_document(migrated)

    assert legacy == original
    assert migrated["schema_version"] == DISK_SCHEMA_VERSION == 31
    assert migrated["party"]["shared_items"] == {
        "charcoal_dust": 5,
        "grade_i_magic_crystal": 1,
        "grade_ii_magic_crystal": 1,
        "mythril_plate": 1,
    }
    assert normalized_again["party"]["shared_items"] == migrated["party"]["shared_items"]
    assert restored.party_state.shared_items == migrated["party"]["shared_items"]


def test_schema24_profile_history_is_accepted_without_rewriting_the_payload():
    historical = _schema24(build_save_document(hub_game()))
    original = json.loads(json.dumps(historical))

    validated = validate_profile_payload(historical)

    assert validated == original
    assert historical == original


def test_schema24_active_outing_migrates_with_route_progress_evidence():
    legacy = _schema24(build_save_document(_progressed_floor_one_rest_game()))

    migrated = validate_save_document(legacy)

    assert migrated["party"]["hub_economy"]["active_outing"] == {
        "outing_id": "outing_1",
        "floor_id": "floor_one",
        "has_encounter_progress": True,
    }


def test_current_dungeon_route_rejects_missing_or_mismatched_outing():
    document = build_save_document(_progressed_floor_one_rest_game())
    document["party"]["hub_economy"]["active_outing"] = None

    with pytest.raises(SaveStateValidationError, match="active outing"):
        validate_save_document(document)

    document = build_save_document(_progressed_floor_one_rest_game())
    document["party"]["hub_economy"]["active_outing"]["floor_id"] = "floor_two"

    with pytest.raises(SaveStateValidationError, match="active outing"):
        validate_save_document(document)


def test_current_outing_progress_must_match_the_route_cursor():
    document = build_save_document(_progressed_floor_one_rest_game())
    document["party"]["hub_economy"]["active_outing"][
        "has_encounter_progress"
    ] = False

    with pytest.raises(SaveStateValidationError, match="progress"):
        validate_save_document(document)


def test_progressed_floor_one_checkpoint_can_round_trip_after_saved_victory():
    game = completed_hub_game()
    assert game.party_state.start_floor_one_run() == 100
    game.overworld_state.begin_route("floor_one")
    game.party_state.add_floor_one_rewards(experience=20, gold=2)
    game.party_state._mark_encounter_progress()
    game.overworld_state.advance_to(
        "floor_one_battle_02",
        contextual_phase=ContextualRoutePhase.ENTER_ENCOUNTER,
    )

    restored = reconstruct_game_state(build_save_document(game))

    assert restored.overworld_state.current_route_node_id == "floor_one_battle_02"
    assert restored.party_state.hub_economy["active_outing"][
        "has_encounter_progress"
    ] is True
    assert restored.party_state.outing_rewards.experience == 20


def test_current_save_rejects_malformed_hub_economy_state():
    document = build_save_document(hub_game())
    document["party"]["hub_economy"]["alchemy_xp"] = -1

    with pytest.raises(SaveStateValidationError):
        validate_save_document(document)


def test_outing_progress_and_settlement_are_recorded_once():
    game = completed_hub_game()
    party = game.party_state
    assert party.start_floor_one_run() == 100
    active = party.hub_economy["active_outing"]
    assert active == {
        "outing_id": "outing_1",
        "floor_id": "floor_one",
        "has_encounter_progress": False,
    }

    party.add_floor_one_rewards(experience=0, gold=0, items={})
    assert party.hub_economy["active_outing"]["has_encounter_progress"] is False
    party._mark_encounter_progress()
    assert party.hub_economy["active_outing"]["has_encounter_progress"] is True
    assert party.fail_floor_one_run(game.active_party_members)
    settled = party.hub_economy
    assert settled["active_outing"] is None
    assert settled["last_settled_outing_id"] == "outing_1"
    assert settled["current_hub_visit_id"] == "hub_visit_3"
    assert settled["hub_visit_sequence"] == 3

    before_repeat = party.hub_economy
    assert not party.settle_active_outing()
    assert party.hub_economy == before_repeat


def test_expired_alchemist_buyback_feeds_specialist_then_merchant_stock_once():
    game = hub_game()
    party = game.party_state
    economy = party.hub_economy_state
    economy.spend_vendor_stock("alchemist", "medicinal_herb", 2)
    economy.spend_vendor_stock("merchant", "medicinal_herb", 1)
    economy.add_buyback_record(
        {
            "sale_id": "sale_7",
            "vendor_id": "alchemist",
            "visit_id": economy.current_hub_visit_id,
            "item_id": "medicinal_herb",
            "remaining_quantity": 5,
            "original_unit_payout": 2,
        }
    )

    economy.begin_outing("floor_one")
    assert economy.snapshot()["buyback_records"] == []
    assert economy.snapshot()["future_stock_queue"] == [
        {
            "sale_id": "sale_7",
            "specialist_id": "alchemist",
            "item_id": "medicinal_herb",
            "remaining_quantity": 5,
        }
    ]

    economy.mark_encounter_progress()
    settled = economy.settle_outing()
    kwargs = {
        "recruited_drifter_ids": tuple(
            member.drifter_id for member in game.recruited_members
        ),
        "floor_one_cleared": False,
        "floor_two_cleared": False,
        "floor_three_cleared": False,
    }

    unrelated_receipt = dict(settled, outing_id="unrelated_outing")
    before_rejected_receipt = economy.snapshot()
    assert not economy.replenish_for_qualifying_return(
        unrelated_receipt, **kwargs
    )
    assert economy.snapshot() == before_rejected_receipt

    assert economy.replenish_for_qualifying_return(settled, **kwargs)
    assert economy.vendor_stock_quantity("alchemist", "medicinal_herb") == 2
    assert economy.vendor_stock_quantity("merchant", "medicinal_herb") == 1
    assert economy.snapshot()["future_stock_queue"] == [
        {
            "sale_id": "sale_7",
            "specialist_id": "alchemist",
            "item_id": "medicinal_herb",
            "remaining_quantity": 2,
        }
    ]
    after_replenishment = economy.snapshot()

    assert not economy.replenish_for_qualifying_return(settled, **kwargs)
    assert economy.snapshot() == after_replenishment


@pytest.mark.parametrize("floor_id", ("floor_one", "floor_two"))
@pytest.mark.parametrize(
    ("experience", "gold", "items"),
    ((0, 0, {}), (5, 2, {"healing_potion": 1})),
)
def test_reward_mutation_alone_does_not_qualify_outing(
    floor_id, experience, gold, items
):
    game = completed_hub_game()
    party = game.party_state
    if floor_id == "floor_two":
        assert party.start_floor_one_run() == 100
        assert party.complete_floor_one_boss(game.active_party_members)
        party.start_floor_two_run(run_id_factory=lambda: "reward-only-outing")
    else:
        party.start_floor_one_run()

    award = (
        party.add_floor_one_rewards
        if floor_id == "floor_one"
        else party.add_floor_two_rewards
    )
    award(experience=experience, gold=gold, items=items)

    assert party.hub_economy["active_outing"]["has_encounter_progress"] is False


@pytest.mark.parametrize("floor_id", ("floor_one", "floor_two"))
def test_rejected_reward_payload_does_not_qualify_outing_progress(floor_id):
    game = completed_hub_game()
    party = game.party_state
    if floor_id == "floor_two":
        assert party.start_floor_one_run() == 100
        assert party.complete_floor_one_boss(game.active_party_members)
        party.start_floor_two_run(run_id_factory=lambda: "invalid-reward-run")
    else:
        party.start_floor_one_run()

    award = (
        party.add_floor_one_rewards
        if floor_id == "floor_one"
        else party.add_floor_two_rewards
    )
    with pytest.raises(ValueError):
        award(experience=-1, gold=0)

    assert party.hub_economy["active_outing"]["has_encounter_progress"] is False
    assert party.outing_rewards.snapshot() == {
        "experience": 0,
        "gold": 0,
        "items": {},
    }


def test_floor_one_first_clear_reward_is_banked_once_across_replay():
    game = completed_hub_game()
    party = game.party_state

    assert party.start_floor_one_run() == 100
    assert party.complete_floor_one_boss(game.active_party_members)
    assert party.shared_items["grade_i_magic_crystal"] == 1

    assert party.start_floor_one_run() == 50
    assert party.complete_floor_one_boss(game.active_party_members)

    assert party.shared_items["grade_i_magic_crystal"] == 1


def test_floor_one_extraction_does_not_award_first_clear_reward():
    game = completed_hub_game()
    party = game.party_state

    assert party.start_floor_one_run() == 100
    assert party.begin_floor_one_extraction(partial=True)
    assert party.complete_extraction(game.active_party_members)

    assert party.floor_one_cleared is False
    assert "grade_i_magic_crystal" not in party.shared_items


def test_floor_two_first_clear_rewards_are_banked_once_across_replay():
    game = completed_hub_game()
    party = game.party_state
    assert party.start_floor_one_run() == 100
    assert party.complete_floor_one_boss(game.active_party_members)

    assert party.start_floor_two_run(
        run_id_factory=lambda: "first-clear-floor-two"
    ) == 100
    assert party.complete_floor_two_boss(game.active_party_members)
    assert party.shared_items["grade_ii_magic_crystal"] == 1
    assert party.shared_items["mythril_plate"] == 1

    assert party.start_floor_two_run(
        run_id_factory=lambda: "replay-floor-two"
    ) == 50
    assert party.complete_floor_two_boss(game.active_party_members)

    assert party.shared_items["grade_ii_magic_crystal"] == 1
    assert party.shared_items["mythril_plate"] == 1


def test_outing_start_save_failure_keeps_hub_state_and_route_unchanged():
    class FailNextSave:
        def __init__(self):
            self.fail = True

        def inspect(self):
            return SaveLoadResult(SaveLoadStatus.MISSING)

        def load(self):
            return SaveLoadResult(SaveLoadStatus.MISSING)

        def save(self, _game_state):
            if self.fail:
                self.fail = False
                return SaveLoadResult(
                    SaveLoadStatus.INVALID,
                    error="injected local save failure",
                )
            return SaveLoadResult(SaveLoadStatus.SAVED)

    game = completed_hub_game()
    before = game.snapshot()
    session = make_session(game, FailNextSave())
    session.submit(ChooseOverworldAction(OverworldAction.START_FLOOR_ONE))

    result = session.submit(ChooseOverworldAction(OverworldAction.SET_OUT))

    assert result.screen is OverworldScreen.HUB
    assert session.game_state.snapshot() == before
    assert session.game_state.party_state.phase is DungeonPhase.HUB
    assert session.active_battle is None


def test_new_game_party_has_vendor_state_and_no_active_outing():
    game = GameState(PlayerState(get_drifter_spec("branoc").create_character()))

    state = game.party_state.hub_economy

    assert state["active_outing"] is None
    assert state["current_hub_visit_id"] is None
    assert state["transaction_sequence"] == 0
