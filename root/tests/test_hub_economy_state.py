import json

import pytest

from app.content.catalog import get_drifter_spec
from app.game.game_state import GameState
from app.game.overworld_state import ContextualRoutePhase
from app.game.overworld_session import OverworldSession
from app.game.party_state import DungeonPhase
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
    return legacy


def _progressed_floor_one_rest_game():
    game = floor_one_rest_game()
    game.party_state.add_floor_one_rewards(experience=0, gold=0)
    return game


def test_hub_economy_state_round_trips_with_current_save():
    game = hub_game()
    document = build_save_document(game)

    restored = reconstruct_game_state(document)

    assert document["schema_version"] == DISK_SCHEMA_VERSION == 25
    assert set(restored.party_state.hub_economy["vendor_stock"]) == {
        "merchant",
        "blacksmith",
        "alchemist",
    }
    assert restored.party_state.hub_economy == game.party_state.hub_economy


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
    assert migrated["schema_version"] == 25
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
