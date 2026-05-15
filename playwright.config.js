// Playwright config — issue #72.
//
// Scope: a single chromium project pointed at the Vite dev server.
// The dev server is auto-started by Playwright with VITE_STT_STREAMING=1
// so the streaming UI is enabled. Backend isn't started here; the specs
// mock every backend call via `page.route()` so they run offline.

import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",

  use: {
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
    // Grant microphone permission preemptively so the AudioContext
    // mock-out (in the spec's addInitScript) doesn't trip on a real
    // permission prompt that headless Chromium would otherwise stall
    // on. The spec stubs getUserMedia anyway — the permission is just
    // a belt-and-braces for navigator.permissions checks.
    permissions: ["microphone"],
  },

  webServer: {
    command: "npm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
    env: {
      // Turn the streaming UI on for the duration of the E2E run.
      VITE_STT_STREAMING: "1",
    },
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
