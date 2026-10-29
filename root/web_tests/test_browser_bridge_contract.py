import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

from app.presentation.battle_models import InteractionPhase
from app.presentation.overworld_models import OverworldScreen
from app.combat.battle import Battle
from app.content.catalog import (
    create_enemy_state,
    get_encounter_spec,
    get_route_spec,
)
from app.game.overworld_session import OverworldSession
from app.game.overworld_state import OverworldState
from app.game.party_state import DungeonPhase
from app.persistence.ports import SaveLoadResult
from app.persistence.save_port_contract import SaveLoadStatus
from app.ui.battle_ui import ChooseAction, ChooseMove, ChooseTarget
from app.ui.overworld_ui import (
    ChooseCompanion,
    ChooseMerchantCraftComponent,
    ChooseMerchantDismantle,
    ChooseMerchantImprove,
    ChooseMerchantTarget,
    ChooseOverworldAction,
    ChooseOverworldItem,
    ChoosePermanentStatIncrease,
    ChooseWeaponTarget,
)


ROOT = Path(__file__).parents[1]
BRIDGE_PATH = ROOT / "web" / "python" / "dd_bridge.py"
SPEC = importlib.util.spec_from_file_location("dd_bridge_contract", BRIDGE_PATH)
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)


class QualificationSavePort:
    def __init__(self):
        self.saved_states = []

    def inspect(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)

    def save(self, game_state):
        self.saved_states.append(game_state)
        return SaveLoadResult(SaveLoadStatus.SAVED)

    def load(self):
        return SaveLoadResult(SaveLoadStatus.MISSING)


class MemoryBrowserStorage:
    def __init__(self):
        self.values = {}

    def getItem(self, key):
        return self.values.get(key)

    def setItem(self, key, value):
        self.values[key] = value


def test_browser_store_treats_pyodide_jsnull_as_a_missing_profile(monkeypatch):
    class JsNull:
        def __str__(self):
            return "null"

    jsnull = JsNull()
    ffi = types.ModuleType("pyodide.ffi")
    ffi.jsnull = jsnull
    pyodide = types.ModuleType("pyodide")
    pyodide.ffi = ffi
    monkeypatch.setitem(sys.modules, "pyodide", pyodide)
    monkeypatch.setitem(sys.modules, "pyodide.ffi", ffi)

    class EmptyStorage:
        def getItem(self, key):
            return jsnull

    result = bridge.BrowserLocalProfileStore(EmptyStorage()).load(
        bridge._BROWSER_PROFILE_ID
    )

    assert result.status is bridge.ProfileStoreStatus.MISSING


def test_browser_save_survives_runtime_reload_and_restores_weapon_progression():
    storage = MemoryBrowserStorage()
    first_runtime = bridge.BrowserRuntime(storage=storage)
    first_runtime.start_game("branoc")
    first_runtime._game.player_state.signature_weapon_state.set_slot_progress(
        "blade_guard", 25
    )
    first_runtime._game.party_state.add_shared_items({"scrap_metal": 3})

    options = first_runtime.submit(
        {"kind": "overworld_action", "action": "options"}
    )
    assert any(
        item["action"] == "save" and item["enabled"]
        for item in options["options"]
    )
    saved = first_runtime.submit(
        {"kind": "overworld_action", "action": "save"}
    )
    assert saved["notice"] == "Game saved."

    reloaded_runtime = bridge.BrowserRuntime(storage=storage)
    reloaded_runtime.start_game("joruun")
    options = reloaded_runtime.submit(
        {"kind": "overworld_action", "action": "options"}
    )
    assert any(
        item["action"] == "load" and item["enabled"]
        for item in options["options"]
    )
    confirmation = reloaded_runtime.submit(
        {"kind": "overworld_action", "action": "load"}
    )
    assert confirmation["screen"] == OverworldScreen.LOAD_CONFIRMATION.value
    restored = reloaded_runtime.submit(
        {"kind": "overworld_action", "action": "confirm"}
    )

    assert restored["screen"] == OverworldScreen.MAIN.value
    restored_game = reloaded_runtime._session.game_state
    assert restored_game.player_state.character.profile.drifter_id == "branoc"
    assert restored_game.player_state.signature_weapon_state.slot_progress[
        "blade_guard"
    ] == 25
    assert restored_game.party_state.shared_items == {"scrap_metal": 3}

