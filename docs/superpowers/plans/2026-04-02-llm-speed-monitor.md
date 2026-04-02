# LLM Speed Monitor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dual-process LLM performance monitoring system with a collector for metrics gathering and a Streamlit dashboard for visualization.

**Architecture:** Collector process runs independently to test LLM APIs at configured intervals, storing results in SQLite. Streamlit dashboard reads from SQLite to display real-time status and historical trends.

**Tech Stack:** Python 3.10+, OpenAI SDK, SQLite, Streamlit, pandas, Plotly

---

## File Structure

```
llm-speed/
├── config.yaml              # Provider and model configuration
├── .env.example             # API key template
├── llm_speed.db             # SQLite database (generated)
│
├── shared/
│   ├── __init__.py
│   ├── config.py            # Config loader (YAML + .env)
│   ├── models.py            # Dataclasses for config/metrics
│   └── db.py                # SQLite operations
│
├── collector/
│   ├── __init__.py
│   ├── tester.py            # LLM API tester with metrics
│   └── main.py              # Scheduler entry point
│
├── dashboard/
│   ├── __init__.py
│   ├── app.py               # Streamlit application
│   └── charts.py            # Chart generation functions
│
├── requirements.txt
├── start.sh                 # Startup script
└── README.md
```

---

### Task 1: Project Initialization

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `config.yaml`
- Create: `shared/__init__.py`
- Create: `collector/__init__.py`
- Create: `dashboard/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```txt
openai>=1.0.0
streamlit>=1.30.0
pandas>=2.0.0
plotly>=5.18.0
pyyaml>=6.0
python-dotenv>=1.0.0
```

- [ ] **Step 2: Create .env.example**

```env
# Copy this file to .env and fill in your API keys
# Key format: {PROVIDER_NAME}_API_KEY (uppercase)

DEEPSEEK_API_KEY=sk-your-key-here
OPENAI_API_KEY=sk-your-key-here
ZHIPU_API_KEY=your-key-here
```

- [ ] **Step 3: Create config.yaml**

```yaml
# Collector settings
collector:
  interval_minutes: 5
  timeout_seconds: 60
  test_prompt: "请用中文简短介绍一下人工智能，不超过100字。"
  max_tokens: 100

# Provider configurations
providers:
  - name: deepseek
    display_name: DeepSeek
    base_url: https://api.deepseek.com/v1
    models:
      - id: deepseek-chat
        display_name: DeepSeek Chat
      - id: deepseek-reasoner
        display_name: DeepSeek Reasoner

  - name: openai
    display_name: OpenAI
    base_url: https://api.openai.com/v1
    models:
      - id: gpt-4o
        display_name: GPT-4o
      - id: gpt-4o-mini
        display_name: GPT-4o Mini

  - name: zhipu
    display_name: 智谱 AI
    base_url: https://open.bigmodel.cn/api/paas/v4
    models:
      - id: glm-4-flash
        display_name: GLM-4 Flash
```

- [ ] **Step 4: Create package __init__.py files**

```bash
mkdir -p shared collector dashboard
touch shared/__init__.py collector/__init__.py dashboard/__init__.py
```

- [ ] **Step 5: Install dependencies**

```bash
pip install -r requirements.txt
```

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .env.example config.yaml shared/__init__.py collector/__init__.py dashboard/__init__.py
git commit -m "chore: initialize project structure and dependencies"
```

---

### Task 2: Shared Configuration Module

**Files:**
- Create: `shared/config.py`
- Create: `shared/models.py`

- [ ] **Step 1: Create shared/models.py with dataclasses**

