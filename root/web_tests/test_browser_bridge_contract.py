import importlib.util
import json
from pathlib import Path

import pytest

from app.presentation.battle_models import InteractionPhase
from app.presentation.overworld_models import OverworldScreen
from app.ui.battle_ui import ChooseAction, ChooseMove, ChooseTarget
from app.ui.overworld_ui import ChooseOverworldAction, ChoosePermanentStatIncrease


ROOT = Path(__file__).parents[1]
BRIDGE_PATH = ROOT / "web" / "python" / "dd_bridge.py"
SPEC = importlib.util.spec_from_file_location("dd_bridge_contract", BRIDGE_PATH)
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)


def test_bridge_starts_the_canonical_headless_runtime():
    runtime = bridge.BrowserRuntime()

    view = runtime.start_game()

    assert view["screen"] == OverworldScreen.MAIN.value
    assert view["contextual_route_option"]["action"] == "enter_encounter"
    assert runtime._session.game_state is runtime._game
    assert runtime._session._save_repository is None


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


def test_bridge_command_decoder_returns_existing_input_types():
    cases = (
        ({"kind": "overworld_action", "action": "enter_encounter"}, ChooseOverworldAction),
        ({"kind": "stat_increase", "stat_name": "strength"}, ChoosePermanentStatIncrease),
        ({"kind": "action", "intent": "attack"}, ChooseAction),
        ({"kind": "move", "key": "slash"}, ChooseMove),
        ({"kind": "target", "target_id": "enemy-1"}, ChooseTarget),
    )

    for command, expected_type in cases:
        assert isinstance(bridge._command_to_input(command), expected_type)


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
