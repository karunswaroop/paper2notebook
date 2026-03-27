# Sprint v3 — Tasks

## Status: In Progress

### Pillar Map
Tasks are grouped by sprint pillar: [TESTING], [CI/CD], [DOCKER], [CLOUD].

---

## TESTING — Unit Tests (~70%)

- [x] Task 1: Expand unit tests for pdf_parser.py — edge cases and error paths (P0)
  - Acceptance: Tests cover: empty PDF (0 text), corrupted/invalid bytes (raises exception), PDF with only images (no extractable text returns empty string), Unicode/special characters in text, exactly 200 pages (boundary), 201 pages (just over limit). All pass.
  - Files: tests/unit/test_pdf_parser.py
  - Completed: 2026-03-26 — Added 9 new tests (14 total): corrupted bytes, empty bytes, blank PDF, Unicode Latin text, page number sequencing, full_text join format, return dict keys, over-limit error message, image-only PDF. All pass, semgrep clean.

- [ ] Task 2: Expand unit tests for llm_service.py — sanitization, prompt, and error handling (P0)
  - Acceptance: Tests cover: `sanitize_text()` with normal text passthrough, nested injection patterns, case-insensitive matching, text at exactly 100K chars (boundary); `build_prompt()` output contains delimiter markers and sanitized text; `generate_notebook_content()` with malformed JSON response from LLM (raises), empty `cells` array, missing `cells` key (returns []), OpenAI API raising connection error, OpenAI API raising timeout error. All pass.
  - Files: tests/unit/test_llm_service.py

- [ ] Task 3: Expand unit tests for notebook_builder.py — malformed input and edge cases (P0)
  - Acceptance: Tests cover: empty cell list (only title + setup cells in output), cell missing `source` key (defaults to ""), cell missing `cell_type` key (defaults to "markdown"), cell with `cell_type: "raw"` (treated as markdown), very long paper title (>500 chars, truncated in metadata), multiple dangerous patterns in single cell (all flagged), code cell with no dangerous patterns plus one with many. All pass.
  - Files: tests/unit/test_notebook_builder.py

- [ ] Task 4: Add unit tests for generate.py router — validation and error paths (P0)
  - Acceptance: Tests cover: filename with uppercase `.PDF` extension accepted, filename with no extension rejected, empty filename rejected, empty API key (whitespace only) rejected, PDF bytes exactly at 50MB limit accepted, request logging output contains expected fields (client IP, filename, size), successful response logs duration and cell count. All pass. Tests use httpx AsyncClient with mocked service functions.
  - Files: tests/unit/test_generate_router.py

## TESTING — Integration Tests (~20%)

- [ ] Task 5: Add integration tests for full POST /api/generate pipeline with mocked OpenAI (P0)
  - Acceptance: Tests cover: valid PDF upload returns 200 with valid notebook JSON containing title cell + setup cell + LLM cells; response notebook has correct nbformat version (4); LLM returning code cells with dangerous patterns results in warning comments in output; LLM returning empty cells array produces notebook with only title + setup; OpenAI auth error returns 401; OpenAI timeout returns 502 with generic message; OpenAI rate limit (429) returns 502 with generic message; concurrent requests within rate limit all succeed. All tests mock only the OpenAI API call — the rest of the pipeline (PDF parsing, sanitization, notebook building) runs for real.
  - Files: tests/integration/test_full_pipeline.py

## TESTING — E2E Tests (~10%)

