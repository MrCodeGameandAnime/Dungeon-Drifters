import { chromium } from "playwright";

const baseUrl = (process.argv[2] || "http://127.0.0.1:8765").replace(/\/$/, "");
const errors = [];

function requireCondition(condition, message) {
  if (!condition) throw new Error(message);
}

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  page.on("pageerror", (error) => errors.push(error.message));

  await page.goto(`${baseUrl}/`, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__DD_BROWSER_READY__ === true, null, {
    timeout: 120000,
  });
  requireCondition(
    await page.getByRole("heading", { name: "Browser Playtest" }).isVisible(),
    "browser shell did not render",
  );
  await page.getByRole("button", { name: "Enter Encounter" }).click();
  await page.getByRole("button", { name: "Attack" }).click();
  await page.locator("#moves button:not(:disabled)").first().click();
  const targets = page.locator("#targets button:not(:disabled)");
  if (await targets.count()) await targets.first().click();
  requireCondition(
    ["BATTLE", "MAIN"].includes(await page.locator("#screen-badge").innerText()),
    "semantic input did not return an authoritative screen",
  );

  const qualification = await browser.newPage();
  qualification.on("pageerror", (error) => errors.push(error.message));
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
  console.log("PYD7|BROWSER|FULL_ROUTE|PASS");
  console.log("PYD7|BROWSER|COMPLETION_SIGNAL|PASS");
} finally {
  await browser.close();
}
