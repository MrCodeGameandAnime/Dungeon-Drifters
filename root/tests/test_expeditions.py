from datetime import datetime, timedelta, timezone

import pytest

from app.game.expedition_state import ExpeditionState as PersistentExpeditionState
from app.game.expeditions import ExpeditionState


def _stamp(value):
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def test_service_module_uses_the_same_expedition_state_as_game_snapshots():
    from tests.game_test_support import completed_hub_game

    assert ExpeditionState is PersistentExpeditionState
    assert type(completed_hub_game().expedition_state) is ExpeditionState


def test_expedition_energy_starts_at_capacity_and_regenerates_each_nine_minutes():
    started = datetime(2026, 11, 10, 12, tzinfo=timezone.utc)
    state = ExpeditionState.from_snapshot(
        {
            "energy": 98,
            "energy_anchor_utc": _stamp(started),
            "active_assignment": None,
            "reports": [],
        }
    )

    state.update_energy(started + timedelta(minutes=8, seconds=59))
    assert state.energy == 98

    state.update_energy(started + timedelta(minutes=9))
    assert state.energy == 99
    state.update_energy(started + timedelta(minutes=18))
    assert state.energy == 100


def test_full_capacity_discards_overflow_and_spending_restarts_regeneration_clock():
    started = datetime(2026, 11, 10, 12, tzinfo=timezone.utc)
    state = ExpeditionState.from_snapshot(
        {
            "energy": 100,
            "energy_anchor_utc": _stamp(started),
            "active_assignment": None,
            "reports": [],
        }
    )
    full_since = started + timedelta(hours=3)

    state.update_energy(full_since)
    assert state.spend_energy(10, now=full_since + timedelta(seconds=1))
    assert state.energy == 90

    state.update_energy(full_since + timedelta(minutes=9))
    assert state.energy == 90
    state.update_energy(full_since + timedelta(minutes=9, seconds=1))
    assert state.energy == 91


def test_clock_rollback_neither_grants_energy_nor_moves_the_utc_anchor_backwards():
    accepted = datetime(2026, 11, 10, 12, tzinfo=timezone.utc)
    state = ExpeditionState.from_snapshot(
        {
            "energy": 50,
            "energy_anchor_utc": _stamp(accepted),
            "active_assignment": None,
            "reports": [],
        }
    )

    state.update_energy(accepted - timedelta(days=2))

    assert state.energy == 50
    assert state.energy_anchor_utc == _stamp(accepted)


def test_expedition_state_clone_copies_energy_and_assignment_independently():
    started = datetime(2026, 11, 10, 12, tzinfo=timezone.utc)
    state = ExpeditionState.from_snapshot(
        {
            "energy": 90,
            "energy_anchor_utc": _stamp(started),
            "active_assignment": None,
            "reports": [],
        }
    )
    state.install_assignment(
        {
            "assignment_id": "00000000-0000-4000-8000-000000000902",
            "outing_floor_id": "floor_one",
            "destination_floor_id": "floor_two",
            "category": "training",
            "expedition_drifter_ids": ["joruun", "zhaivra"],
            "started_at_utc": _stamp(started),
            "last_observed_at_utc": _stamp(started),
            "completed_at_utc": None,
        }
    )

    cloned = state.clone()
    cloned.update_energy(started + timedelta(minutes=9))
    cloned.observe_assignment_time(started + timedelta(minutes=1))

    assert cloned.energy == 91
    assert state.energy == 90
    assert cloned.active_assignment["last_observed_at_utc"] == _stamp(
        started + timedelta(minutes=1)
    )
    assert state.active_assignment["last_observed_at_utc"] == _stamp(started)


