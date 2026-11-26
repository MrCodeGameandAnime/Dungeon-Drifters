import { chromium } from "playwright";
import { execFileSync } from "node:child_process";
import { mkdir } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const baseUrl = (process.argv[2] || "http://127.0.0.1:8765").replace(/\/$/, "");
const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const pythonCandidates = [
  process.env.PYTHON,
  ...(process.platform === "win32"
    ? [path.resolve(repositoryRoot, "..", ".venv", "Scripts", "python.exe"), "python3"]
    : ["python3"]),
].filter((candidate, index, candidates) => candidate && candidates.indexOf(candidate) === index);
let floorTwoProfileEnvelope;
let m5EquipmentFixtures;
let m6ExpeditionFixtures;
let m65ProfessionFixtures;
let m8DiscoveryFixtures;
let m85ExpeditionFixture;
for (const pythonExecutable of pythonCandidates) {
  try {
    floorTwoProfileEnvelope = execFileSync(
      pythonExecutable,
      [path.join(repositoryRoot, "web_tests", "floor_two_browser_save_fixture.py")],
      { cwd: repositoryRoot, encoding: "utf8", maxBuffer: 1024 * 1024 },
    ).trim();
    m5EquipmentFixtures = JSON.parse(execFileSync(
      pythonExecutable,
      [path.join(repositoryRoot, "web_tests", "m5_browser_save_fixtures.py")],
      { cwd: repositoryRoot, encoding: "utf8", maxBuffer: 1024 * 1024 },
    ));
    m6ExpeditionFixtures = JSON.parse(execFileSync(
      pythonExecutable,
      [path.join(repositoryRoot, "web_tests", "m6_browser_save_fixture.py")],
      { cwd: repositoryRoot, encoding: "utf8", maxBuffer: 1024 * 1024 },
    ));
    m65ProfessionFixtures = JSON.parse(execFileSync(
      pythonExecutable,
      [path.join(repositoryRoot, "web_tests", "m65_profession_browser_fixture.py")],
      { cwd: repositoryRoot, encoding: "utf8", maxBuffer: 1024 * 1024 },
    ));
    m8DiscoveryFixtures = JSON.parse(execFileSync(
      pythonExecutable,
      [path.join(repositoryRoot, "web_tests", "m8_discovery_browser_fixtures.py")],
      { cwd: repositoryRoot, encoding: "utf8", maxBuffer: 1024 * 1024 },
    ));
    m85ExpeditionFixture = JSON.parse(execFileSync(
      pythonExecutable,
      [path.join(repositoryRoot, "web_tests", "m85_expedition_browser_fixture.py")],
      { cwd: repositoryRoot, encoding: "utf8", maxBuffer: 1024 * 1024 },
    ));
    break;
  } catch (error) {
    if (!new Set(["ENOENT", "EACCES"]).has(error.code)) throw error;
  }
}
if (!floorTwoProfileEnvelope) {
  throw new Error(`could not generate the Floor II browser save fixture with: ${pythonCandidates.join(", ")}`);
}
if (!m5EquipmentFixtures?.hub || !m5EquipmentFixtures?.outing) {
  throw new Error("could not generate the M5 equipment browser save fixtures");
}
if (!m6ExpeditionFixtures?.hub) {
  throw new Error("could not generate the M6 expedition browser save fixture");
}
if (!m65ProfessionFixtures?.hub) {
  throw new Error("could not generate the M6.5 profession browser save fixture");
}
if (!m8DiscoveryFixtures?.ancient_well || !m8DiscoveryFixtures?.forgotten_altar) {
  throw new Error("could not generate the M8 discovery browser save fixtures");
}
if (!m85ExpeditionFixture?.envelope || !m85ExpeditionFixture?.profile_key) {
  throw new Error("could not generate the M8.5 expedition browser save fixture");
}
const errors = [];
const observedMomentumLabels = new Set();
const pendingRequests = new Map();
const screenshotDirectory = path.join(os.tmpdir(), "dd-pd-ui3-evidence");
await mkdir(screenshotDirectory, { recursive: true });

async function observeMomentum(page) {
  const state = await page.locator("#momentum-track").evaluate((track) => ({
    position: Number(track.getAttribute("aria-valuenow")),
    label: document.getElementById("momentum-control").textContent.trim(),
    valueText: track.getAttribute("aria-valuetext"),
    markerPositionError: (() => {
      const trackRect = track.getBoundingClientRect();
      const markerRect = document.getElementById("momentum-marker").getBoundingClientRect();
      const actual = markerRect.left + markerRect.width / 2 - trackRect.left;
      return Math.abs(actual - trackRect.width * Number(track.getAttribute("aria-valuenow")) / 10);
    })(),
  }));
  requireCondition(
    state.markerPositionError <= 2,
    `Momentum marker does not follow its authoritative value: ${JSON.stringify(state)}`,
  );
  observedMomentumLabels.add(state.label.replace(/^Momentum \d+\/10 - /, ""));
  return state;
}

async function assertMomentumNeutral(page, label) {
  const state = await observeMomentum(page);
  requireCondition(
    state.position === 5 && state.label === "Momentum 5/10 - Neutral",
    `${label} did not start at neutral Momentum: ${JSON.stringify(state)}`,
  );
}

async function captureScreenshot(page, name) {
  const output = path.join(screenshotDirectory, `${name}.png`);
  await page.screenshot({ path: output });
  console.log(`PD|UI3|SCREENSHOT|${name}|${output}`);
}

async function scrollWithinControls(locator) {
  await locator.evaluate((element) => {
    const panel = document.getElementById("controls-panel");
    panel.scrollTop += element.getBoundingClientRect().top - panel.getBoundingClientRect().top;
  });
}

async function waitForViewportSync(page, width, height) {
  await page.waitForFunction(({ expectedWidth, expectedHeight }) =>
    window.innerWidth === expectedWidth &&
      window.innerHeight === expectedHeight &&
      getComputedStyle(document.documentElement).getPropertyValue("--app-height").trim() === `${expectedHeight}px`,
  { expectedWidth: width, expectedHeight: height });
}

async function inspectMobileSelection(page) {
  return page.evaluate(() => {
    const selection = document.getElementById("selection-screen");
    const grid = document.getElementById("drifter-options");
    const title = document.getElementById("selection-title").getBoundingClientRect();
    const header = document.querySelector(".app-header").getBoundingClientRect();
    const selectionRect = selection.getBoundingClientRect();
    const cards = [...grid.querySelectorAll("[data-drifter-id]")].map((button) => ({
      buttonTop: button.getBoundingClientRect().top,
      buttonBottom: button.getBoundingClientRect().bottom,
      summaryBottom: button.querySelector(".drifter-option-summary").getBoundingClientRect().bottom,
    }));
    return {
      viewport: { width: window.innerWidth, height: window.innerHeight },
      columns: getComputedStyle(grid).gridTemplateColumns.split(" ").length,
      titleHeaderCenterGap: Math.abs(
        (title.top + title.bottom) / 2 - (header.top + header.bottom) / 2,
      ),
      pageHeight: document.documentElement.scrollHeight,
      selectionHeight: selection.clientHeight,
      selectionScrollHeight: selection.scrollHeight,
      selectionTop: selectionRect.top,
      selectionBottom: selectionRect.bottom,
      titleBottom: title.bottom,
      cards,
    };
  });
}

function mobileSelectionFits(layout) {
  const rowTop = Math.min(...layout.cards.map((card) => card.buttonTop));
  const rowBottom = Math.max(...layout.cards.map((card) => card.buttonBottom));
  const spaceAboveCards = rowTop - layout.titleBottom;
  const spaceBelowCards = layout.selectionBottom - rowBottom;
  return layout.columns === 4 &&
    layout.titleHeaderCenterGap <= 18 &&
    layout.pageHeight <= layout.viewport.height &&
    layout.selectionScrollHeight <= layout.selectionHeight &&
    layout.cards.length === 4 &&
    layout.cards.every((card) =>
      card.buttonBottom <= layout.selectionBottom + 1 &&
      card.summaryBottom <= layout.selectionBottom + 1 &&
      card.buttonBottom - card.summaryBottom <= 12) &&
    Math.abs(spaceAboveCards - spaceBelowCards) <= 24;
}

async function inspectMobileOverworld(page) {
  return page.evaluate(() => {
    const screen = document.getElementById("overworld-screen");
    const screenRect = screen.getBoundingClientRect();
    const route = document.getElementById("route-panel").getBoundingClientRect();
    const controls = [...screen.querySelectorAll("#route-actions button, #overworld-options button")]
      .map((button) => {
        const rect = button.getBoundingClientRect();
        return {
          label: button.innerText.trim(),
          visible: rect.width > 0 && rect.height > 0,
          top: rect.top,
          bottom: rect.bottom,
        };
      });
    return {
      viewport: { width: innerWidth, height: innerHeight },
      pageHeight: document.documentElement.scrollHeight,
      bodyHeight: document.body.scrollHeight,
      screenClientHeight: screen.clientHeight,
      screenScrollHeight: screen.scrollHeight,
      screenOverflowY: getComputedStyle(screen).overflowY,
      screenTop: screenRect.top,
      screenBottom: screenRect.bottom,
      routeTop: route.top,
      routeBottom: route.bottom,
      controls,
    };
  });
}

function mobileOverworldFits(layout) {
  return layout.pageHeight <= layout.viewport.height &&
    layout.bodyHeight <= layout.viewport.height &&
    layout.screenOverflowY === "hidden" &&
    layout.screenScrollHeight <= layout.screenClientHeight + 1 &&
    layout.routeTop >= layout.screenTop - 1 &&
    layout.routeBottom <= layout.screenBottom + 1 &&
    layout.controls.length >= 5 &&
    layout.controls.every((control) => control.visible &&
      control.top >= layout.screenTop - 1 && control.bottom <= layout.screenBottom + 1);
}

async function mobileDetailLayout(page, panelId, navigationId) {
  return page.evaluate(({ activePanelId, activeNavigationId }) => {
    const overworld = document.getElementById("overworld-screen");
    const route = document.getElementById("route-panel");
    const activePanel = document.getElementById(activePanelId);
    const content = activePanel.querySelector(".detail-page-content");
    const navigation = document.getElementById(activeNavigationId);
    const screenRect = overworld.getBoundingClientRect();
    const navigationRect = navigation.getBoundingClientRect();
    const visibleDetails = Array.from(overworld.querySelectorAll(".overworld-detail-panel"))
      .filter((panel) => !panel.hidden && panel.getBoundingClientRect().width > 0)
      .map((panel) => panel.id);
    return {
      routeVisible: route.getBoundingClientRect().width > 0,
      visibleDetails,
      contentOverflowY: content ? getComputedStyle(content).overflowY : "missing",
      navigationBottomGap: screenRect.bottom - navigationRect.bottom,
      documentOverflowY: document.documentElement.scrollHeight > window.innerHeight + 1 ||
        document.body.scrollHeight > window.innerHeight + 1,
    };
  }, { activePanelId: panelId, activeNavigationId: navigationId });
}

async function assertMobileDetailView(page, panelId, navigationId, label) {
  const layout = await mobileDetailLayout(page, panelId, navigationId);
  requireCondition(
    !layout.routeVisible && layout.visibleDetails.join(",") === panelId &&
      layout.contentOverflowY === "auto" && layout.navigationBottomGap >= -1 &&
      layout.navigationBottomGap <= 24 && !layout.documentOverflowY,
    `${label} did not isolate its page with reachable bottom navigation: ${JSON.stringify(layout)}`,
  );
}

async function mobileCharacterLayout(page) {
  return page.evaluate(() => {
    const panel = document.getElementById("character-panel");
    const content = panel.querySelector(".detail-page-content");
    const stats = [...document.querySelectorAll("#character-stats .character-stat")]
      .map((stat) => {
        const rect = stat.getBoundingClientRect();
        return { name: stat.dataset.statName, text: stat.innerText.trim(), top: rect.top, left: rect.left };
      })
      .sort((first, second) => Math.abs(first.top - second.top) > 1
        ? first.top - second.top
        : first.left - second.left);
    const resources = document.getElementById("character-resources");
    const progress = document.getElementById("experience-progress");
    const progressRect = progress.getBoundingClientRect();
    const contentRect = content.getBoundingClientRect();
    return {
      name: document.getElementById("character-name").innerText.trim(),
      archetype: document.getElementById("character-archetype").innerText.trim(),
      stats,
      statColumns: getComputedStyle(document.getElementById("character-stats")).gridTemplateColumns.split(" ").length,
      level: document.getElementById("character-level").innerText.trim(),
      resources: [...resources.querySelectorAll(".status-line")].map((line) => line.innerText.trim()),
      resourceLayout: getComputedStyle(resources).display,
      progressVisible: !progress.hidden && progressRect.width > 0 && progressRect.height > 0,
      progressInsideContent: progressRect.left >= contentRect.left - 1 && progressRect.right <= contentRect.right + 1,
      contentFits: content.scrollHeight <= content.clientHeight + 1,
    };
  });
}

function mobileCharacterFits(layout) {
  return !layout.name.startsWith("[") && !layout.name.endsWith("]") &&
    layout.archetype.length > 0 &&
    layout.statColumns === 3 &&
    JSON.stringify(layout.stats.map((stat) => stat.name)) === JSON.stringify([
      "constitution", "spirit", "strength", "intelligence", "dexterity", "intuition",
    ]) &&
    layout.stats.every((stat) => stat.text.includes(":")) &&
    layout.level.startsWith("Level ") &&
    layout.resources.length === 3 && layout.resourceLayout === "flex" &&
    layout.progressVisible && layout.progressInsideContent && layout.contentFits;
}

async function inspectViewport(page) {
  return page.evaluate(() => {
    const root = document.documentElement;
    const body = document.body;
    const shell = document.getElementById("app");
    const battle = document.getElementById("battle-screen");
    const controls = document.getElementById("controls-panel");
    const battleRect = battle.getBoundingClientRect();
    const phaseIds = ["actions", "moves", "targets", "inventory"];
    return {
      viewportWidth: window.innerWidth,
      viewportHeight: window.innerHeight,
      pageOverflowX: root.scrollWidth > window.innerWidth + 1 || body.scrollWidth > window.innerWidth + 1,
      pageOverflowY: root.scrollHeight > window.innerHeight + 1 || body.scrollHeight > window.innerHeight + 1,
      documentSize: { rootWidth: root.clientWidth, rootHeight: root.clientHeight, rootScrollHeight: root.scrollHeight, bodyClientHeight: body.clientHeight, bodyScrollHeight: body.scrollHeight },
      documentScrollTop: document.scrollingElement.scrollTop,
      shellRect: (() => { const rect = shell.getBoundingClientRect(); return { top: rect.top, bottom: rect.bottom, height: rect.height, clientHeight: shell.clientHeight, scrollHeight: shell.scrollHeight }; })(),
      battleRect: { top: battleRect.top, bottom: battleRect.bottom, height: battleRect.height },
      battleStatusRect: (() => { const rect = document.getElementById("battle-status").getBoundingClientRect(); return { top: rect.top, bottom: rect.bottom }; })(),
      momentumRect: (() => { const rect = document.getElementById("momentum-meter").getBoundingClientRect(); return { top: rect.top, bottom: rect.bottom }; })(),
      momentumVisible: (() => { const element = document.getElementById("momentum-meter"); const rect = element.getBoundingClientRect(); return !element.hidden && getComputedStyle(element).display !== "none" && rect.width > 0 && rect.height > 0; })(),
      controlsRect: (() => { const rect = controls.getBoundingClientRect(); return { top: rect.top, bottom: rect.bottom }; })(),
      shellOverflowX: shell.scrollWidth > shell.clientWidth + 1,
      shellOverflowY: shell.scrollHeight > shell.clientHeight + 1,
      battleWithinViewport: battleRect.top >= -1 && battleRect.bottom <= window.innerHeight + 1,
      controlsOverflowY: getComputedStyle(controls).overflowY,
      controlsScrollable: controls.scrollHeight > controls.clientHeight + 1,
      activePhases: phaseIds.filter((id) => {
        const element = document.getElementById(id);
        const rect = element && element.getBoundingClientRect();
        return element && !element.hidden && getComputedStyle(element).display !== "none" && rect.width > 0 && rect.height > 0;
      }),
      orientationGuidanceVisible: getComputedStyle(document.getElementById("orientation-guidance")).display !== "none",
    };
  });
}

async function assertBattleViewport(page, expectedPhase, label) {
  const metrics = await inspectViewport(page);
  requireCondition(
    !metrics.pageOverflowX && !metrics.pageOverflowY && !metrics.shellOverflowX && !metrics.shellOverflowY,
    `${label} introduced page/shell scrolling or horizontal overflow: ${JSON.stringify(metrics)}`,
  );
  requireCondition(metrics.battleWithinViewport, `${label} clipped the active Battle surface: ${JSON.stringify(metrics)}`);
  requireCondition(
    metrics.momentumVisible && metrics.momentumRect.top >= -1 &&
      metrics.momentumRect.bottom <= metrics.viewportHeight + 1 &&
      metrics.momentumRect.bottom <= metrics.controlsRect.top + 1,
    `${label} hid, clipped, or overlapped the Momentum meter: ${JSON.stringify(metrics)}`,
  );
  requireCondition(
    metrics.activePhases.join(",") === expectedPhase,
    `${label} changed the active interaction phase: ${JSON.stringify(metrics.activePhases)}`,
  );
  await observeMomentum(page);
  return metrics;
}

async function controlSignature(page) {
  return page.locator("#actions button").evaluateAll((buttons) => buttons.map((button) => ({
    label: button.querySelector(".choice-label")?.textContent || button.textContent.trim(),
    disabled: button.disabled,
    reason: button.querySelector(".option-reason")?.textContent || "",
  })));
}

async function clickVisibleOption(page, containerSelector, label) {
  const button = page
    .locator(containerSelector)
    .getByText(label, { exact: true })
    .locator("xpath=ancestor::button[1]");
  const deadline = Date.now() + 3000;
  while (Date.now() < deadline) {
    try {
      if (await button.count() && await button.isEnabled()) {
        await button.click({ timeout: 500 });
        return;
      }
    } catch (error) {
      if (error.name !== "TimeoutError") {
        throw error;
      }
    }
    await page.waitForTimeout(50);
  }
  const state = await page.evaluate(({ selector }) => {
    const buttons = [...document.querySelectorAll(`${selector} button`)].map((button) => ({
      label: button.querySelector(".choice-label")?.textContent?.trim() || button.textContent.trim(),
      disabled: button.disabled,
      reason: button.querySelector(".option-reason")?.textContent?.trim() || "",
    }));
    const profileKey = "dungeon-drifters.profile.v1.d4d4d4d4-0000-4000-8000-000000000001";
    let save = { available: false };
    try {
      const raw = localStorage.getItem(profileKey);
      if (raw !== null) {
        const envelope = JSON.parse(raw);
        save = {
          available: true,
          length: raw.length,
          localSequence: envelope.local_sequence ?? null,
          syncState: envelope.sync_state ?? null,
          payloadSchema: envelope.payload?.schema_version ?? null,
        };
      }
    } catch (error) {
      save = { available: false, error: String(error) };
    }
    return {
      url: location.href,
      badge: document.getElementById("screen-badge")?.textContent?.trim() || "",
      notice: document.getElementById("notice")?.textContent?.trim() || "",
      buttons,
      save,
    };
  }, { selector: containerSelector });
  throw new Error(
    `offered control not found: ${label} in ${containerSelector}; state=${JSON.stringify(state)}`,
  );
}

async function restartForNewGame(page) {
  await page.locator("#restart").click();
  await page.waitForFunction(() => {
    const selection = document.getElementById("selection-screen");
    return !selection.hidden ||
      document.getElementById("saved-game-dialog").open ||
      document.getElementById("save-replacement-dialog").open ||
      document.getElementById("save-unavailable-dialog").open;
  });
  if (await page.locator("#saved-game-dialog").isVisible()) {
    await page.getByRole("button", { name: "New Game" }).click();
    await page.locator("#save-replacement-dialog").waitFor({ state: "visible" });
  }
  if (await page.locator("#save-replacement-dialog").isVisible()) {
    await page.getByRole("button", { name: "Replace Saved Game" }).click();
  }
  if (await page.locator("#save-unavailable-dialog").isVisible()) {
    throw new Error("restart opened the invalid-save recovery dialog");
  }
  await page.locator("#selection-screen").waitFor({ state: "visible" });
}

async function continueSavedGameAfterReload(page) {
  await page.getByRole("button", { name: "Start" }).click();
  await page.locator("#saved-game-dialog").waitFor({ state: "visible" });
  await page.getByRole("button", { name: "Continue" }).click();
  await page.locator("#overworld-screen").waitFor({ state: "visible" });
}

const targetProjection = {
  interaction_phase: "targets",
  player: {
    display_name: "Ser Branoc",
    hp_current: 88,
    hp_maximum: 116,
    mana_current: 31,
    mana_maximum: 46,
    super_current: 45,
    super_maximum: 100,
    defending: false,
    temporary_labels: [],
  },
  enemies: [
    { target_id: "enemy_1", display_label: "Goblin 1", hp_current: 60, hp_maximum: 60, temporary_labels: [], defeated: false },
    { target_id: "enemy_2", display_label: "Goblin 2", hp_current: 43, hp_maximum: 60, temporary_labels: ["Guarding"], defeated: false },
  ],
  super_meter: { current: 45, maximum: 100, fill_bps: 4500, ready: false, activation_key: "S", activation_offered: false },
  momentum: { position: 2, control_label: "Enemies +3", critical_bonus_percent_points: 6, outgoing_damage_bonus_percent: 5, incoming_mitigation_percent: 5 },
  encounter_label: "Goblin Pair",
  visual: { player_lines: ["Ser Branoc"], enemy_lines: [] },
  action_options: [],
  move_options: [],
  target_options: [
    {
      target_id: "enemy_1", number: 1, display_label: "Goblin 1", hp_current: 60, hp_maximum: 60,
      temporary_labels: [], enabled: true, disabled_reason: null,
      move_preview: { selection_key: "Crestgrave Reaping", number: 1, name: "Crestgrave Reaping", tags: ["Normal"], rules_summary: "Sunder-Spire tears through the target, cleaving guard and armor.", resource_label: null, enabled: true, disabled_reason: null },
    },
    {
      target_id: "enemy_2", number: 2, display_label: "Goblin 2", hp_current: 43, hp_maximum: 60,
      temporary_labels: ["Guarding"], enabled: false, disabled_reason: "target_unavailable",
      move_preview: { selection_key: "Crestgrave Reaping", number: 1, name: "Crestgrave Reaping", tags: ["Normal"], rules_summary: "Sunder-Spire tears through the target, cleaving guard and armor.", resource_label: null, enabled: true, disabled_reason: null },
    },
  ],
  inventory_items: [],
  selected_inventory_item: null,
  inventory_commands: [],
  inventory_inspection: null,
  inventory_companions: [],
  inventory_confirmation: null,
  log_entries: [],
};

const neutralTargetProjection = {
  ...targetProjection,
  momentum: {
    position: 5,
    control_label: "Neutral",
    critical_bonus_percent_points: 0,
    outgoing_damage_bonus_percent: 0,
    incoming_mitigation_percent: 0,
  },
};

const completeProjection = {
  ...targetProjection,
  interaction_phase: "complete",
  action_options: [],
  target_options: [],
};

const resultOverworldProjection = {
  screen: "main",
  location_label: "The road ahead",
  adventure_text: "Goblin Ambush is defeated. Rewards: 40 EXP and 3 gold. The route continues toward Goblin Pair.",
  options: [{ action: "character", label: "Character", enabled: true, disabled_reason: null }],
  contextual_route_option: { action: "enter_encounter", label: "Enter Encounter", enabled: true, disabled_reason: null },
  notice: null,
  character: {
    display_name: "Ser Branoc", hp_current: 88, hp_maximum: 116, mana_current: 31, mana_maximum: 46,
    super_current: 45, super_maximum: 100,
  },
};

const hubProjection = {
  screen: "hub",
  location_label: "Floor 1 Hub",
  adventure_text: "You have reached the Floor 1 Hub. Recruit one companion to continue.",
  options: [
    { action: "vendors", label: "Vendors", enabled: true, disabled_reason: null },
    { action: "hub_inventory", label: "Hub Inventory", enabled: true, disabled_reason: null },
    { action: "region_portal", label: "Region Portal", enabled: true, disabled_reason: null },
    { action: "recruit_companion", label: "Recruit Companion", enabled: true, disabled_reason: null },
    { action: "character", label: "Character", enabled: true, disabled_reason: null },
    { action: "items", label: "Items", enabled: true, disabled_reason: null },
    { action: "map", label: "Map", enabled: true, disabled_reason: null },
    { action: "options", label: "Options", enabled: true, disabled_reason: null },
  ],
  contextual_route_option: null,
  character: null,
  notice: null,
  shared_gold: 75,
};

const companionProjection = {
  ...hubProjection,
  screen: "companion_selection",
  adventure_text: "Choose one Drifter to join your party.",
  options: [{ action: "back", label: "Back", enabled: true, disabled_reason: null }],
  companion_choices: [
    { event_id: "floor_one_d2_recruitment", drifter_id: "azhvielle", display_name: "Azhvielle", archetype_label: "Black Mage | Elemental Controller", summary: "versatile, dangerous, unpredictable", cost: 65, enabled: true, disabled_reason: null },
    { event_id: "floor_one_d2_recruitment", drifter_id: "zhaivra", display_name: "Zhaivra Kelyth", archetype_label: "Rogue Archer | Alchemical Marksman", summary: "precise, prepared, resource-limited", cost: 65, enabled: true, disabled_reason: null },
    { event_id: "floor_one_d2_recruitment", drifter_id: "joruun", display_name: "Joruun Veyr", archetype_label: "Monk | Elemental Skirmisher", summary: "mobile, adaptable, physically costly", cost: 65, enabled: true, disabled_reason: null },
  ],
  recruitment_cost: 65,
};

const partyReadyProjection = {
  ...hubProjection,
  screen: "party_ready",
  adventure_text: "Your party is assembled and ready to set out.",
  shared_gold: 10,
  options: [
    { action: "ready", label: "Ready / Set Out", enabled: true, disabled_reason: null },
    { action: "region_portal", label: "Region Portal", enabled: true, disabled_reason: null },
    { action: "back", label: "Back", enabled: true, disabled_reason: null },
  ],
};

const partyBattleProjection = {
  ...targetProjection,
  interaction_phase: "actions",
  encounter_label: "Goblin Trio",
  enemies: [1, 2, 3].map((number) => ({
    target_id: `enemy_${number}`,
    display_label: `Goblin ${number}`,
    hp_current: 60,
    hp_maximum: 60,
    temporary_labels: [],
    defeated: false,
  })),
  party_members: [
    { target_id: "drifter_branoc", display_name: "Ser Branoc", hp_current: 116, hp_maximum: 116, mana_current: 46, mana_maximum: 46, super_current: 0, super_maximum: 100, defending: false, temporary_labels: [], active: true },
    { target_id: "drifter_azhvielle", display_name: "Azhvielle", hp_current: 92, hp_maximum: 92, mana_current: 70, mana_maximum: 70, super_current: 0, super_maximum: 100, defending: false, temporary_labels: [], active: false },
  ],
  action_options: [{ intent: "defend", label: "Defend", enabled: true, disabled_reason: null }],
  target_options: [],
  log_entries: [],
};

const extractionProjection = {
  screen: "extraction",
  location_label: "Floor 1 Hub",
  adventure_text: "The Goblin trio is defeated. Return to the hub to secure your rewards.",
  options: [{ action: "return_to_hub", label: "Return to Hub", enabled: true, disabled_reason: null }],
  contextual_route_option: null,
  character: null,
  notice: null,
  outing_rewards: {
    experience: 120,
    gold: 9,
    items: [{ item_id: "goblin_scrap", display_name: "Goblin Scrap", quantity: 3 }],
  },
};

const securedHubProjection = {
  ...hubProjection,
  adventure_text: "You return to the Floor 1 Hub. The tutorial rewards are secured.",
  shared_gold: 19,
  options: [
    { action: "vendors", label: "Vendors", enabled: true, disabled_reason: null },
    { action: "hub_inventory", label: "Hub Inventory", enabled: true, disabled_reason: null },
    { action: "region_portal", label: "Region Portal", enabled: true, disabled_reason: null },
    ...hubProjection.options.slice(4),
    { action: "select_party", label: "Choose Party", enabled: true, disabled_reason: null },
    { action: "start_floor_one", label: "Start Floor 1", enabled: true, disabled_reason: null },
  ],
};

const regionPortalProjection = {
  ...securedHubProjection,
  screen: "region_portal",
  adventure_text: "Choose a region to review its available destinations.",
  options: [{ action: "back", label: "Back", enabled: true, disabled_reason: null }],
  region_choices: [
    { region_id: "region_1", display_name: "Region 1", unlocked: true, selectable: true, message: null },
  ],
};

const regionDestinationsProjection = {
  ...regionPortalProjection,
  screen: "region_destinations",
  adventure_text: "The Drowned Reliquary remains unknown.",
  region_choices: [],
  destination_choices: [
    { destination_id: "floor_one", display_name: "Floor I", enabled: true, disabled_reason: null, knowledge_status: null },
    { destination_id: "floor_two", display_name: "Floor II", enabled: false, disabled_reason: "Requires Floor I clear.", knowledge_status: null },
  ],
  knowledge_facts: [],
};

const regionDestinationsClearedProjection = {
  ...regionDestinationsProjection,
  adventure_text: "Floor II is available. The Drowned Reliquary remains unknown.",
  destination_choices: [
    { destination_id: "floor_one", display_name: "Floor I", enabled: true, disabled_reason: null, knowledge_status: null },
    { destination_id: "floor_two", display_name: "Floor II", enabled: true, disabled_reason: null, knowledge_status: null },
  ],
};

const vendorsProjection = {
  ...securedHubProjection,
  screen: "vendors",
  options: [
    { action: "merchant", label: "Merchant", enabled: true, disabled_reason: null },
    { action: "blacksmith", label: "Blacksmith", enabled: true, disabled_reason: null },
    { action: "enchanter", label: "Enchanter", enabled: true, disabled_reason: null },
    { action: "alchemist", label: "Alchemist", enabled: true, disabled_reason: null },
    { action: "back", label: "Back", enabled: true, disabled_reason: null },
  ],
};

const partySelectionProjection = {
  ...securedHubProjection,
  screen: "party_selection",
  adventure_text: "Choose the two Drifters for your next outing.",
  options: [{ action: "back", label: "Back", enabled: true, disabled_reason: null }],
  active_drifter_ids: ["branoc", "azhvielle"],
  active_party_choices: [
    ["branoc", "azhvielle", "Ser Branoc", "Azhvielle", true],
    ["branoc", "joruun", "Ser Branoc", "Joruun Veyr", false],
    ["azhvielle", "branoc", "Azhvielle", "Ser Branoc", false],
    ["azhvielle", "joruun", "Azhvielle", "Joruun Veyr", false],
    ["joruun", "branoc", "Joruun Veyr", "Ser Branoc", false],
    ["joruun", "azhvielle", "Joruun Veyr", "Azhvielle", false],
  ].map(([first, second, firstName, secondName, selected]) => ({
    drifter_ids: [first, second],
    display_names: [firstName, secondName],
    selected,
  })),
};

const partyChosenProjection = {
  ...securedHubProjection,
  adventure_text: "Party selected for the next outing.",
};

const itemsProjection = {
  ...securedHubProjection,
  screen: "items",
  options: [
    { action: "inspect", label: "Inspect", enabled: false, disabled_reason: "no_item_selected" },
    { action: "back", label: "Back", enabled: true, disabled_reason: null },
  ],
  inventory: {
    items: [{ selection_key: "shared-item:goblin_scrap", display_name: "Goblin Scrap", quantity: 3, description: "Goblin remains suitable for dismantling.", overworld_use_enabled: false, location_label: "Hub Storage" }],
    selected_item_key: null,
    inspected_item: null,
  },
};

const itemsSelectedProjection = {
  ...itemsProjection,
  options: [
    { action: "inspect", label: "Inspect", enabled: true, disabled_reason: null },
    { action: "back", label: "Back", enabled: true, disabled_reason: null },
  ],
  inventory: { ...itemsProjection.inventory, selected_item_key: "shared-item:goblin_scrap" },
};

const itemInspectionProjection = {
  ...itemsProjection,
  screen: "item_inspect",
  options: [{ action: "back", label: "Back", enabled: true, disabled_reason: null }],
  inventory: {
    ...itemsSelectedProjection.inventory,
    inspected_item: itemsProjection.inventory.items[0],
  },
};

const merchantProjection = {
  ...securedHubProjection,
  screen: "blacksmith",
  options: [{ action: "back", label: "Back", enabled: true, disabled_reason: null }],
  merchant: {
    crafting_level: 1,
    crafting_experience: 12,
    targets: [
      { drifter_id: "branoc", display_name: "Ser Branoc", selected: true },
      { drifter_id: "azhvielle", display_name: "Azhvielle", selected: false },
    ],
    selected_target_id: "branoc",
    weapon_name: "Sunder-Spire",
    slots: [
      { slot_id: "blade_guard", label: "Blade / Guard assembly", material_family: "metal", progress: 0, material_id: "grade_i_metal", material_name: "Scrap metal", material_cost: 1, material_quantity: 3, can_improve: true, blocked_reason: null },
      { slot_id: "grip_binding", label: "Grip wrap / binding", material_family: "fiber", progress: 0, material_id: "grade_i_fiber", material_name: "Cord", material_cost: 1, material_quantity: 0, can_improve: false, blocked_reason: "insufficient_materials" },
      { slot_id: "hilt_handle", label: "Hilt core / handle", material_family: "timber", progress: 0, material_id: "grade_i_timber", material_name: "Softwood", material_cost: 1, material_quantity: 0, can_improve: false, blocked_reason: "insufficient_materials" },
      { slot_id: "crest_core", label: "Crest / Core", material_family: "cores", progress: 0, material_id: "grade_i_cores", material_name: "Faded Core", material_cost: 1, material_quantity: 0, can_improve: false, blocked_reason: "insufficient_materials" },
    ],
    materials: [
      { item_id: "grade_i_metal", display_name: "Scrap metal", quantity: 3 },
      { item_id: "grade_i_fiber", display_name: "Cord", quantity: 0 },
      { item_id: "grade_i_timber", display_name: "Softwood", quantity: 0 },
      { item_id: "grade_i_cores", display_name: "Faded Core", quantity: 0 },
    ],
    dismantle_items: [
      { item_id: "goblin_scrap", display_name: "Goblin Scrap", quantity: 3, output_material_names: ["Scrap metal", "Cord", "Softwood"], maximum_yield: 2 },
    ],
    component_recipes: [
      { component_id: "sunder_spire_blade_reinforced", display_name: "Reinforced Blade and Guard", slot_id: "blade_guard", slot_label: "Blade / Guard assembly", material_name: "Scrap metal", material_cost: 1, material_quantity: 3, crafting_award: 10, can_craft: true, effect_summary: ["Crestgrave Reaping: Power +2, Accuracy -2", "Heavy identity +1"] },
    ],
    tier_v: {
      success_chance_percent: 20,
      materials: [
        { item_id: "grade_iv_metal", display_name: "Etheral Alloy", required: 12, available: 0 },
        { item_id: "grade_iv_fiber", display_name: "Carbon", required: 12, available: 0 },
        { item_id: "grade_iv_timber", display_name: "Elderwood", required: 12, available: 0 },
        { item_id: "grade_iv_cores", display_name: "Singularity Core", required: 12, available: 0 },
      ],
      can_attempt: false,
      completed: false,
      blocked_reason: "tier_locked",
    },
  },
};

const merchantAzhvielleProjection = {
  ...merchantProjection,
  merchant: {
    ...merchantProjection.merchant,
    selected_target_id: "azhvielle",
    weapon_name: "Needle of Plain Iron",
    targets: merchantProjection.merchant.targets.map((target) => ({
      ...target,
      selected: target.drifter_id === "azhvielle",
    })),
    slots: [
      { slot_id: "focus_fittings", label: "Focus head / fittings", material_family: "metal", progress: 0, material_id: "grade_i_metal", material_name: "Scrap metal", material_cost: 1, material_quantity: 3, can_improve: true, blocked_reason: null },
      { slot_id: "binding", label: "Binding", material_family: "fiber", progress: 0, material_id: "grade_i_fiber", material_name: "Cord", material_cost: 1, material_quantity: 0, can_improve: false, blocked_reason: "insufficient_materials" },
      ...merchantProjection.merchant.slots.slice(2),
    ],
    component_recipes: [
      { component_id: "needle_focus_fitted", display_name: "Obsidian Focus Fittings", slot_id: "focus_fittings", slot_label: "Focus head / fittings", material_name: "Scrap metal", material_cost: 1, crafting_award: 10, material_quantity: 3, can_craft: true, effect_summary: ["Scepter Sweep: Power +2, Resource cost -2", "Refined identity +1"] },
    ],
  },
};

const merchantImprovedProjection = {
  ...merchantAzhvielleProjection,
  merchant: {
    ...merchantAzhvielleProjection.merchant,
    crafting_experience: 20,
    slots: merchantAzhvielleProjection.merchant.slots.map((slot, index) => index === 0
      ? { ...slot, progress: 3, material_quantity: 2 }
      : slot),
    materials: merchantProjection.merchant.materials.map((material, index) => index === 0
      ? { ...material, quantity: 2 }
      : material),
  },
};

const merchantDismantledProjection = {
  ...merchantImprovedProjection,
  merchant: {
    ...merchantImprovedProjection.merchant,
    materials: merchantImprovedProjection.merchant.materials.map((material, index) => index === 1
      ? { ...material, quantity: 1 }
      : material),
    dismantle_items: [{ ...merchantProjection.merchant.dismantle_items[0], quantity: 2 }],
  },
};

const merchantCraftedProjection = {
  ...merchantDismantledProjection,
  merchant: {
    ...merchantDismantledProjection.merchant,
    materials: merchantDismantledProjection.merchant.materials.map((material, index) => index === 0
      ? { ...material, quantity: 1 }
      : material),
    component_recipes: [],
  },
};

const hubCharacterProjection = {
  ...securedHubProjection,
  screen: "character",
  options: [
    { action: "skills", label: "Skills", enabled: true, disabled_reason: null },
    { action: "weapon", label: "Weapon", enabled: true, disabled_reason: null },
    { action: "equipment", label: "Equipment", enabled: true, disabled_reason: null },
    { action: "back", label: "Back", enabled: true, disabled_reason: null },
  ],
  character: {
    display_name: "Ser Branoc, the Unbroken Crest",
    archetype_label: "Brawler",
    stats: [],
    level: 1,
    hp_current: 116,
    hp_maximum: 116,
    mana_current: 46,
    mana_maximum: 46,
    super_current: 0,
    super_maximum: 100,
    exp_current: 0,
    exp_threshold: 100,
    exp_fill_bps: 0,
    targets: [
      { drifter_id: "branoc", display_name: "Ser Branoc", selected: true },
      { drifter_id: "azhvielle", display_name: "Azhvielle", selected: false },
    ],
    selected_target_id: "branoc",
  },
};

