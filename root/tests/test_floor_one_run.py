import pytest
from uuid import UUID

from app.combat.battle import Battle
from app.content.catalog import (
    create_enemy_state,
    get_drifter_spec,
    get_encounter_item_rewards,
    get_route_node_spec,
    get_route_spec,
)
from app.game.overworld_session import OverworldSession
from app.game.overworld_state import ContextualRoutePhase
from app.persistence.ports import SaveLoadResult
from app.persistence.save_port_contract import SaveLoadStatus
from app.persistence.coordinator import SaveCoordinator
from app.persistence.local_store import LocalProfileStore
from app.game.party_state import DungeonPhase, PartyState
from app.player.player_state import PlayerState
from app.presentation.battle_models import ActionIntent, BattleView
from app.presentation.overworld_models import (
    MapNodeState,
    OverworldAction,
    OverworldScreen,
)
from app.presentation.overworld_presenter import OverworldPresenter
from app.ui.battle_ui import ChooseAction, GoBack
from app.ui.overworld_ui import (
    ChooseActivePair,
    ChooseCharacterTarget,
    ChooseOverworldAction,
    ChooseOverworldItem,
)
from tests.game_test_support import (
    completed_hub_game as game_at_completed_hub,
    three_member_hub_game,
)


def completed_tutorial_party():
    lead = PlayerState(get_drifter_spec("branoc").create_character(), gold=75)
    companion = PlayerState(get_drifter_spec("azhvielle").create_character())
    party = PartyState()
    assert party.arrive_at_hub(lead)
    assert party.recruit_companion(lead, companion)
    assert party.begin_outing()
    assert party.begin_extraction(experience=0, gold=0)
    assert party.complete_extraction((lead, companion))
    return party, (lead, companion)


def clear_floor_one(party, party_members):
    assert party.start_floor_one_run() == 100
    assert party.complete_floor_one_boss(party_members)


class StableRng:
    def randint(self, _minimum, _maximum):
        return 1

    def choice(self, values):
        return values[0]


class RecordingSavePort:
    def __init__(self):
        self.saved_states = []
        self.save_attempts = []
        self.fail_next_save = False

    def inspect(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def load(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def save(self, game_state):
        self.save_attempts.append(game_state)
        if self.fail_next_save:
            self.fail_next_save = False
            return SaveLoadResult(
                SaveLoadStatus.INVALID,
                error="The game could not be saved.",
            )
        self.saved_states.append(game_state)
        return SaveLoadResult(SaveLoadStatus.SAVED)


class FailNextSavePort:
    def __init__(self, save_port):
        self._save_port = save_port
        self.fail_next_save = False

    def inspect(self):
        return self._save_port.inspect()

    def load(self):
        return self._save_port.load()

    def save(self, game_state):
        if self.fail_next_save:
            self.fail_next_save = False
            return SaveLoadResult(
                SaveLoadStatus.INVALID,
                error="The game could not be saved.",
            )
        return self._save_port.save(game_state)


def make_session(game, save_port=None):
    if save_port is None:
        save_port = RecordingSavePort()
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
    )


def set_out(session):
    view = session.current_view()
    assert view.screen is OverworldScreen.HUB
    warning = session.submit(
        ChooseOverworldAction(OverworldAction.START_FLOOR_ONE)
    )
    assert warning.screen is OverworldScreen.FLOOR_ONE_WARNING
    return session.submit(ChooseOverworldAction(OverworldAction.SET_OUT))


def win_current_battle(session):
    for enemy in session.active_battle.enemies:
        enemy.health.take_damage(enemy.health.current)
    session.submit(ChooseAction(ActionIntent.DEFEND))
    return session.current_view()


def reach_first_floor_one_rest(session):
    set_out(session)
    for battle_number in range(5):
        if battle_number:
            session.submit(
                ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER)
            )
        view = win_current_battle(session)
    return view


def test_floor_one_run_rejects_invalid_start_phases():
    party = PartyState()

    with pytest.raises(ValueError, match="tutorial must be complete"):
        party.start_floor_one_run()

    ready_party, party_members = completed_tutorial_party()
    assert ready_party.start_floor_one_run() == 100
    with pytest.raises(ValueError, match="Hub"):
        ready_party.start_floor_one_run()


