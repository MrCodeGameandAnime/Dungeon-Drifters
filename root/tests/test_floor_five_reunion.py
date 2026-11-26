import copy

from itertools import combinations

import pytest

from app.combat.battle import Battle
from app.content.catalog import (
    create_enemy_state,
    get_encounter_spec,
    get_enemy_spec,
    get_route_spec,
)
from app.content.route_spec import RouteNodeKind
from app.game.game_state import GameState
from app.game.overworld_session import OverworldSession
from app.game.overworld_state import ContextualRoutePhase
from app.game.region_progression import is_reunion_boss_eligible
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
from app.presentation.battle_models import BattleView
from app.presentation.overworld_models import (
    OverworldAction,
    OverworldScreen,
)
from app.ui.overworld_ui import ChooseOverworldAction
from tests.game_test_support import completed_hub_game
from tests.test_floor_five_approach import floor_five_ready_game


class StableRng:
    def randint(self, minimum, maximum):
        return minimum

    def choice(self, values):
        return values[0]


class ReloadableSavePort:
    def __init__(self, *, fail_on_save_calls=()):
        self.save_calls = 0
        self.fail_on_save_calls = set(fail_on_save_calls)
        self._state = None

    def inspect(self):
        status = SaveLoadStatus.MISSING if self._state is None else SaveLoadStatus.LOADED
        return SaveLoadResult(status)

    def load(self):
        if self._state is None:
            return SaveLoadResult(SaveLoadStatus.MISSING)
        return SaveLoadResult(SaveLoadStatus.LOADED, game_state=self._state.clone())

    def save(self, game_state):
        self.save_calls += 1
        if self.save_calls in self.fail_on_save_calls:
            return SaveLoadResult(SaveLoadStatus.INVALID)
        self._state = game_state.clone()
        return SaveLoadResult(SaveLoadStatus.SAVED)


def make_session(game, save_port, *, now_factory=None):
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
        run_event_rng=StableRng(),
        **options,
    )


def defeat_current_encounter(session):
    if session.active_battle is None:
        action = (
            OverworldAction.RETRY
            if session.game_state.overworld_state.current_contextual_route_phase
            is ContextualRoutePhase.RETRY
            else OverworldAction.ENTER_ENCOUNTER
        )
        session.submit(ChooseOverworldAction(action))
    battle = session.active_battle
    assert battle is not None
    for enemy in battle.enemies:
        enemy.health.take_damage(enemy.health.current)
    session._finalize_active_battle(winner="player")


def test_floor_five_reunion_authors_the_approved_one_boss_encounter():
    route = get_route_spec("floor_five_reunion")
    assert tuple((node.node_id, node.kind, node.encounter_id) for node in route.nodes) == (
        (
            "floor_five_reunion_battle_01",
            RouteNodeKind.BOSS,
            "m8_ashen_regent_boss",
        ),
    )
    assert get_encounter_spec("m8_ashen_regent_boss").enemy_archetype_ids == (
        "ashen_regent",
        "brine_oracle",
    )


def test_ashen_regent_uses_tier_three_content_and_the_approved_core_source():
    regent = get_enemy_spec("ashen_regent")
    profile = next(profile for profile in regent.tier_profiles if profile.tier == 3)
    assert regent.rank.value == "boss"
    assert tuple(
        (drop.item_id, drop.quantity, drop.source_id)
        for drop in profile.item_drops
    ) == (("grade_iv_cores", 1, "m8_ashen_regent_grade_iv_core_01"),)


def test_reunion_eligibility_requires_reveal_floor_four_full_roster_and_no_assignment():
    game = floor_five_ready_game()
    game.story_state._completed_events.append("m8_ashen_arena_revealed")
    assert is_reunion_boss_eligible(game)

    game.story_state._completed_events.clear()
    assert not is_reunion_boss_eligible(game)
    game.story_state._completed_events.append("m8_ashen_arena_revealed")

    game.party_state._floor_four_cleared = False
    assert not is_reunion_boss_eligible(game)
    game.party_state._floor_four_cleared = True

    game.party_state._companions = game.party_state.companions[:2]
    assert not is_reunion_boss_eligible(game)


