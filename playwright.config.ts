import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/ui",
  fullyParallel: true,
  use: {
    baseURL: "http://127.0.0.1:4173",
    browserName: "chromium",
    channel: "chrome",
  },
  webServer: {
    command: "npm run dev -- --host 127.0.0.1 --port 4173",
    env: { VITE_BASE_PATH: "/rts/" },
    port: 4173,
    reuseExistingServer: false,
  },
});
