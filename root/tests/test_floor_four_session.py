from app.combat.battle import Battle
from app.content.catalog import create_enemy_state, get_drifter_spec, get_route_spec
from app.content.route_spec import RouteNodeKind
from app.game.game_state import GameState
from app.game.overworld_session import OverworldSession
from app.game.overworld_state import ContextualRoutePhase
from app.game.story_state import KnowledgeStatus
from app.persistence.ports import SaveLoadResult
from app.persistence.save_document import build_save_document, reconstruct_game_state
from app.persistence.save_port_contract import SaveLoadStatus
from app.player.player_state import PlayerState
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.presentation.battle_models import BattleView
from app.ui.overworld_ui import ChooseDestination, ChooseOverworldAction, ChooseRegion
from tests.game_test_support import completed_hub_game


class StableRng:
    def randint(self, minimum, maximum):
        return minimum

    def choice(self, values):
        return values[0]


class RecordingSavePort:
    def __init__(self, *, fail=False, fail_on_save_calls=()):
        self.saved_states = []
        self.fail = fail
        self.fail_on_save_calls = set(fail_on_save_calls)
        self.save_calls = 0

    def inspect(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def load(self):
        return self.inspect()

    def save(self, game_state):
        self.save_calls += 1
        self.saved_states.append(game_state.clone())
        status = (
            SaveLoadStatus.INVALID
            if self.fail or self.save_calls in self.fail_on_save_calls
            else SaveLoadStatus.SAVED
        )
        return SaveLoadResult(status)


def floor_four_ready_game(*, floor_three_cleared=True, recruit_fourth=True):
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
            if len(game.recruited_members) == 3 and not recruit_fourth:
                break
    game.party_state._floor_one_cleared = True
    game.party_state._floor_two_cleared = True
    game.party_state._floor_three_cleared = floor_three_cleared
    return game


def make_session(game, save_port):
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
    )


def move_to_floor_four_boss(game):
    assert game.party_state.start_floor_four_run(
        run_id_factory=lambda: "floor-four-boss-session"
    ) == 100
    game.overworld_state.begin_route("floor_four")
    route = get_route_spec("floor_four")
    for index, node in enumerate(route.nodes[1:], start=1):
        previous = route.nodes[index - 1]
        if previous.kind.value == "rest":
            game.overworld_state.record_resolved_rest_node(previous.node_id)
        game.overworld_state.advance_to(
            node.node_id,
            contextual_phase=(
                ContextualRoutePhase.ENTER_ENCOUNTER
                if node.encounter_id is not None
                else ContextualRoutePhase.NONE
            ),
        )


def start_floor_four_session(game, save_port):
    game.story_state.reveal_knowledge_fact(
        "m8_fact_drowned_reliquary",
        KnowledgeStatus.RUMORED,
    )
    session = make_session(game, save_port)
    session.submit(ChooseOverworldAction(OverworldAction.REGION_PORTAL))
    session.submit(ChooseRegion("region_1"))
    session.submit(ChooseDestination("drowned_reliquary"))
    return session


def advance_active_floor_four_run_to_boss(game):
    route = get_route_spec("floor_four")
    current_node_id = game.overworld_state.current_route_node_id
    current_index = next(
        index for index, node in enumerate(route.nodes)
        if node.node_id == current_node_id
    )
    for index in range(current_index + 1, len(route.nodes)):
        previous = route.nodes[index - 1]
        if previous.kind is RouteNodeKind.REST:
            game.overworld_state.record_resolved_rest_node(previous.node_id)
        node = route.nodes[index]
        game.overworld_state.advance_to(
            node.node_id,
            contextual_phase=(
                ContextualRoutePhase.ENTER_ENCOUNTER
                if node.encounter_id is not None
                else ContextualRoutePhase.NONE
            ),
        )


def test_floor_four_run_requires_floor_three_clear_and_four_recruits():
    not_cleared = floor_four_ready_game(floor_three_cleared=False)
    try:
        not_cleared.party_state.start_floor_four_run()
    except ValueError as error:
        assert "Floor 3" in str(error)
    else:
        raise AssertionError("Floor IV started before Floor III was cleared")

    three_recruits = floor_four_ready_game(recruit_fourth=False)
    try:
        three_recruits.party_state.start_floor_four_run()
    except ValueError as error:
        assert "four permanent Drifters" in str(error)
    else:
        raise AssertionError("Floor IV started without all four recruits")


