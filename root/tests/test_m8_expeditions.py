from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.game.expeditions import (
    ExpeditionClaimStatus,
    ExpeditionLaunchStatus,
    ExpeditionService,
    ExpeditionSettlementStatus,
)
from app.game.expedition_state import ExpeditionState
from app.game.party_state import DungeonPhase
from app.game.story_state import KnowledgeStatus
from tests.test_expeditions import _m6_ready_game
from tests.persistence_test_support import make_test_save_port


START = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)


class _LowestArmorRolls:
    @staticmethod
    def randint(start, _end):
        return start


def _floor_four_game():
    game = _m6_ready_game()
    game.party_state._floor_four_cleared = True
    game.story_state.reveal_knowledge_fact(
        "m8_fact_drowned_reliquary", KnowledgeStatus.RUMORED
    )
    return game


def _service(port, report_number):
    return ExpeditionService(
        port,
        now_factory=lambda: START,
        assignment_id_factory=lambda: UUID(
            f"00000000-0000-4000-8000-{report_number:012d}"
        ),
        run_id_factory=lambda: f"m85-floor-four-{report_number}",
        equipment_instance_id_factory=lambda: UUID(
            f"10000000-0000-4000-8000-{report_number:012d}"
        ),
        armor_rng=_LowestArmorRolls(),
    )


@pytest.mark.parametrize(
    ("category", "report_content_id", "expected_outcome"),
    (
        (
            "material",
            "m8_floor_four_material_report",
            {
                "source_id": "m8_floor_four_metal_drop_01",
                "reward_item_id": "grade_iv_metal",
                "reward_quantity": 1,
            },
        ),
        (
            "recovery",
            "m8_floor_four_recovery_report",
            {
                "source_id": "m8_floor_four_recovery_source",
                "reward_item_id": "healing_potion",
                "reward_quantity": 1,
            },
        ),
        (
            "scouting",
            "m8_floor_four_scouting_report",
            {
                "knowledge_fact_ids": [
                    "m8_fact_reliquary_threats",
                    "m8_fact_ashen_vault",
                    "m8_fact_ashen_regent",
                ],
            },
        ),
        (
            "story",
            "m8_floor_four_story_report",
            {"story_event_id": "m8_story_reliquary_echo"},
        ),
        (
            "elite",
            "m8_floor_four_elite_report",
            {
                "source_id": "m8_floor_four_core_drop_01",
                "reward_item_id": "grade_iv_cores",
                "reward_quantity": 1,
            },
        ),
    ),
)
def test_floor_four_report_outcome_is_frozen_and_claimed_once(
    tmp_path, category, report_content_id, expected_outcome
):
    game = _floor_four_game()
    port = make_test_save_port(tmp_path / f"{category}.json")
    service = _service(port, 501)

    launched = service.launch(
        game,
        outing_floor_id="floor_four",
        destination_floor_id="floor_four",
        category=category,
        confirmed=True,
    )

    assert launched.status is ExpeditionLaunchStatus.LAUNCHED
    outing = launched.game_state
    assignment = outing.expedition_state.active_assignment
    assert assignment["report_content_id"] == report_content_id
    frozen = assignment["frozen_outcome"]
    if category == "equipment":
        assert frozen["source_id"] == "m8_floor_four_armor_source"
        assert frozen["equipment_instance"]["definition_id"] == "field_chest"
        assert frozen["equipment_instance"]["secured"] is True
        instance_id = frozen["equipment_instance"]["instance_id"]
    else:
        assert frozen == expected_outcome
        instance_id = None

    assert outing.party_state.phase is DungeonPhase.OUTING
    assert outing.overworld_state.active_route_id == "floor_four"
    assert outing.party_state.active_drifter_ids == game.party_state.active_drifter_ids
    assert outing.expedition_state.active_assignment["expedition_drifter_ids"] == [
        drifter_id
        for drifter_id in ("branoc", "azhvielle", "joruun", "zhaivra")
        if drifter_id not in game.party_state.active_drifter_ids
    ]

    persisted_assignment = port.load().game_state.expedition_state.active_assignment
    assert persisted_assignment["frozen_outcome"] == frozen

    assert outing.party_state.begin_floor_four_extraction(partial=False)
    assert outing.party_state.complete_floor_four_extraction(
        outing.active_party_members
    )
    outing.overworld_state.return_to_surface_entrance()
    settled = service.settle_outing(
        outing,
        secured_base_xp=0,
        now=START + timedelta(minutes=20),
    )

    assert settled.status is ExpeditionSettlementStatus.SETTLED
    report, = settled.game_state.expedition_state.reports
    assert report["report_content_id"] == report_content_id
    assert report["frozen_outcome"] == frozen
    assert report["claimed"] is False

    claimed = service.claim_report(
        settled.game_state,
        report["report_id"],
        confirmed=True,
    )
    assert claimed.status is ExpeditionClaimStatus.CLAIMED
    if category in {"material", "recovery", "elite"}:
        assert claimed.game_state.party_state.shared_items[
            expected_outcome["reward_item_id"]
        ] == 1
    elif category == "scouting":
        for fact_id in expected_outcome["knowledge_fact_ids"]:
            assert claimed.game_state.story_state.knowledge_status(
                fact_id
            ) is KnowledgeStatus.CONFIRMED
    elif category == "story":
        assert "m8_story_reliquary_echo" in (
            claimed.game_state.story_state.completed_events
        )
        from app.game.overworld_session import OverworldSession
        from app.presentation.overworld_models import OverworldAction

        session = OverworldSession(
            claimed.game_state,
            battle_factory=lambda *args, **kwargs: None,
            enemy_factory=lambda *args, **kwargs: None,
        )
        assert OverworldAction.OPEN_RELIQUARY_ECHO in {
            option.action for option in session.current_view().options
        }
    elif category == "equipment":
        owned = claimed.game_state.party_state.equipment_instance(instance_id)
        assert owned.snapshot() == frozen["equipment_instance"]

    assert port.load().game_state.expedition_state.reports[0]["frozen_outcome"] == frozen
    repeated = service.claim_report(
        claimed.game_state,
        report["report_id"],
        confirmed=True,
    )
    assert repeated.status is ExpeditionClaimStatus.ALREADY_CLAIMED
    assert repeated.game_state.snapshot() == claimed.game_state.snapshot()


