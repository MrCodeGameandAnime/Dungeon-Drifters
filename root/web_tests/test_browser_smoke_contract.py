from pathlib import Path


ROOT = Path(__file__).parents[1]
SMOKE_PATH = ROOT / "web_tests" / "browser_smoke.mjs"
SHELL_PATH = ROOT / "web" / "play" / "index.html"
SCRIPT_PATH = ROOT / "web" / "play" / "js" / "pyd4.js"
CSS_PATH = ROOT / "web" / "play" / "styles.css"


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
        'clickVisibleOption(targetPage, "#overworld-options", "Vendors")',
        'clickVisibleOption(targetPage, "#vendors-options", "Blacksmith")',
        'PYD8|BROWSER|HUB_BLACKSMITH|PASS',
        'clickVisibleOption(page, "#overworld-options", "Hub Inventory")',
        '"Shared gold: 19"',
        '"Recruitment cost: 65"',
        '"120 EXP | 9 gold"',
        "PYD7|BROWSER|HUB_OUTING|PASS",
        "M8.1_BROWSER|REGION_PORTAL_FLOOR_I_RETURN_AND_BACKWARD_ACCESS|PASS",
        "M8.3_BROWSER|FLOOR_FOUR_ENTRY_AND_PAIR|PASS",
        "M8.3_BROWSER|FLOOR_FOUR_MIDPOINT_SAVE_RELOAD|PASS",
        "M8.3_BROWSER|FLOOR_FOUR_BOSS_CLEAR_AND_REWARDS|PASS",
        "PYD7|BROWSER|DEFEAT_RESELECT|PASS",
        "PYD7|BROWSER|SAVE_RELOAD|PASS",
        "F1_BROWSER|CONTINUE_REPLACE_CANCEL|PASS",
        "F1_BROWSER|INVALID_SAVE_PRESERVED|PASS",
        "PYD7|BROWSER|WEAPON_SAVE_RELOAD|PASS",
        "Crafted Reinforced Blade and Guard",
        "Installed: Reinforced Blade and Guard",
        "browser Continue did not restore Branoc's weapon progression",
        "startup Continue did not restore the saved Drifter and route",
        'locator("#saved-game-dialog")',
        'locator("#save-replacement-dialog")',
        'locator("#save-unavailable-dialog")',
        'getByRole("button", { name: "Continue" })',
        'getByRole("button", { name: "Replace Saved Game" })',
        'getByRole("button", { name: "Try Again" })',
        "floorOneWarningProjection",
        "floorOneRestProjection",
        "floorOneExtractionProjection",
        "FLOOR_ONE_BATTLE_10",
        "FLOOR_ONE_REPLAY_MIDWAY_REST",
        "FLOOR_ONE_REPLAY_EXTRACT|PASS",
        "FLOOR_ONE_BOSS_CLEAR|PASS",
        "M4_BROWSER|FLOOR_THREE_ORDINARY_PAIR|PASS",
        "M4_BROWSER|FLOOR_THREE_REST_SAVE_RELOAD|PASS",
        "M4_BROWSER|FLOOR_THREE_FOUR_MEMBER_BOSS_CLEAR|PASS",
        "M4_BROWSER|FLOOR_THREE_CLEAR_SAVE_RELOAD|PASS",
    ):
        assert required in source

    save_reload = source.index('"PYD7|BROWSER|WEAPON_SAVE_RELOAD|PASS"')
    qualification_page = source.index("const qualification = page;", save_reload)
    qualification = source.index('goto(`${baseUrl}/qualification/`', qualification_page)
    assert save_reload < qualification_page < qualification
    assert "await page.close();" not in source[save_reload:qualification]

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


def test_browser_shell_wires_craft_and_install_and_component_inspection():
    shell = SHELL_PATH.read_text()
    script = SCRIPT_PATH.read_text()
    smoke = SMOKE_PATH.read_text()

    assert 'id="merchant-component-recipes"' in shell
    assert 'id="merchant-tier-v"' in shell
    assert 'id="weapon-targets"' in shell
    assert 'id="weapon-identities"' in shell
    assert 'id="weapon-components"' in shell
    assert 'kind: "merchant_craft_component"' in script
    assert 'kind: "merchant_tier_v"' in script
    assert 'kind: "weapon_target"' in script
    assert '"Craft & Install"' in script
    assert 'kind: "weapon_component"' not in script
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


def test_browser_smoke_persists_active_pair_and_exact_member_progression():
    source = SMOKE_PATH.read_text()

    for required in (
        'clickVisibleOption(page, "#overworld-options", "Choose Party")',
        '"Azhvielle, the Unconfessed + Ser Branoc, the Unbroken Crest"',
        'clickVisibleOption(page, "#skills-targets", "Azhvielle, the Unconfessed")',
        '"Growth Points:"',
        'M3_BROWSER|ADVANCEMENT_SAVE_RELOAD|PASS',
        'M3_BROWSER|ADVANCEMENT_MOVE_USED|PASS',
        'M1_BROWSER|ACTIVE_PAIR_SAVE_RELOAD|PASS',
        "saved active-pair selection did not survive browser reload",
        "Azhvielle's skills, loadout, or stat investment did not survive browser reload",
        'M3_BROWSER|RESPEC_SAVE_RELOAD|PASS',
    ):
        assert required in source

    pair_return = source.index('const restoredActivePair =')
    back = source.index('clickVisibleOption(page, "#overworld-options", "Back")', pair_return)
    hub_ready = source.index('textContent.trim() === "HUB"', back)
    character = source.index('clickVisibleOption(page, "#overworld-options", "Character")', back)
    assert back < hub_ready < character