```python
"""Data models for configuration and metrics."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelConfig:
    """Model configuration."""
    id: str
    display_name: str


@dataclass
class ProviderConfig:
    """Provider configuration."""
    name: str
    display_name: str
    base_url: str
    models: list[ModelConfig] = field(default_factory=list)
    api_key: Optional[str] = None  # Loaded from .env


@dataclass
class CollectorConfig:
    """Collector settings."""
    interval_minutes: int = 5
    timeout_seconds: int = 60
    test_prompt: str = "Hello"
    max_tokens: int = 100


@dataclass
class Config:
    """Root configuration."""
    collector: CollectorConfig = field(default_factory=CollectorConfig)
    providers: list[ProviderConfig] = field(default_factory=list)


@dataclass
class MetricResult:
    """Result of a single model test."""
    provider_name: str
    model_id: str
    ttft_ms: Optional[float] = None
    total_time_ms: Optional[float] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    tokens_per_second: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
```

- [ ] **Step 2: Create shared/config.py**

```python
"""Configuration loader from YAML and environment variables."""

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

from .models import Config, CollectorConfig, ProviderConfig, ModelConfig


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from YAML file and environment variables.

    Args:
        config_path: Path to config.yaml. Defaults to ./config.yaml

    Returns:
        Config object with all settings loaded.
    """
    if config_path is None:
        config_path = "config.yaml"

    # Load .env file
    load_dotenv()

    # Load YAML
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    # Parse collector config
    collector_raw = raw.get("collector", {})
    collector = CollectorConfig(
        interval_minutes=collector_raw.get("interval_minutes", 5),
        timeout_seconds=collector_raw.get("timeout_seconds", 60),
        test_prompt=collector_raw.get("test_prompt", "Hello"),
        max_tokens=collector_raw.get("max_tokens", 100),
    )

    # Parse providers
    providers = []
    for p_raw in raw.get("providers", []):
        provider_name = p_raw["name"]
        api_key = os.getenv(f"{provider_name.upper()}_API_KEY")

        models = [
            ModelConfig(id=m["id"], display_name=m["display_name"])
            for m in p_raw.get("models", [])
        ]

        provider = ProviderConfig(
            name=provider_name,
            display_name=p_raw["display_name"],
            base_url=p_raw["base_url"],
            models=models,
            api_key=api_key,
        )
        providers.append(provider)

    return Config(collector=collector, providers=providers)
```

- [ ] **Step 3: Test configuration loading**

```bash
python -c "from shared.config import load_config; c = load_config(); print(f'Providers: {len(c.providers)}'); print(f'Interval: {c.collector.interval_minutes}m')"
```

Expected output:
```
Providers: 3
Interval: 5m
```

- [ ] **Step 4: Commit**

```bash
git add shared/models.py shared/config.py
git commit -m "feat(shared): add configuration loader and data models"
```

---

### Task 3: Database Module

**Files:**
- Create: `shared/db.py`

- [ ] **Step 1: Create shared/db.py**

```python
"""SQLite database operations."""

import sqlite3
from datetime import datetime
from pathlib import Path
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
```

- [ ] **Step 2: Test database initialization**

```bash
python -c "
from shared.config import load_config
from shared.db import init_db, get_connection

config = load_config()
init_db(config)

conn = get_connection()
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM providers')
print(f'Providers: {cur.fetchone()[0]}')
cur.execute('SELECT COUNT(*) FROM models')
print(f'Models: {cur.fetchone()[0]}')
conn.close()
"
```

Expected output:
```
Providers: 3
Models: 5
```

- [ ] **Step 3: Commit**

```bash
git add shared/db.py
git commit -m "feat(shared): add SQLite database module"
```

---

### Task 4: LLM Tester Module

**Files:**
- Create: `collector/tester.py`

- [ ] **Step 1: Create collector/tester.py**

