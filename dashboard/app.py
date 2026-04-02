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
        st.sidebar.info("暂无数据")

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
        # Parse UTC time and convert to local timezone
        df["recorded_at"] = pd.to_datetime(df["recorded_at"], utc=True).dt.tz_convert('Asia/Shanghai')

    # === Real-time Status Cards ===
    st.header("📊 实时状态")
    latest = get_latest_metrics()

    if latest:
        # Filter by selected providers
        if selected_providers:
            latest = [m for m in latest if m["provider_display_name"] in selected_providers]

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
                    label=f"{status_emoji} {metric['model_display_name']}",
                    value=speed,
                    delta=f"TTFT: {ttft} | {metric['provider_display_name']}",
                )

        if len(latest) > 4:
            st.caption(f"还有 {len(latest) - 4} 个模型...")
    else:
        st.info("暂无数据，请等待采集器运行或手动运行 `python -m collector.main --once`")

    st.divider()

    # === Performance Trend Charts ===
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

        # === Performance Ranking ===
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
            st.warning("暂无成功数据")

    else:
        st.warning("所选时间范围内没有数据")
        st.code("python -m collector.main --once", language="bash")

    # === Footer ===
    st.divider()
    if not df.empty:
        latest_time = df["recorded_at"].max()
        # Convert to local time string without timezone info for display
        st.caption(f"最后更新: {latest_time.strftime('%Y-%m-%d %H:%M:%S')} (CST)")
    else:
        st.caption("等待数据...")


if __name__ == "__main__":
    main()
