from app.combat.battle import Battle
import pytest

from app.content.catalog import create_enemy_state
from app.game.game_state import GameState
from app.game.overworld_session import OverworldSession
from app.game.party_state import DungeonPhase
from app.persistence.ports import SaveLoadStatus
from app.persistence.save_document import build_save_document, reconstruct_game_state
from app.player.character_run_state import FIRE_INFUSION_REQUIREMENTS, InfusionKind
from app.player.player_state import PlayerState
from app.presentation.battle_models import ActionIntent, BattleView, InteractionPhase
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.ui.battle_ui import ChooseAction, GoBack
from app.ui.overworld_ui import ChooseCompanion, ChooseOverworldAction
from tests.persistence_test_support import make_test_save_port
from app.content import catalog
from tests.game_test_support import (
    hub_game as game_at_hub,
    three_member_hub_game,
)


class StableRng:
    def randint(self, _minimum, _maximum):
        return 1

    def choice(self, values):
        return values[0]


def ready_party():
    game = game_at_hub()
    session = OverworldSession(
        game,
        battle_factory=lambda player, enemies, **kwargs: Battle(
            player,
            enemies,
            rng=StableRng(),
            **kwargs,
        ),
        enemy_factory=lambda archetype_id, tier=0: create_enemy_state(
            archetype_id,
            tier=tier,
        ),
    )
    session.submit(ChooseOverworldAction(OverworldAction.RECRUIT_COMPANION))
    session.submit(ChooseCompanion("azhvielle", "floor_one_d2_recruitment"))
    view = session.submit(ChooseOverworldAction(OverworldAction.READY))
    assert isinstance(view, BattleView)
    return game, session, view


def test_ready_starts_the_authored_party_encounter_and_victory_opens_extraction():
    game, session, battle_view = ready_party()
    assert len(session.active_battle.enemies) == 3
    assert len(battle_view.party_members) == 2

    for enemy in session.active_battle.enemies:
        enemy.health.take_damage(enemy.health.current)
    completed = session.submit(ChooseAction(ActionIntent.DEFEND))
    extraction = session.current_view()

    assert completed.interaction_phase is InteractionPhase.COMPLETE
    assert extraction.screen.value == "extraction"
    assert game.party_state.phase is DungeonPhase.EXTRACTION
    assert extraction.adventure_text
    assert extraction.outing_rewards.experience == 120
    assert extraction.outing_rewards.gold == 9
    assert tuple(
        (item.item_id, item.quantity) for item in extraction.outing_rewards.items
    ) == (("goblin_scrap", 3),)
    assert tuple(option.action.value for option in extraction.options) == (
        "return_to_hub",
    )


def test_extraction_delays_rewards_then_banks_once_and_restores_both_drifters():
    game, session, _ = ready_party()
    lead = game.player_state
    companion = game.party_state.companions[0]
    lead.health.take_damage(25)
    lead.mana_resource.spend(min(lead.mana_resource.current, 7))
    companion.health.take_damage(31)
    companion.mana_resource.spend(min(companion.mana_resource.current, 9))
    player_xp_before = lead.exp_state.current
    companion_xp_before = companion.exp_state.current
    for enemy in session.active_battle.enemies:
        enemy.health.take_damage(enemy.health.current)
    session.submit(ChooseAction(ActionIntent.DEFEND))

    pending = session.current_view()
    assert lead.exp_state.current == player_xp_before
    assert companion.exp_state.current == companion_xp_before
    assert game.party_state.shared_gold == 10

    returned = session.submit(
        ChooseOverworldAction(OverworldAction.RETURN_TO_HUB)
    )

    assert returned.screen.value == "hub"
    assert game.party_state.phase is DungeonPhase.HUB
    assert game.party_state.tutorial_complete is True
    assert game.party_state.shared_gold == 19
    assert game.party_state.shared_items == {"goblin_scrap": 3}
    assert lead.exp_state.current - player_xp_before == 60
    assert companion.exp_state.current - companion_xp_before == 60
    assert lead.health.current == lead.health.maximum
    assert lead.mana_resource.current == lead.mana_resource.maximum
    assert companion.health.current == companion.health.maximum
    assert companion.mana_resource.current == companion.mana_resource.maximum
    assert session.active_battle is None
    assert session.submit(
        ChooseOverworldAction(OverworldAction.RETURN_TO_HUB)
    ).notice == "That option is not available."
    assert game.party_state.shared_gold == 19
    assert OverworldAction.READY not in {
        option.action for option in returned.options if option.enabled
    }
    assert pending.outing_rewards.experience == 120

    reloaded = reconstruct_game_state(build_save_document(game))
    assert reloaded.party_state.phase is DungeonPhase.HUB
    assert reloaded.party_state.tutorial_complete is True
    assert reloaded.party_state.shared_gold == 19
    assert reloaded.player_state.exp_state.current == 60
    assert reloaded.party_state.companions[0].exp_state.current == 60


