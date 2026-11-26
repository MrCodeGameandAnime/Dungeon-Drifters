import copy

from app.content.catalog import get_encounter_spec, get_route_spec
from app.content.catalog import get_permanent_discovery_source
from app.content.route_spec import RouteNodeKind
from app.content.region_progression_spec import M8_ASHEN_ARENA_REVEALED_EVENT_ID
from app.game.game_state import GameState
from app.game.overworld_session import OverworldSession
from app.game.permanent_discovery import (
    DiscoveryClaimStatus,
    PermanentDiscoveryService,
)
from app.game.region_progression import destination_availability
from app.game.story_state import KnowledgeStatus
from app.persistence.ports import SaveLoadResult
from app.persistence.save_document import (
    DISK_SCHEMA_VERSION,
    build_save_document,
    reconstruct_game_state,
    validate_profile_payload,
    validate_save_document,
)
from app.persistence.save_port_contract import SaveLoadStatus
from app.player.player_state import PlayerState
from app.combat.battle import Battle
from app.content.catalog import create_enemy_state, get_drifter_spec
from app.presentation.battle_models import BattleView
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.ui.overworld_ui import (
    ChooseDestination,
    ChooseDiscoverySearcher,
    ChooseDiscoveryTarget,
    ChooseExpeditionReport,
    ChooseOverworldAction,
    ChooseRegion,
)
from tests.game_test_support import completed_hub_game


class StableRng:
    def randint(self, minimum, maximum):
        return minimum

    def choice(self, values):
        return values[0]