def test_floor_four_equipment_report_freezes_a_complete_unique_armor_instance(
    tmp_path,
):
    game = _floor_four_game()
    port = make_test_save_port(tmp_path / "equipment.json")
    service = _service(port, 502)

    launched = service.launch(
        game,
        outing_floor_id="floor_four",
        destination_floor_id="floor_four",
        category="equipment",
        confirmed=True,
    )

    assert launched.status is ExpeditionLaunchStatus.LAUNCHED
    assignment = launched.game_state.expedition_state.active_assignment
    assert assignment["report_content_id"] == "m8_floor_four_equipment_report"
    instance = assignment["frozen_outcome"]["equipment_instance"]
    assert set(instance) == {
        "instance_id",
        "definition_id",
        "source_id",
        "secured",
        "stat_bonuses",
        "rarity",
        "upgrade_rank",
        "modifier_slots",
    }
    assert instance["instance_id"] == str(
        UUID("10000000-0000-4000-8000-000000000502")
    )
    assert instance["source_id"] == "m8_floor_four_armor_source"
    assert instance["secured"] is True


def test_equipment_report_rejects_an_already_owned_instance_id(tmp_path):
    from app.content.catalog import get_armor_reward_source
    from app.game.armor_generation import ArmorGenerationService

    game = _floor_four_game()
    duplicate_id = "10000000-0000-4000-8000-000000000503"
    source = get_armor_reward_source("m8_floor_four_armor_source")
    owned = ArmorGenerationService(rng=_LowestArmorRolls()).generate(
        template_id=source.template_id,
        floor=source.floor,
        source_id=source.source_id,
        instance_id=duplicate_id,
        secured=True,
    )
    game.party_state.add_equipment_instance(owned)
    port = make_test_save_port(tmp_path / "duplicate-owned-equipment.json")
    service = ExpeditionService(
        port,
        now_factory=lambda: START,
        assignment_id_factory=lambda: UUID(
            "00000000-0000-4000-8000-000000000503"
        ),
        equipment_instance_id_factory=lambda: UUID(duplicate_id),
        armor_rng=_LowestArmorRolls(),
    )
    before = game.snapshot()

    result = service.launch(
        game,
        outing_floor_id="floor_four",
        destination_floor_id="floor_four",
        category="equipment",
        confirmed=True,
    )

    assert result.status is ExpeditionLaunchStatus.INVALID_OUTING
    assert result.game_state is game
    assert game.snapshot() == before