def test_bridge_starts_the_canonical_headless_runtime():
    runtime = bridge.BrowserRuntime()

    view = runtime.start_game()

    assert view["screen"] == OverworldScreen.MAIN.value
    assert view["contextual_route_option"]["action"] == "enter_encounter"
    assert runtime._session.game_state is runtime._game
    assert runtime._session._save_port is None


def test_browser_shortcut_h01b_starts_branoc_at_the_floor_one_hub():
    runtime = bridge.BrowserRuntime()

    view = runtime.load_scenario("  h01b  ")

    assert view["screen"] == OverworldScreen.HUB.value
    assert runtime._game.player_state.character.profile.drifter_id == "branoc"
    assert runtime._game.party_state.phase is DungeonPhase.HUB
    assert runtime._game.party_state.tutorial_complete is False
    assert runtime._game.party_state.shared_gold == 75
    assert runtime._game.party_state.companions == ()


def test_browser_shortcut_f01ba_starts_after_branoc_and_azhvielle_clear_floor_one():
    runtime = bridge.BrowserRuntime()

    view = runtime.load_scenario("F01BA")

    assert view["screen"] == OverworldScreen.HUB.value
    assert runtime._game.player_state.character.profile.drifter_id == "branoc"
    assert tuple(
        member.character.profile.drifter_id
        for member in runtime._game.party_state.companions
    ) == ("azhvielle",)
    assert runtime._game.party_state.phase is DungeonPhase.HUB
    assert runtime._game.party_state.tutorial_complete is True
    assert runtime._game.party_state.floor_one_cleared is True
    assert runtime._game.party_state.shared_gold == 106
    assert runtime._game.party_state.shared_items
    assert runtime._game.party_state.outing_rewards.snapshot() == {
        "experience": 0,
        "gold": 0,
        "items": {},
    }
    assert "Floor 1 is cleared" in view["adventure_text"]


def test_browser_shortcut_rejects_unknown_codes_without_replacing_the_game():
    runtime = bridge.BrowserRuntime()
    current = runtime.start_game("joruun")
    game = runtime._game

    with pytest.raises(ValueError, match="invalid shortcut code"):
        runtime.load_scenario("not-a-code")

    assert runtime._game is game
    assert runtime.current_view() == current


def test_bridge_exposes_authored_roster_and_starts_each_drifter():
    runtime = bridge.BrowserRuntime()
    roster = bridge.drifter_roster()

    assert [profile["drifter_id"] for profile in roster] == [
        "branoc",
        "azhvielle",
        "zhaivra",
        "joruun",
    ]
    assert [profile["sprite_url"] for profile in roster] == [
        "assets/drifters/branoc.png",
        "assets/drifters/azhvielle.png",
        "assets/drifters/zhaivra.png",
        "assets/drifters/joruun.png",
    ]
    assert all(profile["short_name"] and profile["combat_role"] for profile in roster)

    for profile in roster:
        view = runtime.start_game(profile["drifter_id"])
        assert view["screen"] == OverworldScreen.MAIN.value
        assert view["contextual_route_option"]["action"] == "enter_encounter"
        assert runtime._game.player_state.character.profile.drifter_id == profile["drifter_id"]
        battle = runtime.submit({"kind": "overworld_action", "action": "enter_encounter"})
        assert battle["interaction_phase"] in {
            InteractionPhase.ACTIONS.value,
            InteractionPhase.COMPLETE.value,
        }


