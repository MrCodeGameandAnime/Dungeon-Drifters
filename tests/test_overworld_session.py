import pytest

from app.game.game_state import GameState
from app.game.overworld_route import FIRST_SURFACE_NODE_ID, SECOND_SURFACE_NODE_ID
from app.game.overworld_state import ContextualRoutePhase
from app.player.character import Brawler, RogueArcher
from app.player.character_run_state import (
    CharacterRunCheckpoint,
    FIRE_INFUSION_REQUIREMENTS,
    InfusionKind,
    PreparedPayloadId,
    RunItemId,
)
from app.player.player_state import PlayerState
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.presentation.overworld_presenter import OverworldPresenter
from app.ui.overworld_ui import (
    ChooseOverworldAction,
    ChooseOverworldItem,
    ChoosePermanentStatIncrease,
)
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

    def factory(self, player_state, enemy, *, ui, encounter_label=None):
        index = len(self.instances)
        harness = self

        class FakeBattle:
            def __init__(self):
                self.player_state = player_state
                self.enemies = tuple(enemy)
                self.enemy = self.enemies
                self.ui = ui
                self.encounter_label = encounter_label

            def run(self):
                if index < len(harness.mutations):
                    harness.mutations[index](self.player_state)
                if harness.winners[index] == "player":
                    for enemy in self.enemies:
                        enemy.alive = False
                return harness.winners[index]

        battle = FakeBattle()
        self.instances.append(battle)
        return battle


class EnemyFactory:
    def __init__(self):
        self.calls = []
        self.enemies = []

    def __call__(self, archetype_id, *, tier):
        enemy = StubEnemy()
        self.calls.append((archetype_id, tier))
        self.enemies.append(enemy)
        return enemy


class StubEnemy:
    def __init__(self):
        self.alive = True

    def is_alive(self):
        return self.alive


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


def move_to_woodland_rest(game):
    game.overworld_state.advance_to(SECOND_SURFACE_NODE_ID)
    game.overworld_state.advance_to(
        "surface_warrior_solo",
        contextual_phase=ContextualRoutePhase.ENTER_ENCOUNTER,
    )
    game.overworld_state.advance_to("surface_rest_after_warrior_solo")


def test_rest_fully_recovers_without_changing_unrelated_player_state():
    player = PlayerState(RogueArcher(), gold=17)
    player.gain_experience(140)
    player.increase_permanent_stat("strength")
    player.health.take_damage(23)
    player.mana_resource.spend(8)
    player.super_resource.gain(31)
    signature_weapon = player.get_equipped("weapon")
    player.inventory.add_item(signature_weapon)
    player.character_run_state.prepare_infusion(
        InfusionKind.FIRE,
        FIRE_INFUSION_REQUIREMENTS,
    )
    game = GameState(player)
    game.world_state.mark_encounter_defeated(FIRST_SURFACE_NODE_ID)
    game.world_state.mark_encounter_defeated(SECOND_SURFACE_NODE_ID)
    game.world_state.mark_encounter_defeated("surface_warrior_solo")
    move_to_woodland_rest(game)
    before = {
        "super": player.super_resource.current,
        "exp": player.exp_state.current,
        "level": player.level_state.current,
        "growth_points": player.growth_points,
        "gold": player.gold,
        "equipment": player.equipment,
        "inventory": player.inventory,
        "run_state": player.character_run_state,
        "prepared": player.character_run_state.prepared_infusion(),
    }

    result, ui, battles, _, _ = run_session(
        game,
        [
            ChooseOverworldAction(OverworldAction.REST),
            ChooseOverworldAction(OverworldAction.REST),
            *quit_inputs(),
        ],
    )

    assert result is OverworldSessionResult.QUIT
    assert battles.instances == []
    assert ui.views[1].screen is OverworldScreen.REST
    assert player.health.current == player.health.maximum
    assert player.mana_resource.current == player.mana_resource.maximum
    assert player.super_resource.current == before["super"]
    assert player.exp_state.current == before["exp"]
    assert player.level_state.current == before["level"]
    assert player.growth_points == before["growth_points"]
    assert player.gold == before["gold"]
    assert player.equipment == before["equipment"]
    assert player.inventory is before["inventory"]
    assert player.character_run_state is before["run_state"]
    assert player.character_run_state.prepared_infusion() is before["prepared"]
    assert game.world_state.defeated_encounters == (
        FIRST_SURFACE_NODE_ID,
        SECOND_SURFACE_NODE_ID,
        "surface_warrior_solo",
    )
    assert game.overworld_state.resolved_rest_node_ids == (
        "surface_rest_after_warrior_solo",
    )
    assert game.overworld_state.current_route_node_id == "surface_warrior_pair"
    assert ui.views[-1].adventure_text == (
        "You rest at Woodland Rest. HP and Mana are fully restored. "
        "The route continues toward Warrior Patrol."
    )


