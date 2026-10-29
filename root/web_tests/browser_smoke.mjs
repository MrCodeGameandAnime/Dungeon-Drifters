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

async function clickVisibleOption(page, containerSelector, label) {
  const buttons = page.locator(`${containerSelector} button`);
  for (let index = 0; index < await buttons.count(); index += 1) {
    const button = buttons.nth(index);
    const text = await button.locator(".choice-label").textContent().catch(() => null);
    if (text?.trim() === label && await button.isEnabled()) {
      await button.click();
      return;
    }
  }
  throw new Error(`offered control not found: ${label} in ${containerSelector}`);
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

const hubProjection = {
  screen: "hub",
  location_label: "Floor 1 Hub",
  adventure_text: "You have reached the Floor 1 Hub. Recruit one companion to continue.",
  options: [
    { action: "merchant", label: "Merchant", enabled: true, disabled_reason: null },
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
    { drifter_id: "azhvielle", display_name: "Azhvielle", archetype_label: "Black Mage | Elemental Controller", summary: "versatile, dangerous, unpredictable", cost: 65, enabled: true, disabled_reason: null },
    { drifter_id: "zhaivra", display_name: "Zhaivra Kelyth", archetype_label: "Rogue Archer | Alchemical Marksman", summary: "precise, prepared, resource-limited", cost: 65, enabled: true, disabled_reason: null },
    { drifter_id: "joruun", display_name: "Joruun Veyr", archetype_label: "Monk | Elemental Skirmisher", summary: "mobile, adaptable, physically costly", cost: 65, enabled: true, disabled_reason: null },
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
    { action: "merchant", label: "Merchant", enabled: true, disabled_reason: null },
    ...hubProjection.options.slice(2),
    { action: "start_floor_one", label: "Start Floor 1", enabled: true, disabled_reason: null },
  ],
};

const itemsProjection = {
  ...securedHubProjection,
  screen: "items",
  options: [
    { action: "inspect", label: "Inspect", enabled: false, disabled_reason: "no_item_selected" },
    { action: "back", label: "Back", enabled: true, disabled_reason: null },
  ],
  inventory: {
    items: [{ selection_key: "shared-item:goblin_scrap", display_name: "Goblin Scrap", quantity: 3, description: "Goblin remains suitable for dismantling.", overworld_use_enabled: false }],
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
  screen: "merchant",
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

const browserOptions = { headless: true };
if (process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH) {
  browserOptions.executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH;
}
const browser = await chromium.launch(browserOptions);
try {
  const page = await browser.newPage();
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
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });

  await page.route("**/favicon.ico", (route) =>
    route.fulfill({ status: 204, body: "" }),
  );
  await page.goto(`${baseUrl}/`, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 30000,
  }).catch(async (error) => {
    const startupError = await page.locator("#error-message").innerText().catch(() => "");
    throw new Error(startupError || errors.join("; ") || error.message);
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
  await page.locator("#restart").click();
  await page.locator("#selection-screen").waitFor({ state: "visible" });
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
  await page.locator("#restart").click();
  await page.locator("#selection-screen").waitFor({ state: "visible" });
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
      (await page.locator("#equipment-panel").innerText()).includes("Necklace") &&
      (await page.locator("#equipment-panel").innerText()).includes("Ring") &&
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

  await page.locator("#restart").click();
  await page.locator("#selection-screen").waitFor({ state: "visible" });
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
  await page.locator("#restart").click();
  await page.locator("#selection-screen").waitFor({ state: "visible" });
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
          if (source === "start_game_json(_selected_drifter_id)") {
            window.__fixtureSelectedDrifter = window.__fixtureGlobals._selected_drifter_id;
            window.__fixtureStartCalls.push(window.__fixtureSelectedDrifter);
            if (window.__fixtureAwaitingReselect) {
              window.__fixtureDefeatMode = false;
              window.__fixtureAwaitingReselect = false;
              window.__fixtureHubMode = false;
              return JSON.stringify(views.overworld);
            }
            return JSON.stringify(window.__fixtureHubMode ? views.hub : views.targets);
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
              if (window.__fixtureHubPhase === "securedHub" && command.action === "merchant") {
                window.__fixtureHubPhase = "merchant";
                return JSON.stringify(views.merchant);
              }
              if (window.__fixtureHubPhase === "merchant" && command.kind === "merchant_target" && command.drifter_id === "azhvielle") {
                return JSON.stringify(views.merchantAzhvielle);
              }
              if (window.__fixtureHubPhase === "merchant" && command.kind === "merchant_improve") {
                return JSON.stringify(views.merchantImproved);
              }
              if (window.__fixtureHubPhase === "merchant" && command.kind === "merchant_dismantle") {
                return JSON.stringify(views.merchantDismantled);
              }
              if (window.__fixtureHubPhase === "merchant" && command.kind === "merchant_craft_component") {
                return JSON.stringify(views.merchantCrafted);
              }
              if (window.__fixtureHubPhase === "merchant" && command.action === "back") {
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
              if (window.__fixtureHubPhase === "companion" && command.drifter_id === "azhvielle") {
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
    complete: completeProjection,
    overworld: resultOverworldProjection,
    hub: hubProjection,
    companion: companionProjection,
    partyReady: partyReadyProjection,
    partyBattle: partyBattleProjection,
    extraction: extractionProjection,
    securedHub: securedHubProjection,
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
  requireCondition(
    await targetPage.evaluate(() => window.__fixtureSelectedDrifter === "branoc"),
    "Drifter selection did not pass its authored ID to the Python bridge",
  );
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
  await targetPage.locator("#restart").click();
  await targetPage.locator("#selection-screen").waitFor({ state: "visible" });
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
      await targetPage.locator("#overworld-options button").count() === 6 &&
      !(await targetPage.getByRole("button", { name: "Recruit Companion" }).count()) &&
      !(await targetPage.getByRole("button", { name: "Ready / Set Out" }).count()),
    "returned Hub did not show secured currency or offer Floor 1",
  );
  const hubCommands = await targetPage.evaluate(() => window.__fixtureCommands);
  requireCondition(
    JSON.stringify(hubCommands) === JSON.stringify([
      { kind: "overworld_action", action: "recruit_companion" },
      { kind: "companion", drifter_id: "azhvielle" },
      { kind: "overworld_action", action: "ready" },
      { kind: "action", intent: "defend" },
      { kind: "overworld_action", action: "return_to_hub" },
    ]),
    `Hub flow did not submit existing semantic commands: ${JSON.stringify(hubCommands)}`,
  );
  console.log("PYD7|BROWSER|HUB_OUTING|PASS");

  await clickVisibleOption(targetPage, "#overworld-options", "Merchant");
  await targetPage.locator("#merchant-panel").waitFor({ state: "visible" });
  requireCondition(
    (await targetPage.locator("#merchant-weapon-name").innerText()) === "Sunder-Spire" &&
      await targetPage.locator("#merchant-targets button").count() === 2 &&
      await targetPage.locator("#merchant-slots .merchant-row").count() === 4 &&
      await targetPage.locator("#merchant-slots button:enabled").count() === 1 &&
      (await targetPage.locator("#merchant-dismantle").innerText()).includes("Goblin Scrap x3"),
    "Hub Merchant omitted the selected weapon, four slots, authoritative availability, or dismantle offer",
  );
  console.log("PYD8|BROWSER|HUB_MERCHANT|PASS");
  await clickVisibleOption(targetPage, "#merchant-targets", "Azhvielle");
  requireCondition(
    (await targetPage.locator("#merchant-weapon-name").innerText()) === "Needle of Plain Iron" &&
      (await targetPage.locator("#merchant-targets button[aria-pressed='true']").innerText()) === "Azhvielle",
    "Merchant target selection did not switch to the chosen companion's weapon",
  );
  await clickVisibleOption(targetPage, "#merchant-slots", "Improve");
  requireCondition(
    (await targetPage.locator("#merchant-slots .merchant-row").first().innerText()).includes("3/100") &&
      (await targetPage.locator("#merchant-crafting").innerText()).includes("20 XP"),
    "Merchant improvement did not render the authoritative slot and Crafting updates",
  );
  await clickVisibleOption(targetPage, "#merchant-dismantle", "Dismantle");
  requireCondition(
    (await targetPage.locator("#merchant-materials").innerText()).includes("Cord: 1") &&
      (await targetPage.locator("#merchant-dismantle").innerText()).includes("Goblin Scrap x2"),
    "Merchant dismantling did not render the authoritative materials and remaining loot",
  );
  requireCondition(
    (await targetPage.locator("#merchant-component-recipes").innerText()).includes("Obsidian Focus Fittings") &&
      await targetPage.locator("#merchant-component-recipes button:enabled").count() === 1,
    "Merchant did not show the available Grade-I component recipe",
  );
  await clickVisibleOption(targetPage, "#merchant-component-recipes", "Craft & Install");
  requireCondition(
    !(await targetPage.locator("#merchant-component-recipes").innerText()).includes("Obsidian Focus Fittings") &&
      (await targetPage.locator("#merchant-materials").innerText()).includes("Scrap metal: 1"),
    "Crafting and installing did not consume material and remove the installed recipe",
  );
  await clickVisibleOption(targetPage, "#merchant-options", "Back");
  await targetPage.locator("#merchant-panel").waitFor({ state: "hidden" });
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
      { kind: "overworld_action", action: "merchant" },
      { kind: "merchant_target", drifter_id: "azhvielle" },
      { kind: "merchant_improve", target_drifter_id: "azhvielle", slot_id: "focus_fittings" },
      { kind: "merchant_dismantle", target_drifter_id: "azhvielle", item_id: "goblin_scrap" },
      { kind: "merchant_craft_component", target_drifter_id: "azhvielle", component_id: "needle_focus_fitted" },
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
    (await targetPage.locator("#items-list").innerText()).includes("Goblin Scrap x3"),
    "Items page did not show the secured Goblin Scrap stack",
  );
  await clickVisibleOption(targetPage, "#items-list", "Goblin Scrap x3");
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

  await clickVisibleOption(targetPage, "#overworld-options", "Start Floor 1");
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
    fullFloorOneCommands.filter((command) => command.action === "start_floor_one").length === 2 &&
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
  await targetPage.locator("#restart").click();
  await targetPage.locator("#selection-screen").waitFor({ state: "visible" });
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

  const qualification = await browser.newPage();
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
  requireCondition(result.includes("Floor 1: 10 battles, 670 EXP each, 115 shared gold"), "Pyodide did not complete and secure the full Floor 1 route");
  requireCondition(result.includes("FLOOR_ONE_BATTLE_10|PASS") && result.includes("FLOOR_ONE_BOSS_CLEAR|PASS"), "Pyodide qualification omitted the Floor 1 boss clear");
  requireCondition(result.includes("Replay: 50% EXP, 140 EXP | 21 gold, 136 shared gold"), "Pyodide did not qualify the early replay extraction");
  requireCondition(result.includes("FLOOR_ONE_REPLAY_MIDWAY_REST|PASS") && result.includes("FLOOR_ONE_REPLAY_EXTRACT|PASS"), "Pyodide qualification omitted the replay midway extraction");
  requireCondition(errors.length === 0, `browser page errors: ${errors.join("; ")}`);

  await page.locator("#restart").click();
  await page.locator("#selection-screen").waitFor({ state: "visible" });
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
    timeout: 30000,
  });
  await page.getByRole("button", { name: "Start" }).click();
  await page.locator("#selection-screen").waitFor({ state: "visible" });
  await page.locator('#drifter-options [data-drifter-id="joruun"]').click();
  await page.locator("#overworld-screen").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#overworld-options", "Options");
  await clickVisibleOption(page, "#overworld-options", "Load");
  await page.waitForFunction(
    () => document.getElementById("screen-badge").textContent.trim() === "LOAD_CONFIRMATION",
  );
  await clickVisibleOption(page, "#overworld-options", "Confirm");
  await page.locator("#notice").filter({ hasText: "Saved session loaded." }).waitFor({ state: "visible" });
  await clickVisibleOption(page, "#overworld-options", "Character");
  await page.locator("#character-panel").waitFor({ state: "visible" });
  requireCondition(
    (await page.locator("#character-name").innerText()).includes("Ser Branoc") &&
      await page.locator("#location-label").innerText() === "Goblin Ambush",
    "browser reload and Load did not restore the saved Drifter and route",
  );
  requireCondition(errors.length === 0, `browser page errors after save/reload: ${errors.join("; ")}`);
  console.log("PYD7|BROWSER|SAVE_RELOAD|PASS");

  await page.locator("#restart").click();
  await page.locator("#selection-screen").waitFor({ state: "visible" });
  await page.keyboard.press("Shift+Alt+C");
  await page.locator("#shortcut-dialog").waitFor({ state: "visible" });
  await page.locator("#shortcut-code").fill("F01BA");
  await page.locator('#shortcut-form button[type="submit"]').click();
  await page.locator("#overworld-screen").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#overworld-options", "Merchant");
  await page.locator("#merchant-panel").waitFor({ state: "visible" });
  const branocMerchantTarget = page.locator("#merchant-targets button").filter({ hasText: "Ser Branoc" });
  await branocMerchantTarget.click();

  const scrapMetalCount = async () => {
    const text = await page.locator("#merchant-materials").innerText();
    return Number(text.match(/Scrap metal:\s*(\d+)/i)?.[1] || 0);
  };
  const scrapRow = page.locator("#merchant-dismantle .merchant-row").filter({ hasText: "Goblin Scrap" });
  requireCondition(await scrapRow.count() === 1, "weapon save/reload scenario did not provide Goblin Scrap");
  for (let attempt = 0; attempt < 30 && await scrapMetalCount() < 2; attempt += 1) {
    const previous = await page.locator("#merchant-dismantle").innerText();
    await scrapRow.getByRole("button", { name: "Dismantle" }).click();
    await page.waitForFunction((prior) =>
      document.getElementById("merchant-dismantle").innerText !== prior,
    previous);
  }
  requireCondition(await scrapMetalCount() >= 2, "Goblin Scrap did not yield enough metal to craft and improve Branoc's weapon");

  const bladeRecipe = page.locator("#merchant-component-recipes .merchant-row")
    .filter({ hasText: "Reinforced Blade and Guard" });
  const craftingBeforeRecipe = await page.locator("#merchant-crafting").innerText();
  const materialsBeforeRecipe = await page.locator("#merchant-materials").innerText();
  await bladeRecipe.getByRole("button", { name: "Craft & Install" }).click();
  await page.waitForFunction(({ crafting, materials }) =>
    document.getElementById("merchant-crafting").innerText !== crafting &&
      document.getElementById("merchant-materials").innerText !== materials &&
      !document.getElementById("merchant-component-recipes").innerText.includes("Reinforced Blade and Guard"),
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
  await clickVisibleOption(page, "#overworld-options", "Merchant");
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
  await clickVisibleOption(page, "#overworld-options", "Options");
  await page.waitForFunction(
    () => document.getElementById("screen-badge").textContent.trim() === "OPTIONS",
  );
  await clickVisibleOption(page, "#overworld-options", "Save");
  await page.locator("#notice").filter({ hasText: "Game saved." }).waitFor({ state: "visible" });
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 30000,
  });
  await page.getByRole("button", { name: "Start" }).click();
  await page.locator("#selection-screen").waitFor({ state: "visible" });
  await page.locator('#drifter-options [data-drifter-id="joruun"]').click();
  await page.locator("#overworld-screen").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#overworld-options", "Options");
  await clickVisibleOption(page, "#overworld-options", "Load");
  await page.waitForFunction(
    () => document.getElementById("screen-badge").textContent.trim() === "LOAD_CONFIRMATION",
  );
  await clickVisibleOption(page, "#overworld-options", "Confirm");
  await page.locator("#notice").filter({ hasText: "Saved session loaded." }).waitFor({ state: "visible" });
  const restoredHubState = {
    location: await page.locator("#location-label").innerText(),
    adventure: await page.locator("#adventure-text").innerText(),
    badge: await page.locator("#screen-badge").innerText(),
    notice: await page.locator("#notice").innerText(),
  };
  requireCondition(
    restoredHubState.location === "Floor 1 Hub",
    `browser reload and Load did not restore Branoc's weapon progression: ${JSON.stringify(restoredHubState)}`,
  );
  await clickVisibleOption(page, "#overworld-options", "Character");
  await page.locator("#character-panel").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#character-options", "Weapon");
  await page.locator("#weapon-panel").waitFor({ state: "visible" });
  const loadedWeaponTarget = page.locator("#weapon-targets button").filter({ hasText: "Ser Branoc" });
  await loadedWeaponTarget.click();
  const loadedBladeState = await page.locator("#weapon-components .weapon-component-slot").first().innerText();
  requireCondition(
    loadedBladeState.includes("Installed: Reinforced Blade and Guard") &&
      loadedBladeState === installedBladeState,
    "browser reload and Load did not restore Branoc's weapon progression: installed component changed",
  );
  await clickVisibleOption(page, "#weapon-options", "Back");
  await page.locator("#character-panel").waitFor({ state: "visible" });
  await clickVisibleOption(page, "#character-options", "Back");
  await page.locator("#character-panel").waitFor({ state: "hidden" });
  await clickVisibleOption(page, "#overworld-options", "Merchant");
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

  console.log("PYD7|PASS");
  console.log("PYD7|BROWSER|INITIAL_SESSION|PASS");
  console.log("PYD7|BROWSER|SEMANTIC_ROUND_TRIP|PASS");
  console.log("PYD7|BROWSER|MULTI_TARGET_PROJECTION|PASS");
  console.log("PYD7|BROWSER|RESULT_TO_OVERWORLD|PASS");
  console.log("PYD7|BROWSER|FULL_ROUTE|PASS");
  console.log("PYD7|BROWSER|FLOOR_ONE_FULL_CLEAR|PASS");
  console.log("PYD7|BROWSER|FLOOR_ONE_REPLAY_EXTRACTION|PASS");
} finally {
  await browser.close();
}