def test_floor_one_replay_rates_advance_for_every_started_run_and_clamp():
    party, party_members = completed_tutorial_party()
    clear_floor_one(party, party_members)

    for expected_rate, expected_runs_started in zip(
        (50, 40, 30, 20, 20, 20),
        (1, 2, 3, 4, 5, 6),
    ):
        assert party.start_floor_one_run() == expected_rate
        assert party.floor_one_runs_started_after_clear == expected_runs_started
        assert party.outing_xp_multiplier_percent == expected_rate
        assert party.fail_floor_one_run(party_members)

    assert party.snapshot()["floor_one_cleared"] is True


def test_floor_one_victory_places_authored_enemy_drops_in_pending_rewards():
    game = game_at_completed_hub()
    session = make_session(game)
    set_out(session)
    current_node = get_route_node_spec(
        game.overworld_state.current_route_node_id
    )
    expected_items = dict(get_encounter_item_rewards(current_node.encounter_id))

    result = win_current_battle(session)

    assert game.party_state.outing_rewards.items == expected_items
    assert "Items: 4 Goblin Scrap." in result.adventure_text


def test_floor_one_failure_discards_unsecured_rewards_and_restores_the_party():
    party, party_members = completed_tutorial_party()
    lead, companion = party_members
    lead.health.take_damage(17)
    lead.mana_resource.spend(min(lead.mana_resource.current, 3))
    companion.health.take_damage(23)
    companion.mana_resource.spend(min(companion.mana_resource.current, 5))

    assert party.start_floor_one_run() == 100
    party.add_floor_one_rewards(experience=17, gold=9, items={"herb": 2})
    party.add_floor_one_rewards(experience=4, gold=3, items={"herb": 1})

    assert party.outing_rewards.snapshot() == {
        "experience": 21,
        "gold": 12,
        "items": {"herb": 3},
    }
    assert party.fail_floor_one_run(party_members)

    assert party.phase is DungeonPhase.HUB
    assert party.tutorial_complete is True
    assert party.outing_rewards.snapshot() == {
        "experience": 0,
        "gold": 0,
        "items": {},
    }
    assert party.shared_gold == 10
    assert party.shared_items == {}
    for member in party_members:
        assert member.health.current == member.health.maximum
        assert member.mana_resource.current == member.mana_resource.maximum


def test_floor_one_partial_extraction_rounds_equal_xp_and_gold_and_keeps_items():
    party, party_members = completed_tutorial_party()
    clear_floor_one(party, party_members)
    xp_before = tuple(member.exp_state.current for member in party_members)
    assert party.start_floor_one_run() == 50
    party.add_floor_one_rewards(experience=35, gold=7, items={"herb": 2})

    assert party.begin_floor_one_extraction(partial=True)
    assert party.outing_rewards.snapshot() == {
        "experience": 8,
        "gold": 4,
        "items": {"herb": 2},
    }
    assert party.complete_extraction(party_members)

    assert tuple(
        member.exp_state.current - before
        for member, before in zip(party_members, xp_before)
    ) == (4, 4)
    assert party.shared_gold == 14
    assert party.shared_items == {"herb": 2}
    assert party.phase is DungeonPhase.HUB


def test_floor_one_boss_banks_full_rewards_and_marks_floor_cleared():
    party, party_members = completed_tutorial_party()
    lead, companion = party_members
    lead.health.take_damage(13)
    companion.health.take_damage(19)
    assert party.start_floor_one_run() == 100
    party.add_floor_one_rewards(experience=11, gold=7, items={"relic": 1})

    assert party.complete_floor_one_boss(party_members)

    assert party.floor_one_cleared is True
    assert party.floor_one_runs_started_after_clear == 0
    assert tuple(member.exp_state.current for member in party_members) == (5, 5)
    assert party.shared_gold == 17
    assert party.shared_items == {"relic": 1}
    assert party.outing_rewards.experience == 0
    assert party.phase is DungeonPhase.HUB
    for member in party_members:
        assert member.health.current == member.health.maximum


def test_floor_one_clear_and_active_replay_rate_round_trip_in_party_snapshot():
    party, party_members = completed_tutorial_party()
    clear_floor_one(party, party_members)
    party.start_floor_one_run()

    restored = PartyState.from_snapshot(
        party.snapshot(), companions=(party_members[1],)
    )

    assert restored.floor_one_cleared is True
    assert restored.floor_one_runs_started_after_clear == 1
    assert restored.outing_xp_multiplier_percent == 50


