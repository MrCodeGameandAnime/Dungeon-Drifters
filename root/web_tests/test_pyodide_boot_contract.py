import importlib.util
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile


ROOT = Path(__file__).parents[1]
TOOL_PATH = ROOT / "tools" / "build_browser_runtime.py"
SPEC = importlib.util.spec_from_file_location("build_browser_runtime", TOOL_PATH)
runtime_builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime_builder)


Pyd0_ROOT = ROOT / "web" / "pyd0"


def test_runtime_archive_contains_only_authoritative_app_python(tmp_path):
    output = tmp_path / "dd_runtime.zip"

    files = runtime_builder.build_runtime(ROOT / "src", output)

    with ZipFile(output) as archive:
        names = archive.namelist()
        assert names == sorted(names)
        assert "app/__init__.py" in names
        assert "app/game/new_game.py" in names
        assert "app/game/overworld_session.py" in names
        assert "app/combat/battle.py" in names
        assert all(name.startswith("app/") for name in names)
        assert all("__pycache__" not in name for name in names)
        assert all(name.endswith(".py") for name in names)
        assert all(
            item.compress_type == ZIP_STORED for item in archive.infolist()
        )
        assert all(item.create_system == 3 for item in archive.infolist())

    assert len(files) == len(names)


def test_runtime_archive_is_reproducible(tmp_path):
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"

    runtime_builder.build_runtime(ROOT / "src", first)
    runtime_builder.build_runtime(ROOT / "src", second)

    assert first.read_bytes() == second.read_bytes()


def test_pyd0_pins_pyodide_and_declares_required_boot_contract():
    html = (Pyd0_ROOT / "index.html").read_text()
    javascript = (Pyd0_ROOT / "js" / "pyd0.js").read_text()
    boot = (Pyd0_ROOT / "python" / "boot.py").read_text()

    assert "v314.0.7/full/pyodide.js" in html
    assert 'PYODIDE_VERSION = "314.0.7"' in javascript
    assert "latest" not in html.lower()
    assert "latest" not in javascript.lower()
    assert "game/dd_runtime.zip" in javascript
    assert "sys.path.insert(0, '/dd_runtime.zip')" in javascript
    assert '"app.game.new_game"' in boot
    assert '"app.game.overworld_session"' in boot
    assert '"app.combat.battle"' in boot
    assert '"app.content.catalog"' in boot
    assert 'create_new_game("branoc")' in boot


def test_browser_boot_has_no_copied_application_tree():
    copied_app = Pyd0_ROOT / "app"

    assert not copied_app.exists()
