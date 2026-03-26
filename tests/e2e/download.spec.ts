import { test, expect } from "@playwright/test";
import path from "path";
import fs from "fs";

const SCREENSHOT_DIR = path.join(__dirname, "..", "screenshots");

test.beforeAll(() => {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
});

test.describe("Download Notebook", () => {
  test("download button appears after generation and triggers download", async ({
    page,
  }) => {
    await page.goto("http://localhost:3000");

    // Mock the API response
    await page.route("**/api/generate", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          notebook: {
            nbformat: 4,
            nbformat_minor: 5,
            metadata: {},
            cells: [
              { cell_type: "markdown", source: "# Test", metadata: {} },
              {
                cell_type: "code",
                source: "print('hello')",
                metadata: {},
                outputs: [],
                execution_count: null,
              },
            ],
          },
        }),
      });
    });

    // Fill form and submit
    await page.getByTestId("api-key-input").fill("sk-test-key");
    await page
      .getByTestId("pdf-file-input")
      .setInputFiles(path.join(__dirname, "..", "fixtures", "test.pdf"));
    await page.getByTestId("submit-button").click();

    // Wait for download button
    const downloadBtn = page.getByTestId("download-button");
    await expect(downloadBtn).toBeVisible({ timeout: 5000 });
    await expect(downloadBtn).toContainText("Download Notebook");

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "task9-01-download-button.png"),
    });

    // Click and verify download is triggered
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      downloadBtn.click(),
    ]);

    expect(download.suggestedFilename()).toBe(
      "paper2notebook_tutorial.ipynb"
    );

    // Verify the downloaded content is valid JSON with notebook structure
    const downloadPath = await download.path();
    if (downloadPath) {
      const content = fs.readFileSync(downloadPath, "utf-8");
      const parsed = JSON.parse(content);
      expect(parsed.nbformat).toBe(4);
      expect(parsed.cells).toBeDefined();
    }
  });
});
