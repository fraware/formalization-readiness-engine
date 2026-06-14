# Docker Compose stack

The Formalization Readiness Engine ships a Docker Compose stack for local API, review UI, and async extraction jobs. Run from the repository root:

```bash
docker compose up --build
```

Copy `.env.example` to `.env` and set `OPENAI_API_KEY` before submitting live extraction jobs.

## Services

| Service | Port | Purpose |
|---------|------|---------|
| `api` | 8000 | FastAPI backend: validation, alignment, async job enqueue |
| `review-ui` | 8080 | Minimal static review interface |
| `worker` | — | RQ worker for long-running extraction and Lean jobs |
| `redis` | 6379 | Job broker |
| `lean` | — | Optional Lean check environment (`--profile lean`) |

Job metadata uses SQLite at `FRE_JOBS_DB` (default `/data/jobs.db` in Compose). PostgreSQL is deferred for v0.

## Async jobs (RQ)

| Job type | Endpoint | Notes |
|----------|----------|-------|
| `extract_report` | `POST /jobs/extract` | Live readiness extraction |
| `check_lean` | `POST /jobs/check-lean` | Lean typecheck through pinned project |
| `run_baselines` | `POST /jobs/run-baselines` | Wave 3 baseline stub |

Poll job status with `GET /jobs/{id}`.

### Example

```bash
curl -s -X POST http://localhost:8000/jobs/extract \
  -H "Content-Type: application/json" \
  -d '{"unit_path":"examples/finite_tree/unit.json"}'

curl -s http://localhost:8000/jobs/<job-id>
```

## Environment variables

| Variable | Default (Compose) | Purpose |
|----------|-------------------|---------|
| `REDIS_URL` | `redis://redis:6379/0` | RQ broker |
| `OPENAI_API_KEY` | unset | Required for live extraction jobs |
| `FRE_MODEL_NAME` | `gpt-4.1` | Model override |
| `FRE_JOBS_DB` | `/data/jobs.db` | SQLite job metadata path |
| `FRE_ARTIFACT_DIR` | `/data/artifacts` | Generated artifact storage |
| `FRE_JOBS_INLINE` | `0` | Set to `1` to run jobs in-process without Redis (local dev) |
| `FRE_REVIEW_WRITE_ENABLED` | `0` | Review write path (disabled by default) |

See `.env.example` for the full list.

## Local development without Docker

You can run the API and worker directly on the host:

```bash
make setup-api
make run-api
```

Set `FRE_JOBS_INLINE=1` to execute jobs in the API process without Redis. This is useful for quick local testing but not recommended for concurrent workloads.

On Windows:

```powershell
.\scripts\dev.ps1 setup-api
.\scripts\dev.ps1 run-api
```

## Why RQ

RQ keeps the v0 worker surface minimal (three task types, one queue). Celery remains an option if the project later needs periodic tasks or multi-queue routing.

## Lean profile

Build and run the optional Lean service for containerized typechecking:

```bash
docker compose --profile lean up --build lean
```

Normal Python CI does not build mathlib. Local Lean checks use the pinned `lean/` Lake project (see `lean/README.md`).