def test_hub_warning_requires_explicit_set_out_and_rejects_stale_confirmation():
    game = game_at_completed_hub()
    session = make_session(game)

    hub = session.current_view()
    assert any(
        option.action is OverworldAction.START_FLOOR_ONE
        for option in hub.options
    )
    warning = session.submit(
        ChooseOverworldAction(OverworldAction.START_FLOOR_ONE)
    )
    assert warning.screen is OverworldScreen.FLOOR_ONE_WARNING
    assert "Death means returning to the Hub" in warning.adventure_text
    assert tuple(option.action for option in warning.options) == (
        OverworldAction.SET_OUT,
        OverworldAction.BACK,
    )

    returned = session.submit(ChooseOverworldAction(OverworldAction.BACK))
    stale = session.submit(ChooseOverworldAction(OverworldAction.SET_OUT))

    assert returned.screen is OverworldScreen.HUB
    assert stale.screen is OverworldScreen.HUB
    assert stale.notice == "That option is not available."
    assert game.party_state.phase is DungeonPhase.HUB
    assert game.overworld_state.active_route_id == "surface"


def test_set_out_starts_the_four_goblin_battle_with_both_drifters():
    game = game_at_completed_hub()
    session = make_session(game)

    battle_view = set_out(session)

    assert isinstance(battle_view, BattleView)
    assert len(session.active_battle.enemies) == 4
    assert session.active_battle.party_states == (
        game.player_state,
        game.party_state.companions[0],
    )
    assert game.party_state.phase is DungeonPhase.OUTING
    assert game.overworld_state.active_route_id == "floor_one"
    assert game.overworld_state.current_route_node_id == "floor_one_battle_01"


def test_active_pair_and_bench_access_stay_locked_through_rest():
    game = three_member_hub_game()
    session = make_session(game)
    game.party_state.select_active_pair(
        ("joruun", "azhvielle"),
        recruited_ids=tuple(
            member.character.profile.drifter_id
            for member in game.recruited_members
        ),
    )
    active_ids = game.party_state.active_drifter_ids
    rest_view = reach_first_floor_one_rest(session)
    assert rest_view.screen is OverworldScreen.REST

    rejected_swap = session.submit(
        ChooseActivePair(("branoc", "joruun"))
    )
    character = session.submit(
        ChooseOverworldAction(OverworldAction.CHARACTER)
    )
    rejected_bench_target = session.submit(ChooseCharacterTarget("branoc"))

    assert rejected_swap.notice == "That party is not available."
    assert game.party_state.active_drifter_ids == active_ids
    assert {target.drifter_id for target in character.character.targets} == {
        "joruun",
        "azhvielle",
    }
    assert rejected_bench_target.notice == "That Drifter is not available."
    assert game.party_state.active_drifter_ids == active_ids


def test_reused_floor_encounters_do_not_enter_surface_defeat_history():
    game = game_at_completed_hub()
    session = make_session(game)
    set_out(session)

    first_result = win_current_battle(session)
    assert first_result.screen is OverworldScreen.MAIN
    assert game.party_state.outing_rewards.experience == 160
    assert "dungeon_goblin_quad" not in game.world_state.defeated_encounters

    second_view = session.submit(
        ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER)
    )
    assert isinstance(second_view, BattleView)
    assert len(session.active_battle.enemies) == 3
    win_current_battle(session)

    assert game.overworld_state.current_route_node_id == "floor_one_battle_03"
    assert "dungeon_goblin_trio" not in game.world_state.defeated_encounters


