from datetime import datetime, timezone

from app.content.catalog import get_drifter_spec
from app.game.expeditions import ExpeditionService
from app.game.overworld_session import OverworldSession
from app.game.party_state import DungeonPhase
from app.player.player_state import PlayerState
from app.presentation.overworld_models import (
    OverworldAction,
    OverworldScreen,
)
from app.presentation.overworld_presenter import OverworldPresenter
from app.ui.overworld_ui import (
    ChooseExpeditionPlan,
    ChooseExpeditionReport,
    ChooseOverworldAction,
)
from tests.game_test_support import completed_hub_game
from tests.persistence_test_support import make_test_save_port


def m6_ready_game():
    from app.player.player_state import PlayerState

    game = completed_hub_game()
    for drifter_id in ("joruun", "zhaivra"):
        game.party_state.recruit_companion(
            game.player_state,
            PlayerState(get_drifter_spec(drifter_id).create_character()),
            cost=0,
        )
    game.party_state._floor_one_cleared = True
    game.party_state._floor_two_cleared = True
    game.party_state._floor_three_cleared = True
    game.party_state.select_active_pair(
        ("branoc", "azhvielle"),
        recruited_ids=tuple(member.drifter_id for member in game.recruited_members),
    )
    return game


def test_hub_expeditions_are_unlocked_without_gating_ordinary_floor_entry():
    game = m6_ready_game()
    game.expedition_state._energy = 0

    view = OverworldPresenter().build(
        game,
        screen=OverworldScreen.HUB,
        now=datetime(2026, 11, 10, tzinfo=timezone.utc),
    )
    actions = {option.action: option for option in view.options}

    assert actions[OverworldAction.EXPEDITIONS].enabled
    assert actions[OverworldAction.START_FLOOR_ONE].enabled
    assert actions[OverworldAction.START_FLOOR_TWO].enabled
    assert actions[OverworldAction.START_FLOOR_THREE].enabled


def test_expedition_screen_lists_available_and_unavailable_categories():
    view = OverworldPresenter().build(
        m6_ready_game(),
        screen=OverworldScreen.EXPEDITION_SETUP,
        now=datetime(2026, 11, 10, tzinfo=timezone.utc),
    )

    floor_ids = {choice.destination_floor_id for choice in view.expedition_choices}
    assert floor_ids == {"floor_one", "floor_two", "floor_three"}
    training = next(
        choice for choice in view.expedition_choices
        if choice.destination_floor_id == "floor_two" and choice.category == "training"
    )
    material = next(
        choice for choice in view.expedition_choices
        if choice.destination_floor_id == "floor_two" and choice.category == "material"
    )
    equipment = next(
        choice for choice in view.expedition_choices
        if choice.destination_floor_id == "floor_two" and choice.category == "equipment"
    )
    recovery = next(
        choice for choice in view.expedition_choices
        if choice.destination_floor_id == "floor_two" and choice.category == "recovery"
    )

    assert training.enabled and material.enabled
    assert not equipment.enabled and "no eligible" in equipment.disabled_reason.casefold()
    assert not recovery.enabled and "no eligible" in recovery.disabled_reason.casefold()


def test_setup_selection_requires_confirmation_and_cancel_spends_nothing(tmp_path):
    game = m6_ready_game()
    port = make_test_save_port(tmp_path / "profile.json")
    session = OverworldSession(
        game,
        battle_factory=lambda *_args, **_kwargs: None,
        enemy_factory=lambda *_args, **_kwargs: None,
        save_port=port,
        now_factory=lambda: datetime(2026, 11, 10, tzinfo=timezone.utc),
    )

    session.submit(ChooseOverworldAction(OverworldAction.EXPEDITIONS))
    setup = session.submit(
        ChooseOverworldAction(OverworldAction.PREPARE_EXPEDITION_FLOOR_ONE)
    )
    confirmation = session.submit(
        ChooseExpeditionPlan("floor_two", "material")
    )

    assert setup.screen is OverworldScreen.EXPEDITION_SETUP
    assert confirmation.screen is OverworldScreen.EXPEDITION_CONFIRMATION
    assert confirmation.expedition_confirmation.destination_floor_label == "Floor II"
    assert confirmation.expedition_confirmation.expedition_member_names == (
        "Joruun Veyr, the Bloody Storm Monk",
        "Zhaivra Kelyth, the Uncontrolled Reagent",
    )
    assert session.game_state.expedition_state.energy == 100

    cancelled = session.submit(ChooseOverworldAction(OverworldAction.CANCEL))

    assert cancelled.screen is OverworldScreen.EXPEDITION_SETUP
    assert session.game_state.expedition_state.energy == 100
    assert session.game_state.party_state.phase is DungeonPhase.HUB


