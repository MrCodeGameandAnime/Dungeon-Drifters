from app.combat.battle import Battle
from app.content.catalog import create_enemy_state, get_drifter_spec, get_route_spec
from app.content.route_spec import RouteNodeKind
from app.game.game_state import GameState
from app.game.overworld_session import OverworldSession
from app.game.overworld_state import ContextualRoutePhase
from app.persistence.ports import SaveLoadResult
from app.persistence.save_port_contract import SaveLoadStatus
from app.player.player_state import PlayerState
from app.presentation.battle_models import BattleView
from app.presentation.overworld_models import (
    OverworldAction,
    OverworldAvailabilityReason,
    OverworldScreen,
)
from app.presentation.overworld_presenter import OverworldPresenter
from app.ui.overworld_ui import ChooseOverworldAction
from tests.game_test_support import three_member_hub_game


class StableRng:
    def randint(self, minimum, maximum):
        return minimum

    def choice(self, values):
        return values[0]


class RecordingSavePort:
    def __init__(self, *, fail_on_save_calls=()):
        self.saved_states = []
        self.fail_on_save_calls = set(fail_on_save_calls)
        self.save_calls = 0

    def inspect(self):
        from app.persistence.ports import SaveLoadResult
        from app.persistence.save_port_contract import SaveLoadStatus

        return SaveLoadResult(SaveLoadStatus.MISSING)

    def load(self):
        return self.inspect()

    def save(self, game_state):
        self.save_calls += 1
        self.saved_states.append(game_state)
        status = (
            SaveLoadStatus.INVALID
            if self.save_calls in self.fail_on_save_calls
            else SaveLoadStatus.SAVED
        )
        return SaveLoadResult(status)


def floor_three_hub_game(*, recruited_count=4, cleared=True):
    game = three_member_hub_game()
    if recruited_count == 4:
        zhaivra = PlayerState(get_drifter_spec("zhaivra").create_character())
        assert game.party_state.recruit_companion(
            game.player_state,
            zhaivra,
            cost=0,
        )
    party = game.party_state
    assert party.start_floor_one_run() == 100
    assert party.complete_floor_one_boss(game.active_party_members)
    if cleared:
        assert party.start_floor_two_run() == 100
        assert party.complete_floor_two_boss(game.active_party_members)
    return game


def make_session(game):
    return OverworldSession(
        game,
        battle_factory=lambda player, enemies, **kwargs: Battle(
            player,
            enemies,
            rng=StableRng(),
            **kwargs,
        ),
        enemy_factory=create_enemy_state,
        save_port=RecordingSavePort(),
        run_event_rng=StableRng(),
    )


def defeat_enemies(battle):
    for enemy in battle.enemies:
        enemy.health.take_damage(enemy.health.current)


def experience_state(member):
    return (member.level_state.current, member.exp_state.current)


def move_to_floor_three_boss(game):
    assert game.party_state.start_floor_three_run(
        run_id_factory=lambda: "floor-three-boss-session"
    ) == 100
    game.overworld_state.begin_route("floor_three")
    route = get_route_spec("floor_three")
    for index, node in enumerate(route.nodes[1:], start=1):
        previous = route.nodes[index - 1]
        if previous.kind.value == "rest":
            game.overworld_state.record_resolved_rest_node(previous.node_id)
        phase = (
            ContextualRoutePhase.ENTER_ENCOUNTER
            if node.encounter_id is not None
            else ContextualRoutePhase.NONE
        )
        game.overworld_state.advance_to(node.node_id, contextual_phase=phase)


def move_to_first_floor_three_rest(game):
    assert game.party_state.start_floor_three_run(
        run_id_factory=lambda: "floor-three-rest-session"
    ) == 100
    game.overworld_state.begin_route("floor_three")
    route = get_route_spec("floor_three")
    for node in route.nodes[1:]:
        game.overworld_state.advance_to(
            node.node_id,
            contextual_phase=(
                ContextualRoutePhase.NONE
                if node.kind is RouteNodeKind.REST
                else ContextualRoutePhase.ENTER_ENCOUNTER
            ),
        )
        if node.kind is RouteNodeKind.REST:
            return
    raise AssertionError("Floor 3 route has no Rest")


