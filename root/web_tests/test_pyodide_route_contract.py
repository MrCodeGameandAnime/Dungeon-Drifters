from pathlib import Path


ROOT = Path(__file__).parents[1]
BOOT_PATH = ROOT / "web" / "pyd2" / "python" / "boot.py"

EXPECTED_ROUTE = (
    "surface_goblin_solo",
    "surface_goblin_pair",
    "surface_warrior_solo",
    "surface_rest_after_warrior_solo",
    "surface_warrior_pair",
    "surface_shaman_solo",
    "surface_shaman_pair",
    "surface_rest_after_shaman_pair",
    "surface_elite_patrol",
    "surface_rest_before_goblin_lord",
    "surface_goblin_lord",
    "surface_dungeon_entrance",
)


def test_pyd2_uses_the_pinned_runtime_archive():
    root = ROOT / "web" / "pyd2"
    html = (root / "index.html").read_text()
    javascript = (root / "js" / "pyd2.js").read_text()

    assert "v314.0.7/full/pyodide.js" in html
    assert 'PYODIDE_VERSION = "314.0.7"' in javascript
    assert "game/dd_runtime.zip" in javascript


def test_pyd2_contains_the_exact_authored_route_oracle():
    boot = BOOT_PATH.read_text()
    route_start = boot.index("EXPECTED_ROUTE = (")
    route_end = boot.index(")\nEXPECTED_COMPOSITIONS", route_start)
    route_source = boot[route_start:route_end]
    positions = [route_source.index(node) for node in EXPECTED_ROUTE]

    assert positions == sorted(positions)
    assert boot.count("surface_") >= len(EXPECTED_ROUTE)
    assert "EXPECTED_ENCOUNTER_COUNT = 8" in boot
    assert "EXPECTED_REST_COUNT = 3" in boot
    assert "EXPECTED_BATTLE_COUNT = 8" in boot
    assert "EXPECTED_ENEMY_COUNT = 14" in boot
    assert '"surface_dungeon_entrance"' in boot


def test_pyd2_uses_real_session_and_probe_only_determinism():
    boot = BOOT_PATH.read_text()

    for required in (
        "Battle(",
        "OverworldSession(",
        "create_enemy_state",
        "DeterministicResolver",
        "MoveResult",
        "ChooseOverworldAction",
        "ChooseAction",
        "ChooseMove",
        "ChooseTarget",
        "save_repository=None",
        "InteractionPhase.COMPLETE",
        "dungeon_entrance_reached",
    ):
        assert required in boot

    assert "SaveRepository" not in boot
    assert "import pytest" not in boot
    assert "tempfile" not in boot


def test_pyd2_does_not_copy_application_code_or_create_browser_state():
    assert not (ROOT / "web" / "pyd2" / "app").exists()
    boot = BOOT_PATH.read_text()

    assert "class GameState" not in boot
    assert "class OverworldSession" not in boot
    assert "damage = target.health.current" in boot