def test_equipment_claim_save_failure_keeps_frozen_reward_retryable(tmp_path):
    from app.persistence.save_port_contract import SaveLoadStatus

    delegate = make_test_save_port(tmp_path / "equipment-claim-retry.json")

    class FailNextSavePort:
        fail_next = False

        def inspect(self):
            return delegate.inspect()

        def load(self):
            return delegate.load()

        def save(self, game_state):
            if self.fail_next:
                self.fail_next = False
                return type("Result", (), {"status": SaveLoadStatus.INVALID})()
            return delegate.save(game_state)

    port = FailNextSavePort()
    service = _service(port, 504)
    launched = service.launch(
        _floor_four_game(),
        outing_floor_id="floor_four",
        destination_floor_id="floor_four",
        category="equipment",
        confirmed=True,
    )
    outing = launched.game_state
    frozen = outing.expedition_state.active_assignment["frozen_outcome"]
    outing.party_state.begin_floor_four_extraction(partial=False)
    outing.party_state.complete_floor_four_extraction(outing.active_party_members)
    outing.overworld_state.return_to_surface_entrance()
    settled = service.settle_outing(
        outing,
        secured_base_xp=0,
        now=START + timedelta(minutes=20),
    )
    report, = settled.game_state.expedition_state.reports
    original = settled.game_state.snapshot()
    port.fail_next = True

    failed = service.claim_report(
        settled.game_state,
        report["report_id"],
        confirmed=True,
    )

    assert failed.status is ExpeditionClaimStatus.SAVE_FAILED
    assert failed.game_state is settled.game_state
    assert settled.game_state.snapshot() == original
    assert not settled.game_state.party_state.equipment_instances
    assert not settled.game_state.expedition_state.reports[0]["claimed"]

    retried = service.claim_report(
        settled.game_state,
        report["report_id"],
        confirmed=True,
    )

    assert retried.status is ExpeditionClaimStatus.CLAIMED
    assert retried.game_state.party_state.equipment_instance(
        frozen["equipment_instance"]["instance_id"]
    ).snapshot() == frozen["equipment_instance"]
    assert retried.game_state.expedition_state.reports[0]["claimed"]


def test_equipment_report_claim_equip_and_reload_preserves_generated_instance(
    tmp_path,
):
    from app.game.equipment import EquipmentActionStatus, EquipmentService

    game = _floor_four_game()
    port = make_test_save_port(tmp_path / "equipment-equip-reload.json")
    service = _service(port, 508)
    launched = service.launch(
        game,
        outing_floor_id="floor_four",
        destination_floor_id="floor_four",
        category="equipment",
        confirmed=True,
    )
    assert launched.status is ExpeditionLaunchStatus.LAUNCHED
    frozen_instance = launched.game_state.expedition_state.active_assignment[
        "frozen_outcome"
    ]["equipment_instance"]
    outing = launched.game_state
    assert outing.party_state.begin_floor_four_extraction(partial=False)
    assert outing.party_state.complete_floor_four_extraction(
        outing.active_party_members
    )
    outing.overworld_state.return_to_surface_entrance()
    settled = service.settle_outing(
        outing,
        secured_base_xp=0,
        now=START + timedelta(minutes=20),
    )
    report, = settled.game_state.expedition_state.reports
    claimed = service.claim_report(
        settled.game_state, report["report_id"], confirmed=True
    )
    assert claimed.status is ExpeditionClaimStatus.CLAIMED

    equipped = EquipmentService(save_port=port).equip(
        claimed.game_state,
        target_drifter_id="branoc",
        instance_id=frozen_instance["instance_id"],
    )

    assert equipped.status is EquipmentActionStatus.EQUIPPED
    reloaded = port.load().game_state
    assert reloaded.party_state.equipment_instance(
        frozen_instance["instance_id"]
    ).snapshot() == frozen_instance
    assert reloaded.member_for_drifter_id(
        "branoc"
    ).equipped_equipment_ids["chest"] == frozen_instance["instance_id"]
    assert reloaded.expedition_state.reports[0]["claimed"] is True


class _FailNextSavePort:
    def __init__(self, delegate):
        self.delegate = delegate
        self.fail_next = False

    def inspect(self):
        return self.delegate.inspect()

    def load(self):
        return self.delegate.load()

    def save(self, game_state):
        if self.fail_next:
            self.fail_next = False
            from app.persistence.save_port_contract import SaveLoadStatus

            return type("Result", (), {"status": SaveLoadStatus.INVALID})()
        return self.delegate.save(game_state)


