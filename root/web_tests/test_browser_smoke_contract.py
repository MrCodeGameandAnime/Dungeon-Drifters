from pathlib import Path


ROOT = Path(__file__).parents[1]
SMOKE_PATH = ROOT / "web_tests" / "browser_smoke.mjs"


def test_headless_smoke_uses_real_browser_and_authoritative_signals():
    source = SMOKE_PATH.read_text()

    for required in (
        'import { chromium } from "playwright"',
        "chromium.launch({ headless: true })",
        'locator("#overworld-screen").waitFor({ state: "visible" })',
        'locator(".app-header").innerText()',
        'locator("#immersive").isVisible()',
        'locator("#sound-toggle").isVisible()',
        'locator("#restart").isVisible()',
        "header did not retain only browser utility controls",
        'locator("#selection-screen").waitFor({ state: "visible" })',
        'locator("#drifter-options [data-drifter-id]")',
        'data-drifter-id="azhvielle"',
        'getByRole("button", { name: "Start" })',
        'getByRole("button", { name: "Loading..." })',
        'locator("#start-logo")',
        "Start did not request fullscreen and reveal Drifter selection",
        "Restart did not return to Drifter selection",
        "selecting a different Drifter after Restart did not start that character",
        "Fullscreen control did not show its inactive icon after exiting",
        "Fullscreen control did not show its active icon after re-entering",
        "Restart changed an already active fullscreen state",
        "Fullscreen icon did not follow an external fullscreen exit",
        "utility buttons did not show compact rendered icons",
        "header utilities do not align with the Overworld top line",
        'locator("#sound-toggle img")',
        "mobile Start did not request fullscreen from its user gesture",
        'captureScreenshot(targetPage, "mobile-start-screen")',
        'getByRole("button", { name: "Enter Encounter" })',
        'getByRole("button", { name: "Attack" })',
        'locator("#battle-status")',
        'locator("#battle-matchup")',
        'locator("#super-meter")',
        'getByRole("button", { name: "Back" })',
        'getByRole("button", { name: /Crestgrave Reaping/ })',
        "authoritative availability reason",
        "Move Selection omitted authoritative names, tags, resource costs, or rules summaries",
        "inactive interaction phases",
        'submittedTarget.target_id === "enemy_1"',
        "MULTI_TARGET_PROJECTION|PASS",
        "RESULT_TO_OVERWORLD|PASS",
        'goto(`${baseUrl}/qualification/`',
        'PYD2|PASS',
        "surface_dungeon_entrance",
        "L9 EXP 68 GP 24 Gold 75",
        "PYD7|BROWSER|COMPLETION_SIGNAL|PASS",
    ):
        assert required in source

    for screenshot in (
        "desktop-start-ready",
        "desktop-drifter-selection",
        "desktop-overworld",
        "desktop-battle-actions",
        "desktop-move-selection",
        "desktop-target-selection",
        "landscape-battle-actions",
        "landscape-move-selection",
        "mobile-start-ready",
    ):
        assert f'"{screenshot}"' in source
    assert 'await page.screenshot({ path: output })' in source
    assert "damage" not in source
    assert "reward" not in source
    assert "route_complete =" not in source