- [ ] Task 6: Add E2E Playwright tests — full user flow with screenshots at each step (P0)
  - Acceptance: A single Playwright test file exercises the complete user flow against a running local stack (frontend :3000, backend :8000 with mocked OpenAI). Steps: (1) Navigate to homepage — screenshot "step-01-homepage.png"; (2) Enter API key — screenshot "step-02-api-key.png"; (3) Upload a PDF file — screenshot "step-03-pdf-uploaded.png"; (4) Click Generate — screenshot "step-04-loading.png" (verify spinner visible); (5) Wait for result — screenshot "step-05-notebook-preview.png" (verify notebook cells rendered); (6) Verify safety warning banner visible; (7) Click Download — screenshot "step-06-download.png" (verify download triggered); (8) Validate downloaded file is valid JSON with nbformat=4. All screenshots saved to `tests/screenshots/e2e-flow/`. Test uses route interception to mock the backend API response.
  - Files: tests/e2e/full-flow.spec.ts

- [ ] Task 7: Add real quality test — generate notebook from "Attention Is All You Need" (P1)
  - Acceptance: A separate Playwright test file marked with `test.describe.configure({ mode: 'serial', timeout: 180_000 })` that: (1) Opens a visible browser (headful via project config); (2) Navigates to the app; (3) Pauses for the user to enter their real API key manually (`page.pause()`); (4) Uploads the "Attention Is All You Need" PDF (stored in `tests/fixtures/attention.pdf`); (5) Clicks Generate and waits for completion (up to 120s); (6) Takes a screenshot of the full result; (7) Downloads the .ipynb and validates: valid JSON, `nbformat >= 4`, has at least 8 cells, contains at least one code cell with valid Python syntax (compile check), safety disclaimer banner is visible in preview. Test is skipped in CI (gated by `REAL_TEST=true` env var). The "Attention Is All You Need" PDF must be provided or downloaded into `tests/fixtures/`.
  - Files: tests/e2e/real-quality.spec.ts, tests/fixtures/attention.pdf

## CI/CD PIPELINE

- [ ] Task 8: Connect repo to GitHub via CLI, create remote, and configure secrets (P0)
  - Acceptance: (1) Verify `gh` CLI is installed and authenticated (`gh auth status` succeeds); if not, prompt user to run `gh auth login`; (2) Create a GitHub repository (or connect existing) via `gh repo create paper2notebook --source=. --public --push` (or `--private` per user preference); (3) Set GitHub Actions secrets for AWS deployment: `gh secret set AWS_ACCESS_KEY_ID`, `gh secret set AWS_SECRET_ACCESS_KEY`, `gh secret set AWS_REGION` using values from the `MSD_User` IAM credentials; (4) Verify remote is set and push succeeds. Note: if secret access key is still invalid, document the `gh secret set` commands for the user to run manually once they have the correct key.
  - Files: (no files created — CLI setup only)

- [ ] Task 9: Create GitHub Actions CI workflow — pytest, Playwright, semgrep, pip-audit (P0)
  - Acceptance: `.github/workflows/ci.yml` runs on every push and pull_request to any branch. Four parallel jobs: (1) **backend-tests** — sets up Python 3.12, installs requirements.txt + test deps, runs `pytest tests/unit tests/integration -v`; (2) **frontend-build** — sets up Node 20, installs deps, runs `npm run build` in frontend/; (3) **e2e-tests** — sets up both Python + Node, starts backend + frontend, installs Playwright browsers, runs Playwright tests (excluding real-quality), uploads screenshot artifacts; (4) **security-scan** — runs `semgrep --config=auto backend/ frontend/src/` and `pip-audit -r backend/requirements.txt`. All four jobs must pass. Workflow uses `concurrency` to cancel stale runs.
  - Files: .github/workflows/ci.yml

- [ ] Task 10: Add branch protection documentation and merge-blocking config (P1)
  - Acceptance: A `BRANCH_PROTECTION.md` file in the repo root documents the required GitHub branch protection settings for `main`: require PR reviews, require status checks (backend-tests, frontend-build, e2e-tests, security-scan) to pass, no direct pushes. Also includes a `gh` CLI command to set this up programmatically. The workflow from Task 9 already names jobs correctly so they can be referenced as required status checks.
  - Files: BRANCH_PROTECTION.md

## DOCKER