def test_floor_four_route_entry_confirms_knowledge_and_starts_two_member_run():
    game = floor_four_ready_game()
    game.story_state.reveal_knowledge_fact(
        "m8_fact_drowned_reliquary",
        KnowledgeStatus.RUMORED,
    )
    save_port = RecordingSavePort()
    session = make_session(game, save_port)

    session.submit(ChooseOverworldAction(OverworldAction.REGION_PORTAL))
    session.submit(ChooseRegion("region_1"))
    view = session.submit(ChooseDestination("drowned_reliquary"))

    assert isinstance(view, BattleView)
    assert session.game_state.overworld_state.active_route_id == "floor_four"
    assert session.game_state.party_state.active_run_floor_id == "floor_four"
    assert session.game_state.party_state.active_run_id is not None
    assert len(session.active_battle.party_states) == 2
    assert session.active_battle.enemies[0].tier == 3
    assert (
        session.game_state.story_state.knowledge_status(
            "m8_fact_drowned_reliquary"
        )
        is KnowledgeStatus.CONFIRMED
    )
    assert save_port.saved_states


def test_floor_four_rest_checkpoint_round_trips_active_run_and_route():
    game = floor_four_ready_game()
    party = game.party_state
    assert party.start_floor_four_run(
        run_id_factory=lambda: "floor-four-rest-checkpoint"
    ) == 100
    game.overworld_state.begin_route("floor_four")
    route = get_route_spec("floor_four")
    for node in route.nodes[1:6]:
        game.overworld_state.advance_to(
            node.node_id,
            contextual_phase=(
                ContextualRoutePhase.NONE
                if node.kind.value == "rest"
                else ContextualRoutePhase.ENTER_ENCOUNTER
            ),
        )
        if node.kind.value == "rest":
            break
    party._mark_encounter_progress()

    restored = reconstruct_game_state(build_save_document(game))

    assert restored.party_state.floor_four_run_id == "floor-four-rest-checkpoint"
    assert restored.party_state.active_run_floor_id == "floor_four"
    assert restored.overworld_state.active_route_id == "floor_four"
    assert restored.overworld_state.current_route_node_id == "floor_four_rest_midpoint"
    assert len(restored.active_party_members) == 2


def test_floor_four_rest_screen_exposes_recovery_and_extraction_controls():
    game = floor_four_ready_game()
    party = game.party_state
    assert party.start_floor_four_run(
        run_id_factory=lambda: "floor-four-rest-screen"
    ) == 100
    game.overworld_state.begin_route("floor_four")
    for node in get_route_spec("floor_four").nodes[1:6]:
        game.overworld_state.advance_to(
            node.node_id,
            contextual_phase=(
                ContextualRoutePhase.NONE
                if node.kind.value == "rest"
                else ContextualRoutePhase.ENTER_ENCOUNTER
            ),
        )
    session = make_session(game, RecordingSavePort())

    view = session.current_view()

    assert view.screen is OverworldScreen.REST
    actions = {option.action for option in view.options}
    assert OverworldAction.REST in actions
    assert OverworldAction.EXTRACT in actions
    assert OverworldAction.CHARACTER in actions
    assert OverworldAction.ITEMS in actions


def test_floor_four_pending_boss_settlement_is_finalizable_not_talisman_exitable():
    game = floor_four_ready_game()
    game.party_state.add_shared_items({"return_talisman": 1})
    assert game.party_state.load_carried_supplies({"return_talisman": 1})
    move_to_floor_four_boss(game)
    save_port = RecordingSavePort(fail_on_save_calls={2})
    session = make_session(game, save_port)
    battle = session._create_active_battle(ui=None)
    for enemy in battle.enemies:
        enemy.health.take_damage(enemy.health.current)

    session._finalize_active_battle(winner="player")

    assert session.game_state.floor_four_boss_settlement_pending
    pending_state = session.game_state.party_state.snapshot()
    actions = {option.action for option in session.current_view().options}
    assert OverworldAction.FINALIZE_FLOOR_FOUR_CLEAR in actions
    assert OverworldAction.RETURN_WITH_TALISMAN not in actions

    session.submit(ChooseOverworldAction(OverworldAction.RETURN_WITH_TALISMAN))

    assert session.game_state.floor_four_boss_settlement_pending
    assert session.game_state.party_state.snapshot() == pending_state

    session.submit(
        ChooseOverworldAction(OverworldAction.FINALIZE_FLOOR_FOUR_CLEAR)
    )

    assert not session.game_state.floor_four_boss_settlement_pending
    assert session.game_state.party_state.floor_four_cleared
    assert session.game_state.party_state.phase.value == "hub"
    assert save_port.save_calls == 3