def test_expedition_state_defensively_copies_plain_assignment_and_report_values():
    assignment = {
        "assignment_id": "00000000-0000-4000-8000-000000000901",
        "outing_floor_id": "floor_one",
        "destination_floor_id": "floor_two",
        "category": "training",
        "expedition_drifter_ids": ["joruun", "zhaivra"],
        "started_at_utc": "2026-11-10T12:00:00Z",
        "last_observed_at_utc": "2026-11-10T12:00:00Z",
        "completed_at_utc": None,
    }
    report = {
        "report_id": assignment["assignment_id"],
        "outing_floor_id": assignment["outing_floor_id"],
        "destination_floor_id": assignment["destination_floor_id"],
        "category": "training",
        "expedition_drifter_ids": ["joruun", "zhaivra"],
        "started_at_utc": assignment["started_at_utc"],
        "completed_at_utc": "2026-11-10T12:20:00Z",
        "secured_base_xp": 0,
        "experience_awards": {"joruun": 0, "zhaivra": 0},
        "reward_item_id": None,
        "reward_quantity": 0,
        "claimed": False,
    }
    state = ExpeditionState()
    state.install_assignment(assignment)
    assignment["expedition_drifter_ids"].append("branoc")
    exposed_assignment = state.active_assignment
    exposed_assignment["expedition_drifter_ids"].append("branoc")
    assert state.active_assignment["expedition_drifter_ids"] == [
        "joruun",
        "zhaivra",
    ]

    assert state.settle_assignment(report)
    report["experience_awards"]["joruun"] = 99
    exposed_reports = state.reports
    exposed_reports[0]["experience_awards"]["zhaivra"] = 99
    assert state.reports[0]["experience_awards"] == {
        "joruun": 0,
        "zhaivra": 0,
    }


def _m6_ready_game(active_pair=("branoc", "azhvielle")):
    from app.content.catalog import get_drifter_spec
    from app.player.player_state import PlayerState
    from tests.game_test_support import completed_hub_game

    game = completed_hub_game()
    for drifter_id in ("joruun", "zhaivra"):
        assert game.party_state.recruit_companion(
            game.player_state, PlayerState(get_drifter_spec(drifter_id).create_character()), cost=0
        )
    game.party_state._floor_one_cleared = True
    game.party_state._floor_two_cleared = True
    game.party_state._floor_three_cleared = True
    roster = tuple(member.drifter_id for member in game.recruited_members)
    game.party_state.select_active_pair(active_pair, recruited_ids=roster)
    return game


@pytest.mark.parametrize(
    ("active_pair", "expected_expedition_pair"),
    (
        (("branoc", "azhvielle"), ("joruun", "zhaivra")),
        (("branoc", "joruun"), ("azhvielle", "zhaivra")),
        (("branoc", "zhaivra"), ("azhvielle", "joruun")),
        (("azhvielle", "joruun"), ("branoc", "zhaivra")),
        (("azhvielle", "zhaivra"), ("branoc", "joruun")),
        (("joruun", "zhaivra"), ("branoc", "azhvielle")),
    ),
)
def test_expedition_pair_is_roster_order_complement(active_pair, expected_expedition_pair):
    from app.game.expeditions import ExpeditionService

    assert ExpeditionService.expedition_pair_for_active_party(
        _m6_ready_game(active_pair)
    ) == expected_expedition_pair


def test_only_completed_floors_are_eligible_and_training_material_are_initial_categories():
    from app.game.expeditions import ExpeditionService
    from tests.persistence_test_support import make_test_save_port

    game = _m6_ready_game()
    service = ExpeditionService(make_test_save_port("unused"))

    assert service.eligible_destinations(game) == ("floor_one", "floor_two", "floor_three")
    assert service.category_unavailable_reason("floor_one", "training") is None
    assert service.category_unavailable_reason("floor_two", "material") is None
    assert "no eligible" in service.category_unavailable_reason("floor_three", "equipment").casefold()
    assert "no eligible" in service.category_unavailable_reason("floor_one", "recovery").casefold()
    assert service.category_unavailable_reason("floor_four", "training") is not None