@pytest.mark.parametrize("elapsed", (False, True))
def test_reunion_direct_submission_rejects_active_unsettled_expedition(
    tmp_path, elapsed
):
    from datetime import datetime, timedelta, timezone
    from uuid import UUID

    from app.game.expeditions import ExpeditionLaunchStatus, ExpeditionService

    started = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)
    game = floor_five_ready_game()
    game.story_state.complete_event("m8_ashen_arena_revealed")
    port = ReloadableSavePort()
    launch = ExpeditionService(
        port,
        now_factory=lambda: started,
        assignment_id_factory=lambda: UUID(
            "00000000-0000-4000-8000-000000000801"
        ),
        run_id_factory=lambda: "m8-8-active-expedition",
    ).launch(
        game,
        outing_floor_id="floor_one",
        destination_floor_id="floor_one",
        category="training",
        confirmed=True,
    )
    assert launch.status is ExpeditionLaunchStatus.LAUNCHED
    outing = launch.game_state
    if elapsed:
        outing.expedition_state.observe_assignment_time(
            started + timedelta(minutes=20)
        )
        assert outing.expedition_state.active_assignment["completed_at_utc"]

    before = outing.snapshot()
    session = make_session(outing, port)
    session.submit(
        ChooseOverworldAction(OverworldAction.CHALLENGE_ASHEN_REGENT)
    )

    assert session.active_battle is None
    assert session.game_state.snapshot() == before
    assert session.game_state.expedition_state.active_assignment is not None
    assert session.game_state.overworld_state.active_route_id == "floor_one"


def test_settled_unclaimed_expedition_report_does_not_block_reunion_entry(
    tmp_path,
):
    from datetime import datetime, timedelta, timezone
    from uuid import UUID

    from app.game.expeditions import ExpeditionLaunchStatus, ExpeditionService

    started = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)
    game = floor_five_ready_game()
    game.story_state.complete_event("m8_ashen_arena_revealed")
    port = ReloadableSavePort()
    service = ExpeditionService(
        port,
        now_factory=lambda: started,
        assignment_id_factory=lambda: UUID(
            "00000000-0000-4000-8000-000000000802"
        ),
        run_id_factory=lambda: "m8-8-unclaimed-report",
    )
    launch = service.launch(
        game,
        outing_floor_id="floor_one",
        destination_floor_id="floor_one",
        category="training",
        confirmed=True,
    )
    assert launch.status is ExpeditionLaunchStatus.LAUNCHED
    outing = launch.game_state
    outing.party_state.add_floor_one_rewards(experience=100, gold=0)
    assert outing.party_state.begin_floor_one_extraction(partial=True)
    session = make_session(
        outing,
        port,
        now_factory=lambda: started + timedelta(minutes=20),
    )
    session.submit(ChooseOverworldAction(OverworldAction.RETURN_TO_HUB))

    report, = session.game_state.expedition_state.reports
    assert report["claimed"] is False
    assert session.game_state.expedition_state.active_assignment is None
    assert is_reunion_boss_eligible(session.game_state)

    view = session.submit(
        ChooseOverworldAction(OverworldAction.CHALLENGE_ASHEN_REGENT)
    )

    assert isinstance(view, BattleView)
    assert len(session.active_battle.party_states) == 4
    assert session.game_state.expedition_state.reports[0]["claimed"] is False


def test_reunion_hub_action_launches_four_permanent_drifters_without_changing_pair():
    game = floor_five_ready_game()
    game.story_state.complete_event("m8_ashen_arena_revealed")
    original_pair = game.party_state.active_drifter_ids
    port = ReloadableSavePort()
    session = make_session(game, port)

    view = session.submit(
        ChooseOverworldAction(OverworldAction.CHALLENGE_ASHEN_REGENT)
    )

    assert isinstance(view, BattleView)
    assert session.game_state.overworld_state.active_route_id == "floor_five_reunion"
    assert session.game_state.party_state.active_drifter_ids == original_pair
    assert tuple(
        member.character.profile.drifter_id
        for member in session.active_battle.party_states
    ) == tuple(
        member.character.profile.drifter_id
        for member in session.game_state.recruited_members
    )
    assert len(session.active_battle.party_states) == 4
    assert all(enemy.tier == 3 for enemy in session.active_battle.enemies)


