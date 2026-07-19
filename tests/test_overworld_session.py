from app.game.game_state import GameState
from app.game.overworld_route import FIRST_SURFACE_NODE_ID, SECOND_SURFACE_NODE_ID
from app.game.overworld_state import ContextualRoutePhase
from app.player.character import Brawler, RogueArcher
from app.player.character_run_state import (
    FIRE_INFUSION_REQUIREMENTS,
    InfusionKind,
    PreparedPayloadId,
    RunItemId,
)
from app.player.player_state import PlayerState
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.presentation.overworld_presenter import OverworldPresenter
from app.ui.overworld_ui import ChooseOverworldAction, ChooseOverworldItem
from app.game.overworld_session import OverworldSession, OverworldSessionResult


class ScriptedUI:
    def __init__(self, inputs):
        self.inputs = list(inputs)
        self.views = []

    def render(self, view):
        self.views.append(view)

    def read_input(self, view):
        if not self.inputs:
            raise AssertionError("the session requested unexpected input")
        return self.inputs.pop(0)


class BattleHarness:
    def __init__(self, winners, mutations=()):
        self.winners = list(winners)
        self.mutations = list(mutations)
        self.instances = []

    def factory(self, player_state, enemy, *, ui):
        index = len(self.instances)
        harness = self

        class FakeBattle:
            def __init__(self):
                self.player_state = player_state
                self.enemy = enemy
                self.ui = ui

            def run(self):
                if index < len(harness.mutations):
                    harness.mutations[index](self.player_state)
                return harness.winners[index]

        battle = FakeBattle()
        self.instances.append(battle)
        return battle


class EnemyFactory:
    def __init__(self):
        self.calls = []
        self.enemies = []

    def __call__(self, archetype_id, *, tier):
        enemy = object()
        self.calls.append((archetype_id, tier))
        self.enemies.append(enemy)
        return enemy


class BattleUIFactory:
    def __init__(self):
        self.instances = []

    def __call__(self):
        instance = object()
        self.instances.append(instance)
        return instance


def run_session(game, inputs, winners=(), mutations=()):
    ui = ScriptedUI(inputs)
    battles = BattleHarness(winners, mutations)
    enemies = EnemyFactory()
    battle_uis = BattleUIFactory()
    session = OverworldSession(
        game,
        ui=ui,
        battle_factory=battles.factory,
        enemy_factory=enemies,
        battle_ui_factory=battle_uis,
    )
    result = session.run()
    return result, ui, battles, enemies, battle_uis


def quit_inputs():
    return [
        ChooseOverworldAction(OverworldAction.OPTIONS),
        ChooseOverworldAction(OverworldAction.QUIT),
        ChooseOverworldAction(OverworldAction.CONFIRM),
    ]


def test_navigation_covers_every_shell_and_back_returns_one_level():
    game = GameState(PlayerState(Brawler()))
    inputs = [
        ChooseOverworldAction(OverworldAction.CHARACTER),
        ChooseOverworldAction(OverworldAction.SKILLS),
        ChooseOverworldAction(OverworldAction.BACK),
        ChooseOverworldAction(OverworldAction.WEAPON),
        ChooseOverworldAction(OverworldAction.BACK),
        ChooseOverworldAction(OverworldAction.EQUIPMENT),
        ChooseOverworldAction(OverworldAction.BACK),
        ChooseOverworldAction(OverworldAction.BACK),
        ChooseOverworldAction(OverworldAction.ITEMS),
        ChooseOverworldAction(OverworldAction.BACK),
        ChooseOverworldAction(OverworldAction.MAP),
        ChooseOverworldAction(OverworldAction.BACK),
        *quit_inputs(),
    ]

    result, ui, battles, enemies, _ = run_session(game, inputs)

    assert result is OverworldSessionResult.QUIT
    assert [view.screen for view in ui.views] == [
        OverworldScreen.MAIN,
        OverworldScreen.CHARACTER,
        OverworldScreen.SKILLS,
        OverworldScreen.CHARACTER,
        OverworldScreen.WEAPON,
        OverworldScreen.CHARACTER,
        OverworldScreen.EQUIPMENT,
        OverworldScreen.CHARACTER,
        OverworldScreen.MAIN,
        OverworldScreen.ITEMS,
        OverworldScreen.MAIN,
        OverworldScreen.MAP,
        OverworldScreen.MAIN,
        OverworldScreen.OPTIONS,
        OverworldScreen.QUIT_CONFIRMATION,
    ]
    assert battles.instances == []
    assert enemies.calls == []


def test_item_selection_and_inspection_are_transient_and_non_consuming():
    game = GameState(PlayerState(RogueArcher()))
    initial_view = OverworldPresenter().build(
        game,
        screen=OverworldScreen.ITEMS,
    )
    ember = initial_view.inventory.items[0]
    before = game.snapshot()
    inputs = [
        ChooseOverworldAction(OverworldAction.ITEMS),
        ChooseOverworldItem(ember.selection_key),
        ChooseOverworldAction(OverworldAction.INSPECT),
        ChooseOverworldAction(OverworldAction.BACK),
        ChooseOverworldAction(OverworldAction.BACK),
        *quit_inputs(),
    ]

    _, ui, _, _, _ = run_session(game, inputs)

    item_views = [view for view in ui.views if view.screen is OverworldScreen.ITEMS]
    inspection = next(
        view for view in ui.views if view.screen is OverworldScreen.ITEM_INSPECT
    )
    assert item_views[-1].inventory.selected_item_key == ember.selection_key
    assert inspection.inventory.inspected_item.display_name == "Ember Shard"
    assert game.snapshot() == before


