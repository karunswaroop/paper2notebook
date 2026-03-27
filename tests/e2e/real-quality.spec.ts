import { test, expect } from "@playwright/test";
import path from "path";
import fs from "fs";

const SCREENSHOT_DIR = path.join(__dirname, "..", "screenshots", "real-quality");

/**
 * Real Quality Test — "Attention Is All You Need"
 *
 * This test opens a visible browser, pauses for the user to enter their
 * real API key, generates a notebook from the paper, and validates the output.
 *
 * Run with: REAL_TEST=true npx playwright test real-quality --headed
 *
 * Skipped in CI (no REAL_TEST env var).
 */

const isRealTest = process.env.REAL_TEST === "true";

test.describe("Real Quality Test", () => {
  test.describe.configure({ mode: "serial", timeout: 180_000 });

  test.skip(!isRealTest, "Skipped: set REAL_TEST=true to run");

  test.beforeAll(() => {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  });

  test("generate notebook from 'Attention Is All You Need' and validate", async ({
    page,
  }) => {
    const attentionPdfPath = path.join(
      __dirname,
      "..",
      "fixtures",
      "attention.pdf"
    );
    expect(fs.existsSync(attentionPdfPath)).toBe(true);

    // Step 1: Navigate to the app
    await page.goto("http://localhost:3000");
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "01-homepage.png"),
    });

    // Step 2: Pause for user to enter API key manually
    // The user will type their real OpenAI API key in the browser
    await page.pause();

    // Step 3: Upload the "Attention Is All You Need" PDF
    await page.getByTestId("pdf-file-input").setInputFiles(attentionPdfPath);
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "02-pdf-uploaded.png"),
    });

    // Step 4: Click Generate and wait for completion (up to 120s)
    const submitBtn = page.getByTestId("submit-button");
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click();

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "03-generating.png"),
    });

    // Wait for notebook preview to appear (long timeout for real LLM call)
    await expect(page.getByTestId("notebook-preview")).toBeVisible({
      timeout: 120_000,
    });

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "04-notebook-result.png"),
      fullPage: true,
    });

    // Step 5: Verify safety warning banner is visible
    await expect(page.getByTestId("safety-warning-banner")).toBeVisible();

    // Step 6: Download and validate the notebook
    const downloadPromise = page.waitForEvent("download");
    await page.getByTestId("download-button").click();
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toMatch(/\.ipynb$/);

    const downloadPath = await download.path();
    expect(downloadPath).toBeTruthy();

    const content = fs.readFileSync(downloadPath!, "utf-8");
    const nb = JSON.parse(content);

    // Validate: valid JSON with nbformat >= 4
    expect(nb.nbformat).toBeGreaterThanOrEqual(4);

    // Validate: at least 8 cells
    expect(nb.cells.length).toBeGreaterThanOrEqual(8);

    // Validate: has at least one code cell
    const codeCells = nb.cells.filter(
      (c: { cell_type: string }) => c.cell_type === "code"
    );
    expect(codeCells.length).toBeGreaterThanOrEqual(1);

    // Validate: code cells contain Python-like syntax
    const hasImport = codeCells.some((c: { source: string | string[] }) => {
      const source = Array.isArray(c.source) ? c.source.join("") : c.source;
      return source.includes("import") || source.includes("def ");
    });
    expect(hasImport).toBe(true);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "05-validation-complete.png"),
    });
  });
});