class RecordingSavePort:
    def __init__(self, *, fail_on_save_calls=()):
        self.save_calls = 0
        self.fail_on_save_calls = set(fail_on_save_calls)
        self.saved_states = []

    def inspect(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def load(self):
        return self.inspect()

    def save(self, game_state):
        self.save_calls += 1
        self.saved_states.append(game_state.clone())
        status = (
            SaveLoadStatus.INVALID
            if self.save_calls in self.fail_on_save_calls
            else SaveLoadStatus.SAVED
        )
        return SaveLoadResult(status)


class ValidatingSavePort(RecordingSavePort):
    def save(self, game_state):
        validate_save_document(build_save_document(game_state))
        return super().save(game_state)


class FailedSearchRng(StableRng):
    def randint(self, minimum, maximum):
        return maximum


def floor_five_ready_game(*, floor_four_cleared=True):
    game = completed_hub_game()
    existing = {
        member.character.profile.drifter_id for member in game.recruited_members
    }
    for drifter_id in ("azhvielle", "branoc", "joruun", "zhaivra"):
        if drifter_id not in existing:
            companion = PlayerState(get_drifter_spec(drifter_id).create_character())
            assert game.party_state.recruit_companion(
                game.player_state,
                companion,
                cost=0,
            )
    game.party_state._floor_one_cleared = True
    game.party_state._floor_two_cleared = True
    game.party_state._floor_three_cleared = True
    game.party_state._floor_four_cleared = floor_four_cleared
    if floor_four_cleared:
        game.story_state.reveal_knowledge_fact(
            "m8_fact_ashen_vault", KnowledgeStatus.RUMORED
        )
    return game


def make_session(game, save_port, *, now_factory=None, run_event_rng=None):
    options = {} if now_factory is None else {"now_factory": now_factory}
    return OverworldSession(
        game,
        battle_factory=lambda player, enemies, **kwargs: Battle(
            player,
            enemies,
            rng=StableRng(),
            **kwargs,
        ),
        enemy_factory=create_enemy_state,
        save_port=save_port,
        run_event_rng=run_event_rng or StableRng(),
        **options,
    )


def test_floor_five_approach_has_the_approved_seven_nodes_and_compositions():
    route = get_route_spec("floor_five_approach")

    assert tuple(node.node_id for node in route.nodes) == (
        "floor_five_battle_01",
        "floor_five_battle_02",
        "floor_five_battle_03",
        "floor_five_rest_midpoint",
        "floor_five_battle_04",
        "floor_five_battle_05",
        "floor_five_battle_06",
    )
    expected = (
        ("ashbound_hound", "drowned_stalker"),
        ("brine_oracle", "ashbound_hound"),
        ("reliquary_sentinel", "reliquary_sentinel"),
        ("ashbound_hound", "ashbound_hound"),
        ("reliquary_sentinel", "brine_oracle", "drowned_stalker"),
        ("brine_oracle", "brine_oracle", "ashbound_hound"),
    )
    battle_nodes = tuple(
        node for node in route.nodes if node.kind is RouteNodeKind.COMBAT
    )
    assert tuple(
        get_encounter_spec(node.encounter_id).enemy_archetype_ids
        for node in battle_nodes
    ) == expected
    assert route.nodes[3].kind is RouteNodeKind.REST


def test_ashen_vault_requires_floor_four_clear_and_rumored_knowledge():
    locked = floor_five_ready_game(floor_four_cleared=False)
    locked.story_state.reveal_knowledge_fact(
        "m8_fact_ashen_vault", KnowledgeStatus.RUMORED
    )
    assert not destination_availability(locked, "ashen_vault").enabled

    unknown = floor_five_ready_game()
    unknown.story_state._knowledge_facts.pop("m8_fact_ashen_vault")
    assert not destination_availability(unknown, "ashen_vault").visible

    available = floor_five_ready_game()
    assert destination_availability(available, "ashen_vault").enabled


def test_ashen_vault_accepts_each_of_the_six_legal_active_pairs():
    from itertools import combinations

    baseline = floor_five_ready_game()
    recruited_ids = tuple(
        member.character.profile.drifter_id
        for member in baseline.recruited_members
    )
    for pair in combinations(recruited_ids, 2):
        game = baseline.clone()
        game.party_state.select_active_pair(pair, recruited_ids=recruited_ids)
        session = make_session(game, RecordingSavePort())
        session.submit(ChooseOverworldAction(OverworldAction.REGION_PORTAL))
        session.submit(ChooseRegion("region_1"))
        view = session.submit(ChooseDestination("ashen_vault"))

        assert isinstance(view, BattleView), pair
        assert game.party_state.active_drifter_ids == pair
        assert tuple(
            member.character.profile.drifter_id
            for member in session.active_battle.party_states
        ) == pair


def test_floor_five_entry_confirms_destination_and_starts_two_member_tier_three_run():
    game = floor_five_ready_game()
    save_port = RecordingSavePort()
    session = make_session(game, save_port)

    session.submit(ChooseOverworldAction(OverworldAction.REGION_PORTAL))
    session.submit(ChooseRegion("region_1"))
    view = session.submit(ChooseDestination("ashen_vault"))

    assert isinstance(view, BattleView)
    assert session.game_state.overworld_state.active_route_id == "floor_five_approach"
    assert session.game_state.party_state.active_run_floor_id == "floor_five"
    assert len(session.active_battle.party_states) == 2
    assert all(enemy.tier == 3 for enemy in session.active_battle.enemies)
    assert (
        session.game_state.story_state.knowledge_status("m8_fact_ashen_vault")
        is KnowledgeStatus.CONFIRMED
    )
    assert save_port.saved_states


def test_floor_five_entry_save_failure_preserves_party_route_and_knowledge():
    game = floor_five_ready_game()
    before_party = game.party_state.snapshot()
    before_overworld = game.overworld_state.snapshot()
    before_story = game.story_state.snapshot()
    session = make_session(game, RecordingSavePort(fail_on_save_calls={1}))

    session.submit(ChooseOverworldAction(OverworldAction.REGION_PORTAL))
    session.submit(ChooseRegion("region_1"))
    session.submit(ChooseDestination("ashen_vault"))

    assert session.game_state.party_state.snapshot() == before_party
    assert session.game_state.overworld_state.snapshot() == before_overworld
    assert session.game_state.story_state.snapshot() == before_story
    assert session.active_battle is None


def _defeat_current_encounter(session):
    if session.active_battle is None:
        session.submit(ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER))
    battle = session.active_battle
    assert battle is not None
    assert len(battle.party_states) == 2
    for enemy in battle.enemies:
        assert enemy.tier == 3
        enemy.health.take_damage(enemy.health.current)
    session._finalize_active_battle(winner="player")