def test_skip_rest_consumes_node_without_recovery():
    player = PlayerState(Brawler())
    player.health.take_damage(12)
    player.mana_resource.spend(4)
    game = GameState(player)
    move_to_woodland_rest(game)
    before = (player.health.current, player.mana_resource.current)

    result, ui, battles, _, _ = run_session(
        game,
        [
            ChooseOverworldAction(OverworldAction.REST),
            ChooseOverworldAction(OverworldAction.SKIP_REST),
            *quit_inputs(),
        ],
    )

    assert result is OverworldSessionResult.QUIT
    assert battles.instances == []
    assert (player.health.current, player.mana_resource.current) == before
    assert game.overworld_state.resolved_rest_node_ids == (
        "surface_rest_after_warrior_solo",
    )
    assert game.overworld_state.current_route_node_id == "surface_warrior_pair"
    assert ui.views[-1].adventure_text == (
        "You continue from Woodland Rest without resting. "
        "The route continues toward Warrior Patrol."
    )


def test_rest_menu_save_and_quit_cancel_preserve_unresolved_node():
    game = GameState(PlayerState(Brawler()))
    move_to_woodland_rest(game)

    result, ui, _, _, _ = run_session(
        game,
        [
            ChooseOverworldAction(OverworldAction.REST),
            ChooseOverworldAction(OverworldAction.MENU),
            ChooseOverworldAction(OverworldAction.REST),
            ChooseOverworldAction(OverworldAction.SAVE),
            ChooseOverworldAction(OverworldAction.QUIT),
            ChooseOverworldAction(OverworldAction.CANCEL),
            ChooseOverworldAction(OverworldAction.SKIP_REST),
            *quit_inputs(),
        ],
    )

    assert result is OverworldSessionResult.QUIT
    assert game.overworld_state.resolved_rest_node_ids == (
        "surface_rest_after_warrior_solo",
    )
    assert [view.screen for view in ui.views[:7]] == [
        OverworldScreen.MAIN,
        OverworldScreen.REST,
        OverworldScreen.MAIN,
        OverworldScreen.REST,
        OverworldScreen.REST,
        OverworldScreen.QUIT_CONFIRMATION,
        OverworldScreen.REST,
    ]
    assert ui.views[1].options[1].enabled is False


def test_rest_quit_confirmation_does_not_recover_or_consume_node():
    player = PlayerState(Brawler())
    player.health.take_damage(12)
    player.mana_resource.spend(4)
    game = GameState(player)
    move_to_woodland_rest(game)
    before_resources = (player.health.current, player.mana_resource.current)

    result, ui, battles, _, _ = run_session(
        game,
        [
            ChooseOverworldAction(OverworldAction.REST),
            ChooseOverworldAction(OverworldAction.QUIT),
            ChooseOverworldAction(OverworldAction.CONFIRM),
        ],
    )

    assert result is OverworldSessionResult.QUIT
    assert battles.instances == []
    assert (player.health.current, player.mana_resource.current) == before_resources
    assert game.overworld_state.current_route_node_id == (
        "surface_rest_after_warrior_solo"
    )
    assert game.overworld_state.resolved_rest_node_ids == ()
    assert ui.views[-1].screen is OverworldScreen.QUIT_CONFIRMATION


