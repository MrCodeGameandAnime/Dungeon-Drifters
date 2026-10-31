import json
import sys

from app.combat.battle import Battle
from app.combat.result import MoveResult
from app.content.catalog import create_enemy_state
from app.game.new_game import create_new_game
from app.game.overworld_session import OverworldSession
from app.game.party_state import DungeonPhase
from app.presentation.battle_models import InteractionPhase
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.persistence.ports import SaveLoadResult
from app.persistence.save_port_contract import SaveLoadStatus
from app.player.progression import xp_required_for_next_level
from app.ui.battle_ui import ChooseAction, ChooseMove, ChooseTarget
from app.ui.overworld_ui import ChooseCompanion, ChooseOverworldAction


PYODIDE_VERSION = "314.0.7"
EXPECTED_ENCOUNTERS = (
    "surface_goblin_solo",
    "surface_goblin_pair",
    "surface_warrior_solo",
    "surface_warrior_pair",
    "surface_shaman_solo",
    "surface_shaman_pair",
    "surface_elite_patrol",
    "surface_goblin_lord",
)
EXPECTED_RESTS = (
    "surface_rest_after_warrior_solo",
    "surface_rest_after_shaman_pair",
    "surface_rest_before_goblin_lord",
)
EXPECTED_ROUTE = (
    "surface_goblin_solo",
    "surface_goblin_pair",
    "surface_warrior_solo",
    "surface_rest_after_warrior_solo",
    "surface_warrior_pair",
    "surface_shaman_solo",
    "surface_shaman_pair",
    "surface_rest_after_shaman_pair",
    "surface_elite_patrol",
    "surface_rest_before_goblin_lord",
    "surface_goblin_lord",
    "surface_dungeon_entrance",
)
EXPECTED_COMPOSITIONS = (
    ("goblin",),
    ("goblin", "goblin"),
    ("goblin_warrior",),
    ("goblin_warrior", "goblin_warrior"),
    ("goblin_shaman",),
    ("goblin_shaman", "goblin_shaman"),
    ("goblin_elite", "goblin"),
    ("goblin_lord", "goblin", "goblin_warrior"),
)
EXPECTED_ENCOUNTER_COUNT = 8
EXPECTED_REST_COUNT = 3
EXPECTED_BATTLE_COUNT = 8
EXPECTED_ENEMY_COUNT = 14
MAX_BATTLE_INPUTS = 100


class DeterministicRng:
    def randint(self, start, _end):
        return start

    def choice(self, options):
        return tuple(options)[0]


class DeterministicResolver:
    def resolve_move(
        self,
        actor,
        target,
        move_name,
        *,
        combat_state=None,
        character_run_state=None,
    ):
        del actor, combat_state, character_run_state
        damage = 0
        if hasattr(target, "archetype_id") and target.is_alive():
            damage = target.health.current
            target.health.take_damage(damage)
        return MoveResult(
            accepted=True,
            hit=True,
            move_name=move_name,
            resource_spent=0,
            damage=damage,
            healing=0,
            statuses_applied=(),
            reason=None,
        )


class HeadlessBattleFactory:
    def __init__(self):
        self.battles = []

    def __call__(
        self,
        player_state,
        enemies,
        *,
        ui,
        encounter_label,
        party=(),
        party_state=None,
        smoke_escape_allowed=False,
    ):
        if ui is not None:
            raise AssertionError("route battle must be headless")
        battle = Battle(
            player_state,
            enemies,
            ui=None,
            resolver=DeterministicResolver(),
            rng=DeterministicRng(),
            encounter_label=encounter_label,
            party=party,
            party_state=party_state,
            smoke_escape_allowed=smoke_escape_allowed,
        )
        self.battles.append(battle)
        return battle


class HeadlessEnemyFactory:
    def __init__(self):
        self.enemies = []

    def __call__(self, archetype_id, *, tier):
        enemy = create_enemy_state(archetype_id, tier=tier)
        self.enemies.append(enemy)
        return enemy


