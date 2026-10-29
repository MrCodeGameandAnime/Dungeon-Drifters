from pathlib import Path


ROOT = Path(__file__).parents[1]
SMOKE_PATH = ROOT / "web_tests" / "browser_smoke.mjs"
SHELL_PATH = ROOT / "web" / "play" / "index.html"
SCRIPT_PATH = ROOT / "web" / "play" / "js" / "pyd4.js"


def test_headless_smoke_uses_real_browser_and_authoritative_signals():
    source = SMOKE_PATH.read_text()

    for required in (
        'import { chromium } from "playwright"',
        "const browserOptions = { headless: true }",
        "process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH",
        "chromium.launch(browserOptions)",
        'locator("#overworld-screen").waitFor({ state: "visible" })',
        'locator(".app-header").innerText()',
        'locator("#immersive").isVisible()',
        'locator("#sound-toggle").isVisible()',
        'locator("#restart").isVisible()',
        "header did not retain only browser utility controls",
        'locator("#selection-screen").waitFor({ state: "visible" })',
        'locator("#shortcut-dialog")',
        'locator("#shortcut-code")',
        'locator("#shortcut-error")',
        'page.keyboard.press("Shift+Alt+C")',
        "the picker-only shortcut opened before Start",
        "the picker-only shortcut opened during gameplay",
        "the Hub shortcut did not load its expected Branoc start state",
        "the Floor 1 shortcut did not load its Branoc/Azhvielle clear state",
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
        "const companionProjection = {",
        "const partyBattleProjection = {",
        "const extractionProjection = {",
        "const securedHubProjection = {",
        "window.__fixtureHubMode = true",
        'targetPage.locator("#companion-choices',
        'targetPage.locator("#party-members',
        'targetPage.locator("#extraction-rewards',
        'targetPage.locator("#hub-shared-gold',
        'targetPage.locator("#merchant-panel")',
        '"#merchant-targets button"',
        '"#merchant-slots .merchant-row"',
        '"#merchant-dismantle"',
        'targetPage.locator("#items-panel")',
        '"#items-list"',
        '"#character-targets button"',
        '"character_target", drifter_id: "azhvielle"',
        '"3 x Goblin Scrap"',
        "PYD9|BROWSER|SHARED_ITEMS_INSPECT|PASS",
        'clickVisibleOption(targetPage, "#overworld-options", "Merchant")',
        'PYD8|BROWSER|HUB_MERCHANT|PASS',
        '"Shared gold: 19"',
        '"Recruitment cost: 65"',
        '"120 EXP | 9 gold"',
        "PYD7|BROWSER|HUB_OUTING|PASS",
        "PYD7|BROWSER|DEFEAT_RESELECT|PASS",
        "floorOneWarningProjection",
        "floorOneRestProjection",
        "floorOneExtractionProjection",
        "FLOOR_ONE_BATTLE_10",
        "FLOOR_ONE_REPLAY_MIDWAY_REST",
        "FLOOR_ONE_REPLAY_EXTRACT|PASS",
        "FLOOR_ONE_BOSS_CLEAR|PASS",
    ):
        assert required in source

    for screenshot in (
        "desktop-start-ready",
        "desktop-drifter-selection",
        "desktop-overworld",
        "desktop-battle-actions",
        "desktop-move-selection",
        "desktop-target-selection",
        "desktop-floor-one-hub",
        "desktop-hub-party-battle",
        "desktop-hub-extraction",
        "landscape-battle-actions",
        "landscape-move-selection",
        "mobile-start-ready",
    ):
        assert f'"{screenshot}"' in source
    assert 'await page.screenshot({ path: output })' in source
    assert "damage =" not in source
    assert "reward =" not in source
    assert "route_complete =" not in source


def test_browser_shell_wires_component_crafting_and_weapon_configuration():
    shell = SHELL_PATH.read_text()
    script = SCRIPT_PATH.read_text()
    smoke = SMOKE_PATH.read_text()

    assert 'id="merchant-component-recipes"' in shell
    assert 'id="weapon-targets"' in shell
    assert 'id="weapon-identities"' in shell
    assert 'id="weapon-components"' in shell
    assert 'kind: "merchant_craft_component"' in script
    assert 'kind: "weapon_target"' in script
    assert 'kind: "weapon_component"' in script
    assert 'targetPage.locator("#weapon-components .weapon-component-slot")' in smoke
    assert "PYD8|BROWSER|HUB_WEAPON_COMPONENTS|PASS" in smoke


def test_browser_shell_exposes_shared_items_and_item_inspection():
    shell = SHELL_PATH.read_text()
    script = SCRIPT_PATH.read_text()

    assert 'id="items-panel"' in shell
    assert 'id="items-list"' in shell
    assert 'id="items-inspection"' in shell
    assert 'id="items-options"' in shell
    assert "function renderOverworldItems(view)" in script
    assert 'view.screen === "item_inspect"' in script
    assert '{ kind: "overworld_item", selection_key: item.selection_key }' in script