@pytest.mark.parametrize(
    "stale_action",
    (OverworldAction.REST, OverworldAction.SKIP_REST),
)
def test_stale_rest_actions_cannot_resolve_or_recover_again(stale_action):
    player = PlayerState(Brawler(), gold=9)
    player.health.take_damage(12)
    player.mana_resource.spend(4)
    player.super_resource.gain(19)
    player.gain_experience(40)
    game = GameState(player)
    move_to_woodland_rest(game)
    rest_node_id = game.overworld_state.current_route_node_id
    before = {
        "health": player.health.current,
        "mana": player.mana_resource.current,
        "super": player.super_resource.current,
        "exp": player.exp_state.current,
        "gold": player.gold,
        "resolved": game.overworld_state.resolved_rest_node_ids,
    }

    class StaleRestUI(ScriptedUI):
        def __init__(self):
            super().__init__(
                [
                    ChooseOverworldAction(OverworldAction.REST),
                    ChooseOverworldAction(OverworldAction.QUIT),
                    ChooseOverworldAction(OverworldAction.CONFIRM),
                ]
            )
            self.injected = False

        def read_input(self, view):
            if view.screen is OverworldScreen.REST and not self.injected:
                game.overworld_state.record_resolved_rest_node(rest_node_id)
                game.overworld_state.advance_to("surface_warrior_pair")
                self.injected = True
                return ChooseOverworldAction(stale_action)
            return super().read_input(view)

    ui = StaleRestUI()
    session = OverworldSession(
        game,
        ui=ui,
        battle_factory=BattleHarness(()).factory,
        enemy_factory=EnemyFactory(),
        battle_ui_factory=BattleUIFactory(),
    )

    result = session.run()

    assert result is OverworldSessionResult.QUIT
    assert player.health.current == before["health"]
    assert player.mana_resource.current == before["mana"]
    assert player.super_resource.current == before["super"]
    assert player.exp_state.current == before["exp"]
    assert player.gold == before["gold"]
    assert game.overworld_state.resolved_rest_node_ids == (rest_node_id,)
    assert game.overworld_state.current_route_node_id == "surface_warrior_pair"
    assert ui.views[2].notice == "That Rest is not available."
    assert ui.views[2].screen is OverworldScreen.REST


def test_rest_is_rejected_at_a_combat_node_without_mutation():
    game = GameState(PlayerState(Brawler()))
    before = game.snapshot()

    result, ui, battles, _, _ = run_session(
        game,
        [
            ChooseOverworldAction(OverworldAction.REST),
            *quit_inputs(),
        ],
    )

    assert result is OverworldSessionResult.QUIT
    assert battles.instances == []
    assert game.snapshot() == before
    assert ui.views[1].notice == "That option is not available."


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
        ChooseOverworldAction(OverworldAction.INSPECT),
        ChooseOverworldAction(OverworldAction.BACK),
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
        OverworldScreen.MAP_INSPECT,
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


def test_skills_stat_input_delegates_growth_and_stays_on_skills():
    player = PlayerState(Brawler())
    player.gain_experience(100)
    game = GameState(player)
    strength_before = player.character.permanent_stats.strength

    inputs = [
        ChooseOverworldAction(OverworldAction.CHARACTER),
        ChooseOverworldAction(OverworldAction.SKILLS),
        ChoosePermanentStatIncrease("strength"),
        ChooseOverworldAction(OverworldAction.BACK),
        ChooseOverworldAction(OverworldAction.BACK),
        *quit_inputs(),
    ]

    result, ui, _, _, _ = run_session(game, inputs)

    assert result is OverworldSessionResult.QUIT
    assert player.character.permanent_stats.strength == strength_before + 1
    assert player.growth_points == 2
    skills_views = [
        view
        for view in ui.views
        if view.screen is OverworldScreen.SKILLS
    ]
    assert skills_views[-1].notice == (
        "Strength increased to "
        f"{strength_before + 1}. Growth Points remaining: 2."
    )
    assert [view.screen for view in ui.views[:4]] == [
        OverworldScreen.MAIN,
        OverworldScreen.CHARACTER,
        OverworldScreen.SKILLS,
        OverworldScreen.SKILLS,
    ]


