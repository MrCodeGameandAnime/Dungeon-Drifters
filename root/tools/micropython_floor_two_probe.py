"""Floor II runtime qualification on the completed Hub/Floor I probe state."""

import gc


_FLOOR_TWO_NODE_IDS = (
    "floor_two_battle_01",
    "floor_two_battle_02",
    "floor_two_battle_03",
    "floor_two_battle_04",
    "floor_two_battle_05",
    "floor_two_midway_rest",
    "floor_two_battle_06",
    "floor_two_battle_07",
    "floor_two_battle_08",
    "floor_two_battle_09",
    "floor_two_pre_boss_rest",
    "floor_two_battle_10",
)
_GRADE_TWO_ITEMS = (
    "grade_ii_metal",
    "grade_ii_fiber",
    "grade_ii_timber",
    "grade_ii_cores",
)
_DISCOVERY_SOURCE_ID = "ancient_well_floor2_01"
_M4_STAGE_NAMES = (
    "M4_TIER_ONE_CONTENT",
    "M4_FLOOR_TWO_START",
    "M4_FLOOR_TWO_BATTLE_01",
    "M4_FLOOR_TWO_BATTLE_02",
    "M4_FLOOR_TWO_BATTLE_03",
    "M4_FLOOR_TWO_BATTLE_04",
    "M4_FLOOR_TWO_BATTLE_05",
    "M4_D3_RECRUITMENT",
    "M4_FLOOR_TWO_BATTLE_06",
    "M4_FLOOR_TWO_BATTLE_07",
    "M4_FLOOR_TWO_BATTLE_08",
    "M4_FLOOR_TWO_BATTLE_09",
    "M4_DISCOVERY_SEARCH_ROUNDTRIP",
    "M4_FLOOR_TWO_BATTLE_10_BOSS",
    "M4_FLOOR_TWO_FINAL_STATE",
    "M4_PROBE_TEARDOWN",
)


def _game(state):
    game = state["route_session"].game_state
    state["route_game"] = game
    return game


def _assert_tier_one_content(state):
    from app.content.catalog import get_enemy_spec, get_encounter_spec, get_route_spec

    route = get_route_spec("floor_two")
    if tuple(node.node_id for node in route.nodes) != _FLOOR_TWO_NODE_IDS:
        raise AssertionError("Floor II authored route node sequence changed")

    drop_families = {}
    for node in route.nodes:
        if node.encounter_id is None:
            continue
        encounter = get_encounter_spec(node.encounter_id)
        for archetype_id in encounter.enemy_archetype_ids:
            enemy = get_enemy_spec(archetype_id)
            if 1 not in enemy.supported_tiers:
                raise AssertionError("Floor II encounter lacks Tier I enemy data")
            profile = None
            for candidate in enemy.tier_profiles:
                if candidate.tier == 1:
                    profile = candidate
                    break
            if profile is None:
                raise AssertionError("Tier I enemy profile was not authored")
            for drop in profile.item_drops:
                if drop.item_id in _GRADE_TWO_ITEMS:
                    drop_families[drop.item_id] = True
    if any(item_id not in drop_families for item_id in _GRADE_TWO_ITEMS):
        raise AssertionError("Floor II Tier I profiles omit a Grade II family")
    state["m4_floor_two_route"] = route