def test_floor_one_death_discards_rewards_and_returns_restored_party_to_hub():
    game = game_at_completed_hub()
    session = make_session(game)
    lead, companion = game.player_state, game.party_state.companions[0]
    lead_exp = lead.exp_state.current
    shared_gold = game.party_state.shared_gold
    set_out(session)
    win_current_battle(session)
    session.submit(ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER))
    for member in (lead, companion):
        member.health.take_damage(member.health.current)
    session.active_battle._finish("enemy")

    session.submit(GoBack())
    returned = session.current_view()

    assert returned.screen is OverworldScreen.HUB
    assert "unsecured" in returned.adventure_text.lower()
    assert game.party_state.phase is DungeonPhase.HUB
    assert game.party_state.tutorial_complete is True
    assert game.party_state.floor_one_cleared is False
    assert game.party_state.outing_rewards.experience == 0
    assert game.party_state.shared_gold == shared_gold
    assert session._save_port.saved_states == [game]
    assert lead.exp_state.current == lead_exp
    assert game.overworld_state.current_route_node_id == "surface_dungeon_entrance"
    for member in (lead, companion):
        assert member.health.current == member.health.maximum
        assert member.mana_resource.current == member.mana_resource.maximum


def test_floor_one_boss_clear_banks_even_if_surface_goblin_lord_was_defeated():
    game = game_at_completed_hub()
    party_members = (game.player_state,) + game.party_state.companions
    assert game.party_state.start_floor_one_run() == 100
    route = get_route_spec("floor_one")
    overworld = game.overworld_state
    overworld.begin_route("floor_one")
    for node in route.nodes[1:-1]:
        overworld.advance_to(node.node_id)
        if node.kind.value == "rest":
            overworld.record_resolved_rest_node(node.node_id)
    overworld.advance_to(
        route.nodes[-1].node_id,
        contextual_phase=ContextualRoutePhase.ENTER_ENCOUNTER,
    )

    session = make_session(game)
    session._screen = OverworldScreen.MAIN
    boss_view = session.submit(
        ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER)
    )
    assert isinstance(boss_view, BattleView)
    assert session.active_battle.encounter_label == "Goblin Lord"
    win_current_battle(session)

    returned = session.current_view()
    assert returned.screen is OverworldScreen.HUB
    assert game.party_state.floor_one_cleared is True
    assert game.party_state.shared_gold == 28
    assert tuple(member.level_state.current for member in party_members) == (2, 2)
    assert tuple(member.exp_state.current for member in party_members) == (50, 50)
    assert game.overworld_state.active_route_id == "surface"
    assert game.overworld_state.current_route_node_id == "surface_dungeon_entrance"
    assert game.world_state.defeated_encounters.count("surface_goblin_lord") == 1
    assert session._save_port.saved_states == [game]


def test_floor_one_extraction_returns_to_hub_and_supersedes_the_run_save():
    game = game_at_completed_hub()
    party_members = (game.player_state,) + game.party_state.companions
    assert game.party_state.start_floor_one_run() == 100
    game.overworld_state.begin_route("floor_one")
    game.party_state.add_floor_one_rewards(
        experience=20,
        gold=9,
        items={"herb": 1},
    )
    assert game.party_state.begin_floor_one_extraction(partial=True)
    session = make_session(game)

    returned = session.submit(
        ChooseOverworldAction(OverworldAction.RETURN_TO_HUB)
    )

    assert returned.screen is OverworldScreen.HUB
    assert game.party_state.phase is DungeonPhase.HUB
    assert game.party_state.shared_gold == 15
    assert game.party_state.shared_items == {"herb": 1}
    assert tuple(member.exp_state.current for member in party_members) == (5, 5)
    assert game.overworld_state.current_route_node_id == "surface_dungeon_entrance"
    assert session._save_port.saved_states == [game]
    duplicate = session.submit(
        ChooseOverworldAction(OverworldAction.RETURN_TO_HUB)
    )
    assert duplicate.notice == "That option is not available."
    assert session._save_port.saved_states == [game]


def test_floor_one_rest_offers_run_choices_and_saves_only_at_rest():
    game = game_at_completed_hub()
    session = make_session(game)
    rest = reach_first_floor_one_rest(session)

    assert rest.screen is OverworldScreen.REST
    assert rest.location_label == "Midway Rest"
    assert tuple(option.action for option in rest.options) == (
        OverworldAction.REST,
        OverworldAction.SAVE,
        OverworldAction.CHARACTER,
        OverworldAction.ITEMS,
        OverworldAction.EXTRACT,
    )
    assert tuple(option.label for option in rest.options) == (
        "Recover",
        "Save",
        "Character",
        "Items",
        "Extract",
    )
    assert rest.contextual_route_option.action is OverworldAction.SKIP_REST
    assert rest.contextual_route_option.label == "Continue Without Rest"
    assert next(
        option for option in rest.options if option.action is OverworldAction.SAVE
    ).enabled
    saved = session.submit(ChooseOverworldAction(OverworldAction.SAVE))
    assert saved.notice == "Game saved."
    assert session._save_port.saved_states == [game]

    session.submit(ChooseOverworldAction(OverworldAction.SKIP_REST))
    fallback = session._save_port.saved_states[1]
    options = session.submit(ChooseOverworldAction(OverworldAction.OPTIONS))
    save = next(
        option for option in options.options if option.action is OverworldAction.SAVE
    )
    assert not save.enabled
    session.submit(ChooseOverworldAction(OverworldAction.SAVE))
    assert session._save_port.saved_states == [game, fallback]


