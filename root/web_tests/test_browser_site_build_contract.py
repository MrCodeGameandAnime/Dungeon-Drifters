import importlib.util
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).parents[1]
REPOSITORY_ROOT = ROOT.parent
TOOL_PATH = ROOT / "tools" / "build_browser_site.py"
WORKFLOW_PATH = ROOT.parent / ".github" / "workflows" / "pages.yml"
SPEC = importlib.util.spec_from_file_location("build_browser_site", TOOL_PATH)
site_builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(site_builder)


def test_site_builder_stages_only_the_static_playtest_and_runtime(tmp_path):
    output = tmp_path / "site"

    result = site_builder.build_site(
        source_root=ROOT / "src",
        output_root=output,
    )

    assert result.runtime_file_count == 122
    assert (output / "index.html").is_file()
    assert (output / "styles.css").is_file()
    assert (output / "js" / "pyd4.js").is_file()
    assert (output / "python" / "boot.py").is_file()
    assert (output / "python" / "dd_bridge.py").is_file()
    assert (output / "game" / "dd_runtime.zip").is_file()
    assert (output / "qualification" / "game" / "dd_runtime.zip").is_file()
    logo_source = ROOT.parent / "res" / "Dungeon Drifters Logo.png"
    logo_output = output / "assets" / "dungeon-drifters-logo.png"
    assert logo_source.is_file()
    assert logo_output.read_bytes() == logo_source.read_bytes()
    music_source = ROOT.parent / "res" / "music" / "theme.m4a"
    music_output = output / "assets" / "theme.m4a"
    assert music_source.is_file()
    assert music_output.read_bytes() == music_source.read_bytes()
    assert (output / ".nojekyll").is_file()
    assert (output / "build-metadata.json").is_file()
    assert not (output / "app").exists()


def test_site_builder_stages_utility_icons_without_modifying_source_images(tmp_path):
    output = tmp_path / "site"

    site_builder.build_site(ROOT / "src", output)

    for name in (
        "exit-fullscreen.png",
        "fullscreen.png",
        "music-off.png",
        "music-on.png",
        "restart.png",
    ):
        source = ROOT.parent / "res" / "icons" / name
        staged = output / "assets" / "icons" / name
        assert source.is_file()
        assert staged.read_bytes() == source.read_bytes()


def test_site_builder_metadata_and_archive_are_deterministic(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"

    site_builder.build_site(ROOT / "src", first)
    site_builder.build_site(ROOT / "src", second)

    assert (first / "game" / "dd_runtime.zip").read_bytes() == (
        second / "game" / "dd_runtime.zip"
    ).read_bytes()
    assert (first / "build-metadata.json").read_bytes() == (
        second / "build-metadata.json"
    ).read_bytes()
    metadata = json.loads((first / "build-metadata.json").read_text())
    assert metadata == {
        "pyodide_version": "314.0.7",
        "runtime_file_count": 122,
        "shell": "pyd4",
    }


def test_site_paths_are_relative_for_project_pages_deployment(tmp_path):
    output = tmp_path / "site"
    site_builder.build_site(ROOT / "src", output)
    html = (output / "index.html").read_text()
    javascript = (output / "js" / "pyd4.js").read_text()

    assert 'href="styles.css"' in html
    assert 'src="js/pyd4.js"' in html
    assert 'src="assets/theme.m4a"' in html
    assert 'fetch("game/dd_runtime.zip")' in javascript
    assert 'fetch("python/dd_bridge.py")' in javascript
    assert "src=\"/" not in html
    assert "fetch(\"/" not in javascript


def test_play_navigation_follows_home_on_every_normal_website_page():
    pages = (
        REPOSITORY_ROOT / "index.html",
        *sorted((REPOSITORY_ROOT / "site").rglob("*.html")),
    )

    for page in pages:
        html = page.read_text(encoding="utf-8")
        navigation = re.search(
            r'<nav class="site-nav"[^>]*>(.*?)</nav>', html, flags=re.DOTALL
        )
        assert navigation is not None, page
        links = re.findall(
            r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            navigation.group(1),
            flags=re.DOTALL,
        )
        first_two_labels = [
            re.sub(r"<[^>]+>", "", label).strip() for _, label in links[:2]
        ]
        expected_play_href = (
            os.path.relpath(REPOSITORY_ROOT / "play", page.parent).replace("\\", "/")
            + "/"
        )

        assert first_two_labels == ["Home", "Play"], page
        assert links[1][0] == expected_play_href, page


def test_branch_playtest_runtime_archive_is_not_ignored():
    gitignore = (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8")

    for archive in (
        "!play/game/dd_runtime.zip",
        "!play/qualification/game/dd_runtime.zip",
    ):
        assert archive in gitignore


def test_pages_workflow_validates_branch_playtest_without_deploying_it():
    workflow = WORKFLOW_PATH.read_text()

    for required in (
        "branches:\n      - pyodide",
        "actions/checkout@v6",
        "actions/setup-python@v6",
        "python tools/build_browser_site.py --output ../play",
        "git -C .. status --porcelain --untracked-files=all -- play",
    ):
        assert required in workflow
    assert "actions/upload-pages-artifact" not in workflow
    assert "actions/deploy-pages" not in workflow
    assert "pages: write" not in workflow
    assert "id-token: write" not in workflow


def test_pages_artifact_does_not_include_tests_or_docs(tmp_path):
    output = tmp_path / "site"
    site_builder.build_site(ROOT / "src", output)
    files = tuple(path.relative_to(output).as_posix() for path in output.rglob("*"))

    assert all(not path.startswith(("tests/", "web_tests/", "docs/")) for path in files)
    assert all(not path.endswith((".pyc", ".pytest_cache")) for path in files)
