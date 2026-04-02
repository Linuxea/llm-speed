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
# Python 后端依赖
pip install -r requirements.txt

# Next.js 前端依赖（可选）
cd web && npm install && cd ..
```

### 2. 配置 API Keys

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Keys
```

### 3. 启动服务

```bash
# 启动后端 API（必须）
python -m api.main &

# 选择前端：

# 方式一：Streamlit（简单快速）
streamlit run dashboard/app.py
# 访问 http://localhost:8501

# 方式二：Next.js（美观现代）
cd web && npm run dev
# 访问 http://localhost:3000
```

## 前端对比

| 特性 | Streamlit | Next.js |
|------|-----------|---------|
| 地址 | http://localhost:8501 | http://localhost:3000 |
| 启动速度 | 快 | 较慢（首次编译） |
| 界面 | 简洁实用 | 美观现代 |
| 交互 | 基础 | 流畅 |
| 自定义 | 有限 | 高度可定制 |

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

## 项目结构

```
llm-speed/
├── config.yaml           # 服务商配置
├── .env                  # API Keys
├── llm_speed.db          # SQLite 数据库
│
├── shared/               # 共享模块
│   ├── config.py         # 配置加载
│   ├── models.py         # 数据模型
│   └── db.py             # 数据库操作
│
├── collector/            # 采集器
│   ├── main.py           # 入口
│   └── tester.py         # API 测试
│
├── api/                  # FastAPI 后端
│   └── main.py           # REST API
│
├── dashboard/            # Streamlit 前端
│   ├── app.py            # 应用入口
│   └── charts.py         # 图表生成
│
├── web/                  # Next.js 前端
│   └── src/app/          # 页面组件
│
├── start.sh              # 启动脚本
└── requirements.txt      # 依赖
```

## 技术栈

- Python 3.10+
- OpenAI SDK (兼容多家服务商)
- SQLite
- FastAPI
- Streamlit + Plotly
- Next.js + Recharts
