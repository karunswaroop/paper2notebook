import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  timeout: 30000,
  use: {
    baseURL: "http://localhost:3000",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: "npm run dev",
    cwd: "../../frontend",
    port: 3000,
    reuseExistingServer: true,
    timeout: 30000,
  },
});
