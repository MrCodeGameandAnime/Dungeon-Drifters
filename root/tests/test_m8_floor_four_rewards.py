from copy import deepcopy

import pytest

from app.content.catalog import (
    get_encounter_item_drop_tables,
    get_permanent_discovery_search_node_id,
    get_permanent_discovery_source,
    get_route_spec,
)
from app.content.route_spec import RouteNodeKind
from app.game.overworld_session import OverworldSession
from app.game.overworld_state import ContextualRoutePhase
from app.game.permanent_discovery import (
    DiscoveryClaimStatus,
    PermanentDiscoveryService,
)
from app.game.run_events import RunEventService, RunEventStatus
from app.items.equipment import EquipmentInstance
from app.persistence.ports import SaveLoadResult
from app.persistence.save_document import (
    SaveStateValidationError,
    build_save_document,
    reconstruct_game_state,
    validate_profile_payload,
    validate_save_document,
)
from app.persistence.save_port_contract import SaveLoadStatus
from app.player.player_state import PlayerState
from app.combat.battle import Battle
from app.content.catalog import create_enemy_state, get_drifter_spec
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.ui.overworld_ui import (
    ChooseDiscoverySearcher,
    ChooseDiscoveryTarget,
    ChooseOverworldAction,
)
from app.player.scaling import discovery_bonus_bps_from_intuition
from tests.game_test_support import completed_hub_game


