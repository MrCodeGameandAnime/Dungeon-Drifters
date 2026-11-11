"""Floor III runtime qualification on the completed Floor II probe state."""

import gc


_FLOOR_THREE_NODE_IDS = (
    "floor_three_battle_01",
    "floor_three_battle_02",
    "floor_three_battle_03",
    "floor_three_battle_04",
    "floor_three_battle_05",
    "floor_three_midway_rest",
    "floor_three_battle_06",
    "floor_three_battle_07",
    "floor_three_battle_08",
    "floor_three_battle_09",
    "floor_three_pre_boss_rest",
    "floor_three_battle_10",
)
_GRADE_THREE_ITEMS = (
    "grade_iii_metal",
    "grade_iii_fiber",
    "grade_iii_timber",
    "grade_iii_cores",
)
_M4B_STAGE_NAMES = (
    "M4B_TIER_TWO_CONTENT",
    "M4B_D3_RECRUITMENT",
    "M4B_D4_RECRUITMENT",
    "M4B_FLOOR_THREE_START",
    "M4B_FLOOR_THREE_BATTLE_01",
    "M4B_FLOOR_THREE_BATTLE_02",
    "M4B_FLOOR_THREE_BATTLE_03",
    "M4B_FLOOR_THREE_BATTLE_04",
    "M4B_FLOOR_THREE_BATTLE_05",
    "M4B_MIDWAY_REST",
    "M4B_FLOOR_THREE_BATTLE_06",
    "M4B_FLOOR_THREE_BATTLE_07",
    "M4B_FLOOR_THREE_BATTLE_08",
    "M4B_FLOOR_THREE_BATTLE_09",
    "M4B_PRE_BOSS_REST",
    "M4B_FLOOR_THREE_BATTLE_10_BOSS",
    "M4B_FLOOR_THREE_FINAL_STATE",
    "M4B_PROBE_TEARDOWN",
)


def _game(state):
    game = state["route_session"].game_state
    state["route_game"] = game
    return game


def _assert_tier_two_content(state):
    from app.content.catalog import get_enemy_spec, get_encounter_spec, get_route_spec

    route = get_route_spec("floor_three")
    if tuple(node.node_id for node in route.nodes) != _FLOOR_THREE_NODE_IDS:
        raise AssertionError("Floor III authored route node sequence changed")

    drop_families = {}
    for node in route.nodes:
        if node.encounter_id is None:
            continue
        encounter = get_encounter_spec(node.encounter_id)
        for archetype_id in encounter.enemy_archetype_ids:
            enemy = get_enemy_spec(archetype_id)
            if 2 not in enemy.supported_tiers:
                raise AssertionError("Floor III encounter lacks Tier II enemy data")
            profile = None
            for candidate in enemy.tier_profiles:
                if candidate.tier == 2:
                    profile = candidate
                    break
            if profile is None:
                raise AssertionError("Tier II enemy profile was not authored")
            for drop in profile.item_drops:
                if drop.item_id in _GRADE_THREE_ITEMS:
                    drop_families[drop.item_id] = True
    if any(item_id not in drop_families for item_id in _GRADE_THREE_ITEMS):
        raise AssertionError("Floor III Tier II profiles omit a Grade III family")
    state["m4b_floor_three_route"] = route


