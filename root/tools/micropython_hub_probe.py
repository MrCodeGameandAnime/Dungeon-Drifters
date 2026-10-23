"""Lazily loaded Hub tutorial and extraction portion of the raw probe."""

import gc


_TUTORIAL_COMPOSITION = ("goblin", "goblin", "goblin")
_TUTORIAL_REWARDS = (120, 9)
_FLOOR_ONE_NODE_IDS = (
    "floor_one_battle_01",
    "floor_one_battle_02",
    "floor_one_battle_03",
    "floor_one_battle_04",
    "floor_one_battle_05",
    "floor_one_midway_rest",
    "floor_one_battle_06",
    "floor_one_battle_07",
    "floor_one_battle_08",
    "floor_one_battle_09",
    "floor_one_pre_boss_rest",
    "floor_one_battle_10",
)
_FLOOR_ONE_ENCOUNTER_NODE_IDS = (
    "floor_one_battle_01",
    "floor_one_battle_02",
    "floor_one_battle_03",
    "floor_one_battle_04",
    "floor_one_battle_05",
    "floor_one_battle_06",
    "floor_one_battle_07",
    "floor_one_battle_08",
    "floor_one_battle_09",
    "floor_one_battle_10",
)
_FLOOR_ONE_EXPECTED_REWARDS = (1340, 96)
_FLOOR_ONE_EXPECTED_REWARD_PER_DRIFTER = 670


def _recruit_companion(state):
    if (
        state["route_battle_factory"].battle_compositions
        or state["route_enemy_factory"].enemies
        or state["route_battle_factory"].completed_count
        or "route_initial_view" in state
    ):
        raise AssertionError("surface route evidence was retained into the Hub probe")

    from app.game.party_state import DungeonPhase
    from app.presentation.overworld_models import OverworldAction, OverworldScreen
    from app.ui.overworld_ui import ChooseCompanion, ChooseOverworldAction

    game = state["route_game"]
    session = state["route_session"]
    if session.current_view().screen is not OverworldScreen.HUB:
        raise AssertionError("tutorial recruitment did not begin at the Hub")
    selection = session.submit(
        ChooseOverworldAction(OverworldAction.RECRUIT_COMPANION)
    )
    if selection.screen is not OverworldScreen.COMPANION_SELECTION:
        raise AssertionError("Hub did not open companion selection")
    ready = session.submit(ChooseCompanion("azhvielle"))
    if ready.screen is not OverworldScreen.PARTY_READY:
        raise AssertionError("companion recruitment did not ready the party")
    if game.party_state.phase is not DungeonPhase.PARTY_READY:
        raise AssertionError("recruitment did not enter PARTY_READY")
    if game.party_state.shared_gold != 10:
        raise AssertionError("recruitment did not spend 65 of the Hub's 75 gold")
    if tuple(
        member.character.profile.drifter_id
        for member in game.party_state.companions
    ) != ("azhvielle",):
        raise AssertionError("the tutorial companion was not recruited")
    if not any(
        option.action.value == "ready" and option.enabled
        for option in ready.options
    ):
        raise AssertionError("the recruited party was not offered Ready")


def _ready_party(state):
    from app.game.party_state import DungeonPhase
    from app.presentation.battle_models import BattleView
    from app.presentation.overworld_models import OverworldAction
    from app.ui.overworld_ui import ChooseOverworldAction

    game = state["route_game"]
    session = state["route_session"]
    members = (game.player_state,) + game.party_state.companions
    if len(members) != 2:
        raise AssertionError("tutorial did not have a two-Drifter party")
    for member in members:
        if not member.is_alive():
            raise AssertionError("a Drifter was not alive at tutorial start")
        if member.health.current == member.health.maximum:
            member.health.take_damage(1)
        if member.mana_resource.current == member.mana_resource.maximum:
            member.mana_resource.spend(1)
        if member.health.current == member.health.maximum:
            raise AssertionError("tutorial did not begin with injured Drifters")
        if member.mana_resource.current == member.mana_resource.maximum:
            raise AssertionError("tutorial did not begin with spent Mana")

    state["hub_tutorial_xp_before"] = tuple(
        member.exp_state.current for member in members
    )
    battle_view = session.submit(ChooseOverworldAction(OverworldAction.READY))
    if not isinstance(battle_view, BattleView):
        raise AssertionError("Ready did not enter the tutorial Battle")
    if game.party_state.phase is not DungeonPhase.OUTING:
        raise AssertionError("Ready did not begin the tutorial outing")
    if len(battle_view.party_members) != 2:
        raise AssertionError("tutorial BattleView omitted a Drifter")
    battle_factory = state["route_battle_factory"]
    if battle_factory.battle_compositions[-1] != _TUTORIAL_COMPOSITION:
        raise AssertionError("tutorial encounter was not three Goblins")
    state["hub_tutorial_battle_view"] = battle_view