def test_floor_one_recover_keeps_the_party_at_rest_until_explicit_continue():
    game = game_at_completed_hub()
    session = make_session(game)
    reach_first_floor_one_rest(session)
    party_members = (game.player_state,) + game.party_state.companions
    for member in party_members:
        member.health.take_damage(11)
        member.mana_resource.spend(min(member.mana_resource.current, 3))

    recovered = session.submit(ChooseOverworldAction(OverworldAction.REST))

    assert recovered.screen is OverworldScreen.REST
    assert game.overworld_state.current_route_node_id == "floor_one_midway_rest"
    assert "floor_one_midway_rest" not in game.overworld_state.resolved_rest_node_ids
    assert any(
        option.action is OverworldAction.EXTRACT and option.enabled
        for option in recovered.options
    )
    for member in party_members:
        assert member.health.current == member.health.maximum
        assert member.mana_resource.current == member.mana_resource.maximum

    continued = session.submit(ChooseOverworldAction(OverworldAction.SKIP_REST))
    assert continued.screen is OverworldScreen.MAIN
    assert game.overworld_state.current_route_node_id == "floor_one_battle_06"


def test_floor_one_continue_without_rest_does_not_heal_either_drifter():
    game = game_at_completed_hub()
    session = make_session(game)
    reach_first_floor_one_rest(session)
    party_members = (game.player_state,) + game.party_state.companions
    for member in party_members:
        member.health.take_damage(11)
        member.mana_resource.spend(min(member.mana_resource.current, 3))
    before = tuple(
        (member.health.current, member.mana_resource.current)
        for member in party_members
    )

    continued = session.submit(ChooseOverworldAction(OverworldAction.SKIP_REST))

    assert continued.screen is OverworldScreen.MAIN
    assert game.overworld_state.current_route_node_id == "floor_one_battle_06"
    assert tuple(
        (member.health.current, member.mana_resource.current)
        for member in party_members
    ) == before


def test_floor_one_rest_can_extract_for_partial_rewards_and_return_to_hub():
    game = game_at_completed_hub()
    session = make_session(game)
    rest = reach_first_floor_one_rest(session)
    assert rest.screen is OverworldScreen.REST
    assert game.party_state.outing_rewards.experience > 0
    expected_gold = (game.party_state.outing_rewards.gold + 1) // 2

    extraction = session.submit(
        ChooseOverworldAction(OverworldAction.EXTRACT)
    )
    assert extraction.screen is OverworldScreen.EXTRACTION
    assert extraction.outing_rewards.gold == expected_gold

    hub = session.submit(
        ChooseOverworldAction(OverworldAction.RETURN_TO_HUB)
    )
    assert hub.screen is OverworldScreen.HUB
    assert hub.location_label == "Floor 1 Hub"
    assert game.party_state.phase is DungeonPhase.HUB


def test_floor_one_recovered_party_can_still_extract_and_keep_items():
    game = game_at_completed_hub()
    session = make_session(game)
    reach_first_floor_one_rest(session)
    party_members = (game.player_state,) + game.party_state.companions
    expected_items = game.party_state.outing_rewards.items
    for member in party_members:
        member.health.take_damage(11)
        member.mana_resource.spend(min(member.mana_resource.current, 3))

    recovered = session.submit(ChooseOverworldAction(OverworldAction.REST))
    assert recovered.screen is OverworldScreen.REST

    extraction = session.submit(ChooseOverworldAction(OverworldAction.EXTRACT))
    assert extraction.screen is OverworldScreen.EXTRACTION
    assert {
        item.item_id: item.quantity for item in extraction.outing_rewards.items
    } == expected_items

    hub = session.submit(ChooseOverworldAction(OverworldAction.RETURN_TO_HUB))
    assert hub.screen is OverworldScreen.HUB
    assert game.party_state.shared_items == expected_items
    assert all(
        member.health.current == member.health.maximum
        and member.mana_resource.current == member.mana_resource.maximum
        for member in party_members
    )