```python
"""LLM API tester with performance metrics."""

import asyncio
import time
from typing import AsyncGenerator

from openai import AsyncOpenAI

from shared.models import ProviderConfig, CollectorConfig, MetricResult


async def test_model(
    provider: ProviderConfig,
    config: CollectorConfig
) -> MetricResult:
    """Test a single model and return metrics.

    Args:
        provider: Provider configuration with models to test.
        config: Collector configuration with test settings.

    Returns:
        MetricResult with performance data.
    """
    if not provider.api_key:
        return MetricResult(
            provider_name=provider.name,
            model_id="",
            success=False,
            error_message="API key not configured"
        )

    client = AsyncOpenAI(
        api_key=provider.api_key,
        base_url=provider.base_url,
        timeout=config.timeout_seconds,
    )

    results = []

    for model in provider.models:
        result = await _test_single_model(client, model.id, provider.name, config)
        results.append(result)

    # Return first result for now (or modify to return list)
    return results[0] if results else MetricResult(
        provider_name=provider.name,
        model_id="",
        success=False,
        error_message="No models configured"
    )


async def test_all_models(
    providers: list[ProviderConfig],
    config: CollectorConfig
) -> list[MetricResult]:
    """Test all models from all providers.

    Args:
        providers: List of provider configurations.
        config: Collector configuration.

    Returns:
        List of MetricResult for all tested models.
    """
    results = []

    for provider in providers:
        if not provider.api_key:
            for model in provider.models:
                results.append(MetricResult(
                    provider_name=provider.name,
                    model_id=model.id,
                    success=False,
                    error_message="API key not configured"
                ))
            continue

        client = AsyncOpenAI(
            api_key=provider.api_key,
            base_url=provider.base_url,
            timeout=config.timeout_seconds,
        )

        for model in provider.models:
            result = await _test_single_model(client, model.id, provider.name, config)
            results.append(result)

            # Small delay between tests to avoid rate limits
            await asyncio.sleep(1)

    return results


async def _test_single_model(
    client: AsyncOpenAI,
    model_id: str,
    provider_name: str,
    config: CollectorConfig
) -> MetricResult:
    """Test a single model and calculate metrics.

    Args:
        client: OpenAI async client.
        model_id: Model identifier.
        provider_name: Provider name for result.
        config: Collector configuration.

    Returns:
        MetricResult with performance data.
    """
    start_time = time.time()

    try:
        response = await client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": config.test_prompt}],
            max_tokens=config.max_tokens,
            stream=True,
            stream_options={"include_usage": True},
        )

        # Measure TTFT (Time To First Token)
        first_chunk = None
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                first_chunk = chunk
                break

        ttft_ms = (time.time() - start_time) * 1000 if first_chunk else None

        # Consume remaining stream and get usage
        completion_tokens = 0
        prompt_tokens = 0

        async for chunk in response:
            if chunk.usage:
                completion_tokens = chunk.usage.completion_tokens
                prompt_tokens = chunk.usage.prompt_tokens

        total_time_ms = (time.time() - start_time) * 1000

        # Calculate tokens per second
        tokens_per_second = None
        if ttft_ms and completion_tokens:
            generation_time_ms = total_time_ms - ttft_ms
            if generation_time_ms > 0:
                tokens_per_second = completion_tokens / (generation_time_ms / 1000)

        return MetricResult(
            provider_name=provider_name,
            model_id=model_id,
            ttft_ms=ttft_ms,
            total_time_ms=total_time_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            tokens_per_second=tokens_per_second,
            success=True,
        )

    except Exception as e:
        total_time_ms = (time.time() - start_time) * 1000
        return MetricResult(
            provider_name=provider_name,
            model_id=model_id,
            total_time_ms=total_time_ms,
            success=False,
            error_message=str(e),
        )
```

- [ ] **Step 2: Test the tester with a real API (manual verification)**

```bash
# Make sure you have DEEPSEEK_API_KEY in .env
python -c "
import asyncio
from shared.config import load_config
from collector.tester import test_all_models

async def main():
    config = load_config()
    results = await test_all_models(config.providers, config.collector)
    for r in results:
        status = '✓' if r.success else '✗'
        speed = f'{r.tokens_per_second:.1f} t/s' if r.tokens_per_second else 'N/A'
        print(f'{status} {r.provider_name}/{r.model_id}: {speed}')

asyncio.run(main())
"
```

