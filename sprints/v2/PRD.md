# Sprint v2 — PRD: Security Hardening

## Overview
Harden the Paper2Notebook application against all 12 vulnerabilities identified in the v1 security audit. This sprint addresses every finding — 9 with direct code fixes and 3 with preparatory measures (full resolution in v3 deployment sprint). No new features; pure security.

## Goals
- PDF uploads are size-capped (50MB) and page-limited (200 pages) to prevent DoS
- Extracted PDF text is sanitized to neutralize prompt injection before reaching the LLM
- LLM-generated code cells are scanned for dangerous patterns (os.system, subprocess, eval, etc.)
- Users see a non-dismissable safety warning banner on generated notebooks
- Error messages never leak API keys or internal stack traces
- Rate limiting (5 req/min per IP) protects `/api/generate` from abuse
- CORS is locked down to only required methods and headers
- Security headers are set on both FastAPI and Next.js responses
- LLM client has a 120-second timeout to prevent worker starvation
- Backend API URL is environment-configurable (prep for HTTPS in v3)
- Frontend security headers prevent clickjacking and MIME sniffing
- Server-side structured logging provides an audit trail for security events

## User Stories
- As a user, I want the server to reject oversized or malformed PDFs, so the service stays responsive
- As a user, I want to be warned that generated code should be reviewed before execution, so I don't unknowingly run malicious code
- As a developer, I want error messages to be safe and generic, so my API key is never exposed in responses
- As an operator, I want rate limiting and request logging, so abuse is throttled and traceable

## Technical Architecture

```
Frontend (Next.js)                          Backend (FastAPI)
┌─────────────────────────┐                 ┌──────────────────────────────────┐
│ next.config.ts           │                 │ main.py                          │
│  - Security headers      │                 │  - Tightened CORS (GET/POST only)│
│                          │                 │  - Security headers middleware   │
│ upload-form.tsx          │                 │  - Rate limiter (slowapi)        │
│  - Env-based API URL     │─POST /generate─▶│  - Structured request logging    │
│                          │                 │                                  │
│ notebook-preview.tsx     │                 │ routers/generate.py              │
│  - Safety warning banner │◀── response ───│  - 50MB file size cap            │
└─────────────────────────┘                 │  - Generic error responses       │
                                            │                                  │
                                            │ services/pdf_parser.py           │
                                            │  - 200-page limit                │
                                            │                                  │
                                            │ services/llm_service.py          │
                                            │  - Input text sanitization       │
                                            │  - 120s client timeout           │
                                            │                                  │
                                            │ services/notebook_builder.py     │
                                            │  - Code cell safety scanner      │
                                            └──────────────────────────────────┘
```

**New dependencies:** `slowapi` (rate limiting)

## Audit Finding Coverage

| # | Finding | Severity | Resolution |
|---|---|---|---|
| 1 | Prompt injection via PDF | CRITICAL | Tasks 2, 3, 4 (sanitize + scan + warn) |
| 2 | No file size limit | CRITICAL | Task 1 |
| 3 | API key over HTTP | HIGH | Task 10 (env-configurable URL; HTTPS in v3) |
| 4 | No rate limiting | HIGH | Task 6 |
| 5 | No LLM output validation | HIGH | Task 3 |
| 6 | API key in error messages | HIGH | Task 5 |
| 7 | Overly permissive CORS | MEDIUM | Task 7 |
| 8 | Missing security headers | MEDIUM | Tasks 8, 11 |
| 9 | No authentication | MEDIUM | Task 12 (logging/audit trail; full auth in v3) |
| 10 | PDF parser DoS | LOW | Task 1 |
| 11 | Hardcoded backend URL | LOW | Task 10 |
| 12 | No LLM call timeout | LOW | Task 9 |

## Out of Scope (v3 — Deployment Sprint)
- HTTPS enforcement and TLS configuration
- User authentication / accounts
- Production deployment (Docker, cloud, CI/CD)
- Content Security Policy tuning for production domains
- Sandboxed code execution environment

## Dependencies
- v1 codebase (fully built and functional)
- Security audit report (12 findings documented)