def test_floor_four_entry_write_failure_does_not_confirm_fact_or_start_run():
    game = floor_four_ready_game()
    game.story_state.reveal_knowledge_fact(
        "m8_fact_drowned_reliquary",
        KnowledgeStatus.RUMORED,
    )
    before_party = game.party_state.snapshot()
    before_overworld = game.overworld_state.snapshot()
    before_knowledge = game.story_state.snapshot()
    session = make_session(game, RecordingSavePort(fail=True))

    session.submit(ChooseOverworldAction(OverworldAction.REGION_PORTAL))
    session.submit(ChooseRegion("region_1"))
    session.submit(ChooseDestination("drowned_reliquary"))

    assert session.game_state.party_state.snapshot() == before_party
    assert session.game_state.overworld_state.snapshot() == before_overworld
    assert session.game_state.story_state.snapshot() == before_knowledge
    assert session.active_battle is None


def test_floor_four_ordinary_victory_persists_provenance_without_immediate_xp():
    game = floor_four_ready_game()
    save_port = RecordingSavePort()
    session = start_floor_four_session(game, save_port)
    active_ids = game.party_state.active_drifter_ids
    experience_before = {
        member.character.profile.drifter_id: member.exp_state.current
        for member in game.recruited_members
    }
    battle = session.active_battle
    for enemy in battle.enemies:
        enemy.health.take_damage(enemy.health.current)

    session._finalize_active_battle(winner="player")

    party = session.game_state.party_state
    event = next(
        event
        for event in party.resolved_run_events
        if event["kind"] == "encounter_rewards"
    )
    drop_events = [
        event for event in party.resolved_run_events if event["kind"] == "enemy_drop"
    ]
    source_ids = {
        entry["source_id"]
        for drop_event in drop_events
        for entry in drop_event["result"]["entries"]
        if "source_id" in entry
    }

    assert event["floor_id"] == "floor_four"
    assert event["node_id"] == "floor_four_battle_01"
    assert source_ids == {
        "m8_floor_four_metal_drop_01",
        "m8_floor_four_fiber_drop_01",
    }
    assert party.outing_rewards.items == {
        "grade_iv_fiber": 1,
        "grade_iv_metal": 1,
    }
    assert all(
        member.exp_state.current == experience_before[
            member.character.profile.drifter_id
        ]
        for member in session.game_state.recruited_members
    )
    assert tuple(
        member.character.profile.drifter_id for member in session.game_state.active_party_members
    ) == active_ids
    assert session.game_state.overworld_state.current_route_node_id == (
        "floor_four_battle_02"
    )


def test_floor_four_replay_can_award_repeatable_grade_four_materials():
    game = floor_four_ready_game()
    game.party_state._floor_four_cleared = True
    save_port = RecordingSavePort()
    session = start_floor_four_session(game, save_port)

    assert session.game_state.party_state.floor_four_runs_started_after_clear == 1
    battle = session.active_battle
    for enemy in battle.enemies:
        enemy.health.take_damage(enemy.health.current)
    session._finalize_active_battle(winner="player")

    party = session.game_state.party_state
    drop_events = [
        event for event in party.resolved_run_events if event["kind"] == "enemy_drop"
    ]
    source_ids = {
        entry["source_id"]
        for drop_event in drop_events
        for entry in drop_event["result"]["entries"]
        if "source_id" in entry
    }

    assert source_ids == {
        "m8_floor_four_metal_drop_01",
        "m8_floor_four_fiber_drop_01",
    }
    assert party.outing_rewards.items == {
        "grade_iv_fiber": 1,
        "grade_iv_metal": 1,
    }