def test_browser_smoke_covers_m65_professions_and_mana_potion():
    source = SMOKE_PATH.read_text()

    for required in (
        'M65_BROWSER|ALCHEMY_PROFESSION_RECIPE_FLOW|PASS',
        'M65_BROWSER|ENCHANTER_LEARNED_AFFIX_RELOAD|PASS',
        'M65_BROWSER|MANA_POTION_TARGETING|PASS',
        'm65ProfessionFixtures.hub',
        'Alchemy Level 2 | 50 XP',
        'Enchanting Level 1 | 0 XP',
        'Choose a Drifter for Mana',
        'Applied learned affix Bastion.',
        'Crafted 1 Smoke Bomb; gained 15 Alchemy XP.',
        'Crafted 1 Mana Potion; gained 20 Alchemy XP.',
    ):
        assert required in source

    assert 'craftAlchemy("Smoke Powder")' not in source


def test_floor_four_pack_waits_for_hub_inventory_render():
    source = SMOKE_PATH.read_text()
    floor_three_clear = source.index("M4_BROWSER|FLOOR_THREE_CLEAR_SAVE_RELOAD|PASS")
    inventory_click = source.index(
        'await clickVisibleOption(page, "#overworld-options", "Hub Inventory");',
        floor_three_clear,
    )
    first_inventory_read = source.index("const carriedBeforeFloorFour", inventory_click)
    inventory_transition = source[inventory_click:first_inventory_read]

    assert "await page.waitForFunction" in inventory_transition
    assert 'const title = document.getElementById("hub-economy-title")?.textContent.trim()' in inventory_transition
    assert 'title === "Hub Inventory"' in inventory_transition
    assert 'document.getElementById("hub-economy-panel")' in inventory_transition
    assert "!panel.hidden" in inventory_transition


def test_browser_skills_panel_exposes_purchase_loadout_and_respec_contracts():
    shell = SHELL_PATH.read_text()
    script = SCRIPT_PATH.read_text()

    for element_id in (
        "skill-advancement",
        "skill-loadout",
        "skill-available-moves",
        "respec-panel",
        "respec-stat-points",
        "respec-skills",
        "respec-result-stats",
    ):
        assert f'id="{element_id}"' in shell
    assert 'kind: "advancement_purchase"' in script
    assert 'kind: "advancement_equip"' in script
    assert 'view.screen === "respec_confirmation"' in script
    assert 'view.respec_preview' in script


def test_battle_momentum_meter_renders_python_projection_accessibly():
    shell = SHELL_PATH.read_text()
    script = SCRIPT_PATH.read_text()
    styles = CSS_PATH.read_text()
    smoke = SMOKE_PATH.read_text()

    assert 'id="momentum-meter"' in shell
    assert 'id="momentum-track"' in shell
    assert 'role="meter"' in shell
    assert 'id="momentum-control"' in shell
    assert 'id="momentum-bonuses"' in shell
    assert "function renderMomentumMeter(momentum)" in script
    assert "renderMomentumMeter(view.momentum)" in script
    for field in (
        "momentum.position",
        "momentum.control_label",
        "momentum.critical_bonus_percent_points",
        "momentum.outgoing_damage_bonus_percent",
        "momentum.incoming_mitigation_percent",
    ):
        assert field in script
    assert ".momentum-track" in styles
    assert 'locator("#momentum-meter")' in smoke
    assert 'momentum: { position: 2, control_label: "Enemies +3", critical_bonus_percent_points: 6, outgoing_damage_bonus_percent: 5, incoming_mitigation_percent: 5 }' in smoke
    assert "M7_BROWSER|MOMENTUM_PROJECTION|PASS" in smoke


def test_browser_momentum_neutral_is_checked_without_racing_opening_attacks():
    smoke = SMOKE_PATH.read_text()

    assert 'assertMomentumNeutral(targetPage, "deterministic neutral projection")' in smoke
    assert 'assertMomentumNeutral(page, "first browser encounter")' not in smoke
    assert 'assertMomentumNeutral(page, `${floorLabel} Battle ${battleNumber}`)' not in smoke
    assert '"deterministic neutral projection"' in smoke
    assert "await observeMomentum(page);" in smoke


def test_region_portal_uses_python_projected_choices_in_both_browser_screens():
    shell = SHELL_PATH.read_text()
    script = SCRIPT_PATH.read_text()

    assert 'id="region-panel"' in shell
    assert 'id="region-choices"' in shell
    assert 'id="region-facts"' in shell
    assert 'kind: "region"' in script
    assert 'kind: "destination"' in script
    assert 'view.region_choices || []' in script
    assert 'view.destination_choices || []' in script
