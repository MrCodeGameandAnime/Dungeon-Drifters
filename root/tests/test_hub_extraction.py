from app.combat.battle import Battle
from app.content.catalog import create_enemy_state
from app.game.game_state import GameState
from app.game.overworld_session import OverworldSession, OverworldSessionResult
from app.game.overworld_state import OverworldState
from app.game.party_state import DungeonPhase
from app.persistence.save_document import build_save_document, reconstruct_game_state
from app.player.player_state import PlayerState
from app.presentation.battle_models import ActionIntent, BattleView, InteractionPhase
from app.presentation.overworld_models import OverworldAction
from app.ui.battle_ui import ChooseAction, GoBack
from app.ui.overworld_ui import ChooseCompanion, ChooseOverworldAction
from app.content.catalog import get_route_spec
from app.content import catalog


class StableRng:
    def randint(self, _minimum, _maximum):
        return 1

    def choice(self, values):
        return values[0]


def game_at_hub():
    lead = PlayerState(catalog.get_drifter_spec("branoc").create_character(), gold=75)
    game = GameState(lead)
    route = get_route_spec("surface")
    entrance = route.nodes[-1]
    for node in route.nodes[:-1]:
        if node.encounter_id is not None:
            game.world_state.mark_encounter_defeated(node.encounter_id)
    rests = tuple(
        node.node_id for node in route.nodes[:-1] if node.kind.value == "rest"
    )
    game._overworld_state = OverworldState.from_snapshot(
        {
            "current_route_node_id": entrance.node_id,
            "surface_route_begun": True,
            "dungeon_entrance_reached": True,
            "route_complete": True,
            "resolved_rest_node_ids": list(rests),
            "current_contextual_route_phase": "none",
        }
    )
    assert game.party_state.arrive_at_hub(lead)
    return game


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
    session.submit(ChooseCompanion("azhvielle"))
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
    assert extraction.outing_rewards.items == ()
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
    assert reloaded.party_state.shared_gold == 10
    assert reloaded.player_state.exp_state.current == 0


def test_tutorial_defeat_discards_attempt_and_returns_to_drifter_selection():
    game, session, _ = ready_party()
    for member in (game.player_state, *game.party_state.companions):
        member.health.take_damage(member.health.current)
    session.active_battle._finish("enemy")

    result = session.submit(GoBack())

    assert result is OverworldSessionResult.SELECT_DRIFTER
    assert game.party_state.phase is DungeonPhase.OUTSIDE
    assert game.party_state.companions == ()
    assert game.party_state.outing_rewards.experience == 0
    assert game.party_state.outing_rewards.gold == 0
