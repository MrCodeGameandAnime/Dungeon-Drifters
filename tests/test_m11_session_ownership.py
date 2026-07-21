import copy
import json

import pytest

from app.enemies.factory import create_enemy_state
from app.game.game_state import GameState
from app.game.overworld_session import OverworldSession, OverworldSessionResult
from app.game.save_repository import SaveRepository
from app.player.character_run_state import InfusionKind
from app.player.inventory_action import InventoryActionResolver
from app.player.player_state import PlayerState
from app.presentation.overworld_models import OverworldAction
from app.snapshot import validate_plain_value
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


def _quit_inputs():
    return (
        ChooseOverworldAction(OverworldAction.OPTIONS),
        ChooseOverworldAction(OverworldAction.QUIT),
        ChooseOverworldAction(OverworldAction.CONFIRM),
    )


@pytest.mark.parametrize(
    "profile",
    get_character_profiles(),
    ids=lambda profile: profile.choice,
)
def test_selected_drifter_owner_graph_survives_battle_and_return(
    profile,
    tmp_path,
):
    player = PlayerState(profile.create_character())
    game = GameState(player)
    captured = {}

    owner_ids = {
        "player": id(player),
        "character": id(player.character),
        "health": id(player.health),
        "mana": id(player.mana_resource),
        "super": id(player.super_resource),
        "inventory": id(player.inventory),
        "run_state": id(player.character_run_state),
        "equipment": {
            slot: id(item)
            for slot, item in player.equipment.items()
            if item is not None
        },
    }

    class IdentityBattle:
        def __init__(self, player_state, enemies, *, ui, encounter_label):
            captured["player"] = player_state
            captured["enemies"] = tuple(enemies)
            captured["label"] = encounter_label
            self.player_state = player_state
            self.enemies = tuple(enemies)
            self.ui = ui

        def run(self):
            self.player_state.health.take_damage(1)
            self.player_state.mana_resource.spend(1)
            self.player_state.super_resource.gain(1)
            for enemy in self.enemies:
                enemy.health.take_damage(enemy.health.current)
            return "player"

    ui = ScriptedUI(
        (
            ChooseOverworldAction(OverworldAction.ENTER_ENCOUNTER),
            *_quit_inputs(),
        )
    )
    session = OverworldSession(
        game,
        ui=ui,
        battle_factory=IdentityBattle,
        enemy_factory=create_enemy_state,
        battle_ui_factory=lambda: object(),
        save_repository=SaveRepository(tmp_path / "dungeon_drifters.json"),
    )

    assert session.run() is OverworldSessionResult.QUIT
    assert captured["player"] is player
    assert captured["label"] == "Goblin Ambush"
    assert all(not enemy.is_alive() for enemy in captured["enemies"])
    assert player.character.profile is profile
    assert id(player) == owner_ids["player"]
    assert id(player.character) == owner_ids["character"]
    assert id(player.health) == owner_ids["health"]
    assert id(player.mana_resource) == owner_ids["mana"]
    assert id(player.super_resource) == owner_ids["super"]
    assert id(player.inventory) == owner_ids["inventory"]
    assert id(player.character_run_state) == owner_ids["run_state"]
    assert {
        slot: id(item)
        for slot, item in player.equipment.items()
        if item is not None
    } == owner_ids["equipment"]
    assert session.game_state is game
    assert game.world_state.defeated_encounters == ("surface_goblin_solo",)
    assert game.overworld_state.current_route_node_id == "surface_goblin_pair"