def test_reunion_run_round_trips_as_schema_31_without_claiming_a_clear():
    game = floor_five_ready_game()
    game.story_state.complete_event("m8_ashen_arena_revealed")
    port = ReloadableSavePort()
    session = make_session(game, port)
    session.submit(ChooseOverworldAction(OverworldAction.CHALLENGE_ASHEN_REGENT))

    document = build_save_document(session.game_state)
    restored = reconstruct_game_state(document)

    assert DISK_SCHEMA_VERSION == document["schema_version"] == 31
    assert restored.overworld_state.active_route_id == "floor_five_reunion"
    assert restored.party_state.floor_five_reunion_run_id is not None
    assert not restored.party_state.floor_five_cleared
    assert not restored.party_state.region_two_unlocked
    assert build_save_document(restored) == document


def test_schema30_history_is_immutable_and_migrates_with_empty_reunion_state():
    historical = copy.deepcopy(build_save_document(completed_hub_game()))
    historical["schema_version"] = 30
    historical["party"].pop("floor_five_reunion_run_id")
    original = copy.deepcopy(historical)

    assert validate_profile_payload(historical) == original
    migrated = validate_save_document(historical)
    restored = reconstruct_game_state(historical)

    assert historical == original
    assert migrated["schema_version"] == 31
    assert migrated["party"]["floor_five_reunion_run_id"] is None
    assert not restored.party_state.floor_five_cleared
    assert not restored.party_state.region_two_unlocked


def test_committed_reunion_victory_survives_failed_final_settlement_and_retries_once():
    game = floor_five_ready_game()
    game.story_state.complete_event("m8_ashen_arena_revealed")
    port = ReloadableSavePort(fail_on_save_calls={3})
    session = make_session(game, port)
    session.submit(ChooseOverworldAction(OverworldAction.CHALLENGE_ASHEN_REGENT))
    original_snapshot = game.snapshot()
    defeat_current_encounter(session)

    pending = port.load().game_state
    assert pending.floor_five_reunion_settlement_pending
    assert not pending.party_state.floor_five_cleared
    assert not pending.party_state.region_two_unlocked
    assert pending.party_state.outing_rewards.items.get("grade_iv_cores") == 1
    assert pending.party_state.shared_items.get("grade_iv_cores", 0) == 0
    assert session.game_state.snapshot() == pending.snapshot()
    assert game.snapshot() == original_snapshot

    retry = make_session(pending, port)
    assert retry.current_view().screen is OverworldScreen.MAIN
    retry.submit(
        ChooseOverworldAction(OverworldAction.FINALIZE_FLOOR_FIVE_REUNION)
    )

    settled = retry.game_state
    assert settled.party_state.floor_five_cleared
    assert settled.party_state.region_two_unlocked
    assert settled.story_state.completed_events.count(
        "m8_ashen_regent_defeated"
    ) == 1
    assert settled.party_state.shared_items["grade_iv_magic_crystal"] == 1
    assert settled.party_state.shared_items["grade_iv_cores"] == 1
    assert settled.party_state.floor_five_reunion_run_id is None
    assert settled.party_state.phase.value == "hub"

    retry.submit(
        ChooseOverworldAction(OverworldAction.FINALIZE_FLOOR_FIVE_REUNION)
    )
    assert retry.game_state.party_state.shared_items["grade_iv_magic_crystal"] == 1


def test_terminal_can_render_and_retry_a_committed_reunion_settlement():
    from app.ui.terminal_overworld_ui import TerminalOverworldUI

    game = floor_five_ready_game()
    game.story_state.complete_event("m8_ashen_arena_revealed")
    port = ReloadableSavePort(fail_on_save_calls={3})
    session = make_session(game, port)
    session.submit(ChooseOverworldAction(OverworldAction.CHALLENGE_ASHEN_REGENT))
    defeat_current_encounter(session)

    pending = port.load().game_state
    assert pending.floor_five_reunion_settlement_pending
    retry_session = make_session(pending, port)
    retry_view = retry_session.current_view()
    assert tuple(option.action for option in retry_view.options) == (
        OverworldAction.FINALIZE_FLOOR_FIVE_REUNION,
    )
    output = []
    terminal = TerminalOverworldUI(
        input_func=lambda _prompt: "f",
        output_func=output.append,
        interactive=False,
    )
    terminal.render(retry_view)
    assert "[F] Finalize Ashen Regent Victory" in "\n".join(output)

    action = terminal.read_input(retry_view)
    assert action.action is OverworldAction.FINALIZE_FLOOR_FIVE_REUNION
    retry_session.submit(action)

    assert retry_session.game_state.party_state.floor_five_cleared
    assert retry_session.game_state.party_state.region_two_unlocked
    assert retry_session.game_state.party_state.phase.value == "hub"


