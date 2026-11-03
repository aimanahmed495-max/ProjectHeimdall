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

  await consoleFrame.locator("#logoutButton").click();
  await expect(consoleFrame.locator("#authGate")).toBeVisible();
});