def test_bridge_projects_and_submits_existing_semantic_inputs():
    runtime = bridge.BrowserRuntime()
    initial = runtime.start_game()

    assert json.loads(runtime.current_view_json()) == initial
    battle = runtime.submit({"kind": "overworld_action", "action": "enter_encounter"})

    assert battle["interaction_phase"] in {
        InteractionPhase.ACTIONS.value,
        InteractionPhase.COMPLETE.value,
    }
    assert runtime._session.active_battle is not None


def test_bridge_projects_and_submits_hub_merchant_actions():
    runtime = bridge.BrowserRuntime()
    runtime.start_game("branoc")
    game = runtime._game
    assert game.party_state.arrive_at_hub(game.player_state)
    game.party_state.add_shared_items(
        {"grade_i_metal": 1, "goblin_scrap": 1}
    )
    runtime._session = OverworldSession(
        game,
        battle_factory=Battle,
        enemy_factory=create_enemy_state,
    )

    merchant = runtime.submit(
        {"kind": "overworld_action", "action": "merchant"}
    )

    assert merchant["screen"] == OverworldScreen.MERCHANT.value
    assert merchant["merchant"]["selected_target_id"] == "branoc"
    assert merchant["merchant"]["weapon_name"] == "Sunder-Spire"
    assert len(merchant["merchant"]["slots"]) == 4
    assert merchant["merchant"]["slots"][0]["can_improve"] is True

    improved = runtime.submit(
        {
            "kind": "merchant_improve",
            "target_drifter_id": "branoc",
            "slot_id": "blade_guard",
        }
    )

    assert 1 <= improved["merchant"]["slots"][0]["progress"] <= 5
    assert improved["merchant"]["crafting_experience"] == 20
    dismantled = runtime.submit(
        {
            "kind": "merchant_dismantle",
            "target_drifter_id": "branoc",
            "item_id": "goblin_scrap",
        }
    )
    assert all(
        material["quantity"] >= 0
        for material in dismantled["merchant"]["materials"]
    )
    assert game.party_state.shared_items.get("goblin_scrap", 0) == 0
    assert game.party_state.crafting_experience == 20


def test_bridge_exposes_and_submits_tier_v_for_the_exact_target():
    runtime = bridge.BrowserRuntime()
    runtime.start_game("branoc")
    game = runtime._game
    assert game.party_state.arrive_at_hub(game.player_state)
    game.party_state.add_crafting_experience(990)
    for slot_id in game.player_state.signature_weapon_state.slot_progress:
        game.player_state.signature_weapon_state.set_slot_progress(slot_id, 100)
    costs = {
        "grade_iv_metal": 12,
        "grade_iv_fiber": 12,
        "grade_iv_timber": 12,
        "grade_iv_cores": 12,
    }
    game.party_state.add_shared_items(costs)
    runtime._session = OverworldSession(
        game,
        battle_factory=Battle,
        enemy_factory=create_enemy_state,
    )

    merchant = runtime.submit({"kind": "overworld_action", "action": "merchant"})
    tier_v_view = merchant["merchant"]["tier_v"]
    assert tier_v_view["can_attempt"] is True
    assert tier_v_view["success_chance_percent"] == 20
    attempted = runtime.submit(
        {"kind": "merchant_tier_v", "target_drifter_id": "branoc"}
    )

    assert attempted["screen"] == OverworldScreen.MERCHANT.value
    assert attempted["merchant"]["tier_v"]["completed"] in (True, False)
    assert game.party_state.shared_items == {}


