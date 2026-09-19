import { chromium } from "playwright";

const baseUrl = (process.argv[2] || "http://127.0.0.1:8765").replace(/\/$/, "");
const errors = [];

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
  requireCondition(
    (await page.locator("#moves button").count()) > 0 &&
      (await page.locator("#moves button").filter({ hasText: "Back" }).count()) === 1,
    "Move Selection choices or Back control are missing",
  );

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