- [ ] **Step 3: Commit**

```bash
git add collector/tester.py
git commit -m "feat(collector): add LLM API tester with metrics calculation"
```

---

### Task 5: Collector Main Entry Point

**Files:**
- Create: `collector/main.py`

- [ ] **Step 1: Create collector/main.py**

```python
"""Collector main entry point - runs scheduled model tests."""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.config import load_config
from shared.db import init_db, save_metric
from collector.tester import test_all_models

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def collect_once(config) -> None:
    """Run a single collection cycle.

    Args:
        config: Configuration object.
    """
    logger.info("Starting collection cycle...")

    results = await test_all_models(config.providers, config.collector)

    for result in results:
        try:
            save_metric(result)

            status = "✓" if result.success else "✗"
            if result.success:
                speed = f"{result.tokens_per_second:.1f} t/s" if result.tokens_per_second else "N/A"
                ttft = f"{result.ttft_ms:.0f}ms" if result.ttft_ms else "N/A"
                logger.info(f"{status} {result.provider_name}/{result.model_id}: {speed}, TTFT: {ttft}")
            else:
                logger.warning(f"{status} {result.provider_name}/{result.model_id}: {result.error_message}")

        except Exception as e:
            logger.error(f"Failed to save metric for {result.provider_name}/{result.model_id}: {e}")

    logger.info(f"Collection cycle complete. Tested {len(results)} models.")


async def run_collector(interval_minutes: int = 5) -> None:
    """Run collector on a schedule.

    Args:
        interval_minutes: Interval between collection cycles.
    """
    config = load_config()

    # Initialize database
    logger.info("Initializing database...")
    init_db(config)

    logger.info(f"Starting collector with {interval_minutes} minute interval")
    logger.info(f"Monitoring {len(config.providers)} providers")

    while True:
        try:
            await collect_once(config)
        except Exception as e:
            logger.error(f"Collection cycle failed: {e}")

        logger.info(f"Sleeping for {interval_minutes} minutes...")
        await asyncio.sleep(interval_minutes * 60)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="LLM Speed Monitor Collector")
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Collection interval in minutes (overrides config)",
    )
    args = parser.parse_args()

    config = load_config()
    interval = args.interval or config.collector.interval_minutes

    try:
        asyncio.run(run_collector(interval))
    except KeyboardInterrupt:
        logger.info("Collector stopped by user")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test collector startup (quick test)**

```bash
# This will run one collection cycle, then you can Ctrl+C
timeout 10 python -m collector.main --interval 1 || true
```

- [ ] **Step 3: Commit**

```bash
git add collector/main.py
git commit -m "feat(collector): add main entry point with scheduler"
```

---

### Task 6: Dashboard Charts Module

**Files:**
- Create: `dashboard/charts.py`

- [ ] **Step 1: Create dashboard/charts.py**

```python
"""Chart generation functions for the dashboard."""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_speed_trend_chart(df: pd.DataFrame, title: str = "Token 速度趋势") -> go.Figure:
    """Create a line chart showing token speed over time.

    Args:
        df: DataFrame with columns: recorded_at, tokens_per_second, model_display_name
        title: Chart title.

    Returns:
        Plotly Figure object.
    """
    if df.empty:
        return go.Figure().add_annotation(text="暂无数据", showarrow=False)

    fig = go.Figure()

    # Group by model
    for model_name in df["model_display_name"].unique():
        model_df = df[df["model_display_name"] == model_name].sort_values("recorded_at")

        fig.add_trace(go.Scatter(
            x=model_df["recorded_at"],
            y=model_df["tokens_per_second"],
            mode="lines+markers",
            name=model_name,
            hovertemplate="%{y:.1f} t/s<br>%{x}<extra></extra>",
        ))

    fig.update_layout(
        title=title,
        xaxis_title="时间",
        yaxis_title="Token 速度 (tokens/s)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=400,
    )

    return fig