def _start_floor_two(state):
    from app.game.party_state import DungeonPhase
    from app.presentation.battle_models import BattleView
    from app.presentation.overworld_models import OverworldAction, OverworldScreen
    from app.ui.overworld_ui import ChooseOverworldAction

    session = state["route_session"]
    game = _game(state)
    party = game.party_state
    if party.phase is not DungeonPhase.HUB or not party.floor_one_cleared:
        raise AssertionError("Floor II probe did not start from a cleared Hub")
    if party.shared_gold < 65:
        party.add_shared_gold(65 - party.shared_gold)
    active_ids = party.active_drifter_ids
    view = session.current_view()
    if view.screen is not OverworldScreen.HUB:
        raise AssertionError("Floor II probe did not start on the Hub screen")
    enemy_factory = state["route_enemy_factory"]
    enemy_start = len(enemy_factory.enemies)
    tier_start = len(enemy_factory.tiers)
    view = session.submit(
        ChooseOverworldAction(OverworldAction.START_FLOOR_TWO)
    )
    game = _game(state)
    if not isinstance(view, BattleView) or session.active_battle is None:
        raise AssertionError("Floor II did not immediately enter its first Battle")
    if game.overworld_state.active_route_id != "floor_two":
        raise AssertionError("Floor II route was not selected")
    if game.party_state.floor_two_run_id is None:
        raise AssertionError("Floor II run identity was not created")
    if game.party_state.active_drifter_ids != active_ids:
        raise AssertionError("starting Floor II changed the active pair")
    first_node = state["m4_floor_two_route"].nodes[0]
    first_encounter = state["catalog"].get_encounter_spec(first_node.encounter_id)
    if tuple(enemy_factory.tiers[tier_start:]) != (1,) * len(
        first_encounter.enemy_archetype_ids
    ):
        raise AssertionError("Floor II start did not construct Tier I enemies")
    state["m4_active_drifter_ids"] = active_ids
    state["m4_floor_two_run_id"] = game.party_state.floor_two_run_id
    state["floor_two_battle_view"] = view
    state["m4_first_enemy_start"] = enemy_start
    state["m4_first_tier_start"] = tier_start


def _assert_encounter_event(state, node, enemy_count):
    from app.game.run_events import RunEventService

    game = _game(state)
    run_id = state["m4_floor_two_run_id"]
    event_key = "floor_two:%s:%s:encounter_rewards" % (run_id, node.node_id)
    event = game.party_state.run_event(event_key)
    if event is None or event["kind"] != "encounter_rewards":
        raise AssertionError("Floor II encounter reward event was not persisted")
    drop_keys = event["result"]["drop_event_keys"]
    if len(drop_keys) != enemy_count:
        raise AssertionError("Floor II encounter omitted per-enemy drop evidence")
    for drop_key in drop_keys:
        drop_event = game.party_state.run_event(drop_key)
        if drop_event is None or drop_event["kind"] != "enemy_drop":
            raise AssertionError("Floor II enemy drop evidence was not persisted")

    if node.node_id != "floor_two_battle_01":
        return

    snapshot = game.snapshot()
    restored = game.clone()
    if restored.snapshot() != snapshot:
        raise AssertionError("Floor II drop evidence changed on snapshot round-trip")
    encounter = state["m4_floor_two_route"].nodes[0]
    from app.content.catalog import get_encounter_item_drop_tables, get_encounter_rewards

    experience, gold = get_encounter_rewards(encounter.encounter_id)

    class CountingRng:
        def __init__(self):
            self.calls = 0

        def randint(self, start, _end):
            self.calls += 1
            return start

    rng = CountingRng()
    before_rewards = restored.party_state.outing_rewards.snapshot()
    result = RunEventService(
        save_port=state["route_battle_factory"],
        rng=rng,
    ).resolve_encounter_rewards(
        restored,
        node_id=node.node_id,
        experience=experience,
        gold=gold,
        enemy_drop_tables=get_encounter_item_drop_tables(
            encounter.encounter_id,
            tier=1,
        ),
    )
    if result.status.value != "already_resolved" or rng.calls:
        raise AssertionError("Floor II drop replay rerolled an accepted event")
    if restored.party_state.outing_rewards.snapshot() != before_rewards:
        raise AssertionError("Floor II drop replay duplicated unsecured rewards")
    del snapshot
    del restored