@pytest.mark.parametrize(
    ("category", "fact_id", "expected_status"),
    (
        ("scouting", "m8_fact_ashen_vault", KnowledgeStatus.UNKNOWN),
        ("story", None, None),
    ),
)
def test_scouting_and_story_failed_claim_save_rolls_back_and_retries(
    tmp_path, category, fact_id, expected_status
):
    port = _FailNextSavePort(
        make_test_save_port(tmp_path / f"{category}-claim-retry.json")
    )
    service = _service(port, 509 if category == "scouting" else 510)
    launched = service.launch(
        _floor_four_game(),
        outing_floor_id="floor_four",
        destination_floor_id="floor_four",
        category=category,
        confirmed=True,
    )
    assert launched.status is ExpeditionLaunchStatus.LAUNCHED
    outing = launched.game_state
    assert outing.party_state.begin_floor_four_extraction(partial=False)
    assert outing.party_state.complete_floor_four_extraction(
        outing.active_party_members
    )
    outing.overworld_state.return_to_surface_entrance()
    settled = service.settle_outing(
        outing,
        secured_base_xp=0,
        now=START + timedelta(minutes=20),
    )
    report, = settled.game_state.expedition_state.reports
    before = settled.game_state.snapshot()
    port.fail_next = True

    failed = service.claim_report(
        settled.game_state, report["report_id"], confirmed=True
    )

    assert failed.status is ExpeditionClaimStatus.SAVE_FAILED
    assert failed.game_state is settled.game_state
    assert settled.game_state.snapshot() == before
    assert port.load().game_state.expedition_state.reports[0]["claimed"] is False
    if fact_id is not None:
        assert settled.game_state.story_state.knowledge_status(
            fact_id
        ) is expected_status
        assert port.load().game_state.story_state.knowledge_status(
            fact_id
        ) is expected_status
    else:
        event_id = report["frozen_outcome"]["story_event_id"]
        assert event_id not in settled.game_state.story_state.completed_events
        assert event_id not in port.load().game_state.story_state.completed_events

    retried = service.claim_report(
        settled.game_state, report["report_id"], confirmed=True
    )
    assert retried.status is ExpeditionClaimStatus.CLAIMED
    assert port.load().game_state.expedition_state.reports[0]["claimed"] is True
    if fact_id is not None:
        assert retried.game_state.story_state.knowledge_status(
            fact_id
        ) is KnowledgeStatus.CONFIRMED
    else:
        assert report["frozen_outcome"]["story_event_id"] in (
            retried.game_state.story_state.completed_events
        )


def test_floor_four_expedition_elapsed_settlement_claim_and_reload_through_session(
    tmp_path,
):
    from app.game.overworld_session import OverworldSession
    from app.presentation.overworld_models import OverworldAction, OverworldScreen
    from app.ui.overworld_ui import ChooseOverworldAction, ChooseExpeditionReport

    port = make_test_save_port(tmp_path / "floor-four-terminal-settlement.json")
    game = _floor_four_game()
    game.story_state.reveal_knowledge_fact(
        "m8_fact_drowned_reliquary", KnowledgeStatus.RUMORED
    )
    service = _service(port, 511)
    launched = service.launch(
        game,
        outing_floor_id="floor_four",
        destination_floor_id="floor_four",
        category="material",
        confirmed=True,
    )
    assert launched.status is ExpeditionLaunchStatus.LAUNCHED
    persisted_assignment = port.load().game_state.expedition_state.active_assignment
    assert persisted_assignment["completed_at_utc"] is None
    assert persisted_assignment["frozen_outcome"] == {
        "source_id": "m8_floor_four_metal_drop_01",
        "reward_item_id": "grade_iv_metal",
        "reward_quantity": 1,
    }

    outing = port.load().game_state
    assert outing.party_state.begin_floor_four_extraction(partial=False)
    current_time = [START + timedelta(minutes=20)]
    session = OverworldSession(
        outing,
        battle_factory=lambda *_args, **_kwargs: None,
        enemy_factory=lambda *_args, **_kwargs: None,
        save_port=port,
        now_factory=lambda: current_time[0],
    )
    assert session.current_view().screen is OverworldScreen.EXTRACTION
    session.submit(ChooseOverworldAction(OverworldAction.RETURN_TO_HUB))

    assert session.game_state.party_state.phase is DungeonPhase.HUB
    settled = port.load().game_state
    report, = settled.expedition_state.reports
    assert report["completed_at_utc"] == "2026-11-20T12:20:00Z"
    assert report["claimed"] is False
    assert settled.expedition_state.active_assignment is None

    session.submit(ChooseOverworldAction(OverworldAction.EXPEDITIONS))
    session.submit(ChooseExpeditionReport(report["report_id"]))
    assert session.game_state.party_state.shared_items["grade_iv_metal"] == 1
    assert session.game_state.expedition_state.reports[0]["claimed"] is True
    reloaded = port.load().game_state
    assert reloaded.party_state.shared_items["grade_iv_metal"] == 1
    assert reloaded.expedition_state.reports[0]["claimed"] is True


