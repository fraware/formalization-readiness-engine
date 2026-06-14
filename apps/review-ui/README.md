# Review UI

Minimal static review interface for inspecting example readiness artifacts and validating structured review submissions.

## Prerequisites

Install API dependencies and start the backend from the repository root:

```bash
python -m pip install -r requirements-api.txt
make run-api
```

On Windows:

```powershell
.\scripts\dev.ps1 run-api
```

## Run the UI

Serve this directory on port 8080:

```bash
make run-review-ui
```

On Windows:

```powershell
.\scripts\dev.ps1 run-review-ui
```

Open `http://127.0.0.1:8080` in a browser. The page loads example artifact metadata from the API, fetches committed JSON from `examples/`, and posts review submissions to `POST /validate/review-submission`.

## Untrusted source policy

Loaded example JSON (unit statements, proofs, and readiness report fields) is treated as untrusted text. The UI renders artifact strings with DOM APIs (`textContent`, `createElement`, and form `.value` assignments) rather than `innerHTML`, so malicious payloads display as literal text without script execution.

## Scope

This is a first-version review surface. It does not replace the full annotation workflow described in `docs/review/REVIEWER_GUIDE.md`. It exists to validate the Phase 5 API contract and give reviewers a thin inspection path before interface polish.
