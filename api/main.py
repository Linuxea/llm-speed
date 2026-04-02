"""FastAPI backend for LLM Speed Monitor."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.db import get_connection

app = FastAPI(
    title="LLM Speed Monitor API",
    description="API for LLM performance monitoring",
    version="1.0.0",
)

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/providers")
def get_providers():
    """Get all providers with their models."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.id, p.name, p.display_name, p.base_url,
            m.id as model_id, m.model_id, m.display_name as model_display_name
        FROM providers p
        LEFT JOIN models m ON m.provider_id = p.id
        ORDER BY p.display_name, m.display_name
    """)

    rows = cursor.fetchall()
    conn.close()

    providers = {}
    for row in rows:
        pid, name, display_name, base_url, mid, model_id, model_display = row

        if name not in providers:
            providers[name] = {
                "id": pid,
                "name": name,
                "display_name": display_name,
                "base_url": base_url,
                "models": []
            }

        if model_id:
            providers[name]["models"].append({
                "id": mid,
                "model_id": model_id,
                "display_name": model_display
            })

    return list(providers.values())


@app.get("/api/metrics")
def get_metrics(
    hours: int = Query(24, ge=1, le=168),
    provider: str = Query(None),
    success_only: bool = Query(True),
):
    """Get metrics within time range."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            datetime(m.recorded_at, 'localtime') as recorded_at,
            m.ttft_ms,
            m.total_time_ms,
            m.tokens_per_second,
            m.success,
            mo.model_id,
            mo.display_name as model_display_name,
            p.name as provider_name,
            p.display_name as provider_display_name
        FROM metrics m
        JOIN models mo ON m.model_id = mo.id
        JOIN providers p ON mo.provider_id = p.id
        WHERE m.recorded_at >= datetime('now', ?)
    """
    params = [f"-{hours} hours"]

    if provider:
        query += " AND p.name = ?"
        params.append(provider)

    if success_only:
        query += " AND m.success = 1"

    query += " ORDER BY m.recorded_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/api/latest")
def get_latest():
    """Get latest metric for each model (success only)."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            datetime(m.recorded_at, 'localtime') as recorded_at,
            m.ttft_ms,
            m.total_time_ms,
            m.tokens_per_second,
            mo.model_id,
            mo.display_name as model_display_name,
            p.name as provider_name,
            p.display_name as provider_display_name
        FROM metrics m
        JOIN models mo ON m.model_id = mo.id
        JOIN providers p ON mo.provider_id = p.id
        WHERE m.success = 1
        AND m.id IN (
            SELECT MAX(id) FROM metrics WHERE success = 1 GROUP BY model_id
        )
        ORDER BY m.tokens_per_second DESC
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/api/aggregate")
def get_aggregate(hours: int = Query(24, ge=1, le=168)):
    """Get aggregated statistics per model."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            p.display_name as provider_display_name,
            mo.display_name as model_display_name,
            AVG(m.tokens_per_second) as avg_tokens_per_second,
            AVG(m.ttft_ms) as avg_ttft_ms,
            COUNT(*) as total_requests,
            SUM(CASE WHEN m.success = 1 THEN 1 ELSE 0 END) as successful_requests
        FROM metrics m
        JOIN models mo ON m.model_id = mo.id
        JOIN providers p ON mo.provider_id = p.id
        WHERE m.recorded_at >= datetime('now', ?)
        GROUP BY mo.id
        ORDER BY avg_tokens_per_second DESC
    """

    cursor.execute(query, [f"-{hours} hours"])
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "provider_display_name": row[0],
            "model_display_name": row[1],
            "avg_tokens_per_second": round(row[2], 1) if row[2] else 0,
            "avg_ttft_ms": round(row[3], 0) if row[3] else 0,
            "total_requests": row[4],
            "success_rate": round(row[5] / row[4] * 100, 1) if row[4] > 0 else 0
        })

    return result


@app.get("/api/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