def test_reunion_entry_failure_does_not_change_saved_game_or_selected_pair():
    game = floor_five_ready_game()
    game.story_state.complete_event("m8_ashen_arena_revealed")
    before = game.snapshot()
    session = make_session(game, ReloadableSavePort(fail_on_save_calls={1}))

    session.submit(ChooseOverworldAction(OverworldAction.CHALLENGE_ASHEN_REGENT))

    assert session.game_state is game
    assert game.snapshot() == before
    assert session.active_battle is None


@pytest.mark.parametrize(
    "active_pair",
    tuple(combinations(("branoc", "azhvielle", "joruun", "zhaivra"), 2)),
)
def test_each_legal_pair_reunites_for_the_boss_and_is_restored(active_pair):
    game = floor_five_ready_game()
    roster_ids = tuple(
        member.character.profile.drifter_id
        for member in game.recruited_members
    )
    game.party_state.select_active_pair(active_pair, recruited_ids=roster_ids)
    game.story_state.complete_event("m8_ashen_arena_revealed")
    session = make_session(game, ReloadableSavePort())

    session.submit(ChooseOverworldAction(OverworldAction.CHALLENGE_ASHEN_REGENT))
    assert tuple(
        member.character.profile.drifter_id
        for member in session.active_battle.party_states
    ) == roster_ids
    assert session.game_state.party_state.active_drifter_ids == active_pair

    defeat_current_encounter(session)

    assert session.game_state.party_state.active_drifter_ids == active_pair
    assert len(session.game_state.recruited_members) == 4
    assert session.game_state.party_state.floor_five_cleared


def test_reunion_defeat_returns_all_four_without_rewards_or_progression():
    game = floor_five_ready_game()
    game.story_state.complete_event("m8_ashen_arena_revealed")
    port = ReloadableSavePort()
    session = make_session(game, port)
    original_pair = game.party_state.active_drifter_ids
    session.submit(ChooseOverworldAction(OverworldAction.CHALLENGE_ASHEN_REGENT))

    session._finalize_active_battle(winner="enemy")

    settled = session.game_state
    assert settled.party_state.phase.value == "hub"
    assert settled.party_state.active_drifter_ids == original_pair
    assert settled.party_state.floor_five_reunion_run_id is None
    assert not settled.party_state.floor_five_cleared
    assert not settled.party_state.region_two_unlocked
    assert "m8_ashen_regent_defeated" not in settled.story_state.completed_events
    assert settled.party_state.shared_items.get("grade_iv_cores", 0) == 0
    assert settled.party_state.shared_items.get("grade_iv_magic_crystal", 0) == 0
    assert all(
        member.health.current == member.health.maximum
        and member.mana_resource.current == member.mana_resource.maximum
        for member in settled.recruited_members
    )


def test_failed_boss_victory_write_can_retry_without_partial_rewards():
    game = floor_five_ready_game()
    game.story_state.complete_event("m8_ashen_arena_revealed")
    port = ReloadableSavePort(fail_on_save_calls={2})
    session = make_session(game, port)
    session.submit(ChooseOverworldAction(OverworldAction.CHALLENGE_ASHEN_REGENT))

    defeat_current_encounter(session)

    committed = port.load().game_state
    assert session.active_battle is None
    assert session.game_state.party_state.floor_five_reunion_run_id is not None
    assert not session.game_state.floor_five_reunion_settlement_pending
    assert not session.game_state.party_state.floor_five_cleared
    assert not session.game_state.party_state.region_two_unlocked
    assert "m8_ashen_regent_defeated" not in (
        session.game_state.story_state.completed_events
    )
    assert session.game_state.party_state.outing_rewards.items == {}
    assert committed.party_state.resolved_run_events == ()

    defeat_current_encounter(session)

    assert session.game_state.party_state.floor_five_cleared
    assert session.game_state.party_state.region_two_unlocked
    assert session.game_state.party_state.shared_items["grade_iv_magic_crystal"] == 1
    assert session.game_state.party_state.shared_items["grade_iv_cores"] == 1
    assert session.game_state.story_state.completed_events.count(
        "m8_ashen_regent_defeated"
    ) == 1