const hubCharacterAzhvielleProjection = {
  ...hubCharacterProjection,
  character: {
    ...hubCharacterProjection.character,
    display_name: "Azhvielle",
    archetype_label: "Black Mage",
    targets: hubCharacterProjection.character.targets.map((target) => ({
      ...target,
      selected: target.drifter_id === "azhvielle",
    })),
    selected_target_id: "azhvielle",
  },
};

const weaponProjection = {
  ...hubCharacterProjection,
  screen: "weapon",
  options: [{ action: "back", label: "Back", enabled: true, disabled_reason: null }],
  character: null,
  weapon: {
    name: "Sunder-Spire",
    weapon_type: "Great Flamberge",
    intended_wielder: "Branoc",
    bonuses: [],
    description: "A massive Deep-Iron flamberge.",
    targets: [
      { drifter_id: "branoc", display_name: "Ser Branoc", selected: true },
      { drifter_id: "azhvielle", display_name: "Azhvielle", selected: false },
    ],
    selected_target_id: "branoc",
    components: [
      { slot_id: "blade_guard", label: "Blade / Guard assembly", installed_component_id: "sunder_spire_blade", installed_component_name: "Deep-Iron Blade and Guard" },
      { slot_id: "grip_binding", label: "Grip wrap / binding", installed_component_id: "sunder_spire_grip", installed_component_name: "Bound Grip Wrap" },
      { slot_id: "hilt_handle", label: "Hilt core / handle", installed_component_id: "sunder_spire_hilt", installed_component_name: "Ashwood Hilt Core" },
      { slot_id: "crest_core", label: "Crest / Core", installed_component_id: "sunder_spire_crest", installed_component_name: "Deep-Iron Crest" },
    ],
    physical_identity: null,
    mystical_identity: null,
  },
};

const weaponAzhvielleProjection = {
  ...weaponProjection,
  weapon: {
    ...weaponProjection.weapon,
    name: "Needle of Plain Iron",
    weapon_type: "Ritual Needle",
    intended_wielder: "Azhvielle",
    targets: weaponProjection.weapon.targets.map((target) => ({
      ...target,
      selected: target.drifter_id === "azhvielle",
    })),
    selected_target_id: "azhvielle",
    components: [
      { slot_id: "focus_fittings", label: "Focus head / fittings", installed_component_id: "needle_focus_fitted", installed_component_name: "Obsidian Focus Fittings", installed_effect_summary: ["Scepter Sweep: Power +2, Resource cost -2", "Refined identity +1"] },
      { slot_id: "binding", label: "Binding", installed_component_id: "needle_binding", installed_component_name: "Plain Binding" },
      { slot_id: "haft", label: "Haft", installed_component_id: "needle_haft", installed_component_name: "Ritual Needle Haft" },
      { slot_id: "seal_catalyst", label: "Seal / Catalyst", installed_component_id: "needle_seal", installed_component_name: "Unawakened Seal" },
    ],
  },
};

const floorOneWarningProjection = {
  ...securedHubProjection,
  screen: "floor_one_warning",
  adventure_text: "Death means returning to the Hub. All unsecured XP, gold, and items are lost.",
  options: [
    { action: "set_out", label: "Set Out", enabled: true, disabled_reason: null },
    { action: "back", label: "Back", enabled: true, disabled_reason: null },
  ],
};

const floorOneMainProjection = {
  ...hubProjection,
  screen: "main",
  location_label: "Goblin Patrol",
  adventure_text: "The route continues deeper into Floor 1.",
  contextual_route_option: { action: "enter_encounter", label: "Enter Encounter", enabled: true, disabled_reason: null },
};

const floorOneBattleProjection = {
  ...partyBattleProjection,
  encounter_label: "Floor 1 Goblins",
  enemies: [1, 2, 3, 4].map((number) => ({
    target_id: `floor_one_enemy_${number}`,
    display_label: `Goblin ${number}`,
    hp_current: 60,
    hp_maximum: 60,
    temporary_labels: [],
    defeated: false,
  })),
};

const floorOneRestProjection = {
  ...hubProjection,
  screen: "rest",
  location_label: "Midway Rest",
  adventure_text: "The party reaches the midway Rest.",
  options: [
    { action: "rest", label: "Recover", enabled: true, disabled_reason: null },
    { action: "save", label: "Save", enabled: true, disabled_reason: null },
    { action: "character", label: "Character", enabled: true, disabled_reason: null },
    { action: "items", label: "Items", enabled: true, disabled_reason: null },
    { action: "extract", label: "Extract", enabled: true, disabled_reason: null },
  ],
  contextual_route_option: { action: "skip_rest", label: "Continue Without Rest", enabled: true, disabled_reason: null },
};

const floorOnePreBossRestProjection = {
  ...floorOneRestProjection,
  location_label: "Pre-Boss Rest",
  adventure_text: "The party reaches the Rest before the Goblin Lord.",
};

const floorOneExtractionProjection = {
  ...extractionProjection,
  adventure_text: "The midway extraction secures half of the adjusted rewards and all items.",
  outing_rewards: { experience: 140, gold: 21, items: [] },
};

const floorOneClearedHubProjection = {
  ...securedHubProjection,
  adventure_text: "The Goblin Lord is defeated. Floor 1 is cleared.",
  shared_gold: 115,
};

const floorOneReplayHubProjection = {
  ...floorOneClearedHubProjection,
  adventure_text: "The party extracts safely and returns to the Hub.",
  shared_gold: 136,
};

function requireCondition(condition, message) {
  if (!condition) throw new Error(message);
}

const floorTwoProfileKey =
  "dungeon-drifters.profile.v1.d4d4d4d4-0000-4000-8000-000000000001";