def _complete_battle(state, complete_battle, battle_number):
    from app.content.route_spec import RouteNodeKind
    from app.presentation.overworld_models import OverworldAction, OverworldScreen
    from app.ui.overworld_ui import ChooseOverworldAction

    session = state["route_session"]
    game = _game(state)
    route = state["m4_floor_two_route"]
    battle_nodes = tuple(
        candidate
        for candidate in route.nodes
        if candidate.kind in {RouteNodeKind.COMBAT, RouteNodeKind.BOSS}
    )
    node = battle_nodes[battle_number - 1]
    if node.node_id != "floor_two_battle_%02d" % battle_number:
        raise AssertionError("Floor II battle index did not match authored route")
    encounter = state["catalog"].get_encounter_spec(node.encounter_id)
    composition = tuple(encounter.enemy_archetype_ids)
    enemy_factory = state["route_enemy_factory"]
    if battle_number == 1:
        enemy_start = state.pop("m4_first_enemy_start")
        tier_start = state.pop("m4_first_tier_start")
        battle_view = state.pop("floor_two_battle_view")
    else:
        enemy_start = len(enemy_factory.enemies)
        tier_start = len(enemy_factory.tiers)
        view = session.current_view()
        if view.screen is not OverworldScreen.MAIN:
            raise AssertionError("Floor II encounter did not present the MAIN screen")
        if game.overworld_state.current_route_node_id != node.node_id:
            raise AssertionError("Floor II encounter cursor changed")
        battle_view = session.submit(
            ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER)
        )
    active = session.active_battle
    if active is None or tuple(enemy.archetype_id for enemy in active.enemies) != composition:
        raise AssertionError("Floor II Battle composition differed from authored data")
    if tuple(enemy_factory.tiers[tier_start:]) != (1,) * len(composition):
        raise AssertionError("Floor II Battle did not construct Tier I enemies")
    if len(battle_view.party_members) != 2:
        raise AssertionError("Floor II Battle changed the deployed pair")

    final_view = complete_battle(battle_view)
    game = _game(state)
    if session.active_battle is not None:
        raise AssertionError("completed Floor II Battle remained active")

    if battle_number == 10:
        if state["route_battle_factory"].floor_two_boss_pending_event_counts != (
            1,
            len(composition),
        ):
            raise AssertionError(
                "Floor II boss event evidence was not saved before settlement"
            )
        if game.party_state.resolved_run_events:
            raise AssertionError("settled Floor II run retained event history")
        if final_view.screen is not OverworldScreen.HUB:
            raise AssertionError("Floor II boss did not settle at the Hub")
    else:
        _assert_encounter_event(state, node, len(composition))
        route_node_index = route.nodes.index(node)
        following = route.nodes[route_node_index + 1]
        expected_screen = (
            OverworldScreen.REST
            if following.kind.value == "rest"
            else OverworldScreen.MAIN
        )
        if final_view.screen is not expected_screen:
            raise AssertionError("Floor II Battle returned the wrong route screen")
        if game.overworld_state.current_route_node_id != following.node_id:
            raise AssertionError("Floor II did not advance to its next authored node")

    del enemy_factory.enemies[enemy_start:]
    del enemy_factory.tiers[tier_start:]
    gc.collect()


def _has_bonus_at_least(member, bonus_id, minimum):
    bonuses = member.permanent_discovery_bonuses
    return bonus_id in bonuses and bonuses[bonus_id] >= minimum