def test_floor_five_material_controlled_source_settles_and_claims_once(
    tmp_path, monkeypatch
):
    import app.game.expedition_state as expedition_state

    source_id = "m8_floor_five_controlled_core_source"
    monkeypatch.setattr(
        expedition_state, "_floor_five_material_source_ids", lambda: (source_id,)
    )
    game = _floor_four_game()
    game.party_state._floor_five_cleared = True
    game.party_state._region_two_unlocked = True
    port = make_test_save_port(tmp_path / "floor-five-controlled-material.json")
    service = _service(port, 512)
    launched = service.launch(
        game,
        outing_floor_id="floor_four",
        destination_floor_id="floor_five",
        category="material",
        confirmed=True,
    )

    assert launched.status is ExpeditionLaunchStatus.LAUNCHED
    frozen = launched.game_state.expedition_state.active_assignment[
        "frozen_outcome"
    ]
    assert frozen == {
        "source_id": source_id,
        "reward_item_id": "grade_iv_cores",
        "reward_quantity": 1,
    }
    outing = launched.game_state
    assert outing.party_state.begin_floor_four_extraction(partial=False)
    assert outing.party_state.complete_floor_four_extraction(
        outing.active_party_members
    )
    outing.overworld_state.return_to_surface_entrance()
    settled = service.settle_outing(
        outing,
        secured_base_xp=0,
        now=START + timedelta(minutes=20),
    )
    report, = settled.game_state.expedition_state.reports
    assert report["frozen_outcome"] == frozen
    assert report["reward_item_id"] == "grade_iv_cores"
    assert report["reward_quantity"] == 1

    claimed = service.claim_report(
        settled.game_state, report["report_id"], confirmed=True
    )
    assert claimed.status is ExpeditionClaimStatus.CLAIMED
    assert claimed.game_state.party_state.shared_items["grade_iv_cores"] == 1
    reloaded = port.load().game_state
    assert reloaded.party_state.shared_items["grade_iv_cores"] == 1
    assert reloaded.expedition_state.reports[0]["frozen_outcome"] == frozen
    assert service.claim_report(
        reloaded, report["report_id"], confirmed=True
    ).status is ExpeditionClaimStatus.ALREADY_CLAIMED


@pytest.mark.parametrize("record_kind", ("assignment", "report"))
def test_current_expedition_floor_four_evidence_requires_completed_destination(
    tmp_path, record_kind
):
    from app.persistence.save_document import (
        SaveStateValidationError,
        build_save_document,
        validate_save_document,
    )

    game = _floor_four_game()
    port = make_test_save_port(tmp_path / f"floor-four-{record_kind}-eligibility.json")
    service = _service(port, 513 if record_kind == "assignment" else 514)
    launched = service.launch(
        game,
        outing_floor_id="floor_four",
        destination_floor_id="floor_four",
        category="training",
        confirmed=True,
    )
    assert launched.status is ExpeditionLaunchStatus.LAUNCHED
    evidence_game = launched.game_state
    if record_kind == "report":
        assert evidence_game.party_state.begin_floor_four_extraction(partial=False)
        assert evidence_game.party_state.complete_floor_four_extraction(
            evidence_game.active_party_members
        )
        evidence_game.overworld_state.return_to_surface_entrance()
        settled = service.settle_outing(
            evidence_game,
            secured_base_xp=0,
            now=START + timedelta(minutes=20),
        )
        assert settled.status is ExpeditionSettlementStatus.SETTLED
        evidence_game = settled.game_state

    document = build_save_document(evidence_game)
    document["party"]["floor_four_cleared"] = False
    document["party"]["floor_four_runs_started_after_clear"] = 0
    document["party"]["floor_four_outing_xp_multiplier_percent"] = 100

    with pytest.raises(SaveStateValidationError, match="uncleared expedition destination"):
        validate_save_document(document)


def test_current_save_rejects_unclaimed_equipment_already_in_party_inventory(
    tmp_path,
):
    from copy import deepcopy

    from app.persistence.save_document import (
        SaveStateValidationError,
        build_save_document,
        validate_save_document,
    )

    launched = _service(make_test_save_port(tmp_path / "equipment.json"), 505).launch(
        _floor_four_game(),
        outing_floor_id="floor_four",
        destination_floor_id="floor_four",
        category="equipment",
        confirmed=True,
    )
    document = build_save_document(launched.game_state)
    duplicate = deepcopy(
        document["expedition"]["active_assignment"]["frozen_outcome"][
            "equipment_instance"
        ]
    )
    document["party"]["equipment_instances"].append(duplicate)

    with pytest.raises(SaveStateValidationError, match="already owned"):
        validate_save_document(document)


def test_current_save_rejects_equipment_template_mismatched_to_authored_source(
    tmp_path,
):
    from app.persistence.save_document import (
        SaveStateValidationError,
        build_save_document,
        validate_save_document,
    )

    launched = _service(make_test_save_port(tmp_path / "equipment.json"), 508).launch(
        _floor_four_game(),
        outing_floor_id="floor_four",
        destination_floor_id="floor_four",
        category="equipment",
        confirmed=True,
    )
    document = build_save_document(launched.game_state)
    instance = document["expedition"]["active_assignment"]["frozen_outcome"][
        "equipment_instance"
    ]
    instance["definition_id"] = "field_helm"
    instance["stat_bonuses"] = {"constitution": 1}

    with pytest.raises(SaveStateValidationError, match="authored source"):
        validate_save_document(document)


