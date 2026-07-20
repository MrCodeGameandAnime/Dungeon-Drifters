from app.game.game_state import GameState
import pytest

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

    def __call__(self, player_state, enemies, *, ui, encounter_label=None):
        factory = self

        class FakeBattle:
            def __init__(self):
                self.player_state = player_state
                self.enemies = tuple(enemies)
                self.ui = ui
                self.encounter_label = encounter_label

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


def test_pair_route_uses_authored_tuple_advances_once_and_applies_rewards():
    player = PlayerState(Brawler(), gold=17)
    player.exp_state.gain(23)
    game = GameState(player)
    game.overworld_state.advance_to(
        "surface_goblin_pair",
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
    assert battles.calls[0].encounter_label == "Goblin Pair"
    assert battles.calls[0].enemies[0] is not battles.calls[0].enemies[1]
    assert "Goblin Pair awaits along the surface route." in ui.views[0].adventure_text
    assert game.world_state.defeated_encounters == ("surface_goblin_pair",)
    assert game.overworld_state.current_route_node_id == "surface_warrior_solo"
    assert (
        game.overworld_state.current_contextual_route_phase
        is ContextualRoutePhase.ENTER_ENCOUNTER
    )
    assert player.level_state.current == 2
    assert player.exp_state.current == 3
    assert player.growth_points == 3
    assert player.gold == 23
    assert ui.views[1].adventure_text == (
        "Goblin Pair is defeated. Rewards: 80 EXP and 6 gold. "
        "Level up! Reached Level 2 and gained 3 Growth Points. "
        "The route continues toward Goblin Warrior."
    )


def test_duplicate_completion_raises_without_reward_or_route_mutation():
    player = PlayerState(Brawler(), gold=11)
    player.exp_state.gain(37)
    game = GameState(player)
    game.overworld_state.begin_surface_route()
    game.world_state.mark_encounter_defeated("surface_goblin_solo")
    before_player = player.snapshot()
    before_overworld = game.overworld_state.snapshot()
    before_world = game.world_state.snapshot()
    enemies = RouteEnemyFactory()
    battles = RouteBattleFactory()
    ui = ScriptedUI((ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER),))

    with pytest.raises(RuntimeError, match="already been defeated"):
        OverworldSession(
            game,
            ui=ui,
            battle_factory=battles,
            enemy_factory=enemies,
            battle_ui_factory=object,
        ).run()

    assert player.snapshot() == before_player
    assert game.overworld_state.snapshot() == before_overworld
    assert game.world_state.snapshot() == before_world


def test_victory_at_combat_before_rest_pauses_without_consuming_rest():
    player = PlayerState(Brawler(), gold=31)
    player.exp_state.gain(19)
    game = GameState(player)
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
    assert ui.views[1].adventure_text == (
        "Goblin Warrior is defeated. Rewards: 60 EXP and 5 gold. "
        "The route continues toward Woodland Rest."
    )
    assert player.exp_state.current == 79
    assert player.level_state.current == 1
    assert player.growth_points == 0
    assert player.gold == 36


def test_reported_victory_with_living_enemy_fails_before_route_mutation():
    player = PlayerState(Brawler(), gold=11)
    player.exp_state.gain(13)
    before_player = player.snapshot()
    game = GameState(player)
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
    assert player.snapshot() == before_player


def test_goblin_lord_victory_reaches_dungeon_with_rewards_and_without_continuation():
    player = PlayerState(Brawler(), gold=47)
    player.exp_state.gain(61)
    player.health.take_damage(11)
    assert player.mana_resource.spend(3) is True
    player.super_resource.gain(14)
    equipped_weapon = player.get_equipped("weapon")
    before_health = player.health.current
    before_mana = player.mana_resource.current
    before_super = player.super_resource.current
    game = GameState(player)
    for node_id, phase in (
        ("surface_goblin_pair", ContextualRoutePhase.NONE),
        ("surface_warrior_solo", ContextualRoutePhase.ENTER_ENCOUNTER),
        ("surface_rest_after_warrior_solo", ContextualRoutePhase.NONE),
        ("surface_warrior_pair", ContextualRoutePhase.ENTER_ENCOUNTER),
        ("surface_shaman_solo", ContextualRoutePhase.ENTER_ENCOUNTER),
        ("surface_shaman_pair", ContextualRoutePhase.ENTER_ENCOUNTER),
        ("surface_rest_after_shaman_pair", ContextualRoutePhase.NONE),
        ("surface_elite_patrol", ContextualRoutePhase.ENTER_ENCOUNTER),
        ("surface_rest_before_goblin_lord", ContextualRoutePhase.NONE),
        ("surface_goblin_lord", ContextualRoutePhase.ENTER_ENCOUNTER),
    ):
        game.overworld_state.advance_to(node_id, contextual_phase=phase)
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
    assert enemies.calls == [
        ("goblin_lord", 0),
        ("goblin", 0),
        ("goblin_warrior", 0),
    ]
    assert battles.calls[0].player_state is player
    assert battles.calls[0].enemies == tuple(enemies.enemies)
    assert battles.calls[0].encounter_label == "Goblin Lord"
    assert game.world_state.defeated_encounters == ("surface_goblin_lord",)
    assert game.overworld_state.current_route_node_id == "surface_dungeon_entrance"
    assert game.overworld_state.dungeon_entrance_reached is True
    assert game.overworld_state.route_complete is True
    assert game.overworld_state.current_contextual_route_phase is ContextualRoutePhase.NONE
    assert game.overworld_state.resolved_rest_node_ids == ()
    assert ui.views[1].contextual_route_option is None
    assert ui.views[1].adventure_text == (
        "Goblin Lord is defeated. Rewards: 300 EXP and 18 gold. "
        "Level up! Gained 3 levels, reached Level 4, and gained 9 Growth Points. "
        "The route continues toward Dungeon Entrance."
    )
    assert player.exp_state.current == 42
    assert player.level_state.current == 4
    assert player.growth_points == 9
    assert player.gold == 65
    assert player.health.current == before_health + 12
    assert player.mana_resource.current == before_mana + 3
    assert player.super_resource.current == before_super
    assert player.get_equipped("weapon") is equipped_weapon