def _advance_to_floor_five_midpoint(session):
    for _ in range(3):
        _defeat_current_encounter(session)
    assert session.game_state.overworld_state.current_route_node_id == (
        "floor_five_rest_midpoint"
    )
    assert session.current_view().screen is OverworldScreen.REST


def test_floor_five_midpoint_spirit_relic_claims_three_gp_once_for_one_active_target():
    game = floor_five_ready_game()
    port = RecordingSavePort()
    session = make_session(game, port)
    session.submit(ChooseOverworldAction(OverworldAction.REGION_PORTAL))
    session.submit(ChooseRegion("region_1"))
    session.submit(ChooseDestination("ashen_vault"))
    _advance_to_floor_five_midpoint(session)

    active_ids = session.game_state.party_state.active_drifter_ids
    target_id = active_ids[1]
    source = get_permanent_discovery_source("spirit_relic_floor5_01")
    all_ids = tuple(
        member.character.profile.drifter_id
        for member in session.game_state.recruited_members
    )
    before = {
        drifter_id: session.game_state.member_for_drifter_id(drifter_id).growth_points
        for drifter_id in all_ids
    }

    session.submit(ChooseOverworldAction(OverworldAction.SEARCH_SITE))
    session.submit(ChooseDiscoverySearcher(active_ids[0]))
    assert session.current_view().screen is OverworldScreen.DISCOVERY_TARGETS
    benched_id = next(drifter_id for drifter_id in all_ids if drifter_id not in active_ids)
    session.submit(ChooseDiscoveryTarget(benched_id))
    assert session.current_view().screen is OverworldScreen.DISCOVERY_TARGETS
    assert session.game_state.world_state.permanent_discovery_claims == ()
    assert {
        drifter_id: session.game_state.member_for_drifter_id(drifter_id).growth_points
        for drifter_id in all_ids
    } == before
    session.submit(ChooseDiscoveryTarget(target_id))
    session.submit(ChooseOverworldAction(OverworldAction.CONFIRM))

    assert session.game_state.world_state.discovered_permanent_discovery_sources == (
        source.source_id,
    )
    assert session.game_state.world_state.permanent_discovery_claims == (
        source.source_id,
    )
    for drifter_id in all_ids:
        expected = before[drifter_id] + (3 if drifter_id == target_id else 0)
        assert session.game_state.member_for_drifter_id(drifter_id).growth_points == expected

    restored = reconstruct_game_state(build_save_document(port.saved_states[-1]))
    assert restored.world_state.permanent_discovery_claims == (source.source_id,)
    duplicate = PermanentDiscoveryService(
        (source,),
        save_port=port,
    ).consume(
        restored,
        source.source_id,
        active_ids[0],
        confirmed=True,
    )
    assert duplicate.status is DiscoveryClaimStatus.ALREADY_CLAIMED
    assert duplicate.game_state.member_for_drifter_id(target_id).growth_points == (
        before[target_id] + 3
    )


