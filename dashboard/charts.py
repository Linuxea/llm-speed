"""Chart generation functions for the dashboard."""

import pandas as pd
import plotly.graph_objects as go


def create_speed_trend_chart(df: pd.DataFrame, title: str = "Token 速度趋势") -> go.Figure:
    """Create a line chart showing token speed over time.

    Args:
        df: DataFrame with columns: recorded_at, tokens_per_second, model_display_name
        title: Chart title.

    Returns:
        Plotly Figure object.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", showarrow=False, font=dict(size=20))
        fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig

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
            marker=dict(size=6),
        ))

    fig.update_layout(
        title=title,
        xaxis_title="时间",
        yaxis_title="Token 速度 (tokens/s)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=400,
        margin=dict(t=60, b=40, l=60, r=20),
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
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", showarrow=False, font=dict(size=20))
        fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig

    fig = go.Figure()

    for model_name in df["model_display_name"].unique():
        model_df = df[df["model_display_name"] == model_name].sort_values("recorded_at")

        fig.add_trace(go.Scatter(
            x=model_df["recorded_at"],
            y=model_df["ttft_ms"],
            mode="lines+markers",
            name=model_name,
            hovertemplate="%{y:.0f} ms<br>%{x}<extra></extra>",
            marker=dict(size=6),
        ))

    fig.update_layout(
        title=title,
        xaxis_title="时间",
        yaxis_title="TTFT (毫秒)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=400,
        margin=dict(t=60, b=40, l=60, r=20),
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
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", showarrow=False, font=dict(size=20))
        fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig

    # Sort by tokens_per_second descending (for horizontal bar, this means bottom to top)
    df = df.sort_values("tokens_per_second", ascending=True)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=df["model_display_name"],
        x=df["tokens_per_second"],
        orientation="h",
        text=df["tokens_per_second"].apply(lambda x: f"{x:.1f}"),
        textposition="outside",
        hovertemplate="%{y}: %{x:.1f} t/s<extra></extra>",
        marker=dict(
            color=df["tokens_per_second"],
            colorscale="Viridis",
            showscale=False,
        ),
    ))

    fig.update_layout(
        title=title,
        xaxis_title="平均 Token 速度 (tokens/s)",
        yaxis_title="",
        height=max(300, len(df) * 40),
        showlegend=False,
        margin=dict(t=60, b=40, l=150, r=60),
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

    # Filter only successful requests
    success_df = df[df["success"] == True].copy()

    if success_df.empty:
        return pd.DataFrame()

    agg_df = success_df.groupby(["provider_display_name", "model_display_name"]).agg({
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