def _complete_tutorial_battle(state, complete_battle):
    from app.presentation.overworld_models import OverworldScreen

    battle_view = state.pop("hub_tutorial_battle_view")
    extraction = complete_battle(battle_view)
    if extraction.screen is not OverworldScreen.EXTRACTION:
        raise AssertionError("tutorial victory did not open Extraction")


def _assert_extraction_pending(state):
    from app.game.party_state import DungeonPhase
    from app.presentation.overworld_models import OverworldAction, OverworldScreen

    game = state["route_game"]
    session = state["route_session"]
    view = session.current_view()
    if view.screen is not OverworldScreen.EXTRACTION:
        raise AssertionError("tutorial rewards were not presented at Extraction")
    if game.party_state.phase is not DungeonPhase.EXTRACTION:
        raise AssertionError("party did not enter the Extraction phase")
    if (
        view.outing_rewards.experience,
        view.outing_rewards.gold,
    ) != _TUTORIAL_REWARDS:
        raise AssertionError("tutorial Extraction rewards changed")
    if view.outing_rewards.items != ():
        raise AssertionError("tutorial unexpectedly offered item rewards")
    if game.party_state.shared_gold != 10:
        raise AssertionError("tutorial gold was banked before extraction")
    members = (game.player_state,) + game.party_state.companions
    if tuple(
        member.exp_state.current for member in members
    ) != state["hub_tutorial_xp_before"]:
        raise AssertionError("tutorial EXP was banked before extraction")
    enabled = tuple(
        option.action for option in view.options if option.enabled
    )
    if enabled != (OverworldAction.RETURN_TO_HUB,):
        raise AssertionError("Extraction did not offer only Return to Hub")


def _return_to_hub(state):
    from app.presentation.overworld_models import OverworldAction, OverworldScreen
    from app.ui.overworld_ui import ChooseOverworldAction

    returned = state["route_session"].submit(
        ChooseOverworldAction(OverworldAction.RETURN_TO_HUB)
    )
    if returned.screen is not OverworldScreen.HUB:
        raise AssertionError("Extraction did not return the party to the Hub")


def _assert_final_state(state):
    from app.game.party_state import DungeonPhase
    from app.presentation.overworld_models import OverworldScreen

    game = state["route_game"]
    session = state["route_session"]
    party = game.party_state
    members = (game.player_state,) + party.companions
    if party.phase is not DungeonPhase.HUB or not party.tutorial_complete:
        raise AssertionError("tutorial extraction did not complete at the Hub")
    if len(members) != 2:
        raise AssertionError("tutorial extraction changed party membership")
    if party.shared_gold != 19:
        raise AssertionError("tutorial gold was not secured exactly once")
    if party.shared_items != {}:
        raise AssertionError("tutorial unexpectedly secured items")
    if (party.outing_rewards.experience, party.outing_rewards.gold) != (0, 0):
        raise AssertionError("tutorial rewards remained pending after extraction")
    if tuple(
        member.exp_state.current - previous
        for member, previous in zip(members, state["hub_tutorial_xp_before"])
    ) != (60, 60):
        raise AssertionError("tutorial EXP was not split evenly on extraction")
    for member in members:
        if member.health.current != member.health.maximum:
            raise AssertionError("extraction did not fully restore HP")
        if member.mana_resource.current != member.mana_resource.maximum:
            raise AssertionError("extraction did not fully restore Mana")
    if session.active_battle is not None:
        raise AssertionError("tutorial Battle remained active after extraction")
    battle_factory = state["route_battle_factory"]
    if battle_factory.completed_count != len(battle_factory.battle_compositions):
        raise AssertionError("tutorial Battle was not completed exactly once")
    if battle_factory.battle_compositions[-1] != _TUTORIAL_COMPOSITION:
        raise AssertionError("tutorial Battle composition evidence changed")
    if session.current_view().screen is not OverworldScreen.HUB:
        raise AssertionError("final tutorial view did not remain at the Hub")


