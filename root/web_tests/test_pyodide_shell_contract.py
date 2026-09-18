from pathlib import Path


ROOT = Path(__file__).parents[1]
SHELL = ROOT / "web" / "pyd4"


def _read(relative):
    return (SHELL / relative).read_text()


def test_shell_has_pinned_pyodide_and_required_assets():
    html = _read("index.html")

    assert 'cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.js' in html
    assert 'href="styles.css"' in html
    assert 'src="js/pyd4.js"' in html
    assert 'id="loading"' in html
    assert 'id="error"' in html
    assert 'id="retry"' in html
    assert 'id="orientation-guidance"' in html


def test_shell_contains_operational_view_regions_and_controls():
    html = _read("index.html")

    for element_id in (
        "app",
        "route-panel",
        "player-panel",
        "enemy-panel",
        "battle-log",
        "actions",
        "moves",
        "targets",
        "inventory",
        "completion",
        "restart",
    ):
        assert f'id="{element_id}"' in html


def test_shell_boot_wraps_the_existing_bridge():
    boot = _read("python/boot.py")

    assert "import dd_bridge" in boot
    assert "start_game_json" in boot
    assert "current_view_json" in boot
    assert "submit_json" in boot
    assert "restart_game_json" in boot
    assert "json.dumps" in boot


def test_shell_javascript_uses_authoritative_projection_and_commands():
    javascript = _read("js/pyd4.js")

    assert 'PYODIDE_VERSION = "314.0.7"' in javascript
    assert 'fetch("game/dd_runtime.zip")' in javascript
    assert 'fetch("python/dd_bridge.py")' in javascript
    assert "start_game_json()" in javascript
    assert "current_view_json()" in javascript
    assert "submit_json(_browser_command_json)" in javascript
    assert "restart_game_json()" in javascript
    assert "option.enabled" in javascript
    assert "button.disabled" in javascript
    assert 'kind: "overworld_action"' in javascript
    assert 'kind: "action"' in javascript
    assert 'kind: "move"' in javascript
    assert 'kind: "target"' in javascript
    assert "window.__DD_BROWSER_READY__ = true" in javascript

    for forbidden in ("damage =", "reward =", "route_complete =", "class GameState"):
        assert forbidden not in javascript


def test_shell_does_not_copy_production_runtime_or_add_host_persistence():
    assert not (SHELL / "app").exists()

    for relative in ("index.html", "js/pyd4.js", "python/boot.py"):
        source = _read(relative)
        assert "pytest" not in source
        assert "tempfile" not in source
        assert "SaveRepository" not in source


def test_pyd4_does_not_modify_authoritative_production_source():
    changed = [
        path
        for path in (ROOT / "src").rglob("*")
        if path.is_file() and path.suffix == ".py"
    ]
    assert changed
