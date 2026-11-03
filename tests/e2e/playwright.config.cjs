const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: ".",
  testMatch: "*.spec.js",
  timeout: 60000,
  expect: {
    timeout: 15000,
  },
  use: {
    baseURL: process.env.FRONTEND_URL || "http://127.0.0.1:8501",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  reporter: process.env.CI
    ? [["line"], ["html", { open: "never" }]]
    : "list",
});