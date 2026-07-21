import builtins

import pytest

from app.enemies.factory import create_enemy_state
from app.game.game_state import GameState
from app.game.main_loop import _startup_game_state
from app.game.encounter_manifest import route_manifest_node
from app.game.overworld_route import (
    RouteNodeKind,
    SURFACE_ROUTE_NODES,
    route_node,
)
from app.game.overworld_session import OverworldSession, OverworldSessionResult
from app.game.overworld_state import ContextualRoutePhase
from app.game.save_repository import SaveLoadStatus, SaveRepository
from app.player.character import Brawler
from app.player.inventory_action import InventoryActionResolver
from app.player.player_state import PlayerState
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.ui.overworld_ui import ChooseOverworldAction
from app.world.character_profiles.roster import get_character_profiles


class ScriptedUI:
    def __init__(self, inputs):
        self._inputs = list(inputs)
        self.views = []

    def render(self, view):
        self.views.append(view)

    def read_input(self, _view):
        return self._inputs.pop(0)


def _phase_for(kind):
    if kind in {RouteNodeKind.COMBAT, RouteNodeKind.BOSS}:
        return ContextualRoutePhase.ENTER_ENCOUNTER
    return ContextualRoutePhase.NONE


def _state_at_node(profile_choice, target_node_id, *, begin_route=True):
    profile = next(
        profile
        for profile in get_character_profiles()
        if profile.choice == profile_choice
    )
    player = PlayerState(profile.create_character(), gold=37)
    player.health.take_damage(13)
    player.mana_resource.spend(7)
    player.super_resource.gain(29)
    player.gain_experience(100)
    player.increase_permanent_stat("strength")
    player.inventory.add_item("tonic")
    if profile_choice == "3":
        assert InventoryActionResolver().resolve(
            "prepare_fire_infusion",
            player.character_run_state,
        ).accepted

    game = GameState(player)
    game.set_metadata("m11_gate4", {"profile": profile_choice})
    game.story_state.current_chapter = "chapter_one"
    game.story_state.add_story_flag("surface_started")
    game.story_state.record_decision("route", "surface")
    game.world_state.discover_location("ketlyv_woods")
    if begin_route:
        game.overworld_state.begin_surface_route()

    if target_node_id == game.overworld_state.current_route_node_id:
        return game

    target_index = next(
        index
        for index, node in enumerate(SURFACE_ROUTE_NODES)
        if node.node_id == target_node_id
    )
    for node in SURFACE_ROUTE_NODES[:target_index]:
        if node.kind in {RouteNodeKind.COMBAT, RouteNodeKind.BOSS}:
            game.world_state.mark_encounter_defeated(
                route_manifest_node(node.node_id).encounter.encounter_id
            )
        if node.kind is RouteNodeKind.REST:
            game.overworld_state.record_resolved_rest_node(node.node_id)
        next_node = SURFACE_ROUTE_NODES[
            SURFACE_ROUTE_NODES.index(node) + 1
        ]
        game.overworld_state.advance_to(
            next_node.node_id,
            contextual_phase=_phase_for(next_node.kind),
        )
    return game


@pytest.mark.parametrize("profile", get_character_profiles(), ids=lambda item: item.choice)
def test_all_drifters_round_trip_complete_persistent_session(profile, tmp_path):
    game = _state_at_node(profile.choice, "surface_warrior_pair")
    before = game.snapshot()
    repository = SaveRepository(tmp_path / f"{profile.choice}.json")

    repository.save(game)
    result = repository.load()

    assert result.status is SaveLoadStatus.LOADED
    assert result.game_state is not game
    assert result.game_state.snapshot() == before
    assert result.game_state.player_state is not game.player_state
    assert result.game_state.player_state.character is not game.player_state.character
    assert result.game_state.player_state.inventory is not game.player_state.inventory
    assert (
        result.game_state.player_state.character_run_state
        is not game.player_state.character_run_state
    )
    assert result.game_state.overworld_state.current_route_node_id == (
        "surface_warrior_pair"
    )
    assert not hasattr(result.game_state, "battle")
    assert not hasattr(result.game_state, "combat_state")

    repository.save(result.game_state)
    assert repository.load().game_state.snapshot() == before