def test_disabled_or_offscreen_stat_input_changes_nothing():
    player = PlayerState(Brawler())
    game = GameState(player)
    before = game.snapshot()
    inputs = [
        ChoosePermanentStatIncrease("strength"),
        ChooseOverworldAction(OverworldAction.OPTIONS),
        ChooseOverworldAction(OverworldAction.QUIT),
        ChooseOverworldAction(OverworldAction.CONFIRM),
    ]

    result, ui, _, _, _ = run_session(game, inputs)

    assert result is OverworldSessionResult.QUIT
    assert game.snapshot() == before
    assert ui.views[1].notice == "That stat is not available."

    player = PlayerState(Brawler())
    game = GameState(player)
    before = game.snapshot()
    inputs = [
        ChooseOverworldAction(OverworldAction.CHARACTER),
        ChooseOverworldAction(OverworldAction.SKILLS),
        ChoosePermanentStatIncrease("strength"),
        ChooseOverworldAction(OverworldAction.BACK),
        ChooseOverworldAction(OverworldAction.BACK),
        *quit_inputs(),
    ]

    result, ui, _, _, _ = run_session(game, inputs)

    assert result is OverworldSessionResult.QUIT
    assert game.snapshot() == before
    assert ui.views[3].notice == "Earn Growth Points by leveling up."


def test_stale_enabled_stat_input_is_rejected_after_points_are_spent():
    player = PlayerState(Brawler())
    player.gain_experience(100)
    game = GameState(player)
    initial_strength = player.character.permanent_stats.strength
    initial_hp = player.health.current
    initial_mana = player.mana_resource.current

    class StaleSkillsUI(ScriptedUI):
        def __init__(self):
            super().__init__(
                [
                    ChooseOverworldAction(OverworldAction.CHARACTER),
                    ChooseOverworldAction(OverworldAction.SKILLS),
                    ChooseOverworldAction(OverworldAction.BACK),
                    ChooseOverworldAction(OverworldAction.BACK),
                    *quit_inputs(),
                ]
            )
            self.mutated_before_dispatch = False

        def read_input(self, view):
            if (
                view.screen is OverworldScreen.SKILLS
                and not self.mutated_before_dispatch
            ):
                for _ in range(3):
                    player.increase_permanent_stat("strength")
                self.mutated_before_dispatch = True
                return ChoosePermanentStatIncrease("strength")
            return super().read_input(view)

    ui = StaleSkillsUI()
    session = OverworldSession(
        game,
        ui=ui,
        battle_factory=BattleHarness(()).factory,
        enemy_factory=EnemyFactory(),
        battle_ui_factory=BattleUIFactory(),
    )

    result = session.run()

    assert result is OverworldSessionResult.QUIT
    assert player.character.permanent_stats.strength == initial_strength + 3
    assert player.growth_points == 0
    assert player.health.current == initial_hp
    assert player.mana_resource.current == initial_mana
    skills_views = [
        view for view in ui.views if view.screen is OverworldScreen.SKILLS
    ]
    assert skills_views[0].skills.stats[0].increase_enabled is True
    assert skills_views[1].notice == "That stat is not available."
    assert skills_views[1].screen is OverworldScreen.SKILLS


