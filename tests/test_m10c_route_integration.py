from app.game.game_state import GameState
from app.game.overworld_session import OverworldSession, OverworldSessionResult
from app.game.overworld_state import ContextualRoutePhase
from app.player.character import Brawler
from app.player.player_state import PlayerState
from app.presentation.overworld_models import OverworldAction
from app.ui.overworld_ui import ChooseOverworldAction


class ScriptedUI:
    def __init__(self, inputs):
        self._inputs = iter(inputs)
        self.views = []

    def render(self, view):
        self.views.append(view)

    def read_input(self, _view):
        return next(self._inputs)


class StubEnemy:
    def __init__(self):
        self.alive = True

    def is_alive(self):
        return self.alive


class RouteBattleFactory:
    def __init__(self, *, winner="player", defeat_enemies=True):
        self.winner = winner
        self.defeat_enemies = defeat_enemies
        self.calls = []

    def __call__(self, player_state, enemies, *, ui):
        factory = self

        class FakeBattle:
            def __init__(self):
                self.player_state = player_state
                self.enemies = tuple(enemies)
                self.ui = ui

            def run(self):
                if factory.winner == "player" and factory.defeat_enemies:
                    for enemy in self.enemies:
                        enemy.alive = False
                return factory.winner

        battle = FakeBattle()
        self.calls.append(battle)
        return battle


class RouteEnemyFactory:
    def __init__(self):
        self.calls = []
        self.enemies = []

    def __call__(self, archetype_id, *, tier):
        enemy = StubEnemy()
        self.calls.append((archetype_id, tier))
        self.enemies.append(enemy)
        return enemy


def _quit_inputs():
    return (
        ChooseOverworldAction(OverworldAction.OPTIONS),
        ChooseOverworldAction(OverworldAction.QUIT),
        ChooseOverworldAction(OverworldAction.CONFIRM),
    )


def test_pair_route_uses_authored_tuple_advances_once_and_defers_rewards():
    player = PlayerState(Brawler(), gold=17)
    player.exp_state.gain(23)
    game = GameState(player)
    game.overworld_state.advance_to(
        "surface_goblin_pair",
        contextual_phase=ContextualRoutePhase.ENTER_ENCOUNTER,
    )
    before_exp = player.exp_state.current
    before_gold = player.gold
    enemies = RouteEnemyFactory()
    battles = RouteBattleFactory()
    ui = ScriptedUI(
        (
            ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER),
            *_quit_inputs(),
        )
    )

    result = OverworldSession(
        game,
        ui=ui,
        battle_factory=battles,
        enemy_factory=enemies,
        battle_ui_factory=object,
    ).run()

    assert result is OverworldSessionResult.QUIT
    assert enemies.calls == [("goblin", 0), ("goblin", 0)]
    assert battles.calls[0].enemies == tuple(enemies.enemies)
    assert battles.calls[0].enemies[0] is not battles.calls[0].enemies[1]
    assert game.world_state.defeated_encounters == ("surface_goblin_pair",)
    assert game.overworld_state.current_route_node_id == "surface_warrior_solo"
    assert (
        game.overworld_state.current_contextual_route_phase
        is ContextualRoutePhase.ENTER_ENCOUNTER
    )
    assert player.exp_state.current == before_exp
    assert player.gold == before_gold
    assert "Goblin Pair is defeated" in ui.views[1].adventure_text
    assert "Goblin Warrior" in ui.views[1].adventure_text


def test_victory_at_combat_before_rest_pauses_without_consuming_rest():
    game = GameState(PlayerState(Brawler()))
    game.overworld_state.advance_to("surface_goblin_pair")
    game.overworld_state.advance_to(
        "surface_warrior_solo",
        contextual_phase=ContextualRoutePhase.ENTER_ENCOUNTER,
    )
    enemies = RouteEnemyFactory()
    battles = RouteBattleFactory()
    ui = ScriptedUI(
        (
            ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER),
            *_quit_inputs(),
        )
    )

    OverworldSession(
        game,
        ui=ui,
        battle_factory=battles,
        enemy_factory=enemies,
        battle_ui_factory=object,
    ).run()

    assert game.overworld_state.current_route_node_id == (
        "surface_rest_after_warrior_solo"
    )
    assert game.overworld_state.current_contextual_route_phase is ContextualRoutePhase.NONE
    assert game.overworld_state.resolved_rest_node_ids == ()
    assert ui.views[1].contextual_route_option is None


def test_reported_victory_with_living_enemy_fails_before_route_mutation():
    game = GameState(PlayerState(Brawler()))
    enemies = RouteEnemyFactory()
    battles = RouteBattleFactory(defeat_enemies=False)
    ui = ScriptedUI((ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER),))

    session = OverworldSession(
        game,
        ui=ui,
        battle_factory=battles,
        enemy_factory=enemies,
        battle_ui_factory=object,
    )

    try:
        session.run()
    except RuntimeError as error:
        assert str(error) == "Battle reported victory before every enemy was defeated"
    else:
        raise AssertionError("reported victory with a living enemy must fail")

    assert game.world_state.defeated_encounters == ()
    assert game.overworld_state.current_route_node_id == "surface_goblin_solo"
