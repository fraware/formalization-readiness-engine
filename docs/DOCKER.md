# Docker Compose stack

See `docker compose up --build` from repo root.

Services: `api` (8000), `review-ui` (8080), `worker`, `redis`, optional `lean` profile.

Job metadata uses SQLite at `FRE_JOBS_DB` (default `/data/jobs.db` in Compose). PostgreSQL deferred for v0.

## Async jobs (RQ)

| Job type | Endpoint |
|----------|----------|
| extract_report | `POST /jobs/extract` |
| check_lean | `POST /jobs/check-lean` |
| run_baselines | `POST /jobs/run-baselines` (Wave 3 stub) |

Poll with `GET /jobs/{id}`.

## Environment

- `REDIS_URL` — RQ broker (default `redis://redis:6379/0` in Compose)
- `OPENAI_API_KEY` — required for live extraction jobs
- `FRE_JOBS_INLINE=1` — run jobs in-process without Redis (local dev)

## Why RQ

RQ keeps the v0 worker surface minimal (three task types, one queue). Celery remains an option if we need periodic tasks or multi-queue routing later.

## Example

```bash
curl -s -X POST http://localhost:8000/jobs/extract \
  -H "Content-Type: application/json" \
  -d '{"unit_path":"examples/finite_tree/unit.json"}'
curl -s http://localhost:8000/jobs/<job-id>
```
