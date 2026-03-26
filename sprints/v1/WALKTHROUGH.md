# Sprint v1 — Walkthrough

## Summary
Built **Paper2Notebook**, a full-stack web application that accepts a research paper PDF, extracts its text using PyMuPDF, sends it to OpenAI GPT-4o to generate tutorial content, and produces a downloadable Google Colab-compatible Jupyter notebook. The frontend provides a form for upload + API key entry, a live notebook preview with syntax-highlighted code cells, and a one-click `.ipynb` download. All 10 planned tasks were completed with 23 Python tests and 11 Playwright E2E tests.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                   Browser (:3000)                         │
│                                                          │
│  ┌─────────────────┐   ┌──────────────────────────────┐  │
│  │  UploadForm      │   │  NotebookPreview             │  │
│  │  - API key input │   │  - MarkdownCell (GFM)        │  │
│  │  - PDF dropzone  │   │  - CodeCell (Prism)          │  │
│  │  - Submit button │   │                              │  │
│  └────────┬─────────┘   └──────────▲───────────────────┘  │
│           │                        │                      │
│  ┌────────▼────────┐   ┌──────────┴───────────────────┐  │
│  │  LoadingState    │   │  DownloadButton              │  │
│  │  (skeleton)      │   │  (Blob → .ipynb download)    │  │
│  └─────────────────┘   └──────────────────────────────┘  │
│           │                        ▲                      │
└───────────┼────────────────────────┼──────────────────────┘
            │  POST /api/generate    │  JSON (notebook)
            │  (FormData: pdf+key)   │
            ▼                        │
┌───────────────────────────────────────────────────────────┐
│                  FastAPI Backend (:8000)                   │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │  pdf_parser   │  │  llm_service  │  │ notebook_builder│ │
│  │  (PyMuPDF)    │──│  (GPT-4o)    │──│ (nbformat)      │ │
│  │              │  │  JSON mode   │  │                 │ │
│  └──────────────┘  └──────────────┘  └─────────────────┘ │
│                                                           │
│  POST /api/generate  ─┐                                   │
│    1. Validate PDF     │                                   │
│    2. Extract text     │  pipeline                         │
│    3. Call GPT-4o      │  orchestration                    │
│    4. Build .ipynb     │                                   │
│    5. Return JSON     ─┘                                   │
└───────────────────────────────────────────────────────────┘
```

## Files Created/Modified

---

### backend/main.py
**Purpose**: FastAPI application entry point — creates the app, adds CORS middleware, mounts the generate router.

**Key Components**:
- `app` — FastAPI instance with title "Paper2Notebook API"
- CORS middleware allowing `http://localhost:3000`
- `GET /health` — simple health check endpoint

**How it works**:
This is a minimal FastAPI bootstrap. It creates the app, includes the generate router (which registers `POST /api/generate`), and configures CORS to accept requests from the Next.js frontend running on port 3000. The health endpoint exists for readiness checks.

---

### backend/routers/generate.py
**Purpose**: The main API endpoint that orchestrates the entire PDF-to-notebook pipeline.

**Key Functions**:
- `generate_notebook()` — async endpoint handler for `POST /api/generate`