def test_floor_five_failed_spirit_relic_search_is_persisted_without_reward():
    game = floor_five_ready_game()
    port = RecordingSavePort()
    session = make_session(game, port, run_event_rng=FailedSearchRng())
    session.submit(ChooseOverworldAction(OverworldAction.REGION_PORTAL))
    session.submit(ChooseRegion("region_1"))
    session.submit(ChooseDestination("ashen_vault"))
    _advance_to_floor_five_midpoint(session)
    before_growth = tuple(
        member.growth_points for member in session.game_state.recruited_members
    )

    session.submit(ChooseOverworldAction(OverworldAction.SEARCH_SITE))
    session.submit(
        ChooseDiscoverySearcher(session.game_state.party_state.active_drifter_ids[0])
    )

    assert session.current_view().screen is OverworldScreen.REST
    assert session.game_state.party_state.resolved_run_events[-1]["result"]["found"] is False
    assert session.game_state.world_state.discovered_permanent_discovery_sources == ()
    assert session.game_state.world_state.permanent_discovery_claims == ()
    assert tuple(
        member.growth_points for member in session.game_state.recruited_members
    ) == before_growth
    restored = reconstruct_game_state(build_save_document(port.saved_states[-1]))
    assert restored.party_state.resolved_run_events[-1]["result"]["found"] is False
    assert restored.world_state.permanent_discovery_claims == ()


def test_floor_five_approach_round_trips_midpoint_without_unlocking_reunion():
    game = floor_five_ready_game()
    session = make_session(game, RecordingSavePort())
    session.submit(ChooseOverworldAction(OverworldAction.REGION_PORTAL))
    session.submit(ChooseRegion("region_1"))
    session.submit(ChooseDestination("ashen_vault"))
    _advance_to_floor_five_midpoint(session)

    restored = reconstruct_game_state(build_save_document(session.game_state))

    assert restored.party_state.floor_five_approach_run_id == (
        session.game_state.party_state.floor_five_approach_run_id
    )
    assert restored.party_state.active_run_floor_id == "floor_five"
    assert restored.overworld_state.active_route_id == "floor_five_approach"
    assert restored.overworld_state.current_route_node_id == "floor_five_rest_midpoint"
    assert not restored.party_state.floor_five_cleared
    assert not restored.party_state.region_two_unlocked


def test_floor_five_approach_ends_at_revealed_arena_without_clearing_floor_five():
    game = floor_five_ready_game()
    port = ValidatingSavePort()
    session = make_session(game, port)
    session.submit(ChooseOverworldAction(OverworldAction.REGION_PORTAL))
    session.submit(ChooseRegion("region_1"))
    session.submit(ChooseDestination("ashen_vault"))
    _advance_to_floor_five_midpoint(session)
    session.submit(ChooseOverworldAction(OverworldAction.REST))

    for _ in range(3):
        _defeat_current_encounter(session)

    final_encounter_saves = [
        saved
        for saved in port.saved_states
        if saved.overworld_state.active_route_id == "floor_five_approach"
        and saved.overworld_state.current_route_node_id == "floor_five_battle_06"
        and saved.party_state.floor_five_approach_final_reward_committed
    ]
    assert final_encounter_saves
    assert not final_encounter_saves[-1].overworld_state.route_complete
    assert M8_ASHEN_ARENA_REVEALED_EVENT_ID not in (
        final_encounter_saves[-1].story_state.completed_events
    )

    state = session.game_state
    assert state.overworld_state.active_route_id == "surface"
    assert state.party_state.phase.value == "hub"
    assert M8_ASHEN_ARENA_REVEALED_EVENT_ID in state.story_state.completed_events
    assert not state.party_state.floor_five_cleared
    assert not state.party_state.region_two_unlocked
    assert state.party_state.floor_five_approach_run_id is None
    assert all(
        member.health.current == member.health.maximum
        for member in state.recruited_members
    )
    assert session.current_view().screen is OverworldScreen.HUB
    floor_five_drop_events = [
        event
        for saved in port.saved_states
        for event in saved.party_state.resolved_run_events
        if event["floor_id"] == "floor_five" and event["kind"] == "enemy_drop"
    ]
    assert floor_five_drop_events
    assert all(
        event["result"] == {"entries": [], "items": {}}
        for event in floor_five_drop_events
    )