def test_pending_extraction_round_trips_without_banking_rewards():
    game, session, _ = ready_party()
    for enemy in session.active_battle.enemies:
        enemy.health.take_damage(enemy.health.current)
    session.submit(ChooseAction(ActionIntent.DEFEND))

    reloaded = reconstruct_game_state(build_save_document(game))
    resumed = OverworldSession(
        reloaded,
        battle_factory=Battle,
        enemy_factory=create_enemy_state,
    )
    view = resumed.current_view()

    assert view.screen.value == "extraction"
    assert reloaded.party_state.phase is DungeonPhase.EXTRACTION
    assert view.outing_rewards.experience == 120
    assert tuple(
        (item.item_id, item.quantity) for item in view.outing_rewards.items
    ) == (("goblin_scrap", 3),)
    assert reloaded.party_state.shared_gold == 10
    assert reloaded.player_state.exp_state.current == 0


def test_tutorial_defeat_keeps_recruited_pair_and_returns_them_ready_to_retry():
    game, session, _ = ready_party()
    for member in (game.player_state, *game.party_state.companions):
        member.health.take_damage(member.health.current)
    session.active_battle._finish("enemy")

    session.submit(GoBack())
    view = session.current_view()

    assert view.screen is OverworldScreen.PARTY_READY
    assert game.party_state.phase is DungeonPhase.PARTY_READY
    assert len(game.party_state.companions) == 1
    assert game.player_state.health.current == game.player_state.health.maximum
    assert game.party_state.companions[0].health.current == game.party_state.companions[0].health.maximum
    assert game.party_state.outing_rewards.experience == 0
    assert game.party_state.outing_rewards.gold == 0


def test_outing_rewards_follow_selected_pair_and_leave_bench_unchanged():
    game = three_member_hub_game()
    party = game.party_state
    recruited_ids = tuple(
        member.character.profile.drifter_id for member in game.recruited_members
    )
    party.select_active_pair(
        ("joruun", "azhvielle"),
        recruited_ids=recruited_ids,
    )
    active_members = game.active_party_members
    benched = game.member_for_drifter_id("branoc")
    benched_before = benched.snapshot()
    active_xp_before = tuple(member.exp_state.current for member in active_members)

    party.start_floor_one_run()
    party.add_floor_one_rewards(experience=120, gold=9)
    assert party.complete_floor_one_boss(active_members)

    assert tuple(member.exp_state.current for member in active_members) == tuple(
        value + 60 for value in active_xp_before
    )
    assert benched.snapshot() == benched_before


@pytest.mark.parametrize(
    ("failure_point", "error_type"),
    (
        ("enemy", RuntimeError),
        ("battle", RuntimeError),
        ("battle", MemoryError),
    ),
)
def test_ready_failure_restores_party_state_when_construction_raises(
    failure_point, error_type
):
    game = game_at_hub()
    def fail_battle_construction(player, _enemies, **kwargs):
        if failure_point == "battle":
            companion = kwargs["party"][0]
            player.health.take_damage(7)
            player.mana_resource.spend(3)
            player.super_resource.gain(8)
            companion.health.take_damage(11)
            companion.mana_resource.spend(5)
            companion.super_resource.gain(13)
            companion.character_run_state.prepare_infusion(
                InfusionKind.FIRE,
                FIRE_INFUSION_REQUIREMENTS,
            )
        raise error_type("injected construction failure")

    def fail_enemy_construction(*_args, **_kwargs):
        raise error_type("injected construction failure")

    session = OverworldSession(
        game,
        battle_factory=fail_battle_construction,
        enemy_factory=(
            fail_enemy_construction
            if failure_point == "enemy"
            else create_enemy_state
        ),
    )
    session.submit(ChooseOverworldAction(OverworldAction.RECRUIT_COMPANION))
    session.submit(ChooseCompanion("zhaivra", "floor_one_d2_recruitment"))
    party_members = (game.player_state, *game.party_state.companions)
    checkpoints = tuple(
        member.create_battle_checkpoint() for member in party_members
    )

    with pytest.raises(error_type, match="injected construction failure"):
        session.submit(ChooseOverworldAction(OverworldAction.READY))

    assert game.party_state.phase is DungeonPhase.PARTY_READY
    assert session.active_battle is None
    assert session._active_battle_context is None
    assert tuple(
        member.create_battle_checkpoint() for member in party_members
    ) == checkpoints
    assert any(
        option.action is OverworldAction.READY and option.enabled
        for option in session.current_view().options
    )