**How it works**:
This is the heart of the backend. It accepts a multipart form upload with two fields: `file` (the PDF) and `api_key` (the user's OpenAI key). The handler runs a 4-step pipeline:

1. **Validate** — checks that the file has a `.pdf` extension and the API key is non-empty
2. **Extract** — calls `extract_text_from_pdf()` with the raw PDF bytes, rejects image-only PDFs
3. **Generate** — calls `generate_notebook_content()` which sends the extracted text to GPT-4o
4. **Build** — calls `build_notebook()` to assemble a valid `.ipynb` structure

Error handling maps specific failure modes to appropriate HTTP status codes:
```python
if "auth" in detail.lower() or "api key" in detail.lower():
    raise HTTPException(status_code=401, detail="Invalid OpenAI API key.")
raise HTTPException(status_code=502, detail=f"LLM generation failed: {detail}")
```

The paper title is extracted from the first line of text (up to 100 chars) and used as the notebook title.

---

### backend/services/pdf_parser.py
**Purpose**: Extracts text content from PDF files page-by-page using PyMuPDF.

**Key Functions**:
- `extract_text_from_pdf(pdf_bytes)` — returns structured dict with pages, full_text, and total_pages

**How it works**:
Opens the PDF from raw bytes using PyMuPDF's `fitz.open()`, iterates through each page calling `page.get_text()`, and collects the text into a structured dict:

```python
doc = fitz.open(stream=pdf_bytes, filetype="pdf")
for i, page in enumerate(doc):
    text = page.get_text()
    pages.append({"page_number": i + 1, "text": text})
```

The return value includes individual pages (with page numbers for potential future use), the full concatenated text (joined with double newlines), and the total page count. The full_text field is what gets sent to the LLM.

---

### backend/services/llm_service.py
**Purpose**: Constructs the prompt and calls OpenAI GPT-4o to generate tutorial notebook cells.

**Key Functions**:
- `build_prompt(paper_text)` — wraps paper text with instructions
- `generate_notebook_content(paper_text, api_key)` — calls GPT-4o, returns parsed cell list

**How it works**:
The system prompt instructs GPT-4o to act as an expert at converting research papers into educational Colab notebooks. It specifies the exact JSON output format and provides guidelines (start with title, include setup cell, alternate markdown/code, include visualizations, 10-20 cells).

The API call uses JSON mode (`response_format={"type": "json_object"}`) with `temperature=0.3` for more deterministic output:

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_prompt(paper_text)},
    ],
    temperature=0.3,
    response_format={"type": "json_object"},
)
```

The response is parsed as JSON and the `"cells"` array is extracted. Each cell has a `cell_type` ("markdown" or "code") and a `source` (the content string).

---

### backend/services/notebook_builder.py
**Purpose**: Converts LLM-generated cell dicts into a valid nbformat v4 Jupyter notebook with Colab metadata.

**Key Functions**:
- `build_notebook(cells, paper_title)` — returns a `NotebookNode` ready for serialization

**How it works**:
Creates a new nbformat v4 notebook and sets Colab-compatible metadata (provenance, kernel spec, language info). Before appending the LLM-generated cells, it prepends two standard cells:

1. A **title markdown cell** with the paper name and an auto-generated attribution note
2. A **setup code cell** with `!pip install -q numpy matplotlib seaborn scipy scikit-learn`

Then iterates through the LLM cells, creating proper `new_code_cell()` or `new_markdown_cell()` objects. The resulting notebook validates against the nbformat spec and opens correctly in both Google Colab and Jupyter.

---

### frontend/src/app/page.tsx
**Purpose**: Root page component — manages notebook state and renders the three-phase UI (form → loading → results).

**Key Components**:
- `Home` — client component with `notebook` and `isLoading` state

**How it works**:
The page has three visual states controlled by two pieces of state:
- **Initial**: Only the `UploadForm` is visible
- **Loading** (`isLoading=true`): Form + `LoadingState` skeleton
- **Complete** (`notebook` is set): Form + `DownloadButton` + `NotebookPreview`

The `UploadForm` communicates upward via two callbacks: `onNotebookGenerated` sets the notebook data, and `onLoadingChange` controls the skeleton visibility.

---

### frontend/src/components/upload-form.tsx
**Purpose**: The main input form — API key field, PDF drag-and-drop dropzone, and submit button with loading/error states.

**Key Components**:
- `UploadForm` — client component handling file selection, validation, and API submission

**How it works**:
The form manages four local state values: `apiKey`, `file`, `isLoading`, and `error`. The submit button is disabled unless both fields are filled and no request is in flight.

The PDF dropzone is implemented as a clickable div that triggers a hidden `<input type="file">`. It also supports native drag-and-drop via `onDragOver` and `onDrop` handlers that filter for `application/pdf` MIME type.

On submit, the form builds a `FormData` with the PDF and API key, POSTs to `http://localhost:8000/api/generate`, and handles the response:

