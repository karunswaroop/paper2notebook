# Sprint v3 — Tasks

## Status: Complete

### Pillar Map
Tasks are grouped by sprint pillar: [TESTING], [CI/CD], [DOCKER], [CLOUD].

---

## TESTING — Unit Tests (~70%)

- [x] Task 1: Expand unit tests for pdf_parser.py — edge cases and error paths (P0)
  - Acceptance: Tests cover: empty PDF (0 text), corrupted/invalid bytes (raises exception), PDF with only images (no extractable text returns empty string), Unicode/special characters in text, exactly 200 pages (boundary), 201 pages (just over limit). All pass.
  - Files: tests/unit/test_pdf_parser.py
  - Completed: 2026-03-26 — Added 9 new tests (14 total): corrupted bytes, empty bytes, blank PDF, Unicode Latin text, page number sequencing, full_text join format, return dict keys, over-limit error message, image-only PDF. All pass, semgrep clean.

- [x] Task 2: Expand unit tests for llm_service.py — sanitization, prompt, and error handling (P0)
  - Acceptance: Tests cover: `sanitize_text()` with normal text passthrough, nested injection patterns, case-insensitive matching, text at exactly 100K chars (boundary); `build_prompt()` output contains delimiter markers and sanitized text; `generate_notebook_content()` with malformed JSON response from LLM (raises), empty `cells` array, missing `cells` key (returns []), OpenAI API raising connection error, OpenAI API raising timeout error. All pass.
  - Files: tests/unit/test_llm_service.py
  - Completed: 2026-03-27 — Expanded from 4 to 35 tests: sanitization edge cases, build_prompt validation, malformed JSON handling, connection/timeout errors. All pass.

- [x] Task 3: Expand unit tests for notebook_builder.py — malformed input and edge cases (P0)
  - Acceptance: Tests cover: empty cell list (only title + setup cells in output), cell missing `source` key (defaults to ""), cell missing `cell_type` key (defaults to "markdown"), cell with `cell_type: "raw"` (treated as markdown), very long paper title (>500 chars, truncated in metadata), multiple dangerous patterns in single cell (all flagged), code cell with no dangerous patterns plus one with many. All pass.
  - Files: tests/unit/test_notebook_builder.py
  - Completed: 2026-03-27 — Expanded from 7 to 22 tests: empty cells, missing keys, raw cell type, long titles, multi-pattern danger, mixed safe/dangerous. All pass.

- [x] Task 4: Add unit tests for generate.py router — validation and error paths (P0)
  - Acceptance: Tests cover: filename with uppercase `.PDF` extension accepted, filename with no extension rejected, empty filename rejected, empty API key (whitespace only) rejected, PDF bytes exactly at 50MB limit accepted, request logging output contains expected fields (client IP, filename, size), successful response logs duration and cell count. All pass. Tests use httpx AsyncClient with mocked service functions.
  - Files: tests/unit/test_generate_router.py
  - Completed: 2026-03-27 — New file with 8 tests: filename validation, API key validation, size limits, logging assertions. All pass.

## TESTING — Integration Tests (~20%)

- [x] Task 5: Add integration tests for full POST /api/generate pipeline with mocked OpenAI (P0)
  - Acceptance: Tests cover: valid PDF upload returns 200 with valid notebook JSON containing title cell + setup cell + LLM cells; response notebook has correct nbformat version (4); LLM returning code cells with dangerous patterns results in warning comments in output; LLM returning empty cells array produces notebook with only title + setup; OpenAI auth error returns 401; OpenAI timeout returns 502 with generic message; OpenAI rate limit (429) returns 502 with generic message.
  - Files: tests/integration/test_full_pipeline.py
  - Completed: 2026-03-27 — New file with 7 tests covering full pipeline, nbformat validation, dangerous code warnings, empty cells, auth/timeout/rate-limit errors. All pass.

## TESTING — E2E Tests (~10%)

- [x] Task 6: Add E2E Playwright tests — full user flow with screenshots at each step (P0)
  - Acceptance: Full flow test with route interception: homepage → API key → PDF upload → generate → notebook preview → safety banner → download → validate JSON.
  - Files: tests/e2e/full-flow.spec.ts
  - Completed: 2026-03-27 — 1 E2E test with 6 screenshots in tests/screenshots/e2e-flow/. Validates safety banner, download, nbformat=4. Passes.

