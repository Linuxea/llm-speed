"""Chart generation functions for the dashboard - Light Theme."""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# === Plotly Light Theme ===
PLOTLY_THEME = {
    "bgcolor": "#f6f8fa",
    "paper_bgcolor": "#ffffff",
    "font_color": "#24292f",
    "grid_color": "#d0d7de",
    "legend_bgcolor": "#ffffff",
}

# Color palette for different models
COLORS = [
    "#0969da",  # Blue
    "#1a7f37",  # Green
    "#bf5700",  # Orange
    "#8250df",  # Purple
    "#0550ae",  # Dark Blue
    "#116329",  # Dark Green
    "#953800",  # Dark Orange
    "#6e40c9",  # Dark Purple
]


def create_speed_trend_chart(df: pd.DataFrame, title: str = "") -> go.Figure:
    """Create a line chart showing token speed over time."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", showarrow=False, font=dict(size=20, color="#57606a"))
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor=PLOTLY_THEME["paper_bgcolor"],
            paper_bgcolor=PLOTLY_THEME["paper_bgcolor"],
        )
        return fig

    fig = go.Figure()

    models = df["model_display_name"].unique()

    for i, model_name in enumerate(models):
        model_df = df[df["model_display_name"] == model_name].sort_values("recorded_at")
        color = COLORS[i % len(COLORS)]

        fig.add_trace(go.Scatter(
            x=model_df["recorded_at"],
            y=model_df["tokens_per_second"],
            mode="lines+markers",
            name=model_name,
            line=dict(color=color, width=2),
            marker=dict(color=color, size=6),
            hovertemplate="<b>%{fullData.name}</b><br>%{y:.1f} t/s<br>%{x}<extra></extra>",
        ))

    fig.update_layout(
        title=title,
        xaxis=dict(
            title="",
            gridcolor=PLOTLY_THEME["grid_color"],
            linecolor=PLOTLY_THEME["grid_color"],
            tickfont=dict(color=PLOTLY_THEME["font_color"]),
        ),
        yaxis=dict(
            title="Token 速度 (tokens/s)",
            gridcolor=PLOTLY_THEME["grid_color"],
            linecolor=PLOTLY_THEME["grid_color"],
            tickfont=dict(color=PLOTLY_THEME["font_color"]),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor=PLOTLY_THEME["legend_bgcolor"],
            font=dict(color=PLOTLY_THEME["font_color"], size=11),
        ),
        hovermode="x unified",
        plot_bgcolor=PLOTLY_THEME["paper_bgcolor"],
        paper_bgcolor=PLOTLY_THEME["paper_bgcolor"],
        font=dict(color=PLOTLY_THEME["font_color"]),
        margin=dict(t=60, b=40, l=60, r=40),
    )

    return fig


def create_ttft_trend_chart(df: pd.DataFrame, title: str = "") -> go.Figure:
    """Create a line chart showing TTFT over time."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", showarrow=False, font=dict(size=20, color="#57606a"))
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor=PLOTLY_THEME["paper_bgcolor"],
            paper_bgcolor=PLOTLY_THEME["paper_bgcolor"],
        )
        return fig

    fig = go.Figure()

    models = df["model_display_name"].unique()

    for i, model_name in enumerate(models):
        model_df = df[df["model_display_name"] == model_name].sort_values("recorded_at")
        color = COLORS[i % len(COLORS)]

        fig.add_trace(go.Scatter(
            x=model_df["recorded_at"],
            y=model_df["ttft_ms"],
            mode="lines+markers",
            name=model_name,
            line=dict(color=color, width=2),
            marker=dict(color=color, size=6),
            hovertemplate="<b>%{fullData.name}</b><br>%{y:.0f} ms<br>%{x}<extra></extra>",
        ))

    fig.update_layout(
        title=title,
        xaxis=dict(
            title="",
            gridcolor=PLOTLY_THEME["grid_color"],
            linecolor=PLOTLY_THEME["grid_color"],
            tickfont=dict(color=PLOTLY_THEME["font_color"]),
        ),
        yaxis=dict(
            title="TTFT (毫秒)",
            gridcolor=PLOTLY_THEME["grid_color"],
            linecolor=PLOTLY_THEME["grid_color"],
            tickfont=dict(color=PLOTLY_THEME["font_color"]),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor=PLOTLY_THEME["legend_bgcolor"],
            font=dict(color=PLOTLY_THEME["font_color"], size=11),
        ),
        hovermode="x unified",
        plot_bgcolor=PLOTLY_THEME["paper_bgcolor"],
        paper_bgcolor=PLOTLY_THEME["paper_bgcolor"],
        font=dict(color=PLOTLY_THEME["font_color"]),
        margin=dict(t=60, b=40, l=60, r=40),
    )

    return fig


def create_performance_bar_chart(df: pd.DataFrame, title: str = "") -> go.Figure:
    """Create a horizontal bar chart comparing average performance."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", showarrow=False, font=dict(size=20, color="#57606a"))
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor=PLOTLY_THEME["paper_bgcolor"],
            paper_bgcolor=PLOTLY_THEME["paper_bgcolor"],
        )
        return fig

    # Sort by speed ascending (so fastest is at top)
    df = df.sort_values("tokens_per_second", ascending=True)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=df["model_display_name"],
        x=df["tokens_per_second"],
        orientation="h",
        marker=dict(
            color=df["tokens_per_second"],
            colorscale="Blues",
            line=dict(color="#d0d7de", width=1),
        ),
        hovertemplate="<b>%{y}</b><br>%{x:.1f} t/s<extra></extra>",
    ))

    fig.update_layout(
        title=title,
        xaxis=dict(
            title="平均 Token 速度 (tokens/s)",
            gridcolor=PLOTLY_THEME["grid_color"],
            linecolor=PLOTLY_THEME["grid_color"],
            tickfont=dict(color=PLOTLY_THEME["font_color"]),
        ),
        yaxis=dict(
            title="",
            tickfont=dict(color=PLOTLY_THEME["font_color"], size=11),
        ),
        plot_bgcolor=PLOTLY_THEME["paper_bgcolor"],
        paper_bgcolor=PLOTLY_THEME["paper_bgcolor"],
        font=dict(color=PLOTLY_THEME["font_color"]),
        height=max(300, len(df) * 45),
        showlegend=False,
        margin=dict(t=20, b=40, l=150, r=60),
    )

    return fig


def aggregate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate metrics by model for summary display."""
    if df.empty:
        return pd.DataFrame()

    success_df = df[df["success"] == True].copy()

    if success_df.empty:
        return pd.DataFrame()

    agg_df = success_df.groupby(["provider_display_name", "model_display_name"]).agg({
        "tokens_per_second": "mean",
        "ttft_ms": "mean",
        "success": "mean",
    }).reset_index()

    agg_df.columns = [
        "provider_display_name",
        "model_display_name",
        "tokens_per_second",
        "ttft_ms",
        "success_rate",
    ]

    agg_df["tokens_per_second"] = agg_df["tokens_per_second"].round(1)
    agg_df["ttft_ms"] = agg_df["ttft_ms"].round(0)
    agg_df["success_rate"] = (agg_df["success_rate"] * 100).round(1)

    return agg_df.sort_values("tokens_per_second", ascending=False)