def test_reunion_boss_xp_is_split_four_ways_with_personal_intuition_and_replay():
    from app.content.catalog import get_encounter_rewards
    from app.player.scaling import secured_xp_bonus_bps_from_intuition

    game = floor_five_ready_game()
    game.story_state.complete_event("m8_ashen_arena_revealed")
    game.recruited_members[0].gain_experience(41)
    game.recruited_members[1].gain_experience(27)
    for member, intuition in zip(game.recruited_members, (1, 30, 60, 100)):
        member.character.permanent_stats.set_stat("intuition", intuition)
    port = ReloadableSavePort()
    session = make_session(game, port)
    members = session.game_state.recruited_members
    exp, _ = get_encounter_rewards("m8_ashen_regent_boss")
    share = exp // 4
    awards = {}
    expected = {}
    for member in members:
        drifter_id = member.character.profile.drifter_id
        award = share + share * secured_xp_bonus_bps_from_intuition(
            member.effective_stat("intuition")
        ) // 10000
        awards[drifter_id] = award
        expected_state = copy.deepcopy(member.exp_state)
        expected_state.gain(award)
        expected[drifter_id] = (
            expected_state.level.current,
            expected_state.current,
        )

    session.submit(ChooseOverworldAction(OverworldAction.CHALLENGE_ASHEN_REGENT))
    defeat_current_encounter(session)

    assert {
        member.character.profile.drifter_id: (
            member.level_state.current,
            member.exp_state.current,
        )
        for member in session.game_state.recruited_members
    } == expected
    assert session.game_state.party_state.shared_items["grade_iv_magic_crystal"] == 1
    assert session.game_state.party_state.shared_items["grade_iv_cores"] == 1

    replay_expected = {}
    for member in session.game_state.recruited_members:
        drifter_id = member.character.profile.drifter_id
        expected_state = copy.deepcopy(member.exp_state)
        expected_state.gain(awards[drifter_id])
        replay_expected[drifter_id] = (
            expected_state.level.current,
            expected_state.current,
        )
    session.submit(ChooseOverworldAction(OverworldAction.CHALLENGE_ASHEN_REGENT))
    defeat_current_encounter(session)

    assert session.game_state.party_state.shared_items["grade_iv_magic_crystal"] == 1
    assert session.game_state.party_state.shared_items["grade_iv_cores"] == 2
    assert session.game_state.story_state.completed_events.count(
        "m8_ashen_regent_defeated"
    ) == 1
    assert {
        member.character.profile.drifter_id: (
            member.level_state.current,
            member.exp_state.current,
        )
        for member in session.game_state.recruited_members
    } == replay_expected


def test_floor_five_clear_keeps_region_one_accessible_and_region_two_unavailable():
    from app.ui.overworld_ui import ChooseRegion

    game = floor_five_ready_game()
    game.story_state.complete_event("m8_ashen_arena_revealed")
    port = ReloadableSavePort()
    session = make_session(game, port)
    session.submit(ChooseOverworldAction(OverworldAction.CHALLENGE_ASHEN_REGENT))
    defeat_current_encounter(session)

    assert session.game_state.party_state.floor_five_cleared
    assert session.game_state.party_state.region_two_unlocked
    portal = session.submit(ChooseOverworldAction(OverworldAction.REGION_PORTAL))
    region_two = next(
        choice for choice in portal.region_choices if choice.region_id == "region_2"
    )
    assert region_two.unlocked and not region_two.selectable
    assert "no playable" in region_two.message.lower()
    blocked = session.submit(ChooseRegion("region_2"))
    assert blocked.screen is OverworldScreen.REGION_PORTAL

    session.submit(ChooseRegion("region_1"))
    region_one_destinations = session.current_view().destination_choices
    assert any(
        choice.destination_id == "ashen_vault" and choice.enabled
        for choice in region_one_destinations
    )

    restored = reconstruct_game_state(build_save_document(port.load().game_state))
    assert restored.party_state.floor_five_cleared
    assert restored.party_state.region_two_unlocked
    reloaded_session = make_session(restored, port)
    reloaded_session.submit(ChooseOverworldAction(OverworldAction.REGION_PORTAL))
    assert tuple(
        choice.region_id for choice in reloaded_session.current_view().region_choices
    ) == ("region_1", "region_2")