```typescript
const formData = new FormData();
formData.append("file", file);
formData.append("api_key", apiKey);

const res = await fetch("http://localhost:8000/api/generate", {
    method: "POST",
    body: formData,
});
```

Error responses are parsed for the `detail` field (from FastAPI's HTTPException) and displayed in red below the dropzone. During loading, the button shows an animated spinner with "Generating..." text.

---

### frontend/src/components/notebook-preview.tsx
**Purpose**: Renders a Jupyter notebook as a scrollable cell-by-cell preview with formatted markdown and syntax-highlighted code.

**Key Components**:
- `NotebookPreview` — container that iterates through notebook cells
- `MarkdownCell` — renders markdown source using `react-markdown` with GFM support
- `CodeCell` — renders Python code with Prism syntax highlighting and cell numbering

**How it works**:
The component accepts a notebook object (matching the `.ipynb` JSON structure) and maps each cell to either a `MarkdownCell` or `CodeCell`. Code cells are numbered sequentially (skipping markdown cells), mimicking Jupyter's `In [N]:` convention.

The `getCellSource()` helper handles both string and array source formats (nbformat allows either). Markdown cells use `react-markdown` with the `remark-gfm` plugin for tables and strikethrough. Code cells use `react-syntax-highlighter` with the `oneLight` Prism theme:

```tsx
<SyntaxHighlighter language="python" style={oneLight}>
    {source}
</SyntaxHighlighter>
```

---

### frontend/src/components/download-button.tsx
**Purpose**: One-click download of the generated notebook as a `.ipynb` file.

**Key Functions**:
- `handleDownload()` — serializes notebook JSON to a Blob and triggers browser download

**How it works**:
Creates a JSON Blob from the notebook object, generates an object URL, creates a temporary `<a>` element with the `download` attribute set to `paper2notebook_tutorial.ipynb`, programmatically clicks it, then cleans up:

```typescript
const blob = new Blob([json], { type: "application/json" });
const url = URL.createObjectURL(blob);
const a = document.createElement("a");
a.href = url;
a.download = filename;
a.click();
URL.revokeObjectURL(url);
```

---

### frontend/src/components/loading-state.tsx
**Purpose**: Skeleton placeholder shown while the backend is generating the notebook (typically 30-60 seconds).

**How it works**:
Renders a shadcn/ui Card with animated pulse bars that mimic the shape of a notebook preview (alternating text blocks and code blocks). Includes a status message ("Analyzing paper and generating tutorial notebook...") and a time estimate.

---

### backend/requirements.txt
**Purpose**: Python dependency pins for the backend.

**Dependencies**:
- `fastapi==0.115.6` + `uvicorn==0.34.0` — web framework and ASGI server
- `python-multipart==0.0.20` — required for FastAPI file uploads
- `PyMuPDF==1.25.3` — PDF text extraction
- `openai==1.59.3` — OpenAI API client
- `nbformat==5.10.4` — Jupyter notebook creation/validation
- `pytest==8.3.4` + `httpx==0.28.1` — testing

---

## Data Flow

1. User opens `http://localhost:3000` → sees the upload form
2. User enters their OpenAI API key (stored only in component state, never persisted)
3. User uploads a PDF via click or drag-and-drop → filename displayed in dropzone
4. User clicks "Generate Notebook" → button shows spinner, skeleton appears below
5. Frontend POSTs `FormData` (PDF file + API key) to `http://localhost:8000/api/generate`
6. Backend reads PDF bytes → `extract_text_from_pdf()` extracts text via PyMuPDF
7. Backend sends extracted text to GPT-4o with structured prompt → receives JSON with cells
8. Backend runs `build_notebook()` → prepends title + setup cells → creates nbformat notebook
9. Backend returns `{"notebook": {...}}` JSON to frontend
10. Frontend stores notebook in state → hides skeleton → renders `DownloadButton` + `NotebookPreview`
11. User can preview the notebook (markdown + syntax-highlighted code cells) in the browser
12. User clicks "Download Notebook (.ipynb)" → browser downloads valid Jupyter notebook file
13. User opens `.ipynb` in Google Colab → runs the tutorial cells

## Test Coverage

- **Unit: 18 tests**
  - `test_backend_health.py` (2) — health endpoint returns 200, CORS headers present
  - `test_pdf_parser.py` (5) — single page, multi-page, page numbers, full text, metadata
  - `test_llm_service.py` (4) — prompt includes paper text, requests code/explanations/plots, returns cells, uses gpt-4o model
  - `test_notebook_builder.py` (7) — valid nbformat, correct version, setup cell first, title cell, all LLM cells included, Colab metadata, serializes to JSON

- **Integration: 5 tests**
  - `test_generate_endpoint.py` (4) — 400 when no file, 400 when no API key, 400 for non-PDF, 200 with valid inputs
  - `test_pipeline.py` (1) — full pipeline with mocked LLM returns valid notebook with title + setup + LLM cells

- **E2E (Playwright): 11 tests**
  - `upload-form.spec.ts` (6) — renders all elements, button disabled when empty, disabled without file, enabled when filled, shows filename, file removal
  - `notebook-preview.spec.ts` (1) — renders markdown + code cells with correct count
  - `download.spec.ts` (1) — download button triggers .ipynb download with valid content
  - `loading-error.spec.ts` (3) — loading spinner + skeleton during generation, error message on API failure, responsive layout on tablet

**Total: 34 tests (23 Python + 11 Playwright)**

## Security Measures

- API key is transmitted via `FormData` (POST body), not URL parameters
- API key input uses `type="password"` to prevent shoulder-surfing
- API key is never persisted (stored only in React component state)
- CORS restricted to `http://localhost:3000` (not wildcard)
- File type validation on both frontend (MIME type check) and backend (extension check)
- Backend rejects empty/image-only PDFs before calling the LLM
- OpenAI auth errors return 401, not 500 (no stack traces leaked)
- Semgrep static analysis passed clean on all source files
- npm audit shows 0 vulnerabilities

## Known Limitations

- **No streaming** — notebook generation takes 30-60s with no progress indication beyond the skeleton. GPT-4o response is received all at once.
- **Backend URL hardcoded** — frontend has `http://localhost:8000` hardcoded in the fetch call. Not configurable via environment variable.
- **Image-based PDFs unsupported** — PyMuPDF text extraction fails on scanned/image-only PDFs. OCR (e.g., Tesseract) would be needed.
- **No token limit handling** — very long papers may exceed GPT-4o's context window. No chunking or summarization strategy is implemented.
- **Single LLM call** — the entire notebook is generated in one API call. No retry logic, no partial results.
- **No persistent storage** — generated notebooks exist only in browser memory. Refreshing the page loses them.
- **No authentication** — anyone who can reach the server can use it. API key is the only gating mechanism.
- **LaTeX rendering** — math notation ($$..$$) from the LLM is displayed as raw LaTeX in the preview. A KaTeX/MathJax renderer would be needed.
- **Static setup cell** — the `!pip install` cell always installs the same packages regardless of what the paper actually needs.

## What's Next

For **v2**, the highest-impact improvements would be:

1. **Streaming generation** — use OpenAI's streaming API + Server-Sent Events to show notebook cells as they're generated, reducing perceived wait time
2. **Environment configuration** — make backend URL configurable via `NEXT_PUBLIC_API_URL`, add `.env` support to both frontend and backend
3. **Token-aware chunking** — for long papers, split text into sections and generate notebook content per-section, then merge
4. **LaTeX rendering** — add KaTeX to the notebook preview for proper math notation display
5. **OCR fallback** — use Tesseract or a cloud OCR service when PyMuPDF extracts no text
6. **History/saving** — store generated notebooks in localStorage or a database so users can revisit them
7. **Multiple LLM providers** — support Anthropic Claude, Google Gemini, or local models as alternatives to GPT-4o