def test_floor_five_arena_reveal_waits_for_atomic_settlement_retry():
    game = floor_five_ready_game()
    port = RecordingSavePort()
    session = make_session(game, port)
    session.submit(ChooseOverworldAction(OverworldAction.REGION_PORTAL))
    session.submit(ChooseRegion("region_1"))
    session.submit(ChooseDestination("ashen_vault"))
    _advance_to_floor_five_midpoint(session)
    session.submit(ChooseOverworldAction(OverworldAction.REST))
    _defeat_current_encounter(session)
    _defeat_current_encounter(session)

    port.fail_on_save_calls.add(port.save_calls + 2)
    _defeat_current_encounter(session)

    assert session.game_state.floor_five_approach_settlement_pending
    assert M8_ASHEN_ARENA_REVEALED_EVENT_ID not in (
        session.game_state.story_state.completed_events
    )
    assert not session.game_state.party_state.floor_five_cleared
    assert not session.game_state.party_state.region_two_unlocked
    assert OverworldAction.FINALIZE_FLOOR_FIVE_APPROACH in {
        option.action for option in session.current_view().options
    }

    session.submit(
        ChooseOverworldAction(OverworldAction.FINALIZE_FLOOR_FIVE_APPROACH)
    )

    assert M8_ASHEN_ARENA_REVEALED_EVENT_ID in (
        session.game_state.story_state.completed_events
    )
    assert session.game_state.story_state.completed_events.count(
        M8_ASHEN_ARENA_REVEALED_EVENT_ID
    ) == 1
    assert not session.game_state.floor_five_approach_settlement_pending
    assert not session.game_state.party_state.floor_five_cleared
    assert not session.game_state.party_state.region_two_unlocked


def test_floor_five_defeat_and_extraction_do_not_reveal_arena():
    defeated = floor_five_ready_game()
    defeat_session = make_session(defeated, RecordingSavePort())
    defeat_session.submit(ChooseOverworldAction(OverworldAction.REGION_PORTAL))
    defeat_session.submit(ChooseRegion("region_1"))
    defeat_session.submit(ChooseDestination("ashen_vault"))
    battle = defeat_session.active_battle
    for member in battle.party_states:
        member.health.take_damage(member.health.current)
    defeat_session._finalize_active_battle(winner="enemy")
    assert M8_ASHEN_ARENA_REVEALED_EVENT_ID not in (
        defeat_session.game_state.story_state.completed_events
    )

    extracted = floor_five_ready_game()
    extraction_session = make_session(extracted, RecordingSavePort())
    extraction_session.submit(ChooseOverworldAction(OverworldAction.REGION_PORTAL))
    extraction_session.submit(ChooseRegion("region_1"))
    extraction_session.submit(ChooseDestination("ashen_vault"))
    _advance_to_floor_five_midpoint(extraction_session)
    extraction_session.submit(ChooseOverworldAction(OverworldAction.REST))
    extraction_session.submit(ChooseOverworldAction(OverworldAction.EXTRACT))
    extraction_session.submit(ChooseOverworldAction(OverworldAction.RETURN_TO_HUB))
    assert M8_ASHEN_ARENA_REVEALED_EVENT_ID not in (
        extraction_session.game_state.story_state.completed_events
    )


