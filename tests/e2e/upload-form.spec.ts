import { test, expect } from "@playwright/test";
import path from "path";
import fs from "fs";

const SCREENSHOT_DIR = path.join(__dirname, "..", "screenshots");

test.beforeAll(() => {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
});

test.describe("Upload Form", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("http://localhost:3000");
  });

  test("renders the upload form with all required elements", async ({
    page,
  }) => {
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "task2-01-initial-page.png"),
    });

    // Page title / heading
    await expect(page.getByTestId("page-title")).toBeVisible();
    await expect(page.getByTestId("page-title")).toContainText(
      "Paper2Notebook"
    );

    // API key input (password type)
    const apiKeyInput = page.getByTestId("api-key-input");
    await expect(apiKeyInput).toBeVisible();
    await expect(apiKeyInput).toHaveAttribute("type", "password");

    // PDF file input / dropzone
    await expect(page.getByTestId("pdf-dropzone")).toBeVisible();

    // Submit button
    const submitBtn = page.getByTestId("submit-button");
    await expect(submitBtn).toBeVisible();
    await expect(submitBtn).toContainText("Generate Notebook");
  });

  test("submit button is disabled when form is empty", async ({ page }) => {
    const submitBtn = page.getByTestId("submit-button");
    await expect(submitBtn).toBeDisabled();
  });

  test("submit button is disabled when only API key is filled", async ({
    page,
  }) => {
    await page.getByTestId("api-key-input").fill("sk-test-key-123");
    const submitBtn = page.getByTestId("submit-button");
    await expect(submitBtn).toBeDisabled();
  });

  test("submit button is enabled when both API key and PDF are provided", async ({
    page,
  }) => {
    // Fill API key
    await page.getByTestId("api-key-input").fill("sk-test-key-123");

    // Upload a PDF file
    const fileInput = page.getByTestId("pdf-file-input");
    const testPdfPath = path.join(__dirname, "..", "fixtures", "test.pdf");
    await fileInput.setInputFiles(testPdfPath);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "task2-02-form-filled.png"),
    });

    const submitBtn = page.getByTestId("submit-button");
    await expect(submitBtn).toBeEnabled();
  });

  test("shows file name after PDF upload", async ({ page }) => {
    const fileInput = page.getByTestId("pdf-file-input");
    const testPdfPath = path.join(__dirname, "..", "fixtures", "test.pdf");
    await fileInput.setInputFiles(testPdfPath);

    await expect(page.getByTestId("file-name")).toContainText("test.pdf");
  });

  test("can remove uploaded file", async ({ page }) => {
    // Upload a file
    const fileInput = page.getByTestId("pdf-file-input");
    const testPdfPath = path.join(__dirname, "..", "fixtures", "test.pdf");
    await fileInput.setInputFiles(testPdfPath);
    await expect(page.getByTestId("file-name")).toBeVisible();

    // Remove it
    await page.getByTestId("remove-file-button").click();
    await expect(page.getByTestId("file-name")).not.toBeVisible();

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, "task2-03-file-removed.png"),
    });
  });
});
