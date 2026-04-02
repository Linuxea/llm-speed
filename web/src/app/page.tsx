"use client";

import { useState, useEffect } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const COLORS = ["#2563eb", "#16a34a", "#ea580c", "#9333ea", "#0891b2", "#ca8a04"];

interface Metric {
  recorded_at: string;
  ttft_ms: number | null;
  tokens_per_second: number | null;
  model_display_name: string;
  provider_display_name: string;
}

interface Agg {
  provider_display_name: string;
  model_display_name: string;
  avg_tokens_per_second: number;
  avg_ttft_ms: number;
  success_rate: number;
}

export default function Dashboard() {
  const [timeRange, setTimeRange] = useState(24);
  const [latest, setLatest] = useState<Metric[]>([]);
  const [aggregate, setAggregate] = useState<Agg[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(`${API_BASE}/api/latest`).then((r) => r.json()),
      fetch(`${API_BASE}/api/aggregate?hours=${timeRange}`).then((r) => r.json()),
    ])
      .then(([latestData, aggData]) => {
        setLatest(latestData);
        setAggregate(aggData.filter((a: Agg) => a.success_rate > 0));
        setError(null);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [timeRange]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-red-600 text-xl mb-4">❌ {error}</p>
          <p className="text-gray-600">请确保 API 运行在 {API_BASE}</p>
        </div>
      </div>
    );
  }

  // Chart data - sorted by speed
  const chartData = [...aggregate]
    .sort((a, b) => a.avg_tokens_per_second - b.avg_tokens_per_second)
    .slice(0, 10);

  const ttftChartData = [...aggregate]
    .filter((a) => a.avg_ttft_ms > 0)
    .sort((a, b) => b.avg_ttft_ms - a.avg_ttft_ms)
    .slice(0, 10);

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <span className="text-3xl">🚀</span>
              <span className="bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
                LLM Speed Monitor
              </span>
            </h1>
            <p className="text-sm text-gray-500 mt-1">实时监控大模型 API 性能</p>
          </div>

          <div className="flex gap-2">
            {[1, 6, 24, 168].map((h) => (
              <button
                key={h}
                onClick={() => setTimeRange(h)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  timeRange === h
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {h === 1 ? "1h" : h === 6 ? "6h" : h === 24 ? "24h" : "7d"}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Status Cards */}
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <span>📊</span> 实时状态
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {latest.map((m, i) => (
              <div
                key={m.model_display_name}
                className="rounded-xl p-5 border border-gray-200 bg-white shadow-sm"
                style={{
                  boxShadow: `0 1px 3px rgba(0,0,0,0.1), 0 0 0 1px ${COLORS[i % COLORS.length]}20`,
                }}
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
                      {m.model_display_name}
                    </h3>
                    <p className="text-xs text-gray-400 mt-1">{m.provider_display_name}</p>
                  </div>
                  <span
                    className="px-2 py-1 rounded text-xs font-semibold"
                    style={{ backgroundColor: `${COLORS[i % COLORS.length]}15`, color: COLORS[i % COLORS.length] }}
                  >
                    ● ONLINE
                  </span>
                </div>

                <div className="mb-3">
                  <span className="text-4xl font-bold" style={{ color: COLORS[i % COLORS.length] }}>
                    {m.tokens_per_second?.toFixed(1) ?? "-"}
                  </span>
                  <span className="text-lg text-gray-400 ml-1">t/s</span>
                </div>

                <div className="flex items-center text-sm text-gray-600">
                  <span>TTFT:</span>
                  <span className="ml-2 text-green-600 font-medium">
                    {m.ttft_ms ? `${m.ttft_ms.toFixed(0)} ms` : "N/A"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Charts */}
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <span>📈</span> 性能对比 ({timeRange}h 平均)
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Speed Bar Chart */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h3 className="text-sm font-medium text-gray-500 mb-4">Token 速度排行</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis type="number" stroke="#6b7280" fontSize={12} />
                  <YAxis
                    type="category"
                    dataKey="model_display_name"
                    stroke="#6b7280"
                    fontSize={11}
                    width={100}
                    tickFormatter={(v) => v?.length > 12 ? v.slice(0, 12) + "..." : v}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#fff",
                      border: "1px solid #e5e7eb",
                      borderRadius: "8px",
                      boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
                    }}
                    formatter={(value: number) => [`${value.toFixed(1)} t/s`, "速度"]}
                  />
                  <Bar dataKey="avg_tokens_per_second" radius={[0, 4, 4, 0]}>
                    {chartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* TTFT Bar Chart */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h3 className="text-sm font-medium text-gray-500 mb-4">TTFT 延迟排行 (越低越好)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={ttftChartData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis type="number" stroke="#6b7280" fontSize={12} />
                  <YAxis
                    type="category"
                    dataKey="model_display_name"
                    stroke="#6b7280"
                    fontSize={11}
                    width={100}
                    tickFormatter={(v) => v?.length > 12 ? v.slice(0, 12) + "..." : v}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#fff",
                      border: "1px solid #e5e7eb",
                      borderRadius: "8px",
                      boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
                    }}
                    formatter={(value: number) => [`${value.toFixed(0)} ms`, "TTFT"]}
                  />
                  <Bar dataKey="avg_ttft_ms" radius={[0, 4, 4, 0]}>
                    {ttftChartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill="#16a34a" />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        {/* Performance Table */}
        <section>
          <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <span>🏆</span> 详细数据
          </h2>
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">#</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">模型</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">速度</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">TTFT</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">可用率</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {aggregate.map((row, i) => (
                  <tr key={row.model_display_name} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <span
                        className="w-6 h-6 rounded-full inline-flex items-center justify-center text-xs font-bold"
                        style={{ backgroundColor: COLORS[i % COLORS.length], color: "#fff" }}
                      >
                        {i + 1}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{row.model_display_name}</div>
                        <div className="text-xs text-gray-400">{row.provider_display_name}</div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="font-mono font-medium text-lg" style={{ color: COLORS[i % COLORS.length] }}>
                        {row.avg_tokens_per_second}
                      </span>
                      <span className="text-gray-400 text-xs ml-1">t/s</span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="font-mono text-green-600">{row.avg_ttft_ms}</span>
                      <span className="text-gray-400 text-xs ml-1">ms</span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span
                        className={`font-mono font-medium ${
                          row.success_rate >= 99
                            ? "text-green-600"
                            : row.success_rate >= 95
                            ? "text-yellow-600"
                            : "text-red-600"
                        }`}
                      >
                        {row.success_rate}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 mt-8 bg-white">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-sm text-gray-500">
          {latest.length > 0 ? (
            <span>最后更新: {latest[0]?.recorded_at}</span>
          ) : (
            <span>等待数据...</span>
          )}
        </div>
      </footer>
    </div>
  );
}
