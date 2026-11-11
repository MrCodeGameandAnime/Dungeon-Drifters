import copy
import importlib

import pytest

from app.content.permanent_discovery_spec import (
    PermanentDiscoverySource,
    PermanentDiscoveryType,
)
from app.game.party_state import DungeonPhase
from app.game.permanent_discovery import (
    DiscoveryClaimStatus,
    PermanentDiscoveryService,
)
from app.persistence.save_document import (
    SaveStateValidationError,
    build_save_document,
    reconstruct_game_state,
)
from app.persistence.ports import SaveLoadResult
from app.persistence.save_port_contract import SaveLoadStatus
from tests.game_test_support import completed_hub_game, three_member_hub_game


def load_event_module():
    try:
        return importlib.import_module("app.game.run_events")
    except ModuleNotFoundError:
        return None


class SequenceRng:
    def __init__(self, rolls):
        self.rolls = list(rolls)
        self.calls = 0

    def randint(self, minimum, maximum):
        self.calls += 1
        assert minimum == 1
        assert maximum == 10000
        return self.rolls.pop(0)


class ScriptedArmorRng:
    def __init__(self, rolls):
        self.rolls = list(rolls)
        self.calls = 0

    def randrange(self, stop):
        self.calls += 1
        value = self.rolls.pop(0)
        assert 0 <= value < stop
        return value

    def randint(self, minimum, maximum):
        return self.randrange(maximum - minimum + 1) + minimum