@pytest.mark.parametrize(
    ("first_action", "nested_action", "expected_screen"),
    (
        (OverworldAction.CHARACTER, OverworldAction.SKILLS, OverworldScreen.SKILLS),
        (OverworldAction.ITEMS, OverworldAction.INSPECT, OverworldScreen.ITEM_INSPECT),
    ),
)
def test_floor_one_rest_inspection_returns_to_same_rest(
    first_action,
    nested_action,
    expected_screen,
):
    game = game_at_completed_hub()
    game.player_state.inventory.add_item(
        game.player_state.get_equipped("weapon")
    )
    session = make_session(game)
    reach_first_floor_one_rest(session)

    parent = session.submit(ChooseOverworldAction(first_action))
    if first_action is OverworldAction.ITEMS:
        parent = session.submit(
            ChooseOverworldItem(parent.inventory.items[0].selection_key)
        )
        parent = session.submit(ChooseOverworldAction(nested_action))
    else:
        parent = session.submit(ChooseOverworldAction(nested_action))
    assert parent.screen is expected_screen

    returned = session.submit(ChooseOverworldAction(OverworldAction.BACK))
    if expected_screen in {OverworldScreen.SKILLS, OverworldScreen.WEAPON}:
        assert returned.screen is OverworldScreen.CHARACTER
        returned = session.submit(ChooseOverworldAction(OverworldAction.BACK))
    elif expected_screen is OverworldScreen.ITEM_INSPECT:
        assert returned.screen is OverworldScreen.ITEMS
        returned = session.submit(ChooseOverworldAction(OverworldAction.BACK))

    assert returned.screen is OverworldScreen.REST
    assert returned.location_label == "Midway Rest"


def test_floor_one_active_run_resumes_at_unresolved_rest_screen():
    game = game_at_completed_hub()
    session = make_session(game)
    rest = reach_first_floor_one_rest(session)

    resumed = make_session(game).current_view()

    assert rest.screen is OverworldScreen.REST
    assert resumed.screen is OverworldScreen.REST
    assert resumed.location_label == rest.location_label
    assert resumed.contextual_route_option.action is OverworldAction.SKIP_REST


def test_floor_one_rest_save_load_resumes_at_same_checkpoint(tmp_path):
    game = game_at_completed_hub()
    save = SaveCoordinator(
        LocalProfileStore(tmp_path / "profiles"),
        UUID("00000000-0000-4000-8000-000000000021"),
    )
    session = make_session(game, save)
    rest = reach_first_floor_one_rest(session)

    saved = session.submit(ChooseOverworldAction(OverworldAction.SAVE))
    loaded = save.load()
    resumed = make_session(loaded.game_state).current_view()

    assert saved.notice == "Game saved."
    assert loaded.status is SaveLoadStatus.LOADED
    assert resumed.screen is OverworldScreen.REST
    assert resumed.location_label == rest.location_label
    assert resumed.contextual_route_option.action is OverworldAction.SKIP_REST
    assert loaded.game_state.overworld_state.current_route_node_id == (
        game.overworld_state.current_route_node_id
    )
    assert loaded.game_state.party_state.outing_rewards.snapshot() == (
        game.party_state.outing_rewards.snapshot()
    )


@pytest.mark.parametrize(
    "action",
    (
        OverworldAction.SKIP_REST,
        OverworldAction.EXTRACT,
    ),
)
def test_floor_one_rest_exit_stays_at_rest_when_fallback_save_fails(action):
    game = game_at_completed_hub()
    save = RecordingSavePort()
    session = make_session(game, save)
    reach_first_floor_one_rest(session)
    before = game.snapshot()
    save.fail_next_save = True

    view = session.submit(ChooseOverworldAction(action))

    assert view.screen is OverworldScreen.REST
    assert view.notice == "The next step could not be saved. You remain at this Rest."
    assert game.snapshot() == before
    assert save.saved_states == []