- [ ] Task 11: Create backend Dockerfile (FastAPI + uvicorn) (P0)
  - Acceptance: `backend/Dockerfile` uses multi-stage build: (1) Builder stage installs deps from requirements.txt into a venv; (2) Runtime stage uses `python:3.12-slim`, copies venv and app code, exposes port 8000, runs `uvicorn backend.main:app --host 0.0.0.0 --port 8000`. Image builds successfully with `docker build -t paper2notebook-backend ./backend` (or from repo root with correct context). Includes a `HEALTHCHECK` instruction hitting `/health`. Non-root user. `.dockerignore` excludes `__pycache__`, `.pytest_cache`, `tests/`.
  - Files: backend/Dockerfile, backend/.dockerignore

- [ ] Task 12: Create frontend Dockerfile (Next.js standalone) (P0)
  - Acceptance: `frontend/Dockerfile` uses multi-stage build: (1) Builder stage installs deps and runs `npm run build` with `output: "standalone"` in next.config.ts; (2) Runtime stage uses `node:20-alpine`, copies standalone output + static + public dirs, exposes port 3000, runs `node server.js`. Includes `NEXT_PUBLIC_API_URL` as a build arg. `.dockerignore` excludes `node_modules`, `.next`, `test-results/`. Image builds successfully. Includes `HEALTHCHECK`.
  - Files: frontend/Dockerfile, frontend/.dockerignore

- [ ] Task 13: Create docker-compose.yml for local development (P0)
  - Acceptance: `docker-compose.yml` in repo root defines two services: `backend` (builds from `backend/Dockerfile`, port 8000:8000, healthcheck) and `frontend` (builds from `frontend/Dockerfile`, port 3000:3000, depends_on backend healthy, passes `NEXT_PUBLIC_API_URL=http://backend:8000` as build arg and env var). Running `docker compose up --build` starts both services and the app is accessible at `http://localhost:3000`. Includes a `.env` file reference for optional config overrides.
  - Files: docker-compose.yml

## CLOUD DEPLOYMENT

- [ ] Task 14: Create Terraform config for AWS ECS Fargate deployment (P0)
  - Acceptance: `terraform/` directory contains: `main.tf` (provider config for `us-east-2`, VPC with 2 public subnets, security groups), `ecr.tf` (ECR repos for frontend + backend images), `ecs.tf` (ECS cluster, task definitions for frontend + backend using Fargate, ECS services with desired_count=1), `alb.tf` (Application Load Balancer with HTTP listener, target groups for frontend and backend, path-based routing: `/api/*` and `/health` → backend, `/*` → frontend), `outputs.tf` (ALB DNS name, ECR repo URLs, ECS cluster name), `variables.tf` (region defaults to `us-east-2`, app name, container ports, image tags). Uses `aws_ecs_task_definition` with Fargate launch type, 256 CPU / 512 MiB memory. Backend task passes `CORS_ORIGIN` env var. All resources tagged with `app=paper2notebook`. IAM user `MSD_User` credentials used for deployment. `terraform validate` passes.
  - Files: terraform/main.tf, terraform/ecr.tf, terraform/ecs.tf, terraform/alb.tf, terraform/outputs.tf, terraform/variables.tf

- [ ] Task 15: Create CD pipeline — auto-deploy to AWS after tests pass on main (P1)
  - Acceptance: `.github/workflows/cd.yml` triggers only on push to `main` (after CI passes). Steps: (1) Configure AWS credentials using GitHub secrets (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`) set in Task 8 for IAM user `MSD_User`; (2) Log in to ECR in `us-east-2`; (3) Build and push backend Docker image to ECR with `latest` and `${{ github.sha }}` tags; (4) Build and push frontend Docker image to ECR; (5) Update ECS service to force new deployment (picks up latest image). Includes manual approval gate via `environment: production` (optional, documented). Workflow references the ECR repo URLs and ECS service/cluster names as GitHub secrets or variables.
  - Files: .github/workflows/cd.yml