class RecordingSavePort:
    def __init__(self, status=SaveLoadStatus.SAVED):
        self.status = status
        self.saved_states = []

    def inspect(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def load(self):
        return self.inspect()

    def save(self, game_state):
        if self.status is SaveLoadStatus.SAVED:
            self.saved_states.append(game_state.clone())
        return SaveLoadResult(self.status)


class RewardRng:
    def __init__(self, *, drop_roll=10000):
        self.drop_roll = drop_roll
        self.randint_calls = 0
        self.randrange_calls = 0

    def randint(self, minimum, maximum):
        self.randint_calls += 1
        assert (minimum, maximum) == (1, 10000)
        return self.drop_roll

    def randrange(self, stop):
        self.randrange_calls += 1
        return 0


class StableRng(RewardRng):
    def randint(self, minimum, maximum):
        if (minimum, maximum) == (1, 10000):
            return self.drop_roll
        return minimum

    def choice(self, values):
        return values[0]


class RunEventOnlyRng:
    def randint(self, minimum, maximum):
        if (minimum, maximum) == (1, 10000):
            return maximum
        return minimum


def floor_four_game_at(node_id):
    game = completed_hub_game()
    recruited = {
        member.character.profile.drifter_id for member in game.recruited_members
    }
    for drifter_id in ("azhvielle", "branoc", "joruun", "zhaivra"):
        if drifter_id in recruited:
            continue
        member = PlayerState(get_drifter_spec(drifter_id).create_character())
        assert game.party_state.recruit_companion(game.player_state, member, cost=0)
    party = game.party_state
    party._floor_one_cleared = True
    party._floor_two_cleared = True
    party._floor_three_cleared = True
    assert party.start_floor_four_run(
        run_id_factory=lambda: "m8-floor-four-reward-run"
    ) == 100
    game.overworld_state.begin_route("floor_four")
    route = get_route_spec("floor_four")
    for node in route.nodes[1:]:
        previous = game.overworld_state.current_route_node_id
        previous_node = next(item for item in route.nodes if item.node_id == previous)
        if previous_node.kind is RouteNodeKind.REST:
            game.overworld_state.record_resolved_rest_node(previous)
        game.overworld_state.advance_to(
            node.node_id,
            contextual_phase=(
                ContextualRoutePhase.ENTER_ENCOUNTER
                if node.encounter_id is not None
                else ContextualRoutePhase.NONE
            ),
        )
        if node.node_id == node_id:
            break
    party._mark_encounter_progress()
    return game


def test_schema27_floor_four_save_is_immutable_and_migrates_to_schema28():
    historical = build_save_document(
        floor_four_game_at("floor_four_rest_midpoint")
    )
    historical["schema_version"] = 27
    original = deepcopy(historical)

    assert validate_profile_payload(historical) == original
    migrated = validate_save_document(historical)
    restored = reconstruct_game_state(historical)

    assert historical == original
    assert migrated["schema_version"] == 28
    assert migrated["overworld"]["active_route_id"] == "floor_four"
    assert migrated["party"]["floor_four_run_id"] == "m8-floor-four-reward-run"
    assert build_save_document(restored) == migrated


def session_for(game, save_port, *, rng=None):
    return OverworldSession(
        game,
        battle_factory=lambda player, enemies, **kwargs: Battle(
            player, enemies, rng=StableRng(), **kwargs
        ),
        enemy_factory=create_enemy_state,
        save_port=save_port,
        run_event_rng=rng or StableRng(),
    )


@pytest.mark.parametrize(
    ("source_id", "node_id", "amount", "discovery_type"),
    (
        ("ancient_well_floor4_01", "floor_four_rest_midpoint", 5, "ancient_well"),
        ("forgotten_altar_floor4_01", "floor_four_rest_pre_boss", 5, "forgotten_altar"),
        ("spirit_relic_floor5_01", "floor_five_rest_midpoint", 3, "spirit_relic"),
    ),
)
def test_m8_discovery_sources_are_authored_with_approved_rewards_and_locations(
    source_id, node_id, amount, discovery_type
):
    source = get_permanent_discovery_source(source_id)

    assert source.amount == amount
    assert source.discovery_type.value == discovery_type
    assert source.search_chance_bps == 1000
    assert get_permanent_discovery_search_node_id(source_id) == node_id


@pytest.mark.parametrize(
    ("source_id", "node_id"),
    (
        ("ancient_well_floor4_01", "floor_four_rest_midpoint"),
        ("forgotten_altar_floor4_01", "floor_four_rest_pre_boss"),
    ),
)
def test_floor_four_search_persists_one_intuition_adjusted_outcome_without_reroll(
    source_id, node_id
):
    source = get_permanent_discovery_source(source_id)
    game = floor_four_game_at(node_id)
    port = RecordingSavePort()
    rng = RewardRng(drop_roll=1)
    service = RunEventService(save_port=port, rng=rng)

    first = service.search_discovery(
        game,
        node_id=node_id,
        searcher_drifter_id=game.party_state.active_drifter_ids[0],
        source=source,
    )
    searcher = game.member_for_drifter_id(game.party_state.active_drifter_ids[0])
    expected_chance = min(
        10000,
        1000
        + 1000
        * discovery_bonus_bps_from_intuition(searcher.effective_stat("intuition"))
        // 10000,
    )
    restored = reconstruct_game_state(build_save_document(port.saved_states[0]))
    replay = RunEventService(save_port=port, rng=RewardRng()).search_discovery(
        restored,
        node_id=node_id,
        searcher_drifter_id=game.party_state.active_drifter_ids[0],
        source=source,
    )

    assert first.status is RunEventStatus.RESOLVED
    assert first.found is True
    assert first.effective_chance_bps == expected_chance
    assert first.game_state.world_state.discovered_permanent_discovery_sources == (
        source_id,
    )
    assert replay.status is RunEventStatus.ALREADY_RESOLVED
    assert replay.roll == first.roll
    assert len(port.saved_states) == 1
    event = restored.party_state.resolved_run_events[0]
    assert event["floor_id"] == "floor_four"
    assert event["node_id"] == node_id


@pytest.mark.parametrize(
    ("source_id", "node_id", "resource_name"),
    (
        ("ancient_well_floor4_01", "floor_four_rest_midpoint", "health"),
        ("forgotten_altar_floor4_01", "floor_four_rest_pre_boss", "mana_resource"),
    ),
)
@pytest.mark.parametrize("target_index", (0, 1))
def test_floor_four_discovery_journey_claims_only_the_selected_active_drifter(
    source_id, node_id, resource_name, target_index
):
    game = floor_four_game_at(node_id)
    port = RecordingSavePort()
    active_ids = game.party_state.active_drifter_ids
    recruited_ids = tuple(
        member.character.profile.drifter_id
        for member in game.recruited_members
    )
    searcher_id = active_ids[1 - target_index]
    target_id = active_ids[target_index]
    before = {
        drifter_id: getattr(game.member_for_drifter_id(drifter_id), resource_name).maximum
        for drifter_id in recruited_ids
    }
    session = session_for(game, port, rng=RewardRng(drop_roll=1))

    session.submit(ChooseOverworldAction(OverworldAction.SEARCH_SITE))
    session.submit(ChooseDiscoverySearcher(searcher_id))
    assert session.current_view().screen is OverworldScreen.DISCOVERY_TARGETS
    session.submit(ChooseDiscoveryTarget(target_id))
    session.submit(ChooseOverworldAction(OverworldAction.CONFIRM))

    for drifter_id in recruited_ids:
        expected_gain = 5 if drifter_id == target_id else 0
        resource = getattr(session.game_state.member_for_drifter_id(drifter_id), resource_name)
        assert resource.maximum == before[drifter_id] + expected_gain
    assert source_id in session.game_state.world_state.permanent_discovery_claims
    restored = reconstruct_game_state(build_save_document(port.saved_states[-1]))
    assert source_id in restored.world_state.permanent_discovery_claims
    assert len(port.saved_states) == 2

    source = get_permanent_discovery_source(source_id)
    duplicate_port = RecordingSavePort()
    duplicate = PermanentDiscoveryService(
        (source,),
        save_port=duplicate_port,
    ).consume(
        restored,
        source_id,
        searcher_id,
        confirmed=True,
    )
    assert duplicate.status is DiscoveryClaimStatus.ALREADY_CLAIMED
    assert duplicate.game_state.world_state.permanent_discovery_claims.count(source_id) == 1
    for drifter_id in recruited_ids:
        resource = getattr(duplicate.game_state.member_for_drifter_id(drifter_id), resource_name)
        assert resource.maximum == before[drifter_id] + (
            5 if drifter_id == target_id else 0
        )
    assert duplicate_port.saved_states == []


def test_discovery_claim_save_failure_leaves_claim_and_reward_retryable():
    source_id = "ancient_well_floor4_01"
    game = floor_four_game_at("floor_four_rest_midpoint")
    port = RecordingSavePort()
    target_id = game.party_state.active_drifter_ids[1]
    target = game.member_for_drifter_id(target_id)
    before_max_hp = target.health.maximum
    session = session_for(game, port, rng=RewardRng(drop_roll=1))
    session.submit(ChooseOverworldAction(OverworldAction.SEARCH_SITE))
    session.submit(ChooseDiscoverySearcher(game.party_state.active_drifter_ids[0]))
    session.submit(ChooseDiscoveryTarget(target_id))

    port.status = SaveLoadStatus.INVALID
    session.submit(ChooseOverworldAction(OverworldAction.CONFIRM))

    assert target.health.maximum == before_max_hp
    assert source_id not in session.game_state.world_state.permanent_discovery_claims
    assert source_id in session.game_state.world_state.discovered_permanent_discovery_sources
    assert session.current_view().screen is OverworldScreen.DISCOVERY_CONFIRMATION
    assert len(port.saved_states) == 1

    port.status = SaveLoadStatus.SAVED
    session.submit(ChooseOverworldAction(OverworldAction.CONFIRM))
    assert session.game_state.member_for_drifter_id(target_id).health.maximum == before_max_hp + 5
    assert source_id in session.game_state.world_state.permanent_discovery_claims
    assert len(port.saved_states) == 2


def test_spirit_relic_claim_awards_three_gp_once_to_one_active_drifter():
    source = get_permanent_discovery_source("spirit_relic_floor5_01")
    game = completed_hub_game()
    first_id, second_id = game.party_state.active_drifter_ids
    game.world_state.discover_permanent_discovery_source(source.source_id)
    before_first = game.member_for_drifter_id(first_id).growth_points
    before_second = game.member_for_drifter_id(second_id).growth_points
    port = RecordingSavePort()
    service = PermanentDiscoveryService((source,), save_port=port)

    claimed = service.consume(game, source.source_id, second_id, confirmed=True)
    loaded = reconstruct_game_state(build_save_document(port.saved_states[0]))
    duplicate = service.consume(loaded, source.source_id, first_id, confirmed=True)

    assert claimed.status is DiscoveryClaimStatus.CLAIMED
    assert claimed.game_state.member_for_drifter_id(first_id).growth_points == before_first
    assert claimed.game_state.member_for_drifter_id(second_id).growth_points == before_second + 3
    assert source.source_id in loaded.world_state.permanent_discovery_claims
    assert duplicate.status is DiscoveryClaimStatus.ALREADY_CLAIMED
    assert duplicate.game_state.member_for_drifter_id(first_id).growth_points == before_first
    assert len(port.saved_states) == 1


def test_encounter_eight_commits_armor_and_healing_potion_with_reward_evidence():
    game = floor_four_game_at("floor_four_battle_08")
    port = RecordingSavePort()
    rng = RewardRng()
    service = RunEventService(save_port=port, rng=rng)

    result = service.resolve_encounter_rewards(
        game,
        node_id="floor_four_battle_08",
        experience=75,
        gold=12,
        enemy_drop_tables=get_encounter_item_drop_tables(
            "m8_floor_four_encounter_08", tier=3
        ),
    )

    assert result.status is RunEventStatus.RESOLVED
    assert dict(result.items)["healing_potion"] == 1
    party = result.game_state.party_state
    assert len(party.equipment_instances) == 1
    armor = party.equipment_instances[0]
    assert armor.definition_id == "field_chest"
    assert armor.source_id == "m8_floor_four_armor_source"
    assert armor.secured is False
    assert party.outing_rewards.items["healing_potion"] == 1
    assert len(port.saved_states) == 1
    assert {event["kind"] for event in party.resolved_run_events} >= {
        "encounter_rewards",
        "armor_reward",
        "fixed_item_reward",
    }

    restored = reconstruct_game_state(build_save_document(port.saved_states[0]))
    assert restored.party_state.equipment_instance(armor.instance_id).snapshot() == (
        armor.snapshot()
    )
    assert restored.party_state.outing_rewards.items["healing_potion"] == 1
    replay_rng = RewardRng()
    replay = RunEventService(save_port=port, rng=replay_rng).resolve_encounter_rewards(
        restored,
        node_id="floor_four_battle_08",
        experience=75,
        gold=12,
        enemy_drop_tables=get_encounter_item_drop_tables(
            "m8_floor_four_encounter_08", tier=3
        ),
    )
    assert replay.status is RunEventStatus.ALREADY_RESOLVED
    assert dict(replay.items)["healing_potion"] == 1
    assert replay.equipment_instance_id == armor.instance_id
    assert replay_rng.randint_calls == replay_rng.randrange_calls == 0
    assert len(port.saved_states) == 1


def test_schema27_rejects_m8_4_encounter_reward_evidence():
    game = floor_four_game_at("floor_four_battle_08")
    port = RecordingSavePort()
    result = RunEventService(save_port=port, rng=RewardRng()).resolve_encounter_rewards(
        game,
        node_id="floor_four_battle_08",
        experience=75,
        gold=12,
        enemy_drop_tables=get_encounter_item_drop_tables(
            "m8_floor_four_encounter_08", tier=3
        ),
    )
    historical = build_save_document(result.game_state)
    historical["schema_version"] = 27

    with pytest.raises(SaveStateValidationError, match="M8.4 reward evidence"):
        validate_profile_payload(historical)


@pytest.mark.parametrize("evidence_kind", ("claim", "discovered", "search"))
def test_schema27_rejects_m8_4_discovery_evidence(evidence_kind):
    source_id = "ancient_well_floor4_01"
    game = floor_four_game_at("floor_four_rest_midpoint")
    if evidence_kind == "claim":
        game.world_state.claim_permanent_discovery(source_id)
    elif evidence_kind == "discovered":
        game.world_state.discover_permanent_discovery_source(source_id)
    else:
        result = RunEventService(
            save_port=RecordingSavePort(),
            rng=RewardRng(drop_roll=10000),
        ).search_discovery(
            game,
            node_id="floor_four_rest_midpoint",
            searcher_drifter_id=game.party_state.active_drifter_ids[0],
            source=get_permanent_discovery_source(source_id),
        )
        assert result.status is RunEventStatus.RESOLVED
        assert result.found is False
        game = result.game_state

    historical = build_save_document(game)
    historical["schema_version"] = 27

    with pytest.raises(SaveStateValidationError, match="M8.4 discovery evidence"):
        validate_profile_payload(historical)
    with pytest.raises(SaveStateValidationError, match="M8.4 discovery evidence"):
        validate_save_document(historical)


def test_encounter_eight_armor_uses_the_run_event_randint_contract():
    game = floor_four_game_at("floor_four_battle_08")
    port = RecordingSavePort()

    result = RunEventService(save_port=port, rng=RunEventOnlyRng()).resolve_encounter_rewards(
        game,
        node_id="floor_four_battle_08",
        experience=75,
        gold=12,
        enemy_drop_tables=get_encounter_item_drop_tables(
            "m8_floor_four_encounter_08", tier=3
        ),
    )

    assert result.status is RunEventStatus.RESOLVED
    assert len(result.game_state.party_state.equipment_instances) == 1
    assert len(port.saved_states) == 1


def test_live_encounter_eight_reward_survives_reload_and_next_victory():
    game = floor_four_game_at("floor_four_battle_08")
    port = RecordingSavePort()
    session = session_for(game, port, rng=RewardRng())
    battle = session._create_active_battle(ui=None)
    for enemy in battle.enemies:
        enemy.health.take_damage(enemy.health.current)

    session._finalize_active_battle(winner="player")

    assert session.game_state.overworld_state.current_route_node_id == "floor_four_battle_09"
    assert session.game_state.party_state.outing_rewards.items["healing_potion"] == 1
    assert len(session.game_state.party_state.equipment_instances) == 1
    first_saved = reconstruct_game_state(build_save_document(port.saved_states[-1]))
    assert first_saved.party_state.equipment_instances[0].secured is False

    reloaded_session = session_for(first_saved, port, rng=RewardRng())
    next_battle = reloaded_session._create_active_battle(ui=None)
    for enemy in next_battle.enemies:
        enemy.health.take_damage(enemy.health.current)
    reloaded_session._finalize_active_battle(winner="player")

    party = reloaded_session.game_state.party_state
    assert len([event for event in party.resolved_run_events if event["kind"] == "encounter_rewards"]) == 2
    assert party.outing_rewards.items["healing_potion"] == 1
    assert len(party.equipment_instances) == 1
    assert reloaded_session.current_view().screen is OverworldScreen.REST

    reloaded_session.submit(ChooseOverworldAction(OverworldAction.REST))
    secured_state = reconstruct_game_state(build_save_document(port.saved_states[-1]))
    secured_party = secured_state.party_state
    secured_armor = secured_party.equipment_instances[0]
    armor_event = next(
        event
        for event in secured_party.resolved_run_events
        if event["kind"] == "armor_reward"
    )
    assert secured_armor.secured is True
    assert armor_event["result"]["instance"]["secured"] is False

    next_encounter = RunEventService(
        save_port=port,
        rng=RewardRng(),
    ).resolve_encounter_rewards(
        secured_state,
        node_id="floor_four_battle_10",
        experience=100,
        gold=20,
        enemy_drop_tables=get_encounter_item_drop_tables(
            "m8_tidebound_curator_boss", tier=3
        ),
    )
    assert next_encounter.status is RunEventStatus.RESOLVED
    assert next_encounter.game_state.party_state.equipment_instance(
        secured_armor.instance_id
    ).secured is True


def test_floor_four_armor_cannot_be_resolved_outside_encounter_victory_transaction():
    game = floor_four_game_at("floor_four_battle_08")
    port = RecordingSavePort()
    before = game.snapshot()

    result = RunEventService(save_port=port, rng=RewardRng()).resolve_armor_reward(
        game,
        node_id="floor_four_battle_08",
        template_id="field_chest",
        source_id="m8_floor_four_armor_source",
    )

    assert result.status is RunEventStatus.INVALID_TARGET
    assert result.game_state is game
    assert game.snapshot() == before
    assert port.saved_states == []


def test_encounter_eight_reward_save_failure_leaves_no_reward_or_evidence():
    game = floor_four_game_at("floor_four_battle_08")
    before = game.snapshot()
    port = RecordingSavePort(SaveLoadStatus.INVALID)

    result = RunEventService(save_port=port, rng=RewardRng()).resolve_encounter_rewards(
        game,
        node_id="floor_four_battle_08",
        experience=75,
        gold=12,
        enemy_drop_tables=get_encounter_item_drop_tables(
            "m8_floor_four_encounter_08", tier=3
        ),
    )

    assert result.status is RunEventStatus.SAVE_FAILED
    assert result.game_state is game
    assert game.snapshot() == before
    assert port.saved_states == []


def test_floor_four_recover_secures_reward_and_advances_only_after_save():
    game = floor_four_game_at("floor_four_rest_pre_boss")
    game.party_state.add_equipment_instance(
        EquipmentInstance.create(
            instance_id="00000000-0000-4000-8000-000000000401",
            definition_id="field_chest",
            source_id="m8_floor_four_armor_source",
            secured=False,
            stat_bonuses={"constitution": 2},
        )
    )
    game.party_state.add_floor_four_rewards(
        experience=20,
        gold=0,
        items={"healing_potion": 1},
    )
    port = RecordingSavePort()
    session = session_for(game, port)

    view = session.submit(ChooseOverworldAction(OverworldAction.REST))

    assert view.screen is OverworldScreen.MAIN
    assert session.game_state.overworld_state.current_route_node_id == "floor_four_battle_10"
    armor = session.game_state.party_state.equipment_instances[0]
    assert armor.secured is True
    assert session.game_state.party_state.outing_rewards.items == {"healing_potion": 1}
    assert len(port.saved_states) == 1
    saved = reconstruct_game_state(build_save_document(port.saved_states[0]))
    assert saved.party_state.equipment_instance(armor.instance_id).secured is True
    assert saved.party_state.outing_rewards.items == {"healing_potion": 1}


def test_floor_four_extraction_banks_recovery_reward_and_secures_armor_once():
    game = floor_four_game_at("floor_four_rest_pre_boss")
    armor = EquipmentInstance.create(
        instance_id="00000000-0000-4000-8000-000000000403",
        definition_id="field_chest",
        source_id="m8_floor_four_armor_source",
        secured=False,
        stat_bonuses={"constitution": 2},
    )
    game.party_state.add_equipment_instance(armor)
    game.party_state.add_floor_four_rewards(
        experience=20,
        gold=10,
        items={"healing_potion": 1},
    )
    port = RecordingSavePort()
    session = session_for(game, port)

    extracted = session.submit(ChooseOverworldAction(OverworldAction.EXTRACT))
    assert extracted.screen is OverworldScreen.EXTRACTION
    returned = session.submit(ChooseOverworldAction(OverworldAction.RETURN_TO_HUB))

    assert returned.screen is OverworldScreen.HUB
    party = session.game_state.party_state
    assert party.shared_items["healing_potion"] == 1
    assert party.outing_rewards.items == {}
    assert party.equipment_instance(armor.instance_id).secured is True
    assert party.floor_four_run_id is None
    assert len(port.saved_states) == 2
    saved = reconstruct_game_state(build_save_document(port.saved_states[-1]))
    assert saved.party_state.shared_items["healing_potion"] == 1
    assert saved.party_state.equipment_instance(armor.instance_id).secured is True


def test_floor_four_recovery_reward_is_lost_on_death():
    game = floor_four_game_at("floor_four_battle_08")
    port = RecordingSavePort()
    rewarded = RunEventService(save_port=port, rng=RewardRng()).resolve_encounter_rewards(
        game,
        node_id="floor_four_battle_08",
        experience=75,
        gold=12,
        enemy_drop_tables=get_encounter_item_drop_tables(
            "m8_floor_four_encounter_08", tier=3
        ),
    )
    assert rewarded.status is RunEventStatus.RESOLVED
    dead_run = rewarded.game_state
    assert dead_run.party_state.outing_rewards.items["healing_potion"] == 1

    assert dead_run.party_state.fail_floor_four_run(
        dead_run.active_party_members,
        recruited_members=dead_run.recruited_members,
    )
    for member in dead_run.recruited_members:
        member.health.heal(member.health.maximum)
        member.mana_resource.restore(member.mana_resource.maximum)
    dead_run.overworld_state.return_to_surface_entrance()

    party = dead_run.party_state
    assert party.shared_items.get("healing_potion", 0) == 0
    assert party.outing_rewards.items == {}
    assert party.phase.value == "hub"
    assert party.equipment_instances == ()
    saved = reconstruct_game_state(build_save_document(dead_run))
    assert saved.party_state.shared_items.get("healing_potion", 0) == 0


def test_floor_four_rest_save_failure_preserves_unsecured_armor_and_route():
    game = floor_four_game_at("floor_four_rest_pre_boss")
    game.party_state.add_equipment_instance(
        EquipmentInstance.create(
            instance_id="00000000-0000-4000-8000-000000000402",
            definition_id="field_chest",
            source_id="m8_floor_four_armor_source",
            secured=False,
            stat_bonuses={"constitution": 2},
        )
    )
    port = RecordingSavePort(SaveLoadStatus.INVALID)
    before = game.snapshot()
    session = session_for(game, port)

    session.submit(ChooseOverworldAction(OverworldAction.REST))

    assert game.snapshot() == before
    assert session.game_state.party_state.equipment_instances[0].secured is False
    assert session.game_state.overworld_state.current_route_node_id == "floor_four_rest_pre_boss"
    assert session.current_view().notice == "The Rest transition could not be saved. Nothing changed."


def test_floor_four_discovery_actions_appear_only_at_the_authored_rests():
    midpoint = floor_four_game_at("floor_four_rest_midpoint")
    midpoint_session = session_for(midpoint, RecordingSavePort())
    pre_boss = floor_four_game_at("floor_four_rest_pre_boss")
    pre_boss_session = session_for(pre_boss, RecordingSavePort())

    midpoint_actions = {option.action for option in midpoint_session.current_view().options}
    pre_boss_actions = {option.action for option in pre_boss_session.current_view().options}

    assert OverworldAction.SEARCH_SITE in midpoint_actions
    assert OverworldAction.SEARCH_SITE in pre_boss_actions
    assert midpoint_session.game_state.party_state.resolved_run_events == ()
    assert pre_boss_session.game_state.party_state.resolved_run_events == ()