def test_victory_preserves_battle_mutations_and_advances_to_paused_pair_node():
    player = PlayerState(RogueArcher())
    game = GameState(player)
    identities = (
        player,
        player.character,
        player.health,
        player.mana_resource,
        player.super_resource,
        player.inventory,
        player.character_run_state,
        player.get_equipped("weapon"),
    )

    def mutate(acting_player):
        acting_player.health.take_damage(12)
        acting_player.mana_resource.spend(5)
        acting_player.super_resource.gain(20)
        acting_player.character_run_state.prepare_infusion(
            InfusionKind.FIRE,
            FIRE_INFUSION_REQUIREMENTS,
        )

    inputs = [
        ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER),
        *quit_inputs(),
    ]
    result, ui, battles, enemies, battle_uis = run_session(
        game,
        inputs,
        winners=("player",),
        mutations=(mutate,),
    )

    assert result is OverworldSessionResult.QUIT
    assert battles.instances[0].player_state is player
    assert enemies.calls == [("goblin", 0)]
    assert battles.instances[0].enemy is enemies.enemies[0]
    assert battles.instances[0].ui is battle_uis.instances[0]
    assert player.health.current == player.health.maximum - 12
    assert player.mana_resource.current == player.mana_resource.maximum - 5
    assert player.super_resource.current == 20
    assert player.character_run_state.payload_prepared(
        PreparedPayloadId.INFUSED_BARB
    ) is True
    assert game.world_state.defeated_encounters == (FIRST_SURFACE_NODE_ID,)
    assert game.overworld_state.current_route_node_id == SECOND_SURFACE_NODE_ID
    assert game.overworld_state.current_contextual_route_phase is ContextualRoutePhase.NONE
    post_victory = ui.views[1]
    assert post_victory.location_label == "Goblin Pair"
    assert post_victory.contextual_route_option is None
    assert identities == (
        player,
        player.character,
        player.health,
        player.mana_resource,
        player.super_resource,
        player.inventory,
        player.character_run_state,
        player.get_equipped("weapon"),
    )


def test_defeat_restores_values_in_place_and_exposes_retry_without_advancing():
    player = PlayerState(RogueArcher())
    game = GameState(player)
    character = player.character
    run_state = player.character_run_state

    def mutate(acting_player):
        acting_player.health.take_damage(33)
        acting_player.mana_resource.spend(8)
        acting_player.super_resource.gain(50)
        acting_player.character_run_state.prepare_infusion(
            InfusionKind.FIRE,
            FIRE_INFUSION_REQUIREMENTS,
        )

    inputs = [
        ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER),
        *quit_inputs(),
    ]
    _, ui, _, _, _ = run_session(
        game,
        inputs,
        winners=("enemy",),
        mutations=(mutate,),
    )

    assert player.character is character
    assert player.character_run_state is run_state
    assert player.health.current == player.health.maximum
    assert player.mana_resource.current == player.mana_resource.maximum
    assert player.super_resource.current == 0
    assert player.character_run_state.item_quantity(RunItemId.EMBER_SHARD) == 1
    assert player.character_run_state.payload_prepared(
        PreparedPayloadId.INFUSED_BARB
    ) is False
    assert game.world_state.defeated_encounters == ()
    assert game.overworld_state.current_route_node_id == FIRST_SURFACE_NODE_ID
    assert game.overworld_state.current_contextual_route_phase is ContextualRoutePhase.RETRY
    assert (
        ui.views[1].contextual_route_option.action
        is OverworldAction.RETRY
    )


def test_retry_creates_a_fresh_enemy_and_victory_cannot_replay_first_encounter():
    game = GameState(PlayerState(Brawler()))
    inputs = [
        ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER),
        ChooseOverworldAction(OverworldAction.RETRY),
        *quit_inputs(),
    ]

    _, _, battles, enemies, _ = run_session(
        game,
        inputs,
        winners=("enemy", "player"),
    )

    assert len(battles.instances) == 2
    assert len(enemies.enemies) == 2
    assert enemies.enemies[0] is not enemies.enemies[1]
    assert game.world_state.defeated_encounters == (FIRST_SURFACE_NODE_ID,)
    assert game.overworld_state.current_contextual_route_phase is ContextualRoutePhase.NONE


def test_quit_confirmation_is_transient_cancelable_and_does_not_autosave():
    game = GameState(PlayerState(Brawler()))
    before = game.snapshot()
    inputs = [
        ChooseOverworldAction(OverworldAction.OPTIONS),
        ChooseOverworldAction(OverworldAction.QUIT),
        ChooseOverworldAction(OverworldAction.CANCEL),
        ChooseOverworldAction(OverworldAction.BACK),
        *quit_inputs(),
    ]

    _, ui, _, _, _ = run_session(game, inputs)

    assert [view.screen for view in ui.views][-5:] == [
        OverworldScreen.QUIT_CONFIRMATION,
        OverworldScreen.OPTIONS,
        OverworldScreen.MAIN,
        OverworldScreen.OPTIONS,
        OverworldScreen.QUIT_CONFIRMATION,
    ]
    assert game.snapshot() == before
    assert "confirmation" not in repr(game.snapshot()).lower()
