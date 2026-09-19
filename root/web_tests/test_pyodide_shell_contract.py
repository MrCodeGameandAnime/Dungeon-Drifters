from pathlib import Path
from html.parser import HTMLParser


ROOT = Path(__file__).parents[1]
SHELL = ROOT / "web" / "pyd4"


def _read(relative):
    return (SHELL / relative).read_text()


class _PhaseSurfaceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.surfaces = {}

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id in ("overworld-screen", "battle-screen"):
            self.surfaces[element_id] = (tag, "hidden" in attributes)


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
        "overworld-screen",
        "battle-screen",
        "player-panel",
        "enemy-panel",
        "battle-log",
        "battle-status",
        "battle-matchup",
        "super-meter",
        "actions",
        "moves",
        "targets",
        "inventory",
        "completion",
        "restart",
    ):
        assert f'id="{element_id}"' in html


def test_battle_shell_uses_terminal_information_order():
    html = _read("index.html")
    order = (
        'id="battle-status"',
        'id="battle-matchup"',
        'id="battle-log"',
        'id="controls-panel"',
        'id="super-meter"',
    )

    positions = [html.index(element_id) for element_id in order]

    assert positions == sorted(positions)
    assert 'id="phase-badge"' not in html


def test_shell_separates_initial_overworld_from_inactive_battle_surface():
    parser = _PhaseSurfaceParser()
    parser.feed(_read("index.html"))

    assert parser.surfaces == {
        "overworld-screen": ("section", False),
        "battle-screen": ("section", True),
    }


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
    assert 'kind: commandKind' in javascript
    assert 'renderMoveOptions(moves, view.move_options, "move")' in javascript
    assert 'kind: "target"' in javascript
    assert 'state.interaction_phase === "complete"' in javascript
    assert 'pythonJson("current_view_json()")' in javascript
    assert "window.__DD_BROWSER_READY__ = true" in javascript

    for forbidden in ("damage =", "reward =", "route_complete =", "class GameState"):
        assert forbidden not in javascript


def test_shell_javascript_preserves_battle_phase_detail():
    javascript = _read("js/pyd4.js")

    for projection_field in (
        "view.interaction_phase",
        "option.tags",
        "option.resource_label",
        "option.rules_summary",
        "option.disabled_reason",
        "option.target_id",
        "option.move_preview",
        "view.super_meter",
        "view.inventory_inspection",
    ):
        assert projection_field in javascript

    assert 'kind: "back"' in javascript


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
