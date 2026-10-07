import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "tests/e2e", fullyParallel: false, workers: 1,
  webServer: process.env.CI ? [
    { command: "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log", url: "http://127.0.0.1:8000/health/ready", reuseExistingServer: false },
    { command: "npm run start --workspace apps/web", url: "http://localhost:3000", reuseExistingServer: false },
  ] : undefined,
  use: { baseURL: "http://localhost:3000", trace: "retain-on-failure", screenshot: "only-on-failure" },
  projects: [
    { name: "desktop", use: { channel: process.env.CI ? "chromium" : "msedge", viewport: { width: 1440, height: 960 } } },
    { name: "mobile", use: { ...devices["iPhone 13"], defaultBrowserType: "chromium", channel: process.env.CI ? "chromium" : "msedge" } },
  ],
});
