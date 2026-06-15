import { defineConfig, devices } from "@playwright/test";

const hubEnv = {
  SUPABASE_URL: "https://example.supabase.co",
  SUPABASE_KEY: "test-supabase-key",
  OPENROUTER_API_KEY: "test-openrouter-key",
  HUB_API_KEY: "test-hub-key-for-ci",
  ENVIRONMENT: "development",
  ADMIN_COSTS_PAGE_ENABLED: "1",
  ADMIN_EVENTS_PAGE_ENABLED: "1",
  ADMIN_AB_TEST_PAGE_ENABLED: "1",
  BRIEFING_COO_SECTION_ENABLED: "1",
  GDD_MANAGER_ENABLED: "1",
};

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: process.env.CI ? "github" : "list",
  timeout: 60_000,
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: "python -m uvicorn api.main:app --host 127.0.0.1 --port 8001",
      cwd: "..",
      url: "http://127.0.0.1:8001/health",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: hubEnv,
    },
    {
      command: "npm run dev",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ...hubEnv,
        HUB_API_BACKEND_URL: "http://127.0.0.1:8001",
        PORT: "3000",
      },
    },
  ],
});