class MemorySavePort:
    def __init__(self, status=SaveLoadStatus.SAVED):
        self.status = status
        self.saved_states = []

    def inspect(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def load(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def save(self, game_state):
        if self.status is SaveLoadStatus.SAVED:
            self.saved_states.append(game_state.clone())
        return SaveLoadResult(self.status)


def floor_two_game():
    game = completed_hub_game()
    party = game.party_state
    assert party.start_floor_one_run() == 100
    assert party.complete_floor_one_boss(game.active_party_members)
    assert party.start_floor_two_run(run_id_factory=lambda: "floor-two-run") == 100
    game.overworld_state.begin_route("floor_two")
    return game


def searchable_well():
    catalog = importlib.import_module("app.content.catalog")
    if not hasattr(catalog, "get_permanent_discovery_source"):
        return None
    return catalog.get_permanent_discovery_source("ancient_well_floor2_01")


def test_run_event_service_resolves_enemy_drops_and_encounter_rewards_once():
    content = importlib.import_module("app.content.enemy_spec")
    events = load_event_module()
    assert hasattr(content, "ItemDropSpec")
    assert events is not None
    assert hasattr(events, "RunEventService")
    ItemDropSpec = content.ItemDropSpec
    service_type = events.RunEventService

    game = floor_two_game()
    save_port = MemorySavePort()
    rng = SequenceRng([1, 10000])
    service = service_type(save_port=save_port, rng=rng)
    tables = (
        (ItemDropSpec("grade_ii_metal", 1, 2000),),
        (ItemDropSpec("grade_ii_fiber", 2, 2000),),
    )

    first = service.resolve_encounter_rewards(
        game,
        node_id="floor_two_battle_01",
        experience=100,
        gold=12,
        enemy_drop_tables=tables,
    )
    replay = service.resolve_encounter_rewards(
        first.game_state.clone(),
        node_id="floor_two_battle_01",
        experience=100,
        gold=12,
        enemy_drop_tables=tables,
    )

    assert first.status.value == "resolved"
    assert first.game_state.party_state.outing_rewards.snapshot() == {
        "experience": 100,
        "gold": 12,
        "items": {"grade_ii_metal": 1},
    }
    assert len(first.game_state.party_state.resolved_run_events) == 3
    assert replay.status.value == "already_resolved"
    assert replay.game_state.party_state.outing_rewards.snapshot() == (
        first.game_state.party_state.outing_rewards.snapshot()
    )
    assert rng.calls == 2
    assert len(save_port.saved_states) == 1
    saved = save_port.saved_states[0]
    assert saved.party_state.outing_rewards.snapshot() == {
        "experience": 100,
        "gold": 12,
        "items": {"grade_ii_metal": 1},
    }
    assert saved.party_state.resolved_run_events == (
        first.game_state.party_state.resolved_run_events
    )


def test_failed_drop_commit_leaves_rewards_and_event_evidence_unchanged():
    event_module = load_event_module()
    assert event_module is not None
    content = importlib.import_module("app.content.enemy_spec")
    game = floor_two_game()
    rng = SequenceRng([1])
    service = event_module.RunEventService(
        save_port=MemorySavePort(SaveLoadStatus.INVALID),
        rng=rng,
    )

    result = service.resolve_encounter_rewards(
        game,
        node_id="floor_two_battle_01",
        experience=100,
        gold=12,
        enemy_drop_tables=((content.ItemDropSpec("grade_ii_metal", 1, 2000),),),
    )

    assert result.status.value == "save_failed"
    assert result.game_state is game
    assert game.party_state.outing_rewards.snapshot() == {
        "experience": 0,
        "gold": 0,
        "items": {},
    }
    assert game.party_state.resolved_run_events == ()
    assert game.party_state.phase is DungeonPhase.OUTING


def test_drop_replay_rejects_a_changed_authored_table_for_the_same_event():
    content = importlib.import_module("app.content.enemy_spec")
    events = load_event_module()
    game = floor_two_game()
    service = events.RunEventService(
        save_port=MemorySavePort(),
        rng=SequenceRng([1]),
    )
    first = service.resolve_encounter_rewards(
        game,
        node_id="floor_two_battle_01",
        experience=100,
        gold=12,
        enemy_drop_tables=((content.ItemDropSpec("grade_ii_metal", 1, 2000),),),
    )

    try:
        service.resolve_encounter_rewards(
            first.game_state,
            node_id="floor_two_battle_01",
            experience=100,
            gold=12,
            enemy_drop_tables=((content.ItemDropSpec("grade_ii_fiber", 1, 2000),),),
        )
    except ValueError as error:
        assert "different inputs" in str(error)
    else:
        raise AssertionError("changed drop inputs reused an existing event key")


def test_search_uses_only_the_selected_active_drifters_intuition_and_persists_found_source():
    event_module = load_event_module()
    assert event_module is not None
    source = searchable_well()
    assert source is not None
    high_intuition_game = floor_two_game()
    low_intuition_game = floor_two_game()
    high_intuition = high_intuition_game.active_party_members[0]
    low_intuition = low_intuition_game.active_party_members[1]
    high_intuition.stats.permanent_stats.set_stat("intuition", 100)
    low_intuition.stats.permanent_stats.set_stat("intuition", 10)
    high_rng = SequenceRng([1700])
    low_rng = SequenceRng([1001])
    high_save = MemorySavePort()
    high_service = event_module.RunEventService(
        save_port=high_save, rng=high_rng
    )
    low_service = event_module.RunEventService(
        save_port=MemorySavePort(), rng=low_rng
    )

    high_result = high_service.search_discovery(
        high_intuition_game,
        node_id="floor_two_pre_boss_rest",
        searcher_drifter_id="branoc",
        source=source,
    )
    low_result = low_service.search_discovery(
        low_intuition_game,
        node_id="floor_two_pre_boss_rest",
        searcher_drifter_id="azhvielle",
        source=source,
    )

    assert high_result.found is True
    assert high_result.effective_chance_bps == 1700
    assert high_result.game_state.world_state.discovered_permanent_discovery_sources == (
        "ancient_well_floor2_01",
    )
    assert high_save.saved_states[0].world_state.discovered_permanent_discovery_sources == (
        "ancient_well_floor2_01",
    )
    assert high_save.saved_states[0].party_state.resolved_run_events == (
        high_result.game_state.party_state.resolved_run_events
    )
    assert low_result.found is False
    assert low_result.effective_chance_bps == 1000
    assert low_result.game_state.world_state.discovered_permanent_discovery_sources == ()
    assert high_rng.calls == low_rng.calls == 1


def test_found_source_uses_m3_claim_service_for_one_selected_active_drifter():
    events = load_event_module()
    source = searchable_well()
    game = floor_two_game()
    search_result = events.RunEventService(
        save_port=MemorySavePort(),
        rng=SequenceRng([1]),
    ).search_discovery(
        game,
        node_id="floor_two_pre_boss_rest",
        searcher_drifter_id="branoc",
        source=source,
    )
    target_before = search_result.game_state.member_for_drifter_id("azhvielle")
    hp_before = target_before.health.maximum
    other_hp_before = search_result.game_state.member_for_drifter_id(
        "branoc"
    ).health.maximum
    claim_service = PermanentDiscoveryService(
        (source,),
        save_port=MemorySavePort(),
    )

    claim = claim_service.consume(
        search_result.game_state,
        source.source_id,
        "azhvielle",
        confirmed=True,
    )

    assert claim.status is DiscoveryClaimStatus.CLAIMED
    assert claim.game_state.member_for_drifter_id("azhvielle").health.maximum == (
        hp_before + 5
    )
    assert claim.game_state.member_for_drifter_id("branoc").health.maximum == (
        other_hp_before
    )
    assert claim.game_state.world_state.permanent_discovery_claims == (
        source.source_id,
    )
    assert claim.game_state.world_state.discovered_permanent_discovery_sources == (
        source.source_id,
    )


def test_search_replay_returns_stored_failure_without_rerolling():
    event_module = load_event_module()
    assert event_module is not None
    source = searchable_well()
    assert source is not None
    rng = SequenceRng([10000])
    service = event_module.RunEventService(save_port=MemorySavePort(), rng=rng)
    game = floor_two_game()

    first = service.search_discovery(
        game,
        node_id="floor_two_pre_boss_rest",
        searcher_drifter_id="branoc",
        source=source,
    )
    replay = service.search_discovery(
        first.game_state.clone(),
        node_id="floor_two_pre_boss_rest",
        searcher_drifter_id="branoc",
        source=source,
    )

    assert first.found is False
    assert replay.status.value == "already_resolved"
    assert replay.found is False
    assert replay.roll == 10000
    assert rng.calls == 1


def test_search_replay_rejects_a_different_searcher_for_the_same_event():
    events = load_event_module()
    source = searchable_well()
    game = floor_two_game()
    service = events.RunEventService(
        save_port=MemorySavePort(),
        rng=SequenceRng([10000]),
    )
    first = service.search_discovery(
        game,
        node_id="floor_two_pre_boss_rest",
        searcher_drifter_id="branoc",
        source=source,
    )

    try:
        service.search_discovery(
            first.game_state,
            node_id="floor_two_pre_boss_rest",
            searcher_drifter_id="azhvielle",
            source=source,
        )
    except ValueError as error:
        assert "searcher" in str(error)
    else:
        raise AssertionError("a second searcher reused the first search event")


def test_failed_search_commit_leaves_source_and_event_history_unchanged():
    events = load_event_module()
    source = searchable_well()
    game = floor_two_game()
    service = events.RunEventService(
        save_port=MemorySavePort(SaveLoadStatus.INVALID),
        rng=SequenceRng([1]),
    )

    result = service.search_discovery(
        game,
        node_id="floor_two_pre_boss_rest",
        searcher_drifter_id="branoc",
        source=source,
    )

    assert result.status.value == "save_failed"
    assert result.game_state is game
    assert game.world_state.discovered_permanent_discovery_sources == ()
    assert game.party_state.resolved_run_events == ()


def test_failed_search_can_be_retried_in_a_new_run():
    events = load_event_module()
    source = searchable_well()
    game = floor_two_game()
    rng = SequenceRng([10000, 1])
    service = events.RunEventService(save_port=MemorySavePort(), rng=rng)
    first = service.search_discovery(
        game,
        node_id="floor_two_pre_boss_rest",
        searcher_drifter_id="branoc",
        source=source,
    )
    assert first.found is False
    assert first.game_state.party_state.fail_floor_two_run(
        first.game_state.active_party_members
    )
    assert first.game_state.party_state.start_floor_two_run(
        run_id_factory=lambda: "floor-two-run-retry"
    ) == 100

    second = service.search_discovery(
        first.game_state,
        node_id="floor_two_pre_boss_rest",
        searcher_drifter_id="branoc",
        source=source,
    )

    assert second.found is True
    assert second.game_state.world_state.discovered_permanent_discovery_sources == (
        "ancient_well_floor2_01",
    )
    assert rng.calls == 2


def test_armor_reward_event_persists_generated_result_and_replay_after_reload_does_not_reroll():
    events = load_event_module()
    game = floor_two_game()
    save_port = MemorySavePort()
    rng = ScriptedArmorRng([0, 2, 1, 99])
    service = events.RunEventService(save_port=save_port, rng=rng)
    instance_id = "00000000-0000-4000-8000-000000000351"

    first = service.resolve_armor_reward(
        game,
        node_id="floor_two_battle_01",
        template_id="field_chest",
        source_id="floor_two_battle_01_armor_01",
        instance_id_factory=lambda: instance_id,
    )
    reloaded = reconstruct_game_state(
        build_save_document(save_port.saved_states[0])
    )
    replay = service.resolve_armor_reward(
        reloaded,
        node_id="floor_two_battle_01",
        template_id="field_chest",
        source_id="floor_two_battle_01_armor_01",
        instance_id_factory=lambda: "00000000-0000-4000-8000-000000000352",
    )

    assert first.status.value == "resolved"
    assert replay.status.value == "already_resolved"
    assert first.equipment_instance_id == replay.equipment_instance_id == instance_id
    assert len(first.game_state.party_state.equipment_instances) == 1
    assert len(replay.game_state.party_state.equipment_instances) == 1
    assert replay.game_state.party_state.equipment_instance(instance_id).snapshot() == (
        first.game_state.party_state.equipment_instance(instance_id).snapshot()
    )
    assert rng.calls == 4
    assert len(save_port.saved_states) == 1

    saved_payload = build_save_document(save_port.saved_states[0])
    missing_item = copy.deepcopy(saved_payload)
    missing_item["party"]["equipment_instances"] = []
    with pytest.raises(SaveStateValidationError, match="not owned by the party"):
        reconstruct_game_state(missing_item)

    mismatched_item = copy.deepcopy(saved_payload)
    mismatched_item["party"]["equipment_instances"][0]["rarity"] = "uncommon"
    with pytest.raises(SaveStateValidationError, match="disagrees with its owned instance"):
        reconstruct_game_state(mismatched_item)


def test_armor_reward_event_rejects_reused_key_with_different_authored_inputs():
    events = load_event_module()
    game = floor_two_game()
    rng = ScriptedArmorRng([0, 0, 99])
    service = events.RunEventService(save_port=MemorySavePort(), rng=rng)
    first = service.resolve_armor_reward(
        game,
        node_id="floor_two_battle_01",
        template_id="field_helm",
        source_id="floor_two_battle_01_armor_02",
        instance_id_factory=lambda: "00000000-0000-4000-8000-000000000353",
    )

    try:
        service.resolve_armor_reward(
            first.game_state,
            node_id="floor_two_battle_01",
            template_id="field_chest",
            source_id="floor_two_battle_01_armor_02",
            instance_id_factory=lambda: "00000000-0000-4000-8000-000000000354",
        )
    except ValueError as error:
        assert "different inputs" in str(error)
    else:
        raise AssertionError("changed armor inputs reused an existing reward key")

    assert rng.calls == 3


def test_failed_armor_reward_commit_leaves_no_item_or_event_evidence():
    events = load_event_module()
    game = floor_two_game()
    rng = ScriptedArmorRng([0, 0, 99])
    save_port = MemorySavePort(SaveLoadStatus.INVALID)
    service = events.RunEventService(save_port=save_port, rng=rng)

    result = service.resolve_armor_reward(
        game,
        node_id="floor_two_battle_01",
        template_id="field_helm",
        source_id="floor_two_battle_01_armor_03",
        instance_id_factory=lambda: "00000000-0000-4000-8000-000000000355",
    )

    assert result.status.value == "save_failed"
    assert result.game_state is game
    assert game.party_state.equipment_instances == ()
    assert game.party_state.resolved_run_events == ()
    assert save_port.saved_states == []


def test_search_rejects_a_benched_searcher_without_writing():
    event_module = load_event_module()
    assert event_module is not None
    source = searchable_well()
    assert source is not None
    game = floor_two_game()
    save_port = MemorySavePort()
    rng = SequenceRng([1])
    service = event_module.RunEventService(save_port=save_port, rng=rng)

    result = service.search_discovery(
        game,
        node_id="floor_two_pre_boss_rest",
        searcher_drifter_id="joruun",
        source=source,
    )

    assert result.status.value == "invalid_target"
    assert result.game_state is game
    assert rng.calls == 0
    assert save_port.saved_states == []


def test_search_rejects_unauthored_source_without_rolling_or_writing():
    events = load_event_module()
    game = floor_two_game()
    source = PermanentDiscoverySource(
        "ancient_well_unknown",
        PermanentDiscoveryType.ANCIENT_WELL,
        5,
        search_chance_bps=1000,
    )
    rng = SequenceRng([1])
    save_port = MemorySavePort()
    service = events.RunEventService(save_port=save_port, rng=rng)

    result = service.search_discovery(
        game,
        node_id="floor_two_pre_boss_rest",
        searcher_drifter_id="branoc",
        source=source,
    )

    assert result.status.value == "invalid_source"
    assert result.game_state is game
    assert rng.calls == 0
    assert save_port.saved_states == []


def test_search_rejects_authored_source_at_the_wrong_route_node():
    events = load_event_module()
    source = searchable_well()
    game = floor_two_game()
    rng = SequenceRng([1])
    save_port = MemorySavePort()
    service = events.RunEventService(save_port=save_port, rng=rng)

    result = service.search_discovery(
        game,
        node_id="floor_two_midway_rest",
        searcher_drifter_id="branoc",
        source=source,
    )

    assert result.status.value == "invalid_source"
    assert result.game_state is game
    assert rng.calls == 0
    assert save_port.saved_states == []


def test_search_rejects_modified_authored_source_without_rolling_or_writing():
    events = load_event_module()
    authored = searchable_well()
    game = floor_two_game()
    modified = PermanentDiscoverySource(
        authored.source_id,
        authored.discovery_type,
        authored.amount,
        search_chance_bps=authored.search_chance_bps + 1,
    )
    rng = SequenceRng([1])
    save_port = MemorySavePort()
    service = events.RunEventService(save_port=save_port, rng=rng)

    result = service.search_discovery(
        game,
        node_id="floor_two_pre_boss_rest",
        searcher_drifter_id="branoc",
        source=modified,
    )

    assert result.status.value == "invalid_source"
    assert result.game_state is game
    assert rng.calls == 0
    assert save_port.saved_states == []


def test_run_event_evidence_and_discovered_source_survive_save_reload():
    events = load_event_module()
    content = importlib.import_module("app.content.enemy_spec")
    game = floor_two_game()
    source = searchable_well()
    initial_shared_gold = game.party_state.shared_gold
    save_port = MemorySavePort()
    first_rng = SequenceRng([1, 1])
    service = events.RunEventService(save_port=save_port, rng=first_rng)
    drop_result = service.resolve_encounter_rewards(
        game,
        node_id="floor_two_battle_01",
        experience=100,
        gold=12,
        enemy_drop_tables=(
            (content.ItemDropSpec("grade_ii_metal", 1, 2000),),
        ),
    )
    search_result = service.search_discovery(
        drop_result.game_state,
        node_id="floor_two_pre_boss_rest",
        searcher_drifter_id="branoc",
        source=source,
    )
    assert search_result.found
    assert search_result.game_state.party_state.complete_floor_two_boss(
        search_result.game_state.active_party_members
    )
    search_result.game_state.overworld_state.return_to_surface_entrance()

    restored = reconstruct_game_state(build_save_document(search_result.game_state))
    assert restored.party_state.resolved_run_events == (
        search_result.game_state.party_state.resolved_run_events
    )
    assert restored.world_state.discovered_permanent_discovery_sources == (
        "ancient_well_floor2_01",
    )
    assert restored.party_state.shared_gold == initial_shared_gold + 12
    assert restored.party_state.shared_items == {"grade_ii_metal": 1}

    assert restored.party_state.start_floor_two_run(
        run_id_factory=lambda: "floor-two-run-retry"
    ) == 50
    retry_rng = SequenceRng([])
    retry_service = events.RunEventService(
        save_port=MemorySavePort(),
        rng=retry_rng,
    )
    retry = retry_service.search_discovery(
        restored,
        node_id="floor_two_pre_boss_rest",
        searcher_drifter_id="branoc",
        source=source,
    )
    assert retry.status.value == "already_found"
    assert retry_rng.calls == 0


def test_settled_run_event_history_does_not_block_a_new_active_pair():
    events = load_event_module()
    game = three_member_hub_game()
    party = game.party_state
    assert party.start_floor_one_run() == 100
    assert party.complete_floor_one_boss(game.active_party_members)
    assert party.start_floor_two_run(run_id_factory=lambda: "search-run") == 100

    source = searchable_well()
    search = events.RunEventService(
        save_port=MemorySavePort(),
        rng=SequenceRng([10000]),
    ).search_discovery(
        game,
        node_id="floor_two_pre_boss_rest",
        searcher_drifter_id="branoc",
        source=source,
    )
    assert search.status.value == "resolved"
    assert not search.found

    party = search.game_state.party_state
    assert party.fail_floor_two_run(search.game_state.active_party_members)
    search.game_state.overworld_state.return_to_surface_entrance()
    party.select_active_pair(
        ("azhvielle", "joruun"),
        recruited_ids=("branoc", "azhvielle", "joruun"),
    )

    document = build_save_document(search.game_state)
    restored = reconstruct_game_state(document)

    assert restored.party_state.active_drifter_ids == ("azhvielle", "joruun")
    assert restored.party_state.resolved_run_events == ()


def test_legacy_settled_search_history_is_ignored_after_pair_change():
    game = three_member_hub_game()
    party = game.party_state
    assert party.start_floor_one_run() == 100
    assert party.complete_floor_one_boss(game.active_party_members)
    run_id = party.start_floor_two_run(run_id_factory=lambda: "legacy-search-run")
    assert run_id == 100
    search_event = {
        "event_key": (
            "floor_two:legacy-search-run:floor_two_pre_boss_rest:"
            "discovery_search"
        ),
        "run_id": "legacy-search-run",
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
    party.record_run_event(search_event)
    assert party.fail_floor_two_run(game.active_party_members)
    game.overworld_state.return_to_surface_entrance()
    party.select_active_pair(
        ("azhvielle", "joruun"),
        recruited_ids=("branoc", "azhvielle", "joruun"),
    )

    legacy_save = build_save_document(game)
    legacy_save["schema_version"] = 22
    legacy_save.pop("expedition")
    for field in (
        "floor_three_cleared",
        "floor_three_runs_started_after_clear",
        "floor_three_run_id",
        "floor_three_outing_xp_multiplier_percent",
    ):
        legacy_save["party"].pop(field)
    legacy_save["party"]["resolved_run_events"] = [search_event]

    restored = reconstruct_game_state(legacy_save)

    assert restored.party_state.active_drifter_ids == ("azhvielle", "joruun")
    assert restored.party_state.resolved_run_events == ()
