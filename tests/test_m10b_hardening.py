from app.game.encounter_manifest import (
    SURFACE_ROUTE_MANIFEST,
    create_route_encounter_enemies,
)
from app.game.game_state import GameState
from app.game.overworld_route import (
    SURFACE_REST_NODE_IDS,
    SURFACE_ROUTE_NODES,
)
from app.game.overworld_session import OverworldSession, OverworldSessionResult
from app.game.overworld_state import ContextualRoutePhase
from app.player.character import Brawler
from app.player.player_state import PlayerState
from app.presentation.overworld_models import (
    MapNodeState,
    OverworldAction,
    OverworldScreen,
)
from app.presentation.overworld_presenter import OverworldPresenter
from app.ui.overworld_ui import ChooseOverworldAction


EXPECTED_ENCOUNTER_IDS = (
    "surface_goblin_solo",
    "surface_goblin_pair",
    "surface_warrior_solo",
    "surface_warrior_pair",
    "surface_shaman_solo",
    "surface_shaman_pair",
    "surface_elite_patrol",
    "surface_goblin_lord",
)


class ScriptedUI:
    def __init__(self, inputs):
        self._inputs = iter(inputs)
        self.views = []

    def render(self, view):
        self.views.append(view)

    def read_input(self, view):
        return next(self._inputs)


def test_all_encounter_completion_ids_remain_world_owned_and_schema_seven():
    game = GameState(PlayerState(Brawler()))

    for encounter_id in EXPECTED_ENCOUNTER_IDS:
        game.world_state.mark_encounter_defeated(encounter_id)

    snapshot = game.snapshot()

    assert game.world_state.defeated_encounters == EXPECTED_ENCOUNTER_IDS
    assert snapshot["schema_version"] == 7
    assert snapshot["world"]["defeated_encounters"] == list(
        EXPECTED_ENCOUNTER_IDS
    )
    assert "defeated_encounters" not in snapshot["overworld"]


def test_map_completion_uses_world_for_combat_and_overworld_for_rest():
    game = GameState(PlayerState(Brawler()))
    for encounter_id in EXPECTED_ENCOUNTER_IDS:
        game.world_state.mark_encounter_defeated(encounter_id)
    for rest_node_id in SURFACE_REST_NODE_IDS:
        game.overworld_state.record_resolved_rest_node(rest_node_id)
    for node in SURFACE_ROUTE_NODES[1:]:
        game.overworld_state.advance_to(node.node_id)

    route_map = OverworldPresenter().build(
        game,
        screen=OverworldScreen.MAP,
    ).route_map

    assert tuple(node.state for node in route_map.nodes[:-1]) == (
        MapNodeState.COMPLETED,
    ) * 11
    assert route_map.nodes[-1].state is MapNodeState.CURRENT


def test_every_composition_can_be_recreated_without_identity_leakage():
    combat_nodes = tuple(
        node.node_id for node in SURFACE_ROUTE_MANIFEST if node.encounter
    )

    for node_id in combat_nodes:
        first = create_route_encounter_enemies(node_id)
        second = create_route_encounter_enemies(node_id)

        assert len(first) == len(second)
        for first_enemy, second_enemy in zip(first, second, strict=True):
            assert first_enemy is not second_enemy
            assert first_enemy.health is not second_enemy.health
            assert first_enemy.mana_resource is not second_enemy.mana_resource
            assert first_enemy.super_resource is not second_enemy.super_resource


def test_first_victory_remains_reward_free_and_pair_combat_stays_paused():
    player = PlayerState(Brawler(), gold=9)
    player.exp_state.gain(13)
    game = GameState(player)
    before_exp = player.exp_state.current
    before_level = player.level_state.current
    before_gold = player.gold
    enemy_calls = []

    def enemy_factory(archetype_id, *, tier):
        enemy_calls.append((archetype_id, tier))
        return object()

    def battle_factory(acting_player, enemy, *, ui):
        assert acting_player is player

        class WinningBattle:
            @staticmethod
            def run():
                return "player"

        return WinningBattle()

    ui = ScriptedUI(
        (
            ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER),
            ChooseOverworldAction(OverworldAction.OPTIONS),
            ChooseOverworldAction(OverworldAction.QUIT),
            ChooseOverworldAction(OverworldAction.CONFIRM),
        )
    )
    session = OverworldSession(
        game,
        ui=ui,
        battle_factory=battle_factory,
        enemy_factory=enemy_factory,
        battle_ui_factory=object,
    )

    result = session.run()

    assert result is OverworldSessionResult.QUIT
    assert enemy_calls == [("goblin", 0)]
    assert player.exp_state.current == before_exp
    assert player.level_state.current == before_level
    assert player.gold == before_gold
    assert game.world_state.defeated_encounters == ("surface_goblin_solo",)
    assert game.overworld_state.current_route_node_id == "surface_goblin_pair"
    assert game.overworld_state.resolved_rest_node_ids == ()
    assert (
        game.overworld_state.current_contextual_route_phase
        is ContextualRoutePhase.NONE
    )
    pair_main = ui.views[1]
    assert pair_main.screen is OverworldScreen.MAIN
    assert pair_main.location_label == "Goblin Pair"
    assert pair_main.contextual_route_option is None