def test_floor_four_reward_write_failure_rolls_back_and_retry_commits_once():
    game = floor_four_ready_game()
    save_port = RecordingSavePort(fail_on_save_calls={2})
    session = start_floor_four_session(game, save_port)
    run_id = session.game_state.party_state.floor_four_run_id
    durable_health = tuple(
        member.health.current for member in save_port.saved_states[0].active_party_members
    )
    battle = session.active_battle
    session.game_state.active_party_members[0].health.take_damage(10)
    for enemy in battle.enemies:
        enemy.health.take_damage(enemy.health.current)

    session._finalize_active_battle(winner="player")

    assert session.game_state.party_state.floor_four_run_id == run_id
    assert session.game_state.party_state.outing_rewards.experience == 0
    assert session.game_state.party_state.resolved_run_events == ()
    assert session.game_state.overworld_state.current_route_node_id == (
        "floor_four_battle_01"
    )
    assert session.game_state.overworld_state.current_contextual_route_phase.value == "retry"
    assert tuple(
        member.health.current for member in session.game_state.active_party_members
    ) == durable_health

    session.submit(ChooseOverworldAction(OverworldAction.RETRY))
    retry_battle = session.active_battle
    for enemy in retry_battle.enemies:
        enemy.health.take_damage(enemy.health.current)
    session._finalize_active_battle(winner="player")

    reward_events = [
        event
        for event in session.game_state.party_state.resolved_run_events
        if event["kind"] == "encounter_rewards"
    ]
    assert len(reward_events) == 1
    assert reward_events[0]["node_id"] == "floor_four_battle_01"
    assert save_port.save_calls == 3


def test_floor_four_boss_clear_banks_pair_xp_once_and_reveals_ashen_vault():
    game = floor_four_ready_game()
    save_port = RecordingSavePort()
    session = start_floor_four_session(game, save_port)
    first_battle = session.active_battle
    for enemy in first_battle.enemies:
        enemy.health.take_damage(enemy.health.current)
    session._finalize_active_battle(winner="player")

    experience_before = {
        member.character.profile.drifter_id: member.exp_state.current
        for member in session.game_state.recruited_members
    }
    active_ids = session.game_state.party_state.active_drifter_ids
    advance_active_floor_four_run_to_boss(session.game_state)
    boss_battle = session._create_active_battle(ui=None)
    boss_experience = sum(enemy.exp_reward for enemy in boss_battle.enemies)
    for enemy in boss_battle.enemies:
        enemy.health.take_damage(enemy.health.current)

    session._finalize_active_battle(winner="player")

    party = session.game_state.party_state
    assert party.floor_four_cleared
    assert party.floor_four_run_id is None
    assert session.game_state.story_state.knowledge_status(
        "m8_fact_ashen_vault"
    ) is KnowledgeStatus.RUMORED
    assert session.game_state.party_state.shared_items["grade_iv_magic_crystal"] == 1
    assert session.game_state.overworld_state.active_route_id == "surface"
    for member in session.game_state.recruited_members:
        drifter_id = member.character.profile.drifter_id
        if drifter_id in active_ids:
            assert member.exp_state.current > experience_before[drifter_id]
        else:
            assert member.exp_state.current == experience_before[drifter_id]

    settled = party.snapshot()
    session.submit(ChooseOverworldAction(OverworldAction.FINALIZE_FLOOR_FOUR_CLEAR))
    assert session.game_state.party_state.snapshot() == settled
    assert session.game_state.party_state.shared_items["grade_iv_magic_crystal"] == 1
    assert boss_experience > 0


def test_floor_four_boss_defeat_discards_rewards_without_unlocking_next_fact():
    game = floor_four_ready_game()
    game.party_state.add_shared_items({"healing_potion": 1})
    assert game.party_state.load_carried_supplies({"healing_potion": 1})
    save_port = RecordingSavePort()
    session = make_session(game, save_port)
    move_to_floor_four_boss(game)
    game.party_state.add_floor_four_rewards(
        experience=120,
        gold=30,
        items={"grade_iv_metal": 1},
    )
    battle = session._create_active_battle(ui=None)
    for member in battle.party_states:
        member.health.take_damage(member.health.current)

    session._finalize_active_battle(winner="enemy")

    party = session.game_state.party_state
    assert not party.floor_four_cleared
    assert party.floor_four_run_id is None
    assert party.outing_rewards.experience == 0
    assert party.outing_rewards.gold == 0
    assert party.shared_items.get("grade_iv_metal", 0) == 0
    assert party.carried_items == {}
    assert party.shared_items.get("healing_potion", 0) == 0
    assert session.game_state.story_state.knowledge_status(
        "m8_fact_ashen_vault"
    ) is KnowledgeStatus.UNKNOWN
    assert all(
        member.health.current == member.health.maximum
        for member in session.game_state.recruited_members
    )