def test_confirmed_launch_spends_once_and_persists_route_assignment_atomically(tmp_path):
    from uuid import UUID

    from app.game.expeditions import ExpeditionLaunchStatus, ExpeditionService
    from app.persistence.save_port_contract import SaveLoadStatus
    from tests.persistence_test_support import make_test_save_port

    game = _m6_ready_game()
    port = make_test_save_port(tmp_path / "profile.json")
    service = ExpeditionService(
        port,
        now_factory=lambda: datetime(2026, 11, 10, 12, tzinfo=timezone.utc),
        assignment_id_factory=lambda: UUID("00000000-0000-4000-8000-000000000111"),
        run_id_factory=lambda: "m6-floor-one-run",
    )

    result = service.launch(
        game,
        outing_floor_id="floor_one",
        destination_floor_id="floor_two",
        category="material",
        confirmed=True,
    )

    assert result.status is ExpeditionLaunchStatus.LAUNCHED
    assert result.game_state.expedition_state.energy == 90
    assignment = result.game_state.expedition_state.active_assignment
    assert assignment["expedition_drifter_ids"] == ["joruun", "zhaivra"]
    assert assignment["started_at_utc"] == "2026-11-10T12:00:00Z"
    assert result.game_state.overworld_state.active_route_id == "floor_one"
    assert result.game_state.party_state.phase.value == "outing"
    assert port.load().status is SaveLoadStatus.LOADED
    assert port.load().game_state.expedition_state.active_assignment == assignment
    assert game.expedition_state.energy == 100


def test_unconfirmed_or_unavailable_launch_does_not_mutate_or_save(tmp_path):
    from app.game.expeditions import ExpeditionLaunchStatus, ExpeditionService
    from app.persistence.save_port_contract import SaveLoadStatus
    from tests.persistence_test_support import make_test_save_port

    game = _m6_ready_game()
    before = game.snapshot()
    port = make_test_save_port(tmp_path / "profile.json")
    service = ExpeditionService(port)

    cancelled = service.launch(
        game,
        outing_floor_id="floor_one",
        destination_floor_id="floor_one",
        category="training",
        confirmed=False,
    )
    unavailable = service.launch(
        game,
        outing_floor_id="floor_one",
        destination_floor_id="floor_one",
        category="recovery",
        confirmed=True,
    )

    assert cancelled.status is ExpeditionLaunchStatus.CANCELLED
    assert unavailable.status is ExpeditionLaunchStatus.UNAVAILABLE_CATEGORY
    assert game.snapshot() == before
    assert port.inspect().status is SaveLoadStatus.MISSING


def test_floor_three_outing_and_floor_two_d3_d4_replay_pair_are_rejected(tmp_path):
    from app.game.expeditions import ExpeditionLaunchStatus, ExpeditionService
    from tests.persistence_test_support import make_test_save_port

    game = _m6_ready_game(("joruun", "zhaivra"))
    service = ExpeditionService(make_test_save_port(tmp_path / "profile.json"))

    floor_three = service.launch(
        game,
        outing_floor_id="floor_three",
        destination_floor_id="floor_one",
        category="training",
        confirmed=True,
    )
    floor_two = service.launch(
        game,
        outing_floor_id="floor_two",
        destination_floor_id="floor_one",
        category="training",
        confirmed=True,
    )

    assert floor_three.status is ExpeditionLaunchStatus.FLOOR_THREE_BLOCKED
    assert floor_two.status is ExpeditionLaunchStatus.INVALID_OUTING
    assert game.party_state.phase.value == "hub"


def test_active_expedition_cannot_be_bypassed_by_starting_floor_three(tmp_path):
    from app.game.overworld_session import OverworldSession
    from app.presentation.overworld_models import OverworldAction
    from app.ui.overworld_ui import ChooseOverworldAction
    from tests.persistence_test_support import make_test_save_port

    game = _m6_ready_game()
    _install_assignment(game)
    before = game.snapshot()
    session = OverworldSession(
        game,
        battle_factory=lambda *_args, **_kwargs: None,
        enemy_factory=lambda *_args, **_kwargs: None,
        save_port=make_test_save_port(tmp_path / "profile.json"),
    )

    view = session.submit(
        ChooseOverworldAction(OverworldAction.START_FLOOR_THREE)
    )

    assert view.notice == "End the current outing before starting Floor 3."
    assert session.game_state.snapshot() == before
    assert session.game_state.party_state.phase.value == "hub"