def test_floor_one_continue_persists_independent_safe_hub_before_advancing():
    game = game_at_completed_hub()
    save = RecordingSavePort()
    session = make_session(game, save)
    reach_first_floor_one_rest(session)
    party_members = (game.player_state,) + game.party_state.companions
    shared_gold = game.party_state.shared_gold
    game.party_state.add_floor_one_rewards(
        experience=20,
        gold=9,
        items={"herb": 1},
    )
    for member in party_members:
        member.health.take_damage(11)
        member.mana_resource.spend(min(member.mana_resource.current, 3))

    continued = session.submit(
        ChooseOverworldAction(OverworldAction.SKIP_REST)
    )

    fallback = save.saved_states[0]
    assert continued.screen is OverworldScreen.MAIN
    assert game.overworld_state.current_route_node_id == "floor_one_battle_06"
    assert fallback is not game
    assert fallback.party_state.phase is DungeonPhase.HUB
    assert fallback.party_state.outing_rewards.snapshot() == {
        "experience": 0,
        "gold": 0,
        "items": {},
    }
    assert fallback.party_state.shared_gold == shared_gold
    assert fallback.party_state.shared_items == {}
    assert fallback.overworld_state.active_route_id == "surface"
    assert fallback.overworld_state.current_route_node_id == (
        "surface_dungeon_entrance"
    )
    for member in (fallback.player_state,) + fallback.party_state.companions:
        assert member.health.current == member.health.maximum
        assert member.mana_resource.current == member.mana_resource.maximum


def test_floor_one_extract_persists_banked_rewards_before_leaving_rest():
    game = game_at_completed_hub()
    save = RecordingSavePort()
    session = make_session(game, save)
    reach_first_floor_one_rest(session)
    game.party_state.add_floor_one_rewards(
        experience=20,
        gold=9,
        items={"herb": 1},
    )
    secured_gold_before = game.party_state.shared_gold
    secured_items_before = game.party_state.shared_items
    rewards = game.party_state.outing_rewards.snapshot()
    xp_each = (
        rewards["experience"]
        * game.party_state.outing_xp_multiplier_percent
        // 400
    )
    expected_progression = []
    for member in (game.player_state,) + game.party_state.companions:
        expected_member = member.clone()
        expected_member.gain_experience(xp_each)
        expected_progression.append(
            (expected_member.level_state.current, expected_member.exp_state.current)
        )

    extraction = session.submit(
        ChooseOverworldAction(OverworldAction.EXTRACT)
    )

    fallback = save.saved_states[0]
    expected_items = dict(secured_items_before)
    for item_id, quantity in rewards["items"].items():
        expected_items[item_id] = expected_items.get(item_id, 0) + quantity
    assert extraction.screen is OverworldScreen.EXTRACTION
    assert game.party_state.phase is DungeonPhase.EXTRACTION
    assert game.party_state.shared_gold == 10
    assert fallback is not game
    assert fallback.party_state.phase is DungeonPhase.HUB
    assert fallback.party_state.shared_gold == (
        secured_gold_before + (rewards["gold"] + 1) // 2
    )
    assert fallback.party_state.shared_items == expected_items
    assert tuple(
        (member.level_state.current, member.exp_state.current)
        for member in (fallback.player_state,) + fallback.party_state.companions
    ) == tuple(expected_progression)
    assert fallback.party_state.outing_rewards.snapshot() == {
        "experience": 0,
        "gold": 0,
        "items": {},
    }
    assert fallback.overworld_state.current_route_node_id == (
        "surface_dungeon_entrance"
    )


