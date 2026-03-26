# Sprint v1 — Tasks

## Status: Complete

- [x] Task 1: Initialize monorepo with Next.js frontend and FastAPI backend (P0)
  - Acceptance: `npm run dev` starts frontend on :3000, `uvicorn` starts backend on :8000, both run without errors
  - Files: frontend/package.json, frontend/tailwind.config.ts, frontend/app/layout.tsx, backend/main.py, backend/requirements.txt
  - Completed: 2026-03-24 — Next.js 16 + Tailwind v4 + shadcn/ui frontend, FastAPI backend with CORS, health endpoint, all deps installed, tests passing, semgrep clean

- [x] Task 2: Build the upload form UI — PDF file input + API key field + submit button (P0)
  - Acceptance: Page renders with a styled file upload dropzone, a password-type input for API key, and a "Generate Notebook" button. Form validates that both fields are filled before submission.
  - Files: frontend/src/app/page.tsx, frontend/src/components/upload-form.tsx
  - Completed: 2026-03-25 — Upload form with drag & drop dropzone, password API key input, file name display with remove, disabled button until both fields filled. 6 Playwright E2E tests passing, semgrep clean.

- [x] Task 3: Create FastAPI `/api/generate` endpoint that accepts PDF file + API key (P0)
  - Acceptance: Endpoint accepts multipart form data (PDF file + api_key string), returns 400 if either is missing, returns 200 with a placeholder JSON response. Frontend can call it successfully via fetch.
  - Files: backend/main.py, backend/routers/generate.py
  - Completed: 2026-03-25 — POST /api/generate accepts PDF + api_key, validates file type, returns placeholder notebook. 4 integration tests passing.

- [x] Task 4: Implement PDF text extraction using PyMuPDF (P0)
  - Acceptance: Given a PDF file, returns structured text with page numbers. Handles multi-page papers. Extracts at least title, abstract, and body sections.
  - Files: backend/services/pdf_parser.py
  - Completed: 2026-03-25 — PyMuPDF-based extractor returns pages with text + page numbers, full_text, total_pages. 5 unit tests passing.

- [x] Task 5: Build the OpenAI prompt and call GPT-4o to generate notebook content (P0)
  - Acceptance: Given extracted paper text and a valid API key, sends a structured prompt to GPT-4o and returns a parsed response containing markdown explanations, code cells, and visualization suggestions.
  - Files: backend/services/llm_service.py
  - Completed: 2026-03-25 — Structured system prompt + user prompt, GPT-4o JSON mode, returns list of cells. 4 unit tests passing (mocked).

- [x] Task 6: Convert LLM response into a valid `.ipynb` file using nbformat (P0)
  - Acceptance: Produces a valid Jupyter notebook with alternating markdown and code cells. Notebook includes a Colab setup cell (pip installs), explanation cells, implementation code cells, and visualization cells. File opens correctly in Google Colab.
  - Files: backend/services/notebook_builder.py
  - Completed: 2026-03-25 — Builds valid .ipynb with title, setup, and LLM cells. Colab metadata included. 7 unit tests passing.

- [x] Task 7: Wire the full pipeline — upload PDF → extract → LLM → notebook → return to frontend (P0)
  - Acceptance: End-to-end flow works: upload a real PDF, get back a valid `.ipynb` JSON. Frontend receives the notebook JSON and stores it in state.
  - Files: backend/routers/generate.py (update), frontend/src/app/page.tsx (update), frontend/src/components/upload-form.tsx (update)
  - Completed: 2026-03-25 — Full pipeline wired: PDF extract → LLM → nbformat → JSON response. Frontend sends FormData, stores notebook in state. Error handling for bad PDF/API key/LLM failure. 23 Python tests passing.

- [x] Task 8: Build notebook preview component in the frontend (P1)
  - Acceptance: Renders markdown cells as formatted text and code cells with syntax highlighting. Displays cell-by-cell like a real notebook viewer.
  - Files: frontend/src/components/notebook-preview.tsx
  - Completed: 2026-03-25 — NotebookPreview with react-markdown + react-syntax-highlighter. Markdown cells rendered with GFM, code cells with Prism syntax highlighting and cell numbering. 1 E2E test passing.

- [x] Task 9: Add download button that exports the `.ipynb` file (P1)
  - Acceptance: Clicking "Download Notebook" saves a valid `.ipynb` file to disk. File opens correctly in Google Colab and Jupyter.
  - Files: frontend/src/components/download-button.tsx, frontend/src/app/page.tsx (update)
  - Completed: 2026-03-25 — DownloadButton creates Blob from notebook JSON and triggers download as .ipynb. E2E test verifies download triggers and content is valid notebook JSON.

- [x] Task 10: Add loading states, error handling, and UI polish (P2)
  - Acceptance: Shows a spinner/progress indicator during generation. Displays user-friendly error messages for invalid PDF, bad API key, or LLM failure. Responsive layout works on desktop and tablet.
  - Files: frontend/src/components/upload-form.tsx (update), frontend/src/components/loading-state.tsx, frontend/src/app/page.tsx (update)
  - Completed: 2026-03-25 — Spinner in button, skeleton loading card, error messages in red, responsive layout. 3 E2E tests for loading/error/responsive. All 11 E2E + 23 Python tests passing. Semgrep clean.