def test_bridge_crafts_and_installs_component_for_the_selected_drifter():
    runtime = bridge.BrowserRuntime()
    runtime.start_game("branoc")
    game = runtime._game
    assert game.party_state.arrive_at_hub(game.player_state)
    game.party_state.add_shared_items({"grade_i_metal": 1})
    runtime._session = OverworldSession(
        game,
        battle_factory=Battle,
        enemy_factory=create_enemy_state,
    )

    merchant = runtime.submit(
        {"kind": "overworld_action", "action": "merchant"}
    )
    assert merchant["merchant"]["component_recipes"][0]["can_craft"] is True
    crafted = runtime.submit(
        {
            "kind": "merchant_craft_component",
            "target_drifter_id": "branoc",
            "component_id": "sunder_spire_blade_reinforced",
        }
    )
    assert "Crafted and installed Reinforced Blade and Guard" in crafted["notice"]
    assert all(
        recipe["component_id"] != "sunder_spire_blade_reinforced"
        for recipe in crafted["merchant"]["component_recipes"]
    )
    assert game.player_state.signature_weapon_state.components["blade_guard"] == (
        "sunder_spire_blade_reinforced"
    )
    assert game.party_state.shared_items.get("sunder_spire_blade_reinforced", 0) == 0
    assert game.party_state.shared_items.get("grade_i_metal", 0) == 0
    assert game.party_state.crafting_experience == 10

    runtime.submit({"kind": "overworld_action", "action": "back"})
    runtime.submit({"kind": "overworld_action", "action": "character"})
    weapon = runtime.submit(
        {"kind": "overworld_action", "action": "weapon"}
    )
    assert weapon["weapon"]["components"][0]["installed_component_id"] == (
        "sunder_spire_blade_reinforced"
    )
    assert game.player_state.combat_moves[0].power == 11
    assert game.player_state.combat_moves[0].accuracy == 90


def test_bridge_rejects_the_removed_inventory_component_install_command():
    with pytest.raises(ValueError, match="unknown browser command"):
        bridge._command_to_input(
            {
                "kind": "weapon_component",
                "target_drifter_id": "branoc",
                "slot_id": "blade_guard",
                "component_id": "sunder_spire_blade_reinforced",
            }
        )


def test_bridge_exposes_shared_loot_in_items_and_item_inspection():
    runtime = bridge.BrowserRuntime()
    runtime.start_game("branoc")
    game = runtime._game
    assert game.party_state.arrive_at_hub(game.player_state)
    game.party_state.add_shared_items({"goblin_scrap": 3})
    runtime._session = OverworldSession(
        game,
        battle_factory=Battle,
        enemy_factory=create_enemy_state,
    )

    items = runtime.submit({"kind": "overworld_action", "action": "items"})
    assert items["screen"] == OverworldScreen.ITEMS.value
    scrap = next(
        item for item in items["inventory"]["items"]
        if item["display_name"] == "Goblin Scrap"
    )
    assert scrap["quantity"] == 3

    selected = runtime.submit(
        {"kind": "overworld_item", "selection_key": scrap["selection_key"]}
    )
    assert selected["inventory"]["selected_item_key"] == scrap["selection_key"]
    inspected = runtime.submit(
        {"kind": "overworld_action", "action": "inspect"}
    )
    assert inspected["screen"] == OverworldScreen.ITEM_INSPECT.value
    assert inspected["inventory"]["inspected_item"]["display_name"] == "Goblin Scrap"
    assert inspected["inventory"]["inspected_item"]["quantity"] == 3


def test_bridge_command_decoder_returns_existing_input_types():
    cases = (
        ({"kind": "overworld_action", "action": "enter_encounter"}, ChooseOverworldAction),
        ({"kind": "overworld_item", "selection_key": "shared-item:goblin_scrap"}, ChooseOverworldItem),
        ({"kind": "companion", "drifter_id": "azhvielle"}, ChooseCompanion),
        ({"kind": "stat_increase", "stat_name": "strength"}, ChoosePermanentStatIncrease),
        ({"kind": "merchant_target", "drifter_id": "branoc"}, ChooseMerchantTarget),
        (
            {
                "kind": "merchant_improve",
                "target_drifter_id": "branoc",
                "slot_id": "blade_guard",
            },
            ChooseMerchantImprove,
        ),
        (
            {
                "kind": "merchant_dismantle",
                "target_drifter_id": "branoc",
                "item_id": "goblin_scrap",
            },
            ChooseMerchantDismantle,
        ),
        (
            {
                "kind": "merchant_craft_component",
                "target_drifter_id": "branoc",
                "component_id": "sunder_spire_blade_reinforced",
            },
            ChooseMerchantCraftComponent,
        ),
        (
            {"kind": "weapon_target", "drifter_id": "azhvielle"},
            ChooseWeaponTarget,
        ),
        ({"kind": "action", "intent": "attack"}, ChooseAction),
        ({"kind": "move", "key": "slash"}, ChooseMove),
        ({"kind": "target", "target_id": "enemy-1"}, ChooseTarget),
    )

    for command, expected_type in cases:
        assert isinstance(bridge._command_to_input(command), expected_type)