def test_death_save_failure_cannot_restore_the_previous_rest_checkpoint(tmp_path):
    game = game_at_completed_hub()
    store = LocalProfileStore(tmp_path / "profiles")
    coordinator = SaveCoordinator(
        store,
        UUID("00000000-0000-4000-8000-000000000023"),
    )
    save = FailNextSavePort(coordinator)
    session = make_session(game, save)
    reach_first_floor_one_rest(session)
    assert session.submit(ChooseOverworldAction(OverworldAction.SAVE)).notice == (
        "Game saved."
    )

    session.submit(ChooseOverworldAction(OverworldAction.SKIP_REST))
    session.submit(ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER))
    for member in (game.player_state,) + game.party_state.companions:
        member.health.take_damage(member.health.current)
    session.active_battle._finish("enemy")
    save.fail_next_save = True
    session.submit(GoBack())
    defeated = session.current_view()

    loaded = coordinator.load()
    assert defeated.screen is OverworldScreen.HUB
    assert loaded.status is SaveLoadStatus.LOADED
    assert loaded.game_state.party_state.phase is DungeonPhase.HUB
    assert loaded.game_state.party_state.outing_rewards.snapshot() == {
        "experience": 0,
        "gold": 0,
        "items": {},
    }
    assert loaded.game_state.overworld_state.active_route_id == "surface"
    assert loaded.game_state.overworld_state.current_route_node_id == (
        "surface_dungeon_entrance"
    )
    persisted = store.load(coordinator.profile_id).envelope
    assert persisted.local_sequence == 2


def test_floor_one_map_tracks_active_route_cursor_not_surface_defeats():
    game = game_at_completed_hub()
    route = get_route_spec("floor_one")
    game.party_state.start_floor_one_run()
    game.overworld_state.begin_route("floor_one")
    for index in range(1, 7):
        previous = route.nodes[index - 1]
        if previous.kind.value == "rest":
            game.overworld_state.record_resolved_rest_node(previous.node_id)
        game.overworld_state.advance_to(route.nodes[index].node_id)

    view = OverworldPresenter().build(game, screen=OverworldScreen.MAP)

    assert tuple(node.display_label for node in view.route_map.nodes) == tuple(
        node.display_label for node in route.nodes
    )
    assert all(
        node.state is MapNodeState.COMPLETED
        for node in view.route_map.nodes[:6]
    )
    assert view.route_map.nodes[6].state is MapNodeState.CURRENT
    assert all(
        node.state is MapNodeState.REMAINING
        for node in view.route_map.nodes[7:]
    )


def test_floor_one_death_supersedes_saved_rest_checkpoint(tmp_path):
    game = game_at_completed_hub()
    store = LocalProfileStore(tmp_path / "profiles")
    save = SaveCoordinator(
        store,
        UUID("00000000-0000-4000-8000-000000000022"),
    )
    session = make_session(game, save)
    reach_first_floor_one_rest(session)
    assert session.submit(ChooseOverworldAction(OverworldAction.SAVE)).notice == (
        "Game saved."
    )
    xp_before = tuple(
        member.exp_state.current
        for member in (game.player_state,) + game.party_state.companions
    )
    shared_gold_before = game.party_state.shared_gold

    restarted_state = save.load().game_state
    restarted = make_session(restarted_state, save)
    assert restarted.current_view().screen is OverworldScreen.REST
    restarted.submit(ChooseOverworldAction(OverworldAction.SKIP_REST))
    restarted.submit(
        ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER)
    )
    for member in (restarted_state.player_state,) + restarted_state.party_state.companions:
        member.health.take_damage(member.health.current)
    restarted.active_battle._finish("enemy")
    restarted.submit(GoBack())
    defeated = restarted.current_view()

    persisted = store.load(save.profile_id).envelope
    loaded_after_death = save.load()
    returned = make_session(loaded_after_death.game_state).current_view()

    assert defeated.screen is OverworldScreen.HUB
    assert persisted.local_sequence == 3
    assert persisted.payload["overworld"]["active_route_id"] == "surface"
    assert persisted.payload["overworld"]["current_route_node_id"] == (
        "surface_dungeon_entrance"
    )
    assert persisted.payload["party"]["phase"] == "hub"
    assert persisted.payload["party"]["outing_rewards"] == {
        "experience": 0,
        "gold": 0,
        "items": {},
    }
    assert returned.screen is OverworldScreen.HUB
    assert loaded_after_death.game_state.party_state.shared_gold == shared_gold_before
    assert tuple(
        member.exp_state.current
        for member in (loaded_after_death.game_state.player_state,)
        + loaded_after_death.game_state.party_state.companions
    ) == xp_before
    for member in (loaded_after_death.game_state.player_state,) + (
        loaded_after_death.game_state.party_state.companions
    ):
        assert member.health.current == member.health.maximum
        assert member.mana_resource.current == member.mana_resource.maximum
