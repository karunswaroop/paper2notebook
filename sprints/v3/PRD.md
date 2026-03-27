# Sprint v3 — PRD: Production-Ready (Testing, CI/CD, Docker & Cloud)

## Overview
Make Paper2Notebook production-ready without changing any existing functionality. This sprint adds comprehensive test coverage following the testing pyramid (~70% unit, ~20% integration, ~10% E2E), a GitHub Actions CI/CD pipeline that blocks merges on failure, Docker containerization for both services, and Terraform-based AWS ECS Fargate deployment with continuous delivery.

## Goals
- Test coverage follows the pyramid: ~70% unit, ~20% integration, ~10% E2E
- All backend modules have thorough unit tests covering edge cases and error paths
- Integration tests cover the full API endpoint with mocked OpenAI
- E2E Playwright tests cover the complete user flow with screenshots at each step
- A real quality test generates a notebook from "Attention Is All You Need" and validates output
- GitHub Actions runs pytest, Playwright, semgrep, and pip-audit on every push/PR
- Merges are blocked if any CI check fails
- Backend and frontend each have a production Dockerfile
- docker-compose.yml runs both services locally with one command
- Terraform deploys both services to AWS ECS Fargate
- CD pipeline auto-deploys to AWS after tests pass on main

## User Stories
- As a developer, I want comprehensive tests so that regressions are caught before merge
- As an operator, I want Docker containers so that the app runs identically in dev and prod
- As a team lead, I want CI/CD so that no broken code reaches the main branch
- As a DevOps engineer, I want Terraform IaC so that infrastructure is reproducible and auditable
- As a user, I want the app deployed on AWS so that I can access it from anywhere over HTTPS

## Technical Architecture

### Testing Pyramid
```
                    ┌─────────┐
                    │  E2E    │  ~10% — Playwright browser tests
                    │ (3-5)   │  Full user flow + real quality test
                   ─┤         ├─
                  / └─────────┘ \
                 /                \
                ┌──────────────────┐
                │   Integration    │  ~20% — httpx TestClient
                │   (15-20)        │  API endpoints + mocked OpenAI
               ─┤                  ├─
              / └──────────────────┘ \
             /                        \
            ┌──────────────────────────┐
            │         Unit             │  ~70% — pytest
            │        (50-60)           │  All backend modules edge cases
            └──────────────────────────┘
```

### CI/CD Pipeline (GitHub Actions)
```
push/PR to any branch
        │
        ▼
┌─────────────────────────────────────────────┐
│            GitHub Actions Workflow            │
│                                             │
│  ┌──────────┐ ┌───────────┐ ┌────────────┐ │
│  │ Backend  │ │ Frontend  │ │  Security  │ │
│  │ Tests    │ │ Build +   │ │  Scans     │ │
│  │ (pytest) │ │ Playwright│ │ (semgrep + │ │
│  │          │ │           │ │  pip-audit)│ │
│  └────┬─────┘ └─────┬─────┘ └─────┬──────┘ │
│       │             │             │         │
│       └──────┬──────┘─────────────┘         │
│              │                              │
│       ALL MUST PASS                         │
│              │                              │
└──────────────┼──────────────────────────────┘
               │
        ┌──────▼──────┐        ┌──────────────────┐
        │ Merge to    │───────▶│ CD: Build Docker  │
        │ main        │        │ Push to ECR       │
        └─────────────┘        │ Deploy to Fargate │
                               └──────────────────┘
```

### Docker Architecture
```
┌─────────────────────────────────────────────────┐
│              docker-compose.yml                  │
│                                                  │
│  ┌──────────────────┐  ┌──────────────────────┐ │
│  │  frontend         │  │  backend              │ │
│  │  (Next.js)        │  │  (FastAPI + uvicorn)  │ │
│  │  Port: 3000       │──│  Port: 8000           │ │
│  │  standalone build │  │  slim Python image    │ │
│  └──────────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### AWS ECS Fargate (Terraform)
```
┌───────────────────────────────────────────────────────────┐
│                        AWS VPC                             │
│                                                           │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                 Application Load Balancer             │ │
│  │           (HTTPS termination, path routing)           │ │
│  └───────┬────────────────────────┬──────────────────────┘ │
│          │ /*                     │ /api/*, /health        │
│          ▼                        ▼                        │
│  ┌───────────────┐       ┌────────────────┐               │
│  │ ECS Service:  │       │ ECS Service:   │               │
│  │ frontend      │       │ backend        │               │
│  │ (Fargate)     │       │ (Fargate)      │               │
│  └───────────────┘       └────────────────┘               │
│                                                           │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ ECR Repos  │  │ CloudWatch   │  │ Secrets Manager  │  │
│  │ (images)   │  │ (logs)       │  │ (env vars)       │  │
│  └────────────┘  └──────────────┘  └──────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

## Out of Scope
- Changing any existing application functionality
- User authentication / accounts (deferred)
- Custom domain / DNS configuration
- Database setup (app is stateless)
- Auto-scaling policies (can be added post-deploy)
- Monitoring/alerting dashboards (Grafana, Datadog)

## AWS IAM Setup

| Item | Value |
|---|---|
| Account | 217019990640 |
| Deploy IAM User | `MSD_User` |
| ARN | `arn:aws:iam::217019990640:user/MSD_User` |
| Access Key ID | `AKIATFB3GIJYN7VQ6X46` |
| Region | `us-east-2` (US East - Ohio) |
| Key Type | Application running on AWS compute service |

**Required IAM policies** (must be attached to `MSD_User`):
- `AmazonECS_FullAccess` — create/manage ECS clusters, services, task definitions
- `AmazonEC2ContainerRegistryFullAccess` — push/pull Docker images to ECR
- `AmazonVPCFullAccess` — create VPC, subnets, security groups
- `ElasticLoadBalancingFullAccess` — create/manage ALB and target groups
- `CloudWatchLogsFullAccess` — create log groups for container logs
- `IAMFullAccess` (or scoped) — create ECS task execution role
- `SecretsManagerReadWrite` (optional) — store env vars securely

**GitHub Secrets** (for CI/CD workflows):
- `AWS_ACCESS_KEY_ID` → `AKIATFB3GIJYN7VQ6X46`
- `AWS_SECRET_ACCESS_KEY` → *(needs correct value — see note below)*
- `AWS_REGION` → `us-east-2`

> **Note:** The secret access key in `aws_cred.md` is invalid (`:AKIATFB3GIJYN7VQ6X46` is the access key repeated). AWS secret keys are 40 characters long. Retrieve the correct secret from IAM console → Users → MSD_User → Security credentials → Access keys. If lost, create a new access key.

## GitHub CLI Setup
The CI/CD tasks require a GitHub repository with Actions enabled. Task 8 connects the local repo to GitHub via `gh` CLI (`gh auth login` + `gh repo create`), sets up the remote, and configures secrets before creating workflows.

## Dependencies
- v1 codebase (fully built and functional)
- v2 security hardening (all 12 tasks complete)
- AWS account 217019990640 with IAM user `MSD_User` and correct policies attached
- Correct AWS secret access key for `MSD_User` (40 chars) — current value in aws_cred.md is invalid
- GitHub CLI (`gh`) installed and authenticated
- Docker installed locally for build testing