def test_bridge_projects_authoritative_hub_party_battle_and_extraction_flow():
    runtime = bridge.BrowserRuntime()
    runtime.start_game("branoc")
    game = runtime._game
    route = get_route_spec("surface")
    entrance = route.nodes[-1]
    for node in route.nodes[:-1]:
        if node.encounter_id is not None:
            game.world_state.mark_encounter_defeated(node.encounter_id)
    game.player_state.add_gold(75)
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
    assert game.party_state.arrive_at_hub(game.player_state)
    runtime._session = OverworldSession(
        game,
        battle_factory=Battle,
        enemy_factory=create_enemy_state,
    )

    hub = runtime.current_view()
    assert hub["screen"] == OverworldScreen.HUB.value
    assert runtime.submit(
        {"kind": "overworld_action", "action": "recruit_companion"}
    )["screen"] == OverworldScreen.COMPANION_SELECTION.value
    ready = runtime.submit({"kind": "companion", "drifter_id": "azhvielle"})
    assert ready["notice"] is None, ready
    assert ready["screen"] == OverworldScreen.PARTY_READY.value
    battle = runtime.submit({"kind": "overworld_action", "action": "ready"})

    assert battle["interaction_phase"] == InteractionPhase.ACTIONS.value
    assert tuple(member["target_id"] for member in battle["party_members"]) == (
        "drifter_branoc",
        "drifter_azhvielle",
    )
    assert len(battle["enemies"]) == 3
    for enemy in runtime._session.active_battle.enemies:
        enemy.health.take_damage(enemy.health.current)
    completed = runtime.submit({"kind": "action", "intent": "defend"})
    assert completed["interaction_phase"] == InteractionPhase.COMPLETE.value

    extraction = runtime.current_view()
    assert extraction["screen"] == "extraction"
    assert extraction["outing_rewards"] == {
        "experience": 120,
        "gold": 9,
        "items": [
            {"item_id": "goblin_scrap", "quantity": 3, "display_name": "Goblin Scrap"}
        ],
    }
    returned = runtime.submit(
        {"kind": "overworld_action", "action": "return_to_hub"}
    )
    assert returned["screen"] == OverworldScreen.HUB.value
    assert game.party_state.phase is DungeonPhase.HUB
    assert game.party_state.shared_gold == 19
    assert tuple(member.character.profile.drifter_id for member in game.party_state.companions) == (
        "azhvielle",
    )


def test_bridge_projects_tutorial_defeat_to_drifter_selection_and_fresh_start():
    runtime = bridge.BrowserRuntime()
    runtime.start_game("branoc")
    game = runtime._game
    route = get_route_spec("surface")
    entrance = route.nodes[-1]
    for node in route.nodes[:-1]:
        if node.encounter_id is not None:
            game.world_state.mark_encounter_defeated(node.encounter_id)
    game.player_state.add_gold(75)
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
    assert game.party_state.arrive_at_hub(game.player_state)
    runtime._session = OverworldSession(
        game,
        battle_factory=Battle,
        enemy_factory=create_enemy_state,
    )
    runtime.submit({"kind": "overworld_action", "action": "recruit_companion"})
    runtime.submit({"kind": "companion", "drifter_id": "azhvielle"})
    battle_view = runtime.submit({"kind": "overworld_action", "action": "ready"})
    assert battle_view["interaction_phase"] == InteractionPhase.ACTIONS.value
    for member in (game.player_state, *game.party_state.companions):
        member.health.take_damage(member.health.maximum)
    runtime._session.active_battle._finish("enemy")

    result = runtime.submit({"kind": "back"})

    assert result == "select_drifter"
    assert game.party_state.phase is DungeonPhase.OUTSIDE
    assert game.party_state.companions == ()
    fresh = runtime.start_game("joruun")
    assert fresh["screen"] == OverworldScreen.MAIN.value
    assert runtime._game is not game
    assert runtime._game.player_state.character.profile.drifter_id == "joruun"
    assert runtime._game.party_state.phase is DungeonPhase.OUTSIDE