def test_current_save_rejects_duplicate_frozen_equipment_report_identity(tmp_path):
    from copy import deepcopy

    from app.persistence.save_document import (
        SaveStateValidationError,
        build_save_document,
        validate_save_document,
    )

    launched = _service(make_test_save_port(tmp_path / "equipment.json"), 506).launch(
        _floor_four_game(),
        outing_floor_id="floor_four",
        destination_floor_id="floor_four",
        category="equipment",
        confirmed=True,
    )
    document = build_save_document(launched.game_state)
    assignment = document["expedition"]["active_assignment"]
    report = {
        key: deepcopy(assignment[key])
        for key in (
            "outing_floor_id",
            "destination_floor_id",
            "category",
            "report_content_id",
            "expedition_drifter_ids",
            "started_at_utc",
            "frozen_outcome",
        )
    }
    report.update({
        "report_id": "20000000-0000-4000-8000-000000000506",
        "completed_at_utc": "2026-11-20T12:20:00Z",
        "secured_base_xp": 0,
        "experience_awards": {},
        "reward_item_id": None,
        "reward_quantity": 0,
        "claimed": False,
    })
    document["expedition"]["reports"].append(report)

    with pytest.raises(SaveStateValidationError, match="instance IDs must be unique"):
        validate_save_document(document)


def test_floor_five_material_requires_clear_and_authored_source_evidence(tmp_path):
    from app.game.expedition_state import ExpeditionState

    game = _floor_four_game()
    game.party_state._floor_five_cleared = True
    port = make_test_save_port(tmp_path / "floor-five.json")
    service = ExpeditionService(port)

    assert "floor_five" in service.eligible_destinations(game)
    reason = service.category_unavailable_reason(
        "floor_five",
        "material",
        game_state=game,
    )
    assert reason is not None
    assert "source" in reason.casefold()
    assert service.launch(
        game,
        outing_floor_id="floor_one",
        destination_floor_id="floor_five",
        category="material",
        confirmed=True,
    ).status is ExpeditionLaunchStatus.UNAVAILABLE_CATEGORY

    game.party_state._floor_five_cleared = False
    assert "floor_five" not in service.eligible_destinations(game)
    assert ExpeditionState.from_snapshot({
        "energy": 100,
        "energy_anchor_utc": None,
        "active_assignment": None,
        "reports": [],
    }).reports == ()


def test_floor_v_approach_contract_waits_for_its_authored_route():
    game = _floor_four_game()
    port = make_test_save_port("unused")

    result = ExpeditionService(port).launch(
        game,
        outing_floor_id="floor_five_approach",
        destination_floor_id="floor_four",
        category="training",
        confirmed=True,
    )

    assert result.status is ExpeditionLaunchStatus.INVALID_OUTING
    assert result.game_state is game


def test_floor_five_reunion_is_never_an_expedition_compatible_outing():
    game = _floor_four_game()
    before = game.snapshot()
    result = ExpeditionService(make_test_save_port("unused")).launch(
        game,
        outing_floor_id="floor_five_reunion",
        destination_floor_id="floor_four",
        category="training",
        confirmed=True,
    )

    assert result.status is ExpeditionLaunchStatus.INVALID_OUTING
    assert result.game_state is game
    assert game.snapshot() == before


def test_floor_four_launch_save_failure_preserves_roster_energy_and_route():
    from app.persistence.save_port_contract import SaveLoadStatus

    class FailingSavePort:
        def inspect(self):
            return None

        def load(self):
            return None

        def save(self, _game_state):
            return type("Result", (), {"status": SaveLoadStatus.INVALID})()

    game = _floor_four_game()
    before = game.snapshot()
    result = _service(FailingSavePort(), 507).launch(
        game,
        outing_floor_id="floor_four",
        destination_floor_id="floor_four",
        category="scouting",
        confirmed=True,
    )

    assert result.status is ExpeditionLaunchStatus.SAVE_FAILED
    assert result.game_state is game
    assert game.snapshot() == before
    assert game.story_state.knowledge_status(
        "m8_fact_drowned_reliquary"
    ) is KnowledgeStatus.RUMORED


def test_floor_four_expedition_entry_rejects_unknown_region_destination():
    game = _m6_ready_game()
    game.party_state._floor_four_cleared = True
    before = game.snapshot()

    result = _service(make_test_save_port("unused"), 515).launch(
        game,
        outing_floor_id="floor_four",
        destination_floor_id="floor_four",
        category="training",
        confirmed=True,
    )

    assert result.status is ExpeditionLaunchStatus.INVALID_OUTING
    assert result.game_state is game
    assert game.snapshot() == before
    assert game.story_state.knowledge_status(
        "m8_fact_drowned_reliquary"
    ) is KnowledgeStatus.UNKNOWN