def _install_assignment(game, *, category="training", destination="floor_two"):
    assignment_id = "00000000-0000-4000-8000-000000000222"
    game.expedition_state.install_assignment(
        {
            "assignment_id": assignment_id,
            "outing_floor_id": "floor_one",
            "destination_floor_id": destination,
            "category": category,
            "expedition_drifter_ids": ["joruun", "zhaivra"],
            "started_at_utc": "2026-11-10T12:00:00Z",
            "last_observed_at_utc": "2026-11-10T12:00:00Z",
            "completed_at_utc": None,
        }
    )
    return assignment_id


def test_incomplete_assignment_settles_without_report_or_category_reward(tmp_path):
    from app.game.expeditions import (
        ExpeditionService,
        ExpeditionSettlementStatus,
    )
    from tests.persistence_test_support import make_test_save_port

    game = _m6_ready_game()
    _install_assignment(game)
    port = make_test_save_port(tmp_path / "profile.json")
    service = ExpeditionService(port)

    result = service.settle_outing(
        game,
        secured_base_xp=100,
        now=datetime(2026, 11, 10, 12, 19, 59, tzinfo=timezone.utc),
    )

    assert result.status is ExpeditionSettlementStatus.INCOMPLETE
    assert result.game_state.expedition_state.active_assignment is None
    assert result.game_state.expedition_state.reports == ()
    assert game.expedition_state.active_assignment is not None
    assert port.load().game_state.expedition_state.reports == ()


def test_training_settlement_freezes_twenty_percent_and_individual_xp_awards(tmp_path):
    from app.game.expeditions import ExpeditionService, ExpeditionSettlementStatus
    from app.player.scaling import secured_xp_bonus_bps_from_intuition
    from tests.persistence_test_support import make_test_save_port

    game = _m6_ready_game()
    _install_assignment(game)
    port = make_test_save_port(tmp_path / "profile.json")
    service = ExpeditionService(port)
    drifters = ("joruun", "zhaivra")
    base_shares = (13, 12)  # floor(125 * 20%) = 25; roster-first gets the remainder.
    expected_awards = {
        drifter_id: base + base * secured_xp_bonus_bps_from_intuition(
            game.member_for_drifter_id(drifter_id).effective_stat("intuition")
        ) // 10000
        for drifter_id, base in zip(drifters, base_shares)
    }

    result = service.settle_outing(
        game,
        secured_base_xp=125,
        now=datetime(2026, 11, 10, 12, 20, tzinfo=timezone.utc),
    )

    assert result.status is ExpeditionSettlementStatus.SETTLED
    assert result.game_state.expedition_state.active_assignment is None
    report, = result.game_state.expedition_state.reports
    assert report["secured_base_xp"] == 125
    assert report["experience_awards"] == expected_awards
    assert report["completed_at_utc"] == "2026-11-10T12:20:00Z"
    assert report["claimed"] is False
    loaded = port.load().game_state
    assert loaded.expedition_state.reports == (report,)


