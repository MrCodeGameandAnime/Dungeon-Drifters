import copy
from itertools import combinations
import json

import pytest

from app.enemies.factory import create_enemy_state
from app.game.game_state import GameState
from app.game.overworld_session import OverworldSession, OverworldSessionResult
from app.game.save_repository import SaveRepository
from app.player.inventory_action import InventoryActionResolver
from app.player.player_state import PlayerState
from app.presentation.overworld_models import OverworldAction, OverworldScreen
from app.presentation.overworld_presenter import OverworldPresenter
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
    game.world_state.mark_encounter_defeated("surface_goblin_pair")
    game.world_state.mark_encounter_defeated("surface_warrior_solo")
    game.overworld_state.begin_surface_route()
    game.overworld_state.advance_to(
        "surface_goblin_pair",
        contextual_phase="enter_encounter",
    )
    game.overworld_state.advance_to(
        "surface_warrior_solo",
        contextual_phase="enter_encounter",
    )
    game.overworld_state.advance_to("surface_rest_after_warrior_solo")
    game.overworld_state.record_resolved_rest_node(
        "surface_rest_after_warrior_solo"
    )
    game.overworld_state.advance_to(
        "surface_warrior_pair",
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
    expected = {
        "1": {
            "identity": ("Ser Branoc", "Ser Branoc, the Unbroken Crest", "Brawler"),
            "attributes": {
                "constitution": 14,
                "spirit": 6,
                "intelligence": 5,
                "strength": 16,
                "dexterity": 10,
                "intuition": 10,
            },
            "resources": {
                "health": {"current": 111, "maximum": 120},
                "mana": {"current": 41, "maximum": 47},
                "super": {"current": 41, "maximum": 100},
            },
            "weapon": {
                "type": "SunderSpire",
                "name": "Sunder-Spire",
                "weapon_type": "Great Flamberge",
                "intended_wielder": "Branoc",
                "stat_bonuses": {"strength": 3, "constitution": 1},
                "value": 2,
                "description": "A massive Deep-Iron flamberge forged from the broken weapons of Rhom-Ghal.",
            },
            "run_state": {"inventory": {}, "prepared_payloads": {}},
        },
        "2": {
            "identity": ("Azhvielle", "Azhvielle, the Unconfessed", "Black Mage"),
            "attributes": {
                "constitution": 7,
                "spirit": 13,
                "intelligence": 15,
                "strength": 6,
                "dexterity": 8,
                "intuition": 12,
            },
            "resources": {
                "health": {"current": 86, "maximum": 95},
                "mana": {"current": 51, "maximum": 57},
                "super": {"current": 41, "maximum": 100},
            },
            "weapon": {
                "type": "NeedleOfPlainIron",
                "name": "Needle of Plain Iron",
                "weapon_type": "Ritual Needle",
                "intended_wielder": "Azhvielle",
                "stat_bonuses": {"intelligence": 3, "spirit": 1},
                "value": 2,
                "description": "A long, unadorned iron needle used as both a weapon and a precise ritual focus.",
            },
            "run_state": {"inventory": {}, "prepared_payloads": {}},
        },
        "3": {
            "identity": (
                "Zhaivra Kelyth",
                "Zhaivra Kelyth, the Uncontrolled Reagent",
                "Rogue Archer",
            ),
            "attributes": {
                "constitution": 8,
                "spirit": 7,
                "intelligence": 10,
                "strength": 7,
                "dexterity": 15,
                "intuition": 14,
            },
            "resources": {
                "health": {"current": 89, "maximum": 98},
                "mana": {"current": 42, "maximum": 48},
                "super": {"current": 41, "maximum": 100},
            },
            "weapon": {
                "type": "Sathren",
                "name": "Sathren",
                "weapon_type": "Alchemical Recurve Bow",
                "intended_wielder": "Zhaivra",
                "stat_bonuses": {"dexterity": 3, "intuition": 1},
                "value": 2,
                "description": "A recurved bow grown from the bone-fiber of the Hollow Colossus and fitted with six alchemical reservoirs.",
            },
            "run_state": {
                "inventory": {
                    "deep_coal": 0,
                    "ember_shard": 0,
                    "night_berry": 1,
                },
                "prepared_payloads": {"infused_barb": "fire"},
            },
        },
        "4": {
            "identity": (
                "Joruun Veyr",
                "Joruun Veyr, the Bloody Storm Monk",
                "Monk",
            ),
            "attributes": {
                "constitution": 10,
                "spirit": 10,
                "intelligence": 13,
                "strength": 8,
                "dexterity": 12,
                "intuition": 8,
            },
            "resources": {
                "health": {"current": 95, "maximum": 104},
                "mana": {"current": 45, "maximum": 51},
                "super": {"current": 41, "maximum": 100},
            },
            "weapon": {
                "type": "SkyNeedle",
                "name": "Sky-Needle",
                "weapon_type": "Conductive Shakuj\u014d",
                "intended_wielder": "Joruun",
                "stat_bonuses": {"spirit": 2, "dexterity": 1, "intuition": 1},
                "value": 2,
                "description": "An ash-wood shakuj\u014d fitted with copper collars and loose conductive rings.",
            },
            "run_state": {"inventory": {}, "prepared_payloads": {}},
        },
    }[profile_choice]
    assert snapshot["player"]["identity"] == {
        "display_name": expected["identity"][0],
        "full_display_name": expected["identity"][1],
        "archetype_name": expected["identity"][2],
        "profile": {
            "choice": profile_choice,
            "short_name": expected["identity"][0],
            "display_name": expected["identity"][1],
        },
    }
    assert snapshot["player"]["attributes"] == expected["attributes"]
    assert snapshot["player"]["resources"] == expected["resources"]
    assert snapshot["player"]["progression"] == {
        "level": 2,
        "exp": 0,
        "growth_points": 2,
    }
    assert snapshot["player"]["gold"] == 17
    assert snapshot["player"]["inventory"] == ["tonic"]
    assert snapshot["player"]["equipment"] == {
        "weapon": expected["weapon"],
        "off_hand": None,
        "head": None,
        "body": None,
        "accessory": None,
    }
    assert snapshot["player"]["run_state"] == expected["run_state"]
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
    assert snapshot["story"] == {
        "current_chapter": "chapter_one",
        "current_scene": None,
        "current_location": None,
        "story_flags": ["surface_started"],
        "completed_events": [],
        "player_decisions": {"route": "surface"},
    }
    assert snapshot["world"] == {
        "discovered_locations": ["ketlyv_woods"],
        "defeated_encounters": [
            "surface_goblin_solo",
            "surface_goblin_pair",
            "surface_warrior_solo",
        ],
        "opened_objects": [],
        "consumed_objects": [],
        "dungeon_changes": {},
    }
    assert snapshot["overworld"] == {
        "current_route_node_id": "surface_warrior_pair",
        "surface_route_begun": True,
        "dungeon_entrance_reached": False,
        "route_complete": False,
        "resolved_rest_node_ids": [
            "surface_rest_after_warrior_solo"
        ],
        "current_contextual_route_phase": "enter_encounter",
    }
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
    before = tuple(game.snapshot() for game in games)

    first = games[0]
    first.player_state.health.take_damage(13)
    first.player_state.mana_resource.spend(4)
    first.player_state.super_resource.gain(12)
    first.player_state.gain_experience(100)
    first.player_state.increase_permanent_stat("constitution")
    first.player_state.inventory.add_item("first-only")
    first.player_state.unequip("weapon")
    first.player_state.add_gold(10)
    first.story_state.add_story_flag("first-only")
    first.world_state.discover_location("first-only")
    first.overworld_state.record_resolved_rest_node(
        "surface_rest_after_warrior_solo"
    )
    games[2].player_state.character_run_state.consume_infusion()

    assert games[1].snapshot() == before[1]
    assert games[3].snapshot() == before[3]
    assert games[0].snapshot() != before[0]
    assert games[2].snapshot() != before[2]
    for index, game in enumerate(games):
        if index in {0, 2}:
            continue
        assert game.snapshot() == before[index]

    for left, right in combinations(games, 2):
        assert left.player_state is not right.player_state
        assert left.player_state.character is not right.player_state.character
        assert left.player_state.inventory is not right.player_state.inventory
        assert left.player_state.character_run_state is not right.player_state.character_run_state
        assert left.player_state.health is not right.player_state.health
        assert left.player_state.mana_resource is not right.player_state.mana_resource
        assert left.player_state.super_resource is not right.player_state.super_resource
        assert left.player_state.level_state is not right.player_state.level_state
        assert left.player_state.exp_state is not right.player_state.exp_state
        assert left.player_state.character.permanent_stats is not right.player_state.character.permanent_stats
        assert left.player_state._equipment is not right.player_state._equipment
        assert left.story_state is not right.story_state
        assert left.world_state is not right.world_state
        assert left.overworld_state is not right.overworld_state
        assert left.player_state.get_equipped("weapon") is not right.player_state.get_equipped("weapon")


@pytest.mark.parametrize("profile", get_character_profiles(), ids=lambda p: p.choice)
def test_signature_weapon_session_values_and_inspection_are_isolated(profile):
    player = PlayerState(profile.create_character())
    other = PlayerState(profile.create_character())
    game = GameState(player)
    other_before = other.snapshot()
    weapon = player.get_equipped("weapon")
    permanent_before = player.character.permanent_stats.as_dict()
    before = game.snapshot()

    effective_with_weapon = {
        stat_name: player.effective_stat(stat_name)
        for stat_name in permanent_before
    }
    for stat_name, permanent_value in permanent_before.items():
        assert effective_with_weapon[stat_name] == (
            permanent_value + weapon.stat_bonuses.get(stat_name, 0)
        )

    view = OverworldPresenter().build(
        game,
        screen=OverworldScreen.WEAPON,
    ).weapon
    assert view.name == weapon.name
    assert view.weapon_type == weapon.weapon_type
    assert view.intended_wielder == weapon.intended_wielder
    assert view.description == weapon.description
    assert tuple(
        (bonus.label, bonus.amount) for bonus in view.bonuses
    ) == tuple(
        (stat_name.title(), amount)
        for stat_name, amount in weapon.stat_bonuses.items()
    )
    assert game.snapshot() == before

    player.unequip("weapon")
    assert player.get_equipped("weapon") is None
    assert player.character.permanent_stats.as_dict() == permanent_before
    assert all(
        player.effective_stat(stat_name) == permanent_value
        for stat_name, permanent_value in permanent_before.items()
    )
    assert other.snapshot() == other_before

    player.equip("weapon", weapon)
    assert player.get_equipped("weapon") is weapon
    assert player.character.permanent_stats.as_dict() == permanent_before