def test_bridge_spends_growth_points_from_the_authoritative_skills_view():
    runtime = bridge.BrowserRuntime()
    runtime.start_game()
    runtime._game.player_state.gain_experience(100)

    character = runtime.submit({"kind": "overworld_action", "action": "character"})
    assert character["screen"] == OverworldScreen.CHARACTER.value
    assert [option["action"] for option in character["options"]] == [
        "skills",
        "weapon",
        "equipment",
        "back",
    ]

    skills = runtime.submit({"kind": "overworld_action", "action": "skills"})
    strength = next(row for row in skills["skills"]["stats"] if row["stat_name"] == "strength")
    assert skills["screen"] == OverworldScreen.SKILLS.value
    assert skills["skills"]["growth_points_available"] == 3
    assert strength["value"] == 15
    assert strength["increase_enabled"] is True

    updated = runtime.submit({"kind": "stat_increase", "stat_name": "strength"})
    strength = next(row for row in updated["skills"]["stats"] if row["stat_name"] == "strength")
    assert updated["screen"] == OverworldScreen.SKILLS.value
    assert updated["skills"]["growth_points_available"] == 2
    assert strength["value"] == 16


def test_bridge_completes_floor_one_through_semantic_actions():
    runtime = bridge.BrowserRuntime()
    runtime.start_game("branoc")
    game = runtime._game
    surface = get_route_spec("surface")
    for node in surface.nodes[:-1]:
        if node.encounter_id is not None:
            game.world_state.mark_encounter_defeated(node.encounter_id)
    game.player_state.add_gold(75)
    surface_rests = tuple(
        node.node_id for node in surface.nodes[:-1] if node.kind.value == "rest"
    )
    game._overworld_state = OverworldState.from_snapshot(
        {
            "current_route_node_id": surface.nodes[-1].node_id,
            "surface_route_begun": True,
            "dungeon_entrance_reached": True,
            "route_complete": True,
            "resolved_rest_node_ids": list(surface_rests),
            "current_contextual_route_phase": "none",
        }
    )
    assert game.party_state.arrive_at_hub(game.player_state)
    runtime._session = OverworldSession(
        game,
        battle_factory=Battle,
        enemy_factory=create_enemy_state,
        save_port=QualificationSavePort(),
    )
    runtime.submit({"kind": "overworld_action", "action": "recruit_companion"})
    runtime.submit({"kind": "companion", "drifter_id": "azhvielle"})
    runtime.submit({"kind": "overworld_action", "action": "ready"})
    for enemy in runtime._session.active_battle.enemies:
        enemy.health.take_damage(enemy.health.current)
    runtime.submit({"kind": "action", "intent": "defend"})
    assert runtime.current_view()["screen"] == OverworldScreen.EXTRACTION.value
    runtime.submit({"kind": "overworld_action", "action": "return_to_hub"})
    surface_history = game.world_state.defeated_encounters

    warning = runtime.submit(
        {"kind": "overworld_action", "action": "start_floor_one"}
    )
    assert warning["screen"] == OverworldScreen.FLOOR_ONE_WARNING.value
    assert "Death means returning to the Hub" in warning["adventure_text"]
    view = runtime.submit({"kind": "overworld_action", "action": "set_out"})
    floor_route = get_route_spec("floor_one")
    assert len(runtime._session.active_battle.enemies) == 4
    completed_battles = 0
    recovered_at_midway = False
    skipped_pre_boss_rest = False

    for node in floor_route.nodes:
        if node.kind.value == "rest":
            view = runtime.current_view()
            assert view["screen"] == OverworldScreen.REST.value
            if node.node_id == "floor_one_midway_rest":
                actions = [option["action"] for option in view["options"]]
                assert actions == ["rest", "save", "character", "items", "extract"]
                view = runtime.submit(
                    {"kind": "overworld_action", "action": "rest"}
                )
                assert view["screen"] == OverworldScreen.REST.value
                assert runtime._game.overworld_state.current_route_node_id == node.node_id
                assert node.node_id not in runtime._game.overworld_state.resolved_rest_node_ids
                assert "extract" in [option["action"] for option in view["options"]]
                recovered_at_midway = True
                view = runtime.submit(
                    {"kind": "overworld_action", "action": "skip_rest"}
                )
            else:
                view = runtime.submit(
                    {"kind": "overworld_action", "action": "skip_rest"}
                )
                skipped_pre_boss_rest = True
            assert view["screen"] == OverworldScreen.MAIN.value
            continue

        if completed_battles:
            view = runtime.current_view()
            assert view["contextual_route_option"]["action"] == "enter_encounter"
            view = runtime.submit(
                {"kind": "overworld_action", "action": "enter_encounter"}
            )
        battle = runtime._session.active_battle
        assert battle.encounter_label == node.display_label
        assert tuple(enemy.archetype_id for enemy in battle.enemies) == (
            get_encounter_spec(node.encounter_id).enemy_archetype_ids
        )
        for enemy in battle.enemies:
            enemy.health.take_damage(enemy.health.current)
        runtime.submit({"kind": "action", "intent": "defend"})
        completed_battles += 1
        view = runtime.current_view()
        if completed_battles < 10:
            expected_screen = (
                OverworldScreen.REST.value
                if completed_battles in {5, 9}
                else OverworldScreen.MAIN.value
            )
            assert view["screen"] == expected_screen
        else:
            assert view["screen"] == OverworldScreen.HUB.value

    assert completed_battles == 10
    assert recovered_at_midway and skipped_pre_boss_rest
    assert game.party_state.floor_one_cleared is True
    assert game.party_state.shared_gold == 115
    assert game.party_state.outing_rewards.experience == 0
    assert game.party_state.outing_rewards.gold == 0
    assert game.world_state.defeated_encounters == surface_history
    assert game.overworld_state.current_route_node_id == "surface_dungeon_entrance"
    saved_states = runtime._session._save_port.saved_states
    assert len(saved_states) == 3
    for fallback in saved_states[:2]:
        assert fallback is not game
        assert fallback.party_state.phase is DungeonPhase.HUB
        assert fallback.overworld_state.current_route_node_id == "surface_dungeon_entrance"
        assert fallback.party_state.outing_rewards.experience == 0
        assert fallback.party_state.outing_rewards.gold == 0
    assert saved_states[2] is game
    for member in (game.player_state, *game.party_state.companions):
        assert member.health.current == member.health.maximum
        assert member.mana_resource.current == member.mana_resource.maximum


def test_bridge_rejects_unknown_commands_and_restart_rebuilds_the_runtime():
    runtime = bridge.BrowserRuntime()
    runtime.start_game()
    first_game = runtime._game

    with pytest.raises(ValueError, match="unknown browser command"):
        runtime.submit({"kind": "teleport"})

    restarted = runtime.restart_game()

    assert restarted["screen"] == OverworldScreen.MAIN.value
    assert runtime._game is not first_game
    assert runtime._session.active_battle is None
    assert runtime.current_view()["screen"] == OverworldScreen.MAIN.value


def test_bridge_projection_contains_no_browser_owned_gameplay_state():
    source = BRIDGE_PATH.read_text()

    assert "class GameState" not in source
    assert "class OverworldSession" not in source
    assert "damage" not in source
    assert "reward" not in source
    assert "route_complete =" not in source