def test_training_report_claim_is_idempotent_and_only_awards_assigned_pair(tmp_path):
    from app.game.expeditions import (
        ExpeditionClaimStatus,
        ExpeditionService,
        ExpeditionSettlementStatus,
    )
    from tests.persistence_test_support import make_test_save_port

    game = _m6_ready_game()
    _install_assignment(game)
    port = make_test_save_port(tmp_path / "profile.json")
    service = ExpeditionService(port)
    settled = service.settle_outing(
        game,
        secured_base_xp=100,
        now=datetime(2026, 11, 10, 12, 20, tzinfo=timezone.utc),
    )
    assert settled.status is ExpeditionSettlementStatus.SETTLED
    report, = settled.game_state.expedition_state.reports
    before = {
        member.character.profile.drifter_id: member.exp_state.current
        for member in settled.game_state.recruited_members
    }

    claimed = service.claim_report(
        settled.game_state,
        report["report_id"],
        confirmed=True,
    )

    assert claimed.status is ExpeditionClaimStatus.CLAIMED
    assert claimed.game_state.expedition_state.reports[0]["claimed"] is True
    for drifter_id, amount in report["experience_awards"].items():
        assert (
            claimed.game_state.member_for_drifter_id(drifter_id).exp_state.current
            == before[drifter_id] + amount
        )
    for drifter_id in ("branoc", "azhvielle"):
        assert (
            claimed.game_state.member_for_drifter_id(drifter_id).exp_state.current
            == before[drifter_id]
        )

    repeated = service.claim_report(
        claimed.game_state,
        report["report_id"],
        confirmed=True,
    )
    assert repeated.status is ExpeditionClaimStatus.ALREADY_CLAIMED
    assert repeated.game_state.snapshot() == claimed.game_state.snapshot()
    assert port.load().game_state.snapshot() == claimed.game_state.snapshot()


def test_material_report_claim_awards_only_the_destination_grade_metal(tmp_path):
    from app.game.expeditions import (
        ExpeditionClaimStatus,
        ExpeditionService,
        ExpeditionSettlementStatus,
    )
    from tests.persistence_test_support import make_test_save_port

    game = _m6_ready_game()
    _install_assignment(game, category="material", destination="floor_three")
    port = make_test_save_port(tmp_path / "profile.json")
    service = ExpeditionService(port)
    settled = service.settle_outing(
        game,
        secured_base_xp=0,
        now=datetime(2026, 11, 10, 12, 20, tzinfo=timezone.utc),
    )
    assert settled.status is ExpeditionSettlementStatus.SETTLED
    report, = settled.game_state.expedition_state.reports
    assert report["reward_item_id"] == "grade_iii_metal"
    assert report["reward_quantity"] == 1

    claimed = service.claim_report(
        settled.game_state,
        report["report_id"],
        confirmed=True,
    )

    assert claimed.status is ExpeditionClaimStatus.CLAIMED
    assert claimed.game_state.party_state.shared_items["grade_iii_metal"] == 1
    assert "grade_i_metal" not in claimed.game_state.party_state.shared_items
    assert "grade_ii_metal" not in claimed.game_state.party_state.shared_items


def test_failed_report_claim_save_does_not_mutate_reward_or_claim_state():
    from app.game.expeditions import ExpeditionClaimStatus, ExpeditionService
    from app.persistence.save_port_contract import SaveLoadStatus

    class FailingSavePort:
        def inspect(self):
            return None

        def load(self):
            return None

        def save(self, _game_state):
            return type("Result", (), {"status": SaveLoadStatus.INVALID})()

    game = _m6_ready_game()
    _install_assignment(game, category="material")
    port = FailingSavePort()
    service = ExpeditionService(
        port,
        now_factory=lambda: datetime(2026, 11, 10, 12, 20, tzinfo=timezone.utc),
    )
    # Settle through an in-memory working port, then exercise only the failed claim write.
    class WorkingSavePort(FailingSavePort):
        def save(self, _game_state):
            return type("Result", (), {"status": SaveLoadStatus.SAVED})()

    settled = ExpeditionService(
        WorkingSavePort(),
        now_factory=lambda: datetime(2026, 11, 10, 12, 20, tzinfo=timezone.utc),
    ).settle_outing(game, secured_base_xp=0)
    report, = settled.game_state.expedition_state.reports
    before = settled.game_state.snapshot()

    failed = service.claim_report(
        settled.game_state,
        report["report_id"],
        confirmed=True,
    )

    assert failed.status is ExpeditionClaimStatus.SAVE_FAILED
    assert failed.game_state is settled.game_state
    assert settled.game_state.snapshot() == before