def _recruit_drifter(state, drifter_id):
    from app.game.recruitment import available_recruitment_event
    from app.presentation.overworld_models import OverworldAction, OverworldScreen
    from app.ui.overworld_ui import ChooseCompanion, ChooseOverworldAction

    session = state["route_session"]
    game = _game(state)
    party = game.party_state
    if not party.floor_two_cleared or party.floor_three_run_id is not None:
        raise AssertionError("Floor III recruitment started outside the cleared Hub")
    if game.overworld_state.current_route_node_id != "surface_dungeon_entrance":
        raise AssertionError("Floor III recruitment began at the wrong Hub location")
    if "m4b_active_drifter_ids" not in state:
        state["m4b_active_drifter_ids"] = party.active_drifter_ids
        if party.shared_gold < 130:
            party.add_shared_gold(130 - party.shared_gold)
        state["m4b_recruitment_start_gold"] = party.shared_gold

    event = available_recruitment_event(game)
    if event is None or event.event_id != "floor_two_hub_recruitment":
        raise AssertionError("post-Floor-II recruitment event was unavailable")
    view = session.submit(
        ChooseOverworldAction(OverworldAction.RECRUIT_COMPANION)
    )
    if view.screen is not OverworldScreen.COMPANION_SELECTION:
        raise AssertionError("Hub did not open permanent recruitment")
    if not any(
        choice.drifter_id == drifter_id and choice.enabled
        for choice in view.companion_choices
    ):
        raise AssertionError("expected permanent Drifter was not recruitable")
    view = session.submit(ChooseCompanion(drifter_id, event.event_id))
    game = _game(state)
    member = game.member_for_drifter_id(drifter_id)
    if view.screen is not OverworldScreen.HUB:
        raise AssertionError("permanent recruitment did not return to the Hub")
    if member.level_state.current != 1 or member.exp_state.current != 0:
        raise AssertionError("permanent recruit did not start at Level 1")
    if member.growth_points != 0:
        raise AssertionError("permanent recruit received unapproved Growth Points")
    if game.party_state.active_drifter_ids != state["m4b_active_drifter_ids"]:
        raise AssertionError("permanent recruitment changed the active pair")
    expected_gold = state["m4b_recruitment_start_gold"] - (
        65 if drifter_id == "zhaivra" else 130
    )
    if game.party_state.shared_gold != expected_gold:
        raise AssertionError("permanent recruitment did not charge exactly 65 gold")
    if tuple(
        candidate.character.profile.drifter_id
        for candidate in game.recruited_members
    )[-1] != drifter_id:
        raise AssertionError("permanent roster did not record the new Drifter")


def _start_floor_three(state):
    from app.presentation.battle_models import BattleView
    from app.presentation.overworld_models import OverworldAction, OverworldScreen
    from app.ui.overworld_ui import ChooseOverworldAction

    game = _game(state)
    if len(game.recruited_members) != 4:
        raise AssertionError("Floor III started without all four recruits")
    if game.party_state.active_drifter_ids != state["m4b_active_drifter_ids"]:
        raise AssertionError("Floor III start changed the active pair")
    route = state["m4b_floor_three_route"]
    if game.overworld_state.active_route_id != "surface":
        raise AssertionError("Floor III did not start from the Surface Hub")

    enemy_factory = state["route_enemy_factory"]
    state["m4b_completed_battle_start"] = (
        state["route_battle_factory"].completed_count
    )
    enemy_start = len(enemy_factory.enemies)
    tier_start = len(enemy_factory.tiers)
    view = state["route_session"].submit(
        ChooseOverworldAction(OverworldAction.START_FLOOR_THREE)
    )
    game = _game(state)
    if not isinstance(view, BattleView) or state["route_session"].active_battle is None:
        raise AssertionError("Floor III did not enter its first Battle")
    if game.overworld_state.active_route_id != "floor_three":
        raise AssertionError("Floor III route was not selected")
    if game.party_state.floor_three_run_id is None:
        raise AssertionError("Floor III run identity was not created")
    first_node = route.nodes[0]
    encounter = state["catalog"].get_encounter_spec(first_node.encounter_id)
    if tuple(enemy_factory.tiers[tier_start:]) != (2,) * len(
        encounter.enemy_archetype_ids
    ):
        raise AssertionError("Floor III did not construct Tier II enemies")
    if len(view.party_members) != 2:
        raise AssertionError("ordinary Floor III encounter did not use the active pair")
    state["m4b_roster_ids"] = tuple(
        member.character.profile.drifter_id for member in game.recruited_members
    )
    state["m4b_floor_three_run_id"] = game.party_state.floor_three_run_id
    state["m4b_first_enemy_start"] = enemy_start
    state["m4b_first_tier_start"] = tier_start
    state["m4b_first_battle_view"] = view


def _resolve_rest(state, node_id, next_node_id):
    from app.presentation.overworld_models import OverworldAction, OverworldScreen
    from app.ui.overworld_ui import ChooseOverworldAction

    session = state["route_session"]
    game = _game(state)
    view = session.current_view()
    if view.screen is not OverworldScreen.REST:
        raise AssertionError("Floor III Rest node did not present Rest")
    if game.overworld_state.current_route_node_id != node_id:
        raise AssertionError("Floor III Rest cursor changed")
    view = session.submit(ChooseOverworldAction(OverworldAction.REST))
    if view.screen is not OverworldScreen.REST:
        raise AssertionError("Floor III recovery unexpectedly advanced the route")
    game = _game(state)
    snapshot = game.snapshot()
    restored = game.clone()
    if restored.snapshot() != snapshot:
        raise AssertionError("Floor III Rest checkpoint changed on round-trip")
    del restored
    view = session.submit(ChooseOverworldAction(OverworldAction.SKIP_REST))
    game = _game(state)
    if view.screen is not OverworldScreen.MAIN:
        raise AssertionError("Floor III Rest did not resume the route")
    if game.overworld_state.current_route_node_id != next_node_id:
        raise AssertionError("Floor III Rest advanced to the wrong encounter")