def _total_experience(member):
    from app.player.progression import xp_required_for_next_level

    return sum(
        xp_required_for_next_level(level)
        for level in range(1, member.level_state.current)
    ) + member.exp_state.current


def _open_floor_one_warning(state):
    from app.game.party_state import DungeonPhase
    from app.presentation.overworld_models import OverworldAction, OverworldScreen
    from app.ui.overworld_ui import ChooseOverworldAction

    game = state["route_game"]
    session = state["route_session"]
    if session.current_view().screen is not OverworldScreen.HUB:
        raise AssertionError("Floor 1 did not begin from the Hub")
    if game.party_state.phase is not DungeonPhase.HUB:
        raise AssertionError("the tutorial party was not at the Hub")

    battle_factory = state["route_battle_factory"]
    battle_factory.battle_compositions[:] = []
    battle_factory.completed_count = 0
    state["route_enemy_factory"].enemies[:] = []
    gc.collect()

    route = state["catalog"].get_route_spec("floor_one")
    if tuple(node.node_id for node in route.nodes) != _FLOOR_ONE_NODE_IDS:
        raise AssertionError("Floor 1 route sequence changed")
    rewards = [
        state["catalog"].get_encounter_rewards(node.encounter_id)
        for node in route.nodes
        if node.encounter_id is not None
    ]
    total_rewards = (
        sum(reward[0] for reward in rewards),
        sum(reward[1] for reward in rewards),
    )
    if total_rewards != _FLOOR_ONE_EXPECTED_REWARDS:
        raise AssertionError("Floor 1 authored reward totals changed")

    party = game.party_state
    members = (game.player_state,) + party.companions
    state["floor_one_route"] = route
    state["floor_one_battle_compositions"] = []
    state["floor_one_world_history"] = game.world_state.defeated_encounters
    state["floor_one_xp_before"] = tuple(
        _total_experience(member) for member in members
    )
    state["floor_one_gold_before"] = party.shared_gold
    state["floor_one_route_rewards"] = total_rewards

    warning = session.submit(
        ChooseOverworldAction(OverworldAction.START_FLOOR_ONE)
    )
    if warning.screen is not OverworldScreen.FLOOR_ONE_WARNING:
        raise AssertionError("Hub did not open the Floor 1 warning")
    if "Death means returning to the Hub" not in warning.adventure_text:
        raise AssertionError("Floor 1 warning omitted the death consequence")
    if tuple(option.action for option in warning.options) != (
        OverworldAction.SET_OUT,
        OverworldAction.BACK,
    ):
        raise AssertionError("Floor 1 warning offered an unexpected action")


def _set_out_floor_one(state):
    from app.game.party_state import DungeonPhase
    from app.presentation.battle_models import BattleView
    from app.presentation.overworld_models import OverworldAction
    from app.ui.overworld_ui import ChooseOverworldAction

    game = state["route_game"]
    session = state["route_session"]
    battle_view = session.submit(
        ChooseOverworldAction(OverworldAction.SET_OUT)
    )
    if not isinstance(battle_view, BattleView):
        raise AssertionError("Set Out did not start the first Floor 1 battle")
    if game.party_state.phase is not DungeonPhase.OUTING:
        raise AssertionError("Set Out did not begin a dangerous run")
    if game.party_state.outing_xp_multiplier_percent != 100:
        raise AssertionError("first Floor 1 run did not use full XP")
    if game.overworld_state.current_route_node_id != _FLOOR_ONE_NODE_IDS[0]:
        raise AssertionError("Floor 1 did not start at its first battle")
    state["floor_one_battle_view"] = battle_view