def test_report_claim_input_is_only_available_for_unclaimed_report(tmp_path):
    game = m6_ready_game()
    port = make_test_save_port(tmp_path / "profile.json")
    now = datetime(2026, 11, 10, tzinfo=timezone.utc)
    start = "2026-11-10T12:00:00Z"
    complete = "2026-11-10T12:20:00Z"
    assignment_id = "00000000-0000-4000-8000-000000000555"
    game.expedition_state.install_assignment({
        "assignment_id": assignment_id,
        "outing_floor_id": "floor_one",
        "destination_floor_id": "floor_two",
        "category": "material",
        "expedition_drifter_ids": ["joruun", "zhaivra"],
        "started_at_utc": start,
        "last_observed_at_utc": complete,
        "completed_at_utc": complete,
    })
    game.expedition_state.settle_assignment({
        "report_id": assignment_id,
        "outing_floor_id": "floor_one",
        "destination_floor_id": "floor_two",
        "category": "material",
        "expedition_drifter_ids": ["joruun", "zhaivra"],
        "started_at_utc": start,
        "completed_at_utc": complete,
        "secured_base_xp": 0,
        "experience_awards": {},
        "reward_item_id": "grade_ii_metal",
        "reward_quantity": 1,
        "claimed": False,
    })
    session = OverworldSession(
        game,
        battle_factory=lambda *_args, **_kwargs: None,
        enemy_factory=lambda *_args, **_kwargs: None,
        save_port=port,
        now_factory=lambda: now.replace(minute=20),
    )

    hub = session.submit(ChooseOverworldAction(OverworldAction.EXPEDITIONS))
    report_id = hub.expedition_reports[0].report_id
    claimed = session.submit(ChooseExpeditionReport(report_id))
    repeated = session.submit(ChooseExpeditionReport(report_id))

    assert claimed.notice == "Expedition report claimed."
    assert claimed.expedition_reports[0].claimed
    assert repeated.notice == "That expedition report was already claimed."
    assert repeated.expedition_reports[0].claimed


def test_confirmed_assignment_status_is_visible_during_the_active_battle(tmp_path):
    from app.combat.battle import Battle
    from app.content.catalog import create_enemy_state
    from app.presentation.battle_models import BattleView

    game = m6_ready_game()
    port = make_test_save_port(tmp_path / "profile.json")
    now = datetime(2026, 11, 10, tzinfo=timezone.utc)
    session = OverworldSession(
        game,
        battle_factory=Battle,
        enemy_factory=create_enemy_state,
        save_port=port,
        now_factory=lambda: now,
    )

    session.submit(ChooseOverworldAction(OverworldAction.EXPEDITIONS))
    session.submit(
        ChooseOverworldAction(OverworldAction.PREPARE_EXPEDITION_FLOOR_ONE)
    )
    session.submit(ChooseExpeditionPlan("floor_one", "material"))
    battle = session.submit(ChooseOverworldAction(OverworldAction.CONFIRM))

    assert isinstance(battle, BattleView)
    assert "20:00 remaining" in battle.expedition_status
    assert "Joruun Veyr, the Bloody Storm Monk" in battle.expedition_status
    assert "Zhaivra Kelyth, the Uncontrolled Reagent" in battle.expedition_status


def test_launched_expedition_save_reloads_with_the_next_encounter_actionable(tmp_path):
    from app.game.expeditions import ExpeditionLaunchStatus
    from app.presentation.overworld_models import OverworldAction

    game = m6_ready_game()
    port = make_test_save_port(tmp_path / "profile.json")
    now = datetime(2026, 11, 10, tzinfo=timezone.utc)
    launched = ExpeditionService(
        port,
        now_factory=lambda: now,
        assignment_id_factory=lambda: "00000000-0000-4000-8000-000000000777",
    ).launch(
        game,
        outing_floor_id="floor_one",
        destination_floor_id="floor_two",
        category="material",
        confirmed=True,
    )
    assert launched.status is ExpeditionLaunchStatus.LAUNCHED

    loaded = port.load()
    resumed = OverworldSession(
        loaded.game_state,
        battle_factory=lambda *_args, **_kwargs: None,
        enemy_factory=lambda *_args, **_kwargs: None,
        save_port=port,
        now_factory=lambda: now,
    ).current_view()

    assert resumed.screen is OverworldScreen.MAIN
    assert resumed.contextual_route_option.action is OverworldAction.ENTER_ENCOUNTER
    assert resumed.expedition_status.remaining_seconds == 1200