def test_floor_five_approach_can_run_with_a_passive_expedition():
    from datetime import datetime, timedelta, timezone
    from uuid import UUID

    from app.game.expeditions import ExpeditionLaunchStatus, ExpeditionService

    started = datetime(2026, 11, 26, 12, tzinfo=timezone.utc)
    port = RecordingSavePort()
    game = floor_five_ready_game()
    service = ExpeditionService(
        port,
        now_factory=lambda: started,
        assignment_id_factory=lambda: UUID(
            "00000000-0000-4000-8000-000000000871"
        ),
        run_id_factory=lambda: "floor-five-expedition-871",
    )
    launched = service.launch(
        game,
        outing_floor_id="floor_five_approach",
        destination_floor_id="floor_four",
        category="training",
        confirmed=True,
    )

    assert launched.status is ExpeditionLaunchStatus.LAUNCHED
    assert launched.game_state.party_state.active_drifter_ids == (
        game.party_state.active_drifter_ids
    )
    assert launched.game_state.expedition_state.active_assignment[
        "outing_floor_id"
    ] == "floor_five_approach"
    reloaded_assignment = reconstruct_game_state(
        build_save_document(launched.game_state)
    )
    session = make_session(
        reloaded_assignment,
        port,
        now_factory=lambda: started + timedelta(minutes=20),
    )
    _advance_to_floor_five_midpoint(session)
    session.submit(ChooseOverworldAction(OverworldAction.REST))
    for _ in range(3):
        _defeat_current_encounter(session)

    settled = session.game_state
    assert settled.expedition_state.active_assignment is None
    assert len(settled.expedition_state.reports) == 1
    report = settled.expedition_state.reports[0]
    assert report["outing_floor_id"] == "floor_five_approach"
    assert report["destination_floor_id"] == "floor_four"
    assert report["completed_at_utc"] is not None
    assert not report["claimed"]
    settled_reload = reconstruct_game_state(build_save_document(settled))
    assert settled_reload.expedition_state.reports[0]["frozen_outcome"] == (
        report["frozen_outcome"]
    )
    report_session = make_session(
        settled_reload,
        port,
        now_factory=lambda: started + timedelta(minutes=20),
    )
    report_session.submit(ChooseOverworldAction(OverworldAction.EXPEDITIONS))
    report_session.submit(ChooseExpeditionReport(report["report_id"]))
    assert report_session.game_state.expedition_state.reports[0]["claimed"]
    claimed_reload = reconstruct_game_state(
        build_save_document(report_session.game_state)
    )
    assert claimed_reload.expedition_state.reports[0]["claimed"]
    from app.game.expeditions import ExpeditionClaimStatus, ExpeditionService

    duplicate = ExpeditionService(port).claim_report(
        claimed_reload,
        report["report_id"],
        confirmed=True,
    )
    assert duplicate.status is ExpeditionClaimStatus.ALREADY_CLAIMED


def test_floor_five_expedition_launch_write_failure_changes_nothing():
    from app.game.expeditions import ExpeditionLaunchStatus, ExpeditionService

    game = floor_five_ready_game()
    before = game.snapshot()
    result = ExpeditionService(
        RecordingSavePort(fail_on_save_calls={1}),
    ).launch(
        game,
        outing_floor_id="floor_five_approach",
        destination_floor_id="floor_four",
        category="training",
        confirmed=True,
    )

    assert result.status is ExpeditionLaunchStatus.SAVE_FAILED
    assert result.game_state is game
    assert game.snapshot() == before


def test_schema29_migrates_additive_floor_five_run_state_without_mutating_history():
    historical = copy.deepcopy(build_save_document(floor_five_ready_game()))
    historical["party"].pop("floor_five_approach_run_id")
    historical["schema_version"] = 29
    original = copy.deepcopy(historical)

    assert validate_profile_payload(historical) == original
    migrated = validate_save_document(historical)
    restored = reconstruct_game_state(historical)

    assert historical == original
    assert migrated["schema_version"] == DISK_SCHEMA_VERSION == 30
    assert migrated["party"]["floor_five_approach_run_id"] is None
    assert not restored.party_state.floor_five_cleared
    assert not restored.party_state.region_two_unlocked
    assert build_save_document(restored) == migrated


def test_schema29_rejects_floor_five_approach_evidence():
    from app.persistence.save_document import SaveStateValidationError

    game = floor_five_ready_game()
    session = make_session(game, RecordingSavePort())
    session.submit(ChooseOverworldAction(OverworldAction.REGION_PORTAL))
    session.submit(ChooseRegion("region_1"))
    session.submit(ChooseDestination("ashen_vault"))
    historical = build_save_document(session.game_state)
    historical["schema_version"] = 29
    historical["party"].pop("floor_five_approach_run_id")

    try:
        validate_profile_payload(historical)
    except SaveStateValidationError:
        pass
    else:
        raise AssertionError("schema 29 accepted Floor V approach state")