def _recruit_d3_at_midway_rest(state):
    from app.presentation.overworld_models import OverworldAction, OverworldScreen
    from app.ui.overworld_ui import ChooseCompanion, ChooseOverworldAction

    session = state["route_session"]
    game = _game(state)
    active_ids = state["m4_active_drifter_ids"]
    view = session.current_view()
    if view.screen is not OverworldScreen.REST:
        raise AssertionError("Floor II midway node did not present Rest")
    if game.overworld_state.current_route_node_id != "floor_two_midway_rest":
        raise AssertionError("Floor II recruitment was offered at the wrong node")
    view = session.submit(
        ChooseOverworldAction(OverworldAction.RECRUIT_COMPANION)
    )
    if view.screen is not OverworldScreen.COMPANION_SELECTION:
        raise AssertionError("Floor II recruitment did not open D3 selection")
    view = session.submit(
        ChooseCompanion("zhaivra", event_id="floor_two_d3_recruitment")
    )
    game = _game(state)
    if view.screen is not OverworldScreen.REST:
        raise AssertionError("Floor II recruitment did not return to Rest")
    if game.party_state.active_drifter_ids != active_ids:
        raise AssertionError("D3 recruitment changed the locked active pair")
    if "zhaivra" not in tuple(
        member.character.profile.drifter_id for member in game.recruited_members
    ):
        raise AssertionError("Zhaivra was not added to the recruited roster")
    if "floor_two_d3_recruitment" not in game.story_state.completed_events:
        raise AssertionError("D3 recruitment event was not durably recorded")
    view = session.submit(ChooseOverworldAction(OverworldAction.REST))
    if view.screen is not OverworldScreen.REST:
        raise AssertionError("midway recovery unexpectedly advanced the route")
    view = session.submit(ChooseOverworldAction(OverworldAction.SKIP_REST))
    game = _game(state)
    if view.screen is not OverworldScreen.MAIN:
        raise AssertionError("Midway Rest did not resume Floor II")
    if game.overworld_state.current_route_node_id != "floor_two_battle_06":
        raise AssertionError("Midway Rest advanced to the wrong encounter")


def _search_and_roundtrip(state):
    from app.content.catalog import get_permanent_discovery_source
    from app.game.run_events import RunEventService
    from app.presentation.overworld_models import OverworldAction, OverworldScreen
    from app.ui.overworld_ui import (
        ChooseDiscoverySearcher,
        ChooseDiscoveryTarget,
        ChooseOverworldAction,
    )

    session = state["route_session"]
    game = _game(state)
    if game.overworld_state.current_route_node_id != "floor_two_pre_boss_rest":
        raise AssertionError("Floor II discovery search was offered at the wrong node")
    view = session.current_view()
    if view.screen is not OverworldScreen.REST:
        raise AssertionError("Floor II pre-boss node did not present Rest")
    view = session.submit(ChooseOverworldAction(OverworldAction.SEARCH_SITE))
    if view.screen is not OverworldScreen.DISCOVERY_SEARCHERS:
        raise AssertionError("Floor II search did not ask for an active searcher")
    view = session.submit(ChooseDiscoverySearcher("branoc"))
    if view.screen is not OverworldScreen.DISCOVERY_TARGETS:
        raise AssertionError("deterministic Floor II search did not reveal the source")
    view = session.submit(ChooseDiscoveryTarget("azhvielle"))
    if view.screen is not OverworldScreen.DISCOVERY_CONFIRMATION:
        raise AssertionError("Floor II source did not ask for claim confirmation")
    view = session.submit(ChooseOverworldAction(OverworldAction.CONFIRM))
    if view.screen is not OverworldScreen.REST:
        raise AssertionError("discovery claim did not return to the Rest")

    game = _game(state)
    if _DISCOVERY_SOURCE_ID not in game.world_state.permanent_discovery_claims:
        raise AssertionError("Floor II discovery claim was not persisted")
    if not _has_bonus_at_least(
        game.member_for_drifter_id("azhvielle"), "max_hp", 5
    ):
        raise AssertionError("Floor II discovery reward missed its selected target")

    snapshot = game.snapshot()
    restored = game.clone()
    if restored.snapshot() != snapshot:
        raise AssertionError("Floor II search/claim changed on snapshot round-trip")
    event_key = "floor_two:%s:floor_two_pre_boss_rest:discovery_search" % (
        state["m4_floor_two_run_id"],
    )
    search_event = restored.party_state.run_event(event_key)
    if search_event is None or not search_event["result"]["found"]:
        raise AssertionError("Floor II search result was missing after round-trip")

    class CountingRng:
        def __init__(self):
            self.calls = 0

        def randint(self, start, _end):
            self.calls += 1
            return start

    rng = CountingRng()
    result = RunEventService(
        save_port=state["route_battle_factory"],
        rng=rng,
    ).search_discovery(
        restored,
        node_id="floor_two_pre_boss_rest",
        searcher_drifter_id="branoc",
        source=get_permanent_discovery_source(_DISCOVERY_SOURCE_ID),
    )
    if result.status.value != "already_resolved" or rng.calls:
        raise AssertionError("Floor II search reload rerolled its saved outcome")
    view = session.submit(ChooseOverworldAction(OverworldAction.REST))
    if view.screen is not OverworldScreen.REST:
        raise AssertionError("pre-boss recovery unexpectedly advanced the route")
    view = session.submit(ChooseOverworldAction(OverworldAction.SKIP_REST))
    game = _game(state)
    if view.screen is not OverworldScreen.MAIN:
        raise AssertionError("Pre-boss Rest did not resume Floor II")
    if game.overworld_state.current_route_node_id != "floor_two_battle_10":
        raise AssertionError("Pre-boss Rest advanced to the wrong encounter")
    del snapshot
    del restored