class QualificationSavePort:
    def __init__(self):
        self.saved_states = []

    def inspect(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def save(self, game_state):
        self.saved_states.append(game_state)
        return SaveLoadResult(SaveLoadStatus.SAVED)

    def load(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)


def _first_enabled(options, label):
    for option in options:
        if option.enabled:
            return option
    raise AssertionError("no enabled " + label + " option")


def _complete_battle(session, first_view):
    view = first_view
    inputs = 0
    while view.interaction_phase is not InteractionPhase.COMPLETE:
        inputs += 1
        if inputs > MAX_BATTLE_INPUTS:
            raise AssertionError("battle exceeded semantic input limit")
        if view.interaction_phase is InteractionPhase.ACTIONS:
            option = _first_enabled(view.action_options, "action")
            view = session.submit(ChooseAction(option.intent))
        elif view.interaction_phase is InteractionPhase.REGULAR_MOVES:
            option = _first_enabled(view.move_options, "move")
            view = session.submit(ChooseMove(option.selection_key))
        elif view.interaction_phase is InteractionPhase.TARGETS:
            option = _first_enabled(view.target_options, "target")
            view = session.submit(ChooseTarget(option.target_id))
        else:
            raise AssertionError("unexpected battle phase: " + str(view.interaction_phase))
    return session.current_view()


def _assert_prefix(actual, expected):
    if tuple(actual) != tuple(expected[: len(actual)]):
        raise AssertionError("route prefix mismatch")


def _assert_live_route_state(game, session, encounter_ids, rest_ids):
    if game.world_state.defeated_encounters != tuple(encounter_ids):
        raise AssertionError("defeated encounter prefix mismatch")
    if game.overworld_state.resolved_rest_node_ids != tuple(rest_ids):
        raise AssertionError("resolved Rest prefix mismatch")
    if session.active_battle is not None:
        raise AssertionError("active battle remained after route advancement")


def _total_experience(player_state):
    thresholds = (
        xp_required_for_next_level(level)
        for level in range(1, player_state.level_state.current)
    )
    return sum(thresholds) + player_state.exp_state.current


def _qualify_route():
    game = create_new_game("branoc")
    battle_factory = HeadlessBattleFactory()
    enemy_factory = HeadlessEnemyFactory()
    save_port = QualificationSavePort()
    session = OverworldSession(
        game,
        ui=None,
        battle_factory=battle_factory,
        enemy_factory=enemy_factory,
        battle_ui_factory=None,
        save_port=save_port,
    )

    route_trace = []
    encounter_ids = []
    rest_ids = []
    view = session.current_view()
    while not game.overworld_state.route_complete:
        node_id = game.overworld_state.current_route_node_id
        if not route_trace or route_trace[-1] != node_id:
            route_trace.append(node_id)

        if view.screen is OverworldScreen.REST:
            expected_rest = EXPECTED_RESTS[len(rest_ids)]
            if node_id != expected_rest:
                raise AssertionError("unexpected Rest node")
            view = session.submit(ChooseOverworldAction(OverworldAction.REST))
            if view.screen is not OverworldScreen.MAIN:
                raise AssertionError("Rest did not return to MAIN")
            rest_ids.append(node_id)
            _assert_prefix(rest_ids, EXPECTED_RESTS)
            _assert_live_route_state(game, session, encounter_ids, rest_ids)
            continue

        if view.screen is not OverworldScreen.MAIN:
            raise AssertionError("route view is not MAIN")
        route_option = view.contextual_route_option
        if route_option is None:
            raise AssertionError("route option is missing")
        if route_option.action is OverworldAction.ENTER_ENCOUNTER:
            expected_encounter = EXPECTED_ENCOUNTERS[len(encounter_ids)]
            if node_id != expected_encounter:
                raise AssertionError("unexpected encounter node")
            encounter_ids.append(node_id)
            battle_view = session.submit(ChooseOverworldAction(route_option.action))
            view = _complete_battle(session, battle_view)
            _assert_prefix(encounter_ids, EXPECTED_ENCOUNTERS)
            _assert_live_route_state(game, session, encounter_ids, rest_ids)
            continue

        if route_option.action is OverworldAction.REST:
            expected_rest = EXPECTED_RESTS[len(rest_ids)]
            if node_id != expected_rest:
                raise AssertionError("unexpected Rest transition")
            rest_view = session.submit(ChooseOverworldAction(OverworldAction.REST))
            if rest_view.screen is not OverworldScreen.REST:
                raise AssertionError("Rest transition did not open REST")
            view = session.submit(ChooseOverworldAction(OverworldAction.REST))
            if view.screen is not OverworldScreen.MAIN:
                raise AssertionError("Rest resolution did not return to MAIN")
            rest_ids.append(node_id)
            _assert_prefix(rest_ids, EXPECTED_RESTS)
            _assert_live_route_state(game, session, encounter_ids, rest_ids)
            continue

        raise AssertionError("unexpected route action: " + str(route_option.action))

    route_trace.append(game.overworld_state.current_route_node_id)
    if tuple(route_trace) != EXPECTED_ROUTE:
        raise AssertionError("full route sequence mismatch")
    if tuple(encounter_ids) != EXPECTED_ENCOUNTERS:
        raise AssertionError("encounter sequence mismatch")
    if tuple(rest_ids) != EXPECTED_RESTS:
        raise AssertionError("Rest sequence mismatch")
    if len(battle_factory.battles) != EXPECTED_BATTLE_COUNT:
        raise AssertionError("unexpected Battle count")
    if len(enemy_factory.enemies) != EXPECTED_ENEMY_COUNT:
        raise AssertionError("unexpected EnemyState count")
    compositions = tuple(
        tuple(enemy.archetype_id for enemy in battle.enemies)
        for battle in battle_factory.battles
    )
    if compositions != EXPECTED_COMPOSITIONS:
        raise AssertionError("battle compositions mismatch")
    for index, enemy in enumerate(enemy_factory.enemies):
        for previous in enemy_factory.enemies[:index]:
            if enemy is previous:
                raise AssertionError("route reused an EnemyState instance")
    if not all(
        battle.interaction_phase is InteractionPhase.COMPLETE
        for battle in battle_factory.battles
    ):
        raise AssertionError("not all route Battles completed")

    final_view = session.current_view()
    if final_view.screen is not OverworldScreen.HUB:
        raise AssertionError("final route screen is not HUB")
    if final_view.shared_gold != 75:
        raise AssertionError("surface gold was not transferred to the hub")
    surface_gold = final_view.shared_gold
    if not any(
        option.action is OverworldAction.RECRUIT_COMPANION
        for option in final_view.options
    ):
        raise AssertionError("Hub did not offer companion recruitment")
    if game.overworld_state.current_route_node_id != "surface_dungeon_entrance":
        raise AssertionError("Dungeon Entrance was not reached")
    if not game.overworld_state.route_complete:
        raise AssertionError("route did not complete")
    if not game.overworld_state.dungeon_entrance_reached:
        raise AssertionError("Dungeon Entrance flag was not set")
    if game.player_state.level_state.current != 9:
        raise AssertionError("unexpected final level")
    if game.player_state.exp_state.current != 68:
        raise AssertionError("unexpected final EXP")
    if game.player_state.growth_points != 24:
        raise AssertionError("unexpected final Growth Points")
    surface_level = game.player_state.level_state.current
    surface_exp = game.player_state.exp_state.current
    surface_growth_points = game.player_state.growth_points
    if game.player_state.gold != 0:
        raise AssertionError("surface gold remained on the lead instead of the shared balance")
    if session._save_port is not save_port:
        raise AssertionError("route replaced the qualification save port")

    recruit_view = session.submit(
        ChooseOverworldAction(OverworldAction.RECRUIT_COMPANION)
    )
    if recruit_view.screen is not OverworldScreen.COMPANION_SELECTION:
        raise AssertionError("Hub recruitment did not open companion selection")
    companion_id = recruit_view.companion_choices[0].drifter_id
    lead_total_before = _total_experience(game.player_state)
    companion_view = session.submit(
        ChooseCompanion(companion_id, "floor_one_d2_recruitment")
    )
    if companion_view.screen is not OverworldScreen.PARTY_READY:
        raise AssertionError("companion choice did not reach Party Ready")
    if companion_view.shared_gold != 10:
        raise AssertionError("companion recruitment did not charge exactly 65 gold")
    companion = game.party_state.companions[0]
    companion_total_before = _total_experience(companion)

    tutorial_view = session.submit(ChooseOverworldAction(OverworldAction.READY))
    if tutorial_view.interaction_phase is not InteractionPhase.ACTIONS:
        raise AssertionError("Ready did not start the tutorial Battle")
    if len(tutorial_view.enemies) != 3:
        raise AssertionError("tutorial Battle did not contain exactly three Goblins")
    if len(tutorial_view.party_members) != 2:
        raise AssertionError("tutorial Battle did not contain both Drifters")
    if len(session.active_battle.enemies) != 3:
        raise AssertionError("active tutorial Battle composition changed")
    tutorial_view = _complete_battle(session, tutorial_view)
    if tutorial_view.screen is not OverworldScreen.EXTRACTION:
        raise AssertionError("tutorial victory did not stop at Extraction")
    if tutorial_view.outing_rewards.experience != 120:
        raise AssertionError("tutorial EXP was not left pending at Extraction")
    if tutorial_view.outing_rewards.gold != 9:
        raise AssertionError("tutorial gold was not left pending at Extraction")

    hub_view = session.submit(
        ChooseOverworldAction(OverworldAction.RETURN_TO_HUB)
    )
    if hub_view.screen is not OverworldScreen.HUB:
        raise AssertionError("explicit extraction did not return to the Hub")
    lead_tutorial_exp = _total_experience(game.player_state) - lead_total_before
    companion_tutorial_exp = _total_experience(companion) - companion_total_before
    if lead_tutorial_exp != 60 or companion_tutorial_exp != 60:
        raise AssertionError("tutorial EXP was not split evenly between the Drifters")
    if hub_view.shared_gold != 19:
        raise AssertionError("tutorial gold was not secured in shared inventory")
    if any(
        option.action in {OverworldAction.RECRUIT_COMPANION, OverworldAction.READY}
        for option in hub_view.options
    ):
        raise AssertionError("Hub offered another outing after the first extraction")
    if session.active_battle is not None:
        raise AssertionError("active Battle remained after the first extraction")

    floor_one_compositions = (
        ("goblin", "goblin", "goblin", "goblin"),
        ("goblin", "goblin", "goblin"),
        ("goblin", "goblin"),
        ("goblin",),
        ("goblin", "goblin", "goblin", "goblin"),
        ("goblin", "goblin"),
        ("goblin", "goblin", "goblin"),
        ("goblin", "goblin", "goblin", "goblin"),
        ("goblin", "goblin", "goblin"),
        ("goblin_lord", "goblin", "goblin_warrior"),
    )
    floor_one_battle_start = len(battle_factory.battles)
    party_members = (game.player_state, companion)
    floor_one_xp_before = tuple(_total_experience(member) for member in party_members)
    floor_one_world_history = game.world_state.defeated_encounters
    warning = session.submit(
        ChooseOverworldAction(OverworldAction.START_FLOOR_ONE)
    )
    if warning.screen is not OverworldScreen.FLOOR_ONE_WARNING:
        raise AssertionError("Floor 1 did not show its danger warning")
    battle_view = session.submit(ChooseOverworldAction(OverworldAction.SET_OUT))

    for battle_index, expected_composition in enumerate(floor_one_compositions):
        if battle_index:
            if battle_view.screen is OverworldScreen.REST:
                if battle_index == 5:
                    for member in party_members:
                        member.health.take_damage(1)
                        member.mana_resource.spend(1)
                    battle_view = session.submit(
                        ChooseOverworldAction(OverworldAction.REST)
                    )
                    if battle_view.screen is not OverworldScreen.REST:
                        raise AssertionError(
                            "Floor 1 recovery must leave the party at Rest"
                        )
                    if game.overworld_state.current_route_node_id != "floor_one_midway_rest":
                        raise AssertionError(
                            "Floor 1 recovery advanced before the player chose"
                        )
                    if "floor_one_midway_rest" in game.overworld_state.resolved_rest_node_ids:
                        raise AssertionError(
                            "Floor 1 recovery resolved the Rest prematurely"
                        )
                    if not any(
                        option.action is OverworldAction.EXTRACT and option.enabled
                        for option in battle_view.options
                    ):
                        raise AssertionError(
                            "Extract must remain available after Floor 1 recovery"
                        )
                    if any(
                        member.health.current != member.health.maximum
                        or member.mana_resource.current != member.mana_resource.maximum
                        for member in party_members
                    ):
                        raise AssertionError("midway Rest did not restore both Drifters")
                    battle_view = session.submit(
                        ChooseOverworldAction(OverworldAction.SKIP_REST)
                    )
                elif battle_index == 9:
                    for member in party_members:
                        member.health.take_damage(1)
                        member.mana_resource.spend(1)
                    before_skip = tuple(
                        (member.health.current, member.mana_resource.current)
                        for member in party_members
                    )
                    battle_view = session.submit(
                        ChooseOverworldAction(OverworldAction.SKIP_REST)
                    )
                    if tuple(
                        (member.health.current, member.mana_resource.current)
                        for member in party_members
                    ) != before_skip:
                        raise AssertionError("skipping the pre-boss Rest healed the party")
                else:
                    raise AssertionError("Floor 1 opened a Rest at the wrong battle")
            if battle_view.screen is not OverworldScreen.MAIN:
                raise AssertionError("Floor 1 did not return to the route after Rest")
            battle_view = session.submit(
                ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER)
            )

        if battle_view.interaction_phase is not InteractionPhase.ACTIONS:
            raise AssertionError("Floor 1 did not enter a Battle")
        if len(battle_view.party_members) != 2:
            raise AssertionError("Floor 1 Battle did not include both Drifters")
        actual_composition = tuple(
            enemy.archetype_id for enemy in session.active_battle.enemies
        )
        if actual_composition != expected_composition:
            raise AssertionError("Floor 1 Goblin composition changed")
        battle_view = _complete_battle(session, battle_view)
        if battle_index in (4, 8):
            if battle_view.screen is not OverworldScreen.REST:
                raise AssertionError("Floor 1 did not stop at an authored Rest")
        elif battle_index < 9 and battle_view.screen is not OverworldScreen.MAIN:
            raise AssertionError("Floor 1 route advanced to the wrong screen")

    floor_one_hub = battle_view
    if floor_one_hub.screen is not OverworldScreen.HUB:
        raise AssertionError("Goblin Lord victory did not return to the Hub")
    if not game.party_state.floor_one_cleared:
        raise AssertionError("Goblin Lord victory did not clear Floor 1")
    if game.party_state.shared_gold != 115:
        raise AssertionError("Floor 1 rewards did not secure 96 gold")
    floor_one_xp_each = tuple(
        _total_experience(member) - before
        for member, before in zip(party_members, floor_one_xp_before)
    )
    if floor_one_xp_each != (670, 670):
        raise AssertionError("Floor 1 did not split 1340 EXP evenly")
    if game.world_state.defeated_encounters != floor_one_world_history:
        raise AssertionError("Floor 1 polluted Surface encounter history")
    if len(battle_factory.battles) - floor_one_battle_start != 10:
        raise AssertionError("Floor 1 did not complete exactly ten Battles")
    if len(save_port.saved_states) != 3:
        raise AssertionError("Floor 1 did not persist both Rest fallbacks and its Hub outcome")
    for fallback in save_port.saved_states[:2]:
        if fallback is game:
            raise AssertionError("Rest fallback aliased the live run")
        if fallback.party_state.phase is not DungeonPhase.HUB:
            raise AssertionError("Rest fallback did not forfeit the active run")
        if fallback.overworld_state.current_route_node_id != "surface_dungeon_entrance":
            raise AssertionError("Rest fallback did not return to the Surface entrance")
        if fallback.party_state.outing_rewards.experience or fallback.party_state.outing_rewards.gold:
            raise AssertionError("Rest fallback retained unsecured rewards")
    if save_port.saved_states[2] is not game:
        raise AssertionError("Floor 1 clear did not persist its Hub outcome")
    for member in party_members:
        if member.health.current != member.health.maximum:
            raise AssertionError("Floor 1 clear did not restore HP")
        if member.mana_resource.current != member.mana_resource.maximum:
            raise AssertionError("Floor 1 clear did not restore Mana")

    replay_gold_before = game.party_state.shared_gold
    replay_xp_before = tuple(_total_experience(member) for member in party_members)
    replay_warning = session.submit(
        ChooseOverworldAction(OverworldAction.START_FLOOR_ONE)
    )
    if replay_warning.screen is not OverworldScreen.FLOOR_ONE_WARNING:
        raise AssertionError("Floor 1 replay did not show its warning")
    replay_battle = session.submit(ChooseOverworldAction(OverworldAction.SET_OUT))
    if game.party_state.outing_xp_multiplier_percent != 50:
        raise AssertionError("first Floor 1 replay did not use 50% EXP")
    for battle_index, expected_composition in enumerate(
        floor_one_compositions[:5]
    ):
        if battle_index:
            if replay_battle.screen is not OverworldScreen.MAIN:
                raise AssertionError("replay left the route before the midway Rest")
            replay_battle = session.submit(
                ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER)
            )
        actual_composition = tuple(
            enemy.archetype_id for enemy in session.active_battle.enemies
        )
        if actual_composition != expected_composition:
            raise AssertionError("Floor 1 replay encounter sequence changed")
        replay_battle = _complete_battle(session, replay_battle)
    if replay_battle.screen is not OverworldScreen.REST:
        raise AssertionError("Floor 1 replay did not reach its midway Rest")

    raw_replay_rewards = game.party_state.outing_rewards
    expected_replay_xp = (
        raw_replay_rewards.experience * 50 // 400
    ) * 2
    expected_replay_gold = (raw_replay_rewards.gold + 1) // 2
    for member in party_members:
        member.health.take_damage(1)
        member.mana_resource.spend(1)
    replay_extraction = session.submit(
        ChooseOverworldAction(OverworldAction.EXTRACT)
    )
    if replay_extraction.screen is not OverworldScreen.EXTRACTION:
        raise AssertionError("midway replay extraction did not open")
    if replay_extraction.outing_rewards.experience != expected_replay_xp:
        raise AssertionError(
            "replay extraction EXP mismatch: raw=%s actual=%s expected=%s"
            % (
                raw_replay_rewards.experience,
                replay_extraction.outing_rewards.experience,
                expected_replay_xp,
            )
        )
    if replay_extraction.outing_rewards.gold != expected_replay_gold:
        raise AssertionError("replay extraction gold was not rounded up at half")
    replay_hub = session.submit(
        ChooseOverworldAction(OverworldAction.RETURN_TO_HUB)
    )
    if replay_hub.screen is not OverworldScreen.HUB:
        raise AssertionError("early extraction did not return to the Hub")
    replay_xp_each = tuple(
        _total_experience(member) - before
        for member, before in zip(party_members, replay_xp_before)
    )
    if replay_xp_each != (expected_replay_xp // 2,) * 2:
        raise AssertionError("replay extraction EXP did not split evenly")
    if game.party_state.shared_gold != replay_gold_before + expected_replay_gold:
        raise AssertionError("replay extraction did not secure its gold")
    if game.party_state.floor_one_runs_started_after_clear != 1:
        raise AssertionError("early extraction did not count the replay run")
    if len(save_port.saved_states) != 5:
        raise AssertionError("early extraction did not persist its fallback and Hub outcome")
    extraction_fallback = save_port.saved_states[3]
    if extraction_fallback is game:
        raise AssertionError("extraction fallback aliased the live run")
    if extraction_fallback.party_state.phase is not DungeonPhase.HUB:
        raise AssertionError("extraction fallback did not bank the partial run")
    if extraction_fallback.party_state.shared_gold != game.party_state.shared_gold:
        raise AssertionError("extraction fallback did not bank partial gold")
    if save_port.saved_states[4] is not game:
        raise AssertionError("early extraction did not persist the final Hub outcome")
    for member in party_members:
        if member.health.current != member.health.maximum:
            raise AssertionError("early extraction did not restore HP")
        if member.mana_resource.current != member.mana_resource.maximum:
            raise AssertionError("early extraction did not restore Mana")

    return {
        "route_nodes": len(route_trace),
        "encounters": len(encounter_ids),
        "rests": len(rest_ids),
        "battles": EXPECTED_BATTLE_COUNT,
        "enemies": EXPECTED_ENEMY_COUNT,
        "final_node": game.overworld_state.current_route_node_id,
        "level": surface_level,
        "exp": surface_exp,
        "growth_points": surface_growth_points,
        "gold": surface_gold,
        "hub_screen": hub_view.screen.value,
        "tutorial_party_size": 2,
        "tutorial_enemy_count": 3,
        "tutorial_battles": 1,
        "secured_gold": hub_view.shared_gold,
        "lead_tutorial_exp": lead_tutorial_exp,
        "companion_tutorial_exp": companion_tutorial_exp,
        "floor_one_battles": 10,
        "floor_one_xp_each": floor_one_xp_each[0],
        "floor_one_shared_gold": floor_one_hub.shared_gold,
        "floor_one_cleared": game.party_state.floor_one_cleared,
        "floor_one_replay_rate": 50,
        "floor_one_replay_extract_xp": replay_extraction.outing_rewards.experience,
        "floor_one_replay_extract_gold": replay_extraction.outing_rewards.gold,
        "floor_one_replay_secured_gold": replay_hub.shared_gold,
        "floor_one_replay_runs": game.party_state.floor_one_runs_started_after_clear,
    }


def boot():
    result = _qualify_route()
    result.update(
        {
            "pyodide_version": PYODIDE_VERSION,
            "python_version": sys.version.split()[0],
        }
    )
    return json.dumps(result)