def test_ready_factory_returning_no_battle_does_not_leave_an_outing_or_context():
    game = game_at_hub()
    session = OverworldSession(
        game,
        battle_factory=lambda *_args, **_kwargs: None,
        enemy_factory=create_enemy_state,
    )
    session.submit(ChooseOverworldAction(OverworldAction.RECRUIT_COMPANION))
    session.submit(ChooseCompanion("azhvielle", "floor_one_d2_recruitment"))

    view = session.submit(ChooseOverworldAction(OverworldAction.READY))

    assert view.screen.value == "party_ready"
    assert game.party_state.phase is DungeonPhase.PARTY_READY
    assert session.active_battle is None
    assert session._active_battle_context is None


@pytest.mark.parametrize(
    ("state_name", "expected_screen", "expected_location", "text_fragment"),
    (
        ("surface", "main", "Goblin Ambush", "road through Ketlyv"),
        ("hub", "hub", "Floor 1 Hub", "Recruit one companion"),
        ("party_ready", "hub", "Floor 1 Hub", "ready to set out"),
        ("extraction", "extraction", "Floor 1 Hub", "Return to the hub"),
        (
            "completed_hub",
            "hub",
            "Floor 1 Hub",
            "returned to the Floor 1 Hub",
        ),
    ),
)
def test_load_restores_phase_screen_narrative_and_load_notice(
    tmp_path, state_name, expected_screen, expected_location, text_fragment
):
    if state_name == "surface":
        saved_game = GameState(
            PlayerState(catalog.get_drifter_spec("branoc").create_character())
        )
    else:
        saved_game = game_at_hub()
        if state_name in {"party_ready", "extraction", "completed_hub"}:
            setup = OverworldSession(
                saved_game,
                battle_factory=lambda player, enemies, **kwargs: Battle(
                    player, enemies, rng=StableRng(), **kwargs
                ),
                enemy_factory=lambda archetype_id, tier=0: create_enemy_state(
                    archetype_id, tier=tier
                ),
            )
            setup.submit(
                ChooseOverworldAction(OverworldAction.RECRUIT_COMPANION)
            )
            setup.submit(
                ChooseCompanion("azhvielle", "floor_one_d2_recruitment")
            )
            if state_name in {"extraction", "completed_hub"}:
                setup.submit(ChooseOverworldAction(OverworldAction.READY))
                for enemy in setup.active_battle.enemies:
                    enemy.health.take_damage(enemy.health.current)
                setup.submit(ChooseAction(ActionIntent.DEFEND))
                if state_name == "completed_hub":
                    setup.submit(
                        ChooseOverworldAction(OverworldAction.RETURN_TO_HUB)
                    )

    save_port = make_test_save_port(tmp_path / f"{state_name}.json")
    assert save_port.save(saved_game).status is SaveLoadStatus.SAVED
    session = OverworldSession(
        GameState(PlayerState(catalog.get_drifter_spec("branoc").create_character())),
        battle_factory=Battle,
        enemy_factory=create_enemy_state,
        save_port=save_port,
    )
    session.submit(ChooseOverworldAction(OverworldAction.OPTIONS))
    session.submit(ChooseOverworldAction(OverworldAction.LOAD))
    session.submit(ChooseOverworldAction(OverworldAction.CONFIRM))

    view = session.current_view()

    assert view.screen.value == expected_screen
    assert view.location_label == expected_location
    assert text_fragment in view.adventure_text
    assert view.notice == "Saved session loaded."
    if state_name == "party_ready":
        assert any(
            option.action is OverworldAction.READY and option.enabled
            for option in view.options
        )
