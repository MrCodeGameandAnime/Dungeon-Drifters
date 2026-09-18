from pathlib import Path


ROOT = Path(__file__).parents[1]
PYD1_ROOT = ROOT / "web" / "pyd1"


def test_pyd1_is_pinned_to_the_pyd0_runtime_archive():
    javascript = (PYD1_ROOT / "js" / "pyd1.js").read_text()
    html = (PYD1_ROOT / "index.html").read_text()

    assert 'PYODIDE_VERSION = "314.0.7"' in javascript
    assert "v314.0.7/full/pyodide.js" in html
    assert "game/dd_runtime.zip" in javascript
    assert "latest" not in html.lower()
    assert "latest" not in javascript.lower()


def test_pyd1_constructs_the_real_headless_session():
    boot = (PYD1_ROOT / "python" / "boot.py").read_text()

    for required in (
        "create_new_game(\"branoc\")",
        "OverworldSession(",
        "battle_factory=Battle",
        "enemy_factory=create_enemy_state",
        "battle_ui_factory=None",
        "save_repository=None",
        "ChooseOverworldAction",
        "ChooseAction",
        "ChooseMove",
        "ChooseTarget",
        "InteractionPhase.COMPLETE",
    ):
        assert required in boot


def test_pyd1_drives_choices_from_authoritative_views():
    boot = (PYD1_ROOT / "python" / "boot.py").read_text()

    assert "view.action_options" in boot
    assert "view.move_options" in boot
    assert "view.target_options" in boot
    assert "option.enabled" in boot
    assert "selection_key" in boot
    assert "target_id" in boot


def test_pyd1_has_no_copied_application_tree_or_browser_gameplay_state():
    assert not (PYD1_ROOT / "app").exists()
    boot = (PYD1_ROOT / "python" / "boot.py").read_text()

    assert "damage" not in boot
    assert "reward" not in boot
    assert "route_complete =" not in boot
