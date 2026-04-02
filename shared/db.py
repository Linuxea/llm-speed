"""SQLite database operations."""

import sqlite3
from datetime import datetime
from typing import Optional

from .models import Config, MetricResult


DB_PATH = "llm_speed.db"


def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(config: Config) -> None:
    """Initialize database tables and populate providers/models from config.

    Args:
        config: Configuration object with providers and models.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Create tables
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            base_url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_id INTEGER NOT NULL,
            model_id TEXT NOT NULL,
            display_name TEXT NOT NULL,
            FOREIGN KEY (provider_id) REFERENCES providers(id),
            UNIQUE(provider_id, model_id)
        );

        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id INTEGER NOT NULL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ttft_ms REAL,
            total_time_ms REAL,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            tokens_per_second REAL,
            success BOOLEAN,
            error_message TEXT,
            FOREIGN KEY (model_id) REFERENCES models(id)
        );

        CREATE INDEX IF NOT EXISTS idx_metrics_model_time
            ON metrics(model_id, recorded_at);
        CREATE INDEX IF NOT EXISTS idx_metrics_time
            ON metrics(recorded_at);
    """)

    # Populate providers and models from config
    for provider in config.providers:
        cursor.execute(
            """INSERT OR IGNORE INTO providers (name, display_name, base_url)
               VALUES (?, ?, ?)""",
            (provider.name, provider.display_name, provider.base_url)
        )

        if cursor.rowcount > 0:
            provider_id = cursor.lastrowid
        else:
            cursor.execute(
                "SELECT id FROM providers WHERE name = ?",
                (provider.name,)
            )
            provider_id = cursor.fetchone()[0]

        for model in provider.models:
            cursor.execute(
                """INSERT OR IGNORE INTO models (provider_id, model_id, display_name)
                   VALUES (?, ?, ?)""",
                (provider_id, model.id, model.display_name)
            )

    conn.commit()
    conn.close()


def save_metric(metric: MetricResult) -> None:
    """Save a metric result to the database.

    Args:
        metric: MetricResult from a model test.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get model ID
    cursor.execute(
        """SELECT m.id FROM models m
           JOIN providers p ON m.provider_id = p.id
           WHERE p.name = ? AND m.model_id = ?""",
        (metric.provider_name, metric.model_id)
    )
    row = cursor.fetchone()

    if row is None:
        conn.close()
        raise ValueError(f"Model not found: {metric.provider_name}/{metric.model_id}")

    model_id = row[0]

    cursor.execute(
        """INSERT INTO metrics
           (model_id, ttft_ms, total_time_ms, prompt_tokens, completion_tokens,
            tokens_per_second, success, error_message)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (model_id, metric.ttft_ms, metric.total_time_ms, metric.prompt_tokens,
         metric.completion_tokens, metric.tokens_per_second, metric.success,
         metric.error_message)
    )

    conn.commit()
    conn.close()


def get_metrics(
    hours: int = 24,
    provider_name: Optional[str] = None,
    model_id: Optional[str] = None
) -> list[dict]:
    """Query metrics from database.

    Args:
        hours: Number of hours to look back.
        provider_name: Filter by provider name (optional).
        model_id: Filter by model ID (optional).

    Returns:
        List of metric records as dictionaries.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            m.recorded_at,
            m.ttft_ms,
            m.total_time_ms,
            m.prompt_tokens,
            m.completion_tokens,
            m.tokens_per_second,
            m.success,
            m.error_message,
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

    if provider_name:
        query += " AND p.name = ?"
        params.append(provider_name)

    if model_id:
        query += " AND mo.model_id = ?"
        params.append(model_id)

    query += " ORDER BY m.recorded_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_latest_metrics() -> list[dict]:
    """Get the most recent metric for each model.

    Returns:
        List of latest metric records per model.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            m.recorded_at,
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
        WHERE m.id IN (
            SELECT MAX(id) FROM metrics GROUP BY model_id
        )
        ORDER BY p.display_name, mo.display_name
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]
