"""Chart generation functions for the dashboard - Dark Theme."""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# === Plotly Dark Theme ===
PLOTLY_THEME = {
    "bgcolor": "#0e1117",
    "paper_bgcolor": "#161b22",
    "font_color": "#c9d1d9",
    "grid_color": "#30363d",
    "legend_bgcolor": "#161b22",
}

# Color palette for different models
COLORS = [
    "#58a6ff",  # Blue
    "#3fb950",  # Green
    "#f78166",  # Orange
    "#a371f7",  # Purple
    "#79c0ff",  # Light Blue
    "#7ee787",  # Light Green
    "#ffa657",  # Light Orange
    "#d2a8ff",  # Light Purple
]


def create_speed_trend_chart(df: pd.DataFrame, title: str = "") -> go.Figure:
    """Create a line chart showing token speed over time."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", showarrow=False, font=dict(size=20, color="#8b949e"))
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor=PLOTLY_THEME["bgcolor"],
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
        plot_bgcolor=PLOTLY_THEME["bgcolor"],
        paper_bgcolor=PLOTLY_THEME["paper_bgcolor"],
        font=dict(color=PLOTLY_THEME["font_color"]),
        height=350,
        margin=dict(t=20, b=40, l=60, r=20),
    )

    return fig


def create_ttft_trend_chart(df: pd.DataFrame, title: str = "") -> go.Figure:
    """Create a line chart showing TTFT over time."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", showarrow=False, font=dict(size=20, color="#8b949e"))
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor=PLOTLY_THEME["bgcolor"],
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
        plot_bgcolor=PLOTLY_THEME["bgcolor"],
        paper_bgcolor=PLOTLY_THEME["paper_bgcolor"],
        font=dict(color=PLOTLY_THEME["font_color"]),
        height=350,
        margin=dict(t=20, b=40, l=60, r=20),
    )

    return fig


def create_performance_bar_chart(df: pd.DataFrame, title: str = "") -> go.Figure:
    """Create a horizontal bar chart comparing average performance."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", showarrow=False, font=dict(size=20, color="#8b949e"))
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor=PLOTLY_THEME["bgcolor"],
            paper_bgcolor=PLOTLY_THEME["paper_bgcolor"],
        )
        return fig

    df = df.sort_values("tokens_per_second", ascending=True)

    fig = go.Figure()

    colors = [COLORS[i % len(COLORS)] for i in range(len(df))]

    fig.add_trace(go.Bar(
        y=df["model_display_name"],
        x=df["tokens_per_second"],
        orientation="h",
        text=df["tokens_per_second"].apply(lambda x: f"<b>{x:.1f}</b>"),
        textposition="outside",
        textfont=dict(color=PLOTLY_THEME["font_color"], size=12),
        marker=dict(
            color=colors,
            line=dict(color="#30363d", width=1),
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
        plot_bgcolor=PLOTLY_THEME["bgcolor"],
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