def test_session_extraction_settles_assignment_with_existing_secured_xp_pool(
    tmp_path,
):
    from uuid import UUID

    from app.game.expeditions import ExpeditionService, ExpeditionSettlementStatus
    from app.game.overworld_session import OverworldSession
    from app.presentation.overworld_models import OverworldAction, OverworldScreen
    from app.ui.overworld_ui import ChooseOverworldAction
    from tests.persistence_test_support import make_test_save_port

    port = make_test_save_port(tmp_path / "profile.json")
    game = _m6_ready_game()
    launched = ExpeditionService(
        port,
        now_factory=lambda: datetime(2026, 11, 10, 12, tzinfo=timezone.utc),
        assignment_id_factory=lambda: UUID("00000000-0000-4000-8000-000000000333"),
        run_id_factory=lambda: "m6-extraction-run",
    ).launch(
        game,
        outing_floor_id="floor_one",
        destination_floor_id="floor_two",
        category="training",
        confirmed=True,
    )
    outing = launched.game_state
    outing.party_state.add_floor_one_rewards(
        experience=125,
        gold=20,
        items={"goblin_scrap": 1},
    )
    assert outing.party_state.begin_floor_one_extraction(partial=True)
    secured_xp = outing.party_state.outing_rewards.experience
    session = OverworldSession(
        outing,
        battle_factory=lambda *_args, **_kwargs: None,
        enemy_factory=lambda *_args, **_kwargs: None,
        save_port=port,
        now_factory=lambda: datetime(2026, 11, 10, 12, 20, tzinfo=timezone.utc),
    )

    returned = session.submit(
        ChooseOverworldAction(OverworldAction.RETURN_TO_HUB)
    )

    assert returned.screen is OverworldScreen.HUB
    assert session.game_state.party_state.phase.value == "hub"
    assert session.game_state.expedition_state.active_assignment is None
    report, = session.game_state.expedition_state.reports
    assert report["secured_base_xp"] == secured_xp
    assert report["experience_awards"]
    assert report["claimed"] is False
    assert port.load().game_state.expedition_state.reports == (report,)
    assert ExpeditionService(port).settle_outing(
        session.game_state,
        secured_base_xp=secured_xp,
    ).status is ExpeditionSettlementStatus.NO_ASSIGNMENT


def test_completed_assignment_keeps_material_report_when_active_pair_dies(tmp_path):
    from uuid import UUID

    from app.game.expeditions import ExpeditionService, ExpeditionSettlementStatus
    from app.game.overworld_session import OverworldSession
    from app.presentation.overworld_models import OverworldScreen
    from tests.persistence_test_support import make_test_save_port

    port = make_test_save_port(tmp_path / "profile.json")
    game = _m6_ready_game()
    launched = ExpeditionService(
        port,
        now_factory=lambda: datetime(2026, 11, 10, 12, tzinfo=timezone.utc),
        assignment_id_factory=lambda: UUID("00000000-0000-4000-8000-000000000444"),
        run_id_factory=lambda: "m6-death-run",
    ).launch(
        game,
        outing_floor_id="floor_one",
        destination_floor_id="floor_three",
        category="material",
        confirmed=True,
    )
    session = OverworldSession(
        launched.game_state,
        battle_factory=lambda *_args, **_kwargs: None,
        enemy_factory=lambda *_args, **_kwargs: None,
        save_port=port,
        now_factory=lambda: datetime(2026, 11, 10, 12, 20, tzinfo=timezone.utc),
    )

    session._finalize_floor_one_battle(
        None,
        winner="enemy",
        current_node_id="floor_one_battle_01",
        exp_reward=0,
        gold_reward=0,
        party_members=session.game_state.active_party_members,
    )

    assert session.current_view().screen is OverworldScreen.HUB
    report, = session.game_state.expedition_state.reports
    assert report["secured_base_xp"] == 0
    assert report["category"] == "material"
    assert report["reward_item_id"] == "grade_iii_metal"
    assert report["claimed"] is False
    assert session.game_state.expedition_state.active_assignment is None
    loaded = port.load().game_state
    assert loaded.expedition_state.reports == (report,)
    assert loaded.expedition_state.active_assignment is None
    assert ExpeditionSettlementStatus.SETTLED.value == "settled"