@pytest.mark.parametrize(
    "target_node_id",
    (
        "surface_goblin_solo",
        "surface_goblin_pair",
        "surface_rest_after_warrior_solo",
        "surface_shaman_pair",
        "surface_goblin_lord",
        "surface_dungeon_entrance",
    ),
)
def test_save_load_preserves_every_approved_route_boundary(target_node_id, tmp_path):
    game = _state_at_node(
        "1",
        target_node_id,
        begin_route=target_node_id != "surface_goblin_solo",
    )
    repository = SaveRepository(tmp_path / "boundary.json")

    repository.save(game)
    loaded = repository.load()

    assert loaded.status is SaveLoadStatus.LOADED
    assert loaded.game_state.snapshot() == game.snapshot()
    assert loaded.game_state.overworld_state.current_route_node_id == target_node_id
    if target_node_id == "surface_goblin_solo":
        assert loaded.game_state.overworld_state.surface_route_begun is False
    if route_node(target_node_id).kind is RouteNodeKind.REST:
        assert target_node_id not in loaded.game_state.overworld_state.resolved_rest_node_ids
    if target_node_id == "surface_dungeon_entrance":
        assert loaded.game_state.overworld_state.route_complete is True


def test_loaded_session_continues_and_resaves_without_duplicate_reward(tmp_path):
    saved = _state_at_node("1", "surface_goblin_pair")
    repository = SaveRepository(tmp_path / "continue.json")
    repository.save(saved)
    current = GameState(PlayerState(Brawler()))
    captured = {}

    class ContinuingBattle:
        def __init__(self, player_state, enemies, *, ui, encounter_label):
            captured["player"] = player_state
            captured["label"] = encounter_label
            self.enemies = tuple(enemies)

        def run(self):
            for enemy in self.enemies:
                enemy.health.take_damage(enemy.health.current)
            return "player"

    ui = ScriptedUI(
        (
            ChooseOverworldAction(OverworldAction.OPTIONS),
            ChooseOverworldAction(OverworldAction.LOAD),
            ChooseOverworldAction(OverworldAction.CONFIRM),
            ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER),
            ChooseOverworldAction(OverworldAction.OPTIONS),
            ChooseOverworldAction(OverworldAction.SAVE),
            ChooseOverworldAction(OverworldAction.QUIT),
            ChooseOverworldAction(OverworldAction.CONFIRM),
        )
    )
    session = OverworldSession(
        current,
        ui=ui,
        battle_factory=ContinuingBattle,
        enemy_factory=create_enemy_state,
        battle_ui_factory=lambda: object(),
        save_repository=repository,
    )

    assert session.run() is OverworldSessionResult.QUIT
    assert captured["player"] is session.game_state.player_state
    assert captured["label"] == "Goblin Pair"
    assert session.game_state.world_state.defeated_encounters == (
        "surface_goblin_solo",
        "surface_goblin_pair",
    )
    assert session.game_state.player_state.exp_state.current == 80
    assert session.game_state.player_state.gold == 43
    assert session.game_state.overworld_state.current_route_node_id == (
        "surface_warrior_solo"
    )
    assert repository.load().game_state.snapshot() == session.game_state.snapshot()
    assert session.game_state is not current
    assert ui.views[3].screen is OverworldScreen.MAIN


@pytest.mark.parametrize("profile", get_character_profiles(), ids=lambda item: item.choice)
def test_startup_load_reconstructs_each_drifter_without_character_selection(
    profile,
    tmp_path,
    monkeypatch,
):
    game = _state_at_node(profile.choice, "surface_goblin_pair")
    repository = SaveRepository(tmp_path / "startup.json")
    repository.save(game)
    answers = iter(["l"])
    monkeypatch.setattr(builtins, "input", lambda _prompt: next(answers))

    loaded = _startup_game_state(repository)

    assert loaded is not game
    assert loaded.snapshot() == game.snapshot()
    assert loaded.player_state.character.profile.choice == profile.choice
    assert loaded.overworld_state.current_route_node_id == "surface_goblin_pair"
