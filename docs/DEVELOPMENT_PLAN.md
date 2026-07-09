# 旅游智能体平台 — MVP 开发方案

> **版本**: 1.0  
> **日期**: 2026-07-08  
> **状态**: 项目骨架已搭建，开始 MVP 实现

---

## 目录

1. [MVP 目标](#1-mvp-目标)
2. [当前状态](#2-当前状态)
3. [MVP 范围](#3-mvp-范围)
4. [数据流设计](#4-数据流设计)
5. [涉及文件清单](#5-涉及文件清单)
6. [实现步骤](#6-实现步骤)
7. [LLM 调用策略](#7-llm-调用策略)
8. [启动与测试](#8-启动与测试)
9. [MVP 不做](#9-mvp-不做)

---

## 1. MVP 目标

**一句话**：用户通过 API 提交旅行偏好 → Agent 调用 LLM 生成一份可读的每日行程计划。

**核心链路**：`POST /api/v1/travel/plan` → LangGraph 5 节点 → 结构化行程 JSON 响应。

---

## 2. 当前状态

### 2.1 已完成

| 文件 | 说明 |
|---|---|
| `pyproject.toml` | 依赖、构建、工具配置齐全 |
| `apps/api/main.py` | FastAPI 应用工厂 + CORS + Uvicorn |
| `apps/api/schemas/travel.py` | TravelPreference / TravelPlanRequest / TravelPlanResponse |
| `apps/api/routes/__init__.py` | 路由挂载 |
| `packages/.../state.py` | TravelPlanningState 数据类 |
| `packages/.../graph.py` | 5 节点 LangGraph 结构 + MemorySaver |
| `packages/.../routers/routing.py` | 条件路由（基础版） |
| `packages/.../nodes/__init__.py` | 节点重导出 |
| `packages/common/config/settings.py` | ✅ Step 1 — pydantic-settings 配置 |
| `packages/common/config/__init__.py` | ✅ Step 1 — 导出 Settings, get_settings |
| `.env.example` | ✅ Step 1 — DeepSeek 环境变量模板 |
| `packages/travel_agent/llm/factory.py` | ✅ Step 2 — LLMFactory + get_llm() |
| `packages/travel_agent/llm/__init__.py` | ✅ Step 2 — 导出 LLMFactory, get_llm |
| `.gitignore` | Git 忽略规则 |

### 2.2 进行中 / 待实现

| 文件 | 状态 |
|---|---|
| `packages/travel_agent/prompts/*.py` | ✅ Step 3 — 提示模板 |
| `packages/.../nodes/preferences.py` | ✅ Step 4 — LLM 提取偏好 |
| `packages/.../nodes/search.py` | ⬜ Step 5 — LLM 模拟搜索（下一步） |
| `packages/.../nodes/itinerary.py` | ⬜ Step 6 — LLM 生成行程 |
| `packages/travel_agent/application/services/*.py` | ⬜ Step 7 — 编排层 |
| `apps/api/dependencies.py` | ⬜ Step 8 — 依赖注入 |
| `apps/api/routes/travel.py` | ⬜ Step 9 — API 路由 |
| `packages/.../routers/routing.py` | ⬜ Step 10 — 微调路由 |

---

## 3. MVP 范围

### MVP vs 完整版的取舍

| 模块 | MVP | 完整版 |
|---|---|---|
| 搜索数据 | LLM 模拟生成（利用世界知识） | 真实 API（Amadeus/Booking/Google Places） |
| 对话模式 | 单次请求完成 | 多轮对话澄清 |
| 存储 | 内存 MemorySaver | SQLAlchemy + Alembic |
| 长期记忆 | 无 | ChromaDB 向量存储 |
| 安全 | 无认证 | API Key 验证 + 速率限制 |
| 可观测性 | print / 控制台 | LangSmith / LangFuse |
| 测试 | 手动冒烟 | 单元 + 集成 + LLM 评估 |
| 部署 | uvicorn 直接启动 | Docker + CI/CD |

---

## 4. 数据流设计

```
POST /api/v1/travel/plan
  { "preferences": { "destination": "东京", "start_date": "2026-08-01", ... } }
    │
    ▼
TravelAgentService.plan_travel()
    │
    ▼
LangGraph (5 nodes, 顺序执行):
  ┌──────────────────────────────────────────────────────┐
  │ ① gather_preferences                                 │
  │   LLM 分析用户输入 → 提取/确认 目的地/日期/预算/兴趣  │
  │   若不完整 → 返回澄清问题, graph END                  │
  │   若完整   → next: search_flights                    │
  ├──────────────────────────────────────────────────────┤
  │ ② search_flights                                     │
  │   LLM 根据偏好模拟生成 2-3 个航班选项                 │
  │   → 写入 state.flights                               │
  ├──────────────────────────────────────────────────────┤
  │ ③ search_hotels                                      │
  │   LLM 根据偏好模拟生成 2-3 个酒店选项                 │
  │   → 写入 state.hotels                                │
  ├──────────────────────────────────────────────────────┤
  │ ④ search_attractions                                 │
  │   LLM 根据偏好模拟生成每日 2-3 个景点 + 餐厅          │
  │   → 写入 state.attractions                           │
  ├──────────────────────────────────────────────────────┤
  │ ⑤ build_itinerary                                    │
  │   LLM 综合搜索结果 → 生成结构化每日行程 (JSON)        │
  │   包含: 时间 / 活动 / 描述 / 费用估算                 │
  └──────────────────────────────────────────────────────┘
    │
    ▼
TravelPlanResponse (JSON)
  { plan_id, destination, itinerary: [...], total_budget_estimate }
```

---

## 5. 涉及文件清单

共 **11 个文件**（6 新建 + 5 重写），不动现有目录结构。

### 新建文件

| # | 文件路径 | 说明 |
|---|---|---|
| 1 | `packages/common/config/settings.py` | pydantic-settings 全局配置 |
| 2 | `.env.example` | 环境变量模板 |
| 3 | `packages/travel_agent/llm/factory.py` | LLM 工厂 get_chat_model() |
| 4 | `packages/travel_agent/prompts/preferences.py` | 偏好提取 prompt |
| 5 | `packages/travel_agent/prompts/itinerary.py` | 行程生成 prompt |
| 6 | `apps/api/dependencies.py` | FastAPI 依赖注入 |

### 重写文件

| # | 文件路径 | 说明 |
|---|---|---|
| 7 | `packages/.../nodes/preferences.py` | LLM 提取偏好 + 澄清逻辑 |
| 8 | `packages/.../nodes/search.py` | LLM 模拟搜索航班/酒店/景点 |
| 9 | `packages/.../nodes/itinerary.py` | LLM 生成结构化行程 |
| 10 | `packages/.../routers/routing.py` | 完善性检查路由逻辑 |
| 11 | `apps/api/routes/travel.py` | 对接 TravelAgentService |

### 还需要新建

| # | 文件路径 | 说明 |
|---|---|---|
| 12 | `packages/travel_agent/application/services/travel_agent_service.py` | 编排层 |
| 13 | `packages/travel_agent/application/__init__.py` | (已有桩代码，补导出) |
| 14 | `packages/travel_agent/prompts/__init__.py` | (已有桩代码，补导出) |
| 15 | `packages/travel_agent/llm/__init__.py` | (已有桩代码，补导出) |
| 16 | `packages/common/config/__init__.py` | (已有桩代码，补导出) |

---

## 6. 实现步骤

### 进度总览

| 步骤 | 内容 | 状态 |
|---|---|---|
| Step 1 | `settings.py` + `.env.example` | ✅ 已完成 |
| Step 2 | `llm/factory.py` + `__init__.py` | ✅ 已完成 |
| Step 3 | `prompts/preferences.py` + `prompts/itinerary.py` | ✅ 已完成 |
| Step 4 | 重写 `nodes/preferences.py` | ✅ 已完成 |
| Step 5 | 重写 `nodes/search.py` | ⬜ 下一步 |
| Step 6 | 重写 `nodes/itinerary.py` | ⬜ |
| Step 7 | `application/services/travel_agent_service.py` | ⬜ |
| Step 8 | `apps/api/dependencies.py` | ⬜ |
| Step 9 | 重写 `apps/api/routes/travel.py` | ⬜ |
| Step 10 | 微调 `routers/routing.py` | ⬜ |
| Step 11 | 端到端调试（调 prompt） | ⬜ |

---

### Step 1: 配置管理 ✅

**涉及文件**:

| 文件 | 操作 |
|---|---|
| `packages/common/config/settings.py` | 新建 |
| `packages/common/config/__init__.py` | 更新 |
| `.env.example` | 新建 |

**Settings 字段**:

| 字段 | 类型 | 默认值 | 用途 |
|---|---|---|---|
| `deepseek_api_key` | `str` | `""` (必填) | DeepSeek API 密钥 |
| `deepseek_model` | `str` | `"deepseek-chat"` | 主力模型（行程生成） |
| `deepseek_model_fast` | `str` | `"deepseek-chat"` | 轻量模型（偏好/搜索） |
| `debug` | `bool` | `False` | 调试开关 |

**设计要点**:
- pydantic-settings 从 `.env` 加载，优先级：环境变量 > .env > 默认值
- `deepseek_base_url` 为计算属性，返回 `https://api.deepseek.com/v1`
- `get_settings()` 使用 lru_cache 实现单例，首次调用执行 `validate_api_keys()` 校验
- `validate_api_keys()` 检查密钥是否为空或占位符，在启动时 fast-fail

---

### Step 2: LLM 工厂 ✅

**涉及文件**:

| 文件 | 操作 |
|---|---|
| `packages/travel_agent/llm/factory.py` | 新建 |
| `packages/travel_agent/llm/__init__.py` | 更新 |

**对外接口**:

```python
# 类方式
class LLMFactory:
    def get_chat_model(self, fast: bool = False) -> BaseChatModel

# 快捷函数
def get_llm(fast: bool = False) -> BaseChatModel
```

**设计要点**:
- 使用 `langchain_openai.ChatOpenAI`（DeepSeek 兼容 OpenAI API）
- `fast=False` → `deepseek_model`（行程生成）
- `fast=True` → `deepseek_model_fast`（偏好提取 + 搜索）
- `temperature=0` 确保确定性输出
- `streaming=True` 预留流式能力

---

### Step 3: 提示模板 ⬜

**涉及文件**:

| 文件 | 操作 |
|---|---|
| `packages/travel_agent/prompts/preferences.py` | 新建 |
| `packages/travel_agent/prompts/itinerary.py` | 新建 |
| `packages/travel_agent/prompts/__init__.py` | 更新 |

#### `preferences.py` — 偏好提取提示

**导出**:

| 常量 | 用途 |
|---|---|
| `PREFERENCES_SYSTEM_PROMPT` | 系统角色 + JSON 输出格式定义 |
| `PREFERENCES_USER_TEMPLATE` | `"{user_message}"` 占位模板 |

**System Prompt 结构**:

1. **角色定义** — 你是旅行规划助手，从用户消息中提取旅行偏好
2. **必填字段** — `destination`, `start_date`, `end_date`（三者缺一不可）
3. **可选字段** — `budget`, `interests`, `num_travelers`（有就填，没有给默认值）
4. **`is_complete` 逻辑** — 必填字段齐全 → `true`，缺少 → `false`
5. **`clarifying_question`** — `is_complete=false` 时生成一句中文追问；`true` 时为空字符串
6. **输出格式** — 严格 JSON，列出 8 个字段的完整 schema：
   ```json
   {
     "destination": "string",
     "start_date": "string (YYYY-MM-DD)",
     "end_date": "string (YYYY-MM-DD)",
     "budget": "number or null",
     "num_travelers": "integer",
     "interests": ["string"],
     "is_complete": "boolean",
     "clarifying_question": "string"
   }
   ```

#### `itinerary.py` — 行程生成提示

**导出**:

| 常量 | 用途 |
|---|---|
| `ITINERARY_SYSTEM_PROMPT` | 行程规划师角色 + 约束 + JSON schema |
| `ITINERARY_USER_TEMPLATE` | 多行模板，含 6 个 `{placeholder}` |

**System Prompt 结构**:

1. **角色定义** — 你是专业旅行规划师，综合搜索结果生成每日行程
2. **输入说明** — 会收到航班、酒店、景点列表，基于实际数据生成
3. **约束规则**:
   - 每天 3-5 个活动，时间合理不赶路
   - 考虑地理位置和交通衔接
   - 预算分配合理，总费用不超过用户预算
   - 如某项数据缺失，用合理假设填充
4. **活动类型枚举** — `flight` / `hotel` / `attraction` / `meal` / `transit`
5. **输出 JSON schema**:
   ```json
   [{
     "day": "integer",
     "day_date": "string (YYYY-MM-DD)",
     "activities": [{
       "time": "string (HH:MM)",
       "type": "flight|hotel|attraction|meal|transit",
       "title": "string",
       "description": "string",
       "cost": "number"
     }]
   }]
   ```

**User Template 占位符**: `{destination}`, `{start_date}`, `{end_date}`, `{num_travelers}`, `{budget}`, `{interests}`, `{flights}`, `{hotels}`, `{attractions}`

---

### Step 4: 重写 gather_preferences 节点 ⬜

**涉及文件**:

| 文件 | 操作 |
|---|---|
| `packages/.../nodes/preferences.py` | 重写 |

**函数签名**: `async def gather_preferences(state: TravelPlanningState) -> dict`

**逻辑流程**:

```
输入: state.messages (用户消息列表)
  │
  ├─ 1. 取最后一条 HumanMessage
  │     messages[-1].content
  │
  ├─ 2. 调用 LLM (fast=True)
  │     llm = get_llm(fast=True)
  │     prompt = [SystemMessage(PREFERENCES_SYSTEM_PROMPT),
  │               HumanMessage(PREFERENCES_USER_TEMPLATE.format(user_message=msg))]
  │     response = await llm.ainvoke(prompt)
  │
  ├─ 3. 清洗响应字符串
  │     去除首尾空白和 markdown 代码块包裹 (```json ... ```)
  │
  ├─ 4. 解析 JSON
  │     data = json.loads(cleaned)
  │     解析失败 → 返回错误消息 + next_step="" (graph END)
  │
  ├─ 5. 判断 is_complete
  │   若 false:
  │     messages += AIMessage(data["clarifying_question"])
  │     next_step = ""
  │     (空字符串 → router 返回 END，用户收到追问)
  │
  └─ 6. 若 true:
        state.destination = data["destination"]
        state.start_date = data["start_date"]
        state.end_date = data["end_date"]
        state.budget = data["budget"]
        state.num_travelers = data["num_travelers"]
        state.interests = data["interests"]
        messages += AIMessage("已了解您的需求，正在为您搜索...")
        next_step = "search_flights"
```

**返回值**: `{"messages": [...], "destination": ..., "start_date": ..., ..., "next_step": "..."}`

---

### Step 5: 重写 search 节点 ⬜

**涉及文件**:

| 文件 | 操作 |
|---|---|
| `packages/.../nodes/search.py` | 重写 |

**三个节点统一模式** — 差异仅在搜索类型和写入字段：

| 节点 | 搜索内容 | 写入字段 | next_step |
|---|---|---|---|
| `search_flights` | 航班 | `state.flights` | `"search_hotels"` |
| `search_hotels` | 酒店 | `state.hotels` | `"search_attractions"` |
| `search_attractions` | 景点+餐厅 | `state.attractions` | `"build_itinerary"` |

**每个节点的统一逻辑**:

```
输入: state
  │
  ├─ 1. 从 state 取: destination, start_date, end_date,
  │     budget, num_travelers, interests
  │
  ├─ 2. 构建 system prompt（描述角色和输出要求）:
  │     search_flights:      "你是航班查询助手..."
  │     search_hotels:       "你是酒店查询助手..."
  │     search_attractions:  "你是旅游攻略达人..."
  │
  ├─ 3. 构建 user prompt（多行文本，带入用户参数）:
  │     "目的地: {destination}, 日期: {start_date}~{end_date},
  │      人数: {num_travelers}, 预算: {budget}, 兴趣: {interests}"
  │     "请生成 2-3 个合理的选项，以 JSON 数组返回。"
  │
  ├─ 4. 调用 LLM (fast=True)，清洗并解析 JSON
  │     解析失败 → 返回错误消息 + next_step=""
  │
  ├─ 5. 写入对应 state 字段
  │     search_flights:    state.flights = parsed_data
  │     search_hotels:     state.hotels = parsed_data
  │     search_attractions: state.attractions = parsed_data
  │
  └─ 6. 返回 AIMessage + next_step
```

**三个节点的输出 JSON schema**:

```json
// flights
[{ "flight_no": "CA925", "airline": "中国国际航空",
   "departure_time": "08:00", "arrival_time": "11:30",
   "departure_city": "上海", "arrival_city": "东京",
   "price": 2500, "stops": 0 }]

// hotels
[{ "name": "新宿格兰贝尔酒店", "star": 4,
   "address": "新宿区...", "price_per_night": 800,
   "check_in": "15:00", "check_out": "11:00",
   "highlights": "近地铁，步行可至新宿御苑" }]

// attractions
[{ "name": "新宿御苑", "type": "attraction",
   "description": "...", "recommended_duration": "2小时",
   "ticket_price": 200 },
 { "name": "一兰拉面", "type": "meal",
   "description": "...", "avg_cost": 60 }]
```

---

### Step 6: 重写 build_itinerary 节点 ⬜

**涉及文件**:

| 文件 | 操作 |
|---|---|
| `packages/.../nodes/itinerary.py` | 重写 |

**函数签名**: `async def build_itinerary(state: TravelPlanningState) -> dict`

**逻辑流程**:

```
输入: state (含 flights, hotels, attractions, 偏好等)
  │
  ├─ 1. 读取所有搜索结果
  │     flights = state.flights or []
  │     hotels = state.hotels or []
  │     attractions = state.attractions or []
  │
  ├─ 2. 格式化为可读文本
  │     flights_text = "\n".join([f"- {f[flight_no]} {f[airline]}..." for f in flights])
  │     同上处理 hotels, attractions
  │     空列表 → "暂无数据"
  │
  ├─ 3. 构建 prompt
  │     user_msg = ITINERARY_USER_TEMPLATE.format(
  │         destination=state.destination,
  │         start_date=state.start_date,
  │         end_date=state.end_date,
  │         num_travelers=state.num_travelers,
  │         budget=state.budget or "不限",
  │         interests=", ".join(state.interests) or "无特殊偏好",
  │         flights=flights_text,
  │         hotels=hotels_text,
  │         attractions=attractions_text,
  │     )
  │
  ├─ 4. 调用 LLM (fast=False，主力模型)
  │     llm = get_llm(fast=False)
  │     response = await llm.ainvoke([
  │         SystemMessage(ITINERARY_SYSTEM_PROMPT),
  │         HumanMessage(user_msg)
  │     ])
  │
  ├─ 5. 清洗并解析 JSON
  │     解析失败 → 重试一次，prompt 追加 "必须返回合法 JSON"
  │     两次都失败 → 返回原始文本 + next_step=""
  │
  ├─ 6. 计算总预算
  │     遍历所有 activities，累加 cost
  │
  └─ 7. 写入 state
       state.itinerary = parsed_data
       state.total_budget_estimate = total_cost
       messages += AIMessage("行程已生成，请查看。")
       next_step = ""
```

---

### Step 7: TravelAgentService 编排层 ⬜

**涉及文件**:

| 文件 | 操作 |
|---|---|
| `packages/travel_agent/application/services/travel_agent_service.py` | 新建 |
| `packages/travel_agent/application/__init__.py` | 更新 |

**类设计**:

```python
class TravelAgentService:
    def __init__(self):
        self.graph = build_travel_planning_graph()

    async def plan_travel(
        self,
        preferences: TravelPreference,
        conversation_id: str | None = None,
    ) -> TravelPlanResponse:
        ...
```

**`plan_travel` 内部逻辑**:

```
1. 构建初始 TravelPlanningState
   destination = preferences.destination
   start_date = preferences.start_date
   end_date = preferences.end_date
   budget = preferences.budget
   interests = preferences.interests
   num_travelers = preferences.num_travelers
   messages = [HumanMessage("我想去{destination}旅游...")]

2. 构建 LangGraph config
   thread_id = conversation_id or str(uuid4())
   用于 checkpointer 追踪会话

3. 调用 graph.ainvoke(state, config)
   等待所有节点执行完毕

4. 从返回 state 提取结果
   final_state = result
   itinerary = final_state.itinerary
   total_budget = final_state.total_budget_estimate
   plan_id = thread_id  # 用 thread_id 作为 plan_id

5. 构造 TravelPlanResponse
   return TravelPlanResponse(
       plan_id=plan_id,
       destination=final_state.destination,
       itinerary=itinerary,
       total_budget_estimate=total_budget,
       created_at=datetime.utcnow(),
   )
```

---

### Step 8: API 依赖注入 ⬜

**涉及文件**:

| 文件 | 操作 |
|---|---|
| `apps/api/dependencies.py` | 新建 |

**导出**:

| 函数 | 返回类型 | 说明 |
|---|---|---|
| `get_settings()` | `Settings` | 委托给 `common.config.get_settings()` |
| `get_travel_agent_service()` | `TravelAgentService` | 每次创建新实例 |

**设计要点**:
- `get_settings` 委托给 `common.config.get_settings()`，lru_cache 保证单例
- `get_travel_agent_service` 无缓存，每次请求创建新实例：
  - `TravelAgentService` 是无状态对象（Graph 已编译，MemorySaver 在 graph 内部）
  - 创建成本极低，无需缓存

---

### Step 9: 重写 API 路由 ⬜

**涉及文件**:

| 文件 | 操作 |
|---|---|
| `apps/api/routes/travel.py` | 重写 |

**POST /api/v1/travel/plan**:

```
1. 注入 TravelAgentService (Depends)
2. 调用 service.plan_travel(request.preferences, request.conversation_id)
3. 捕获异常:
   ValueError → 422 Unprocessable Entity
   其他异常 → 500 Internal Server Error
4. 返回 TravelPlanResponse
```

**GET /api/v1/travel/plan/{plan_id}**:

```
MVP 阶段直接返回 501 Not Implemented
(无数据库持久化，无法按 ID 查询历史)
```

---

### Step 10: 微调路由逻辑 ⬜

**涉及文件**:

| 文件 | 操作 |
|---|---|
| `packages/.../routers/routing.py` | 微调 |

**修改点** — `route_after_gather`:

```
当前逻辑:  return state.next_step or "search_flights"
修改为:    return state.next_step or END

原因: preferences 不完整时 gather_preferences 设 next_step=""，
      此时应路由到 END 让 graph 停止，把澄清问题返回给用户。
      原逻辑 fallback 到 "search_flights" 会导致信息不全就往下搜索。
```

**`route_after_search` 保持不变**:

```
return state.next_step or END
// search 节点始终明确设置 next_step，逻辑无需修改
```

---

### Step 11: 端到端调试 ⬜

不涉及文件新建/修改，聚焦调优:
- 启动 `uvicorn apps.api.main:app --reload`
- 用 curl 发送完整偏好，验证 200 响应 + 行程 JSON 格式正确
- 发送不完整偏好，验证返回澄清问题而非报错
- 检查 LLM 返回的 JSON 是否稳定可解析
- 根据实际输出微调 prompt 措辞

---

## 7. LLM 调用策略

| 节点 | 模型 | 获取方式 |
|---|---|---|
| gather_preferences | deepseek-chat (fast) | `get_llm(fast=True)` |
| search_flights | deepseek-chat (fast) | `get_llm(fast=True)` |
| search_hotels | deepseek-chat (fast) | `get_llm(fast=True)` |
| search_attractions | deepseek-chat (fast) | `get_llm(fast=True)` |
| build_itinerary | deepseek-chat (主力) | `get_llm(fast=False)` |

**关键设计**：MVP 不调用任何外部搜索 API。search 节点直接让 LLM 根据目的地和日期生成"合理的"航班/酒店/景点数据——LLM 的世界知识足以生成逼真的模拟结果。

**统一参数**：所有调用 `temperature=0`（确定性输出），`streaming=True`（预留流式能力）。

---

## 8. 启动与测试

### 启动

```bash
# 1. 配置 API Key
echo 'DEEPSEEK_API_KEY=sk-your-key' > .env

# 2. 安装依赖（如未安装）
pip install -e ".[dev]"

# 3. 启动服务
uvicorn apps.api.main:app --reload
```

### 测试

```bash
curl -X POST http://localhost:8000/api/v1/travel/plan \
  -H "Content-Type: application/json" \
  -d '{
    "preferences": {
      "destination": "东京",
      "start_date": "2026-08-01",
      "end_date": "2026-08-05",
      "budget": 15000,
      "interests": ["美食", "动漫"],
      "num_travelers": 2
    }
  }'
```

### 预期响应

```json
{
  "plan_id": "uuid-xxxx",
  "destination": "东京",
  "itinerary": [
    {
      "day": 1,
      "date": "2026-08-01",
      "activities": [
        { "time": "08:00", "type": "flight", "title": "CA925 北京→东京", "cost": 2500 },
        { "time": "13:00", "type": "hotel", "title": "入住 新宿格兰贝尔酒店", "cost": 800 },
        { "time": "15:00", "type": "attraction", "title": "新宿御苑", "cost": 200 },
        { "time": "18:30", "type": "meal", "title": "一兰拉面 新宿店", "cost": 60 }
      ]
    }
  ],
  "total_budget_estimate": 14200
}
```

---

## 9. MVP 不做

- ❌ 多轮对话（单次请求完成；preferences 不完整时返回澄清问题即可）
- ❌ 流式响应（SSE）
- ❌ 真实搜索 API（Amadeus / Booking / Google Places）
- ❌ 持久化存储（数据库 / ChromaDB）
- ❌ 用户系统（认证 / 偏好历史）
- ❌ 前端界面
- ❌ Docker / CI / 部署配置