def create_ttft_trend_chart(df: pd.DataFrame, title: str = "TTFT 延迟趋势") -> go.Figure:
    """Create a line chart showing TTFT over time.

    Args:
        df: DataFrame with columns: recorded_at, ttft_ms, model_display_name
        title: Chart title.

    Returns:
        Plotly Figure object.
    """
    if df.empty:
        return go.Figure().add_annotation(text="暂无数据", showarrow=False)

    fig = go.Figure()

    for model_name in df["model_display_name"].unique():
        model_df = df[df["model_display_name"] == model_name].sort_values("recorded_at")

        fig.add_trace(go.Scatter(
            x=model_df["recorded_at"],
            y=model_df["ttft_ms"],
            mode="lines+markers",
            name=model_name,
            hovertemplate="%{y:.0f} ms<br>%{x}<extra></extra>",
        ))

    fig.update_layout(
        title=title,
        xaxis_title="时间",
        yaxis_title="TTFT (毫秒)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=400,
    )

    return fig


def create_performance_bar_chart(df: pd.DataFrame, title: str = "性能排行") -> go.Figure:
    """Create a horizontal bar chart comparing average performance.

    Args:
        df: DataFrame with aggregated metrics.
        title: Chart title.

    Returns:
        Plotly Figure object.
    """
    if df.empty:
        return go.Figure().add_annotation(text="暂无数据", showarrow=False)

    # Sort by tokens_per_second descending
    df = df.sort_values("tokens_per_second", ascending=True)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=df["model_display_name"],
        x=df["tokens_per_second"],
        orientation="h",
        text=df["tokens_per_second"].apply(lambda x: f"{x:.1f}"),
        textposition="outside",
        hovertemplate="%{y}: %{x:.1f} t/s<extra></extra>",
    ))

    fig.update_layout(
        title=title,
        xaxis_title="平均 Token 速度 (tokens/s)",
        yaxis_title="",
        height=max(300, len(df) * 40),
        showlegend=False,
    )

    return fig


def aggregate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate metrics by model for summary display.

    Args:
        df: Raw metrics DataFrame.

    Returns:
        Aggregated DataFrame with mean values.
    """
    if df.empty:
        return pd.DataFrame()

    agg_df = df.groupby(["provider_display_name", "model_display_name"]).agg({
        "tokens_per_second": "mean",
        "ttft_ms": "mean",
        "success": "mean",  # This gives us success rate
    }).reset_index()

    agg_df.columns = [
        "provider_display_name",
        "model_display_name",
        "tokens_per_second",
        "ttft_ms",
        "success_rate",
    ]

    # Round values
    agg_df["tokens_per_second"] = agg_df["tokens_per_second"].round(1)
    agg_df["ttft_ms"] = agg_df["ttft_ms"].round(0)
    agg_df["success_rate"] = (agg_df["success_rate"] * 100).round(1)

    return agg_df.sort_values("tokens_per_second", ascending=False)
```

- [ ] **Step 2: Commit**

```bash
git add dashboard/charts.py
git commit -m "feat(dashboard): add chart generation functions"
```

---

### Task 7: Streamlit Dashboard Application

**Files:**
- Create: `dashboard/app.py`

- [ ] **Step 1: Create dashboard/app.py**

```python
"""Streamlit dashboard for LLM Speed Monitor."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.db import get_metrics, get_latest_metrics
from dashboard.charts import (
    create_speed_trend_chart,
    create_ttft_trend_chart,
    create_performance_bar_chart,
    aggregate_metrics,
)

# Page config
st.set_page_config(
    page_title="LLM Speed Monitor",
    page_icon="🚀",
    layout="wide",
)