def _complete_battle(state, complete_battle, battle_number):
    from app.content.route_spec import RouteNodeKind
    from app.presentation.overworld_models import OverworldAction, OverworldScreen
    from app.ui.overworld_ui import ChooseOverworldAction

    session = state["route_session"]
    game = _game(state)
    route = state["m4b_floor_three_route"]
    battle_nodes = tuple(
        node
        for node in route.nodes
        if node.kind in {RouteNodeKind.COMBAT, RouteNodeKind.BOSS}
    )
    node = battle_nodes[battle_number - 1]
    if node.node_id != "floor_three_battle_%02d" % battle_number:
        raise AssertionError("Floor III battle index did not match its route")
    encounter = state["catalog"].get_encounter_spec(node.encounter_id)
    enemy_factory = state["route_enemy_factory"]
    if battle_number == 1:
        enemy_start = state.pop("m4b_first_enemy_start")
        tier_start = state.pop("m4b_first_tier_start")
        battle_view = state.pop("m4b_first_battle_view")
    else:
        enemy_start = len(enemy_factory.enemies)
        tier_start = len(enemy_factory.tiers)
        view = session.current_view()
        if view.screen is not OverworldScreen.MAIN:
            raise AssertionError("Floor III encounter did not present MAIN")
        if game.overworld_state.current_route_node_id != node.node_id:
            raise AssertionError("Floor III encounter cursor changed")
        battle_view = session.submit(
            ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER)
        )

    active = session.active_battle
    if active is None or tuple(
        enemy.archetype_id for enemy in active.enemies
    ) != encounter.enemy_archetype_ids:
        raise AssertionError("Floor III Battle differed from authored composition")
    if tuple(enemy_factory.tiers[tier_start:]) != (2,) * len(
        encounter.enemy_archetype_ids
    ):
        raise AssertionError("Floor III Battle did not use Tier II enemies")
    expected_party_size = 4 if battle_number == 10 else 2
    if len(battle_view.party_members) != expected_party_size:
        raise AssertionError("Floor III Battle used the wrong party size")
    if battle_number == 10:
        participant_ids = tuple(
            member.target_id[len("drifter_") :]
            for member in battle_view.party_members
        )
        if participant_ids != state["m4b_roster_ids"]:
            raise AssertionError("Floor III boss did not use the full permanent roster")
        for drifter_id in ("zhaivra", "joruun"):
            member = game.member_for_drifter_id(drifter_id)
            if member.level_state.current != 1 or member.exp_state.current != 0:
                raise AssertionError("benched recruits received pre-boss Floor III XP")

    final_view = complete_battle(battle_view)
    game = _game(state)
    if session.active_battle is not None:
        raise AssertionError("completed Floor III Battle remained active")

    if battle_number == 10:
        if state["route_battle_factory"].floor_three_boss_pending_event_counts != (
            1,
            len(encounter.enemy_archetype_ids),
        ):
            raise AssertionError("Floor III boss reward evidence was not saved")
        if game.party_state.resolved_run_events:
            raise AssertionError("settled Floor III run retained event history")
        if final_view.screen is not OverworldScreen.HUB:
            raise AssertionError("Floor III boss did not settle at the Hub")
    else:
        event_key = "floor_three:%s:%s:encounter_rewards" % (
            state["m4b_floor_three_run_id"],
            node.node_id,
        )
        event = game.party_state.run_event(event_key)
        if event is None or event["kind"] != "encounter_rewards":
            raise AssertionError("Floor III encounter reward evidence was not saved")
        following = route.nodes[route.nodes.index(node) + 1]
        expected_screen = (
            OverworldScreen.REST
            if following.kind is RouteNodeKind.REST
            else OverworldScreen.MAIN
        )
        if final_view.screen is not expected_screen:
            raise AssertionError("Floor III Battle returned the wrong route screen")
        if game.overworld_state.current_route_node_id != following.node_id:
            raise AssertionError("Floor III did not advance to its route successor")

    del enemy_factory.enemies[enemy_start:]
    del enemy_factory.tiers[tier_start:]
    gc.collect()