def test_floor_five_material_expedition_claims_regent_core_once_after_real_clear(
    tmp_path,
):
    from datetime import datetime, timedelta, timezone
    from uuid import UUID

    from app.game.expeditions import (
        ExpeditionClaimStatus,
        ExpeditionLaunchStatus,
        ExpeditionService,
    )
    from app.game.expedition_state import _floor_five_material_source_ids

    started = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)
    game = floor_five_ready_game()
    game.story_state.complete_event("m8_ashen_arena_revealed")
    port = ReloadableSavePort()
    service = ExpeditionService(
        port,
        now_factory=lambda: started,
        assignment_id_factory=lambda: UUID(
            "00000000-0000-4000-8000-000000000803"
        ),
        run_id_factory=lambda: "m8-8-floor-five-material",
    )

    assert "floor_five" not in service.eligible_destinations(game)
    assert service.category_unavailable_reason(
        "floor_five", "material", game_state=game
    ) is not None

    reunion = make_session(game, port)
    reunion.submit(
        ChooseOverworldAction(OverworldAction.CHALLENGE_ASHEN_REGENT)
    )
    defeat_current_encounter(reunion)
    cleared = reunion.game_state
    assert cleared.party_state.floor_five_cleared
    assert cleared.party_state.region_two_unlocked
    assert "floor_five" in service.eligible_destinations(cleared)
    assert service.category_unavailable_reason(
        "floor_five", "material", game_state=cleared
    ) is None
    assert _floor_five_material_source_ids() == (
        "m8_ashen_regent_grade_iv_core_01",
    )

    launch = service.launch(
        cleared,
        outing_floor_id="floor_five_approach",
        destination_floor_id="floor_five",
        category="material",
        confirmed=True,
    )
    assert launch.status is ExpeditionLaunchStatus.LAUNCHED
    frozen = launch.game_state.expedition_state.active_assignment[
        "frozen_outcome"
    ]
    assert frozen == {
        "source_id": "m8_ashen_regent_grade_iv_core_01",
        "reward_item_id": "grade_iv_cores",
        "reward_quantity": 1,
    }

    expedition_session = make_session(
        reconstruct_game_state(build_save_document(launch.game_state)),
        port,
        now_factory=lambda: started + timedelta(minutes=20),
    )
    for _ in range(3):
        defeat_current_encounter(expedition_session)
    assert expedition_session.current_view().screen is OverworldScreen.REST
    expedition_session.submit(ChooseOverworldAction(OverworldAction.REST))
    for _ in range(3):
        defeat_current_encounter(expedition_session)

    settled = expedition_session.game_state
    assert settled.party_state.phase.value == "hub"
    assert settled.expedition_state.active_assignment is None
    report, = settled.expedition_state.reports
    assert report["frozen_outcome"] == frozen
    assert report["claimed"] is False
    assert report["completed_at_utc"] is not None

    reloaded = reconstruct_game_state(build_save_document(port.load().game_state))
    assert reloaded.expedition_state.reports[0]["frozen_outcome"] == frozen
    before_core = reloaded.party_state.shared_items["grade_iv_cores"]
    claimed = service.claim_report(
        reloaded,
        report["report_id"],
        confirmed=True,
    )
    assert claimed.status is ExpeditionClaimStatus.CLAIMED
    assert claimed.game_state.party_state.shared_items["grade_iv_cores"] == (
        before_core + 1
    )
    claimed_reload = reconstruct_game_state(
        build_save_document(port.load().game_state)
    )
    repeated = service.claim_report(
        claimed_reload,
        report["report_id"],
        confirmed=True,
    )
    assert repeated.status is ExpeditionClaimStatus.ALREADY_CLAIMED
    assert repeated.game_state.snapshot() == claimed_reload.snapshot()