def _complete_floor_one_battle(state, complete_battle, battle_number):
    from app.presentation.battle_models import BattleView
    from app.presentation.overworld_models import OverworldAction, OverworldScreen
    from app.ui.overworld_ui import ChooseOverworldAction

    game = state["route_game"]
    session = state["route_session"]
    node_id = _FLOOR_ONE_ENCOUNTER_NODE_IDS[battle_number - 1]
    if battle_number > 1:
        view = session.current_view()
        if view.screen is not OverworldScreen.MAIN:
            raise AssertionError("Floor 1 encounter did not return to MAIN")
        if game.overworld_state.current_route_node_id != node_id:
            raise AssertionError("Floor 1 encounter cursor changed")
        if view.contextual_route_option.action is not OverworldAction.ENTER_ENCOUNTER:
            raise AssertionError("Floor 1 encounter did not offer Enter Encounter")
        battle_view = session.submit(
            ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER)
        )
    else:
        battle_view = state.pop("floor_one_battle_view")

    if not isinstance(battle_view, BattleView):
        raise AssertionError("Floor 1 route node did not start a Battle")
    node = state["catalog"].get_route_node_spec(node_id)
    encounter = state["catalog"].get_encounter_spec(node.encounter_id)
    composition = tuple(encounter.enemy_archetype_ids)
    if tuple(
        enemy.archetype_id for enemy in session.active_battle.enemies
    ) != composition:
        raise AssertionError("Floor 1 Battle composition changed")
    if len(battle_view.enemies) != len(composition):
        raise AssertionError("Floor 1 BattleView composition changed")
    if len(battle_view.party_members) != 2:
        raise AssertionError("Floor 1 Battle omitted a Drifter")

    state["floor_one_battle_compositions"].append(composition)
    view = complete_battle(battle_view)
    if session.active_battle is not None:
        raise AssertionError("completed Floor 1 Battle remained active")
    if battle_number < 10:
        following = _FLOOR_ONE_NODE_IDS[
            _FLOOR_ONE_NODE_IDS.index(node_id) + 1
        ]
        if game.overworld_state.current_route_node_id != following:
            raise AssertionError("Floor 1 did not advance one authored node")
        expected_screen = (
            OverworldScreen.REST
            if following in ("floor_one_midway_rest", "floor_one_pre_boss_rest")
            else OverworldScreen.MAIN
        )
        if view.screen is not expected_screen:
            raise AssertionError("Floor 1 Battle returned an unexpected screen")
    elif view.screen is not OverworldScreen.HUB:
        raise AssertionError("Goblin Lord victory did not return to the Hub")

    rewards = state["floor_one_route_rewards"]
    encounter_rewards = state["catalog"].get_encounter_rewards(node.encounter_id)
    party_rewards = game.party_state.outing_rewards
    if battle_number == 1:
        state["floor_one_pending_xp"] = 0
        state["floor_one_pending_gold"] = 0
    state["floor_one_pending_xp"] += encounter_rewards[0]
    state["floor_one_pending_gold"] += encounter_rewards[1]
    if battle_number < 10 and (
        party_rewards.experience != state["floor_one_pending_xp"]
        or party_rewards.gold != state["floor_one_pending_gold"]
    ):
        raise AssertionError("Floor 1 unsecured reward ledger changed")
    if battle_number == 10 and (
        state["floor_one_pending_xp"] != rewards[0]
        or state["floor_one_pending_gold"] != rewards[1]
    ):
        raise AssertionError("Floor 1 completed with unexpected reward totals")

    del state["route_enemy_factory"].enemies[:]
    gc.collect()


def _resolve_floor_one_midway_rest(state):
    from app.presentation.overworld_models import OverworldAction, OverworldScreen
    from app.ui.overworld_ui import ChooseOverworldAction

    game = state["route_game"]
    session = state["route_session"]
    view = session.current_view()
    if (
        view.screen is not OverworldScreen.REST
        or game.overworld_state.current_route_node_id != "floor_one_midway_rest"
    ):
        raise AssertionError("the first Floor 1 Rest is in the wrong location")
    for option in view.options:
        if option.action is OverworldAction.EXTRACT and not option.enabled:
            raise AssertionError("midway Rest disabled extraction")

    members = (game.player_state,) + game.party_state.companions
    for member in members:
        if member.health.current == member.health.maximum:
            member.health.take_damage(1)
        if member.mana_resource.current == member.mana_resource.maximum:
            member.mana_resource.spend(1)
    session.submit(ChooseOverworldAction(OverworldAction.REST))
    if session.current_view().screen is not OverworldScreen.MAIN:
        raise AssertionError("Recover did not continue to battle six")
    _assert_rest_fallback(game, state)
    for member in members:
        if member.health.current != member.health.maximum:
            raise AssertionError("midway Recover did not restore HP")
        if member.mana_resource.current != member.mana_resource.maximum:
            raise AssertionError("midway Recover did not restore Mana")


