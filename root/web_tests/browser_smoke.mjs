import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

const baseUrl = (process.argv[2] || "http://127.0.0.1:8765").replace(/\/$/, "");
const errors = [];
const screenshotDirectory = path.join(os.tmpdir(), "dd-pd-ui3-evidence");
await mkdir(screenshotDirectory, { recursive: true });

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
    metrics.activePhases.join(",") === expectedPhase,
    `${label} changed the active interaction phase: ${JSON.stringify(metrics.activePhases)}`,
  );
  return metrics;
}

async function controlSignature(page) {
  return page.locator("#actions button").evaluateAll((buttons) => buttons.map((button) => ({
    label: button.querySelector(".choice-label")?.textContent || button.textContent.trim(),
    disabled: button.disabled,
    reason: button.querySelector(".option-reason")?.textContent || "",
  })));
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

function requireCondition(condition, message) {
  if (!condition) throw new Error(message);
}

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1440, height: 900 });
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });

  await page.goto(`${baseUrl}/`, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 30000,
  }).catch(async (error) => {
    const startupError = await page.locator("#error-message").innerText().catch(() => "");
    throw new Error(startupError || errors.join("; ") || error.message);
  });
  requireCondition(
    await page.getByRole("heading", { name: "Browser Playtest" }).isVisible(),
    "browser shell did not render",
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
  await captureScreenshot(page, "desktop-overworld");

  await page.getByRole("button", { name: "Enter Encounter" }).click();
  await page.locator("#overworld-screen").waitFor({ state: "hidden" });
  await page.locator("#battle-screen").waitFor({ state: "visible" });
  requireCondition(
    !(await page.locator("#overworld-screen").isVisible()) &&
      await page.locator("#battle-screen").isVisible(),
    "entering an encounter did not replace the Overworld with the Battle surface",
  );

  const battleOrder = await page.evaluate(() => {
    const ids = ["battle-status", "battle-matchup", "battle-log", "controls-panel", "super-meter"];
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
  requireCondition(
    !(await page.locator("#route-panel").isVisible()) &&
      !(await page.locator("#completion").isVisible()),
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

  await page.getByRole("button", { name: "Restart" }).click();
  await page.locator("#overworld-screen").waitFor({ state: "visible" });
  requireCondition(await page.getByRole("button", { name: "Enter Encounter" }).isVisible(), "Restart did not restore the initial Overworld");
  await page.evaluate(async () => {
    if (document.fullscreenElement) await document.exitFullscreen();
  });
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
  targetPage.on("pageerror", (error) => errors.push(error.message));
  await targetPage.route("**/pyodide.js", (route) =>
    route.fulfill({ status: 200, contentType: "application/javascript", body: "" }),
  );
  await targetPage.addInitScript((views) => {
    window.__fixtureCommands = [];
    window.__fixtureGlobals = {};
    window.__fixtureTransitionComplete = false;
    window.loadPyodide = async () => ({
      FS: { writeFile() {} },
      globals: { set(key, value) { window.__fixtureGlobals[key] = value; } },
      runPython() {},
      async runPythonAsync(source) {
        if (source === "current_view_json()") {
          return JSON.stringify(window.__fixtureTransitionComplete ? views.overworld : views.targets);
        }
        if (source === "restart_game_json()") return JSON.stringify(views.targets);
        if (source === "submit_json(_browser_command_json)") {
          window.__fixtureCommands.push(JSON.parse(window.__fixtureGlobals._browser_command_json));
          window.__fixtureTransitionComplete = true;
          return JSON.stringify(views.complete);
        }
        return "null";
      },
    });
  }, {
    targets: targetProjection,
    complete: completeProjection,
    overworld: resultOverworldProjection,
  });
  await targetPage.goto(`${baseUrl}/`, { waitUntil: "domcontentloaded" });
  await targetPage.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, { timeout: 30000 });
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

  const qualification = await browser.newPage();
  qualification.on("pageerror", (error) => errors.push(error.message));
  qualification.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  await qualification.goto(`${baseUrl}/qualification/`, {
    waitUntil: "domcontentloaded",
  });
  await qualification.waitForFunction(
    () => document.getElementById("status").textContent.includes("PYD2|PASS"),
    null,
    { timeout: 120000 },
  );
  const result = await qualification.locator("#status").innerText();
  requireCondition(result.includes("Final node: surface_dungeon_entrance"), "route did not reach Dungeon Entrance");
  requireCondition(result.includes("Progression: L9 EXP 68 GP 24 Gold 75"), "route progression did not match oracle");
  requireCondition(errors.length === 0, `browser page errors: ${errors.join("; ")}`);

  console.log("PYD7|PASS");
  console.log("PYD7|BROWSER|INITIAL_SESSION|PASS");
  console.log("PYD7|BROWSER|SEMANTIC_ROUND_TRIP|PASS");
  console.log("PYD7|BROWSER|MULTI_TARGET_PROJECTION|PASS");
  console.log("PYD7|BROWSER|RESULT_TO_OVERWORLD|PASS");
  console.log("PYD7|BROWSER|FULL_ROUTE|PASS");
  console.log("PYD7|BROWSER|COMPLETION_SIGNAL|PASS");
} finally {
  await browser.close();
}
