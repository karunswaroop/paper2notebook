# Branch Protection Setup

## Required Settings for `main`

Configure these branch protection rules on the `main` branch to enforce CI checks before merge.

### Rules
- **Require pull request reviews**: At least 1 approval before merging
- **Require status checks to pass**: All of the following must be green:
  - `backend-tests`
  - `frontend-build`
  - `e2e-tests`
  - `security-scan`
- **Require branches to be up to date**: PR must be rebased on latest main
- **No direct pushes**: All changes go through PRs

### Setup via GitHub CLI

```bash
# Ensure you're authenticated
gh auth status

# Set branch protection rules (requires admin access)
gh api repos/{owner}/{repo}/branches/main/protection \
  --method PUT \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "backend-tests",
      "frontend-build",
      "e2e-tests",
      "security-scan"
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1
  },
  "restrictions": null
}
EOF
```

Replace `{owner}/{repo}` with your actual GitHub owner and repository name (e.g., `karunswaroop/paper2notebook`).

### Verify

```bash
gh api repos/{owner}/{repo}/branches/main/protection --jq '.required_status_checks.contexts[]'
```

Should output:
```
backend-tests
frontend-build
e2e-tests
security-scan
```
