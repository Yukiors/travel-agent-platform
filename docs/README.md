# Travel Agent Platform

AI-powered travel planning agent platform built with LangGraph and FastAPI.

## Features

✨ **智能旅行规划** - 基于用户偏好自动生成完整旅行计划  
🎯 **多维度搜索** - 并行搜索航班、酒店、景点信息  
📊 **预算分析** - 自动计算费用明细和总预算  
🖥️ **Web UI** - 优雅的用户界面，支持表单输入和结果展示  
🔄 **流式输出** - 实时显示规划进度（SSE 支持）

## Quick Start

### 一键启动（推荐）

```bash
# 1. 配置环境变量
echo "OPENAI_API_KEY=your_api_key_here" > .env

# 2. 启动所有服务
./start.sh
```

访问 http://localhost:3000 查看 Web UI

### 手动启动

**后端：**
```bash
pip install -e .
python -m apps.api.main
```

**前端：**
```bash
cd frontend
npm install
npm run dev
```

详细说明请查看 [Web UI 使用指南](./WEB_UI_GUIDE.md)

## Project Structure

```
travel-agent-platform/
├── apps/
│   └── api/              # FastAPI web application
├── frontend/             # React Web UI
│   ├── src/
│   │   ├── components/   # UI 组件
│   │   ├── pages/        # 页面
│   │   ├── services/     # API 服务
│   │   └── styles/       # 样式文件
│   └── package.json
├── packages/
│   ├── travel_agent/     # Core travel agent logic
│   │   ├── domain/       # Business entities
│   │   ├── application/  # Use cases
│   │   ├── graphs/       # LangGraph workflows
│   │   ├── tools/        # LangChain tools
│   │   ├── prompts/      # LLM prompt templates
│   │   ├── llm/          # Model configuration
│   │   ├── memory/       # Conversation memory
│   │   ├── repositories/ # Data access
│   │   └── observability/# Monitoring
│   └── common/           # Shared utilities
├── tests/                # Test suite
├── evals/                # LLM evaluation harness
├── infra/                # Infrastructure as code
└── docs/                 # Documentation
```

## Architecture

The platform uses a **LangGraph**-based agent architecture:

1. **Gather Preferences** — Extract user travel requirements
2. **Search** — Query flights, hotels, attractions in parallel
3. **Build Itinerary** — Compile results into a structured plan
4. **Finalize** — Generate final plan with budget analysis
5. **Present** — Return the itinerary with reasoning

State is managed through LangGraph's checkpoint system with configurable memory backends.

## API Endpoints

- `GET /health` - 健康检查
- `POST /api/v1/plan` - 创建旅行计划（同步）
- `POST /api/v1/plan/stream` - 创建旅行计划（流式）

API 文档：http://localhost:8000/docs

## Tech Stack

**Backend:**
- LangGraph - Agent orchestration
- LangChain - LLM framework
- FastAPI - Web framework
- Pydantic - Data validation

**Frontend:**
- React 18 - UI framework
- Vite - Build tool
- Axios - HTTP client
