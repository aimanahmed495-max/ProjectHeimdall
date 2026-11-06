const { test, expect } = require("@playwright/test");

test("operator can register, log in, load records, and sign out", async ({
  page,
}) => {
  const username = `operator_${Date.now()}`;
  const password = "Prototype3!Pass123";

  await page.goto("/");

await page.locator("iframe").first().waitFor({
  state: "attached",
});

const consoleFrame = page.frameLocator("iframe").first();
  await consoleFrame.locator("#authUsername").fill(username);
  await consoleFrame.locator("#authPassword").fill(password);
  await consoleFrame.locator("#registerButton").click();

  await expect(consoleFrame.locator("#authMessage")).toContainText(
    "Account created"
  );

  await consoleFrame.locator("#authPassword").fill(password);
  await consoleFrame.locator("#loginButton").click();

  await expect(consoleFrame.locator("#authGate")).toBeHidden();

  await expect(consoleFrame.locator("#coreApiStatus")).toContainText(
    "Connected"
  );

  await expect(consoleFrame.locator("#coreApiRecords")).toContainText(
    "events"
  );
  await consoleFrame.locator('[data-view="history"]').click();
  await expect(consoleFrame.locator("#viewHistory")).toBeVisible();

  const historyRows = consoleFrame.locator("#hBody tr[data-row]");
  await expect(historyRows.first()).toBeVisible();
  const initialRowCount = await historyRows.count();
  expect(initialRowCount).toBeGreaterThan(0);

  const statusFilter = consoleFrame.locator("#hStatus");
  const statusOptions = await statusFilter.locator("option").evaluateAll(
    options => options.map(option => option.value)
  );

  expect(statusOptions).toEqual([
    "",
    "Pending",
    "Corroborated",
    "Resolved",
  ]);

  await statusFilter.selectOption("Pending");

  const displayedStatuses = await consoleFrame
    .locator("#hBody tr[data-row] td:nth-child(7)")
    .allTextContents();

  expect(displayedStatuses.length).toBeGreaterThan(0);
  expect(displayedStatuses.every(status => status === "Pending")).toBe(true);

  await consoleFrame.locator("#hReset").click();
  await expect(statusFilter).toHaveValue("");
  await expect(historyRows.first()).toBeVisible();
  expect(await historyRows.count()).toBeGreaterThan(0);
  await consoleFrame.locator("#logoutButton").click();
  await expect(consoleFrame.locator("#authGate")).toBeVisible();
});