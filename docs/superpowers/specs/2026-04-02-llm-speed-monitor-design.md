# LLM Speed Monitor - 设计文档

## 概述

一个公开的 LLM 性能监控看板，定时采集多家大模型服务商的 Token 生成速度和响应延迟，通过 Web 界面展示历史趋势。

## 目标

- 监控国内外主流 LLM 服务商的性能表现
- 实时展示 Token 速度 (tokens/s) 和 TTFT (首 Token 延迟)
- 记录历史数据，支持趋势分析
- 提供公开的性能对比看板

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                         用户层                               │
│                    Streamlit Web UI                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        数据层                                │
│                      SQLite (llm_speed.db)                   │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│   │  providers  │  │   models    │  │   metrics   │         │
│   └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                       采集层                                 │
│                    Collector (独立进程)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ Scheduler │  │  Tester  │  │  Writer  │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

**双进程架构：**
- **Collector**：独立后台进程，按配置的间隔定时采集所有模型的性能数据
- **Dashboard**：Streamlit Web 应用，从 SQLite 读取数据并展示

## 项目目录结构

```
llm-speed/
├── config.yaml           # 服务商和模型配置
├── .env                  # API Keys (gitignore)
├── llm_speed.db          # SQLite 数据库 (gitignore)
│
├── collector/            # 采集器 (独立进程)
│   ├── __init__.py
│   ├── main.py           # 入口：定时调度
│   ├── tester.py         # 请求 LLM API，计算指标
│   └── db.py             # 数据库写入
│
├── dashboard/            # Streamlit 看板 (独立进程)
│   ├── __init__.py
│   ├── app.py            # Streamlit 入口
│   └── charts.py         # 图表生成逻辑
│
├── shared/               # 共享代码
│   ├── __init__.py
│   ├── config.py         # 配置加载
│   └── models.py         # 数据模型定义
│
├── requirements.txt
└── README.md
```

## 数据库设计

### providers 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 |
| name | TEXT UNIQUE | 服务商标识 (deepseek, openai) |
| display_name | TEXT | 显示名称 (DeepSeek, OpenAI) |
| base_url | TEXT | API Base URL |
| created_at | TIMESTAMP | 创建时间 |

### models 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 |
| provider_id | INTEGER | 外键关联 providers |
| model_id | TEXT | 模型标识 (gpt-4o, deepseek-chat) |
| display_name | TEXT | 显示名称 |

### metrics 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增主键 |
| model_id | INTEGER | 外键关联 models |
| recorded_at | TIMESTAMP | 记录时间 |
| ttft_ms | INTEGER | 首 Token 延迟 (毫秒) |
| total_time_ms | INTEGER | 总响应时间 (毫秒) |
| prompt_tokens | INTEGER | 输入 Token 数 |
| completion_tokens | INTEGER | 输出 Token 数 |
| tokens_per_second | REAL | 生成速度 |
| success | BOOLEAN | 是否成功 |
| error_message | TEXT | 错误信息 |

### 索引

```sql
CREATE INDEX idx_metrics_model_time ON metrics(model_id, recorded_at);
CREATE INDEX idx_metrics_time ON metrics(recorded_at);
```

## 配置设计

### config.yaml

```yaml
# 采集设置
collector:
  interval_minutes: 5
  timeout_seconds: 60
  test_prompt: "请用中文简短介绍一下人工智能，不超过100字。"
  max_tokens: 100

# 服务商配置
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

### .env

```env
DEEPSEEK_API_KEY=sk-xxxxx
OPENAI_API_KEY=sk-xxxxx
ZHIPU_API_KEY=xxxxx
```

Key 命名规则：`{PROVIDER_NAME}_API_KEY`，全大写，对应 config.yaml 里的 name 字段。

## 采集器逻辑

### 核心流程

1. 加载配置，初始化数据库
2. 按配置的间隔循环执行：
   - 遍历所有服务商和模型
   - 使用 OpenAI SDK 发起流式请求
   - 计算 TTFT、Token 速度等指标
   - 写入 SQLite 数据库

### 指标计算

```python
# 使用流式请求
response = await client.chat.completions.create(
    model=model.id,
    messages=[{"role": "user", "content": config.test_prompt}],
    max_tokens=config.max_tokens,
    stream=True,
    stream_options={"include_usage": True}
)

# TTFT: 首 Token 时间
first_chunk = await response.__anext__()
ttft_ms = (time.time() - start_time) * 1000

# 消费剩余流获取 token 统计
async for chunk in response:
    if chunk.usage:
        completion_tokens = chunk.usage.completion_tokens

# 计算生成速度
generation_time_ms = total_time_ms - ttft_ms
tokens_per_second = completion_tokens / (generation_time_ms / 1000)
```

### 错误处理

| 场景 | 处理方式 |
|------|----------|
| API 超时 | 记录 success=False，继续下一个模型 |
| API Key 无效 | 记录错误信息，不中断采集 |
| 速率限制 (429) | 等待后重试，最多 3 次 |
| 网络错误 | 记录失败，下次采集再试 |

## 看板设计

### 页面布局

1. **顶部状态栏**：最后更新时间
2. **实时状态卡片**：各服务商当前速度、TTFT、状态
3. **Token 速度趋势图**：折线图，支持时间范围选择
4. **TTFT 延迟趋势图**：折线图
5. **性能排行表**：24h/7d 平均性能对比

### 交互功能

- 时间范围选择：1h / 6h / 24h / 7d
- 服务商筛选：勾选要对比的服务商

### 技术实现

- Streamlit `st.line_chart()` / `st.bar_chart()` 绑定图表
- pandas 从 SQLite 读取数据并做聚合统计
- Plotly 提供交互式图表

## 启动方式

```bash
# 启动采集器
python -m collector.main

# 启动看板
streamlit run dashboard/app.py

# 或使用启动脚本
./start.sh
```

## 技术栈总结

| 模块 | 技术选型 |
|------|----------|
| 采集器 | Python + asyncio + OpenAI SDK |
| 存储 | SQLite |
| 看板 | Streamlit + pandas + Plotly |
| 配置 | YAML + .env |
| 架构 | 双进程，通过 SQLite 通信 |
