import { test, expect } from "@playwright/test";
import path from "path";
import fs from "fs";

const SCREENSHOT_DIR = path.join(__dirname, "..", "screenshots");

test.beforeAll(() => {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
});

test.describe("Notebook Preview", () => {
  test("renders notebook preview with markdown and code cells", async ({
    page,
  }) => {
    await page.goto("http://localhost:3000");

    // Inject a mock notebook directly via page.evaluate
    await page.evaluate(() => {
      // Simulate notebook state by calling the React state setter
      // We'll use a different approach: intercept the fetch to return mock data
    });

    // Instead, we'll intercept the API call
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
              {
                cell_type: "markdown",
                source: "# Test Tutorial\n\nThis is a test notebook.",
                metadata: {},
              },
              {
                cell_type: "code",
                source: "import numpy as np\nprint('hello')",
                metadata: {},
                outputs: [],
                execution_count: null,
              },
              {
                cell_type: "markdown",
                source: "## Results\n\nHere are the results.",
                metadata: {},
              },
              {
                cell_type: "code",
                source:
                  "import matplotlib.pyplot as plt\nplt.plot([1,2,3])\nplt.show()",
                metadata: {},
                outputs: [],
                execution_count: null,
              },
            ],
          },
        }),
      });
    });

    // Fill the form and submit
    await page.getByTestId("api-key-input").fill("sk-test-key");
    const fileInput = page.getByTestId("pdf-file-input");
    await fileInput.setInputFiles(
      path.join(__dirname, "..", "fixtures", "test.pdf")
    );
    await page.getByTestId("submit-button").click();

    // Wait for the preview to appear
    await expect(page.getByTestId("notebook-preview")).toBeVisible({
      timeout: 5000,
    });

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "task8-01-notebook-preview.png"),
      fullPage: true,
    });

    // Check markdown cells rendered
    const markdownCells = page.getByTestId("markdown-cell");
    await expect(markdownCells.first()).toBeVisible();
    expect(await markdownCells.count()).toBe(2);

    // Check code cells rendered
    const codeCells = page.getByTestId("code-cell");
    await expect(codeCells.first()).toBeVisible();
    expect(await codeCells.count()).toBe(2);
  });
});