def test_floor_three_start_requires_floor_two_clear_and_four_recruits():
    start_action = getattr(OverworldAction, "START_FLOOR_THREE", None)
    assert start_action is not None
    presenter = OverworldPresenter()

    before_clear = presenter.build(
        floor_three_hub_game(cleared=False), screen=OverworldScreen.HUB
    )
    assert not any(option.action is start_action for option in before_clear.options)

    three_recruits = presenter.build(
        floor_three_hub_game(recruited_count=3), screen=OverworldScreen.HUB
    )
    unavailable = next(
        option for option in three_recruits.options if option.action is start_action
    )
    assert unavailable.enabled is False
    assert (
        unavailable.disabled_reason
        is OverworldAvailabilityReason.FLOOR_THREE_REQUIRES_FULL_ROSTER
    )

    four_recruits = presenter.build(
        floor_three_hub_game(), screen=OverworldScreen.HUB
    )
    assert next(
        option for option in four_recruits.options if option.action is start_action
    ).enabled is True


def test_floor_three_entry_starts_with_two_member_ordinary_encounter():
    game = floor_three_hub_game()
    session = make_session(game)
    start_action = getattr(OverworldAction, "START_FLOOR_THREE", None)
    assert start_action is not None

    view = session.submit(ChooseOverworldAction(start_action))

    assert session.game_state.overworld_state.active_route_id == "floor_three"
    assert session.game_state.party_state.floor_three_run_id is not None
    assert len(session.active_battle.party_states) == 2
    assert session.active_battle.enemies[0].tier == 2
    assert isinstance(view, BattleView)


def test_floor_three_semantic_start_with_three_recruits_does_not_mutate_state():
    game = floor_three_hub_game(recruited_count=3)
    session = make_session(game)
    party_before = game.party_state.snapshot()
    overworld_before = game.overworld_state.snapshot()

    session.submit(ChooseOverworldAction(OverworldAction.START_FLOOR_THREE))

    assert session.game_state.party_state.snapshot() == party_before
    assert session.game_state.overworld_state.snapshot() == overworld_before
    assert session.active_battle is None
    assert session.current_view().notice == "Recruit D3 and D4 before starting Floor 3."


def test_floor_three_boss_battle_uses_all_four_permanent_members():
    game = floor_three_hub_game()
    move_to_floor_three_boss(game)
    session = make_session(game)

    battle = session._create_active_battle(ui=None)

    participant_ids = tuple(
        member.character.profile.drifter_id for member in battle.party_states
    )
    assert set(participant_ids) == {
        member.character.profile.drifter_id for member in game.recruited_members
    }
    assert participant_ids[:2] == game.party_state.active_drifter_ids
    assert len(battle.party_states) == 4
    assert battle.enemies[0].tier == 2


def test_floor_three_encounter_victory_commits_rewards_without_banking_xp():
    game = floor_three_hub_game()
    session = make_session(game)
    session.submit(ChooseOverworldAction(OverworldAction.START_FLOOR_THREE))
    experience_before = {
        member.character.profile.drifter_id: experience_state(member)
        for member in session.game_state.recruited_members
    }
    battle = session.active_battle
    encounter_experience = sum(enemy.exp_reward for enemy in battle.enemies)

    defeat_enemies(battle)
    session._finalize_active_battle(winner="player")

    party = session.game_state.party_state
    assert session.game_state.overworld_state.current_route_node_id == (
        "floor_three_battle_02"
    )
    assert party.outing_rewards.experience == encounter_experience
    assert any(
        event["node_id"] == "floor_three_battle_01"
        and event["kind"] == "encounter_rewards"
        for event in party.resolved_run_events
    )
    assert {
        member.character.profile.drifter_id: experience_state(member)
        for member in session.game_state.recruited_members
    } == experience_before