def test_floor_four_expedition_entry_accepts_already_confirmed_destination():
    game = _floor_four_game()
    game.story_state.reveal_knowledge_fact(
        "m8_fact_drowned_reliquary", KnowledgeStatus.CONFIRMED
    )

    result = _service(make_test_save_port("unused"), 516).launch(
        game,
        outing_floor_id="floor_four",
        destination_floor_id="floor_four",
        category="training",
        confirmed=True,
    )

    assert result.status is ExpeditionLaunchStatus.LAUNCHED
    assert result.game_state.story_state.knowledge_status(
        "m8_fact_drowned_reliquary"
    ) is KnowledgeStatus.CONFIRMED


@pytest.mark.parametrize("missing_field", ("frozen_outcome", "report_content_id"))
def test_current_save_rejects_expedition_record_missing_m8_5_fields(
    tmp_path, missing_field
):
    from app.persistence.save_document import (
        SaveStateValidationError,
        build_save_document,
        validate_save_document,
    )

    game = _floor_four_game()
    launched = _service(make_test_save_port(tmp_path / "launch.json"), 701).launch(
        game,
        outing_floor_id="floor_four",
        destination_floor_id="floor_four",
        category="material",
        confirmed=True,
    )
    document = build_save_document(launched.game_state)
    document["expedition"]["active_assignment"].pop(missing_field)

    with pytest.raises(SaveStateValidationError, match="expedition is invalid"):
        validate_save_document(document)


def test_schema28_rejects_m8_5_report_evidence_before_migration(tmp_path):
    from app.persistence.save_document import (
        SaveStateValidationError,
        build_save_document,
        validate_profile_payload,
    )

    launched = _service(make_test_save_port(tmp_path / "launch.json"), 702).launch(
        _floor_four_game(),
        outing_floor_id="floor_four",
        destination_floor_id="floor_four",
        category="material",
        confirmed=True,
    )
    historical = build_save_document(launched.game_state)
    historical["schema_version"] = 28

    with pytest.raises(SaveStateValidationError, match="post-M8.5"):
        validate_profile_payload(historical)


def test_schema28_m6_report_migrates_with_immutable_legacy_shape():
    from copy import deepcopy

    from app.persistence.save_document import (
        build_save_document,
        validate_profile_payload,
        validate_save_document,
    )

    game = _m6_ready_game()
    expedition = ExpeditionState()
    assignment_id = "00000000-0000-4000-8000-000000000701"
    started = "2026-11-20T12:00:00Z"
    completed = "2026-11-20T12:20:00Z"
    pair = ["joruun", "zhaivra"]
    outcome = {
        "source_id": None,
        "reward_item_id": "grade_ii_metal",
        "reward_quantity": 1,
    }
    expedition.install_assignment({
        "assignment_id": assignment_id,
        "outing_floor_id": "floor_one",
        "destination_floor_id": "floor_two",
        "category": "material",
        "report_content_id": None,
        "frozen_outcome": outcome,
        "expedition_drifter_ids": pair,
        "started_at_utc": started,
        "last_observed_at_utc": completed,
        "completed_at_utc": completed,
    })
    expedition.settle_assignment({
        "report_id": assignment_id,
        "outing_floor_id": "floor_one",
        "destination_floor_id": "floor_two",
        "category": "material",
        "report_content_id": None,
        "frozen_outcome": outcome,
        "expedition_drifter_ids": pair,
        "started_at_utc": started,
        "completed_at_utc": completed,
        "secured_base_xp": 0,
        "experience_awards": {},
        "reward_item_id": "grade_ii_metal",
        "reward_quantity": 1,
        "claimed": False,
    })
    game._expedition_state = expedition
    historical = build_save_document(game)
    historical["schema_version"] = 28
    for record in historical["expedition"]["reports"]:
        record.pop("frozen_outcome")
        record.pop("report_content_id")
    original = deepcopy(historical)

    assert validate_profile_payload(historical) == original
    migrated = validate_save_document(historical)

    assert historical == original
    assert migrated["schema_version"] == 29
    assert migrated["expedition"]["reports"][0]["report_content_id"] is None
    assert migrated["expedition"]["reports"][0]["frozen_outcome"] == outcome