def _assert_floor_two_clear(state):
    from app.game.party_state import DungeonPhase
    from app.presentation.overworld_models import OverworldScreen

    game = _game(state)
    party = game.party_state
    if party.phase is not DungeonPhase.HUB or not party.floor_two_cleared:
        raise AssertionError("Goblin Lord victory did not clear Floor II")
    if party.floor_two_run_id is not None:
        raise AssertionError("Floor II clear retained its run identity")
    if party.active_drifter_ids != state["m4_active_drifter_ids"]:
        raise AssertionError("Floor II clear changed the active pair")
    if not set(_GRADE_TWO_ITEMS).issubset(set(party.shared_items)):
        raise AssertionError("Floor II clear did not secure every Grade II family")
    if _DISCOVERY_SOURCE_ID not in game.world_state.permanent_discovery_claims:
        raise AssertionError("Floor II clear lost the claimed discovery")
    if game.overworld_state.active_route_id != "surface":
        raise AssertionError("Floor II clear did not return to the Surface")
    if game.overworld_state.current_route_node_id != "surface_dungeon_entrance":
        raise AssertionError("Floor II clear returned to the wrong Hub location")
    if not game.overworld_state.route_complete:
        raise AssertionError("Floor II clear changed Surface completion")
    if state["route_session"].current_view().screen is not OverworldScreen.HUB:
        raise AssertionError("Floor II clear did not present the Hub")
    restored = game.clone()
    if restored.snapshot() != game.snapshot():
        raise AssertionError("Floor II clear state changed on snapshot round-trip")
    del restored


def _release_probe_evidence(state):
    for key in (
        "m4_floor_two_route",
        "m4_active_drifter_ids",
        "m4_floor_two_run_id",
    ):
        del state[key]
    gc.collect()
    if any(key.startswith("m4_") for key in state):
        raise AssertionError("Floor II probe retained temporary evidence")


def run(state, complete_battle, run_stage):
    run_stage(_M4_STAGE_NAMES[0], lambda: _assert_tier_one_content(state))
    run_stage(_M4_STAGE_NAMES[1], lambda: _start_floor_two(state))
    for battle_number in range(1, 6):
        run_stage(
            _M4_STAGE_NAMES[battle_number + 1],
            lambda battle_number=battle_number: _complete_battle(
                state,
                complete_battle,
                battle_number,
            ),
        )
    run_stage(_M4_STAGE_NAMES[7], lambda: _recruit_d3_at_midway_rest(state))
    for battle_number in range(6, 10):
        run_stage(
            _M4_STAGE_NAMES[battle_number + 2],
            lambda battle_number=battle_number: _complete_battle(
                state,
                complete_battle,
                battle_number,
            ),
        )
    run_stage(_M4_STAGE_NAMES[12], lambda: _search_and_roundtrip(state))
    run_stage(
        _M4_STAGE_NAMES[13],
        lambda: _complete_battle(state, complete_battle, 10),
    )
    run_stage(_M4_STAGE_NAMES[14], lambda: _assert_floor_two_clear(state))
    run_stage(_M4_STAGE_NAMES[15], lambda: _release_probe_evidence(state))