def test_victory_preserves_battle_mutations_and_advances_to_pair_node():
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
    assert battles.instances[0].enemy == (enemies.enemies[0],)
    assert battles.instances[0].ui is battle_uis.instances[0]
    assert player.health.current == player.health.maximum - 12
    assert player.mana_resource.current == player.mana_resource.maximum - 5
    assert player.super_resource.current == 20
    assert player.character_run_state.payload_prepared(
        PreparedPayloadId.INFUSED_BARB
    ) is True
    assert game.world_state.defeated_encounters == (FIRST_SURFACE_NODE_ID,)
    assert game.overworld_state.current_route_node_id == SECOND_SURFACE_NODE_ID
    assert (
        game.overworld_state.current_contextual_route_phase
        is ContextualRoutePhase.ENTER_ENCOUNTER
    )
    post_victory = ui.views[1]
    assert post_victory.location_label == "Goblin Pair"
    assert post_victory.contextual_route_option.action is OverworldAction.ENTER_ENCOUNTER
    assert post_victory.adventure_text == (
        "Goblin Ambush is defeated. Rewards: 40 EXP and 3 gold. "
        "The route continues toward Goblin Pair."
    )
    assert player.exp_state.current == 40
    assert player.gold == 3
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
    player = PlayerState(RogueArcher(), gold=11)
    player.exp_state.gain(13)
    player.health.take_damage(9)
    assert player.mana_resource.spend(4) is True
    player.super_resource.gain(17)
    player.character_run_state.prepare_infusion(
        InfusionKind.FIRE,
        FIRE_INFUSION_REQUIREMENTS,
    )
    game = GameState(player)
    identities = (
        player,
        player.character,
        player.health,
        player.mana_resource,
        player.super_resource,
        player.inventory,
        player.character_run_state,
    )
    equipped = {
        slot: item
        for slot, item in player.equipment.items()
        if item is not None
    }
    expected_health = player.health.current
    expected_mana = player.mana_resource.current
    expected_super = player.super_resource.current
    expected_exp = player.exp_state.current
    expected_gold = player.gold

    def mutate(acting_player):
        acting_player.health.take_damage(33)
        acting_player.mana_resource.spend(8)
        acting_player.super_resource.gain(50)
        assert (
            acting_player.character_run_state.consume_infusion()
            is InfusionKind.FIRE
        )
        acting_player.character_run_state.restore_checkpoint(
            CharacterRunCheckpoint(
                inventory=(
                    (RunItemId.EMBER_SHARD, 0),
                    (RunItemId.DEEP_COAL, 0),
                    (RunItemId.NIGHT_BERRY, 0),
                ),
                prepared_payloads=(
                    (PreparedPayloadId.INFUSED_BARB, None),
                ),
            )
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

    assert identities == (
        player,
        player.character,
        player.health,
        player.mana_resource,
        player.super_resource,
        player.inventory,
        player.character_run_state,
    )
    for slot, item in equipped.items():
        assert player.get_equipped(slot) is item
    assert player.health.current == expected_health
    assert player.mana_resource.current == expected_mana
    assert player.super_resource.current == expected_super
    assert player.exp_state.current == expected_exp
    assert player.gold == expected_gold
    assert player.character_run_state.item_quantity(RunItemId.EMBER_SHARD) == 0
    assert player.character_run_state.item_quantity(RunItemId.DEEP_COAL) == 0
    assert player.character_run_state.item_quantity(RunItemId.NIGHT_BERRY) == 1
    assert player.character_run_state.payload_prepared(
        PreparedPayloadId.INFUSED_BARB
    ) is True
    assert player.character_run_state.prepared_infusion() is InfusionKind.FIRE
    assert game.world_state.defeated_encounters == ()
    assert game.overworld_state.current_route_node_id == FIRST_SURFACE_NODE_ID
    assert game.overworld_state.current_contextual_route_phase is ContextualRoutePhase.RETRY
    assert "Rewards:" not in ui.views[-1].adventure_text
    assert ui.views[1].contextual_route_option.action is OverworldAction.RETRY


def test_victory_adventure_text_uses_actual_level_and_growth_point_grammar():
    one_level = OverworldSession._victory_adventure_text(
        FIRST_SURFACE_NODE_ID,
        SECOND_SURFACE_NODE_ID,
        exp_reward=40,
        gold_reward=3,
        levels_gained=1,
        growth_points_gained=3,
        resulting_level=2,
    )
    multiple_levels = OverworldSession._victory_adventure_text(
        "surface_shaman_pair",
        "surface_elite_patrol",
        exp_reward=180,
        gold_reward=14,
        levels_gained=2,
        growth_points_gained=6,
        resulting_level=6,
    )

    assert one_level == (
        "Goblin Ambush is defeated. Rewards: 40 EXP and 3 gold. "
        "Level up! Reached Level 2 and gained 3 Growth Points. "
        "The route continues toward Goblin Pair."
    )
    assert multiple_levels == (
        "Shaman Pair is defeated. Rewards: 180 EXP and 14 gold. "
        "Level up! Gained 2 levels, reached Level 6, and gained 6 Growth Points. "
        "The route continues toward Elite Patrol."
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
    assert (
        game.overworld_state.current_contextual_route_phase
        is ContextualRoutePhase.ENTER_ENCOUNTER
    )


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
