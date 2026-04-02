"""Streamlit dashboard for LLM Speed Monitor - Light Theme."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.db import get_metrics, get_latest_metrics
from dashboard.charts import (
    create_speed_trend_chart,
    create_ttft_trend_chart,
    create_performance_bar_chart,
    aggregate_metrics,
)

# === Page Config ===
st.set_page_config(
    page_title="LLM Speed Monitor",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# === Custom CSS - Light Theme ===
st.markdown("""
<style>
    /* === Main Theme === */
    .stApp {
        background-color: #f6f8fa;
    }

    /* === Sidebar === */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #d0d7de;
    }

    [data-testid="stSidebar"] .st-header {
        color: #57606a;
    }

    /* === Cards === */
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    }

    div[data-testid="stMetric"] label {
        font-size: 14px;
        font-weight: 600;
        color: #57606a;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
        color: #0969da;
    }

    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-size: 13px;
        color: #1a7f37;
    }

    /* === Headers === */
    .stHeader h1, .stHeader h2, .stHeader h3 {
        color: #24292f;
    }

    h1 {
        font-size: 2rem;
        font-weight: 700;
        border-bottom: 2px solid #1a7f37;
        padding-bottom: 10px;
    }

    h2 {
        font-size: 1.5rem;
        font-weight: 600;
        color: #24292f;
    }

    /* === Dividers === */
    hr {
        border-color: #d0d7de;
    }

    /* === Dataframe === */
    .stDataFrame {
        background-color: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 8px;
    }

    /* === Captions === */
    .stCaption {
        color: #57606a;
    }

    /* === Info/Warnings === */
    .stAlert {
        background-color: #ffffff;
        border: 1px solid #d0d7de;
    }

    /* === Buttons === */
    .stButton button {
        background-color: #1a7f37;
        border: none;
        border-radius: 6px;
        color: white;
    }

    /* === Radio/Multiselect === */
    [data-baseweb="radio"] {
        color: #24292f;
    }

    /* === Sidebar labels === */
    [data-testid="stSidebar"] label {
        color: #24292f;
    }
</style>
""", unsafe_allow_html=True)


def render_status_card(metric: dict):
    """Render a single status card with custom styling."""
    status = "online" if metric["success"] else "offline"
    status_color = "#1a7f37" if metric["success"] else "#cf222e"

    if metric["success"] and metric.get("tokens_per_second"):
        speed = f"{metric['tokens_per_second']:.1f}"
        ttft = f"{metric['ttft_ms']:.0f}" if metric.get("ttft_ms") else "-"
    else:
        speed = "-"
        ttft = "-"

    provider = metric.get("provider_display_name", "")
    model = metric.get("model_display_name", "Unknown")

    st.markdown(f"""
    <div style="
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 12px;
        padding: 20px;
        margin: 5px 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 14px; font-weight: 600; color: #57606a; text-transform: uppercase;">
                {model}
            </span>
            <span style="
                background-color: {status_color}22;
                color: {status_color};
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            ">
                ● {status.upper()}
            </span>
        </div>
        <div style="font-size: 32px; font-weight: 700; color: #0969da; margin: 8px 0;">
            {speed} <span style="font-size: 14px; color: #57606a; font-weight: 400;">t/s</span>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 13px; color: #57606a;">
            <span>TTFT: <span style="color: #1a7f37;">{ttft} ms</span></span>
            <span>{provider}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    # === Header ===
    st.title("🚀 LLM Speed Monitor")
    st.caption("实时监控大模型 API 性能 · Token 速度 & 延迟")

    # === Sidebar ===
    st.sidebar.header("⚙️ 设置")

    time_range = st.sidebar.radio(
        "时间范围",
        options=[1, 6, 24, 168],
        format_func=lambda x: {
            1: "最近 1 小时",
            6: "最近 6 小时",
            24: "最近 24 小时",
            168: "最近 7 天",
        }[x],
        index=2,
    )

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
        st.sidebar.info("暂无数据")

    if selected_providers:
        filtered_metrics = [
            m for m in all_metrics
            if m["provider_display_name"] in selected_providers
        ]
    else:
        filtered_metrics = all_metrics

    df = pd.DataFrame(filtered_metrics)

    if not df.empty:
        df["recorded_at"] = pd.to_datetime(df["recorded_at"], utc=True).dt.tz_convert("Asia/Shanghai")

    # === Status Cards ===
    st.header("📊 实时状态")

    latest = get_latest_metrics(success_only=True)

    if latest:
        if selected_providers:
            latest = [m for m in latest if m["provider_display_name"] in selected_providers]

        # Grid layout
        cols = st.columns(min(len(latest), 4))

        for i, metric in enumerate(latest[:8]):
            with cols[i % 4]:
                render_status_card(metric)

        if len(latest) > 8:
            st.caption(f"还有 {len(latest) - 8} 个模型...")
    else:
        st.info("暂无数据，请等待采集器运行或手动运行 `python -m collector.main --once`")

    st.divider()

    # === Performance Charts ===
    st.header("📈 性能趋势")

    if not df.empty:
        success_df = df[df["success"] == True]

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Token 速度")
            speed_chart = create_speed_trend_chart(success_df)
            st.plotly_chart(speed_chart, use_container_width=True)

        with col2:
            st.subheader("TTFT 延迟")
            ttft_chart = create_ttft_trend_chart(success_df)
            st.plotly_chart(ttft_chart, use_container_width=True)

        st.divider()

        # === Performance Ranking ===
        st.header("🏆 性能排行")

        agg_df = aggregate_metrics(success_df)

        if not agg_df.empty:
            col1, col2 = st.columns([2, 3])

            with col1:
                bar_chart = create_performance_bar_chart(agg_df)
                st.plotly_chart(bar_chart, use_container_width=True)

            with col2:
                display_df = agg_df.copy()
                display_df.columns = ["服务商", "模型", "速度 (t/s)", "TTFT (ms)", "可用率 (%)"]
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.warning("暂无成功数据")

    else:
        st.warning("所选时间范围内没有数据")
        st.code("python -m collector.main --once", language="bash")

    # === Footer ===
    st.divider()
    if not df.empty:
        latest_time = df["recorded_at"].max()
        st.caption(f"最后更新: {latest_time.strftime('%Y-%m-%d %H:%M:%S')} (CST)")
    else:
        st.caption("等待数据...")


if __name__ == "__main__":
    main()