const browserOptions = { headless: true };
if (process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH) {
  browserOptions.executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH;
}
const browser = await chromium.launch(browserOptions);
try {
  const page = await browser.newPage();
  page.setDefaultNavigationTimeout(120000);
  page.on("crash", () => errors.push("browser page crashed"));
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.addInitScript(() => {
    window.__fullscreenRequests = 0;
    window.__fullscreenExits = 0;
    window.__fullscreenElement = null;
    window.__musicPlayRequests = 0;
    window.__musicPlayedBeforeFullscreen = false;
    Object.defineProperty(document, "fullscreenElement", {
      configurable: true,
      get: () => window.__fullscreenElement,
    });
    Object.defineProperty(Element.prototype, "requestFullscreen", {
      configurable: true,
      value: async function () {
        window.__fullscreenRequests += 1;
        window.__fullscreenElement = this;
        document.dispatchEvent(new Event("fullscreenchange"));
      },
    });
    Object.defineProperty(document, "exitFullscreen", {
      configurable: true,
      value: async function () {
        window.__fullscreenExits += 1;
        window.__fullscreenElement = null;
        document.dispatchEvent(new Event("fullscreenchange"));
      },
    });
    Object.defineProperty(HTMLMediaElement.prototype, "play", {
      configurable: true,
      value: function () {
        window.__musicPlayRequests += 1;
        window.__musicPlayedBeforeFullscreen = window.__fullscreenRequests === 0;
        return Promise.resolve();
      },
    });
  });
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("request", (request) => {
    pendingRequests.set(request, request.url());
  });
  page.on("requestfinished", (request) => pendingRequests.delete(request));
  page.on("requestfailed", (request) => {
    pendingRequests.delete(request);
    errors.push(`request failed ${request.url()}: ${request.failure()?.errorText || "unknown"}`);
  });
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });

  await page.route("**/favicon.ico", (route) =>
    route.fulfill({ status: 204, body: "" }),
  );
  // Keep the real combat runtime while making this campaign journey reproducible.
  await page.route("**/python/boot.py", async (route) => {
    const response = await route.fetch();
    const source = await response.text();
    await route.fulfill({
      response,
      body: `${source}\nimport random\nrandom.seed(42)\n`,
    });
  });
  await page.goto(`${baseUrl}/`, { waitUntil: "domcontentloaded" }).catch(async (error) => {
    const navigationState = await page.evaluate(() => ({
      readyState: document.readyState,
      scripts: Array.from(document.scripts, (script) => ({
        source: script.src,
        loaded: script.readyState || "unknown",
      })),
      assets: performance.getEntriesByType("resource")
        .map((entry) => entry.name)
        .filter((name) => /pyodide|dd_runtime|dd_bridge/.test(name)),
    })).catch(() => null);
    throw new Error(`${errors.join("; ") || error.message}; navigation=${JSON.stringify(navigationState)}`);
  });
  await page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  }).catch(async (error) => {
    const startupError = await page.locator("#error-message").innerText().catch(() => "");
    const startupState = await page.evaluate(() => ({
      status: document.querySelector("#start-status")?.textContent?.trim(),
      runtimeLoaded: typeof window.loadPyodide === "function",
      assets: performance.getEntriesByType("resource")
        .map((entry) => entry.name)
        .filter((name) => /pyodide|dd_runtime|dd_bridge|qualification\/python\/boot/.test(name)),
      pendingRequests: Array.from(pendingRequests.values()),
    })).catch(() => null);
    throw new Error(
      startupError || `${errors.join("; ") || error.message}; startup=${JSON.stringify(startupState)}; pending=${JSON.stringify(Array.from(pendingRequests.values()))}`,
    );
  });
  requireCondition(
    await page.locator("#start-screen").isVisible() &&
      await page.locator("#start-logo").evaluate((image) => image.complete && image.naturalWidth > 0) &&
      await page.getByRole("button", { name: "Start" }).isEnabled() &&
      await page.locator("#theme-music").evaluate((audio) => audio.loop && !audio.autoplay && audio.preload === "none") &&
      await page.evaluate(() => window.__musicPlayRequests === 0) &&
      await page.locator("#app").isHidden(),
    "ready browser launch did not show Start without autoplaying the looped theme",
  );
  await captureScreenshot(page, "desktop-start-ready");
  await page.keyboard.press("Shift+Alt+C");
  requireCondition(
    await page.locator("#shortcut-dialog").isHidden(),
    "the picker-only shortcut opened before Start",
  );
  await page.getByRole("button", { name: "Start" }).click();
  await page.locator("#selection-screen").waitFor({ state: "visible" });
  const startTransition = await page.evaluate(() => ({
    startHidden: document.getElementById("start-screen").hidden,
    appVisible: !document.getElementById("app").hidden,
    selectionVisible: !document.getElementById("selection-screen").hidden,
    fullscreenRequests: window.__fullscreenRequests,
    fullscreenActive: Boolean(document.fullscreenElement),
  }));
  requireCondition(
    startTransition.startHidden && startTransition.appVisible && startTransition.selectionVisible &&
      startTransition.fullscreenRequests === 1 && startTransition.fullscreenActive,
    `Start did not request fullscreen and reveal Drifter selection: ${JSON.stringify(startTransition)}`,
  );
  const rosterButtons = page.locator("#drifter-options [data-drifter-id]");
  const rosterLabels = await rosterButtons.allInnerTexts();
  const rosterCards = await rosterButtons.evaluateAll((buttons) => buttons.map((button) => {
    const image = button.querySelector("img");
    const text = Array.from(button.children).map((child) => child.textContent.trim());
    return {
      id: button.dataset.drifterId,
      source: image && image.getAttribute("src"),
      loaded: Boolean(image && image.complete && image.naturalWidth > 0),
      text,
    };
  }));
  requireCondition(
    await rosterButtons.count() === 4 &&
      rosterLabels.some((text) => text.includes("Ser Branoc")) &&
      rosterLabels.some((text) => text.includes("Azhvielle")) &&
      rosterLabels.some((text) => text.includes("Joruun")) &&
      rosterLabels.some((text) => text.includes("Zhaivra")) &&
      rosterCards.every((card) => card.loaded && card.text.length === 4) &&
      rosterCards.map((card) => card.source).join(",") === [
        "assets/drifters/branoc.png",
        "assets/drifters/azhvielle.png",
        "assets/drifters/zhaivra.png",
        "assets/drifters/joruun.png",
      ].join(",") &&
      rosterCards.every((card) => card.text[1].length > 0 && card.text[2].includes("|") && card.text[3].length > 0),
    `Drifter picker did not show loaded sprites with authored text below: ${JSON.stringify(rosterCards)}`,
  );
  await captureScreenshot(page, "desktop-drifter-selection");

  await page.keyboard.press("Shift+Alt+C");
  await page.locator("#shortcut-dialog").waitFor({ state: "visible" });
  await page.locator("#shortcut-code").fill("invalid");
  await page.locator('#shortcut-form button[type="submit"]').click();
  await page.locator("#shortcut-error").waitFor({ state: "visible" });
  requireCondition(
    await page.locator("#shortcut-dialog").isVisible() &&
      (await page.locator("#shortcut-error").innerText()).includes("did not match"),
    "an unrecognized shortcut was not rejected in the picker",
  );
  await page.locator("#shortcut-cancel").click();
  await page.keyboard.press("Shift+Alt+C");
  await page.locator("#shortcut-dialog").waitFor({ state: "visible" });
  await page.locator("#shortcut-code").fill("H01B");
  await page.locator('#shortcut-form button[type="submit"]').click();
  await page.locator("#overworld-screen").waitFor({ state: "visible" });
  requireCondition(
    await page.locator("#location-label").innerText() === "Floor 1 Hub" &&
      (await page.locator("#hub-shared-gold").innerText()).includes("75"),
    "the Hub shortcut did not load its expected Branoc start state",
  );
  await page.keyboard.press("Shift+Alt+C");
  requireCondition(
    await page.locator("#shortcut-dialog").isHidden(),
    "the picker-only shortcut opened during gameplay",
  );
  await restartForNewGame(page);
  await page.keyboard.press("Shift+Alt+C");
  await page.locator("#shortcut-dialog").waitFor({ state: "visible" });
  await page.locator("#shortcut-code").fill("F01BA");
  await page.locator('#shortcut-form button[type="submit"]').click();
  await page.locator("#overworld-screen").waitFor({ state: "visible" });
  requireCondition(
    (await page.locator("#adventure-text").innerText()).includes("Floor 1 is cleared") &&
      (await page.locator("#hub-shared-gold").innerText()).includes("106"),
    "the Floor 1 shortcut did not load its Branoc/Azhvielle clear state",
  );
  await restartForNewGame(page);
  await page.locator('#drifter-options [data-drifter-id="branoc"]').click();
  await page.locator("#overworld-screen").waitFor({ state: "visible" });
  const utilityIcons = await page.locator(".header-actions img").evaluateAll((images) => images.map((image) => {
    const rect = image.getBoundingClientRect();
    return {
      source: image.getAttribute("src"),
      loaded: image.complete && image.naturalWidth > 0,
      width: rect.width,
      height: rect.height,
    };
  }));
  requireCondition(
    utilityIcons.length === 3 &&
      utilityIcons.every((icon) => icon.loaded && icon.width >= 16 && icon.width <= 20 && icon.height >= 16 && icon.height <= 20) &&
      utilityIcons.some((icon) => icon.source === "assets/icons/exit-fullscreen.png") &&
      utilityIcons.some((icon) => icon.source === "assets/icons/music-on.png") &&
      utilityIcons.some((icon) => icon.source === "assets/icons/restart.png"),
    `utility buttons did not show compact rendered icons: ${JSON.stringify(utilityIcons)}`,
  );
  await page.locator("#immersive").click();
  const fullscreenExit = await page.evaluate(() => ({
    requests: window.__fullscreenRequests,
    exits: window.__fullscreenExits,
    active: Boolean(document.fullscreenElement),
    icon: document.querySelector("#immersive img").getAttribute("src"),
  }));
  requireCondition(
    fullscreenExit.requests === 1 && fullscreenExit.exits === 1 && !fullscreenExit.active && fullscreenExit.icon === "assets/icons/fullscreen.png",
    `Fullscreen control did not show its inactive icon after exiting: ${JSON.stringify(fullscreenExit)}`,
  );
  await page.locator("#immersive").click();
  const fullscreenEntry = await page.evaluate(() => ({
    requests: window.__fullscreenRequests,
    exits: window.__fullscreenExits,
    active: Boolean(document.fullscreenElement),
    icon: document.querySelector("#immersive img").getAttribute("src"),
  }));
  requireCondition(
    fullscreenEntry.requests === 2 && fullscreenEntry.exits === 1 && fullscreenEntry.active && fullscreenEntry.icon === "assets/icons/exit-fullscreen.png",
    `Fullscreen control did not show its active icon after re-entering: ${JSON.stringify(fullscreenEntry)}`,
  );
  requireCondition(
    await page.evaluate(() => window.__musicPlayRequests === 1 && window.__musicPlayedBeforeFullscreen && document.getElementById("theme-music").loop),
    "Start did not begin the looping theme before fullscreen exactly once",
  );
  const audioElement = await page.locator("#theme-music").evaluate((audio) => {
    window.__themeMusicElement = audio;
    return true;
  });
  requireCondition(audioElement, "theme audio element was not available after Start");
  await page.locator("#sound-toggle").click();
  requireCondition(
    await page.locator("#theme-music").evaluate((audio) => audio.muted) &&
      await page.locator("#sound-toggle img").getAttribute("src") === "assets/icons/music-off.png",
    "music control did not mute the background theme",
  );
  await page.locator("#sound-toggle").click();
  requireCondition(
    !(await page.locator("#theme-music").evaluate((audio) => audio.muted)) &&
      await page.locator("#sound-toggle img").getAttribute("src") === "assets/icons/music-on.png",
    "music control did not unmute the background theme",
  );
  requireCondition(
    !(await page.locator(".app-header").innerText()).includes("DUNGEON DRIFTERS") &&
      !(await page.locator(".app-header").innerText()).includes("Browser Playtest") &&
      !(await page.locator(".app-header").innerText()).includes("Python runtime ready") &&
      await page.locator("#immersive").isVisible() &&
      await page.locator("#sound-toggle").isVisible() &&
      await page.locator("#restart").isVisible(),
    "header did not retain only browser utility controls",
  );
  requireCondition(
    await page.locator("#overworld-screen").isVisible(),
    "initial Overworld phase is not the active surface",
  );
  requireCondition(
    !(await page.locator("#player-panel").isVisible()) &&
      !(await page.locator("#enemy-panel").isVisible()) &&
      !(await page.locator("#controls-panel").isVisible()),
    "inactive Battle dashboard panels remain visible in the Overworld",
  );
  requireCondition(
    await page.locator("#route-actions button").count() > 0 &&
      await page.locator("#overworld-options button").count() > 0,
    "Overworld did not render its offered contextual and general actions",
  );
  const overworldOrder = await page.evaluate(() => {
    const ids = [
      "location-label",
      "adventure-text",
      "route-actions",
      "overworld-options",
    ];
    const elements = ids.map((id) => document.getElementById(id));
    return elements.every((element, index) =>
      element && (index === elements.length - 1 ||
        Boolean(element.compareDocumentPosition(elements[index + 1]) & Node.DOCUMENT_POSITION_FOLLOWING)),
    );
  });
  requireCondition(overworldOrder, "Overworld information does not follow canonical order");
  const overworldHeaderAlignment = await page.evaluate(() => {
    const actions = document.querySelector(".header-actions").getBoundingClientRect();
    const topLine = document.querySelector("#route-panel .panel-heading").getBoundingClientRect();
    return { actionsRight: actions.right, topLineRight: topLine.right };
  });
  requireCondition(
    Math.abs(overworldHeaderAlignment.actionsRight - overworldHeaderAlignment.topLineRight) <= 1,
    `header utilities do not align with the Overworld top line: ${JSON.stringify(overworldHeaderAlignment)}`,
  );
  await captureScreenshot(page, "desktop-overworld");
  for (const [width, height, screenshotName] of [
    [844, 390, "mobile-overworld-landscape"],
    [667, 375, "mobile-overworld-narrow-landscape"],
  ]) {
    await page.setViewportSize({ width, height });
    await waitForViewportSync(page, width, height);
    const layout = await inspectMobileOverworld(page);
    requireCondition(
      mobileOverworldFits(layout),
      `mobile Overworld should fit without a page or screen scrollbar at ${width}x${height}: ${JSON.stringify(layout)}`,
    );
    await captureScreenshot(page, screenshotName);
  }
  await page.setViewportSize({ width: 1440, height: 900 });
  await waitForViewportSync(page, 1440, 900);

  await page.locator("#overworld-options").getByRole("button", { name: "Character" }).click();
  await page.locator("#character-panel").waitFor({ state: "visible" });
  const characterContext = await page.evaluate(() => ({
    routeVisible: !document.getElementById("route-panel").hidden,
    location: document.getElementById("location-label").textContent,
    adventure: document.getElementById("adventure-text").textContent,
    contextualVisible: !document.getElementById("route-actions").hidden,
    generalVisible: !document.getElementById("overworld-options").hidden,
  }));
  requireCondition(
    await page.locator("#character-panel").isVisible(),
    "Character action did not render the authoritative Character view",
  );
  requireCondition(
    await page.locator("#route-panel").isVisible() &&
      (await page.locator("#location-label").innerText()) === "Goblin Ambush" &&
      (await page.locator("#adventure-text").innerText()).includes("edge of the Goblin horde") &&
      !(await page.locator("#route-actions").isVisible()) &&
      !(await page.locator("#overworld-options").isVisible()),
    `Character view did not retain route context while hiding inactive Overworld controls: ${JSON.stringify(characterContext)}`,
  );
  const characterDetails = await page.evaluate(() => Object.fromEntries(
    ["character-name", "character-archetype", "character-stats", "character-progression"]
      .map((id) => [id, document.getElementById(id).innerText]),
  ));
  requireCondition(
    characterDetails["character-name"] === "Ser Branoc, the Unbroken Crest" &&
      await page.locator("#character-name").evaluate((element) =>
        getComputedStyle(element, "::before").content === '"[ "' &&
        getComputedStyle(element, "::after").content === '" ]"') &&
      characterDetails["character-archetype"] === "Brawler" &&
      characterDetails["character-stats"].includes("Strength") &&
      characterDetails["character-stats"].includes("15") &&
      characterDetails["character-progression"].includes("Level 1") &&
      characterDetails["character-progression"].includes("116/116") &&
      characterDetails["character-progression"].includes("46/46") &&
      characterDetails["character-progression"].includes("0 / 100"),
    `Character view omitted identity, stats, progression, or resource values: ${JSON.stringify(characterDetails)}`,
  );
  const characterOptions = page.locator("#character-options button");
  requireCondition(
    JSON.stringify(await characterOptions.allInnerTexts()) === JSON.stringify(["Skills", "Weapon", "Equipment", "Back"]),
    `Character navigation did not preserve its offered actions and order: ${JSON.stringify(await characterOptions.allInnerTexts())}`,
  );
  const characterGrid = await characterOptions.evaluateAll((buttons) => buttons.map((button) => {
    const rect = button.getBoundingClientRect();
    return { left: rect.left, top: rect.top };
  }));
  requireCondition(
    characterGrid.length === 4 && Math.abs(characterGrid[0].top - characterGrid[1].top) <= 1 &&
      Math.abs(characterGrid[2].top - characterGrid[3].top) <= 1 &&
      characterGrid[2].top > characterGrid[0].top &&
      Math.abs(characterGrid[0].left - characterGrid[2].left) <= 1 &&
      Math.abs(characterGrid[1].left - characterGrid[3].left) <= 1 &&
      characterGrid[0].left < characterGrid[1].left,
    `Character menu did not use the requested two-by-two desktop button layout: ${JSON.stringify(characterGrid)}`,
  );
  await captureScreenshot(page, "desktop-character");

  await page.locator("#character-options").getByRole("button", { name: "Skills" }).click();
  await page.locator("#skills-panel").waitFor({ state: "visible" });
  requireCondition(
    await page.locator("#skills-panel").isVisible() && !(await page.locator("#character-panel").isVisible()),
    "Skills action did not replace Character details with the Skills view",
  );
  requireCondition(
    (await page.locator("#growth-summary").innerText()).includes("Growth Points: 0") &&
      (await page.locator("#growth-message").innerText()).includes("Earn Growth Points by leveling up.") &&
      await page.locator("#skill-stats .skill-stat").count() === 6 &&
      (await page.locator("#skill-attacks").innerText()).includes("Crestgrave Reaping") &&
      (await page.locator("#skill-attacks").innerText()).includes("Third Gate Obsequy"),
    "Skills view omitted authoritative growth state, stat rows, or the attack list",
  );
  const unavailableGrowth = page.locator("#skill-stats button");
  requireCondition(
    await unavailableGrowth.count() === 6 &&
      (await unavailableGrowth.evaluateAll((buttons) => buttons.every((button) => button.disabled))) &&
      (await page.locator("#skill-stats").innerText()).includes("No Growth Points"),
    "Skills view did not preserve disabled stat increases and their authoritative reason",
  );
  requireCondition(
    JSON.stringify(await page.locator("#skills-options button").allInnerTexts()) === JSON.stringify(["Back"]),
    "Skills view exposed controls other than its offered Back action",
  );
  await captureScreenshot(page, "desktop-skills");
  await page.locator("#skills-options").getByRole("button", { name: "Back" }).click();
  await page.locator("#character-panel").waitFor({ state: "visible" });
  requireCondition(await page.locator("#character-panel").isVisible(), "Skills Back did not return to Character");

  await page.locator("#character-options").getByRole("button", { name: "Weapon" }).click();
  await page.locator("#weapon-panel").waitFor({ state: "visible" });
  requireCondition(
    await page.locator("#weapon-panel").isVisible() &&
      (await page.locator("#weapon-panel").innerText()).includes("BONUSES") &&
      (await page.locator("#weapon-panel").innerText()).includes("DESCRIPTION"),
    "Weapon action did not render its authoritative detail view",
  );
  await page.locator("#weapon-options").getByRole("button", { name: "Back" }).click();
  await page.locator("#character-panel").waitFor({ state: "visible" });
  requireCondition(await page.locator("#character-panel").isVisible(), "Weapon Back did not return to Character");

  await page.locator("#character-options").getByRole("button", { name: "Equipment" }).click();
  await page.locator("#equipment-panel").waitFor({ state: "visible" });
  requireCondition(
    await page.locator("#equipment-panel").isVisible() &&
      (await page.locator("#equipment-panel").innerText()).includes("Pendant") &&
      (await page.locator("#equipment-panel").innerText()).includes("Ring") &&
      (await page.locator("#equipment-panel").innerText()).includes("OWNED GEAR") &&
      (await page.locator("#equipment-panel").innerText()).includes("AVAILABLE MODIFIERS") &&
      (await page.locator("#equipment-panel").innerText()).includes("STATIC ACCESSORIES") &&
      (await page.locator("#equipment-panel").innerText()).includes("BENEFITS"),
    "Equipment action did not render its authoritative detail view",
  );
  await page.locator("#equipment-options").getByRole("button", { name: "Back" }).click();
  await page.locator("#character-panel").waitFor({ state: "visible" });
  requireCondition(await page.locator("#character-panel").isVisible(), "Equipment Back did not return to Character");
  await page.locator("#character-options").getByRole("button", { name: "Back" }).click();
  await page.locator("#route-actions").waitFor({ state: "visible" });
  requireCondition(
    await page.locator("#route-actions").isVisible() && await page.locator("#overworld-options").isVisible() &&
      await page.getByRole("button", { name: "Enter Encounter" }).isVisible(),
    "Character Back did not restore the active Overworld actions",
  );

  await page.setViewportSize({ width: 390, height: 844 });
  await waitForViewportSync(page, 390, 844);
  await page.locator("#overworld-options").getByRole("button", { name: "Character" }).click();
  await page.locator("#character-panel").waitFor({ state: "visible" });
  await assertMobileDetailView(page, "character-panel", "character-options", "mobile Character");
  const mobileCharacter = await mobileCharacterLayout(page);
  requireCondition(
    mobileCharacterFits(mobileCharacter),
    `mobile Character should show the full identity, two rows of three stats, compact progression, and XP without clipping: ${JSON.stringify(mobileCharacter)}`,
  );
  await captureScreenshot(page, "mobile-character");
  await page.setViewportSize({ width: 824, height: 384 });
  await waitForViewportSync(page, 824, 384);
  const landscapeCharacter = await mobileCharacterLayout(page);
  requireCondition(
    mobileCharacterFits(landscapeCharacter),
    `landscape mobile Character should use the compact layout at 824x384: ${JSON.stringify(landscapeCharacter)}`,
  );
  await captureScreenshot(page, "landscape-mobile-character");
  await page.setViewportSize({ width: 390, height: 844 });
  await waitForViewportSync(page, 390, 844);

  await page.locator("#character-options").getByRole("button", { name: "Skills" }).click();
  await page.locator("#skills-panel").waitFor({ state: "visible" });
  await assertMobileDetailView(page, "skills-panel", "skills-options", "mobile Skills");
  await captureScreenshot(page, "mobile-skills");
  await page.locator("#skills-options").getByRole("button", { name: "Back" }).click();
  await page.locator("#character-panel").waitFor({ state: "visible" });

  await page.locator("#character-options").getByRole("button", { name: "Weapon" }).click();
  await page.locator("#weapon-panel").waitFor({ state: "visible" });
  await assertMobileDetailView(page, "weapon-panel", "weapon-options", "mobile Weapon");
  await captureScreenshot(page, "mobile-weapon");
  await page.locator("#weapon-options").getByRole("button", { name: "Back" }).click();
  await page.locator("#character-panel").waitFor({ state: "visible" });

  await page.locator("#character-options").getByRole("button", { name: "Equipment" }).click();
  await page.locator("#equipment-panel").waitFor({ state: "visible" });
  await assertMobileDetailView(page, "equipment-panel", "equipment-options", "mobile Equipment");
  await captureScreenshot(page, "mobile-equipment");
  await page.locator("#equipment-options").getByRole("button", { name: "Back" }).click();
  await page.locator("#character-panel").waitFor({ state: "visible" });
  await page.locator("#character-options").getByRole("button", { name: "Back" }).click();
  await page.locator("#route-actions").waitFor({ state: "visible" });
  await page.setViewportSize({ width: 1440, height: 900 });
  await waitForViewportSync(page, 1440, 900);

  await page.getByRole("button", { name: "Enter Encounter" }).click();
  await page.locator("#overworld-screen").waitFor({ state: "hidden" });
  await page.locator("#battle-screen").waitFor({ state: "visible" });
  requireCondition(
    !(await page.locator("#overworld-screen").isVisible()) &&
      await page.locator("#battle-screen").isVisible(),
    "entering an encounter did not replace the Overworld with the Battle surface",
  );

  const battleOrder = await page.evaluate(() => {
    const ids = ["battle-status", "momentum-meter", "battle-matchup", "battle-log", "controls-panel", "super-meter"];
    const elements = ids.map((id) => document.getElementById(id));
    return elements.every((element, index) =>
      element && (index === elements.length - 1 ||
        Boolean(element.compareDocumentPosition(elements[index + 1]) & Node.DOCUMENT_POSITION_FOLLOWING)),
    );
  });
  requireCondition(battleOrder, "Battle information does not follow status, matchup, log, controls, Super order");
  requireCondition(
    await page.locator("#battle-status").isVisible(),
    "Battle status region is not visible",
  );
  const momentumMeter = page.locator("#momentum-meter");
  const momentumTrack = page.locator("#momentum-track");
  const initialMomentumState = await page.evaluate(() => ({
    meterVisible: (() => {
      const meter = document.getElementById("momentum-meter");
      return !meter.hidden && getComputedStyle(meter).display !== "none";
    })(),
    role: document.getElementById("momentum-track").getAttribute("role"),
    minimum: document.getElementById("momentum-track").getAttribute("aria-valuemin"),
    maximum: document.getElementById("momentum-track").getAttribute("aria-valuemax"),
    value: Number(document.getElementById("momentum-track").getAttribute("aria-valuenow")),
    valueText: document.getElementById("momentum-track").getAttribute("aria-valuetext"),
    control: document.getElementById("momentum-control").innerText,
    labels: document.getElementById("momentum-meter").innerText,
  }));
  requireCondition(
    await momentumMeter.isVisible() &&
      await momentumTrack.getAttribute("role") === "meter" &&
      await momentumTrack.getAttribute("aria-valuemin") === "0" &&
      await momentumTrack.getAttribute("aria-valuemax") === "10" &&
      Number.isInteger(initialMomentumState.value) &&
      initialMomentumState.value >= 0 && initialMomentumState.value <= 10 &&
      initialMomentumState.control.startsWith(`Momentum ${initialMomentumState.value}/10 - `) &&
      (await page.locator("#momentum-meter").innerText()).includes("Enemies +5 / +3") &&
      (await page.locator("#momentum-meter").innerText()).includes("Drifters +3 / +5"),
    `the live browser Momentum meter omitted its valid authoritative value or threshold cues: ${JSON.stringify(initialMomentumState)}`,
  );
  await observeMomentum(page);
  requireCondition(
    !(await page.locator("#route-panel").isVisible()),
    "Overworld content remains visible during Battle",
  );
  requireCondition(
    (await page.locator("#player-panel").innerText()).includes("Ser Branoc") &&
      (await page.locator("#enemy-panel").innerText()).includes("Goblin"),
    "Battle status omitted the authoritative player or enemy state",
  );
  requireCondition(
    (await page.locator("#battle-matchup").innerText()).includes("Goblin Ambush") &&
      (await page.locator("#battle-log").innerText()).includes("blocks your path"),
    "Battle matchup or encounter narrative is missing",
  );
  requireCondition(
    (await page.locator("#super-meter").innerText()).includes("0 / 100"),
    "persistent Super resource state is missing",
  );
  requireCondition(
    await page.locator("#actions").isVisible() &&
      !(await page.locator("#moves").isVisible()) &&
      !(await page.locator("#targets").isVisible()) &&
      !(await page.locator("#inventory").isVisible()),
    "Battle Actions displayed controls from inactive interaction phases",
  );
  const actionText = await page.locator("#actions").innerText();
  requireCondition(
    actionText.includes("Unavailable: not implemented"),
    `disabled action did not preserve its authoritative availability reason: ${actionText}`,
  );
  await assertBattleViewport(page, "actions", "desktop Battle Actions");
  const desktopActionHeight = await page.locator("#actions button").first().evaluate((button) => button.getBoundingClientRect().height);
  requireCondition(desktopActionHeight <= 56, `desktop Battle action is too tall for the compact layout: ${desktopActionHeight}px`);
  await captureScreenshot(page, "desktop-battle-actions");

  await page.getByRole("button", { name: "Attack" }).click();
  await page.locator("#moves").waitFor({ state: "visible" });
  requireCondition(
    !(await page.locator("#actions").isVisible()) &&
      await page.locator("#moves").isVisible() &&
      !(await page.locator("#targets").isVisible()) &&
      !(await page.locator("#inventory").isVisible()),
    "Attack did not replace Actions with only the authoritative Move Selection phase",
  );
  const moveText = await page.locator("#moves").innerText();
  requireCondition(
    moveText.includes("Crestgrave Reaping") &&
      moveText.includes("Normal") &&
      moveText.includes("Sunder-Spire tears through the target, cleaving guard and armor.") &&
      moveText.includes("Cinderlung Vesper") &&
      moveText.includes("3 Mana"),
    "Move Selection omitted authoritative names, tags, resource costs, or rules summaries",
  );
  const desktopMoveContext = await page.evaluate(() =>
    getComputedStyle(document.querySelector(".app-header")).display !== "none" &&
      ["battle-status", "battle-matchup", "battle-log"].every((id) =>
        getComputedStyle(document.getElementById(id)).display !== "none"));
  requireCondition(desktopMoveContext, "desktop Move Selection changed the existing Battle layout");
  requireCondition(
    (await page.locator("#moves button").count()) > 0 &&
      (await page.locator("#moves button").filter({ hasText: "Back" }).count()) === 1,
    "Move Selection choices or Back control are missing",
  );
  await assertBattleViewport(page, "moves", "desktop Move Selection");
  await captureScreenshot(page, "desktop-move-selection");

  await page.locator("#moves").getByRole("button", { name: "Back" }).click();
  await page.locator("#actions").waitFor({ state: "visible" });
  requireCondition(
    !(await page.locator("#moves").isVisible()),
    "Back did not return from Move Selection to Actions",
  );

  await page.locator("#actions").getByRole("button", { name: "Attack" }).click();
  await page.locator("#moves").waitFor({ state: "visible" });
  await page.locator("#moves").getByRole("button", { name: /Crestgrave Reaping/ }).click();
  await page.locator("#actions").waitFor({ state: "visible" });
  requireCondition(
    (await page.locator("#battle-log").innerText()).includes("Crestgrave Reaping") &&
      !(await page.locator("#moves").isVisible()),
    "selected semantic move did not return to the authoritative Actions phase and Battle log",
  );

  await page.locator("#actions").getByRole("button", { name: "Items" }).click();
  await page.locator("#inventory").waitFor({ state: "visible" });
  requireCondition(
    !(await page.locator("#actions").isVisible()) &&
      !(await page.locator("#moves").isVisible()) &&
      !(await page.locator("#targets").isVisible()),
    "Battle inventory displayed controls from inactive phases",
  );
  await page.locator("#inventory").getByRole("button", { name: "Back" }).click();
  await page.locator("#actions").waitFor({ state: "visible" });

  requireCondition(
    await page.locator("#battle-screen").isVisible(),
    "semantic input did not return an authoritative Battle phase",
  );

  await restartForNewGame(page);
  requireCondition(
    await page.locator("#overworld-screen").isHidden() && await page.locator("#battle-screen").isHidden() &&
      await page.locator("#drifter-options [data-drifter-id]").count() === 4,
    "Restart did not return to Drifter selection",
  );
  requireCondition(
    await page.evaluate(() => window.__musicPlayRequests === 1 && window.__themeMusicElement === document.getElementById("theme-music")),
    "Restart restarted or replaced the continuously playing theme",
  );
  requireCondition(
    await page.evaluate(() => window.__fullscreenRequests === 2 && window.__fullscreenExits === 1 && Boolean(document.fullscreenElement)),
    "Restart changed an already active fullscreen state",
  );
  await page.locator('#drifter-options [data-drifter-id="azhvielle"]').click();
  await page.locator("#overworld-screen").waitFor({ state: "visible" });
  await page.locator("#overworld-options").getByRole("button", { name: "Character" }).click();
  await page.locator("#character-panel").waitFor({ state: "visible" });
  const switchedName = await page.locator("#character-name").innerText();
  requireCondition(
    switchedName.includes("Azhvielle"),
    `selecting a different Drifter after Restart did not start that character: ${switchedName}`,
  );
  await restartForNewGame(page);
  await page.locator('#drifter-options [data-drifter-id="branoc"]').click();
  await page.locator("#overworld-screen").waitFor({ state: "visible" });
  await page.evaluate(async () => {
    if (document.fullscreenElement) await document.exitFullscreen();
  });
  requireCondition(
    await page.locator("#immersive img").getAttribute("src") === "assets/icons/fullscreen.png",
    "Fullscreen icon did not follow an external fullscreen exit",
  );
  await page.locator("#immersive").click();
  requireCondition(
    await page.evaluate(() => window.__fullscreenRequests === 3 && window.__fullscreenExits === 2 && Boolean(document.fullscreenElement)) &&
      await page.locator("#immersive img").getAttribute("src") === "assets/icons/exit-fullscreen.png",
    "Fullscreen control did not show its active icon after external exit",
  );
  await page.getByRole("button", { name: "Enter Encounter" }).click();
  await page.locator("#actions").waitFor({ state: "visible" });

  const desktopActionSignature = await controlSignature(page);
  await page.setViewportSize({ width: 844, height: 390 });
  await waitForViewportSync(page, 844, 390);
  const landscapeMetrics = await assertBattleViewport(page, "actions", "landscape-phone Battle Actions");
  requireCondition(!landscapeMetrics.orientationGuidanceVisible, "landscape viewport incorrectly shows portrait guidance");
  requireCondition(
    JSON.stringify(await controlSignature(page)) === JSON.stringify(desktopActionSignature),
    "landscape reflow changed offered Battle actions, disabled state, or reasons",
  );
  const actionHeights = await page.locator("#actions button").evaluateAll((buttons) => buttons.map((button) => button.getBoundingClientRect().height));
  requireCondition(actionHeights.every((height) => height >= 44), `landscape Battle action touch targets are too small: ${actionHeights.join(", ")}`);
  await captureScreenshot(page, "landscape-battle-actions");
  console.log("PD|UI3|VIEWPORT|LANDSCAPE_ACTIONS|PASS");

  const landscapeAttack = page.getByRole("button", { name: "Attack" });
  await landscapeAttack.focus();
  await page.keyboard.press("Enter");
  await page.locator("#moves").waitFor({ state: "visible" });
  const landscapeMoveMetrics = await assertBattleViewport(page, "moves", "landscape-phone Move Selection");
  const mobileMovePresentation = await page.evaluate(() => ({
    phase: document.getElementById("battle-screen").dataset.interactionPhase,
    headerHidden: getComputedStyle(document.querySelector(".app-header")).display === "none",
    statusHidden: getComputedStyle(document.getElementById("battle-status")).display === "none",
    matchupHidden: getComputedStyle(document.getElementById("battle-matchup")).display === "none",
    logHidden: getComputedStyle(document.getElementById("battle-log")).display === "none",
    superVisible: getComputedStyle(document.getElementById("super-meter")).display !== "none",
    controlsScrollable: document.getElementById("controls-panel").scrollHeight > document.getElementById("controls-panel").clientHeight + 1,
  }));
  requireCondition(
    mobileMovePresentation.phase === "regular_moves" && mobileMovePresentation.headerHidden &&
      mobileMovePresentation.statusHidden && mobileMovePresentation.matchupHidden &&
      mobileMovePresentation.logHidden && mobileMovePresentation.superVisible &&
      !mobileMovePresentation.controlsScrollable,
    `mobile Move Selection should replace Battle context only on mobile: ${JSON.stringify(mobileMovePresentation)} ${JSON.stringify(landscapeMoveMetrics)}`,
  );
  const moveButtons = page.locator("#moves .move-choice");
  requireCondition(await moveButtons.count() > 1, "mobile Move Selection does not exercise the authored option list");
  const moveHeights = await moveButtons.evaluateAll((buttons) => buttons.map((button) => button.getBoundingClientRect().height));
  requireCondition(moveHeights.every((height) => height >= 44), `landscape Move Selection touch targets are too small: ${moveHeights.join(", ")}`);
  for (let index = 0; index < await moveButtons.count(); index += 1) {
    const moveButton = moveButtons.nth(index);
    await scrollWithinControls(moveButton);
    const detailsFit = await moveButton.evaluate((button) => {
      const panel = document.getElementById("controls-panel").getBoundingClientRect();
      const label = button.querySelector(".choice-label").getBoundingClientRect();
      const summaries = Array.from(button.querySelectorAll(".choice-summary"));
      return label.top >= panel.top - 1 && label.bottom <= panel.bottom + 1 &&
        button.scrollWidth <= button.clientWidth + 1 &&
        summaries.every((summary) => summary.scrollWidth <= summary.clientWidth + 1 && summary.scrollHeight <= summary.clientHeight + 1);
    });
    requireCondition(detailsFit, `mobile move option ${index + 1} or its authored detail is clipped`);
  }
  const mobileBack = page.locator("#moves").getByRole("button", { name: "Back" });
  await scrollWithinControls(mobileBack);
  const backFits = await mobileBack.evaluate((button) => {
    const panel = document.getElementById("controls-panel").getBoundingClientRect();
    const rect = button.getBoundingClientRect();
    return rect.top >= panel.top - 1 && rect.bottom <= panel.bottom + 1 && rect.height >= 44;
  });
  requireCondition(backFits, "mobile Back control is clipped or below touch-target size");
  await page.locator("#controls-panel").evaluate((panel) => { panel.scrollTop = 0; });
  const cleanLandscapeMoveMetrics = await assertBattleViewport(page, "moves", "landscape-phone Move Selection after contained scrolling");
  console.log(`PD|UI3|VIEWPORT_METRICS|LANDSCAPE_MOVES|${JSON.stringify(cleanLandscapeMoveMetrics)}`);
  await captureScreenshot(page, "landscape-move-selection");
  await mobileBack.click();
  await page.locator("#actions").waitFor({ state: "visible" });
  const mobileActionsContextRestored = await page.evaluate(() =>
    getComputedStyle(document.querySelector(".app-header")).display !== "none" &&
      ["battle-status", "battle-matchup", "battle-log"].every((id) =>
        getComputedStyle(document.getElementById(id)).display !== "none"));
  requireCondition(mobileActionsContextRestored, "Back did not restore the normal mobile Battle view");
  await page.getByRole("button", { name: "Attack" }).click();
  await page.locator("#moves").waitFor({ state: "visible" });
  await page.locator("#moves").getByRole("button", { name: /Crestgrave Reaping/ }).click();
  await page.locator("#actions").waitFor({ state: "visible" });
  requireCondition(
    await page.evaluate(() => document.getElementById("battle-screen").dataset.interactionPhase === "actions") &&
      await page.locator("#battle-log").isVisible(),
    "mobile move resolution did not return to Battle Actions",
  );
  const resolvedActionSignature = await controlSignature(page);
  console.log("PD|UI3|VIEWPORT|LANDSCAPE_MOVES|PASS");

  await page.setViewportSize({ width: 390, height: 844 });
  await waitForViewportSync(page, 390, 844);
  await page.waitForFunction(() => window.matchMedia("(orientation: portrait)").matches && !document.getElementById("orientation-guidance").hidden);
  const portraitMetrics = await assertBattleViewport(page, "actions", "portrait Battle Actions");
  requireCondition(portraitMetrics.orientationGuidanceVisible, "portrait guidance is not visible");
  const portraitAttackBox = await page.getByRole("button", { name: "Attack" }).boundingBox();
  requireCondition(
    portraitAttackBox && portraitAttackBox.y >= 0 && portraitAttackBox.y + portraitAttackBox.height <= 844,
    "portrait guidance or layout hides the offered Attack input",
  );
  requireCondition(
    JSON.stringify(await controlSignature(page)) === JSON.stringify(resolvedActionSignature),
    `portrait reflow changed offered Battle actions, disabled state, or reasons: ${JSON.stringify(resolvedActionSignature)} -> ${JSON.stringify(await controlSignature(page))}`,
  );
  await page.getByRole("button", { name: "Attack" }).click();
  await page.locator("#moves").waitFor({ state: "visible" });
  await assertBattleViewport(page, "moves", "portrait Move Selection");
  const portraitBack = page.locator("#moves").getByRole("button", { name: "Back" });
  await portraitBack.scrollIntoViewIfNeeded();
  await portraitBack.click();
  await page.locator("#actions").waitFor({ state: "visible" });
  console.log("PD|UI3|VIEWPORT|PORTRAIT_GUIDANCE|PASS");

  const targetPage = await browser.newPage();
  await targetPage.setViewportSize({ width: 844, height: 390 });
  targetPage.on("pageerror", (error) => errors.push(error.message));
  await targetPage.route("**/pyodide.js", (route) =>
    route.fulfill({ status: 200, contentType: "application/javascript", body: "" }),
  );
  await targetPage.addInitScript((views) => {
    window.__fixtureCommands = [];
    window.__fixtureGlobals = {};
    window.__fixtureTransitionComplete = false;
    window.__fixtureHubMode = false;
    window.__fixtureDefeatMode = false;
    window.__fixtureAwaitingReselect = false;
    window.__fixtureHubPhase = "hub";
    window.__fixtureFloorOneRun = 0;
    window.__fixtureFloorOneBattle = 0;
    window.__fixtureStartCalls = [];
    window.__fullscreenRequests = 0;
    window.__musicPlayRequests = 0;
    window.__musicPlayedBeforeFullscreen = false;
    Object.defineProperty(Element.prototype, "requestFullscreen", {
      configurable: true,
      value: async function () { window.__fullscreenRequests += 1; },
    });
    Object.defineProperty(HTMLMediaElement.prototype, "play", {
      configurable: true,
      value: function () {
        window.__musicPlayRequests += 1;
        window.__musicPlayedBeforeFullscreen = window.__fullscreenRequests === 0;
        return Promise.resolve();
      },
    });
    window.__resolvePyodide = null;
    window.loadPyodide = () => new Promise((resolve) => {
      window.__resolvePyodide = () => resolve({
        FS: { writeFile() {} },
        globals: { set(key, value) { window.__fixtureGlobals[key] = value; } },
        runPython() {},
        async runPythonAsync(source) {
          if (source === "boot()") return JSON.stringify([
            { drifter_id: "branoc", choice: "1", short_name: "Ser Branoc", archetype_name: "Brawler", combat_role: "Heavy Vanguard", selection_summary: "durable, relentless, slow", sprite_url: "assets/drifters/branoc.png" },
            { drifter_id: "azhvielle", choice: "2", short_name: "Azhvielle", archetype_name: "Black Mage", combat_role: "Elemental Controller", selection_summary: "versatile, dangerous, unpredictable", sprite_url: "assets/drifters/azhvielle.png" },
            { drifter_id: "zhaivra", choice: "3", short_name: "Zhaivra Kelyth", archetype_name: "Rogue Archer", combat_role: "Alchemical Marksman", selection_summary: "precise, prepared, resource-limited", sprite_url: "assets/drifters/zhaivra.png" },
            { drifter_id: "joruun", choice: "4", short_name: "Joruun Veyr", archetype_name: "Monk", combat_role: "Elemental Skirmisher", selection_summary: "mobile, adaptable, physically costly", sprite_url: "assets/drifters/joruun.png" },
          ]);
          if (source === "startup_status_json()") return JSON.stringify({ status: "missing" });
          if (source === "request_new_game_json()") return JSON.stringify({ status: "selection" });
          if (source === "confirm_new_game_json(_confirmed_new_game_json)") return JSON.stringify({ status: "selection" });
          if (source === "start_game_json(_selected_drifter_id)") {
            window.__fixtureSelectedDrifter = window.__fixtureGlobals._selected_drifter_id;
            window.__fixtureStartCalls.push(window.__fixtureSelectedDrifter);
            if (window.__fixtureAwaitingReselect) {
              window.__fixtureDefeatMode = false;
              window.__fixtureAwaitingReselect = false;
              window.__fixtureHubMode = false;
              return JSON.stringify(views.overworld);
            }
            const targetView = window.__fixtureStartCalls.length === 1
              ? views.neutralTargets
              : views.targets;
            return JSON.stringify(window.__fixtureHubMode ? views.hub : targetView);
          }
          if (source === "current_view_json()") {
            if (window.__fixtureHubMode) return JSON.stringify(views[window.__fixtureHubPhase]);
            return JSON.stringify(window.__fixtureTransitionComplete ? views.overworld : views.targets);
          }
          if (source === "restart_game_json()") return JSON.stringify(views.targets);
          if (source === "submit_json(_browser_command_json)") {
            const command = JSON.parse(window.__fixtureGlobals._browser_command_json);
            window.__fixtureCommands.push(command);
            if (window.__fixtureHubMode) {
              if (["securedHub", "floorOneClearedHub"].includes(window.__fixtureHubPhase) && command.action === "region_portal") {
                window.__fixtureRegionPortalReturnPhase = window.__fixtureHubPhase;
                window.__fixtureHubPhase = "regionPortal";
                return JSON.stringify(views.regionPortal);
              }
              if (window.__fixtureHubPhase === "regionPortal" && command.kind === "region" && command.region_id === "region_1") {
                window.__fixtureHubPhase = "regionDestinations";
                return JSON.stringify(
                  window.__fixtureRegionPortalReturnPhase === "floorOneClearedHub"
                    ? views.regionDestinationsCleared
                    : views.regionDestinations,
                );
              }
              if (window.__fixtureHubPhase === "regionDestinations" && command.kind === "destination" && command.destination_id === "floor_one" && window.__fixtureRegionPortalReturnPhase === "securedHub") {
                window.__fixtureHubPhase = "floorOneWarning";
                return JSON.stringify(views.floorOneWarning);
              }
              if (window.__fixtureHubPhase === "regionDestinations" && command.action === "back") {
                window.__fixtureHubPhase = "regionPortal";
                return JSON.stringify(views.regionPortal);
              }
              if (window.__fixtureHubPhase === "regionPortal" && command.action === "back") {
                window.__fixtureHubPhase = window.__fixtureRegionPortalReturnPhase;
                return JSON.stringify(views[window.__fixtureHubPhase]);
              }
              if (window.__fixtureHubPhase === "securedHub" && command.action === "items") {
                window.__fixtureHubPhase = "items";
                return JSON.stringify(views.items);
              }
              if (window.__fixtureHubPhase === "items" && command.kind === "overworld_item") {
                return JSON.stringify(views.itemsSelected);
              }
              if (window.__fixtureHubPhase === "items" && command.action === "inspect") {
                window.__fixtureHubPhase = "itemInspection";
                return JSON.stringify(views.itemInspection);
              }
              if (window.__fixtureHubPhase === "itemInspection" && command.action === "back") {
                window.__fixtureHubPhase = "items";
                return JSON.stringify(views.itemsSelected);
              }
              if (window.__fixtureHubPhase === "items" && command.action === "back") {
                window.__fixtureHubPhase = "securedHub";
                return JSON.stringify(views.securedHub);
              }
              if (window.__fixtureHubPhase === "securedHub" && command.action === "vendors") {
                window.__fixtureHubPhase = "vendors";
                return JSON.stringify(views.vendors);
              }
              if (window.__fixtureHubPhase === "vendors" && command.action === "blacksmith") {
                window.__fixtureHubPhase = "blacksmith";
                return JSON.stringify(views.merchant);
              }
              if (window.__fixtureHubPhase === "blacksmith" && command.kind === "merchant_target" && command.drifter_id === "azhvielle") {
                return JSON.stringify(views.merchantAzhvielle);
              }
              if (window.__fixtureHubPhase === "blacksmith" && command.kind === "merchant_improve") {
                return JSON.stringify(views.merchantImproved);
              }
              if (window.__fixtureHubPhase === "blacksmith" && command.kind === "merchant_dismantle") {
                return JSON.stringify(views.merchantDismantled);
              }
              if (window.__fixtureHubPhase === "blacksmith" && command.kind === "merchant_craft_component") {
                return JSON.stringify(views.merchantCrafted);
              }
              if (window.__fixtureHubPhase === "blacksmith" && command.action === "back") {
                window.__fixtureHubPhase = "vendors";
                return JSON.stringify(views.vendors);
              }
              if (window.__fixtureHubPhase === "vendors" && command.action === "back") {
                window.__fixtureHubPhase = "securedHub";
                return JSON.stringify(views.securedHub);
              }
              if (window.__fixtureHubPhase === "securedHub" && command.action === "character") {
                window.__fixtureHubPhase = "character";
                return JSON.stringify(views.hubCharacter);
              }
              if (window.__fixtureHubPhase === "character" && command.kind === "character_target" && command.drifter_id === "azhvielle") {
                window.__fixtureHubPhase = "characterAzhvielle";
                return JSON.stringify(views.hubCharacterAzhvielle);
              }
              if (window.__fixtureHubPhase === "characterAzhvielle" && command.kind === "character_target" && command.drifter_id === "branoc") {
                window.__fixtureHubPhase = "character";
                return JSON.stringify(views.hubCharacter);
              }
              if (window.__fixtureHubPhase === "character" && command.action === "weapon") {
                window.__fixtureHubPhase = "weapon";
                return JSON.stringify(views.weapon);
              }
              if (window.__fixtureHubPhase === "characterAzhvielle" && command.action === "weapon") {
                window.__fixtureHubPhase = "weapon";
                return JSON.stringify(views.weaponAzhvielle);
              }
              if (window.__fixtureHubPhase === "weapon" && command.kind === "weapon_target" && command.drifter_id === "azhvielle") {
                return JSON.stringify(views.weaponAzhvielle);
              }
              if (window.__fixtureHubPhase === "weapon" && command.action === "back") {
                window.__fixtureHubPhase = "character";
                return JSON.stringify(views.hubCharacter);
              }
              if (window.__fixtureHubPhase === "character" && command.action === "back") {
                window.__fixtureHubPhase = "securedHub";
                return JSON.stringify(views.securedHub);
              }
              if (["securedHub", "floorOneClearedHub"].includes(window.__fixtureHubPhase) && command.action === "start_floor_one") {
                window.__fixtureHubPhase = "floorOneWarning";
                return JSON.stringify(views.floorOneWarning);
              }
              if (window.__fixtureHubPhase === "floorOneWarning" && command.action === "set_out") {
                window.__fixtureFloorOneRun += 1;
                window.__fixtureFloorOneBattle = 1;
                window.__fixtureHubPhase = "floorOneBattle";
                return JSON.stringify(views.floorOneBattle);
              }
              if (window.__fixtureHubPhase === "floorOneBattle" && command.intent === "defend") {
                if (window.__fixtureFloorOneBattle === 10) {
                  window.__fixtureHubPhase = "floorOneClearedHub";
                } else if (window.__fixtureFloorOneBattle === 5) {
                  window.__fixtureHubPhase = "floorOneMidwayRest";
                } else if (window.__fixtureFloorOneBattle === 9) {
                  window.__fixtureHubPhase = "floorOnePreBossRest";
                } else {
                  window.__fixtureHubPhase = "floorOneMain";
                }
                return JSON.stringify(views.complete);
              }
              if (window.__fixtureHubPhase === "floorOneMain" && command.action === "enter_encounter") {
                window.__fixtureFloorOneBattle += 1;
                window.__fixtureHubPhase = "floorOneBattle";
                return JSON.stringify(views.floorOneBattle);
              }
              if (window.__fixtureHubPhase === "floorOneMidwayRest" && command.action === "rest") {
                return JSON.stringify(views.floorOneMidwayRest);
              }
              if (window.__fixtureHubPhase === "floorOneMidwayRest" && command.action === "skip_rest") {
                window.__fixtureHubPhase = "floorOneMain";
                return JSON.stringify(views.floorOneMain);
              }
              if (window.__fixtureHubPhase === "floorOneMidwayRest" && command.action === "extract") {
                window.__fixtureHubPhase = "floorOneExtraction";
                return JSON.stringify(views.floorOneExtraction);
              }
              if (window.__fixtureHubPhase === "floorOnePreBossRest" && command.action === "skip_rest") {
                window.__fixtureHubPhase = "floorOneMain";
                return JSON.stringify(views.floorOneMain);
              }
              if (window.__fixtureHubPhase === "floorOneExtraction" && command.action === "return_to_hub") {
                window.__fixtureHubPhase = "floorOneReplayHub";
                return JSON.stringify(views.floorOneReplayHub);
              }
              if (window.__fixtureHubPhase === "hub" && command.action === "recruit_companion") {
                window.__fixtureHubPhase = "companion";
                return JSON.stringify(views.companion);
              }
              if (window.__fixtureHubPhase === "companion" && command.drifter_id === "azhvielle" && command.event_id === "floor_one_d2_recruitment") {
                window.__fixtureHubPhase = "partyReady";
                return JSON.stringify(views.partyReady);
              }
              if (window.__fixtureHubPhase === "partyReady" && command.action === "ready") {
                window.__fixtureHubPhase = "battle";
                return JSON.stringify(views.partyBattle);
              }
              if (window.__fixtureHubPhase === "battle" && command.intent === "defend") {
                if (window.__fixtureDefeatMode) {
                  window.__fixtureAwaitingReselect = true;
                  return JSON.stringify("select_drifter");
                }
                window.__fixtureHubPhase = "extraction";
                return JSON.stringify(views.complete);
              }
              if (window.__fixtureHubPhase === "extraction" && command.action === "return_to_hub") {
                window.__fixtureHubPhase = "securedHub";
                return JSON.stringify(views.securedHub);
              }
              if (window.__fixtureHubPhase === "securedHub" && command.action === "select_party") {
                window.__fixtureHubPhase = "partySelection";
                return JSON.stringify(views.partySelection);
              }
              if (window.__fixtureHubPhase === "partySelection" && command.kind === "active_pair" &&
                  JSON.stringify(command.drifter_ids) === JSON.stringify(["joruun", "azhvielle"])) {
                window.__fixtureHubPhase = "securedHub";
                return JSON.stringify(views.partyChosen);
              }
              throw new Error(`unexpected hub fixture command at ${window.__fixtureHubPhase}`);
            }
            window.__fixtureTransitionComplete = true;
            return JSON.stringify(views.complete);
          }
          return "null";
        },
      });
    });
  }, {
    targets: targetProjection,
    neutralTargets: neutralTargetProjection,
    complete: completeProjection,
    overworld: resultOverworldProjection,
    hub: hubProjection,
    companion: companionProjection,
    partyReady: partyReadyProjection,
    partyBattle: partyBattleProjection,
    extraction: extractionProjection,
    securedHub: securedHubProjection,
    regionPortal: regionPortalProjection,
    regionDestinations: regionDestinationsProjection,
    regionDestinationsCleared: regionDestinationsClearedProjection,
    vendors: vendorsProjection,
    partySelection: partySelectionProjection,
    partyChosen: partyChosenProjection,
    items: itemsProjection,
    itemsSelected: itemsSelectedProjection,
    itemInspection: itemInspectionProjection,
    merchant: merchantProjection,
    merchantAzhvielle: merchantAzhvielleProjection,
    merchantImproved: merchantImprovedProjection,
    merchantDismantled: merchantDismantledProjection,
    merchantCrafted: merchantCraftedProjection,
    hubCharacter: hubCharacterProjection,
    hubCharacterAzhvielle: hubCharacterAzhvielleProjection,
    weapon: weaponProjection,
    weaponAzhvielle: weaponAzhvielleProjection,
    floorOneWarning: floorOneWarningProjection,
    floorOneMain: floorOneMainProjection,
    floorOneBattle: floorOneBattleProjection,
    floorOneMidwayRest: floorOneRestProjection,
    floorOnePreBossRest: floorOnePreBossRestProjection,
    floorOneExtraction: floorOneExtractionProjection,
    floorOneClearedHub: floorOneClearedHubProjection,
    floorOneReplayHub: floorOneReplayHubProjection,
  });
  await targetPage.goto(`${baseUrl}/`, { waitUntil: "domcontentloaded" });
  await targetPage.waitForFunction(() => typeof window.__resolvePyodide === "function");
  requireCondition(
    await targetPage.locator("#start-screen").isVisible() &&
      await targetPage.locator("#start-logo").evaluate((image) => image.complete && image.naturalWidth > 0) &&
      await targetPage.getByRole("button", { name: "Loading..." }).isDisabled() &&
      await targetPage.evaluate(() => window.__musicPlayRequests === 0) &&
      await targetPage.locator("#app").isHidden(),
    "loading browser launch did not keep Start disabled without starting theme music",
  );
  await captureScreenshot(targetPage, "mobile-start-screen");
  await targetPage.evaluate(() => window.__resolvePyodide());
  await targetPage.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, { timeout: 30000 });
  requireCondition(
    await targetPage.getByRole("button", { name: "Start" }).isEnabled() &&
      await targetPage.locator("#app").isHidden(),
    "runtime-ready splash did not enable Start while keeping gameplay hidden",
  );
  await captureScreenshot(targetPage, "mobile-start-ready");
  await targetPage.getByRole("button", { name: "Start" }).click();
  await targetPage.locator("#selection-screen").waitFor({ state: "visible" });
  await targetPage.waitForFunction(
    () => [...document.querySelectorAll("#drifter-options img")].length === 4 &&
      [...document.querySelectorAll("#drifter-options img")].every(
        (image) => image.complete && image.naturalWidth > 0,
      ),
    null,
    { timeout: 30000 },
  );
  const mobileRosterCards = await targetPage.locator("#drifter-options [data-drifter-id]").evaluateAll((buttons) => buttons.map((button) => {
    const image = button.querySelector("img");
    return {
      source: image && image.getAttribute("src"),
      loaded: Boolean(image && image.complete && image.naturalWidth > 0),
      width: button.getBoundingClientRect().width,
      role: button.querySelector(".drifter-option-role")?.textContent.trim(),
      summary: button.querySelector(".drifter-option-summary")?.textContent.trim(),
    };
  }));
  requireCondition(
    mobileRosterCards.length === 4 && mobileRosterCards.every((card) =>
      card.loaded && card.width > 0 && card.role.includes("|") && card.summary.length > 0),
    `mobile Start did not show four sprite choices with text beneath: ${JSON.stringify(mobileRosterCards)}`,
  );
  requireCondition(
    mobileSelectionFits(await inspectMobileSelection(targetPage)),
    `mobile Drifter selection should show four complete cards in one non-scrolling row: ${JSON.stringify(await inspectMobileSelection(targetPage))}`,
  );
  await captureScreenshot(targetPage, "mobile-drifter-selection");
  await targetPage.setViewportSize({ width: 667, height: 375 });
  await waitForViewportSync(targetPage, 667, 375);
  const narrowMobileSelection = await inspectMobileSelection(targetPage);
  requireCondition(
    mobileSelectionFits(narrowMobileSelection),
    `narrow mobile Drifter selection should show four complete cards without scrolling: ${JSON.stringify(narrowMobileSelection)}`,
  );
  await captureScreenshot(targetPage, "mobile-drifter-selection-narrow-landscape");
  await targetPage.setViewportSize({ width: 844, height: 390 });
  await waitForViewportSync(targetPage, 844, 390);
  await targetPage.locator('#drifter-options [data-drifter-id="branoc"]').click();
  await targetPage.locator("#targets").waitFor({ state: "visible" });
  await assertMomentumNeutral(targetPage, "deterministic neutral projection");
  requireCondition(
    await targetPage.evaluate(() => window.__fullscreenRequests === 1),
    "mobile Start did not request fullscreen from its user gesture",
  );
  requireCondition(
    await targetPage.evaluate(() => window.__musicPlayRequests === 1 && window.__musicPlayedBeforeFullscreen),
    "mobile Start did not start theme music before fullscreen from its user gesture",
  );
  await targetPage.setViewportSize({ width: 1440, height: 900 });
  await waitForViewportSync(targetPage, 1440, 900);
  await restartForNewGame(targetPage);
  await targetPage.locator('#drifter-options [data-drifter-id="branoc"]').click();
  await targetPage.locator("#targets").waitFor({ state: "visible" });
  const projectedMomentum = await targetPage.evaluate(() => ({
    value: document.getElementById("momentum-track").getAttribute("aria-valuenow"),
    valueText: document.getElementById("momentum-track").getAttribute("aria-valuetext"),
    label: document.getElementById("momentum-control").innerText,
    bonuses: document.getElementById("momentum-bonuses").innerText,
  }));
  requireCondition(
    projectedMomentum.value === "2" &&
      projectedMomentum.label === "Momentum 2/10 - Enemies +3" &&
      projectedMomentum.bonuses === "Critical chance +6 percentage points; Outgoing damage +5%; Incoming mitigation +5%" &&
      projectedMomentum.valueText === "Enemies +3. Critical chance +6 percentage points; Outgoing damage +5%; Incoming mitigation +5%",
    `browser did not faithfully render the Python-projected +3 Momentum bonuses: ${JSON.stringify(projectedMomentum)}`,
  );
  console.log("M7_BROWSER|MOMENTUM_PROJECTION|PASS");
  requireCondition(
    await targetPage.evaluate(() => window.__fixtureSelectedDrifter === "branoc"),
    "Drifter selection did not pass its authored ID to the Python bridge",
  );
  await targetPage.setViewportSize({ width: 1440, height: 900 });
  await waitForViewportSync(targetPage, 1440, 900);
  requireCondition(
    await targetPage.locator("#targets").isVisible() &&
      !(await targetPage.locator("#actions").isVisible()) &&
      !(await targetPage.locator("#moves").isVisible()),
    "Target Selection did not replace inactive Battle phases",
  );
  const targetButtons = targetPage.locator("#targets .target-choice");
  requireCondition(await targetButtons.count() === 2, "multi-enemy Target Selection omitted an authoritative target");
  const firstTargetText = await targetButtons.nth(0).innerText();
  const secondTarget = targetButtons.nth(1);
  const secondTargetText = await secondTarget.innerText();
  requireCondition(
    firstTargetText.includes("Goblin 1") &&
      firstTargetText.includes("HP 60/60") &&
      firstTargetText.includes("Crestgrave Reaping") &&
      firstTargetText.includes("Sunder-Spire tears through the target, cleaving guard and armor.") &&
      secondTargetText.includes("Goblin 2") &&
      secondTargetText.includes("HP 43/60") &&
      secondTargetText.includes("Guarding") &&
      secondTargetText.includes("Unavailable: target unavailable") &&
      await secondTarget.isDisabled(),
    "Target Selection omitted authoritative labels, HP/state, preview, or availability",
  );
  await captureScreenshot(targetPage, "desktop-target-selection");
  await targetPage.setViewportSize({ width: 844, height: 390 });
  await waitForViewportSync(targetPage, 844, 390);
  const mobileTargetPresentation = await targetPage.evaluate(() => ({
    phase: document.getElementById("battle-screen").dataset.interactionPhase,
    headerHidden: getComputedStyle(document.querySelector(".app-header")).display === "none",
    statusHidden: getComputedStyle(document.getElementById("battle-status")).display === "none",
    logHidden: getComputedStyle(document.getElementById("battle-log")).display === "none",
    targetsVisible: getComputedStyle(document.getElementById("targets")).display !== "none",
  }));
  requireCondition(
    mobileTargetPresentation.phase === "targets" && mobileTargetPresentation.headerHidden &&
      mobileTargetPresentation.statusHidden && mobileTargetPresentation.logHidden &&
      mobileTargetPresentation.targetsVisible,
    `mobile Target Selection did not use the focused submenu: ${JSON.stringify(mobileTargetPresentation)}`,
  );
  await targetButtons.nth(0).click();
  await targetPage.locator("#overworld-screen").waitFor({ state: "visible" });
  const submittedTarget = await targetPage.evaluate(() => window.__fixtureCommands.at(-1));
  requireCondition(
    submittedTarget.kind === "target" && submittedTarget.target_id === "enemy_1",
    "target selection did not submit the authoritative target_id",
  );
  requireCondition(
    (await targetPage.locator("#adventure-text").innerText()).includes("Rewards: 40 EXP and 3 gold") &&
      await targetPage.getByRole("button", { name: "Enter Encounter" }).isVisible() &&
      !(await targetPage.locator("#battle-screen").isVisible()),
    "completed Battle did not return to the authoritative Overworld result projection",
  );

  await targetPage.evaluate(() => {
    window.__fixtureHubMode = true;
    window.__fixtureHubPhase = "hub";
    window.__fixtureCommands = [];
  });
  await restartForNewGame(targetPage);
  await targetPage.locator('#drifter-options [data-drifter-id="branoc"]').click();
  await targetPage.locator("#overworld-screen").waitFor({ state: "visible" });
  requireCondition(
    (await targetPage.locator("#location-label").innerText()) === "Floor 1 Hub" &&
      (await targetPage.locator("#hub-shared-gold").innerText()) === "Shared gold: 75" &&
      await targetPage.getByRole("button", { name: "Recruit Companion" }).isVisible(),
    "Hub projection omitted the shared balance or authoritative recruitment action",
  );
  await captureScreenshot(targetPage, "desktop-floor-one-hub");
  await clickVisibleOption(targetPage, "#overworld-options", "Recruit Companion");
  await targetPage.waitForFunction(() => document.getElementById("screen-badge").textContent.trim() === "RECRUITMENT");
  requireCondition(
    await targetPage.locator("#companion-choices button:enabled").count() === 3 &&
      (await targetPage.locator("#companion-funds").innerText()).includes("Shared gold: 75") &&
      (await targetPage.locator("#companion-funds").innerText()).includes("Recruitment cost: 65"),
    "companion projection omitted the three candidates or authoritative price/balance",
  );
  await clickVisibleOption(targetPage, "#companion-choices", "Azhvielle");
  await targetPage.waitForFunction(() => document.getElementById("screen-badge").textContent.trim() === "PARTY READY");
  requireCondition(
    (await targetPage.locator("#hub-shared-gold").innerText()) === "Shared gold: 10" &&
      await targetPage.getByRole("button", { name: "Ready / Set Out" }).isVisible(),
    "Party Ready projection omitted the post-recruitment balance or explicit action",
  );
  await clickVisibleOption(targetPage, "#overworld-options", "Ready / Set Out");
  await targetPage.locator("#party-panel").waitFor({ state: "visible" });
  requireCondition(
    await targetPage.locator("#party-members .party-member").count() === 2 &&
      (await targetPage.locator("#party-members").innerText()).includes("Ser Branoc") &&
      (await targetPage.locator("#party-members").innerText()).includes("Azhvielle") &&
      await targetPage.locator("#enemy-panel .enemy").count() === 3,
    "party Battle projection omitted a Drifter or one of the three Goblins",
  );
  await captureScreenshot(targetPage, "desktop-hub-party-battle");
  await clickVisibleOption(targetPage, "#actions", "Defend");
  await targetPage.locator("#extraction-rewards").waitFor({ state: "visible" });
  requireCondition(
    (await targetPage.locator("#extraction-rewards").innerText()).includes("120 EXP | 9 gold") &&
      (await targetPage.locator("#extraction-rewards").innerText()).includes("3 x Goblin Scrap") &&
      await targetPage.getByRole("button", { name: "Return to Hub" }).isVisible(),
    "Extraction projection omitted pending tutorial totals, item rewards, or its explicit return action",
  );
  await captureScreenshot(targetPage, "desktop-hub-extraction");
  await clickVisibleOption(targetPage, "#overworld-options", "Return to Hub");
  requireCondition(
    (await targetPage.locator("#hub-shared-gold").innerText()) === "Shared gold: 19" &&
      await targetPage.locator("#overworld-options button").count() === 9 &&
      !(await targetPage.getByRole("button", { name: "Recruit Companion" }).count()) &&
      !(await targetPage.getByRole("button", { name: "Ready / Set Out" }).count()),
    "returned Hub did not show secured currency or offer Floor 1",
  );
  await clickVisibleOption(targetPage, "#overworld-options", "Choose Party");
  await targetPage.waitForFunction(() => document.getElementById("screen-badge").textContent.trim() === "PARTY SELECTION");
  requireCondition(
    await targetPage.locator("#party-pair-choices button").count() === 6 &&
      await targetPage.locator("#party-pair-choices").innerText().then((text) => text.includes("Joruun Veyr + Azhvielle")),
    "party selection did not render all ordered Drifter pairs",
  );
  await clickVisibleOption(targetPage, "#party-pair-choices", "Joruun Veyr + Azhvielle");
  await targetPage.waitForFunction(() => document.getElementById("screen-badge").textContent.trim() === "HUB");
  const hubCommands = await targetPage.evaluate(() => window.__fixtureCommands);
  requireCondition(
    JSON.stringify(hubCommands) === JSON.stringify([
      { kind: "overworld_action", action: "recruit_companion" },
      { kind: "companion", drifter_id: "azhvielle", event_id: "floor_one_d2_recruitment" },
      { kind: "overworld_action", action: "ready" },
      { kind: "action", intent: "defend" },
      { kind: "overworld_action", action: "return_to_hub" },
      { kind: "overworld_action", action: "select_party" },
      { kind: "active_pair", drifter_ids: ["joruun", "azhvielle"] },
    ]),
    `Hub flow did not submit existing semantic commands: ${JSON.stringify(hubCommands)}`,
  );
  console.log("PYD7|BROWSER|HUB_OUTING|PASS");

  await clickVisibleOption(targetPage, "#overworld-options", "Vendors");
  await targetPage.locator("#vendors-panel").waitFor({ state: "visible" }).catch(async (error) => {
    const state = await targetPage.evaluate(() => ({
      phase: window.__fixtureHubPhase,
      lastCommand: window.__fixtureCommands.at(-1),
      badge: document.getElementById("screen-badge")?.textContent?.trim(),
      vendorsPanelHidden: document.getElementById("vendors-panel")?.hidden,
      error: document.getElementById("error-message")?.textContent?.trim(),
    }));
    throw new Error(`${error.message}; vendor navigation state=${JSON.stringify(state)}`);
  });
  requireCondition(
    await targetPage.locator("#vendors-options button").allInnerTexts().then((labels) =>
      ["Merchant", "Blacksmith", "Enchanter", "Alchemist"].every((label) => labels.includes(label))),
    "vendor directory omitted one or more specialist destinations",
  );
  await clickVisibleOption(targetPage, "#vendors-options", "Blacksmith");
  await targetPage.locator("#merchant-panel").waitFor({ state: "visible" });
  requireCondition(
    (await targetPage.locator("#merchant-weapon-name").innerText()) === "Sunder-Spire" &&
      await targetPage.locator("#merchant-targets button").count() === 2 &&
      await targetPage.locator("#merchant-slots .merchant-row").count() === 4 &&
      await targetPage.locator("#merchant-slots button:enabled").count() === 1 &&
      (await targetPage.locator("#merchant-dismantle").innerText()).includes("Goblin Scrap x3"),
    "Blacksmith omitted the selected weapon, four slots, authoritative availability, or dismantle offer",
  );
  console.log("PYD8|BROWSER|HUB_BLACKSMITH|PASS");
  await clickVisibleOption(targetPage, "#merchant-targets", "Azhvielle");
  requireCondition(
    (await targetPage.locator("#merchant-weapon-name").innerText()) === "Needle of Plain Iron" &&
      (await targetPage.locator("#merchant-targets button[aria-pressed='true']").innerText()) === "Azhvielle",
    "Blacksmith target selection did not switch to the chosen companion's weapon",
  );
  await clickVisibleOption(
    targetPage,
    "#merchant-slots .merchant-row:first-child",
    "Improve",
  );
  requireCondition(
    (await targetPage.locator("#merchant-slots .merchant-row").first().innerText()).includes("3/100") &&
      (await targetPage.locator("#merchant-crafting").innerText()).includes("20 XP"),
    "Blacksmith improvement did not render the authoritative slot and Crafting updates",
  );
  await clickVisibleOption(targetPage, "#merchant-dismantle", "Dismantle");
  requireCondition(
    (await targetPage.locator("#merchant-materials").innerText()).includes("Cord: 1") &&
      (await targetPage.locator("#merchant-dismantle").innerText()).includes("Goblin Scrap x2"),
    "Blacksmith dismantling did not render the authoritative materials and remaining loot",
  );
  requireCondition(
    (await targetPage.locator("#merchant-component-recipes").innerText()).includes("Obsidian Focus Fittings") &&
      await targetPage.locator("#merchant-component-recipes button:enabled").count() === 1,
    "Blacksmith did not show the available Grade-I component recipe",
  );
  await clickVisibleOption(targetPage, "#merchant-component-recipes", "Craft & Install");
  requireCondition(
    !(await targetPage.locator("#merchant-component-recipes").innerText()).includes("Obsidian Focus Fittings") &&
      (await targetPage.locator("#merchant-materials").innerText()).includes("Scrap metal: 1"),
    "Crafting and installing did not consume material and remove the installed recipe",
  );
  await clickVisibleOption(targetPage, "#merchant-options", "Back");
  await targetPage.locator("#merchant-panel").waitFor({ state: "hidden" });
  await targetPage.locator("#vendors-panel").waitFor({ state: "visible" });
  await clickVisibleOption(targetPage, "#vendors-options", "Back");
  await targetPage.locator("#vendors-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(targetPage, "#overworld-options", "Character");
  await targetPage.locator("#character-panel").waitFor({ state: "visible" });
  requireCondition(
    await targetPage.locator("#character-targets button").count() === 2,
    "Character page omitted the party Drifter selector",
  );
  await clickVisibleOption(targetPage, "#character-targets", "Azhvielle");
  requireCondition(
    (await targetPage.locator("#character-name").innerText()) === "Azhvielle" &&
      (await targetPage.locator("#character-targets button[aria-pressed='true']").innerText()) === "Azhvielle",
    "Character page did not switch its profile to the selected companion",
  );
  await clickVisibleOption(targetPage, "#character-targets", "Ser Branoc");
  await clickVisibleOption(targetPage, "#character-options", "Weapon");
  await targetPage.locator("#weapon-panel").waitFor({ state: "visible" });
  requireCondition(
    await targetPage.locator("#weapon-targets button").count() === 2 &&
      await targetPage.locator("#weapon-components .weapon-component-slot").count() === 4,
    "Weapon page omitted the party Drifter picker or four component slots",
  );
  await clickVisibleOption(targetPage, "#weapon-targets", "Azhvielle");
  requireCondition(
    (await targetPage.locator("#weapon-components").innerText()).includes("Obsidian Focus Fittings") &&
      (await targetPage.locator("#weapon-components .weapon-component-slot").first().innerText()).includes("Installed"),
    "Crafting and installing did not update the selected Drifter's installed part",
  );
  await clickVisibleOption(targetPage, "#weapon-options", "Back");
  await targetPage.locator("#character-panel").waitFor({ state: "visible" });
  await clickVisibleOption(targetPage, "#character-options", "Back");
  await targetPage.locator("#character-panel").waitFor({ state: "hidden" });
  const merchantCommands = await targetPage.evaluate(() => window.__fixtureCommands.slice(5));
  requireCondition(
    JSON.stringify(merchantCommands) === JSON.stringify([
      { kind: "overworld_action", action: "select_party" },
      { kind: "active_pair", drifter_ids: ["joruun", "azhvielle"] },
      { kind: "overworld_action", action: "vendors" },
      { kind: "overworld_action", action: "blacksmith" },
      { kind: "merchant_target", drifter_id: "azhvielle" },
      { kind: "merchant_improve", target_drifter_id: "azhvielle", slot_id: "focus_fittings" },
      { kind: "merchant_dismantle", target_drifter_id: "azhvielle", item_id: "goblin_scrap" },
      { kind: "merchant_craft_component", target_drifter_id: "azhvielle", component_id: "needle_focus_fitted" },
      { kind: "overworld_action", action: "back" },
      { kind: "overworld_action", action: "back" },
      { kind: "overworld_action", action: "character" },
      { kind: "character_target", drifter_id: "azhvielle" },
      { kind: "character_target", drifter_id: "branoc" },
      { kind: "overworld_action", action: "weapon" },
      { kind: "weapon_target", drifter_id: "azhvielle" },
      { kind: "overworld_action", action: "back" },
      { kind: "overworld_action", action: "back" },
    ]),
    `Hub component flow did not submit the exact selected Drifter and offered actions: ${JSON.stringify(merchantCommands)}`,
  );
  console.log("PYD8|BROWSER|HUB_WEAPON_COMPONENTS|PASS");

  await clickVisibleOption(targetPage, "#overworld-options", "Items");
  await targetPage.locator("#items-panel").waitFor({ state: "visible" });
  requireCondition(
    (await targetPage.locator("#items-list").innerText()).includes("Goblin Scrap x3 | Hub Storage"),
    "Items page did not show the secured Goblin Scrap stack",
  );
  await clickVisibleOption(targetPage, "#items-list", "Goblin Scrap x3 | Hub Storage");
  await clickVisibleOption(targetPage, "#items-options", "Inspect");
  await targetPage.locator("#items-inspection").waitFor({ state: "visible" });
  requireCondition(
    (await targetPage.locator("#items-inspection").innerText()).includes("Quantity: 3") &&
      (await targetPage.locator("#items-inspection").innerText()).includes("dismantling"),
    "Item inspection did not show the secured stack quantity and description",
  );
  await clickVisibleOption(targetPage, "#items-options", "Back");
  await clickVisibleOption(targetPage, "#items-options", "Back");
  await targetPage.locator("#items-panel").waitFor({ state: "hidden" });
  console.log("PYD9|BROWSER|SHARED_ITEMS_INSPECT|PASS");

  await clickVisibleOption(targetPage, "#overworld-options", "Region Portal");
  await targetPage.locator("#screen-badge").filter({ hasText: "REGION PORTAL" }).waitFor({ state: "visible" });
  await targetPage.locator("#region-panel").waitFor({ state: "visible" });
  await clickVisibleOption(targetPage, "#region-choices", "Region 1");
  await targetPage.locator("#screen-badge").filter({ hasText: "DESTINATIONS" }).waitFor({ state: "visible" });
  const floorOneDestination = targetPage.getByRole("button", { name: "Floor I", exact: true });
  requireCondition(
    await floorOneDestination.isEnabled() &&
      await targetPage.locator("#region-choices button").filter({ hasText: "Floor II" }).isDisabled(),
    "Region Portal did not render authoritative Floor I availability and Floor II prerequisites",
  );
  await floorOneDestination.click();
  await targetPage.locator("#screen-badge").filter({ hasText: "FLOOR_ONE_WARNING" }).waitFor({ state: "visible" });
  requireCondition(
    (await targetPage.locator("#adventure-text").innerText()).includes("Death means returning to the Hub") &&
      await targetPage.getByRole("button", { name: "Set Out" }).isVisible(),
    "Floor 1 warning omitted its death consequence or explicit Set Out action",
  );
  await captureScreenshot(targetPage, "desktop-floor-one-warning");
  await clickVisibleOption(targetPage, "#overworld-options", "Set Out");
  await targetPage.locator("#party-panel").waitFor({ state: "visible" });
  requireCondition(
    await targetPage.locator("#party-members .party-member").count() === 2 &&
      await targetPage.locator("#enemy-panel .enemy").count() === 4,
    "Floor 1 Set Out did not open the four-Goblin party battle",
  );

  for (let battleNumber = 1; battleNumber <= 10; battleNumber += 1) {
    if (battleNumber > 1) {
      if (battleNumber === 6) {
        await targetPage.locator("#screen-badge").filter({ hasText: "REST" }).waitFor({ state: "visible" });
        await captureScreenshot(targetPage, "desktop-floor-one-midway-rest");
        await clickVisibleOption(targetPage, "#overworld-options", "Recover");
        await targetPage.locator("#screen-badge").filter({ hasText: "REST" }).waitFor({ state: "visible" });
        requireCondition(
          await targetPage.getByRole("button", { name: "Extract" }).isVisible(),
          "Recover removed the option to extract from the midway Rest",
        );
        await clickVisibleOption(targetPage, "#route-actions", "Continue Without Rest");
      } else if (battleNumber === 10) {
        await targetPage.locator("#screen-badge").filter({ hasText: "REST" }).waitFor({ state: "visible" });
        await clickVisibleOption(targetPage, "#route-actions", "Continue Without Rest");
      }
      await clickVisibleOption(targetPage, "#route-actions", "Enter Encounter");
      await targetPage.locator("#party-panel").waitFor({ state: "visible" });
    }
    await clickVisibleOption(targetPage, "#actions", "Defend");
    if (battleNumber === 5 || battleNumber === 9) {
      await targetPage.locator("#screen-badge").filter({ hasText: "REST" }).waitFor({ state: "visible" });
    }
  }
  await targetPage.locator("#overworld-screen").waitFor({ state: "visible" });
  requireCondition(
    (await targetPage.locator("#hub-shared-gold").innerText()) === "Shared gold: 115" &&
      (await targetPage.locator("#location-label").innerText()) === "Floor 1 Hub" &&
      await targetPage.locator("#party-panel").isHidden(),
    "Goblin Lord victory did not return the cleared party and secured rewards to the Hub",
  );
  await captureScreenshot(targetPage, "desktop-floor-one-cleared-hub");
  await clickVisibleOption(targetPage, "#overworld-options", "Region Portal");
  await clickVisibleOption(targetPage, "#region-choices", "Region 1");
  const floorTwoAfterFloorOne = targetPage.locator("#region-choices button").filter({ hasText: "Floor II" });
  requireCondition(
    await floorTwoAfterFloorOne.isEnabled() &&
      await targetPage.getByRole("button", { name: "Floor I", exact: true }).isEnabled(),
    "cleared Floor I did not unlock Floor II while preserving backward access",
  );
  await clickVisibleOption(targetPage, "#overworld-options", "Back");
  await clickVisibleOption(targetPage, "#overworld-options", "Back");
  await targetPage.locator("#screen-badge").filter({ hasText: "HUB" }).waitFor({ state: "visible" });
  console.log("M8.1_BROWSER|REGION_PORTAL_FLOOR_I_RETURN_AND_BACKWARD_ACCESS|PASS");
  const firstClearCommands = await targetPage.evaluate(() => window.__fixtureCommands);
  requireCondition(
    firstClearCommands.filter((command) => command.action === "enter_encounter").length === 9 &&
      firstClearCommands.filter((command) => command.intent === "defend").length === 11 &&
      firstClearCommands.some((command) => command.action === "rest") &&
      firstClearCommands.some((command) => command.action === "skip_rest"),
    `Floor 1 browser route omitted its ten Battles or two Rest choices: ${JSON.stringify(firstClearCommands)}`,
  );
  console.log("PYD7|BROWSER|FLOOR_ONE_BATTLE_10|PASS");
  console.log("PYD7|BROWSER|FLOOR_ONE_BOSS_CLEAR|PASS");

  await clickVisibleOption(targetPage, "#overworld-options", "Start Floor 1");
  await clickVisibleOption(targetPage, "#overworld-options", "Set Out");
  for (let battleNumber = 1; battleNumber <= 5; battleNumber += 1) {
    if (battleNumber > 1) {
      await clickVisibleOption(targetPage, "#route-actions", "Enter Encounter");
      await targetPage.locator("#party-panel").waitFor({ state: "visible" });
    }
    await clickVisibleOption(targetPage, "#actions", "Defend");
  }
  await targetPage.locator("#screen-badge").filter({ hasText: "REST" }).waitFor({ state: "visible" });
  await clickVisibleOption(targetPage, "#overworld-options", "Extract");
  await targetPage.locator("#extraction-rewards").waitFor({ state: "visible" });
  requireCondition(
    (await targetPage.locator("#extraction-rewards").innerText()).includes("140 EXP | 21 gold"),
    "midway replay extraction did not show the reduced 50% reward",
  );
  await captureScreenshot(targetPage, "desktop-floor-one-extraction");
  await clickVisibleOption(targetPage, "#overworld-options", "Return to Hub");
  requireCondition(
    (await targetPage.locator("#hub-shared-gold").innerText()) === "Shared gold: 136",
    "safe early extraction did not secure its reduced gold at the Hub",
  );
  const fullFloorOneCommands = await targetPage.evaluate(() => window.__fixtureCommands);
  requireCondition(
    fullFloorOneCommands.filter((command) => command.action === "start_floor_one").length === 1 &&
      fullFloorOneCommands.filter((command) => command.kind === "destination" && command.destination_id === "floor_one").length === 1 &&
      fullFloorOneCommands.filter((command) => command.action === "extract").length === 1 &&
      fullFloorOneCommands.filter((command) => command.action === "return_to_hub").length === 2,
    `Floor 1 browser replay did not use the expected semantic actions: ${JSON.stringify(fullFloorOneCommands)}`,
  );
  console.log("PYD7|BROWSER|FLOOR_ONE_REPLAY_MIDWAY_REST|PASS");
  console.log("PYD7|BROWSER|FLOOR_ONE_REPLAY_EXTRACT|PASS");

  await targetPage.evaluate(() => {
    window.__fixtureHubMode = true;
    window.__fixtureDefeatMode = true;
    window.__fixtureHubPhase = "hub";
    window.__fixtureCommands = [];
  });
  await restartForNewGame(targetPage);
  await targetPage.locator('#drifter-options [data-drifter-id="branoc"]').click();
  await targetPage.locator("#overworld-screen").waitFor({ state: "visible" });
  await clickVisibleOption(targetPage, "#overworld-options", "Recruit Companion");
  await clickVisibleOption(targetPage, "#companion-choices", "Azhvielle");
  await clickVisibleOption(targetPage, "#overworld-options", "Ready / Set Out");
  await targetPage.locator("#party-panel").waitFor({ state: "visible" });
  await clickVisibleOption(targetPage, "#actions", "Defend");
  await targetPage.locator("#selection-screen").waitFor({ state: "visible" });
  requireCondition(
    await targetPage.locator("#battle-screen").isHidden() &&
      await targetPage.locator("#drifter-options [data-drifter-id]").count() === 4,
    "Python defeat result did not return the browser to Drifter selection",
  );
  await targetPage.locator('#drifter-options [data-drifter-id="zhaivra"]').click();
  await targetPage.locator("#overworld-screen").waitFor({ state: "visible" });
  requireCondition(
    await targetPage.evaluate(() =>
      window.__fixtureStartCalls.slice(-2).join(",") === "branoc,zhaivra" &&
        window.__fixtureSelectedDrifter === "zhaivra" &&
        window.__fixtureCommands.at(-1).intent === "defend") &&
      (await targetPage.locator("#screen-badge").innerText()) === "OVERWORLD" &&
      (await targetPage.locator("#location-label").innerText()) === "The road ahead",
    "defeat did not allow a new Drifter selection and fresh Overworld session",
  );
  console.log("PYD7|BROWSER|DEFEAT_RESELECT|PASS");

  await restartForNewGame(page);
  await page.locator('#drifter-options [data-drifter-id="branoc"]').click();
  await page.locator("#overworld-screen").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#overworld-options", "Options");
  await page.waitForFunction(
    () => document.getElementById("screen-badge").textContent.trim() === "OPTIONS",
  );
  await clickVisibleOption(page, "#overworld-options", "Save");
  await page.locator("#notice").filter({ hasText: "Game saved." }).waitFor({ state: "visible" });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  }).catch(async (error) => {
    const startupError = await page.locator("#error-message").innerText().catch(() => "");
    throw new Error(startupError || errors.join("; ") || error.message);
  });
  await page.getByRole("button", { name: "Start" }).click();
  await page.locator("#saved-game-dialog").waitFor({ state: "visible" });
  const savedEnvelopeBeforeChoice = await page.evaluate(() => {
    const key = "dungeon-drifters.profile.v1.d4d4d4d4-0000-4000-8000-000000000001";
    return localStorage.getItem(key);
  });
  await page.getByRole("button", { name: "Continue" }).click();
  await page.locator("#overworld-screen").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#overworld-options", "Character");
  await page.locator("#character-panel").waitFor({ state: "visible" });
  requireCondition(
    (await page.locator("#character-name").innerText()).includes("Ser Branoc") &&
      await page.locator("#location-label").innerText() === "Goblin Ambush",
    "startup Continue did not restore the saved Drifter and route",
  );
  await page.locator("#restart").click();
  await page.locator("#save-replacement-dialog").waitFor({ state: "visible" });
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  await page.locator("#saved-game-dialog").waitFor({ state: "visible" });
  await page.getByRole("button", { name: "New Game" }).click();
  await page.locator("#save-replacement-dialog").waitFor({ state: "visible" });
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  await page.locator("#saved-game-dialog").waitFor({ state: "visible" });
  requireCondition(
    await page.evaluate(() => {
      const key = "dungeon-drifters.profile.v1.d4d4d4d4-0000-4000-8000-000000000001";
      return localStorage.getItem(key);
    }) === savedEnvelopeBeforeChoice,
    "canceling new-game replacement changed the saved profile",
  );
  await page.getByRole("button", { name: "New Game" }).click();
  await page.locator("#save-replacement-dialog").waitFor({ state: "visible" });
  await page.getByRole("button", { name: "Replace Saved Game" }).click();
  await page.locator("#selection-screen").waitFor({ state: "visible" });
  await page.locator('#drifter-options [data-drifter-id="joruun"]').click();
  await page.locator("#overworld-screen").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#overworld-options", "Options");
  await clickVisibleOption(page, "#overworld-options", "Save");
  await page.locator("#notice").filter({ hasText: "Game saved." }).waitFor({ state: "visible" });
  const replacedProfile = await page.evaluate(() => {
    const key = "dungeon-drifters.profile.v1.d4d4d4d4-0000-4000-8000-000000000001";
    return JSON.parse(localStorage.getItem(key));
  });
  const previousSequence = JSON.parse(savedEnvelopeBeforeChoice).local_sequence;
  requireCondition(
    replacedProfile.local_sequence === previousSequence + 1 &&
      replacedProfile.payload.player.identity.profile.choice === "4",
    "confirmed New Game did not replace the profile exactly once with the chosen Drifter",
  );
  requireCondition(errors.length === 0, `browser page errors after save/reload: ${errors.join("; ")}`);
  console.log("PYD7|BROWSER|SAVE_RELOAD|PASS");
  console.log("F1_BROWSER|CONTINUE_REPLACE_CANCEL|PASS");

  await restartForNewGame(page);
  await page.keyboard.press("Shift+Alt+C");
  await page.locator("#shortcut-dialog").waitFor({ state: "visible" });
  await page.locator("#shortcut-code").fill("F01BA");
  await page.locator('#shortcut-form button[type="submit"]').click();
  await page.locator("#overworld-screen").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#overworld-options", "Choose Party");
  await page.waitForFunction(
    () => document.getElementById("screen-badge").textContent.trim() === "PARTY SELECTION",
  );
  requireCondition(
    await page.locator("#party-pair-choices .party-pair-choice").count() === 2,
    "the real browser runtime did not offer both ordered choices for the recruited pair",
  );
  const savedActivePairLabel =
    "Azhvielle, the Unconfessed + Ser Branoc, the Unbroken Crest";
  await clickVisibleOption(page, "#party-pair-choices", savedActivePairLabel);
  await page.locator("#screen-badge").filter({ hasText: "HUB" }).waitFor({ state: "visible" });

  await clickVisibleOption(page, "#overworld-options", "Character");
  await page.locator("#character-panel").waitFor({ state: "visible" });
  requireCondition(
    await page.locator("#character-targets button").count() === 2,
    "the real Hub character view did not expose both recruited Drifters",
  );
  await clickVisibleOption(page, "#character-options", "Skills");
  await page.locator("#skills-panel").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#skills-targets", "Azhvielle, the Unconfessed");
  await page.locator("#skills-targets button[aria-pressed='true']")
    .filter({ hasText: "Azhvielle, the Unconfessed" }).waitFor();
  const strengthRow = page.locator("#skill-stats .skill-stat").filter({ hasText: "Strength" });
  const strengthBefore = await strengthRow.locator(".skill-value").innerText();
  const growthBefore = await page.locator("#growth-summary").innerText();
  requireCondition(
    growthBefore.startsWith("Growth Points:") &&
      Number(growthBefore.match(/\d+/)?.[0] || 0) > 0,
    "the controlled Hub state did not provide a Growth Point for the recruited target",
  );
  const passiveSkillRow = page.locator(
    '#skill-advancement [data-skill-id="azhvielle_p01"]',
  );
  const activeSkillRow = page.locator(
    '#skill-advancement [data-skill-id="azhvielle_a01"]',
  );
  await passiveSkillRow.getByRole("button", { name: /Purchase/ }).click();
  await page.waitForFunction(() =>
    document.querySelector('#skill-advancement [data-skill-id="azhvielle_p01"]')
      ?.innerText.includes("Purchased"),
  );
  await activeSkillRow.getByRole("button", { name: /Purchase/ }).click();
  await page.waitForFunction(() =>
    document.querySelector('#skill-advancement [data-skill-id="azhvielle_a01"]')
      ?.innerText.includes("Purchased"),
  );
  const firstMoveSlot = page.locator('#skill-loadout select[data-slot="0"]');
  await firstMoveSlot.selectOption("azhvielle_a01");
  await page.waitForFunction(() =>
    document.querySelector('#skill-loadout select[data-slot="0"]')?.value ===
      "azhvielle_a01",
  );
  await strengthRow.getByRole("button", { name: "[+1]" }).click();
  await page.waitForFunction((previous) => {
    const row = [...document.querySelectorAll("#skill-stats .skill-stat")]
      .find((candidate) => candidate.querySelector(".skill-label")?.textContent === "Strength");
    return row?.querySelector(".skill-value")?.textContent !== previous;
  }, strengthBefore);
  const savedMemberProgression = {
    drifter: "azhvielle",
    strength: await strengthRow.locator(".skill-value").innerText(),
    growth: await page.locator("#growth-summary").innerText(),
    passive: await passiveSkillRow.innerText(),
    active: await activeSkillRow.innerText(),
    equippedMove: await page.locator('#skill-loadout select[data-slot="0"]')
      .inputValue(),
  };
  await clickVisibleOption(page, "#skills-options", "Back");
  await page.locator("#character-panel").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#character-options", "Back");
  await page.locator("#character-panel").waitFor({ state: "hidden" });

  await clickVisibleOption(page, "#overworld-options", "Vendors");
  await clickVisibleOption(page, "#vendors-options", "Blacksmith");
  await page.locator("#merchant-panel").waitFor({ state: "visible" });
  const branocMerchantTarget = page.locator("#merchant-targets button").filter({ hasText: "Ser Branoc" });
  await branocMerchantTarget.click();

  const scrapRow = page.locator("#merchant-dismantle .merchant-row").filter({ hasText: "Goblin Scrap" });
  requireCondition(await scrapRow.count() === 1, "weapon save/reload scenario did not provide Goblin Scrap");
  const scrapBeforeDismantle = await scrapRow.innerText();
  await scrapRow.getByRole("button", { name: "Dismantle" }).click();
  await page.waitForFunction((previous) => {
    const row = [...document.querySelectorAll("#merchant-dismantle .merchant-row")]
      .find((candidate) => candidate.innerText.includes("Goblin Scrap"));
    return row && row.innerText !== previous;
  }, scrapBeforeDismantle);
  requireCondition(
    Number((await scrapRow.innerText()).match(/Goblin Scrap x(\d+)/)?.[1] || 0) ===
      Number(scrapBeforeDismantle.match(/Goblin Scrap x(\d+)/)?.[1] || 0) - 1,
    "Blacksmith dismantling did not consume exactly one Goblin Scrap",
  );

  const metalStockRow = page.locator("#merchant-supplies .hub-supply-row")
    .filter({ hasText: "Grade I Metal" });
  requireCondition(
    await metalStockRow.count() === 1 &&
      (await metalStockRow.innerText()).includes("Stock 2 | 4 gold"),
    "Blacksmith did not offer its two authored Grade-I metal units",
  );
  for (let purchase = 0; purchase < 2; purchase += 1) {
    const previous = await metalStockRow.innerText();
    await metalStockRow.getByRole("button", { name: "Buy", exact: true }).click();
    await page.waitForFunction((prior) => {
      const row = [...document.querySelectorAll("#merchant-supplies .hub-supply-row")]
        .find((candidate) => candidate.innerText.includes("Grade I Metal"));
      return row && row.innerText !== prior;
    }, previous);
  }
  const scrapMetalCount = async () => {
    const text = await page.locator("#merchant-materials").innerText();
    return Number(text.match(/Scrap metal:\s*(\d+)/i)?.[1] || 0);
  };
  requireCondition(
    await scrapMetalCount() >= 2,
    "Blacksmith metal purchases did not provide enough material to craft and improve Branoc's weapon",
  );

  const bladeRecipeTitle = page.getByText(
    "Reinforced Blade and Guard | Blade / Guard assembly",
    { exact: true },
  );
  const bladeRecipe = page.locator("#merchant-component-recipes .merchant-row")
    .filter({ has: bladeRecipeTitle });
  requireCondition(
    await bladeRecipe.count() === 1,
    "Grade-I Reinforced Blade and Guard recipe was not uniquely available",
  );
  const craftingBeforeRecipe = await page.locator("#merchant-crafting").innerText();
  const materialsBeforeRecipe = await page.locator("#merchant-materials").innerText();
  await bladeRecipe.getByRole("button", { name: "Craft & Install" }).click();
  await page.waitForFunction(({ crafting, materials }) =>
    document.getElementById("merchant-crafting").innerText !== crafting &&
      document.getElementById("merchant-materials").innerText !== materials &&
      [...document.querySelectorAll("#merchant-component-recipes strong")]
        .every((title) => title.textContent.trim() !== "Reinforced Blade and Guard | Blade / Guard assembly"),
  { crafting: craftingBeforeRecipe, materials: materialsBeforeRecipe });
  requireCondition(
    (await page.locator("#merchant-crafting").innerText()) !== craftingBeforeRecipe,
    "Crafted Reinforced Blade and Guard did not award Crafting experience",
  );
  const bladeSlot = page.locator("#merchant-slots .merchant-row").first();
  const slotBeforeImprovement = await bladeSlot.innerText();
  await bladeSlot.getByRole("button", { name: "Improve" }).click();
  await page.waitForFunction((previous) =>
    document.querySelector("#merchant-slots .merchant-row").innerText !== previous,
  slotBeforeImprovement);

  await clickVisibleOption(page, "#merchant-options", "Back");
  await page.locator("#merchant-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#vendors-options", "Back");
  await page.locator("#vendors-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#overworld-options", "Character");
  await page.locator("#character-panel").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#character-options", "Weapon");
  await page.locator("#weapon-panel").waitFor({ state: "visible" });
  const bladeComponent = page.locator("#weapon-components .weapon-component-slot").first();
  const installedBladeState = await bladeComponent.innerText();
  requireCondition(
    installedBladeState.includes("Installed: Reinforced Blade and Guard"),
    "Branoc's crafted component was not installed before saving",
  );

  await clickVisibleOption(page, "#weapon-options", "Back");
  await page.locator("#character-panel").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#character-options", "Back");
  await page.locator("#character-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#overworld-options", "Vendors");
  await clickVisibleOption(page, "#vendors-options", "Blacksmith");
  await page.locator("#merchant-panel").waitFor({ state: "visible" });
  const savedWeaponProgression = {
    crafting: await page.locator("#merchant-crafting").innerText(),
    slot: await page.locator("#merchant-slots .merchant-row").first().innerText(),
    materials: await page.locator("#merchant-materials").innerText(),
  };
  requireCondition(
    /\d+\/100/.test(savedWeaponProgression.slot) &&
      /\d+ XP/.test(savedWeaponProgression.crafting) &&
      savedWeaponProgression.materials.includes("Scrap metal:"),
    `weapon progression state was incomplete before saving: ${JSON.stringify(savedWeaponProgression)}`,
  );
  await clickVisibleOption(page, "#merchant-options", "Back");
  await page.locator("#merchant-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#vendors-options", "Back");
  await page.locator("#vendors-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#overworld-options", "Options");
  await page.waitForFunction(
    () => document.getElementById("screen-badge").textContent.trim() === "OPTIONS",
  );
  await clickVisibleOption(page, "#overworld-options", "Save");
  await page.locator("#notice").filter({ hasText: "Game saved." }).waitFor({ state: "visible" });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  }).catch(async (error) => {
    const startupError = await page.locator("#error-message").innerText().catch(() => "");
    throw new Error(startupError || errors.join("; ") || error.message);
  });
  await continueSavedGameAfterReload(page);
  const restoredHubState = {
    location: await page.locator("#location-label").innerText(),
    adventure: await page.locator("#adventure-text").innerText(),
    badge: await page.locator("#screen-badge").innerText(),
    notice: await page.locator("#notice").innerText(),
  };
  requireCondition(
    restoredHubState.location === "Floor 1 Hub",
    `browser Continue did not restore Branoc's weapon progression: ${JSON.stringify(restoredHubState)}`,
  );
  await clickVisibleOption(page, "#overworld-options", "Choose Party");
  await page.waitForFunction(
    () => document.getElementById("screen-badge").textContent.trim() === "PARTY SELECTION",
  );
  const restoredActivePair = page.locator("#party-pair-choices .party-pair-choice.is-selected");
  requireCondition(
    await page.locator("#party-pair-choices .party-pair-choice").count() === 2 &&
      await restoredActivePair.count() === 1 &&
      (await restoredActivePair.innerText()) === savedActivePairLabel,
    "saved active-pair selection did not survive browser reload",
  );
  await clickVisibleOption(page, "#overworld-options", "Back");
  await page.waitForFunction(
    () => document.getElementById("screen-badge").textContent.trim() === "HUB",
  );
  await clickVisibleOption(page, "#overworld-options", "Character");
  await page.locator("#character-panel").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#character-options", "Skills");
  await page.locator("#skills-panel").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#skills-targets", "Azhvielle, the Unconfessed");
  await page.locator("#skills-targets button[aria-pressed='true']")
    .filter({ hasText: "Azhvielle, the Unconfessed" }).waitFor();
  const restoredStrengthRow = page.locator("#skill-stats .skill-stat").filter({ hasText: "Strength" });
  const restoredMemberProgression = {
    strength: await restoredStrengthRow.locator(".skill-value").innerText(),
    growth: await page.locator("#growth-summary").innerText(),
    passive: await page.locator(
      '#skill-advancement [data-skill-id="azhvielle_p01"]',
    ).innerText(),
    active: await page.locator(
      '#skill-advancement [data-skill-id="azhvielle_a01"]',
    ).innerText(),
    equippedMove: await page.locator('#skill-loadout select[data-slot="0"]')
      .inputValue(),
  };
  requireCondition(
    restoredMemberProgression.strength === savedMemberProgression.strength &&
      restoredMemberProgression.growth === savedMemberProgression.growth &&
      restoredMemberProgression.passive.includes("Purchased") &&
      restoredMemberProgression.active.includes("Purchased") &&
      restoredMemberProgression.equippedMove === "azhvielle_a01",
    `Azhvielle's skills, loadout, or stat investment did not survive browser reload: ${JSON.stringify({ savedMemberProgression, restoredMemberProgression })}`,
  );
  console.log("M3_BROWSER|ADVANCEMENT_SAVE_RELOAD|PASS");
  console.log("M1_BROWSER|ACTIVE_PAIR_SAVE_RELOAD|PASS");
  await clickVisibleOption(page, "#skills-options", "Back");
  await page.locator("#character-panel").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#character-options", "Back");
  await page.locator("#character-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#overworld-options", "Character");
  await page.locator("#character-panel").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#character-options", "Weapon");
  await page.locator("#weapon-panel").waitFor({ state: "visible" });
  const loadedWeaponTarget = page.locator("#weapon-targets button").filter({ hasText: "Ser Branoc" });
  await loadedWeaponTarget.click();
  await page.locator("#weapon-targets button[aria-pressed='true']")
    .filter({ hasText: "Ser Branoc" }).waitFor();
  const loadedBladeState = await page.locator("#weapon-components .weapon-component-slot").first().innerText();
  requireCondition(
    loadedBladeState.includes("Installed: Reinforced Blade and Guard") &&
      loadedBladeState === installedBladeState,
    `browser reload and Load did not restore Branoc's weapon progression: installed component changed: ${JSON.stringify({ installedBladeState, loadedBladeState })}`,
  );
  await clickVisibleOption(page, "#weapon-options", "Back");
  await page.locator("#character-panel").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#character-options", "Back");
  await page.locator("#character-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#overworld-options", "Vendors");
  await clickVisibleOption(page, "#vendors-options", "Blacksmith");
  await page.locator("#merchant-panel").waitFor({ state: "visible" });
  const loadedWeaponProgression = {
    crafting: await page.locator("#merchant-crafting").innerText(),
    slot: await page.locator("#merchant-slots .merchant-row").first().innerText(),
    materials: await page.locator("#merchant-materials").innerText(),
  };
  requireCondition(
    JSON.stringify(loadedWeaponProgression) === JSON.stringify(savedWeaponProgression),
    `browser reload and Load did not restore Branoc's weapon progression: ${JSON.stringify({ savedWeaponProgression, loadedWeaponProgression })}`,
  );
  requireCondition(errors.length === 0, `browser page errors after weapon save/reload: ${errors.join("; ")}`);
  console.log("PYD7|BROWSER|WEAPON_SAVE_RELOAD|PASS");

  await clickVisibleOption(page, "#merchant-options", "Back");
  await page.locator("#merchant-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#vendors-options", "Back");
  await page.locator("#vendors-panel").waitFor({ state: "hidden" });

  const supplyRow = (name) => page.locator("#merchant-supplies .hub-supply-row")
    .filter({ hasText: name }).first();
  const supplyActionTrace = [];
  const supplyDiagnostic = async (name) => {
    const state = await page.evaluate(({ profileKey, itemName }) => {
      const rows = [...document.querySelectorAll("#merchant-supplies .hub-supply-row")]
        .filter((candidate) => candidate.querySelector("strong")?.textContent.trim() === itemName);
      const row = rows[0];
      const summary = document.getElementById("merchant-storage-summary")?.innerText || "";
      const quantities = row?.innerText.match(/Stored\s+(\d+)\s+\|\s+Carried\s+(\d+)/);
      const capacity = summary.match(/Carried supplies:\s*(\d+)\/(\d+)/);
      const envelope = JSON.parse(localStorage.getItem(profileKey) || "null");
      const visible = (element) => Boolean(
        element && !element.hidden && element.getClientRects().length > 0 &&
          getComputedStyle(element).display !== "none",
      );
      const mutationTrace = window.__DD_SUPPLY_MUTATION_TRACE__;
      return {
        screen: document.getElementById("screen-badge")?.innerText.trim(),
        location: document.getElementById("location-label")?.innerText.trim(),
        hubEconomyTitle: document.getElementById("hub-economy-title")?.innerText.trim(),
        interactionPhase: document.getElementById("app")?.dataset.interactionPhase || null,
        panels: Object.fromEntries([
          "overworld-screen",
          "vendors-panel",
          "hub-economy-panel",
          "merchant-panel",
          "party-panel",
          "route-actions",
        ].map((id) => [id, visible(document.getElementById(id))])),
        supplyContainerVisible: visible(document.getElementById("merchant-supplies")),
        supplyRowCount: rows.length,
        supplyRowText: row?.innerText || null,
        storedQuantity: quantities ? Number(quantities[1]) : null,
        carriedQuantity: quantities ? Number(quantities[2]) : null,
        actions: row ? [...row.querySelectorAll("button")].map((button) => ({
          label: button.innerText.trim(),
          disabled: button.disabled,
          ariaDisabled: button.getAttribute("aria-disabled"),
          title: button.title,
          visible: visible(button),
        })) : [],
        storageSummary: summary,
        carriedUnits: capacity ? Number(capacity[1]) : null,
        carriedCapacity: capacity ? Number(capacity[2]) : null,
        persistedTransactionSequence:
          envelope?.payload?.party?.hub_economy?.transaction_sequence ?? null,
        notice: document.getElementById("notice")?.innerText.trim(),
        mutationTrace: mutationTrace ? {
          mutationCount: mutationTrace.mutationCount,
          ageSinceLastMutationMs: mutationTrace.lastMutationAtMs === null
            ? null
            : performance.now() - mutationTrace.lastMutationAtMs,
          lastSupplyClick: mutationTrace.lastSupplyClick,
          recentMutations: mutationTrace.recentMutations,
        } : null,
      };
    }, { profileKey: floorTwoProfileKey, itemName: name });
    return {
      ...state,
      recentSupplyActions: supplyActionTrace.slice(-12),
      pendingNetworkRequests: [...pendingRequests.values()],
      pageErrors: errors.slice(),
    };
  };
  const updateSupply = async (name, action) => {
    const row = supplyRow(name);
    const previous = await row.innerText();
    const transaction = {
      name,
      action,
      previous,
      startingSequence: await page.evaluate((key) => {
        const envelope = JSON.parse(localStorage.getItem(key) || "null");
        return envelope?.payload?.party?.hub_economy?.transaction_sequence ?? null;
      }, floorTwoProfileKey),
      status: "pending",
    };
    supplyActionTrace.push(transaction);
    const button = action === "Sell"
      ? row.getByRole("button", { name: /^Sell \d+g$/ }).first()
      : row.getByRole("button", { name: action, exact: true });
    transaction.clickAttempts = 1;
    try {
      await button.click({ timeout: 500 });
      transaction.clickStatus = "completed";
    } catch (error) {
      if (error.name !== "TimeoutError") throw error;
      transaction.clickStatus = "timed_out_waiting_for_click";
    }
    try {
      await page.waitForFunction(({ itemName, oldText }) => {
        const current = [...document.querySelectorAll("#merchant-supplies .hub-supply-row")]
          .find((candidate) => candidate.innerText.includes(itemName));
        return current && current.innerText !== oldText;
      }, { itemName: name, oldText: previous });
    } catch (error) {
      const diagnostic = await supplyDiagnostic(name);
      console.log(`M8.3_BROWSER|SUPPLY_ACTION_TIMEOUT|${JSON.stringify({ name, action, diagnostic })}`);
      throw new Error(`Supply ${action} for ${name} did not reach a changed authoritative row: ${JSON.stringify(diagnostic)}`, { cause: error });
    }
    transaction.updated = await supplyRow(name).innerText();
    transaction.resultingSequence = await page.evaluate((key) => {
      const envelope = JSON.parse(localStorage.getItem(key) || "null");
      return envelope?.payload?.party?.hub_economy?.transaction_sequence ?? null;
    }, floorTwoProfileKey);
    transaction.status = "observed";
  };
  const quantityInSupplyRow = async (name, kind) => {
    const text = await supplyRow(name).innerText();
    const match = text.match(new RegExp(`${kind}\\s+(\\d+)`));
    return Number(match?.[1] || 0);
  };
  await clickVisibleOption(page, "#overworld-options", "Vendors");
  await clickVisibleOption(page, "#vendors-options", "Blacksmith");
  await page.locator("#merchant-panel").waitFor({ state: "visible" });
  const bossCore = page.locator("#merchant-dismantle .merchant-row")
    .filter({ hasText: "Goblin Lord Core" });
  requireCondition(await bossCore.count() === 1, "M2 supply setup did not provide a Goblin Lord Core");
  const coreBeforeDismantle = await bossCore.innerText();
  await bossCore.getByRole("button", { name: "Dismantle" }).click();
  await page.waitForFunction((previous) => {
    const row = [...document.querySelectorAll("#merchant-dismantle .merchant-row")]
      .find((candidate) => candidate.innerText.includes("Goblin Lord Core"));
    return !row || row.innerText !== previous;
  }, coreBeforeDismantle);

  await clickVisibleOption(page, "#merchant-options", "Back");
  await page.locator("#merchant-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#vendors-options", "Back");
  await page.locator("#vendors-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#overworld-options", "Vendors");
  await clickVisibleOption(page, "#vendors-options", "Merchant");
  await page.locator("#hub-economy-panel").waitFor({ state: "visible" });
  await updateSupply("Healing Potion", "Buy");
  await clickVisibleOption(page, "#hub-economy-options", "Back");
  await page.locator("#hub-economy-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#vendors-options", "Back");
  await page.locator("#vendors-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#overworld-options", "Vendors");
  await clickVisibleOption(page, "#vendors-options", "Alchemist");
  await page.locator("#hub-economy-panel").waitFor({ state: "visible" });
  await page.locator("#alchemy-progress").waitFor({ state: "visible" });
  requireCondition(
    (await supplyRow("Charcoal Powder").innerText()).includes("Stock 2 | 3 gold"),
    "Alchemist did not offer the approved two Charcoal Powder units at 3 gold each",
  );
  await updateSupply("Charcoal Powder", "Buy");
  await updateSupply("Charcoal Powder", "Buy");
  requireCondition(
    (await supplyRow("Sulfur").innerText()).includes("Stock 2 | 3 gold"),
    "Alchemist did not offer the approved two Sulfur units at 3 gold each",
  );
  await updateSupply("Sulfur", "Buy");
  await updateSupply("Sulfur", "Buy");
  requireCondition(
    await quantityInSupplyRow("Charcoal Powder", "Stored") === 2 &&
      await quantityInSupplyRow("Charcoal Powder", "Stock") === 0 &&
      await quantityInSupplyRow("Sulfur", "Stored") === 2 &&
      await quantityInSupplyRow("Sulfur", "Stock") === 0,
    "Alchemist purchases did not consume exactly two units of finite smoke-bomb ingredient stock",
  );
  const craftAlchemy = async (name) => {
    const row = page.locator("#merchant-alchemy-recipes .merchant-row")
      .filter({ has: page.locator("strong").getByText(name, { exact: true }) });
    const rowCount = await row.count();
    if (rowCount !== 1) {
      const recipes = await page.locator("#merchant-alchemy-recipes").innerText();
      const badge = await page.locator("#screen-badge").innerText();
      throw new Error(`M2 Alchemist did not offer ${name} (matches=${rowCount}, screen=${badge}, recipes=${recipes})`);
    }
    await page.locator("#notice").evaluate((element) => { element.textContent = ""; });
    await row.getByRole("button", { name: "Craft", exact: true }).click();
    await page.waitForFunction((message) =>
      document.getElementById("notice").textContent === message,
    name === "Smoke Bomb"
      ? "Crafted 1 Smoke Bomb; gained 15 Alchemy XP."
      : "Crafted 1 Mana Potion; gained 20 Alchemy XP.");
  };
  await craftAlchemy("Smoke Bomb");
  await craftAlchemy("Smoke Bomb");
  requireCondition(
    (await page.locator("#alchemy-progress").innerText()).trim() === "Alchemy Level 1 | 30 XP",
    `Alchemy recipes did not advance the approved profession track: ${await page.locator("#alchemy-progress").innerText()}`,
  );
  await clickVisibleOption(page, "#hub-economy-options", "Back");
  await page.locator("#hub-economy-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#vendors-options", "Back");
  await page.locator("#vendors-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#overworld-options", "Vendors");
  await clickVisibleOption(page, "#vendors-options", "Merchant");
  await page.locator("#hub-economy-panel").waitFor({ state: "visible" });
  const talismanRow = supplyRow("Return Talisman");
  requireCondition(
    (await talismanRow.innerText()).includes("Stock 1 | 100 gold"),
    "Merchant did not offer its single exclusive Return Talisman at 100 gold",
  );
  const goldBeforeTalisman = Number(
    (await page.locator("#merchant-storage-summary").innerText()).match(/Shared gold:\s*(\d+)/)?.[1] || 0,
  );
  const talismanGoldShortfall = Math.max(0, 100 - goldBeforeTalisman);
  if (talismanGoldShortfall > 0) {
    const scrapQuantity = await quantityInSupplyRow("Goblin Scrap", "Stored");
    requireCondition(
      scrapQuantity >= talismanGoldShortfall,
      `browser fixture could not fund the Merchant Talisman purchase: gold=${goldBeforeTalisman}, scrap=${scrapQuantity}`,
    );
    const scrapSaleRow = supplyRow("Goblin Scrap");
    await scrapSaleRow.locator('input[aria-label="Goblin Scrap sale quantity"]')
      .fill(String(talismanGoldShortfall));
    await updateSupply("Goblin Scrap", "Sell");
  }
  await updateSupply("Return Talisman", "Buy");
  requireCondition(
    await quantityInSupplyRow("Return Talisman", "Stored") === 1 &&
      await quantityInSupplyRow("Return Talisman", "Stock") === 0,
    "Merchant Talisman purchase did not consume its single finite stock unit",
  );
  await clickVisibleOption(page, "#hub-economy-options", "Back");
  await page.locator("#hub-economy-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#vendors-options", "Back");
  await page.locator("#vendors-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#overworld-options", "Hub Inventory");
  await page.locator("#hub-economy-panel").waitFor({ state: "visible" });
  requireCondition(
    await quantityInSupplyRow("Healing Potion", "Stored") === 1 &&
      await quantityInSupplyRow("Smoke Bomb", "Stored") === 2 &&
      await quantityInSupplyRow("Return Talisman", "Stored") === 1,
    "Hub purchase and Alchemy did not create the expected secured supply quantities",
  );
  await updateSupply("Healing Potion", "Load");
  await updateSupply("Smoke Bomb", "Load");
  await updateSupply("Smoke Bomb", "Load");
  await updateSupply("Return Talisman", "Load");
  requireCondition(
    (await page.locator("#merchant-storage-summary").innerText()).includes("Carried supplies: 4/6") &&
      await quantityInSupplyRow("Healing Potion", "Stored") === 0 &&
      await quantityInSupplyRow("Smoke Bomb", "Stored") === 0 &&
      await quantityInSupplyRow("Return Talisman", "Stored") === 0,
    "loading supplies did not transfer four units out of Hub storage into the pack",
  );
  await clickVisibleOption(page, "#hub-economy-options", "Back");
  await page.locator("#hub-economy-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#overworld-options", "Options");
  await page.waitForFunction(() =>
    [...document.querySelectorAll("#overworld-options button")].some((button) =>
      (button.querySelector(".choice-label")?.textContent ?? button.textContent).trim() === "Save" &&
      !button.disabled,
    ),
  );
  await clickVisibleOption(page, "#overworld-options", "Save");
  await page.locator("#notice").filter({ hasText: "Game saved." }).waitFor({ state: "visible" });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, { timeout: 120000 });
  await continueSavedGameAfterReload(page);
  await clickVisibleOption(page, "#overworld-options", "Items");
  await page.locator("#items-panel").waitFor({ state: "visible" });
  await page.waitForFunction(() => {
    const text = document.getElementById("items-list").innerText;
    return text.includes("Healing Potion x1 | Carried Pack") &&
      text.includes("Smoke Bomb x2 | Carried Pack") &&
      text.includes("Return Talisman x1 | Carried Pack");
  });
  const carriedItemsText = await page.locator("#items-list").innerText();
  requireCondition(
    carriedItemsText.includes("Healing Potion x1 | Carried Pack") &&
      carriedItemsText.includes("Smoke Bomb x2 | Carried Pack") &&
      carriedItemsText.includes("Return Talisman x1 | Carried Pack"),
    `browser save/reload did not preserve carried supplies separately: ${carriedItemsText}`,
  );
  await clickVisibleOption(page, "#items-options", "Back");
  await page.locator("#items-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#overworld-options", "Vendors");
  await clickVisibleOption(page, "#vendors-options", "Alchemist");
  await page.locator("#alchemy-progress").filter({ hasText: "Alchemy Level 1 | 30 XP" }).waitFor({ state: "visible" });
  await clickVisibleOption(page, "#hub-economy-options", "Back");
  await page.locator("#hub-economy-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#vendors-options", "Back");
  await page.locator("#vendors-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#overworld-options", "Items");
  await page.locator("#items-panel").waitFor({ state: "visible" });
  console.log("M2_BROWSER|PREP_ALCHEMY_PACK_SAVE_RELOAD|PASS");

  const hubScrapBeforeRun = Number(
    carriedItemsText.match(/Goblin Scrap x(\d+) \| Hub Storage/)?.[1] || 0,
  );
  await clickVisibleOption(page, "#items-options", "Back");
  await page.locator("#items-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#overworld-options", "Character");
  await page.locator("#character-panel").waitFor({ state: "visible" });
  const characterProgress = async (label) => {
    await clickVisibleOption(page, "#character-targets", label);
    return {
      level: Number((await page.locator("#character-level").innerText()).match(/\d+/)?.[0] || 0),
      experience: Number((await page.locator("#experience-value").innerText()).match(/^\s*(\d+)/)?.[1] || 0),
    };
  };
  const drifterLabels = [
    "Ser Branoc, the Unbroken Crest",
    "Azhvielle, the Unconfessed",
  ];
  const xpBeforeTalismanRun = {};
  for (const label of drifterLabels) xpBeforeTalismanRun[label] = await characterProgress(label);
  await clickVisibleOption(page, "#character-options", "Back");
  await page.locator("#character-panel").waitFor({ state: "hidden" });

  const hubGoldBeforeTalismanRun = await page.locator("#hub-shared-gold").innerText();
  await clickVisibleOption(page, "#overworld-options", "Start Floor 1");
  await page.waitForFunction(() => document.getElementById("screen-badge").textContent.trim() === "FLOOR_ONE_WARNING");
  await clickVisibleOption(page, "#overworld-options", "Set Out");
  await page.locator("#party-panel").waitFor({ state: "visible" });

  const clickFirstBattleChoice = async (selector) => {
    const clicked = await page.evaluate((choiceSelector) => {
      const button = document.querySelector(`${choiceSelector}:not([disabled])`);
      if (!button) return false;
      window.__DD_LAST_BATTLE_CHOICE__ = button;
      button.click();
      return true;
    }, selector);
    requireCondition(clicked, `no enabled battle choice matched ${selector}`);
    await page.waitForFunction(() => !window.__DD_LAST_BATTLE_CHOICE__?.isConnected);
    await observeMomentum(page);
  };
  const resolveAttackChoice = async () => {
    await page.waitForFunction(() =>
      document.querySelector("#moves .move-choice:not([disabled])") !== null ||
        document.querySelector("#targets .target-choice:not([disabled])") !== null,
    null, { timeout: 10000 }).catch(async (error) => {
      const state = await page.evaluate(() => ({
        phase: document.getElementById("app").dataset.interactionPhase,
        actions: [...document.querySelectorAll("#actions button")].map((button) => button.textContent.trim()),
        moves: [...document.querySelectorAll("#moves button")].map((button) => button.textContent.trim()),
        log: document.getElementById("battle-log").innerText,
      }));
      throw new Error(`Attack did not render a move or target choice: ${JSON.stringify(state)}; ${error.message}`);
    });
    if (await page.locator("#targets .target-choice:not([disabled])").count()) return;
    await clickFirstBattleChoice("#moves .move-choice");
    if (await page.locator("#app").getAttribute("data-interaction-phase") === "targets") {
      await clickFirstBattleChoice("#targets .target-choice");
    }
  };
  const attackOnce = async () => {
    await clickVisibleOption(page, "#actions", "Attack");
    await resolveAttackChoice();
  };
  let advancementMoveDamage = 0;
  const useAzhvielleAdvancementMove = async () => {
    await clickVisibleOption(page, "#actions", "Attack");
    const move = page.locator("#moves .move-choice").filter({ hasText: "Witchlight Bolt" }).first();
    await move.waitFor({ state: "visible" });
    await move.click();
    await page.locator("#targets .target-choice:not([disabled])").first()
      .waitFor({ state: "visible" });
    await clickFirstBattleChoice("#targets .target-choice");
    await page.waitForFunction(() =>
      document.getElementById("battle-log").innerText.includes("Witchlight Bolt"),
    );
    const log = await page.locator("#battle-log").innerText();
    const damageMatch = log.match(/Witchlight Bolt[^\n]*It dealt (\d+) damage/i);
    if (damageMatch) advancementMoveDamage = Number(damageMatch[1]);
  };
  for (let action = 0; action < 60 && await page.locator("#overworld-screen").isHidden(); action += 1) {
    const phase = await page.locator("#app").getAttribute("data-interaction-phase");
    if (phase === "actions") {
      const activeDrifterId = await page.locator(
        "#party-members .party-member.is-active",
      ).getAttribute("data-target-id");
      if (activeDrifterId === "drifter_azhvielle" && advancementMoveDamage === 0) {
        await useAzhvielleAdvancementMove();
      } else {
        await attackOnce();
      }
    } else if (phase === "regular_moves") {
      await resolveAttackChoice();
    } else if (phase === "targets") {
      await clickFirstBattleChoice("#targets .target-choice");
    } else {
      throw new Error(`unexpected browser battle phase while clearing one encounter: ${phase}`);
    }
  }
  await page.locator("#overworld-screen").waitFor({ state: "visible" });
  requireCondition(
    advancementMoveDamage > 0,
    "Azhvielle's purchased Witchlight Bolt did not deal damage in the browser battle",
  );
  console.log("M3_BROWSER|ADVANCEMENT_MOVE_USED|PASS");
  const firstEncounterRewards = await page.locator("#adventure-text").innerText();
  requireCondition(
    firstEncounterRewards.includes("Unsecured rewards:") && firstEncounterRewards.includes("Items: 4 Goblin Scrap"),
    `Floor 1 did not display the unsecured item drop: ${firstEncounterRewards}`,
  );
  const smokeNode = await page.locator("#location-label").innerText();
  requireCondition(smokeNode === "Goblin Patrol", `expected the next encounter after the first clear, got ${smokeNode}`);

  const partyStatus = () => page.locator("#party-members .party-member").evaluateAll((members) =>
    members.map((member) => `${member.dataset.targetId}|${member.querySelector(".party-member-status").textContent.trim()}`),
  );
  const enemyStatus = () => page.locator("#enemy-panel .enemy").evaluateAll((enemies) =>
    enemies.map((enemy) => enemy.textContent.trim()),
  );
  const enemyHealthTotal = () => page.locator("#enemy-panel .enemy").evaluateAll((enemies) =>
    enemies.reduce((total, enemy) => {
      const match = enemy.textContent.match(/HP\s+(\d+)\s*\/\s*\d+/i);
      if (!match) throw new Error(`enemy health is not rendered: ${enemy.textContent}`);
      return total + Number(match[1]);
    }, 0),
  );
  await clickVisibleOption(page, "#route-actions", "Enter Encounter");
  await page.locator("#party-panel").waitFor({ state: "visible" });
  const freshEnemyStatus = await enemyStatus();
  requireCondition(freshEnemyStatus.length === 3, `Goblin Patrol did not create three fresh enemies: ${JSON.stringify(freshEnemyStatus)}`);
  const freshEnemyHealth = await enemyHealthTotal();
  let damagedEnemyHealth = freshEnemyHealth;
  for (let attempt = 0; attempt < 12 && damagedEnemyHealth >= freshEnemyHealth; attempt += 1) {
    const phase = await page.locator("#app").getAttribute("data-interaction-phase");
    if (phase === "actions") {
      await attackOnce();
    } else if (phase === "regular_moves") {
      await resolveAttackChoice();
    } else if (phase === "targets") {
      await clickFirstBattleChoice("#targets .target-choice");
    } else {
      throw new Error(`unexpected browser battle phase while preparing smoke retry proof: ${phase}`);
    }
    damagedEnemyHealth = await enemyHealthTotal();
  }
  requireCondition(
    damagedEnemyHealth < freshEnemyHealth,
    `bounded attacks did not damage Goblin Patrol before smoke escape: ${freshEnemyHealth} -> ${damagedEnemyHealth}`,
  );
  const partyBeforeSmoke = await partyStatus();
  const damagedEnemyStatus = await enemyStatus();
  await clickVisibleOption(page, "#actions", "Smoke Bomb");
  await page.locator("#overworld-screen").waitFor({ state: "visible" });
  requireCondition(
    await page.locator("#location-label").innerText() === smokeNode &&
      (await page.locator("#adventure-text").innerText()).includes("No rewards are earned") &&
      JSON.stringify(await partyStatus()) === JSON.stringify(partyBeforeSmoke) &&
      await page.getByRole("button", { name: "Enter Encounter" }).isVisible(),
    "Smoke Bomb changed party resources, awarded rewards, advanced the route, or hid the retry",
  );
  await clickVisibleOption(page, "#route-actions", "Enter Encounter");
  await page.locator("#party-panel").waitFor({ state: "visible" });
  const retriedEnemyHealth = await enemyHealthTotal();
  const retriedEnemyStatus = await enemyStatus();
  requireCondition(
    JSON.stringify(retriedEnemyStatus) === JSON.stringify(freshEnemyStatus) &&
      retriedEnemyHealth === freshEnemyHealth &&
      retriedEnemyHealth > damagedEnemyHealth &&
      JSON.stringify(retriedEnemyStatus) !== JSON.stringify(damagedEnemyStatus),
    "retry did not recreate the same encounter with fresh enemy health",
  );
  console.log("M2_BROWSER|SMOKE_ESCAPE_PRESERVES_AND_RETRIES|PASS");
  await clickVisibleOption(page, "#actions", "Smoke Bomb");
  await page.locator("#overworld-screen").waitFor({ state: "visible" });
  requireCondition(
    await page.locator("#location-label").innerText() === smokeNode &&
      await page.getByRole("button", { name: "Use Return Talisman" }).isVisible(),
    "the second smoke escape did not leave the same node and allow the separate talisman exit",
  );
  await clickVisibleOption(page, "#overworld-options", "Use Return Talisman");
  await page.locator("#screen-badge").filter({ hasText: "HUB" }).waitFor({ state: "visible" });
  const talismanNotice = await page.locator("#adventure-text").innerText();
  requireCondition(
    talismanNotice.includes("Adjusted XP is secured") &&
      talismanNotice.includes("run gold and items are lost") &&
      (await page.locator("#hub-shared-gold").innerText()) === hubGoldBeforeTalismanRun,
    `Return Talisman banked the wrong rewards: ${JSON.stringify({ talismanNotice, gold: await page.locator("#hub-shared-gold").innerText() })}`,
  );
  await clickVisibleOption(page, "#overworld-options", "Character");
  await page.locator("#character-panel").waitFor({ state: "visible" });
  for (const label of drifterLabels) {
    const after = await characterProgress(label);
    const before = xpBeforeTalismanRun[label];
    requireCondition(
      after.level > before.level || (after.level === before.level && after.experience > before.experience),
      `Return Talisman did not secure earned XP for ${label}: ${JSON.stringify({ before, after })}`,
    );
  }
  await clickVisibleOption(page, "#character-options", "Back");
  await page.locator("#character-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#overworld-options", "Items");
  await page.locator("#items-panel").waitFor({ state: "visible" });
  const returnedItems = await page.locator("#items-list").innerText();
  requireCondition(
    returnedItems.includes("Healing Potion x1 | Hub Storage") &&
      !returnedItems.includes("Smoke Bomb x") &&
      !returnedItems.includes("Return Talisman x") &&
      Number(returnedItems.match(/Goblin Scrap x(\d+) \| Hub Storage/)?.[1] || 0) === hubScrapBeforeRun,
    `Return Talisman returned consumed or unsecured items: ${returnedItems}`,
  );
  console.log("M2_BROWSER|TALISMAN_XP_ONLY|PASS");

  await clickVisibleOption(page, "#items-options", "Back");
  await page.locator("#items-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#overworld-options", "Character");
  await page.locator("#character-panel").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#character-options", "Skills");
  await page.locator("#skills-panel").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#skills-targets", "Azhvielle, the Unconfessed");
  const preRespecGrowth = await page.locator("#growth-summary").innerText();
  const baseAzhvielleStrength = "5";
  await clickVisibleOption(page, "#skills-options", "Respec");
  await page.locator("#respec-panel").waitFor({ state: "visible" });
  requireCondition(
    (await page.locator("#respec-target").innerText()) === "Azhvielle, the Unconfessed" &&
      (await page.locator("#respec-cost").innerText()).includes("no Revision Parchment") &&
      (await page.locator("#respec-skills").innerText()).includes("azhvielle_p01") &&
      (await page.locator("#respec-skills").innerText()).includes("azhvielle_a01") &&
      (await page.locator("#respec-stat-points").innerText()).includes("strength"),
    "Azhvielle's first-respec preview omitted its cost or the purchases to be removed",
  );
  await clickVisibleOption(page, "#respec-options", "Confirm");
  await page.locator("#skills-panel").waitFor({ state: "visible" });
  const strengthAfterRespec = page.locator("#skill-stats .skill-stat")
    .filter({ hasText: "Strength" });
  await page.waitForFunction(() => {
    const row = [...document.querySelectorAll("#skill-stats .skill-stat")]
      .find((candidate) => candidate.querySelector(".skill-label")?.textContent === "Strength");
    return row?.querySelector(".skill-value")?.textContent === "5";
  });
  const growthAfterRespec = await page.locator("#growth-summary").innerText();
  requireCondition(
    (await strengthAfterRespec.locator(".skill-value").innerText()) === baseAzhvielleStrength &&
      growthAfterRespec !== preRespecGrowth &&
      !(await page.locator('#skill-advancement [data-skill-id="azhvielle_p01"]')
        .innerText()).includes("Purchased") &&
      !(await page.locator('#skill-advancement [data-skill-id="azhvielle_a01"]')
        .innerText()).includes("Purchased"),
    "confirmed respec did not remove the selected Drifter's tracked upgrades",
  );
  await clickVisibleOption(page, "#skills-options", "Back");
  await page.locator("#character-panel").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#character-options", "Weapon");
  await page.locator("#weapon-panel").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#weapon-targets", "Ser Branoc, the Unbroken Crest");
  await page.locator("#weapon-targets button[aria-pressed='true']")
    .filter({ hasText: "Ser Branoc, the Unbroken Crest" }).waitFor();
  const weaponAfterAzhvielleRespec = await page.locator(
    "#weapon-components .weapon-component-slot",
  ).first().innerText();
  requireCondition(
    weaponAfterAzhvielleRespec === installedBladeState,
    `Azhvielle's respec changed Branoc's independent signature weapon progression: ${JSON.stringify({ installedBladeState, weaponAfterAzhvielleRespec })}`,
  );
  await clickVisibleOption(page, "#weapon-options", "Back");
  await page.locator("#character-panel").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#character-options", "Back");
  await page.locator("#character-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#overworld-options", "Options");
  await page.waitForFunction(
    () => document.getElementById("screen-badge").textContent.trim() === "OPTIONS",
  );
  await clickVisibleOption(page, "#overworld-options", "Save");
  await page.locator("#notice").filter({ hasText: "Game saved." }).waitFor({ state: "visible" });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(page);
  await clickVisibleOption(page, "#overworld-options", "Character");
  await page.locator("#character-panel").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#character-options", "Skills");
  await page.locator("#skills-panel").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#skills-targets", "Azhvielle, the Unconfessed");
  await page.locator("#skills-targets button[aria-pressed='true']")
    .filter({ hasText: "Azhvielle, the Unconfessed" }).waitFor();
  const restoredRespecGrowth = await page.locator("#growth-summary").innerText();
  const restoredRespecStrength = await page.locator("#skill-stats .skill-stat")
    .filter({ hasText: "Strength" }).locator(".skill-value").innerText();
  const restoredPassiveState = await page.locator(
    '#skill-advancement [data-skill-id="azhvielle_p01"]',
  ).innerText();
  const restoredActiveState = await page.locator(
    '#skill-advancement [data-skill-id="azhvielle_a01"]',
  ).innerText();
  requireCondition(
    restoredRespecGrowth === growthAfterRespec &&
      restoredRespecStrength === baseAzhvielleStrength &&
      !restoredPassiveState.includes("Purchased") &&
      !restoredActiveState.includes("Purchased"),
    `browser save/reload changed or repeated Azhvielle's confirmed respec: ${JSON.stringify({ growthAfterRespec, restoredRespecGrowth, restoredRespecStrength, restoredPassiveState, restoredActiveState })}`,
  );
  console.log("M3_BROWSER|RESPEC_SAVE_RELOAD|PASS");

  const readFloorTwoDiscoveryBonuses = async () => page.evaluate((key) => {
    const payload = JSON.parse(localStorage.getItem(key)).payload;
    const members = [payload.player, ...payload.party.companions];
    const drifterIdByChoice = {
      "1": "branoc",
      "2": "azhvielle",
      "3": "zhaivra",
      "4": "joruun",
    };
    return Object.fromEntries(members.map((member) => [
      drifterIdByChoice[member.identity.profile.choice],
      member.permanent_discovery_bonuses,
    ]));
  }, floorTwoProfileKey);
  await page.evaluate(({ key, envelope }) => localStorage.setItem(key, envelope), {
    key: floorTwoProfileKey,
    envelope: floorTwoProfileEnvelope,
  });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(page);
  requireCondition(
    await page.locator("#screen-badge").innerText() === "HUB" &&
      await page.locator("#location-label").innerText() === "Floor 1 Hub" &&
      await page.locator("#hub-shared-gold").innerText() === "Shared gold: 64",
    "the Floor II browser fixture did not load as an insufficient-gold cleared-Hub save",
  );
  await clickVisibleOption(page, "#overworld-options", "Character");
  await page.locator("#character-panel").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#character-targets", "Azhvielle, the Unconfessed");
  const azhvielleHpAtHub = Number(
    (await page.locator("#character-progression").innerText()).match(/HP\s+\d+\/(\d+)/)?.[1] || 0,
  );
  requireCondition(azhvielleHpAtHub > 0, "the qualifying save omitted Azhvielle's starting HP maximum");
  await clickVisibleOption(page, "#character-options", "Back");
  await clickVisibleOption(page, "#overworld-options", "Items");
  await page.locator("#items-panel").waitFor({ state: "visible" });
  const floorTwoPackText = await page.locator("#items-list").innerText();
  requireCondition(
    floorTwoPackText.includes("Healing Potion x6 | Carried Pack"),
    `the Floor II qualifying save did not load its six carried potions: ${floorTwoPackText}`,
  );
  await clickVisibleOption(page, "#items-options", "Back");
  await page.locator("#items-panel").waitFor({ state: "hidden" });
  console.log("M4_BROWSER|LOAD_QUALIFYING_SAVE|PASS");

  const floorTwoPotionUses = [];
  let floorFourHealingPotionUsesBeforeRest = 0;
  let floorFourManaPotionUsesBeforeRest = 0;
  const floorTwoBattleLogs = new Map();
  const readFloorTwoActivePartyResources = async () => {
    await clickVisibleOption(page, "#overworld-options", "Character");
    await page.locator("#character-panel").waitFor({ state: "visible" });
    const resources = {};
    for (const [drifterId, label] of [
      ["branoc", "Ser Branoc, the Unbroken Crest"],
      ["azhvielle", "Azhvielle, the Unconfessed"],
    ]) {
      await clickVisibleOption(page, "#character-targets", label);
      await page.locator("#character-targets button[aria-pressed='true']")
        .filter({ hasText: label }).waitFor({ state: "visible" });
      const text = await page.locator("#character-resources").innerText();
      resources[drifterId] = Object.fromEntries(
        [...text.matchAll(/(HP|Mana|Super)\s+(\d+)\/(\d+)/g)]
          .map((match) => [match[1].toLowerCase(), [Number(match[2]), Number(match[3])]]),
      );
    }
    await clickVisibleOption(page, "#character-options", "Back");
    await page.locator("#character-panel").waitFor({ state: "hidden" });
    await page.locator("#screen-badge").filter({ hasText: "REST" }).waitFor({ state: "visible" });
    return resources;
  };
  const verifyFloorTwoRestRecovery = (before, after, restLabel) => {
    for (const drifterId of ["branoc", "azhvielle"]) {
      for (const resource of ["hp", "mana"]) {
        requireCondition(
          after[drifterId][resource][0] === after[drifterId][resource][1],
          `${restLabel} did not fully restore ${drifterId} ${resource}: ${JSON.stringify(after[drifterId])}`,
        );
      }
      requireCondition(
        after[drifterId].super[0] === before[drifterId].super[0],
        `${restLabel} changed ${drifterId} Super: ${JSON.stringify({ before: before[drifterId], after: after[drifterId] })}`,
      );
    }
  };
  const clearFloorBattle = async (
    battleNumber,
    {
      floorLabel = "Floor II",
      bossParty = ["drifter_branoc", "drifter_azhvielle", "drifter_joruun"],
    } = {},
  ) => {
    await observeMomentum(page);
    const deployedIds = await page.locator("#party-members .party-member").evaluateAll(
      (members) => members.map((member) => member.dataset.targetId),
    );
    const expectedParty = battleNumber === 10
      ? bossParty
      : ["drifter_branoc", "drifter_azhvielle"];
    requireCondition(
      JSON.stringify(deployedIds) === JSON.stringify(expectedParty),
      `${floorLabel} Battle ${battleNumber} deployed ${JSON.stringify(deployedIds)} instead of ${JSON.stringify(expectedParty)}`,
    );
    const observedBattleLog = new Set();
    const captureBattleLog = async () => {
      const log = await page.locator("#battle-log").innerText();
      for (const line of log.split("\n").map((entry) => entry.trim()).filter(Boolean)) {
        observedBattleLog.add(line);
      }
      return [...observedBattleLog].join("\n");
    };
    const defendAndWait = async () => {
      const button = page.locator("#actions button").filter({ hasText: "Defend" }).first();
      await button.evaluate((node) => { window.__DD_FLOOR_TWO_DEFEND_BUTTON__ = node; });
      await button.click();
      await page.waitForFunction(() => {
        const button = window.__DD_FLOOR_TWO_DEFEND_BUTTON__;
        const battle = document.getElementById("battle-screen");
        const overworld = document.getElementById("overworld-screen");
        return !button || !button.isConnected || !battle || battle.hidden ||
          (overworld && !overworld.hidden);
      });
      await captureBattleLog();
    };
    const chooseFloorTwoEnemy = async () => {
      const targets = page.locator("#targets .target-choice:not([disabled])");
      const labels = await targets.allInnerTexts();
      const priority = (label) => {
        if (floorLabel === "Floor IV") {
          if (/Brine Oracle/i.test(label)) return 0;
          if (/Drowned Stalker/i.test(label)) return 1;
          if (/Ashbound Hound/i.test(label)) return 2;
          if (/Reliquary Sentinel/i.test(label)) return 3;
          if (/Tidebound Curator/i.test(label)) return 4;
        }
        if (/\bGoblin\b/i.test(label) && !/\b(Lord|Warrior|Shaman)\b/i.test(label)) return 0;
        if (/\bGoblin Warrior\b/i.test(label)) return 1;
        if (/\bGoblin Shaman\b/i.test(label)) return 2;
        if (/\bGoblin Lord\b/i.test(label)) return 3;
        return 10;
      };
      const targetIndex = labels
        .map((label, index) => ({ label, index, priority: priority(label) }))
        .sort((first, second) => first.priority - second.priority)[0]?.index ?? -1;
      requireCondition(targetIndex >= 0, `${floorLabel} attack had no enabled target`);
      const target = targets.nth(targetIndex);
      await target.evaluate((node) => { window.__DD_FLOOR_TWO_TARGET_BUTTON__ = node; });
      await target.click();
      await page.waitForFunction(
        () => !window.__DD_FLOOR_TWO_TARGET_BUTTON__?.isConnected,
      );
      await observeMomentum(page);
    };
    const resolveFloorTwoAttackChoice = async () => {
      try {
        await page.waitForFunction(() =>
          document.querySelector("#moves .move-choice:not([disabled])") !== null ||
            document.querySelector("#targets .target-choice:not([disabled])") !== null,
        );
      } catch (error) {
        const state = await page.evaluate(() => ({
          badge: document.getElementById("screen-badge")?.textContent.trim(),
          phase: document.getElementById("app")?.dataset.interactionPhase,
          party: [...document.querySelectorAll("#party-members .party-member")].map((member) => ({
            name: member.querySelector("h3")?.textContent.trim(),
            status: member.querySelector(".party-member-status")?.textContent.trim(),
          })),
          enemies: [...document.querySelectorAll("#enemy-panel .enemy")].map((enemy) => enemy.innerText.trim()),
          actions: [...document.querySelectorAll("#actions button")].map((button) => ({
            label: button.textContent.trim(),
            disabled: button.disabled,
          })),
          moves: [...document.querySelectorAll("#moves .move-choice")].map((button) => ({
            label: button.textContent.trim(),
            disabled: button.disabled,
          })),
          targets: [...document.querySelectorAll("#targets .target-choice")].map((button) => ({
            label: button.textContent.trim(),
            disabled: button.disabled,
          })),
          battleLog: document.getElementById("battle-log")?.innerText,
        }));
        throw new Error(
          `No enabled attack choice for ${floorLabel} Battle ${battleNumber}: ${JSON.stringify(state)}; ${error.message}`,
        );
      }
      if (await page.locator("#targets .target-choice:not([disabled])").count()) {
        await chooseFloorTwoEnemy();
        return;
      }
      const activeActor = await page.locator("#party-members .party-member.is-active h3").innerText();
      const preferredMoves = /Branoc/i.test(activeActor)
        ? ["Ironwake Dismemberment", "Crestgrave Reaping", "Cinderlung Vesper"]
        : /Azhvielle/i.test(activeActor)
          ? ["Gloamweight Sepulcher", "Mournglass Bloom", "Scepter Sweep"]
          : [];
      const enabledMoves = page.locator("#moves .move-choice:not([disabled])");
      const moveLabels = await enabledMoves.allInnerTexts();
      const preferredMove = preferredMoves.find((name) =>
        moveLabels.some((label) => label.includes(name)),
      );
      if (preferredMove) {
        const button = enabledMoves.filter({ hasText: preferredMove }).first();
        await button.evaluate((node) => { window.__DD_LAST_BATTLE_CHOICE__ = node; });
        await button.click();
        try {
          await page.waitForFunction(() => !window.__DD_LAST_BATTLE_CHOICE__?.isConnected);
        } catch (error) {
          const state = await page.evaluate(() => ({
            badge: document.getElementById("screen-badge")?.textContent.trim(),
            phase: document.getElementById("app")?.dataset.interactionPhase,
            errorVisible: !document.getElementById("error")?.hidden,
            errorMessage: document.getElementById("error-message")?.textContent.trim(),
            notice: document.getElementById("notice")?.textContent.trim(),
            actor: document.querySelector("#party-members .party-member.is-active h3")?.textContent.trim(),
            actions: [...document.querySelectorAll("#actions button")].map((item) => ({
              label: item.textContent.trim(),
              disabled: item.disabled,
            })),
            moves: [...document.querySelectorAll("#moves .move-choice")].map((item) => ({
              label: item.textContent.trim(),
              disabled: item.disabled,
            })),
            targets: [...document.querySelectorAll("#targets .target-choice")].map((item) => ({
              label: item.textContent.trim(),
              disabled: item.disabled,
            })),
            battleLog: document.getElementById("battle-log")?.innerText,
          }));
          throw new Error(
            `Selected ${preferredMove} did not advance ${floorLabel} Battle ${battleNumber}: ${JSON.stringify(state)}; ${error.message}`,
          );
        }
      } else {
        await clickFirstBattleChoice("#moves .move-choice");
      }
      if (await page.locator("#app").getAttribute("data-interaction-phase") === "targets") {
        await chooseFloorTwoEnemy();
      }
    };
    const attackWithFloorTwoTargeting = async () => {
      await clickVisibleOption(page, "#actions", "Attack");
      await resolveFloorTwoAttackChoice();
    };

    for (let action = 0; action < 120 && await page.locator("#overworld-screen").isHidden(); action += 1) {
      await captureBattleLog();
      const phase = await page.locator("#app").getAttribute("data-interaction-phase");
      if (phase === "actions") {
        const caveInResolved = [...observedBattleLog].some((line) => line.includes("Falling stone struck"));
        if (floorLabel === "Floor II" && battleNumber === 5 && !caveInResolved) {
          await defendAndWait();
          continue;
        }
        const lowestPartyHealth = await page.locator(
          "#party-members .party-member-status",
        ).evaluateAll((statuses) => Math.min(...statuses.map((status) => {
          const match = status.textContent.match(/HP\s+(\d+)\/(\d+)/);
          return match ? Number(match[1]) / Number(match[2]) : 1;
        })));
        const activePartyHealth = await page.locator(
          "#party-members .party-member.is-active .party-member-status",
        ).evaluate((status) => {
          const match = status.textContent.match(/HP\s+(\d+)\/(\d+)/);
          return match ? Number(match[1]) / Number(match[2]) : 1;
        });
        const potion = page.locator("#actions button").filter({ hasText: "Healing Potion" });
        const potionOffered = await potion.count() > 0;
        const floorFourFirstHalf = floorLabel === "Floor IV" && battleNumber <= 5;
        const healingAllowed = !floorFourFirstHalf || floorFourHealingPotionUsesBeforeRest < 3;
        // The midpoint Rest restores HP, so reserve carried healing for later encounters.
        const healingThreshold = floorLabel === "Floor IV"
          ? (floorFourFirstHalf ? 0.35 : 0.5)
          : 0.5;
        if (
          lowestPartyHealth <= healingThreshold && healingAllowed &&
          potionOffered && await potion.isEnabled()
        ) {
          const healthBeforePotion = await page.locator(
            "#party-members .party-member-status",
          ).allInnerTexts();
          await clickVisibleOption(page, "#actions", "Healing Potion");
          await page.waitForFunction(
            () => document.getElementById("app").dataset.interactionPhase === "healing_targets",
          );
          const targetIndex = await page.locator("#targets .target-choice:not([disabled])")
            .evaluateAll((targets) => targets
              .map((target, index) => {
                const match = target.textContent.match(/HP\s+(\d+)\/(\d+)/);
                return { index, ratio: match ? Number(match[1]) / Number(match[2]) : 1 };
              })
              .sort((first, second) => first.ratio - second.ratio)[0]?.index ?? -1);
          requireCondition(targetIndex >= 0, `Healing Potion had no eligible ${floorLabel} target`);
          await page.locator("#targets .target-choice:not([disabled])").nth(targetIndex).click();
          await page.waitForFunction(
            () => document.getElementById("app").dataset.interactionPhase === "actions",
          );
          await captureBattleLog();
          floorTwoPotionUses.push({
            floorLabel,
            battleNumber,
            before: healthBeforePotion,
            after: await page.locator("#party-members .party-member-status").allInnerTexts(),
          });
          if (floorFourFirstHalf) floorFourHealingPotionUsesBeforeRest += 1;
        } else {
          const lowestPartyMana = await page.locator(
            "#party-members .party-member-status",
          ).evaluateAll((statuses) => Math.min(...statuses.map((status) => {
            const match = status.textContent.match(/Mana\s+(\d+)\/(\d+)/);
            return match ? Number(match[1]) / Number(match[2]) : 1;
          })));
          const manaPotion = page.locator("#actions button").filter({ hasText: "Mana Potion" });
          const manaThreshold = floorLabel === "Floor IV" ? 0.35 : 0.2;
          const manaAllowed =
            floorLabel !== "Floor IV" || battleNumber > 5 ||
            floorFourManaPotionUsesBeforeRest < 1;
          if (
            lowestPartyMana <= manaThreshold && manaAllowed &&
            await manaPotion.count() > 0 &&
            await manaPotion.isEnabled()
          ) {
            await clickVisibleOption(page, "#actions", "Mana Potion");
            await page.waitForFunction(
              () => document.getElementById("app").dataset.interactionPhase === "healing_targets",
            );
            const targetIndex = await page.locator("#targets .target-choice:not([disabled])")
              .evaluateAll((targets) => targets
                .map((target, index) => {
                  const match = target.textContent.match(/Mana\s+(\d+)\/(\d+)/);
                  return {
                    index,
                    ratio: match ? Number(match[1]) / Number(match[2]) : 1,
                  };
                })
                .sort((first, second) => first.ratio - second.ratio)[0]?.index ?? -1);
            requireCondition(targetIndex >= 0, `${floorLabel} Mana Potion had no eligible target`);
            await page.locator("#targets .target-choice:not([disabled])").nth(targetIndex).click();
            await page.waitForFunction(
              () => document.getElementById("app").dataset.interactionPhase === "actions",
            );
            await captureBattleLog();
            if (floorLabel === "Floor IV" && battleNumber <= 5) {
              floorFourManaPotionUsesBeforeRest += 1;
            }
          } else {
            const superAction = page.locator("#actions button").filter({ hasText: /^Super$/ });
            if (await superAction.count() && await superAction.isEnabled()) {
              await clickVisibleOption(page, "#actions", "Super");
              await resolveFloorTwoAttackChoice();
            } else if (activePartyHealth <= (floorLabel === "Floor IV" ? 0.5 : 0.35)) {
              await defendAndWait();
            } else {
              await attackWithFloorTwoTargeting();
            }
            await captureBattleLog();
          }
        }
      } else if (phase === "regular_moves") {
        await resolveFloorTwoAttackChoice();
        await captureBattleLog();
      } else if (phase === "targets") {
        await chooseFloorTwoEnemy();
        await captureBattleLog();
      } else {
        const screenState = await page.evaluate(() => ({
          badge: document.getElementById("screen-badge")?.textContent.trim(),
          adventure: document.getElementById("adventure-text")?.textContent.trim(),
          notice: document.getElementById("notice")?.textContent.trim(),
          selectionHidden: document.getElementById("selection-screen")?.hidden,
          overworldHidden: document.getElementById("overworld-screen")?.hidden,
          battleHidden: document.getElementById("battle-screen")?.hidden,
          routeActions: [...document.querySelectorAll("#route-actions button")]
            .map((button) => button.textContent.trim()),
          party: [...document.querySelectorAll("#party-members .party-member")]
            .map((member) => member.innerText.trim()),
          battleLog: document.getElementById("battle-log")?.innerText,
          actions: [...document.querySelectorAll("#actions button")]
            .map((button) => ({ text: button.textContent.trim(), disabled: button.disabled })),
        }));
        throw new Error(
          `unexpected ${floorLabel} Battle ${battleNumber} phase: ${phase}; state=${JSON.stringify(screenState)}`,
        );
      }
    }
    await page.locator("#overworld-screen").waitFor({ state: "visible", timeout: 10000 }).catch(async (error) => {
      const state = await page.evaluate(() => ({
        badge: document.getElementById("screen-badge")?.textContent.trim(),
        phase: document.getElementById("app")?.dataset.interactionPhase,
        party: [...document.querySelectorAll("#party-members .party-member")].map((member) => ({
          name: member.querySelector("h3")?.textContent.trim(),
          status: member.querySelector(".party-member-status")?.textContent.trim(),
        })),
        enemies: [...document.querySelectorAll("#enemy-panel .enemy")].map((enemy) => enemy.innerText.trim()),
        battleLog: document.getElementById("battle-log")?.innerText,
        actions: [...document.querySelectorAll("#actions button")].map((button) => ({
          label: button.textContent.trim(),
          disabled: button.disabled,
        })),
      }));
      throw new Error(
        `${floorLabel} Battle ${battleNumber} did not finish within the action budget: ${JSON.stringify(state)}; ${error.message}`,
      );
    });
    const outcome = await page.evaluate(({ potionUses, battleLog }) => ({
      badge: document.getElementById("screen-badge").textContent.trim(),
      adventure: document.getElementById("adventure-text").textContent.trim(),
      battleLog,
      potionUses,
      party: [...document.querySelectorAll("#party-members .party-member")].map((member) => ({
        id: member.dataset.targetId,
        status: member.querySelector(".party-member-status")?.textContent.trim(),
      })),
    }), {
      potionUses: floorTwoPotionUses,
      battleLog: [...observedBattleLog].join("\n"),
    });
    const clearMessage = {
      "Floor II": "Floor 2 is cleared",
      "Floor III": "Floor 3 is cleared",
      "Floor IV": "Floor IV is cleared",
    }[floorLabel];
    const bossVictory = battleNumber === 10
      && outcome.badge === "HUB"
      && clearMessage !== undefined
      && outcome.adventure.includes(clearMessage);
    requireCondition(
      outcome.badge !== "DRIFTER SELECTION"
        && (outcome.badge !== "HUB" || bossVictory),
      `${floorLabel} Battle ${battleNumber} did not advance: ${JSON.stringify(outcome)}`,
    );
    floorTwoBattleLogs.set(battleNumber, outcome.battleLog);
  };

  await clickVisibleOption(page, "#overworld-options", "Start Floor 2");
  await page.locator("#party-panel").waitFor({ state: "visible" });
  for (let battleNumber = 1; battleNumber <= 5; battleNumber += 1) {
    if (battleNumber > 1) {
      await clickVisibleOption(page, "#route-actions", "Enter Encounter");
      await page.locator("#party-panel").waitFor({ state: "visible" });
      if (battleNumber === 5) {
        await page.locator("#battle-log").filter({ hasText: "Cave-in is imminent." }).waitFor({ state: "visible" });
      }
    }
    await clearFloorBattle(battleNumber);
    if (battleNumber === 5) {
      await page.locator("#screen-badge").filter({ hasText: "REST" }).waitFor({ state: "visible" });
      const caveInLog = floorTwoBattleLogs.get(5) || "";
      requireCondition(
        caveInLog.toLowerCase().includes("a cave-in is imminent.") &&
          caveInLog.includes("used Defend.") &&
          caveInLog.includes("Falling stone struck"),
        `Floor II's cave-in warning and response were not both recorded: ${caveInLog}`,
      );
    }
  }
  requireCondition(
    !(await page.locator("#overworld-options button").allInnerTexts()).includes("Recruit Companion"),
    "the Floor II Midway Rest exposed permanent recruitment",
  );
  console.log("M4_BROWSER|MIDWAY_NO_PERMANENT_RECRUITMENT|PASS");
  await clickVisibleOption(page, "#overworld-options", "Extract");
  await page.locator("#extraction-rewards").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#overworld-options", "Return to Hub");
  await page.locator("#screen-badge").filter({ hasText: "HUB" }).waitFor({ state: "visible" });
  const returnedGold = Number(
    (await page.locator("#hub-shared-gold").innerText()).match(/\d+/)?.[0] || 0,
  );
  requireCondition(
    returnedGold >= 65,
    `Floor II early extraction did not secure its earned gold: ${returnedGold}`,
  );
  requireCondition(
    !(await page.locator("#overworld-options button").allInnerTexts()).includes("Recruit Companion"),
    "early Floor II extraction exposed permanent recruitment before the floor was cleared",
  );
  console.log("M4_BROWSER|EARLY_EXTRACTION_NO_RECRUITMENT|PASS");

  await clickVisibleOption(page, "#overworld-options", "Hub Inventory");
  await page.locator("#hub-economy-panel").waitFor({ state: "visible" });
  let storedHealingPotions = await quantityInSupplyRow("Healing Potion", "Stored");
  while (storedHealingPotions > 0 && await quantityInSupplyRow("Healing Potion", "Carried") < 6) {
    await updateSupply("Healing Potion", "Load");
    storedHealingPotions = await quantityInSupplyRow("Healing Potion", "Stored");
  }
  requireCondition(
    await quantityInSupplyRow("Healing Potion", "Carried") === 6,
    "the Floor II replay did not reload a full Healing Potion pack from secured Hub storage",
  );
  await clickVisibleOption(page, "#hub-economy-options", "Back");
  await page.locator("#hub-economy-panel").waitFor({ state: "hidden" });

  await clickVisibleOption(page, "#overworld-options", "Start Floor 2");
  await page.locator("#party-panel").waitFor({ state: "visible" });
  for (let battleNumber = 1; battleNumber <= 5; battleNumber += 1) {
    if (battleNumber > 1) {
      await clickVisibleOption(page, "#route-actions", "Enter Encounter");
      await page.locator("#party-panel").waitFor({ state: "visible" });
    }
    await clearFloorBattle(battleNumber);
    if (battleNumber === 5) {
      await page.locator("#screen-badge").filter({ hasText: "REST" }).waitFor({ state: "visible" });
    }
  }
  const midwayResourcesBeforeRecover = await readFloorTwoActivePartyResources();
  await clickVisibleOption(page, "#overworld-options", "Recover");
  await page.waitForFunction(() =>
    document.getElementById("adventure-text").textContent.includes(
      "HP and Mana are fully restored. You may continue or extract.",
    ),
  );
  const midwayResourcesAfterRecover = await readFloorTwoActivePartyResources();
  verifyFloorTwoRestRecovery(
    midwayResourcesBeforeRecover,
    midwayResourcesAfterRecover,
    "Floor II Midway Rest",
  );
  await clickVisibleOption(page, "#route-actions", "Continue Without Rest");
  await page.waitForFunction(() => [...document.querySelectorAll("#route-actions button")].some((button) =>
    (button.querySelector(".choice-label")?.textContent?.trim() || button.textContent.trim()) === "Enter Encounter" &&
      !button.disabled,
  ));
  for (let battleNumber = 6; battleNumber <= 9; battleNumber += 1) {
    await clickVisibleOption(page, "#route-actions", "Enter Encounter");
    await page.locator("#party-panel").waitFor({ state: "visible" });
    await clearFloorBattle(battleNumber);
    if (battleNumber === 9) {
      await page.locator("#screen-badge").filter({ hasText: "REST" }).waitFor({ state: "visible" });
    }
  }

  const preSearchResources = await readFloorTwoActivePartyResources();
  const discoveryBonusesBefore = await readFloorTwoDiscoveryBonuses();
  await clickVisibleOption(page, "#overworld-options", "Search Site");
  await page.locator("#discovery-selection").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#discovery-choices", "Ser Branoc, the Unbroken Crest");
  await page.waitForFunction(() => ["CLAIM DISCOVERY", "REST"].includes(
    document.getElementById("screen-badge").textContent.trim(),
  ));
  const searchBadge = await page.locator("#screen-badge").innerText();
  let wellClaimed = false;
  if (searchBadge === "CLAIM DISCOVERY") {
    await clickVisibleOption(page, "#discovery-choices", "Azhvielle, the Unconfessed");
    await page.locator("#screen-badge").filter({ hasText: "CONFIRM DISCOVERY" }).waitFor({ state: "visible" });
    await clickVisibleOption(page, "#overworld-options", "Confirm");
    await page.locator("#screen-badge").filter({ hasText: "REST" }).waitFor({ state: "visible" });
    requireCondition(
      (await page.locator("#notice").innerText()).includes(
        "Ancient Well claimed by Azhvielle, the Unconfessed",
      ),
      `the Well claim did not confirm Azhvielle as its recipient: ${await page.locator("#notice").innerText()}`,
    );
    wellClaimed = true;
  } else {
    requireCondition(
      searchBadge === "REST" && (await page.locator("#notice").innerText()).length > 0,
      `Floor II search did not produce a persisted result screen: ${searchBadge}`,
    );
  }
  await clickVisibleOption(page, "#overworld-options", "Save");
  await page.locator("#notice").filter({ hasText: "Game saved." }).waitFor({ state: "visible" });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(page);
  requireCondition(
    await page.locator("#screen-badge").innerText() === "REST" &&
      await page.locator("#location-label").innerText() === "Pre-Boss Rest" &&
      !(await page.locator("#overworld-options button").allInnerTexts()).includes("Search Site") &&
      !(await page.locator("#overworld-options button").allInnerTexts()).includes("Claim Discovery"),
    "Floor II reload lost the pre-boss search outcome or re-offered its one-time search/claim",
  );
  if (wellClaimed) {
    await clickVisibleOption(page, "#overworld-options", "Character");
    await page.locator("#character-panel").waitFor({ state: "visible" });
    await clickVisibleOption(page, "#character-targets", "Azhvielle, the Unconfessed");
    const azhvielleHpAfterWell = Number(
      (await page.locator("#character-progression").innerText()).match(/HP\s+\d+\/(\d+)/)?.[1] || 0,
    );
    const discoveryBonusesAfter = await readFloorTwoDiscoveryBonuses();
    requireCondition(
      azhvielleHpAfterWell >= preSearchResources.azhvielle.hp[1] + 5 &&
        discoveryBonusesAfter.azhvielle.max_hp === discoveryBonusesBefore.azhvielle.max_hp + 5 &&
        discoveryBonusesAfter.branoc.max_hp === discoveryBonusesBefore.branoc.max_hp,
      `Azhvielle did not retain the Well's targeted +5 Max HP: ` +
        `${preSearchResources.azhvielle.hp[1]} -> ${azhvielleHpAfterWell}; ` +
        `bonuses ${JSON.stringify(discoveryBonusesBefore)} -> ${JSON.stringify(discoveryBonusesAfter)}`,
    );
    await clickVisibleOption(page, "#character-options", "Back");
  }
  console.log(`M4_BROWSER|SEARCH_SAVE_RELOAD|${wellClaimed ? "CLAIMED" : "FAILED_OUTCOME_PERSISTED"}|PASS`);

  const preBossResourcesBeforeRecover = await readFloorTwoActivePartyResources();
  await clickVisibleOption(page, "#overworld-options", "Recover");
  await page.waitForFunction(() =>
    document.getElementById("adventure-text").textContent.includes(
      "HP and Mana are fully restored. You may continue or extract.",
    ),
  );
  const preBossResourcesAfterRecover = await readFloorTwoActivePartyResources();
  verifyFloorTwoRestRecovery(
    preBossResourcesBeforeRecover,
    preBossResourcesAfterRecover,
    "Floor II Pre-Boss Rest",
  );
  await clickVisibleOption(page, "#overworld-options", "Choose Boss Helper");
  await page.locator("#boss-helper-selection").waitFor({ state: "visible" });
  const joruunHelperChoice = page.locator("#boss-helper-choices button")
    .filter({ hasText: "Joruun Veyr" });
  await joruunHelperChoice.waitFor({ state: "visible" });
  await joruunHelperChoice.click();
  await page.locator("#screen-badge").filter({ hasText: "REST" }).waitFor({ state: "visible" });
  await clickVisibleOption(page, "#overworld-options", "Save");
  await page.locator("#notice").filter({ hasText: "Game saved." }).waitFor({ state: "visible" });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(page);
  requireCondition(
    await page.locator("#screen-badge").innerText() === "REST" &&
      !(await page.locator("#overworld-options button").allInnerTexts()).includes("Choose Boss Helper"),
    "Floor II helper choice did not persist across browser save/reload",
  );
  console.log("M4_BROWSER|BOSS_HELPER_SAVE_RELOAD|PASS");
  await clickVisibleOption(page, "#route-actions", "Continue Without Rest");
  await page.waitForFunction(() => [...document.querySelectorAll("#route-actions button")].some((button) =>
    (button.querySelector(".choice-label")?.textContent?.trim() || button.textContent.trim()) === "Enter Encounter" &&
      !button.disabled,
  ));
  await clickVisibleOption(page, "#route-actions", "Enter Encounter");
  await page.locator("#party-panel").waitFor({ state: "visible" });
  await clearFloorBattle(10);
  await page.waitForFunction(
    () => document.getElementById("screen-badge").textContent.trim() === "HUB",
    null,
    { timeout: 10000 },
  ).catch(async (error) => {
    const state = await page.evaluate(() => ({
      badge: document.getElementById("screen-badge")?.textContent.trim(),
      location: document.getElementById("location-label")?.textContent.trim(),
      adventure: document.getElementById("adventure-text")?.textContent.trim(),
      notice: document.getElementById("notice")?.textContent.trim(),
      battleLog: document.getElementById("battle-log")?.innerText,
      party: [...document.querySelectorAll("#party-members .party-member")].map((member) =>
        member.innerText.trim(),
      ),
      routeActions: [...document.querySelectorAll("#route-actions button")].map((button) =>
        button.textContent.trim(),
      ),
    }));
    throw new Error(`Floor II boss did not return to Hub: ${JSON.stringify(state)}; ${error.message}`);
  });
  requireCondition(
    await page.locator("#location-label").innerText() === "Floor 1 Hub" &&
      (await page.locator("#adventure-text").innerText()).includes("Floor 2 is cleared"),
    "the Floor II boss did not secure the clear and return the roster to the Hub",
  );
  await clickVisibleOption(page, "#overworld-options", "Items");
  await page.locator("#items-panel").waitFor({ state: "visible" });
  const floorTwoItems = await page.locator("#items-list").innerText();
  // Floor II drops are chance-based, so a valid clear may award no Grade-II material.
  requireCondition(
    floorTwoItems.includes("Hub Storage"),
    `Floor II boss return did not expose secured inventory: ${floorTwoItems}`,
  );
  await clickVisibleOption(page, "#items-options", "Back");
  await page.locator("#items-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#overworld-options", "Recruit Companion");
  await page.locator("#companion-selection").waitFor({ state: "visible" });
  const zhaivraRecruitmentChoice = page.locator("#companion-choices .companion-choice")
    .filter({ hasText: "Zhaivra" });
  const joruunRecruitmentChoice = page.locator("#companion-choices .companion-choice")
    .filter({ hasText: "Joruun Veyr" });
  requireCondition(
    await page.locator("#companion-choices .companion-choice").count() === 2 &&
      await zhaivraRecruitmentChoice.isEnabled() &&
      await joruunRecruitmentChoice.isEnabled(),
    "Floor II clear did not independently offer both D3 and D4 for permanent recruitment",
  );
  await zhaivraRecruitmentChoice.click();
  await page.locator("#screen-badge").filter({ hasText: "HUB" }).waitFor({ state: "visible" });
  requireCondition(
    (await page.locator("#adventure-text").innerText()).includes("joins the roster at Level 1") &&
      (await page.locator("#adventure-text").innerText()).includes("active party remains unchanged"),
    "D3 Hub recruitment did not start at Level 1 while preserving the active pair",
  );
  console.log("M4_BROWSER|D3_HUB_RECRUITMENT|PASS");

  await clickVisibleOption(page, "#overworld-options", "Recruit Companion");
  await page.locator("#companion-selection").waitFor({ state: "visible" });
  requireCondition(
    await page.locator("#companion-choices .companion-choice").count() === 1 &&
      await joruunRecruitmentChoice.isEnabled(),
    "temporary D4 participation incorrectly counted as permanent recruitment",
  );
  await joruunRecruitmentChoice.click();
  await page.locator("#screen-badge").filter({ hasText: "HUB" }).waitFor({ state: "visible" });
  requireCondition(
    (await page.locator("#adventure-text").innerText()).includes("joins the roster at Level 1") &&
      (await page.locator("#adventure-text").innerText()).includes("active party remains unchanged"),
    "D4 Hub recruitment did not start at Level 1 without changing the active pair",
  );
  console.log("M4_BROWSER|FLOOR_TWO_BOSS_CLEAR|PASS");

  await clickVisibleOption(page, "#overworld-options", "Choose Party");
  await page.waitForFunction(
    () => document.getElementById("screen-badge").textContent.trim() === "PARTY SELECTION",
  );
  const d3d4Pair = page.locator("#party-pair-choices .party-pair-choice")
    .filter({ hasText: "Zhaivra Kelyth" })
    .filter({ hasText: "Joruun Veyr" });
  requireCondition(
    await d3d4Pair.count() === 2,
    "the party picker did not offer both ordered D3+D4 pairs for the Floor II replay check",
  );
  await d3d4Pair.first().click();
  await page.locator("#screen-badge").filter({ hasText: "HUB" }).waitFor({ state: "visible" });
  const startFloorTwoWithD3D4 = page.locator("#overworld-options button")
    .filter({ hasText: "Start Floor 2" });
  requireCondition(
    await startFloorTwoWithD3D4.isDisabled() &&
      (await startFloorTwoWithD3D4.innerText()).includes(
        "Unavailable: Choose an active pair that leaves D3 or D4 available for the Floor II boss.",
      ) &&
      await page.locator("#overworld-options button").filter({ hasText: "Start Floor 1" }).isEnabled(),
    "D3+D4 replay did not show its Floor II-only restriction and explanation",
  );
  console.log("M4_BROWSER|FLOOR_TWO_REPLAY_BLOCKED_D3_D4|PASS");

  await clickVisibleOption(page, "#overworld-options", "Choose Party");
  await page.waitForFunction(
    () => document.getElementById("screen-badge").textContent.trim() === "PARTY SELECTION",
  );
  const availableHelperPair = page.locator("#party-pair-choices .party-pair-choice")
    .filter({ hasText: "Ser Branoc" })
    .filter({ hasText: "Azhvielle" });
  requireCondition(
    await availableHelperPair.count() === 2,
    "the party picker did not offer both ordered pairs that leave D3 and D4 available",
  );
  await availableHelperPair.first().click();
  await page.locator("#screen-badge").filter({ hasText: "HUB" }).waitFor({ state: "visible" });
  requireCondition(
    await page.locator("#overworld-options button").filter({ hasText: "Start Floor 2" }).isEnabled(),
    "changing the active pair did not restore Floor II replay availability",
  );
  console.log("M4_BROWSER|FLOOR_TWO_REPLAY_PAIR_CHANGE|PASS");

  await clickVisibleOption(page, "#overworld-options", "Hub Inventory");
  await page.locator("#hub-economy-panel").waitFor({ state: "visible" });
  let floorThreeStoredPotions = await quantityInSupplyRow("Healing Potion", "Stored");
  while (
    floorThreeStoredPotions > 0 &&
    await quantityInSupplyRow("Healing Potion", "Carried") < 6
  ) {
    await updateSupply("Healing Potion", "Load");
    floorThreeStoredPotions = await quantityInSupplyRow("Healing Potion", "Stored");
  }
  await clickVisibleOption(page, "#hub-economy-options", "Back");
  await page.locator("#hub-economy-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#overworld-options", "Start Floor 3");
  await page.locator("#party-panel").waitFor({ state: "visible" });
  for (let battleNumber = 1; battleNumber <= 5; battleNumber += 1) {
    if (battleNumber > 1) {
      await clickVisibleOption(page, "#route-actions", "Enter Encounter");
      await page.locator("#party-panel").waitFor({ state: "visible" });
    }
    await clearFloorBattle(battleNumber, { floorLabel: "Floor III" });
    if (battleNumber === 1) {
      console.log("M4_BROWSER|FLOOR_THREE_ORDINARY_PAIR|PASS");
    }
    if (battleNumber === 5) {
      await page.locator("#screen-badge").filter({ hasText: "REST" }).waitFor({ state: "visible" });
    }
  }
  const floorThreeMidwayBefore = await readFloorTwoActivePartyResources();
  await clickVisibleOption(page, "#overworld-options", "Recover");
  await page.waitForFunction(() =>
    document.getElementById("adventure-text").textContent.includes(
      "HP and Mana are fully restored. You may continue or extract.",
    ),
  );
  verifyFloorTwoRestRecovery(
    floorThreeMidwayBefore,
    await readFloorTwoActivePartyResources(),
    "Floor III Midway Rest",
  );
  await clickVisibleOption(page, "#route-actions", "Continue Without Rest");
  await page.waitForFunction(() => [...document.querySelectorAll("#route-actions button")].some((button) =>
    (button.querySelector(".choice-label")?.textContent?.trim() || button.textContent.trim()) === "Enter Encounter" &&
      !button.disabled,
  ));

  for (let battleNumber = 6; battleNumber <= 9; battleNumber += 1) {
    await clickVisibleOption(page, "#route-actions", "Enter Encounter");
    await page.locator("#party-panel").waitFor({ state: "visible" });
    await clearFloorBattle(battleNumber, { floorLabel: "Floor III" });
    if (battleNumber === 9) {
      await page.locator("#screen-badge").filter({ hasText: "REST" }).waitFor({ state: "visible" });
    }
  }
  const floorThreePreBossBefore = await readFloorTwoActivePartyResources();
  await clickVisibleOption(page, "#overworld-options", "Recover");
  await page.waitForFunction(() =>
    document.getElementById("adventure-text").textContent.includes(
      "HP and Mana are fully restored. You may continue or extract.",
    ),
  );
  verifyFloorTwoRestRecovery(
    floorThreePreBossBefore,
    await readFloorTwoActivePartyResources(),
    "Floor III Pre-Boss Rest",
  );
  await clickVisibleOption(page, "#overworld-options", "Save");
  await page.locator("#notice").filter({ hasText: "Game saved." }).waitFor({ state: "visible" });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(page);
  requireCondition(
    await page.locator("#screen-badge").innerText() === "REST" &&
      await page.locator("#location-label").innerText() === "Pre-Boss Rest",
    "Floor III save/reload did not restore the pre-boss Rest checkpoint",
  );
  console.log("M4_BROWSER|FLOOR_THREE_REST_SAVE_RELOAD|PASS");
  await clickVisibleOption(page, "#route-actions", "Continue Without Rest");
  await page.waitForFunction(() => [...document.querySelectorAll("#route-actions button")].some((button) =>
    (button.querySelector(".choice-label")?.textContent?.trim() || button.textContent.trim()) === "Enter Encounter" &&
      !button.disabled,
  ));
  await clickVisibleOption(page, "#route-actions", "Enter Encounter");
  await page.locator("#party-panel").waitFor({ state: "visible" });
  const floorThreeBossParty = [
    "drifter_branoc",
    "drifter_azhvielle",
    "drifter_zhaivra",
    "drifter_joruun",
  ];
  await clearFloorBattle(10, {
    floorLabel: "Floor III",
    bossParty: floorThreeBossParty,
  });
  requireCondition(
    await page.locator("#location-label").innerText() === "Floor 1 Hub" &&
      (await page.locator("#adventure-text").innerText()).includes("Floor 3 is cleared"),
    "Floor III four-member boss did not clear the route and return the roster to the Hub",
  );
  const floorThreePersistedClear = await page.evaluate((key) => {
    const envelope = JSON.parse(localStorage.getItem(key));
    return envelope?.payload?.party?.floor_three_cleared;
  }, floorTwoProfileKey);
  requireCondition(floorThreePersistedClear === true, "Floor III clear was not persisted after the boss");
  console.log("M4_BROWSER|FLOOR_THREE_FOUR_MEMBER_BOSS_CLEAR|PASS");
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(page);
  const floorThreeClearAfterReload = await page.evaluate((key) => {
    const envelope = JSON.parse(localStorage.getItem(key));
    return envelope?.payload?.party?.floor_three_cleared;
  }, floorTwoProfileKey);
  requireCondition(
    await page.locator("#screen-badge").innerText() === "HUB" &&
      await page.locator("#location-label").innerText() === "Floor 1 Hub" &&
      floorThreeClearAfterReload === true,
    "Floor III clear or Hub return did not survive save/reload",
  );
  console.log("M4_BROWSER|FLOOR_THREE_CLEAR_SAVE_RELOAD|PASS");

  await clickVisibleOption(page, "#overworld-options", "Vendors");
  await clickVisibleOption(page, "#vendors-options", "Alchemist");
  await page.locator("#hub-economy-panel").waitFor({ state: "visible" });
  for (const itemName of [
    "Healing Potion",
    "Mana Potion",
    "Medicinal Herb",
    "Medicinal Herb",
    "Clean Water",
    "Clean Water",
  ]) {
    await updateSupply(itemName, "Buy");
  }
  const craftFloorFourPotion = async (name) => {
    const row = page.locator("#merchant-alchemy-recipes .merchant-row")
      .filter({ hasText: name });
    requireCondition(await row.count() === 1, `Alchemist did not offer the authored ${name} recipe`);
    const storedBefore = await quantityInSupplyRow(name, "Stored");
    await row.getByRole("button", { name: "Craft", exact: true }).click();
    await page.waitForFunction(({ itemName, previousQuantity }) => {
      const supply = [...document.querySelectorAll("#merchant-supplies .hub-supply-row")]
        .find((candidate) => candidate.innerText.includes(itemName));
      const current = Number(supply?.innerText.match(/Stored\s+(\d+)/)?.[1] || 0);
      return current === previousQuantity + 1;
    }, { itemName: name, previousQuantity: storedBefore });
  };
  await craftFloorFourPotion("Healing Potion");
  await craftFloorFourPotion("Healing Potion");
  await clickVisibleOption(page, "#hub-economy-options", "Back");
  await clickVisibleOption(page, "#vendors-options", "Merchant");
  await updateSupply("Healing Potion", "Buy");
  await updateSupply("Medicinal Herb", "Buy");
  await updateSupply("Clean Water", "Buy");
  await clickVisibleOption(page, "#hub-economy-options", "Back");
  await clickVisibleOption(page, "#vendors-options", "Alchemist");
  await page.locator("#alchemy-progress").waitFor({ state: "visible" });
  await craftFloorFourPotion("Healing Potion");
  await clickVisibleOption(page, "#hub-economy-options", "Back");
  await clickVisibleOption(page, "#vendors-options", "Back");
  await clickVisibleOption(page, "#overworld-options", "Hub Inventory");
  await page.waitForFunction(() => {
    const panel = document.getElementById("hub-economy-panel");
    const title = document.getElementById("hub-economy-title")?.textContent.trim();
    const itemNames = [...document.querySelectorAll("#merchant-supplies .hub-supply-row strong")]
      .map((item) => item.textContent.trim());
    return panel && !panel.hidden && title === "Hub Inventory" &&
      itemNames.includes("Healing Potion") && itemNames.includes("Mana Potion");
  });
  await page.evaluate(() => {
    const container = document.getElementById("merchant-supplies");
    const trace = {
      mutationCount: 0,
      lastMutationAtMs: null,
      lastSupplyClick: null,
      recentMutations: [],
    };
    new MutationObserver((records) => {
      trace.mutationCount += records.length;
      trace.lastMutationAtMs = performance.now();
      for (const record of records) {
        trace.recentMutations.push({
          type: record.type,
          targetId: record.target.parentElement?.closest("[id]")?.id || record.target.id || null,
          targetClass: typeof record.target.className === "string" ? record.target.className : null,
          attributeName: record.attributeName,
          atMs: performance.now(),
        });
      }
      trace.recentMutations = trace.recentMutations.slice(-20);
    }).observe(container, {
      attributes: true,
      childList: true,
      characterData: true,
      subtree: true,
    });
    document.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      const row = button?.closest(".hub-supply-row");
      if (!button || !row || !container.contains(row)) return;
      trace.lastSupplyClick = {
        label: button.innerText.trim(),
        disabled: button.disabled,
        row: row.innerText,
        quantity: row.querySelector("input")?.value ?? null,
        maximum: row.querySelector("input")?.max ?? null,
        atMs: performance.now(),
      };
    }, true);
    window.__DD_SUPPLY_MUTATION_TRACE__ = trace;
  });
  const carriedBeforeFloorFour = await page.locator("#merchant-supplies .hub-supply-row")
    .evaluateAll((rows) => rows.map((row) => ({
      name: row.querySelector("strong")?.textContent.trim(),
      quantity: Number(row.innerText.match(/Carried\s+(\d+)/)?.[1] || 0),
    })).filter((item) => item.name && item.quantity > 0));
  for (const item of carriedBeforeFloorFour) {
    while (await quantityInSupplyRow(item.name, "Carried") > 0) {
      await updateSupply(item.name, "Unload");
    }
  }
  for (const { itemName, target } of [
    { itemName: "Healing Potion", target: 5 },
    { itemName: "Mana Potion", target: 1 },
  ]) {
    let stored = await quantityInSupplyRow(itemName, "Stored");
    while (
      stored > 0 &&
      await quantityInSupplyRow(itemName, "Carried") < target
    ) {
      if (itemName === "Mana Potion") {
        console.log(`M8.3_BROWSER|MANA_LOAD_BEFORE|${JSON.stringify(await supplyDiagnostic(itemName))}`);
      }
      await updateSupply(itemName, "Load");
      stored = await quantityInSupplyRow(itemName, "Stored");
    }
  }
  requireCondition(
    await quantityInSupplyRow("Healing Potion", "Carried") === 5 &&
      await quantityInSupplyRow("Mana Potion", "Carried") === 1,
    "the Floor IV browser journey could not prepare its six-unit potion pack from finite Alchemist stock",
  );
  await clickVisibleOption(page, "#hub-economy-options", "Back");

  await clickVisibleOption(page, "#overworld-options", "Drowned Reliquary Briefing");
  await page.waitForFunction(() =>
    document.getElementById("adventure-text").textContent.includes(
      "Its location is now rumored.",
    ),
  );
  const drownedBriefingStatus = await page.evaluate((key) => {
    const envelope = JSON.parse(localStorage.getItem(key));
    return envelope?.payload?.story?.knowledge_facts?.m8_fact_drowned_reliquary;
  }, floorTwoProfileKey);
  requireCondition(
    drownedBriefingStatus === "rumored",
    `The Drowned Reliquary briefing did not persist Rumored knowledge: ${drownedBriefingStatus}`,
  );
  await clickVisibleOption(page, "#overworld-options", "Region Portal");
  await clickVisibleOption(page, "#region-choices", "Region 1");
  await page.locator("#screen-badge").filter({ hasText: "DESTINATIONS" }).waitFor({ state: "visible" });
  const drownedReliquaryChoice = page.locator("#region-choices button")
    .filter({ hasText: "Drowned Reliquary" });
  requireCondition(
    await drownedReliquaryChoice.isEnabled(),
    "Floor III completion and the four-member roster did not unlock the Drowned Reliquary",
  );
  await drownedReliquaryChoice.click();
  await page.locator("#party-panel").waitFor({ state: "visible" });
  requireCondition(
    await page.locator("#party-members .party-member").count() === 2 &&
      await page.locator("#enemy-panel .enemy").count() === 2,
    "Floor IV entry did not deploy the active pair against its authored first encounter",
  );
  const floorFourEntryEvidence = await page.evaluate((key) => {
    const envelope = JSON.parse(localStorage.getItem(key));
    return {
      floorRun: envelope?.payload?.party?.floor_four_run_id,
      activeRoute: envelope?.payload?.overworld?.active_route_id,
      knowledge: envelope?.payload?.story?.knowledge_facts?.m8_fact_drowned_reliquary,
    };
  }, floorTwoProfileKey);
  requireCondition(
    Boolean(floorFourEntryEvidence.floorRun) &&
      floorFourEntryEvidence.activeRoute === "floor_four" &&
      floorFourEntryEvidence.knowledge === "confirmed",
    `Floor IV entry did not persist its run and confirmed knowledge: ${JSON.stringify(floorFourEntryEvidence)}`,
  );
  console.log("M8.3_BROWSER|FLOOR_FOUR_ENTRY_AND_PAIR|PASS");

  for (let battleNumber = 1; battleNumber <= 5; battleNumber += 1) {
    if (battleNumber > 1) {
      await clickVisibleOption(page, "#route-actions", "Enter Encounter");
      await page.locator("#party-panel").waitFor({ state: "visible" });
    }
    await clearFloorBattle(battleNumber, { floorLabel: "Floor IV" });
  }
  await page.locator("#screen-badge").filter({ hasText: "REST" }).waitFor({ state: "visible" });
  await clickVisibleOption(page, "#overworld-options", "Save");
  await page.locator("#notice").filter({ hasText: "Game saved." }).waitFor({ state: "visible" });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(page);
  const floorFourRestAfterReload = await page.evaluate((key) => {
    const envelope = JSON.parse(localStorage.getItem(key));
    return {
      route: envelope?.payload?.overworld?.active_route_id,
      node: envelope?.payload?.overworld?.current_route_node_id,
      runId: envelope?.payload?.party?.floor_four_run_id,
    };
  }, floorTwoProfileKey);
  requireCondition(
    await page.locator("#screen-badge").innerText() === "REST" &&
      floorFourRestAfterReload.route === "floor_four" &&
      floorFourRestAfterReload.node === "floor_four_rest_midpoint" &&
      Boolean(floorFourRestAfterReload.runId),
    `Floor IV midpoint checkpoint did not survive reload: ${JSON.stringify(floorFourRestAfterReload)}`,
  );
  console.log("M8.3_BROWSER|FLOOR_FOUR_MIDPOINT_SAVE_RELOAD|PASS");

  await clickVisibleOption(page, "#overworld-options", "Talk Together");
  await page.locator("#screen-badge").filter({ hasText: "STORY" }).waitFor({ state: "visible" });
  const pairSceneText = await page.locator("#adventure-text").innerText();
  requireCondition(
    pairSceneText.includes("The Cost Of A Warning") &&
      pairSceneText.includes("This inscription is a warning about the record below it"),
    `Floor IV pair story did not render its authored dialogue: ${pairSceneText}`,
  );
  await clickVisibleOption(
    page,
    "#overworld-options",
    "Read only the warning",
  );
  await page.waitForFunction((key) => {
    const envelope = JSON.parse(localStorage.getItem(key) || "null");
    const story = envelope?.payload?.story;
    return story?.completed_events?.includes("m8_pair_scene_branoc_azhvielle") &&
      story?.player_decisions?.m8_story_choice_m8_pair_scene_branoc_azhvielle ===
        "share_warning";
  }, floorTwoProfileKey);
  const pairStoryEvidence = await page.evaluate((key) => {
    const payload = JSON.parse(localStorage.getItem(key)).payload;
    return {
      completed: payload?.story?.completed_events || [],
      decision: payload?.story?.player_decisions?.m8_story_choice_m8_pair_scene_branoc_azhvielle,
    };
  }, floorTwoProfileKey);
  requireCondition(
    pairStoryEvidence.completed.includes("m8_pair_scene_branoc_azhvielle") &&
      pairStoryEvidence.decision === "share_warning",
    `Floor IV pair story choice was not durably recorded: ${JSON.stringify(pairStoryEvidence)}`,
  );
  await clickVisibleOption(page, "#overworld-options", "Back");
  await page.locator("#screen-badge").filter({ hasText: "REST" }).waitFor({ state: "visible" });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(page);
  const pairStoryAfterReload = await page.evaluate((key) => {
    const payload = JSON.parse(localStorage.getItem(key)).payload;
    return {
      completed: payload?.story?.completed_events || [],
      decision: payload?.story?.player_decisions?.m8_story_choice_m8_pair_scene_branoc_azhvielle,
    };
  }, floorTwoProfileKey);
  requireCondition(
    pairStoryAfterReload.completed.filter(
      (eventId) => eventId === "m8_pair_scene_branoc_azhvielle",
    ).length === 1 &&
      pairStoryAfterReload.decision === "share_warning" &&
      await page.locator("#screen-badge").innerText() === "REST",
    `Floor IV pair story did not survive reload exactly once: ${JSON.stringify(pairStoryAfterReload)}`,
  );
  console.log("M8.6_BROWSER|PAIR_STORY_CHOICE_RELOAD|PASS");

  await clickVisibleOption(
    page,
    "#overworld-options",
    "Azhvielle's Archive Memory",
  );
  await page.locator("#screen-badge").filter({ hasText: "STORY" }).waitFor({ state: "visible" });
  const archiveMemoryText = await page.locator("#adventure-text").innerText();
  requireCondition(
    archiveMemoryText.includes("Azhvielle recognizes a catalog mark") &&
      archiveMemoryText.includes("Ashen Regent") &&
      archiveMemoryText.includes("whether I made that choice"),
    `Archive Memory did not render its authored personal history and reveal: ${archiveMemoryText}`,
  );
  await clickVisibleOption(
    page,
    "#overworld-options",
    "Ask what the party should do now",
  );
  await page.waitForFunction((key) => {
    const story = JSON.parse(localStorage.getItem(key) || "null")?.payload?.story;
    return story?.completed_events?.includes("m8_azh_archive_memory") &&
      story?.player_decisions?.m8_story_choice_m8_azh_archive_memory ===
        "ask_party_plan" &&
      story?.knowledge_facts?.m8_fact_ashen_regent === "confirmed";
  }, floorTwoProfileKey);
  const archiveMemoryEvidence = await page.evaluate((key) => {
    const story = JSON.parse(localStorage.getItem(key)).payload.story;
    return {
      completions: story.completed_events.filter(
        (eventId) => eventId === "m8_azh_archive_memory",
      ).length,
      decision: story.player_decisions.m8_story_choice_m8_azh_archive_memory,
      fact: story.knowledge_facts.m8_fact_ashen_regent,
    };
  }, floorTwoProfileKey);
  requireCondition(
    archiveMemoryEvidence.completions === 1 &&
      archiveMemoryEvidence.decision === "ask_party_plan" &&
      archiveMemoryEvidence.fact === "confirmed",
    `Archive Memory did not persist its choice and knowledge exactly once: ${JSON.stringify(archiveMemoryEvidence)}`,
  );
  await clickVisibleOption(page, "#overworld-options", "Back");
  await page.locator("#screen-badge").filter({ hasText: "REST" }).waitFor({ state: "visible" });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(page);
  const archiveAfterReload = await page.evaluate((key) => {
    const story = JSON.parse(localStorage.getItem(key)).payload.story;
    return {
      completions: story.completed_events.filter(
        (eventId) => eventId === "m8_azh_archive_memory",
      ).length,
      decision: story.player_decisions.m8_story_choice_m8_azh_archive_memory,
      fact: story.knowledge_facts.m8_fact_ashen_regent,
      actionCount: [...document.querySelectorAll("#overworld-options button")]
        .filter((button) => button.innerText.includes("Azhvielle's Archive Memory"))
        .length,
    };
  }, floorTwoProfileKey);
  requireCondition(
    await page.locator("#screen-badge").innerText() === "REST" &&
      archiveAfterReload.completions === 1 &&
      archiveAfterReload.decision === "ask_party_plan" &&
      archiveAfterReload.fact === "confirmed" &&
      archiveAfterReload.actionCount === 0,
    `Archive Memory duplicated or lost its knowledge after reload: ${JSON.stringify(archiveAfterReload)}`,
  );
  console.log("M8.6_BROWSER|ARCHIVE_MEMORY_CHOICE_KNOWLEDGE_RELOAD_ONCE|PASS");

  await clickVisibleOption(page, "#overworld-options", "Search Site");
  await page.locator("#discovery-selection").waitFor({ state: "visible" });
  const floorFourDiscoveryChoices = page.locator("#discovery-choices button");
  requireCondition(
    await floorFourDiscoveryChoices.count() === 2,
    "Floor IV Ancient Well did not offer exactly the active Drifters as searchers",
  );
  const floorFourDiscoveryBefore = await page.evaluate((key) => {
    const payload = JSON.parse(localStorage.getItem(key)).payload;
    return { activeIds: payload.party.active_drifter_ids };
  }, floorTwoProfileKey);
  const floorFourWellBonusesBefore = await readFloorTwoDiscoveryBonuses();
  await floorFourDiscoveryChoices.first().click();
  await page.waitForFunction(() => ["CLAIM DISCOVERY", "REST"].includes(
    document.getElementById("screen-badge").textContent.trim(),
  ));
  const floorFourSearchResult = await page.evaluate((key) => {
    const envelope = JSON.parse(localStorage.getItem(key));
    const event = envelope?.payload?.party?.resolved_run_events?.find(
      (entry) => entry.kind === "discovery_search" &&
        entry.floor_id === "floor_four" &&
        entry.node_id === "floor_four_rest_midpoint",
    );
    return event ? {
      sourceId: event.result.source_id,
      searcherId: event.result.searcher_drifter_id,
      found: event.result.found,
      roll: event.result.roll,
      chance: event.result.effective_chance_bps,
      activeIds: envelope?.payload?.party?.active_drifter_ids || [],
    } : null;
  }, floorTwoProfileKey);
  requireCondition(
    floorFourSearchResult?.sourceId === "ancient_well_floor4_01" &&
      floorFourSearchResult.chance >= 1000 &&
      floorFourSearchResult.chance <= 10000 &&
      floorFourSearchResult.roll >= 1 &&
      floorFourSearchResult.roll <= 10000 &&
      floorFourSearchResult.activeIds.includes(floorFourSearchResult.searcherId) &&
      typeof floorFourSearchResult.found === "boolean",
    `Floor IV search did not persist its authoritative source outcome: ${JSON.stringify(floorFourSearchResult)}`,
  );
  let floorFourWellClaimed = false;
  let floorFourWellTargetId = null;
  if (floorFourSearchResult.found) {
    await page.locator("#screen-badge").filter({ hasText: "CLAIM DISCOVERY" }).waitFor({ state: "visible" });
    const targetChoices = page.locator("#discovery-choices button");
    requireCondition(
      await targetChoices.count() === 2,
      "Floor IV Ancient Well did not restrict claim targets to the active Drifters",
    );
    floorFourWellTargetId = floorFourDiscoveryBefore.activeIds[1];
    await targetChoices.nth(1).click();
    await page.locator("#screen-badge").filter({ hasText: "CONFIRM DISCOVERY" }).waitFor({ state: "visible" });
    await clickVisibleOption(page, "#overworld-options", "Confirm");
    await page.locator("#screen-badge").filter({ hasText: "REST" }).waitFor({ state: "visible" });
    const floorFourClaim = await page.evaluate((key) => {
      const envelope = JSON.parse(localStorage.getItem(key));
      return envelope?.payload?.world?.permanent_discovery_claims || [];
    }, floorTwoProfileKey);
    requireCondition(
      floorFourClaim.includes("ancient_well_floor4_01"),
      `Floor IV Ancient Well claim was not persisted: ${JSON.stringify(floorFourClaim)}`,
    );
    floorFourWellClaimed = true;
  }
  await clickVisibleOption(page, "#overworld-options", "Save");
  await page.locator("#notice").filter({ hasText: "Game saved." }).waitFor({ state: "visible" });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(page);
  const floorFourDiscoveryAfterReload = await page.evaluate((key) => {
    const envelope = JSON.parse(localStorage.getItem(key));
    const event = envelope?.payload?.party?.resolved_run_events?.find(
      (entry) => entry.kind === "discovery_search" &&
        entry.floor_id === "floor_four" &&
        entry.node_id === "floor_four_rest_midpoint",
    );
    return {
      screen: document.getElementById("screen-badge")?.textContent.trim(),
      sourceId: event?.result?.source_id,
      found: event?.result?.found,
      claimed: envelope?.payload?.world?.permanent_discovery_claims?.includes(
        "ancient_well_floor4_01",
      ) || false,
    };
  }, floorTwoProfileKey);
  requireCondition(
    await page.locator("#screen-badge").innerText() === "REST" &&
      floorFourDiscoveryAfterReload.screen === "REST" &&
      floorFourDiscoveryAfterReload.sourceId === "ancient_well_floor4_01" &&
      floorFourDiscoveryAfterReload.claimed === floorFourWellClaimed,
    `Floor IV discovery outcome did not survive reload: ${JSON.stringify(floorFourDiscoveryAfterReload)}`,
  );
  const floorFourWellBonusesAfter = await readFloorTwoDiscoveryBonuses();
  for (const drifterId of floorFourDiscoveryBefore.activeIds) {
    const expected = floorFourWellBonusesBefore[drifterId].max_hp + (
      floorFourWellClaimed && drifterId === floorFourWellTargetId ? 5 : 0
    );
    requireCondition(
      floorFourWellBonusesAfter[drifterId].max_hp === expected,
      `Floor IV Well did not preserve its one-time target effect for ${drifterId}`,
    );
  }
  console.log(`M8.4_BROWSER|FLOOR_FOUR_DISCOVERY|${floorFourWellClaimed ? "CLAIMED" : "OUTCOME_PERSISTED"}|PASS`);

  await clickVisibleOption(page, "#overworld-options", "Recover");
  await page.locator("#route-actions").filter({ hasText: "Enter Encounter" }).waitFor({ state: "visible" });
  let floorFourBattle08Before = null;
  let floorFourBattle08Evidence = null;
  for (let battleNumber = 6; battleNumber <= 9; battleNumber += 1) {
    if (battleNumber === 8) {
      floorFourBattle08Before = await page.evaluate((key) => {
        const payload = JSON.parse(localStorage.getItem(key)).payload;
        return {
          runId: payload.party.floor_four_run_id,
          armorCount: payload.party.equipment_instances.filter(
            (item) => item.source_id === "m8_floor_four_armor_source",
          ).length,
          healingPotionCount: payload.party.outing_rewards.items.healing_potion || 0,
          sharedPotionCount: payload.party.shared_items.healing_potion || 0,
          carriedPotionCount: payload.party.carried_items.healing_potion || 0,
        };
      }, floorTwoProfileKey);
    }
    await clickVisibleOption(page, "#route-actions", "Enter Encounter");
    await page.locator("#party-panel").waitFor({ state: "visible" });
    await clearFloorBattle(battleNumber, { floorLabel: "Floor IV" });
    if (battleNumber === 8) {
      floorFourBattle08Evidence = await page.evaluate(({ key, runId }) => {
        const payload = JSON.parse(localStorage.getItem(key)).payload;
        const events = payload.party.resolved_run_events.filter(
          (event) => event.run_id === runId &&
            event.floor_id === "floor_four" &&
            event.node_id === "floor_four_battle_08",
        );
        const encounter = events.find((event) => event.kind === "encounter_rewards");
        const armorEvents = events.filter(
          (event) => event.kind === "armor_reward" &&
            event.result.source_id === "m8_floor_four_armor_source",
        );
        const recoveryEvents = events.filter(
          (event) => event.kind === "fixed_item_reward" &&
            event.result.source_id === "m8_floor_four_recovery_source",
        );
        const armorInstances = payload.party.equipment_instances.filter(
          (item) => item.source_id === "m8_floor_four_armor_source",
        );
        return {
          events,
          encounterSourceIds: encounter?.result?.reward_source_ids || [],
          armorEvents,
          recoveryEvents,
          armorInstances,
          healingPotionCount: payload.party.outing_rewards.items.healing_potion || 0,
          sharedPotionCount: payload.party.shared_items.healing_potion || 0,
          carriedPotionCount: payload.party.carried_items.healing_potion || 0,
        };
      }, { key: floorTwoProfileKey, runId: floorFourBattle08Before.runId });
      requireCondition(
        floorFourBattle08Before.armorCount === 0 &&
          floorFourBattle08Evidence.armorEvents.length === 1 &&
          floorFourBattle08Evidence.recoveryEvents.length === 1 &&
          floorFourBattle08Evidence.armorInstances.length === 1 &&
          floorFourBattle08Evidence.armorInstances[0].instance_id ===
            floorFourBattle08Evidence.armorEvents[0].result.instance.instance_id &&
          floorFourBattle08Evidence.armorInstances[0].secured === false &&
          floorFourBattle08Evidence.armorEvents[0].result.template_id === "field_chest" &&
          floorFourBattle08Evidence.armorInstances[0].definition_id === "field_chest" &&
          floorFourBattle08Evidence.armorEvents[0].result.floor === 4 &&
          floorFourBattle08Evidence.recoveryEvents[0].result.item_id === "healing_potion" &&
          floorFourBattle08Evidence.recoveryEvents[0].result.quantity === 1 &&
          floorFourBattle08Evidence.encounterSourceIds.includes("m8_floor_four_armor_source") &&
          floorFourBattle08Evidence.encounterSourceIds.includes("m8_floor_four_recovery_source") &&
          floorFourBattle08Evidence.healingPotionCount ===
            floorFourBattle08Before.healingPotionCount + 1 &&
          floorFourBattle08Evidence.sharedPotionCount ===
            floorFourBattle08Before.sharedPotionCount,
        `Encounter 08 did not commit exactly one unsecured authored armor and Healing Potion: ${JSON.stringify({ floorFourBattle08Before, floorFourBattle08Evidence })}`,
      );
      const committedArmorId = floorFourBattle08Evidence.armorInstances[0].instance_id;
      await clickVisibleOption(page, "#overworld-options", "Options");
      await page.locator("#screen-badge").filter({ hasText: "OPTIONS" }).waitFor({ state: "visible" });
      await clickVisibleOption(page, "#overworld-options", "Save");
      await page.locator("#notice").filter({ hasText: "Game saved." }).waitFor({ state: "visible" });
      await page.reload({ waitUntil: "domcontentloaded" });
      await page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
        timeout: 120000,
      });
      await continueSavedGameAfterReload(page);
      const floorFourRewardsAfterReload = await page.evaluate(({ key, runId }) => {
        const payload = JSON.parse(localStorage.getItem(key)).payload;
        const events = payload.party.resolved_run_events.filter(
          (event) => event.run_id === runId &&
            event.floor_id === "floor_four" &&
            event.node_id === "floor_four_battle_08",
        );
        const armorEvent = events.find(
          (event) => event.kind === "armor_reward" &&
            event.result.source_id === "m8_floor_four_armor_source",
        );
        const recoveryEvent = events.find(
          (event) => event.kind === "fixed_item_reward" &&
            event.result.source_id === "m8_floor_four_recovery_source",
        );
        return {
          badge: document.getElementById("screen-badge")?.textContent.trim(),
          armor: payload.party.equipment_instances.filter(
            (item) => item.source_id === "m8_floor_four_armor_source",
          ),
          armorEventCount: events.filter((event) => event.kind === "armor_reward").length,
          recoveryEventCount: events.filter((event) => event.kind === "fixed_item_reward").length,
          armorEvent,
          recoveryEvent,
          potionCount: payload.party.outing_rewards.items.healing_potion || 0,
          sharedPotionCount: payload.party.shared_items.healing_potion || 0,
          carriedPotionCount: payload.party.carried_items.healing_potion || 0,
        };
      }, { key: floorTwoProfileKey, runId: floorFourBattle08Before.runId });
      requireCondition(
        floorFourRewardsAfterReload.badge === "OVERWORLD" &&
          floorFourRewardsAfterReload.armor.length === 1 &&
          floorFourRewardsAfterReload.armor[0].instance_id === committedArmorId &&
          floorFourRewardsAfterReload.armor[0].secured === false &&
          floorFourRewardsAfterReload.armorEventCount === 1 &&
          floorFourRewardsAfterReload.armorEvent.result.source_id === "m8_floor_four_armor_source" &&
          floorFourRewardsAfterReload.armorEvent.result.template_id === "field_chest" &&
          floorFourRewardsAfterReload.armorEvent.result.instance.instance_id === committedArmorId &&
          floorFourRewardsAfterReload.recoveryEventCount === 1 &&
          floorFourRewardsAfterReload.recoveryEvent.result.source_id === "m8_floor_four_recovery_source" &&
          floorFourRewardsAfterReload.recoveryEvent.result.item_id === "healing_potion" &&
          floorFourRewardsAfterReload.recoveryEvent.result.quantity === 1 &&
          floorFourRewardsAfterReload.potionCount ===
            floorFourBattle08Before.healingPotionCount + 1 &&
          floorFourRewardsAfterReload.sharedPotionCount ===
            floorFourBattle08Before.sharedPotionCount &&
          floorFourRewardsAfterReload.carriedPotionCount ===
            floorFourBattle08Evidence.carriedPotionCount,
        `Encounter 08 rewards changed or duplicated after reload: ${JSON.stringify(floorFourRewardsAfterReload)}`,
      );
      console.log("M8.4_BROWSER|FLOOR_FOUR_ENCOUNTER_08_REWARDS|UNSECURED_SAVE_RELOAD|PASS");
    }
  }
  await page.locator("#screen-badge").filter({ hasText: "REST" }).waitFor({ state: "visible" });
  await clickVisibleOption(page, "#overworld-options", "Save");
  await page.locator("#notice").filter({ hasText: "Game saved." }).waitFor({ state: "visible" });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(page);
  requireCondition(
    await page.locator("#screen-badge").innerText() === "REST" &&
      await page.locator("#location-label").innerText() === "Pre-Boss Rest",
    "Floor IV pre-boss Rest did not survive save/reload",
  );

  const floorFourBeforeBossRest = await page.evaluate((key) => {
    const payload = JSON.parse(localStorage.getItem(key)).payload;
    return {
      armor: payload.party.equipment_instances.filter(
        (item) => item.source_id === "m8_floor_four_armor_source",
      ),
      runPotionCount: payload.party.outing_rewards.items.healing_potion || 0,
      sharedPotionCount: payload.party.shared_items.healing_potion || 0,
      carriedPotionCount: payload.party.carried_items.healing_potion || 0,
    };
  }, floorTwoProfileKey);
  requireCondition(
    floorFourBeforeBossRest.armor.length === 1 &&
      floorFourBeforeBossRest.armor[0].secured === false &&
      floorFourBeforeBossRest.runPotionCount ===
        floorFourBattle08Before.healingPotionCount + 1 &&
      floorFourBeforeBossRest.sharedPotionCount ===
        floorFourBattle08Before.sharedPotionCount,
    `Floor IV rewards were not still unsecured before the pre-boss Rest: ${JSON.stringify(floorFourBeforeBossRest)}`,
  );
  await clickVisibleOption(page, "#overworld-options", "Recover");
  await page.locator("#route-actions").filter({ hasText: "Enter Encounter" }).waitFor({ state: "visible" });
  const floorFourAfterBossRest = await page.evaluate((key) => {
    const payload = JSON.parse(localStorage.getItem(key)).payload;
    return {
      armor: payload.party.equipment_instances.filter(
        (item) => item.source_id === "m8_floor_four_armor_source",
      ),
      runPotionCount: payload.party.outing_rewards.items.healing_potion || 0,
      sharedPotionCount: payload.party.shared_items.healing_potion || 0,
      carriedPotionCount: payload.party.carried_items.healing_potion || 0,
    };
  }, floorTwoProfileKey);
  requireCondition(
    floorFourAfterBossRest.armor.length === 1 &&
      floorFourAfterBossRest.armor[0].instance_id ===
        floorFourBattle08Evidence.armorInstances[0].instance_id &&
      floorFourAfterBossRest.armor[0].secured === true &&
      floorFourAfterBossRest.runPotionCount === floorFourBeforeBossRest.runPotionCount &&
      floorFourAfterBossRest.sharedPotionCount === floorFourBeforeBossRest.sharedPotionCount &&
      floorFourAfterBossRest.carriedPotionCount === floorFourBeforeBossRest.carriedPotionCount,
    `Pre-boss Rest did not secure only the armor while preserving unsecured Recovery: ${JSON.stringify(floorFourAfterBossRest)}`,
  );
  const floorFourExpectedPotionSettlement = await page.evaluate((key) => {
    const party = JSON.parse(localStorage.getItem(key)).payload.party;
    return (party.shared_items.healing_potion || 0) +
      (party.carried_items.healing_potion || 0) +
      (party.outing_rewards.items.healing_potion || 0);
  }, floorTwoProfileKey);
  await clickVisibleOption(page, "#route-actions", "Enter Encounter");
  await page.locator("#party-panel").waitFor({ state: "visible" });
  await clearFloorBattle(10, {
    floorLabel: "Floor IV",
    bossParty: ["drifter_branoc", "drifter_azhvielle"],
  });
  const floorFourClearEvidence = await page.evaluate((key) => {
    const envelope = JSON.parse(localStorage.getItem(key));
    const armorInstances = envelope?.payload?.party?.equipment_instances?.filter(
      (item) => item.source_id === "m8_floor_four_armor_source",
    ) || [];
    return {
      cleared: envelope?.payload?.party?.floor_four_cleared,
      crystal: envelope?.payload?.party?.shared_items?.grade_iv_magic_crystal,
      ashenVault: envelope?.payload?.story?.knowledge_facts?.m8_fact_ashen_vault,
      sharedPotionCount: envelope?.payload?.party?.shared_items?.healing_potion || 0,
      carriedPotionCount: envelope?.payload?.party?.carried_items?.healing_potion || 0,
      outingPotionCount: envelope?.payload?.party?.outing_rewards?.items?.healing_potion || 0,
      armorInstances,
    };
  }, floorTwoProfileKey);
  requireCondition(
    floorFourClearEvidence.cleared === true &&
      floorFourClearEvidence.crystal === 1 &&
      floorFourClearEvidence.ashenVault === "rumored" &&
      floorFourClearEvidence.armorInstances.length === 1 &&
      floorFourClearEvidence.armorInstances[0].instance_id ===
        floorFourBattle08Evidence.armorInstances[0].instance_id &&
      floorFourClearEvidence.armorInstances[0].secured === true &&
      floorFourClearEvidence.sharedPotionCount === floorFourExpectedPotionSettlement &&
      floorFourClearEvidence.carriedPotionCount === 0 &&
      floorFourClearEvidence.outingPotionCount === 0,
    `Floor IV boss settlement did not persist clear, one Crystal, and Ashen Vault rumor: ${JSON.stringify(floorFourClearEvidence)}`,
  );
  console.log("M8.3_BROWSER|FLOOR_FOUR_BOSS_CLEAR_AND_REWARDS|PASS");

  const runM8DiscoveryBrowserJourney = async ({
    fixtureName,
    sourceId,
    resourceName,
    rewardLabel,
    marker,
  }) => {
    const fixture = m8DiscoveryFixtures[fixtureName];
    const discoveryPage = await browser.newPage();
    discoveryPage.setDefaultNavigationTimeout(120000);
    discoveryPage.on("pageerror", (error) => errors.push(error.message));
    discoveryPage.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text());
    });
    await discoveryPage.route("**/favicon.ico", (route) =>
      route.fulfill({ status: 204, body: "" }),
    );
    await discoveryPage.route("**/python/boot.py", async (route) => {
      const response = await route.fetch();
      const source = await response.text();
      await route.fulfill({
        response,
        body: `${source}\nimport random\nrandom.seed(2)\n`,
      });
    });
    await discoveryPage.goto(`${baseUrl}/`, { waitUntil: "domcontentloaded" });
    await discoveryPage.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
      timeout: 120000,
    });
    await discoveryPage.evaluate(({ key, envelope }) => localStorage.setItem(key, envelope), {
      key: fixture.profile_key,
      envelope: fixture.envelope,
    });
    await discoveryPage.reload({ waitUntil: "domcontentloaded" });
    await discoveryPage.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
      timeout: 120000,
    });
    await continueSavedGameAfterReload(discoveryPage);
    await discoveryPage.locator("#screen-badge").filter({ hasText: "REST" }).waitFor({ state: "visible" });

    const readDiscoveryState = () => discoveryPage.evaluate(({ key, sourceId }) => {
      const envelope = JSON.parse(localStorage.getItem(key));
      const payload = envelope.payload;
      const members = [payload.player, ...payload.party.companions];
      const drifterIdByChoice = {
        "1": "branoc",
        "2": "azhvielle",
        "3": "zhaivra",
        "4": "joruun",
      };
      const resources = Object.fromEntries(members.map((member) => [
        drifterIdByChoice[member.identity.profile.choice],
        {
          hp: member.resources.health.maximum,
          mana: member.resources.mana.maximum,
        },
      ]));
      const searches = payload.party.resolved_run_events.filter(
        (event) => event.kind === "discovery_search" &&
          event.result.source_id === sourceId,
      );
      return {
        activeIds: payload.party.active_drifter_ids,
        resources,
        claims: payload.world.permanent_discovery_claims,
        searches,
      };
    }, { key: fixture.profile_key, sourceId });

    const before = await readDiscoveryState();
    requireCondition(
      before.activeIds.length === 2 &&
        before.resources.branoc && before.resources.azhvielle &&
        before.resources.zhaivra && before.resources.joruun,
      `${sourceId} fixture did not contain the active pair and full recruited roster: ${JSON.stringify(before)}`,
    );
    await clickVisibleOption(discoveryPage, "#overworld-options", "Search Site");
    await discoveryPage.locator("#discovery-selection").waitFor({ state: "visible" });
    const searcherButtons = discoveryPage.locator("#discovery-choices button");
    const searcherLabels = await searcherButtons.allInnerTexts();
    requireCondition(
      searcherLabels.length === 2 && searcherLabels.some((label) => label.includes("Azhvielle")) &&
        searcherLabels.some((label) => label.includes("Ser Branoc")),
      `${sourceId} search did not offer exactly the active Drifters: ${JSON.stringify(searcherLabels)}`,
    );
    await searcherButtons.filter({ hasText: "Azhvielle" }).click();
    await discoveryPage.locator("#screen-badge").filter({ hasText: "CLAIM DISCOVERY" }).waitFor({ state: "visible" });

    const searchState = await readDiscoveryState();
    const searchEvent = searchState.searches[0];
    requireCondition(
      searchState.searches.length === 1 &&
        searchEvent.result.source_id === sourceId &&
        searchEvent.result.searcher_drifter_id === "azhvielle" &&
        searchEvent.result.found === true &&
        searchEvent.result.roll <= searchEvent.result.effective_chance_bps,
      `${sourceId} seeded browser search did not resolve successfully through Python: ${JSON.stringify(searchState.searches)}`,
    );

    const targetButtons = discoveryPage.locator("#discovery-choices button");
    const targetLabels = await targetButtons.allInnerTexts();
    requireCondition(
      targetLabels.length === 2 && targetLabels.some((label) => label.includes("Azhvielle")) &&
        targetLabels.some((label) => label.includes("Ser Branoc")),
      `${sourceId} reward targeting did not restrict choices to the active pair: ${JSON.stringify(targetLabels)}`,
    );
    await targetButtons.filter({ hasText: "Ser Branoc" }).click();
    await discoveryPage.locator("#screen-badge").filter({ hasText: "CONFIRM DISCOVERY" }).waitFor({ state: "visible" });
    requireCondition(
      (await discoveryPage.locator("#adventure-text").innerText()).includes(rewardLabel),
      `${sourceId} confirmation did not show its exact authored reward`,
    );
    await clickVisibleOption(discoveryPage, "#overworld-options", "Confirm");
    await discoveryPage.locator("#screen-badge").filter({ hasText: "REST" }).waitFor({ state: "visible" });
    requireCondition(
      (await discoveryPage.locator("#notice").innerText()).includes(`claimed by Ser Branoc`) &&
        (await discoveryPage.locator("#notice").innerText()).includes(rewardLabel),
      `${sourceId} did not report its exact reward and selected active Drifter`,
    );

    const afterClaim = await readDiscoveryState();
    requireCondition(
      afterClaim.claims.filter((claimedId) => claimedId === sourceId).length === 1 &&
        afterClaim.searches.length === 1,
      `${sourceId} did not commit exactly one search and claim: ${JSON.stringify(afterClaim)}`,
    );
    for (const drifterId of Object.keys(before.resources)) {
      for (const statName of ["hp", "mana"]) {
        const expected = before.resources[drifterId][statName] + (
          drifterId === "branoc" && statName === resourceName ? 5 : 0
        );
        requireCondition(
          afterClaim.resources[drifterId][statName] === expected,
          `${sourceId} changed ${drifterId}'s ${statName} incorrectly: ${JSON.stringify({ before, afterClaim })}`,
        );
      }
    }
    const actionsAfterClaim = await discoveryPage.locator("#overworld-options button").allInnerTexts();
    requireCondition(
      !actionsAfterClaim.includes("Search Site") && !actionsAfterClaim.includes("Claim Discovery"),
      `${sourceId} was offered again after its claim: ${JSON.stringify(actionsAfterClaim)}`,
    );

    await clickVisibleOption(discoveryPage, "#overworld-options", "Save");
    await discoveryPage.locator("#notice").filter({ hasText: "Game saved." }).waitFor({ state: "visible" });
    await discoveryPage.reload({ waitUntil: "domcontentloaded" });
    await discoveryPage.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
      timeout: 120000,
    });
    await continueSavedGameAfterReload(discoveryPage);
    const afterReload = await readDiscoveryState();
    requireCondition(
      afterReload.claims.filter((claimedId) => claimedId === sourceId).length === 1 &&
        afterReload.searches.length === 1 &&
        JSON.stringify(afterReload.resources) === JSON.stringify(afterClaim.resources) &&
        await discoveryPage.locator("#screen-badge").innerText() === "REST" &&
        !(await discoveryPage.locator("#overworld-options button").allInnerTexts()).includes("Search Site") &&
        !(await discoveryPage.locator("#overworld-options button").allInnerTexts()).includes("Claim Discovery"),
      `${sourceId} claim, exact reward, or duplicate guard changed after reload: ${JSON.stringify(afterReload)}`,
    );
    console.log(marker);
    await discoveryPage.close();
  };

  await runM8DiscoveryBrowserJourney({
    fixtureName: "ancient_well",
    sourceId: "ancient_well_floor4_01",
    resourceName: "hp",
    rewardLabel: "+5 Max HP",
    marker: "M8.4_BROWSER|ANCIENT_WELL_ACTIVE_TARGETED_CLAIM|PASS",
  });
  await runM8DiscoveryBrowserJourney({
    fixtureName: "forgotten_altar",
    sourceId: "forgotten_altar_floor4_01",
    resourceName: "mana",
    rewardLabel: "+5 Max Mana",
    marker: "M8.4_BROWSER|FORGOTTEN_ALTAR_ACTIVE_TARGETED_CLAIM|PASS",
  });

  const m5Page = await browser.newPage();
  m5Page.setDefaultNavigationTimeout(120000);
  m5Page.on("pageerror", (error) => errors.push(error.message));
  await m5Page.goto(`${baseUrl}/`, { waitUntil: "domcontentloaded" });
  const m5HubProfileKey = "dungeon-drifters.profile.v1.d4d4d4d4-0000-4000-8000-000000000001";
  await m5Page.evaluate(({ key, envelope }) => localStorage.setItem(key, envelope), {
    key: m5HubProfileKey,
    envelope: m5EquipmentFixtures.hub,
  });
  await m5Page.reload({ waitUntil: "domcontentloaded" });
  await m5Page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(m5Page);
  await clickVisibleOption(m5Page, "#overworld-options", "Character");
  const m5CharacterEquipmentOption = () =>
    m5Page.locator("#character-options button").filter({ hasText: "Equipment" });
  await m5CharacterEquipmentOption().waitFor({ state: "visible" });
  await m5CharacterEquipmentOption().click();
  await m5Page.locator("#equipment-panel").waitFor({ state: "visible" });
  await clickVisibleOption(m5Page, "#equipment-targets", "Ser Branoc, the Unbroken Crest");
  const m5EquipmentButton = (name) =>
    m5Page.locator("#equipment-inventory button").filter({ hasText: name });
  const m5ActionButton = (name) =>
    m5Page.locator("#equipment-actions button").filter({ hasText: name });
  const selectM5Equipment = async (name) => {
    await m5EquipmentButton(name).click();
    await m5Page.locator("#equipment-inspection-name").filter({ hasText: name }).waitFor({ state: "visible" });
  };
  await selectM5Equipment("Field Helm");
  requireCondition(
    (await m5Page.locator("#equipment-inspection-state").innerText()).includes("Secured") &&
      (await m5Page.locator("#equipment-inspection-state").innerText()).includes("Not equipped"),
    "the generated Hub armor did not preserve its secured, unassigned ownership state",
  );
  await m5ActionButton("Equip").click();
  await m5Page.locator("#notice").filter({ hasText: "assigned to the selected Drifter" }).waitFor({ state: "visible" });
  const characterEquipmentActions = await m5Page.locator("#equipment-actions button").allInnerTexts();
  requireCondition(
    characterEquipmentActions.length === 1 && characterEquipmentActions[0].includes("Equip") &&
      !/Upgrade|Advance Rarity|Extract Modifiers|Affix|Sell|Dismantle/.test(characterEquipmentActions.join(" ")),
    `Character Equipment exposed vendor-only services: ${JSON.stringify(characterEquipmentActions)}`,
  );
  await clickVisibleOption(m5Page, "#equipment-options", "Back");
  await clickVisibleOption(m5Page, "#character-options", "Back");
  await clickVisibleOption(m5Page, "#overworld-options", "Vendors");
  await clickVisibleOption(m5Page, "#vendors-options", "Blacksmith");
  await m5Page.locator("#equipment-panel").waitFor({ state: "visible" });
  await selectM5Equipment("Field Helm");
  await m5ActionButton("Upgrade").click();
  await m5Page.locator("#notice").filter({ hasText: "Armor stats upgraded." }).waitFor({ state: "visible" });
  await m5ActionButton("Advance Rarity").click();
  await m5Page.locator("#notice").filter({ hasText: "Armor rarity advanced." }).waitFor({ state: "visible" });
  requireCondition(
    (await m5EquipmentButton("Field Helm").innerText()).includes("uncommon +1") &&
      (await m5Page.locator("#equipment-inspection-state").innerText()).includes("Equipped by Ser Branoc"),
    "armor upgrade/rarity advancement or exact-target equip did not update its owned instance",
  );
  await clickVisibleOption(m5Page, "#merchant-options", "Back");
  await clickVisibleOption(m5Page, "#vendors-options", "Back");
  await clickVisibleOption(m5Page, "#overworld-options", "Options");
  await clickVisibleOption(m5Page, "#overworld-options", "Save");
  await m5Page.locator("#notice").filter({ hasText: "Game saved." }).waitFor({ state: "visible" });
  await m5Page.reload({ waitUntil: "domcontentloaded" });
  await m5Page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(m5Page);
  await clickVisibleOption(m5Page, "#overworld-options", "Character");
  await m5CharacterEquipmentOption().waitFor({ state: "visible" });
  await m5CharacterEquipmentOption().click();
  await clickVisibleOption(m5Page, "#equipment-targets", "Ser Branoc, the Unbroken Crest");
  await selectM5Equipment("Field Helm");
  requireCondition(
    (await m5EquipmentButton("Field Helm").innerText()).includes("uncommon +1") &&
      (await m5Page.locator("#equipment-inspection-state").innerText()).includes("Equipped by Ser Branoc"),
    "armor ownership, investment, or rarity did not survive browser save/reload",
  );
  await clickVisibleOption(m5Page, "#equipment-targets", "Azhvielle, the Unconfessed");
  await selectM5Equipment("Field Helm");
  await m5ActionButton("Equip").click();
  await m5Page.locator("#notice").filter({ hasText: "assigned to the selected Drifter" }).waitFor({ state: "visible" });
  requireCondition(
    (await m5Page.locator("#equipment-inspection-state").innerText()).includes("Equipped by Azhvielle"),
    "equipment transfer did not target the selected Drifter",
  );

  for (const [name, forbiddenActions] of [
    ["Iron Ring", /Upgrade|Advance Rarity|Extract Modifiers|Affix|Sell|Dismantle/],
    ["Wayfinder Pendant", /Upgrade|Advance Rarity|Extract Modifiers|Affix|Sell|Dismantle/],
  ]) {
    await selectM5Equipment(name);
    const actions = await m5Page.locator("#equipment-actions button").allInnerTexts();
    requireCondition(
      actions.length === 1 && !forbiddenActions.test(actions.join(" ")) && actions[0].includes("Equip"),
      `${name} exposed armor-only or destructive actions: ${JSON.stringify(actions)}`,
    );
  }
  await clickVisibleOption(m5Page, "#equipment-options", "Back");
  await clickVisibleOption(m5Page, "#character-options", "Back");
  await clickVisibleOption(m5Page, "#overworld-options", "Vendors");
  await clickVisibleOption(m5Page, "#vendors-options", "Enchanter");
  await m5Page.locator("#equipment-panel").waitFor({ state: "visible" });
  await clickVisibleOption(m5Page, "#equipment-targets", "Ser Branoc, the Unbroken Crest");
  await selectM5Equipment("Field Helm");

  await m5ActionButton("Affix Vanguard").click();
  await m5Page.locator("#equipment-confirmation-content").waitFor({ state: "visible" });
  const replacementConfirmation = await m5Page.locator("#equipment-confirmation-content").innerText();
  requireCondition(
    replacementConfirmation.includes("Bastion") && replacementConfirmation.includes("permanently destroyed"),
    `modifier replacement omitted its destructive warning: ${replacementConfirmation}`,
  );
  await clickVisibleOption(m5Page, "#equipment-confirmation-options", "Cancel");
  requireCondition(
    (await m5Page.locator("#equipment-inspection-modifiers").innerText()).includes("Bastion") &&
      (await m5Page.locator("#equipment-modifiers").innerText()).includes("Vanguard"),
    "cancelling modifier replacement changed installed or loose modifiers",
  );
  await m5ActionButton("Affix Vanguard").click();
  await clickVisibleOption(m5Page, "#equipment-confirmation-options", "Confirm");
  await m5Page.locator("#notice").filter({ hasText: "Bastion was permanently destroyed." }).waitFor({ state: "visible" });
  requireCondition(
    (await m5Page.locator("#equipment-inspection-modifiers").innerText()).includes("Vanguard") &&
      !(await m5Page.locator("#equipment-modifiers").innerText()).includes("Vanguard"),
    "confirmed modifier replacement did not consume the incoming modifier and destroy the displaced one",
  );

  await selectM5Equipment("Field Chest");
  await m5ActionButton("Extract Modifiers").click();
  await m5Page.locator("#equipment-confirmation-content").waitFor({ state: "visible" });
  await m5Page.locator("#equipment-confirmation-title").filter({ hasText: "Extract" }).waitFor({ state: "visible" });
  const extractionConfirmation = await m5Page.locator("#equipment-confirmation-content").innerText();
  requireCondition(
    extractionConfirmation.includes("Ward") && extractionConfirmation.includes("Donor armor will be destroyed"),
    `modifier extraction did not explain its armor sacrifice: ${extractionConfirmation}`,
  );
  await clickVisibleOption(m5Page, "#equipment-confirmation-options", "Confirm");
  await m5Page.locator("#notice").filter({ hasText: "donor armor was destroyed" }).waitFor({ state: "visible" });
  requireCondition(
    !(await m5Page.locator("#equipment-inventory").innerText()).includes("Field Chest") &&
      (await m5Page.locator("#equipment-modifiers").innerText()).includes("Ward"),
    "confirmed extraction did not destroy the donor while preserving its modifier",
  );

  await clickVisibleOption(m5Page, "#equipment-options", "Back");
  await clickVisibleOption(m5Page, "#vendors-options", "Blacksmith");
  await m5Page.locator("#equipment-panel").waitFor({ state: "visible" });

  await selectM5Equipment("Field Gloves");
  await m5ActionButton("Sell").click();
  await m5Page.locator("#equipment-confirmation-content").waitFor({ state: "visible" });
  await m5Page.locator("#equipment-confirmation-title").filter({ hasText: "Sell" }).waitFor({ state: "visible" });
  const saleConfirmation = await m5Page.locator("#equipment-confirmation-content").innerText();
  requireCondition(
    saleConfirmation.includes("authored gold") &&
      saleConfirmation.includes("buyback during this Hub visit") &&
      saleConfirmation.includes("its modifiers remain available") &&
      saleConfirmation.includes("anything not recovered is discarded when the visit ends"),
    `modified armor sale did not warn of modifier loss: ${saleConfirmation}`,
  );
  await clickVisibleOption(m5Page, "#equipment-confirmation-options", "Confirm");
  await m5Page.locator("#notice").filter({ hasText: "available for buyback during this Hub visit" }).waitFor({ state: "visible" });
  requireCondition(
    !(await m5Page.locator("#equipment-inventory").innerText()).includes("Field Gloves") &&
      (await m5Page.locator("#hub-buyback-list").innerText()).includes("Field Gloves"),
    "selling modified armor did not move the exact instance into same-visit buyback escrow",
  );
  await clickVisibleOption(m5Page, "#hub-buyback-list", "Buy Back");
  await m5Page.locator("#hub-buyback-list").waitFor({ state: "hidden" });
  await selectM5Equipment("Field Gloves");
  requireCondition(
    (await m5Page.locator("#equipment-inspection-modifiers").innerText()).includes("Vanguard"),
    "same-visit equipment buyback did not restore the attached modifier",
  );

  await selectM5Equipment("Field Boots");
  await m5ActionButton("Dismantle").click();
  await m5Page.locator("#equipment-confirmation-content").waitFor({ state: "visible" });
  await m5Page.locator("#equipment-confirmation-title").filter({ hasText: "Dismantle" }).waitFor({ state: "visible" });
  const dismantleConfirmation = await m5Page.locator("#equipment-confirmation-content").innerText();
  requireCondition(
    dismantleConfirmation.includes("authored salvage") && dismantleConfirmation.includes("not returned") && dismantleConfirmation.includes("Bastion"),
    `modified armor dismantle did not warn of modifier loss: ${dismantleConfirmation}`,
  );
  await clickVisibleOption(m5Page, "#equipment-confirmation-options", "Confirm");
  await m5Page.locator("#notice").filter({ hasText: "Installed modifiers were destroyed." }).waitFor({ state: "visible" });
  requireCondition(
    !(await m5Page.locator("#equipment-inventory").innerText()).includes("Field Boots") &&
      !(await m5Page.locator("#equipment-modifiers").innerText()).includes("Bastion"),
    "dismantling modified armor returned or retained its installed modifier",
  );
  console.log("M5_BROWSER|ARMOR_PROGRESS_TRANSFER_RELOAD_ALCHEMIST_STATIC_ACCESSORIES|PASS");

  const m5OutingProfileKey = "dungeon-drifters.profile.v1.d4d4d4d4-0000-4000-8000-000000000001";
  await m5Page.goto(`${baseUrl}/`, { waitUntil: "domcontentloaded" });
  await m5Page.evaluate(({ key, envelope }) => localStorage.setItem(key, envelope), {
    key: m5OutingProfileKey,
    envelope: m5EquipmentFixtures.outing,
  });
  await m5Page.reload({ waitUntil: "domcontentloaded" });
  await m5Page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(m5Page);
  requireCondition(
    await m5Page.locator("#screen-badge").innerText() === "REST" &&
      await m5Page.locator("#location-label").innerText() === "Pre-Boss Rest",
    "the M5 safe-return fixture did not load at the Floor II Rest",
  );
  await clickVisibleOption(m5Page, "#overworld-options", "Extract");
  await m5Page.locator("#screen-badge").filter({ hasText: "EXTRACTION" }).waitFor({ state: "visible" });
  await clickVisibleOption(m5Page, "#overworld-options", "Return to Hub");
  await m5Page.locator("#screen-badge").filter({ hasText: "HUB" }).waitFor({ state: "visible" });
  await clickVisibleOption(m5Page, "#overworld-options", "Character");
  await m5CharacterEquipmentOption().waitFor({ state: "visible" });
  await m5CharacterEquipmentOption().click();
  await m5Page.locator("#equipment-panel").waitFor({ state: "visible" });
  requireCondition(
    (await m5Page.locator("#equipment-inventory").innerText()).includes("Secured") &&
      (await m5Page.locator("#equipment-inventory").innerText()).includes("Field Helm"),
    "safe extraction did not secure and retain the generated armor instance",
  );
  console.log("M5_BROWSER|GENERATED_ARMOR_SAFE_RETURN|PASS");

  const m6Page = await browser.newPage();
  m6Page.setDefaultNavigationTimeout(120000);
  m6Page.on("pageerror", (error) => errors.push(error.message));
  await m6Page.goto(`${baseUrl}/`, { waitUntil: "domcontentloaded" });
  const m6ProfileKey = "dungeon-drifters.profile.v1.d4d4d4d4-0000-4000-8000-000000000001";
  await m6Page.evaluate(({ key, envelope }) => localStorage.setItem(key, envelope), {
    key: m6ProfileKey,
    envelope: m6ExpeditionFixtures.hub,
  });
  await m6Page.reload({ waitUntil: "domcontentloaded" });
  await m6Page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(m6Page);
  await clickVisibleOption(m6Page, "#overworld-options", "Expeditions");
  await m6Page.locator("#expedition-panel").waitFor({ state: "visible" });
  await m6Page.locator("#expedition-energy").filter({ hasText: "Energy 100/100" }).waitFor({ state: "visible" });
  await clickVisibleOption(m6Page, "#expedition-reports", "Claim report");
  await m6Page.locator("#notice").filter({ hasText: "Expedition report claimed." }).waitFor({ state: "visible" });
  const claimedExpeditionProfile = await m6Page.evaluate((key) => {
    const envelope = JSON.parse(localStorage.getItem(key));
    return {
      claimed: envelope?.payload?.expedition?.reports?.[0]?.claimed,
      material: envelope?.payload?.party?.shared_items?.grade_ii_metal ?? 0,
    };
  }, m6ProfileKey);
  requireCondition(
    claimedExpeditionProfile.claimed === true && claimedExpeditionProfile.material === 1,
    `M6 report claim was not saved atomically: ${JSON.stringify(claimedExpeditionProfile)}`,
  );
  requireCondition(
    await m6Page.locator("#expedition-reports").getByRole("button", { name: "Claim report" }).count() === 0,
    "a claimed M6 report remained claimable",
  );
  console.log("M6_BROWSER|REPORT_CLAIM_ONCE|PASS");

  await clickVisibleOption(m6Page, "#overworld-options", "Prepare for Floor I");
  await m6Page.locator("#expedition-choices").waitFor({ state: "visible" });
  const materialChoice = m6Page.locator("#expedition-choices button").filter({ hasText: "Floor III | Material" });
  await materialChoice.waitFor({ state: "visible" });
  requireCondition(
    await m6Page.locator("#expedition-choices button").filter({ hasText: "Floor III | Equipment" }).isDisabled() &&
      await m6Page.locator("#expedition-choices button").filter({ hasText: "Floor III | Recovery" }).isDisabled(),
    "M6 offered an unavailable Equipment or Recovery assignment",
  );
  await materialChoice.click();
  await m6Page.locator("#expedition-confirmation-content").filter({ hasText: "The 20-minute timer starts when confirmed." }).waitFor({ state: "visible" });
  await clickVisibleOption(m6Page, "#overworld-options", "Cancel");
  await m6Page.locator("#notice").filter({ hasText: "Cancelled. No energy was spent." }).waitFor({ state: "visible" });
  await m6Page.locator("#expedition-energy").filter({ hasText: "Energy 100/100" }).waitFor({ state: "visible" });
  await materialChoice.click();
  await clickVisibleOption(m6Page, "#overworld-options", "Confirm Launch");
  await m6Page.locator("#battle-screen").waitFor({ state: "visible" });
  await m6Page.locator("#battle-expedition-status").filter({ hasText: "Floor III" }).waitFor({ state: "visible" });
  const launchedExpedition = await m6Page.evaluate((key) => {
    const envelope = JSON.parse(localStorage.getItem(key));
    return {
      energy: envelope?.payload?.expedition?.energy,
      destination: envelope?.payload?.expedition?.active_assignment?.destination_floor_id,
      partyPhase: envelope?.payload?.party?.phase,
    };
  }, m6ProfileKey);
  requireCondition(
    launchedExpedition.energy === 90 && launchedExpedition.destination === "floor_three" &&
      launchedExpedition.partyPhase === "outing",
    `M6 confirmed launch did not persist its energy and assignment: ${JSON.stringify(launchedExpedition)}`,
  );
  const liveStatusBeforeReload = await m6Page.locator("#battle-expedition-status").innerText();
  requireCondition(
    liveStatusBeforeReload.includes("Joruun Veyr") && liveStatusBeforeReload.includes("Zhaivra Kelyth") &&
      /\d{1,2}:\d{2} remaining/.test(liveStatusBeforeReload),
    `M6 battle did not show the passive assignment timer and pair: ${liveStatusBeforeReload}`,
  );
  const remainingBeforeIdle = (() => {
    const match = liveStatusBeforeReload.match(/(\d+):(\d{2}) remaining/);
    return match ? Number(match[1]) * 60 + Number(match[2]) : null;
  })();
  const assignmentBeforeIdle = await m6Page.evaluate((key) => {
    const assignment = JSON.parse(localStorage.getItem(key))?.payload?.expedition?.active_assignment;
    return assignment && {
      started_at_utc: assignment.started_at_utc,
      last_observed_at_utc: assignment.last_observed_at_utc,
      completed_at_utc: assignment.completed_at_utc,
    };
  }, m6ProfileKey);
  requireCondition(
    remainingBeforeIdle !== null && assignmentBeforeIdle?.completed_at_utc === null,
    `M6 idle countdown did not begin from an active assignment: ${liveStatusBeforeReload}`,
  );
  await m6Page.waitForFunction((previousRemaining) => {
    const text = document.getElementById("battle-expedition-status")?.textContent || "";
    const match = text.match(/(\d+):(\d{2}) remaining/);
    return match && Number(match[1]) * 60 + Number(match[2]) < previousRemaining;
  }, remainingBeforeIdle, { timeout: 5000 });
  const liveStatusAfterIdle = await m6Page.locator("#battle-expedition-status").innerText();
  const withoutClock = (status) => status.replace(
    /\d+:\d{2} remaining|complete; settles when the outing ends\.?/i,
    "[clock]",
  );
  const assignmentAfterIdle = await m6Page.evaluate((key) => {
    const assignment = JSON.parse(localStorage.getItem(key))?.payload?.expedition?.active_assignment;
    return assignment && {
      started_at_utc: assignment.started_at_utc,
      last_observed_at_utc: assignment.last_observed_at_utc,
      completed_at_utc: assignment.completed_at_utc,
    };
  }, m6ProfileKey);
  requireCondition(
    assignmentAfterIdle?.started_at_utc === assignmentBeforeIdle.started_at_utc &&
      assignmentAfterIdle?.last_observed_at_utc === assignmentBeforeIdle.last_observed_at_utc &&
      assignmentAfterIdle?.completed_at_utc === assignmentBeforeIdle.completed_at_utc,
    "M6 browser idle countdown changed persisted assignment state",
  );
  requireCondition(
    withoutClock(liveStatusAfterIdle) === withoutClock(liveStatusBeforeReload),
    "M6 browser idle countdown changed expedition details outside the clock",
  );
  console.log("M6_BROWSER|IDLE_COUNTDOWN_AUTHORITATIVE|PASS");

  await m6Page.reload({ waitUntil: "domcontentloaded" });
  await m6Page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(m6Page);
  await m6Page.locator("#expedition-live-status").filter({ hasText: "Floor III" }).waitFor({ state: "visible" });
  await clickVisibleOption(m6Page, "#route-actions", "Enter Encounter");
  await m6Page.locator("#battle-screen").waitFor({ state: "visible" });
  const liveStatusAfterReload = await m6Page.locator("#battle-expedition-status").innerText();
  requireCondition(
    liveStatusAfterReload.includes("Joruun Veyr") && liveStatusAfterReload.includes("Zhaivra Kelyth") &&
      /\d{1,2}:\d{2} remaining/.test(liveStatusAfterReload),
    `M6 active assignment did not survive save/reload: ${liveStatusAfterReload}`,
  );
  console.log("M6_BROWSER|PASSIVE_ASSIGNMENT_LAUNCH_RELOAD_STATUS|PASS");

  const m85Page = await browser.newPage();
  m85Page.setDefaultNavigationTimeout(120000);
  m85Page.on("pageerror", (error) => errors.push(error.message));
  await m85Page.goto(`${baseUrl}/`, { waitUntil: "domcontentloaded" });
  await m85Page.evaluate(({ key, envelope }) => localStorage.setItem(key, envelope), {
    key: m85ExpeditionFixture.profile_key,
    envelope: m85ExpeditionFixture.envelope,
  });
  await m85Page.reload({ waitUntil: "domcontentloaded" });
  await m85Page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(m85Page);
  await clickVisibleOption(m85Page, "#overworld-options", "Expeditions");
  await m85Page.locator("#expedition-panel").waitFor({ state: "visible" });
  const m85CategoryLabels = [
    "Material", "Equipment", "Recovery", "Scouting", "Story", "Elite",
  ];
  for (const category of m85CategoryLabels) {
    const row = m85Page.locator("#expedition-reports .expedition-report")
      .filter({ hasText: `Floor IV | ${category}` });
    await row.waitFor({ state: "visible" });
    await row.getByRole("button", { name: "Claim report" }).click();
    await row.getByText("Claimed", { exact: true }).waitFor({ state: "visible" });
    await m85Page.locator("#notice")
      .filter({ hasText: "Expedition report claimed." })
      .waitFor({ state: "visible" });
  }
  await m85Page.reload({ waitUntil: "domcontentloaded" });
  await m85Page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(m85Page);
  await clickVisibleOption(m85Page, "#overworld-options", "Expeditions");
  const m85ClaimState = await m85Page.evaluate((key) => {
    const payload = JSON.parse(localStorage.getItem(key))?.payload;
    const reports = payload?.expedition?.reports || [];
    const equipmentReport = reports.find((report) => report.category === "equipment");
    const frozenEquipment = equipmentReport?.frozen_outcome?.equipment_instance;
    const matchingEquipment = (payload?.party?.equipment_instances || []).filter(
      (instance) => instance.instance_id === frozenEquipment?.instance_id,
    );
    const items = payload?.party?.shared_items || {};
    const facts = payload?.story?.knowledge_facts || {};
    const eventIds = payload?.story?.completed_events || [];
    return {
      allClaimed: reports.length === 6 && reports.every((report) => report.claimed),
      material: items.grade_iv_metal || 0,
      recovery: items.healing_potion || 0,
      elite: items.grade_iv_cores || 0,
      equipmentMatches: matchingEquipment.length === 1 &&
        JSON.stringify(matchingEquipment[0]) === JSON.stringify(frozenEquipment),
      scoutingFacts: [
        "m8_fact_reliquary_threats",
        "m8_fact_ashen_vault",
        "m8_fact_ashen_regent",
      ].map((factId) => facts[factId]),
      storyRecorded: eventIds.includes("m8_story_reliquary_echo"),
      claimButtons: document.querySelectorAll("#expedition-reports button").length,
      energy: payload?.expedition?.energy,
    };
  }, m85ExpeditionFixture.profile_key);
  requireCondition(
    m85ClaimState.allClaimed && m85ClaimState.material === 1 &&
      m85ClaimState.recovery === 1 && m85ClaimState.elite === 1 &&
      m85ClaimState.equipmentMatches &&
      m85ClaimState.scoutingFacts.every((status) => status === "confirmed") &&
      m85ClaimState.storyRecorded && m85ClaimState.claimButtons === 0 &&
      m85ClaimState.energy === 100,
    `M8.5 report claims did not persist exactly once: ${JSON.stringify(m85ClaimState)}`,
  );
  console.log("M85_BROWSER|FLOOR_FOUR_REPORTS_CLAIM_RELOAD_ONCE|PASS");

  await clickVisibleOption(m85Page, "#overworld-options", "Back");
  await m85Page.locator("#screen-badge").filter({ hasText: "HUB" }).waitFor({ state: "visible" });
  const echoOption = m85Page.locator("#overworld-options button")
    .filter({ hasText: "Discuss the Reliquary Report" });
  requireCondition(
    await echoOption.count() === 1 && await echoOption.isEnabled(),
    "Claiming the Story report did not unlock the Hub Reliquary Echo scene",
  );
  await echoOption.click();
  await m85Page.locator("#screen-badge").filter({ hasText: "STORY" }).waitFor({ state: "visible" });
  const echoText = await m85Page.locator("#adventure-text").innerText();
  requireCondition(
    echoText.includes("two expedition members") &&
      echoText.includes("My answer to the report") &&
      echoText.includes("The report says they were frightened") &&
      !echoText.includes("I turned toward the passage"),
    `Reliquary Echo did not discuss the reported account without fixed eyewitnesses: ${echoText}`,
  );
  await clickVisibleOption(m85Page, "#overworld-options", "Finish Scene");
  await m85Page.waitForFunction((key) => {
    const events = JSON.parse(localStorage.getItem(key) || "null")
      ?.payload?.story?.completed_events || [];
    return events.includes("m8_reliquary_echo_scene");
  }, m85ExpeditionFixture.profile_key);
  await clickVisibleOption(m85Page, "#overworld-options", "Back");
  await m85Page.locator("#screen-badge").filter({ hasText: "HUB" }).waitFor({ state: "visible" });
  await m85Page.reload({ waitUntil: "domcontentloaded" });
  await m85Page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(m85Page);
  const echoAfterReload = await m85Page.evaluate((key) => {
    const events = JSON.parse(localStorage.getItem(key)).payload.story.completed_events;
    return {
      completions: events.filter(
        (eventId) => eventId === "m8_reliquary_echo_scene",
      ).length,
      actionCount: [...document.querySelectorAll("#overworld-options button")]
        .filter((button) => button.innerText.includes("Discuss the Reliquary Report"))
        .length,
    };
  }, m85ExpeditionFixture.profile_key);
  requireCondition(
    await m85Page.locator("#screen-badge").innerText() === "HUB" &&
      echoAfterReload.completions === 1 && echoAfterReload.actionCount === 0,
    `Reliquary Echo completion duplicated or returned after reload: ${JSON.stringify(echoAfterReload)}`,
  );
  console.log("M8.6_BROWSER|STORY_REPORT_ECHO_COMPLETION_RELOAD_ONCE|PASS");

  await clickVisibleOption(m85Page, "#overworld-options", "Expeditions");
  await clickVisibleOption(m85Page, "#overworld-options", "Prepare for Floor IV");
  await m85Page.locator("#expedition-choices").waitFor({ state: "visible" });
  for (const category of m85CategoryLabels) {
    const choice = m85Page.locator("#expedition-choices button")
      .filter({ hasText: `Floor IV | ${category}` });
    requireCondition(
      await choice.count() === 1 && await choice.isEnabled(),
      `Floor IV ${category} was not available in the browser assignment screen`,
    );
  }
  requireCondition(
    await m85Page.locator("#expedition-choices button")
      .filter({ hasText: "Floor V | Material" }).count() === 0,
    "Floor V Material appeared before a genuine Floor V clear and eligible source",
  );
  console.log("M85_BROWSER|FLOOR_FOUR_CATEGORY_AVAILABILITY|PASS");
  await clickVisibleOption(
    m85Page,
    "#expedition-choices",
    "Floor IV | Scouting",
  );
  await m85Page.locator("#expedition-confirmation-content")
    .filter({ hasText: "The 20-minute timer starts when confirmed." })
    .waitFor({ state: "visible" });
  await clickVisibleOption(m85Page, "#overworld-options", "Confirm Launch");
  await m85Page.waitForFunction((key) => {
    const payload = JSON.parse(localStorage.getItem(key))?.payload;
    return payload?.expedition?.energy === 90 &&
      payload?.expedition?.active_assignment?.category === "scouting" &&
      payload?.expedition?.active_assignment?.outing_floor_id === "floor_four" &&
      payload?.overworld?.active_route_id === "floor_four";
  }, m85ExpeditionFixture.profile_key);
  console.log("M85_BROWSER|FLOOR_FOUR_LAUNCH_AND_ENERGY|PASS");
  await m85Page.close();

  const m65Page = await browser.newPage();
  m65Page.setDefaultNavigationTimeout(120000);
  m65Page.on("pageerror", (error) => errors.push(error.message));
  await m65Page.goto(`${baseUrl}/`, { waitUntil: "domcontentloaded" });
  const m65ProfileKey = "dungeon-drifters.profile.v1.d4d4d4d4-0000-4000-8000-000000000001";
  await m65Page.evaluate(({ key, envelope }) => localStorage.setItem(key, envelope), {
    key: m65ProfileKey,
    envelope: m65ProfessionFixtures.hub,
  });
  await m65Page.reload({ waitUntil: "domcontentloaded" });
  await m65Page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(m65Page);

  await clickVisibleOption(m65Page, "#overworld-options", "Vendors");
  await clickVisibleOption(m65Page, "#vendors-options", "Alchemist");
  await m65Page.locator("#hub-economy-panel").waitFor({ state: "visible" });
  await m65Page.locator("#alchemy-progress").filter({ hasText: "Alchemy Level 1 | 0 XP" }).waitFor({ state: "visible" });
  const m65SupplyRow = (name) => m65Page.locator("#merchant-supplies .hub-supply-row")
    .filter({ hasText: name }).first();
  const m65UpdateSupply = async (name, action) => {
    const row = m65SupplyRow(name);
    const previous = await row.innerText();
    await row.getByRole("button", { name: action, exact: true }).click();
    await m65Page.waitForFunction(({ itemName, oldText }) => {
      const current = [...document.querySelectorAll("#merchant-supplies .hub-supply-row")]
        .find((candidate) => candidate.innerText.includes(itemName));
      return current && current.innerText !== oldText;
    }, { itemName: name, oldText: previous });
  };
  for (const itemName of ["Charcoal Powder", "Charcoal Powder", "Sulfur", "Sulfur", "Magic Reagent", "Aether Dust"]) {
    await m65UpdateSupply(itemName, "Buy");
  }
  const m65CraftAlchemy = async (name, expectedNotice) => {
    const row = m65Page.locator("#merchant-alchemy-recipes .merchant-row")
      .filter({ has: m65Page.locator("strong").getByText(name, { exact: true }) });
    requireCondition(await row.count() === 1, `M6.5 Alchemist did not offer ${name}`);
    await row.getByRole("button", { name: "Craft", exact: true }).click();
    await m65Page.locator("#notice").filter({ hasText: expectedNotice }).waitFor({ state: "visible" });
  };
  await m65CraftAlchemy("Smoke Bomb", "Crafted 1 Smoke Bomb; gained 15 Alchemy XP.");
  await m65CraftAlchemy("Smoke Bomb", "Crafted 1 Smoke Bomb; gained 15 Alchemy XP.");
  await m65CraftAlchemy("Mana Potion", "Crafted 1 Mana Potion; gained 20 Alchemy XP.");
  requireCondition(
    (await m65Page.locator("#alchemy-progress").innerText()).trim() === "Alchemy Level 2 | 50 XP",
    `Alchemy recipes did not award their authored profession progression: ${await m65Page.locator("#alchemy-progress").innerText()}`,
  );
  await clickVisibleOption(m65Page, "#hub-economy-options", "Back");
  await m65Page.locator("#hub-economy-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(m65Page, "#vendors-options", "Back");
  await clickVisibleOption(m65Page, "#overworld-options", "Hub Inventory");
  await m65Page.locator("#hub-economy-panel").waitFor({ state: "visible" });
  requireCondition(
    await m65SupplyRow("Mana Potion").innerText().then((text) => text.includes("Stored 1")),
    "crafted Mana Potion was not placed in secured Hub storage",
  );
  await m65UpdateSupply("Mana Potion", "Load");
  await clickVisibleOption(m65Page, "#hub-economy-options", "Back");
  await m65Page.locator("#hub-economy-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(m65Page, "#overworld-options", "Vendors");
  await clickVisibleOption(m65Page, "#vendors-options", "Enchanter");
  await m65Page.locator("#equipment-panel").waitFor({ state: "visible" });
  await m65Page.locator("#enchanting-progress").filter({ hasText: "Enchanting Level 1 | 0 XP" }).waitFor({ state: "visible" });
  requireCondition(
    (await m65Page.locator("#enchanting-known-affixes").innerText()).includes("Bastion | Grade I"),
    "Enchanter did not show the fixture's permanently learned Bastion recipe",
  );
  await clickVisibleOption(m65Page, "#equipment-targets", "Ser Branoc, the Unbroken Crest");
  await m65Page.locator("#equipment-inventory button").filter({ hasText: "Field Chest" }).click();
  await m65Page.locator("#equipment-actions button").filter({ hasText: "Apply Learned Bastion" }).click();
  await m65Page.locator("#notice").filter({ hasText: "Applied learned affix Bastion." }).waitFor({ state: "visible" });
  requireCondition(
    (await m65Page.locator("#equipment-inspection-modifiers").innerText()).includes("Bastion"),
    "Enchanter did not apply the learned Bastion recipe to Branoc's selected armor",
  );
  await clickVisibleOption(m65Page, "#equipment-options", "Back");
  await m65Page.locator("#equipment-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(m65Page, "#vendors-options", "Back");
  await clickVisibleOption(m65Page, "#overworld-options", "Options");
  await clickVisibleOption(m65Page, "#overworld-options", "Save");
  await m65Page.locator("#notice").filter({ hasText: "Game saved." }).waitFor({ state: "visible" });
  await m65Page.reload({ waitUntil: "domcontentloaded" });
  await m65Page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(m65Page);
  await clickVisibleOption(m65Page, "#overworld-options", "Vendors");
  await clickVisibleOption(m65Page, "#vendors-options", "Alchemist");
  await m65Page.locator("#alchemy-progress").filter({ hasText: "Alchemy Level 2 | 50 XP" }).waitFor({ state: "visible" });
  await clickVisibleOption(m65Page, "#hub-economy-options", "Back");
  await m65Page.locator("#hub-economy-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(m65Page, "#vendors-options", "Enchanter");
  await m65Page.locator("#equipment-panel").waitFor({ state: "visible" });
  requireCondition(
    (await m65Page.locator("#enchanting-progress").innerText()).trim() === "Enchanting Level 1 | 10 XP",
    "Enchanter progress did not survive save/reload",
  );
  console.log("M65_BROWSER|ALCHEMY_PROFESSION_RECIPE_FLOW|PASS");
  requireCondition(
    (await m65Page.locator("#enchanting-progress").innerText()).trim() === "Enchanting Level 1 | 10 XP" &&
      (await m65Page.locator("#enchanting-known-affixes").innerText()).includes("Bastion | Grade I"),
    "Enchanter progress or learned recipe did not survive save/reload",
  );
  await clickVisibleOption(m65Page, "#equipment-targets", "Ser Branoc, the Unbroken Crest");
  await m65Page.locator("#equipment-inventory button").filter({ hasText: "Field Chest" }).click();
  requireCondition(
    (await m65Page.locator("#equipment-inspection-modifiers").innerText()).includes("Bastion"),
    "the learned affix application did not survive save/reload",
  );
  console.log("M65_BROWSER|ENCHANTER_LEARNED_AFFIX_RELOAD|PASS");

  await clickVisibleOption(m65Page, "#equipment-options", "Back");
  await m65Page.locator("#equipment-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(m65Page, "#vendors-options", "Back");
  await clickVisibleOption(m65Page, "#overworld-options", "Items");
  await m65Page.locator("#items-panel").waitFor({ state: "visible" });
  await clickVisibleOption(m65Page, "#items-list", "Mana Potion x1 | Carried Pack");
  await clickVisibleOption(m65Page, "#items-options", "Use");
  await m65Page.locator("#items-title").filter({ hasText: "Choose a Drifter for Mana" }).waitFor({ state: "visible" });
  const manaTargets = m65Page.locator("#items-list button");
  const manaTargetLabels = await manaTargets.allInnerTexts();
  requireCondition(
    manaTargetLabels.length === 1 && manaTargetLabels[0].includes("Azhvielle, the Unconfessed | Mana 0/"),
    `Mana Potion targeting did not offer exactly the active Drifter who can benefit: ${JSON.stringify(manaTargetLabels)}`,
  );
  await manaTargets.first().click();
  await m65Page.locator("#notice").filter({ hasText: "Mana Potion restored" }).waitFor({ state: "visible" });
  requireCondition(
    (await m65Page.locator("#notice").innerText()).includes("to Azhvielle, the Unconfessed.") &&
      !(await m65Page.locator("#items-list").innerText()).includes("Mana Potion"),
    "Mana Potion did not restore the chosen active Drifter and consume exactly one carried potion",
  );
  await clickVisibleOption(m65Page, "#items-options", "Back");
  await m65Page.locator("#items-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(m65Page, "#overworld-options", "Options");
  await clickVisibleOption(m65Page, "#overworld-options", "Save");
  await m65Page.locator("#notice").filter({ hasText: "Game saved." }).waitFor({ state: "visible" });
  await m65Page.reload({ waitUntil: "domcontentloaded" });
  await m65Page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await continueSavedGameAfterReload(m65Page);
  await clickVisibleOption(m65Page, "#overworld-options", "Character");
  await m65Page.locator("#character-panel").waitFor({ state: "visible" });
  await clickVisibleOption(m65Page, "#character-targets", "Azhvielle, the Unconfessed");
  await m65Page.locator("#character-targets button[aria-pressed='true']")
    .filter({ hasText: "Azhvielle, the Unconfessed" }).waitFor();
  const azhvielleMana = (await m65Page.locator("#character-resources").innerText())
    .match(/Mana\s+(\d+)\/(\d+)/);
  requireCondition(
    azhvielleMana && Number(azhvielleMana[1]) > 0 && Number(azhvielleMana[1]) < Number(azhvielleMana[2]),
    `Mana Potion target recovery did not survive save/reload: ${await m65Page.locator("#character-resources").innerText()}`,
  );
  await clickVisibleOption(m65Page, "#character-options", "Back");
  await m65Page.locator("#character-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(m65Page, "#overworld-options", "Items");
  await m65Page.locator("#items-panel").waitFor({ state: "visible" });
  requireCondition(
    !(await m65Page.locator("#items-list").innerText()).includes("Mana Potion"),
    "consumed Mana Potion reappeared after save/reload",
  );
  console.log("M65_BROWSER|MANA_POTION_TARGETING|PASS");
  requireCondition(errors.length === 0, `M6.5 browser journey produced page errors: ${errors.join("; ")}`);
  await m65Page.close();

  const invalidSavePage = await browser.newPage();
  invalidSavePage.on("pageerror", (error) => errors.push(error.message));
  await invalidSavePage.goto(`${baseUrl}/`, { waitUntil: "domcontentloaded" });
  await invalidSavePage.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  const invalidProfileKey = "dungeon-drifters.profile.v1.d4d4d4d4-0000-4000-8000-000000000001";
  await invalidSavePage.evaluate((key) => localStorage.setItem(key, "not a profile envelope"), invalidProfileKey);
  await invalidSavePage.reload({ waitUntil: "domcontentloaded" });
  await invalidSavePage.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  await invalidSavePage.getByRole("button", { name: "Start" }).click();
  await invalidSavePage.locator("#save-unavailable-dialog").waitFor({ state: "visible" });
  await invalidSavePage.getByRole("button", { name: "Try Again" }).click();
  await invalidSavePage.locator("#save-unavailable-dialog").waitFor({ state: "visible" });
  await invalidSavePage.getByRole("button", { name: "Back" }).click();
  await invalidSavePage.getByRole("button", { name: "Start" }).waitFor({ state: "visible" });
  requireCondition(
    await invalidSavePage.evaluate((key) => localStorage.getItem(key), invalidProfileKey) ===
      "not a profile envelope",
    "startup recovery controls modified an invalid saved profile",
  );
  await invalidSavePage.getByRole("button", { name: "Start" }).click();
  await invalidSavePage.locator("#save-unavailable-dialog").waitFor({ state: "visible" });
  requireCondition(
    await invalidSavePage.locator("#selection-screen").isHidden() &&
      await invalidSavePage.locator("#save-unavailable-dialog").isVisible(),
    "an invalid existing save allowed startup to continue into New Game",
  );
  requireCondition(
    await invalidSavePage.evaluate((key) => localStorage.getItem(key), invalidProfileKey) ===
      "not a profile envelope",
    "starting with an invalid profile overwrote the original data",
  );
  console.log("F1_BROWSER|INVALID_SAVE_PRESERVED|PASS");
  await invalidSavePage.close();

  const qualification = page;
  qualification.on("pageerror", (error) => errors.push(error.message));
  qualification.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  await qualification.goto(`${baseUrl}/qualification/`, {
    waitUntil: "domcontentloaded",
  });
  await qualification.waitForFunction(
    () => {
      const output = document.getElementById("status").textContent;
      return output.includes("PYD2|PASS") || output.includes("PYD2|FAIL");
    },
    null,
    { timeout: 120000 },
  );
  const result = await qualification.locator("#status").innerText();
  requireCondition(result.includes("PYD2|PASS"), `Pyodide qualification failed: ${result}`);
  requireCondition(result.includes("Final node: surface_dungeon_entrance"), "route did not reach Dungeon Entrance");
  requireCondition(result.includes("Progression: L9 EXP 68 GP 24 Gold 75"), "route progression did not match oracle");
  requireCondition(result.includes("Hub: hub"), "full Pyodide route did not transition into the Hub");
  requireCondition(result.includes("Tutorial: 2 Drifters, 3 Goblins"), "full Pyodide route did not complete the two-Drifter tutorial Battle");
  requireCondition(result.includes("Extraction: 60 EXP each, 19 shared gold"), "full Pyodide route did not secure the first extraction");
  requireCondition(result.includes("Floor 1: 10 battles, personal XP awards 670 / 671, 115 shared gold"), "Pyodide did not complete and secure the full Floor 1 route");
  requireCondition(result.includes("FLOOR_ONE_BATTLE_10|PASS") && result.includes("FLOOR_ONE_BOSS_CLEAR|PASS"), "Pyodide qualification omitted the Floor 1 boss clear");
  requireCondition(result.includes("Replay: 50% EXP, 140 secured XP (70 / 70 awarded) | 21 gold, 136 shared gold"), "Pyodide did not qualify the early replay extraction");
  requireCondition(result.includes("FLOOR_ONE_REPLAY_MIDWAY_REST|PASS") && result.includes("FLOOR_ONE_REPLAY_EXTRACT|PASS"), "Pyodide qualification omitted the replay midway extraction");
  requireCondition(errors.length === 0, `browser page errors: ${errors.join("; ")}`);

  console.log("PYD7|PASS");
  console.log("PYD7|BROWSER|INITIAL_SESSION|PASS");
  console.log("PYD7|BROWSER|SEMANTIC_ROUND_TRIP|PASS");
  console.log("PYD7|BROWSER|MULTI_TARGET_PROJECTION|PASS");
  console.log("PYD7|BROWSER|RESULT_TO_OVERWORLD|PASS");
  console.log("PYD7|BROWSER|FULL_ROUTE|PASS");
  console.log("PYD7|BROWSER|FLOOR_ONE_FULL_CLEAR|PASS");
  console.log("PYD7|BROWSER|FLOOR_ONE_REPLAY_EXTRACTION|PASS");
  requireCondition(
    observedMomentumLabels.has("Neutral") &&
      [...observedMomentumLabels].some((label) => label.startsWith("Enemies +")) &&
      [...observedMomentumLabels].some((label) => label.startsWith("Drifters +")),
    `real browser combat did not render neutral control and meaningful shifts for both factions: ${JSON.stringify([...observedMomentumLabels])}`,
  );
  console.log("M7_BROWSER|MOMENTUM_BOTH_FACTIONS_AND_NEUTRAL|PASS");
} finally {
  await browser.close();
}