def test_floor_three_boss_clear_recovers_after_final_save_failure_and_blocks_talisman():
    game = floor_three_hub_game()
    game.party_state.add_shared_items({"return_talisman": 1})
    assert game.party_state.load_carried_supplies({"return_talisman": 1})
    move_to_floor_three_boss(game)
    save_port = RecordingSavePort(fail_on_save_calls={2})
    session = OverworldSession(
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
    before_xp = {
        member.character.profile.drifter_id: experience_state(member)
        for member in session.game_state.recruited_members
    }
    battle = session._create_active_battle(ui=None)
    defeat_enemies(battle)

    session._finalize_active_battle(winner="player")

    assert session.game_state.floor_three_boss_settlement_pending
    pending_view = session.current_view()
    assert any(
        option.action is OverworldAction.FINALIZE_FLOOR_THREE_CLEAR
        and option.enabled
        for option in pending_view.options
    )
    assert not any(
        option.action is OverworldAction.RETURN_WITH_TALISMAN
        for option in pending_view.options
    )
    pending_state = session.game_state.party_state.snapshot()
    session.submit(ChooseOverworldAction(OverworldAction.RETURN_WITH_TALISMAN))
    assert session.game_state.floor_three_boss_settlement_pending
    assert session.game_state.party_state.snapshot() == pending_state

    session.submit(
        ChooseOverworldAction(OverworldAction.FINALIZE_FLOOR_THREE_CLEAR)
    )

    assert not session.game_state.floor_three_boss_settlement_pending
    assert session.game_state.party_state.floor_three_cleared
    assert session.game_state.party_state.phase.value == "hub"
    assert session.game_state.overworld_state.active_route_id == "surface"
    assert save_port.save_calls == 3
    assert session.game_state.party_state.shared_items["return_talisman"] == 1
    assert all(
        experience_state(member)
        != before_xp[member.character.profile.drifter_id]
        for member in session.game_state.recruited_members
    )

    settled_xp = tuple(
        experience_state(member) for member in session.game_state.recruited_members
    )
    session.submit(
        ChooseOverworldAction(OverworldAction.FINALIZE_FLOOR_THREE_CLEAR)
    )
    assert tuple(
        experience_state(member) for member in session.game_state.recruited_members
    ) == settled_xp


def test_floor_three_rest_recovers_active_pair_and_continues_route():
    game = floor_three_hub_game()
    move_to_first_floor_three_rest(game)
    active_members = game.active_party_members
    for member in active_members:
        member.health.take_damage(25)
        member.mana_resource.spend(1)
    session = make_session(game)

    rest_view = session.current_view()
    rest_actions = {option.action for option in rest_view.options}
    assert rest_view.screen is OverworldScreen.REST
    assert OverworldAction.REST in rest_actions
    assert OverworldAction.EXTRACT in rest_actions
    assert OverworldAction.CHARACTER in rest_actions
    assert OverworldAction.ITEMS in rest_actions

    session.submit(ChooseOverworldAction(OverworldAction.REST))

    assert all(member.health.current == member.health.maximum for member in active_members)
    assert all(
        member.mana_resource.current == member.mana_resource.maximum
        for member in active_members
    )
    session.submit(ChooseOverworldAction(OverworldAction.SKIP_REST))

    assert session.game_state.overworld_state.current_route_node_id == (
        "floor_three_battle_06"
    )
    assert session.game_state.party_state.floor_three_run_id is not None


def test_floor_three_defeat_discards_outing_and_restores_all_recruits():
    game = floor_three_hub_game()
    move_to_floor_three_boss(game)
    party = game.party_state
    gold_before = party.shared_gold
    assert party.add_floor_three_rewards(
        experience=100,
        gold=9,
        items={"scrap_metal": 1},
    ) is None
    session = make_session(game)
    battle = session._create_active_battle(ui=None)
    for member in battle.party_states:
        member.health.take_damage(member.health.current)

    session._finalize_active_battle(winner="enemy")

    assert session.game_state.party_state.phase.value == "hub"
    assert session.game_state.party_state.floor_three_run_id is None
    assert not session.game_state.party_state.floor_three_cleared
    assert session.game_state.party_state.outing_rewards.experience == 0
    assert session.game_state.party_state.shared_gold == gold_before
    assert all(
        member.health.current == member.health.maximum
        and member.mana_resource.current == member.mana_resource.maximum
        for member in session.game_state.recruited_members
    )


def test_floor_three_reward_save_failure_restores_encounter_checkpoint_and_supplies():
    game = floor_three_hub_game()
    game.party_state.add_shared_items({"healing_potion": 1})
    assert game.party_state.load_carried_supplies({"healing_potion": 1})
    session = OverworldSession(
        game,
        battle_factory=lambda player, enemies, **kwargs: Battle(
            player,
            enemies,
            rng=StableRng(),
            **kwargs,
        ),
        enemy_factory=create_enemy_state,
        save_port=RecordingSavePort(fail_on_save_calls={1}),
        run_event_rng=StableRng(),
    )
    session.submit(ChooseOverworldAction(OverworldAction.START_FLOOR_THREE))
    battle = session.active_battle
    active_member = battle.party_states[0]
    active_member.health.take_damage(25)
    assert game.party_state.use_healing_potion(
        active_member,
        deployed_members=tuple(battle.party_states),
    )
    assert game.party_state.carried_items == {}
    defeat_enemies(battle)

    session._finalize_active_battle(winner="player")

    party = session.game_state.party_state
    assert session.game_state.overworld_state.current_route_node_id == (
        "floor_three_battle_01"
    )
    assert session.game_state.overworld_state.current_contextual_route_phase.value == (
        "retry"
    )
    assert party.outing_rewards.experience == 0
    assert party.resolved_run_events == ()
    assert party.carried_items == {"healing_potion": 1}
    assert active_member.health.current == active_member.health.maximum


def test_floor_three_boss_allows_healing_potion_on_any_permanent_member():
    game = floor_three_hub_game()
    game.party_state.add_shared_items({"healing_potion": 1})
    assert game.party_state.load_carried_supplies({"healing_potion": 1})
    move_to_floor_three_boss(game)
    session = make_session(game)
    battle = session._create_active_battle(ui=None)
    target = battle.party_states[3]
    target.health.take_damage(25)

    assert game.party_state.use_healing_potion(
        target,
        deployed_members=tuple(battle.party_states),
    )

    assert target.health.current > target.health.maximum - 25
    assert game.party_state.carried_items == {}


def test_floor_three_extraction_from_rest_banks_partial_rewards_and_returns_supplies():
    game = floor_three_hub_game()
    game.party_state.add_shared_items({"return_talisman": 1})
    assert game.party_state.load_carried_supplies({"return_talisman": 1})
    move_to_first_floor_three_rest(game)
    party = game.party_state
    gold_before = party.shared_gold
    party.add_floor_three_rewards(
        experience=200,
        gold=10,
        items={"grade_iii_metal": 1},
    )
    session = make_session(game)

    session.submit(ChooseOverworldAction(OverworldAction.EXTRACT))
    assert session.game_state.party_state.phase.value == "extraction"
    session.submit(ChooseOverworldAction(OverworldAction.RETURN_TO_HUB))

    assert session.game_state.party_state.phase.value == "hub"
    assert session.game_state.party_state.floor_three_run_id is None
    assert session.game_state.party_state.shared_gold == gold_before + 5
    assert session.game_state.party_state.shared_items["grade_iii_metal"] == 1
    assert session.game_state.party_state.shared_items["return_talisman"] == 1
    assert session.game_state.overworld_state.active_route_id == "surface"