def _assert_floor_three_clear(state):
    from app.game.party_state import DungeonPhase
    from app.presentation.overworld_models import OverworldScreen

    game = _game(state)
    party = game.party_state
    if party.phase is not DungeonPhase.HUB or not party.floor_three_cleared:
        raise AssertionError("Goblin Lord victory did not clear Floor III")
    if party.floor_three_run_id is not None:
        raise AssertionError("Floor III clear retained its run identity")
    if party.floor_three_runs_started_after_clear != 0:
        raise AssertionError("Floor III qualification started an unintended replay")
    if tuple(
        member.character.profile.drifter_id for member in game.recruited_members
    ) != state["m4b_roster_ids"]:
        raise AssertionError("Floor III clear changed the permanent roster")
    if party.active_drifter_ids != state["m4b_active_drifter_ids"]:
        raise AssertionError("Floor III clear changed the active pair")
    if not party.floor_two_cleared:
        raise AssertionError("Floor III clear lost Floor II progression")
    if game.overworld_state.current_route_node_id != "surface_dungeon_entrance":
        raise AssertionError("Floor III clear returned to the wrong Hub location")
    if not game.overworld_state.route_complete:
        raise AssertionError("Floor III clear changed Surface completion")
    if any(
        member.health.current != member.health.maximum
        or member.mana_resource.current != member.mana_resource.maximum
        for member in game.recruited_members
    ):
        raise AssertionError("Floor III Hub return did not restore the roster")
    if any(
        member.exp_state.current == 0 and member.level_state.current == 1
        for member in game.recruited_members
    ):
        raise AssertionError("Floor III boss XP did not reach every Drifter")
    if (
        state["route_battle_factory"].completed_count
        - state["m4b_completed_battle_start"]
        != 10
    ):
        raise AssertionError("Floor III probe did not complete ten battles")
    restored = game.clone()
    if restored.snapshot() != game.snapshot():
        raise AssertionError("Floor III clear changed on snapshot round-trip")
    if state["route_session"].current_view().screen is not OverworldScreen.HUB:
        raise AssertionError("Floor III clear did not present the Hub")
    del restored


def _release_probe_evidence(state):
    for key in (
        "m4b_floor_three_route",
        "m4b_active_drifter_ids",
        "m4b_recruitment_start_gold",
        "m4b_roster_ids",
        "m4b_floor_three_run_id",
        "m4b_completed_battle_start",
    ):
        del state[key]
    gc.collect()
    if any(key.startswith("m4b_") for key in state):
        raise AssertionError("Floor III probe retained temporary evidence")


def run(state, complete_battle, run_stage):
    run_stage(_M4B_STAGE_NAMES[0], lambda: _assert_tier_two_content(state))
    run_stage(
        _M4B_STAGE_NAMES[1], lambda: _recruit_drifter(state, "zhaivra")
    )
    run_stage(
        _M4B_STAGE_NAMES[2], lambda: _recruit_drifter(state, "joruun")
    )
    run_stage(_M4B_STAGE_NAMES[3], lambda: _start_floor_three(state))
    for battle_number in range(1, 6):
        run_stage(
            _M4B_STAGE_NAMES[battle_number + 3],
            lambda battle_number=battle_number: _complete_battle(
                state,
                complete_battle,
                battle_number,
            ),
        )
    run_stage(
        _M4B_STAGE_NAMES[9],
        lambda: _resolve_rest(
            state,
            "floor_three_midway_rest",
            "floor_three_battle_06",
        ),
    )
    for battle_number in range(6, 10):
        run_stage(
            _M4B_STAGE_NAMES[battle_number + 4],
            lambda battle_number=battle_number: _complete_battle(
                state,
                complete_battle,
                battle_number,
            ),
        )
    run_stage(
        _M4B_STAGE_NAMES[14],
        lambda: _resolve_rest(
            state,
            "floor_three_pre_boss_rest",
            "floor_three_battle_10",
        ),
    )
    run_stage(
        _M4B_STAGE_NAMES[15],
        lambda: _complete_battle(state, complete_battle, 10),
    )
    run_stage(_M4B_STAGE_NAMES[16], lambda: _assert_floor_three_clear(state))
    run_stage(_M4B_STAGE_NAMES[17], lambda: _release_probe_evidence(state))