- [x] Task 7: Add real quality test — generate notebook from "Attention Is All You Need" (P1)
  - Acceptance: Headful browser test gated by REAL_TEST=true. Pauses for manual API key entry, uploads attention.pdf, waits up to 120s, validates: JSON, nbformat>=4, >=8 cells, code cells with Python. Skipped in CI.
  - Files: tests/e2e/real-quality.spec.ts, tests/fixtures/attention.pdf
  - Completed: 2026-03-27 — Test file created with 180s timeout, page.pause() for API key, full validation. Fixture PDF in place. Skipped in CI via REAL_TEST env gate.

## CI/CD PIPELINE

- [x] Task 8: Connect repo to GitHub via CLI, create remote, and configure secrets (P0)
  - Acceptance: gh CLI authenticated, repo created, AWS secrets set.
  - Files: (no files — CLI setup only)
  - Completed: 2026-03-27 — Created https://github.com/karunswaroop/paper2notebook (public). Set 3 GitHub secrets: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION for MSD_User.

- [x] Task 9: Create GitHub Actions CI workflow — pytest, Playwright, semgrep, pip-audit (P0)
  - Acceptance: `.github/workflows/ci.yml` with 4 parallel jobs on push/PR.
  - Files: .github/workflows/ci.yml
  - Completed: 2026-03-27 — CI workflow with backend-tests, frontend-build, e2e-tests, security-scan jobs. Concurrency cancels stale runs.

- [x] Task 10: Add branch protection documentation and merge-blocking config (P1)
  - Acceptance: BRANCH_PROTECTION.md with gh CLI commands.
  - Files: BRANCH_PROTECTION.md
  - Completed: 2026-03-27 — Docs with required status checks and `gh api` command to set protection programmatically.

## DOCKER

- [x] Task 11: Create backend Dockerfile (FastAPI + uvicorn) (P0)
  - Acceptance: Multi-stage build, python:3.12-slim, non-root user, HEALTHCHECK, port 8000.
  - Files: backend/Dockerfile, backend/.dockerignore
  - Completed: 2026-03-27 — Multi-stage Dockerfile with venv, non-root appuser, health check. .dockerignore excludes tests and cache.

- [x] Task 12: Create frontend Dockerfile (Next.js standalone) (P0)
  - Acceptance: Multi-stage build, node:20-alpine, standalone output, NEXT_PUBLIC_API_URL build arg, HEALTHCHECK, port 3000.
  - Files: frontend/Dockerfile, frontend/.dockerignore, frontend/next.config.ts (added output: "standalone")
  - Completed: 2026-03-27 — 3-stage Dockerfile (deps, build, runtime). Added output: "standalone" to next.config.ts. .dockerignore in place.

- [x] Task 13: Create docker-compose.yml for local development (P0)
  - Acceptance: Two services, backend depends_on healthy, NEXT_PUBLIC_API_URL passed.
  - Files: docker-compose.yml, .dockerignore
  - Completed: 2026-03-27 — docker-compose.yml with backend (healthcheck) and frontend (depends_on backend healthy). Root .dockerignore excludes .git, tests, secrets.

## CLOUD DEPLOYMENT

- [x] Task 14: Create Terraform config for AWS ECS Fargate deployment (P0)
  - Acceptance: terraform/ with VPC, ECR, ECS, ALB, path-based routing. terraform validate passes.
  - Files: terraform/main.tf, terraform/ecr.tf, terraform/ecs.tf, terraform/alb.tf, terraform/outputs.tf, terraform/variables.tf
  - Completed: 2026-03-27 — Full Terraform config: VPC + 2 subnets, ALB with /api/* and /health routing to backend, ECR repos, ECS Fargate services (256 CPU/512 MiB), CloudWatch logs, IAM execution role. terraform validate passes.

- [x] Task 15: Create CD pipeline — auto-deploy to AWS after tests pass on main (P1)
  - Acceptance: `.github/workflows/cd.yml` triggers on push to main. Builds + pushes Docker images to ECR, updates ECS services.
  - Files: .github/workflows/cd.yml
  - Completed: 2026-03-27 — CD workflow with ECR login, multi-tag builds (sha + latest), ECS force-deploy, wait-for-stable. Production environment gate.