def main():
    st.title("🚀 LLM Speed Monitor")
    st.caption("实时监控大模型 API 性能")

    # Sidebar - Time range selector
    st.sidebar.header("设置")

    time_range = st.sidebar.radio(
        "时间范围",
        options=[1, 6, 24, 168],
        format_func=lambda x: {
            1: "最近 1 小时",
            6: "最近 6 小时",
            24: "最近 24 小时",
            168: "最近 7 天",
        }[x],
        index=2,  # Default to 24 hours
    )

    # Provider filter
    all_metrics = get_metrics(hours=time_range)
    if all_metrics:
        providers = sorted(set(m["provider_display_name"] for m in all_metrics))
        selected_providers = st.sidebar.multiselect(
            "服务商筛选",
            options=providers,
            default=providers,
        )
    else:
        selected_providers = []

    # Filter data
    if selected_providers:
        filtered_metrics = [
            m for m in all_metrics
            if m["provider_display_name"] in selected_providers
        ]
    else:
        filtered_metrics = all_metrics

    df = pd.DataFrame(filtered_metrics)

    if not df.empty:
        df["recorded_at"] = pd.to_datetime(df["recorded_at"])

    # Latest status cards
    st.header("📊 实时状态")
    latest = get_latest_metrics()

    if latest:
        cols = st.columns(min(len(latest), 4))

        for i, metric in enumerate(latest[:4]):
            with cols[i % 4]:
                status_emoji = "✅" if metric["success"] else "❌"

                if metric["success"] and metric["tokens_per_second"]:
                    speed = f"{metric['tokens_per_second']:.1f} t/s"
                    ttft = f"{metric['ttft_ms']:.0f} ms" if metric["ttft_ms"] else "N/A"
                else:
                    speed = "N/A"
                    ttft = "N/A"

                st.metric(
                    label=f"{status_emoji} {metric['provider_display_name']}",
                    value=speed,
                    delta=f"TTFT: {ttft}",
                )
    else:
        st.info("暂无数据，请等待采集器运行")

    st.divider()

    # Charts
    st.header("📈 性能趋势")

    if not df.empty:
        # Filter successful only for charts
        success_df = df[df["success"] == True]

        col1, col2 = st.columns(2)

        with col1:
            speed_chart = create_speed_trend_chart(success_df)
            st.plotly_chart(speed_chart, use_container_width=True)

        with col2:
            ttft_chart = create_ttft_trend_chart(success_df)
            st.plotly_chart(ttft_chart, use_container_width=True)

        st.divider()

        # Performance ranking
        st.header("🏆 性能排行")

        agg_df = aggregate_metrics(success_df)

        if not agg_df.empty:
            col1, col2 = st.columns([2, 3])

            with col1:
                bar_chart = create_performance_bar_chart(agg_df)
                st.plotly_chart(bar_chart, use_container_width=True)

            with col2:
                # Display table
                display_df = agg_df.copy()
                display_df.columns = ["服务商", "模型", "速度 (t/s)", "TTFT (ms)", "可用率 (%)"]
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                )
    else:
        st.warning("所选时间范围内没有数据")

    # Footer
    st.divider()
    if not df.empty:
        latest_time = df["recorded_at"].max()
        st.caption(f"最后更新: {latest_time.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test dashboard startup**

```bash
# Start streamlit (will open browser)
streamlit run dashboard/app.py --server.headless true &
sleep 3
curl -s http://localhost:8501 | head -20
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/app.py
git commit -m "feat(dashboard): add Streamlit dashboard application"
```

---

### Task 8: Documentation and Startup Script

**Files:**
- Create: `README.md`
- Create: `start.sh`
- Create: `.gitignore`

- [ ] **Step 1: Create .gitignore**

```gitignore
# Environment
.env
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/

# Database
*.db

# IDE
.vscode/
.idea/

# Streamlit
.streamlit/
```

- [ ] **Step 2: Create start.sh**

```bash
#!/bin/bash

# LLM Speed Monitor Startup Script

echo "🚀 Starting LLM Speed Monitor..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Please copy .env.example to .env and fill in your API keys."
    exit 1
fi

# Start collector in background
echo "📊 Starting collector..."
python -m collector.main &
COLLECTOR_PID=$!

# Start dashboard
echo "📈 Starting dashboard..."
streamlit run dashboard/app.py

# Cleanup on exit
trap "kill $COLLECTOR_PID 2>/dev/null" EXIT
```

- [ ] **Step 3: Make start.sh executable**

```bash
chmod +x start.sh
```

- [ ] **Step 4: Create README.md**

```markdown
# 🚀 LLM Speed Monitor

实时监控多家大模型服务商的 API 性能，包括 Token 生成速度和响应延迟。

## 功能

- 📊 **实时监控**: 定时测试各模型 API 的响应速度
- 📈 **趋势分析**: 查看历史性能数据变化趋势
- 🏆 **性能排行**: 对比不同服务商的性能表现
- 🔌 **多服务商支持**: 支持所有 OpenAI 兼容的 API

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Keys

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Keys
```

### 3. 启动服务

```bash
# 方式一：使用启动脚本（同时启动采集器和看板）
./start.sh

# 方式二：分别启动
python -m collector.main        # 启动采集器
streamlit run dashboard/app.py  # 启动看板
```

### 4. 访问看板

打开浏览器访问 http://localhost:8501

## 配置说明

### config.yaml

```yaml
collector:
  interval_minutes: 5      # 采集间隔（分钟）
  timeout_seconds: 60      # API 超时时间
  test_prompt: "..."       # 测试用的 prompt
  max_tokens: 100          # 最大生成 token 数

providers:
  - name: deepseek         # 服务商标识（用于 API Key 命名）
    display_name: DeepSeek # 显示名称
    base_url: https://api.deepseek.com/v1
    models:
      - id: deepseek-chat
        display_name: DeepSeek Chat
```

### .env

API Key 命名规则：`{PROVIDER_NAME}_API_KEY`（全大写）

```env
DEEPSEEK_API_KEY=sk-xxxxx
OPENAI_API_KEY=sk-xxxxx
ZHIPU_API_KEY=xxxxx
```

## 添加新的服务商

1. 在 `config.yaml` 的 `providers` 列表中添加配置
2. 在 `.env` 中添加对应的 API Key
3. 重启采集器

## 指标说明

| 指标 | 说明 |
|------|------|
| Token 速度 | 每秒生成的 token 数量 (tokens/s) |
| TTFT | 首 Token 延迟 (Time To First Token) |
| 可用率 | 成功请求的百分比 |

## 技术栈

- Python 3.10+
- OpenAI SDK
- SQLite
- Streamlit
- Plotly
```

- [ ] **Step 5: Commit all documentation**

```bash
git add .gitignore start.sh README.md
git commit -m "docs: add README, startup script, and gitignore"
```

---

### Task 9: Final Verification

- [ ] **Step 1: Run full test**

```bash
# Test imports
python -c "from shared.config import load_config; from shared.db import init_db; from collector.tester import test_all_models; print('✓ All imports successful')"

# Initialize database
python -c "from shared.config import load_config; from shared.db import init_db; init_db(load_config()); print('✓ Database initialized')"

# Verify dashboard can start
streamlit run dashboard/app.py --server.headless true &
sleep 5
curl -s http://localhost:8501 > /dev/null && echo "✓ Dashboard running"
pkill -f "streamlit run"
```

- [ ] **Step 2: Final commit**

```bash
git add -A
git status
git commit -m "chore: final project setup"
```

---

## Summary

| Task | Description | Files Created |
|------|-------------|---------------|
| 1 | Project initialization | requirements.txt, .env.example, config.yaml |
| 2 | Shared config module | shared/models.py, shared/config.py |
| 3 | Database module | shared/db.py |
| 4 | LLM tester | collector/tester.py |
| 5 | Collector entry point | collector/main.py |
| 6 | Dashboard charts | dashboard/charts.py |
| 7 | Streamlit app | dashboard/app.py |
| 8 | Documentation | README.md, start.sh, .gitignore |
| 9 | Final verification | - |

**Total: 13 source files**