def _resolve_floor_one_pre_boss_rest(state):
    from app.presentation.overworld_models import OverworldAction, OverworldScreen
    from app.ui.overworld_ui import ChooseOverworldAction

    game = state["route_game"]
    session = state["route_session"]
    view = session.current_view()
    if (
        view.screen is not OverworldScreen.REST
        or game.overworld_state.current_route_node_id != "floor_one_pre_boss_rest"
    ):
        raise AssertionError("the pre-boss Floor 1 Rest is in the wrong location")
    before = tuple(
        (member.health.current, member.mana_resource.current)
        for member in (game.player_state,) + game.party_state.companions
    )
    session.submit(ChooseOverworldAction(OverworldAction.SKIP_REST))
    if session.current_view().screen is not OverworldScreen.MAIN:
        raise AssertionError("Continue Without Rest did not advance to the boss")
    _assert_rest_fallback(game, state)
    after = tuple(
        (member.health.current, member.mana_resource.current)
        for member in (game.player_state,) + game.party_state.companions
    )
    if after != before:
        raise AssertionError("Continue Without Rest restored resources")


def _assert_rest_fallback(game, state):
    from app.game.party_state import DungeonPhase

    fallback = state["route_battle_factory"].saved_game_state
    if fallback is None or fallback is game:
        raise AssertionError("Rest exit did not save an independent fallback")
    if fallback.party_state.phase is not DungeonPhase.HUB:
        raise AssertionError("Rest fallback did not return to the Hub")
    if fallback.overworld_state.active_route_id != "surface":
        raise AssertionError("Rest fallback retained the Floor 1 route")
    if fallback.overworld_state.current_route_node_id != "surface_dungeon_entrance":
        raise AssertionError("Rest fallback returned to the wrong location")
    if (
        fallback.party_state.outing_rewards.experience
        or fallback.party_state.outing_rewards.gold
        or fallback.party_state.outing_rewards.items
    ):
        raise AssertionError("Rest fallback retained unsecured rewards")


def _assert_floor_one_final_state(state):
    from app.game.party_state import DungeonPhase
    from app.presentation.overworld_models import OverworldScreen

    game = state["route_game"]
    session = state["route_session"]
    party = game.party_state
    members = (game.player_state,) + party.companions
    if party.phase is not DungeonPhase.HUB or not party.floor_one_cleared:
        raise AssertionError("Goblin Lord victory did not clear Floor 1")
    if party.floor_one_runs_started_after_clear != 0:
        raise AssertionError("the first Floor 1 clear counted as a replay")
    if party.outing_xp_multiplier_percent != 100:
        raise AssertionError("first clear changed the Floor 1 XP rate")
    if party.shared_gold != state["floor_one_gold_before"] + _FLOOR_ONE_EXPECTED_REWARDS[1]:
        raise AssertionError("Floor 1 gold was not fully secured")
    if state["route_battle_factory"].saved_game_state is not game:
        raise AssertionError("boss clear did not save the Hub outcome")
    if (
        party.outing_rewards.experience,
        party.outing_rewards.gold,
        party.outing_rewards.items,
    ) != (0, 0, {}):
        raise AssertionError("Floor 1 rewards remained unsecured after the boss")
    if game.world_state.defeated_encounters != state["floor_one_world_history"]:
        raise AssertionError("Floor 1 encounters changed Surface defeat history")
    if game.overworld_state.active_route_id != "surface":
        raise AssertionError("Floor 1 clear did not return to the Surface route")
    if game.overworld_state.current_route_node_id != "surface_dungeon_entrance":
        raise AssertionError("Floor 1 clear returned to the wrong location")
    if not game.overworld_state.route_complete or not game.overworld_state.dungeon_entrance_reached:
        raise AssertionError("Floor 1 clear changed Surface completion")
    xp_after = tuple(_total_experience(member) for member in members)
    if tuple(
        after - before
        for after, before in zip(xp_after, state["floor_one_xp_before"])
    ) != (_FLOOR_ONE_EXPECTED_REWARD_PER_DRIFTER,) * 2:
        raise AssertionError("Floor 1 XP was not split evenly")
    if tuple(state["floor_one_battle_compositions"]) != tuple(
        tuple(
            state["catalog"].get_encounter_spec(node.encounter_id).enemy_archetype_ids
        )
        for node in state["floor_one_route"].nodes
        if node.encounter_id is not None
    ):
        raise AssertionError("Floor 1 composition sequence changed")
    if state["route_battle_factory"].completed_count != 10:
        raise AssertionError("not all ten Floor 1 battles completed")
    if session.active_battle is not None:
        raise AssertionError("Floor 1 left an active Battle after the boss")
    if session.current_view().screen is not OverworldScreen.HUB:
        raise AssertionError("Floor 1 final view did not remain at the Hub")
    for member in members:
        if member.health.current != member.health.maximum:
            raise AssertionError("Floor 1 boss clear did not restore HP")
        if member.mana_resource.current != member.mana_resource.maximum:
            raise AssertionError("Floor 1 boss clear did not restore Mana")


