import { test, expect } from "@playwright/test";
import path from "path";
import fs from "fs";

const SCREENSHOT_DIR = path.join(__dirname, "..", "screenshots");

test.beforeAll(() => {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
});

test.describe("Loading and Error States", () => {
  test("shows loading state during generation", async ({ page }) => {
    await page.goto("http://localhost:3000");

    // Mock a slow API response
    await page.route("**/api/generate", async (route) => {
      await new Promise((r) => setTimeout(r, 2000));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          notebook: {
            nbformat: 4,
            nbformat_minor: 5,
            metadata: {},
            cells: [
              { cell_type: "markdown", source: "# Done", metadata: {} },
            ],
          },
        }),
      });
    });

    // Fill and submit
    await page.getByTestId("api-key-input").fill("sk-test-key");
    await page
      .getByTestId("pdf-file-input")
      .setInputFiles(path.join(__dirname, "..", "fixtures", "test.pdf"));
    await page.getByTestId("submit-button").click();

    // Should show loading spinner and skeleton
    await expect(page.getByTestId("loading-spinner")).toBeVisible();
    await expect(page.getByTestId("loading-state")).toBeVisible();

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "task10-01-loading-state.png"),
    });

    // Wait for it to complete
    await expect(page.getByTestId("notebook-preview")).toBeVisible({
      timeout: 10000,
    });
    await expect(page.getByTestId("loading-state")).not.toBeVisible();
  });

  test("shows error message on API failure", async ({ page }) => {
    await page.goto("http://localhost:3000");

    // Mock a failed API response
    await page.route("**/api/generate", async (route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Invalid OpenAI API key." }),
      });
    });

    // Fill and submit
    await page.getByTestId("api-key-input").fill("sk-bad-key");
    await page
      .getByTestId("pdf-file-input")
      .setInputFiles(path.join(__dirname, "..", "fixtures", "test.pdf"));
    await page.getByTestId("submit-button").click();

    // Should show error
    await expect(page.getByTestId("error-message")).toBeVisible({
      timeout: 5000,
    });
    await expect(page.getByTestId("error-message")).toContainText(
      "Invalid OpenAI API key"
    );

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "task10-02-error-state.png"),
    });

    // Loading should be gone, no notebook preview
    await expect(page.getByTestId("loading-state")).not.toBeVisible();
    await expect(page.getByTestId("notebook-preview")).not.toBeVisible();
  });

  test("page is responsive on smaller viewport", async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto("http://localhost:3000");

    await expect(page.getByTestId("page-title")).toBeVisible();
    await expect(page.getByTestId("api-key-input")).toBeVisible();
    await expect(page.getByTestId("pdf-dropzone")).toBeVisible();

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "task10-03-responsive.png"),
    });
  });
});