def _historical_expedition_document(tmp_path, schema_version):
    from copy import deepcopy

    from app.persistence.save_document import build_save_document

    game = _m6_ready_game()
    port = make_test_save_port(tmp_path / f"schema-{schema_version}.json")
    launched = _service(port, 720 + schema_version).launch(
        game,
        outing_floor_id="floor_one",
        destination_floor_id="floor_two",
        category="material",
        confirmed=True,
    )
    assert launched.status is ExpeditionLaunchStatus.LAUNCHED
    document = build_save_document(launched.game_state)
    document["schema_version"] = schema_version
    if schema_version < 25:
        document["party"].pop("hub_economy", None)
    if schema_version < 26:
        for field in (
            "floor_four_cleared",
            "floor_five_cleared",
            "region_two_unlocked",
        ):
            document["party"].pop(field, None)
    if schema_version < 27:
        for field in (
            "floor_four_runs_started_after_clear",
            "floor_four_run_id",
            "floor_four_outing_xp_multiplier_percent",
        ):
            document["party"].pop(field, None)
    if schema_version < 26:
        document["story"].pop("knowledge_facts", None)

    document["expedition"]["energy"] = 73
    document["expedition"]["energy_anchor_utc"] = "2026-11-20T11:51:00Z"
    document["expedition"]["active_assignment"].pop("frozen_outcome")
    document["expedition"]["active_assignment"].pop("report_content_id")
    document["expedition"]["active_assignment"]["last_observed_at_utc"] = (
        "2026-11-20T12:09:00Z"
    )
    document["expedition"]["reports"] = [
            {
                "report_id": "00000000-0000-4000-8000-000000000712",
                "outing_floor_id": "floor_one",
                "destination_floor_id": "floor_one",
                "category": "material",
                "expedition_drifter_ids": ["joruun", "zhaivra"],
                "started_at_utc": "2026-11-19T11:00:00Z",
                "completed_at_utc": "2026-11-19T11:20:00Z",
                "secured_base_xp": 0,
                "experience_awards": {},
                "reward_item_id": "grade_i_metal",
                "reward_quantity": 1,
                "claimed": True,
            },
            {
                "report_id": "00000000-0000-4000-8000-000000000713",
                "outing_floor_id": "floor_two",
                "destination_floor_id": "floor_three",
                "category": "material",
                "expedition_drifter_ids": ["joruun", "zhaivra"],
                "started_at_utc": "2026-11-18T11:00:00Z",
                "completed_at_utc": "2026-11-18T11:20:00Z",
                "secured_base_xp": 0,
                "experience_awards": {},
                "reward_item_id": "grade_iii_metal",
                "reward_quantity": 1,
                "claimed": False,
            },
        ]
    return document


@pytest.mark.parametrize("schema_version", (24, 25, 26, 27, 28))
def test_historical_expedition_records_migrate_immutably_from_schemas_24_to_28(
    tmp_path, schema_version,
):
    from copy import deepcopy

    from app.persistence.save_document import (
        DISK_SCHEMA_VERSION,
        reconstruct_game_state,
        validate_profile_payload,
        validate_save_document,
    )

    historical = _historical_expedition_document(tmp_path, schema_version)
    original = deepcopy(historical)
    original_expedition = deepcopy(historical["expedition"])

    assert validate_profile_payload(historical) == original
    migrated = validate_save_document(historical)
    restored = reconstruct_game_state(historical)

    assert historical == original
    assert migrated["schema_version"] == DISK_SCHEMA_VERSION == 29
    assert migrated["expedition"]["energy"] == original_expedition["energy"]
    assert migrated["expedition"]["energy_anchor_utc"] == original_expedition[
        "energy_anchor_utc"
    ]
    assignment = migrated["expedition"]["active_assignment"]
    assert {
        key: value for key, value in assignment.items()
        if key not in {"frozen_outcome", "report_content_id"}
    } == original_expedition["active_assignment"]
    assert assignment["frozen_outcome"] == {
        "source_id": None,
        "reward_item_id": "grade_ii_metal",
        "reward_quantity": 1,
    }
    assert assignment["report_content_id"] is None
    for actual, original_report in zip(
        migrated["expedition"]["reports"], original_expedition["reports"]
    ):
        assert {
            key: value for key, value in actual.items()
            if key not in {"frozen_outcome", "report_content_id"}
        } == original_report
        grade = {"floor_one": "i", "floor_three": "iii"}[
            original_report["destination_floor_id"]
        ]
        assert actual["frozen_outcome"] == {
            "source_id": None,
            "reward_item_id": f"grade_{grade}_metal",
            "reward_quantity": 1,
        }
        assert actual["report_content_id"] is None
    assert [report["claimed"] for report in restored.expedition_state.reports] == [
        True,
        False,
    ]


@pytest.mark.parametrize("schema_version", (24, 25, 26, 27, 28))
@pytest.mark.parametrize(
    ("field", "value"),
    (("reward_item_id", "grade_ii_metal"), ("reward_quantity", 2)),
)
def test_historical_material_report_rejects_wrong_item_or_quantity(
    tmp_path, schema_version, field, value
):
    from app.persistence.save_document import (
        SaveStateValidationError,
        validate_profile_payload,
        validate_save_document,
    )

    historical = _historical_expedition_document(tmp_path, schema_version)
    historical["expedition"]["reports"][0][field] = value

    with pytest.raises(SaveStateValidationError, match="Material report reward"):
        validate_profile_payload(historical)
    with pytest.raises(SaveStateValidationError, match="Material report reward"):
        validate_save_document(historical)
