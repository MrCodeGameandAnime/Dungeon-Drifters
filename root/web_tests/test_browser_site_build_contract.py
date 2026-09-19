import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
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
    assert (output / ".nojekyll").is_file()
    assert (output / "build-metadata.json").is_file()
    assert not (output / "app").exists()


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
    assert 'fetch("game/dd_runtime.zip")' in javascript
    assert 'fetch("python/dd_bridge.py")' in javascript
    assert "src=\"/" not in html
    assert "fetch(\"/" not in javascript


def test_pages_workflow_builds_and_deploys_the_static_site():
    workflow = WORKFLOW_PATH.read_text()

    for required in (
        "branches:\n      - pyodide",
        "actions/checkout@v6",
        "actions/setup-python@v6",
        "python -m pytest web_tests",
        "python tools/build_browser_site.py",
        "actions/upload-pages-artifact@v3",
        "actions/deploy-pages@v4",
        "pages: write",
        "id-token: write",
    ):
        assert required in workflow


def test_pages_artifact_does_not_include_tests_or_docs(tmp_path):
    output = tmp_path / "site"
    site_builder.build_site(ROOT / "src", output)
    files = tuple(path.relative_to(output).as_posix() for path in output.rglob("*"))

    assert all(not path.startswith(("tests/", "web_tests/", "docs/")) for path in files)
    assert all(not path.endswith((".pyc", ".pytest_cache")) for path in files)