def _populated_game(profile_choice):
    profile = next(
        profile
        for profile in get_character_profiles()
        if profile.choice == profile_choice
    )
    player = PlayerState(profile.create_character(), gold=17)
    player.health.take_damage(9)
    player.mana_resource.spend(6)
    player.super_resource.gain(41)
    player.gain_experience(100)
    player.increase_permanent_stat("strength")
    player.inventory.add_item("tonic")
    if profile_choice == "3":
        InventoryActionResolver().resolve(
            "prepare_fire_infusion",
            player.character_run_state,
        )

    game = GameState(player)
    game.set_metadata("m11", {"profile": profile_choice, "checkpoint": 1})
    game.story_state.current_chapter = "chapter_one"
    game.story_state.add_story_flag("surface_started")
    game.story_state.record_decision("route", "surface")
    game.world_state.discover_location("ketlyv_woods")
    game.world_state.mark_encounter_defeated("surface_goblin_solo")
    game.overworld_state.begin_surface_route()
    game.overworld_state.advance_to(
        "surface_goblin_pair",
        contextual_phase="enter_encounter",
    )
    return game


def _walk_values(value):
    yield value
    if isinstance(value, dict):
        for key, nested in value.items():
            yield from _walk_values(key)
            yield from _walk_values(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            yield from _walk_values(nested)


@pytest.mark.parametrize("profile_choice", ("1", "2", "3", "4"))
def test_schema7_snapshot_contains_persistent_state_and_no_runtime_objects(
    profile_choice,
):
    game = _populated_game(profile_choice)
    snapshot = game.snapshot()

    validate_plain_value(snapshot)
    json.dumps(snapshot, allow_nan=False)
    assert snapshot["schema_version"] == 7
    assert set(snapshot) == {
        "schema_version",
        "player",
        "story",
        "world",
        "overworld",
        "metadata",
    }
    assert snapshot["player"]["identity"]["profile"]["choice"] == (
        profile_choice
    )
    assert set(snapshot["player"]) >= {
        "identity",
        "attributes",
        "resources",
        "progression",
        "gold",
        "inventory",
        "run_state",
        "equipment",
        "combat",
    }
    assert snapshot["story"]["story_flags"] == ["surface_started"]
    assert snapshot["world"]["defeated_encounters"] == [
        "surface_goblin_solo"
    ]
    assert snapshot["overworld"]["current_route_node_id"] == (
        "surface_goblin_pair"
    )
    assert snapshot["overworld"]["current_contextual_route_phase"] == (
        "enter_encounter"
    )
    assert snapshot["metadata"] == {
        "m11": {"profile": profile_choice, "checkpoint": 1}
    }

    forbidden_types = tuple(
        type(value)
        for value in (
            game,
            game.player_state,
            game.player_state.character,
            game.player_state.inventory,
            game.player_state.character_run_state,
        )
    )
    assert not any(
        isinstance(value, forbidden_types) for value in _walk_values(snapshot)
    )

    before = copy.deepcopy(snapshot)
    snapshot["player"]["attributes"]["strength"] = 999
    snapshot["player"]["inventory"].append("mutated")
    snapshot["story"]["story_flags"].append("mutated")
    snapshot["world"]["defeated_encounters"].append("mutated")
    snapshot["overworld"]["resolved_rest_node_ids"].append("mutated")
    snapshot["metadata"]["m11"]["checkpoint"] = 99
    assert game.snapshot() == before


def test_four_independent_sessions_do_not_share_mutable_state():
    games = tuple(_populated_game(choice) for choice in ("1", "2", "3", "4"))
    before = tuple(game.snapshot() for game in games[1:])

    first = games[0]
    first.player_state.health.take_damage(13)
    first.player_state.mana_resource.spend(4)
    first.player_state.inventory.add_item("first-only")
    first.player_state.add_gold(10)
    first.story_state.add_story_flag("first-only")
    first.world_state.discover_location("first-only")
    first.overworld_state.record_resolved_rest_node(
        "surface_rest_after_warrior_solo"
    )

    assert tuple(game.snapshot() for game in games[1:]) == before
    for left, right in zip(games, games[1:]):
        assert left.player_state is not right.player_state
        assert left.player_state.character is not right.player_state.character
        assert left.player_state.inventory is not right.player_state.inventory
        assert left.player_state.character_run_state is not right.player_state.character_run_state
        assert left.player_state.get_equipped("weapon") is not right.player_state.get_equipped("weapon")
