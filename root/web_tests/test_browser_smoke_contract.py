from pathlib import Path


ROOT = Path(__file__).parents[1]
SMOKE_PATH = ROOT / "web_tests" / "browser_smoke.mjs"


def test_headless_smoke_uses_real_browser_and_authoritative_signals():
    source = SMOKE_PATH.read_text()

    for required in (
        'import { chromium } from "playwright"',
        "chromium.launch({ headless: true })",
        'getByRole("heading", { name: "Browser Playtest" })',
        'getByRole("button", { name: "Enter Encounter" })',
        'getByRole("button", { name: "Attack" })',
        'locator("#moves button:not(:disabled)")',
        'locator("#targets button:not(:disabled)")',
        'goto(`${baseUrl}/qualification/`',
        'PYD2|PASS',
        "surface_dungeon_entrance",
        "L9 EXP 68 GP 24 Gold 75",
        "PYD7|BROWSER|COMPLETION_SIGNAL|PASS",
    ):
        assert required in source

    assert "screenshot" not in source.lower()
    assert "damage" not in source
    assert "reward" not in source
    assert "route_complete =" not in source
