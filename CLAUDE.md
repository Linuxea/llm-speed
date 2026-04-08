# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running

```bash
# Start everything (auto-installs deps, starts backend + collector + streamlit)
./start.sh              # default: streamlit frontend
./start.sh nextjs       # next.js frontend
./start.sh backend      # API + collector only

# Individual services
python -m api.main              # FastAPI backend, port 8000
python -m collector.main        # Collector (background loop)
streamlit run dashboard/app.py  # Streamlit, port 8501
cd web && npm run dev           # Next.js, port 3000

# One-shot collection (no loop)
python -m collector.main --once
```

## Architecture

Data flow: **collector** calls LLM APIs → **SQLite** (`llm_speed.db`) → **FastAPI** serves REST → **Streamlit/Next.js** displays.

- `config.yaml` defines providers and models. API keys go in `.env` as `{NAME}_API_KEY`.
- `shared/` is imported by both `collector/` and `api/`. Both prepend the project root to `sys.path`.
- `collector/tester.py` uses streaming OpenAI-compatible API calls to measure TTFT and tokens/s. It handles both regular and reasoning models (checks `reasoning_content` alongside `content`).
- SQLite stores UTC timestamps. The API converts to local time via `datetime('recorded_at', 'localtime')`. Streamlit further converts to `Asia/Shanghai` via pandas.
- Database has 3 tables: `providers`, `models`, `metrics`. Schema is in `shared/db.py`, initialized from `config.yaml` on startup.

## API Endpoints

- `GET /api/providers` — providers + models
- `GET /api/metrics?hours=24&provider=&success_only=true` — raw metrics
- `GET /api/latest` — latest success per model
- `GET /api/aggregate?hours=24` — per-model averages
- `GET /api/health` — health check

## Key Conventions

- Provider `name` in config.yaml must match the env var prefix: `name: deepseek` → `DEEPSEEK_API_KEY`.
- All LLM APIs use OpenAI-compatible chat completions format via the `openai` Python SDK.
- No test framework configured. Manual testing via `python -m collector.main --once` or `curl localhost:8000/api/health`.