def run(state, complete_battle, run_stage):
    run_stage("HUB_RECRUITMENT", lambda: _recruit_companion(state))
    run_stage("HUB_READY", lambda: _ready_party(state))
    run_stage(
        "HUB_TUTORIAL_BATTLE",
        lambda: _complete_tutorial_battle(state, complete_battle),
    )
    run_stage("HUB_EXTRACTION", lambda: _assert_extraction_pending(state))
    run_stage("HUB_RETURN", lambda: _return_to_hub(state))
    run_stage("HUB_FINAL_STATE", lambda: _assert_final_state(state))
    run_stage("FLOOR_ONE_WARNING", lambda: _open_floor_one_warning(state))
    run_stage("FLOOR_ONE_SET_OUT", lambda: _set_out_floor_one(state))
    run_stage(
        "FLOOR_ONE_BATTLE_01",
        lambda: _complete_floor_one_battle(state, complete_battle, 1),
    )
    run_stage(
        "FLOOR_ONE_BATTLE_02",
        lambda: _complete_floor_one_battle(state, complete_battle, 2),
    )
    run_stage(
        "FLOOR_ONE_BATTLE_03",
        lambda: _complete_floor_one_battle(state, complete_battle, 3),
    )
    run_stage(
        "FLOOR_ONE_BATTLE_04",
        lambda: _complete_floor_one_battle(state, complete_battle, 4),
    )
    run_stage(
        "FLOOR_ONE_BATTLE_05",
        lambda: _complete_floor_one_battle(state, complete_battle, 5),
    )
    run_stage(
        "FLOOR_ONE_MIDWAY_REST",
        lambda: _resolve_floor_one_midway_rest(state),
    )
    run_stage(
        "FLOOR_ONE_BATTLE_06",
        lambda: _complete_floor_one_battle(state, complete_battle, 6),
    )
    run_stage(
        "FLOOR_ONE_BATTLE_07",
        lambda: _complete_floor_one_battle(state, complete_battle, 7),
    )
    run_stage(
        "FLOOR_ONE_BATTLE_08",
        lambda: _complete_floor_one_battle(state, complete_battle, 8),
    )
    run_stage(
        "FLOOR_ONE_BATTLE_09",
        lambda: _complete_floor_one_battle(state, complete_battle, 9),
    )
    run_stage(
        "FLOOR_ONE_PRE_BOSS_REST",
        lambda: _resolve_floor_one_pre_boss_rest(state),
    )
    run_stage(
        "FLOOR_ONE_BATTLE_10",
        lambda: _complete_floor_one_battle(state, complete_battle, 10),
    )
    run_stage(
        "FLOOR_ONE_FINAL_STATE",
        lambda: _assert_floor_one_final_state(state),
    )
