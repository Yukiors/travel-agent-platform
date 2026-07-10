# Web UI 使用指南

## 快速启动

### 1. 配置环境变量
在项目根目录创建 `.env` 文件：
```bash
OPENAI_API_KEY=your_api_key_here
```

### 2. 一键启动（推荐）
```bash
./start.sh
```

### 3. 分别启动

**启动后端：**
```bash
# 安装依赖
pip install -e .

# 启动 FastAPI 服务
python -m apps.api.main
```

**启动前端：**
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 访问地址

- 前端界面：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 功能说明

### 旅行规划表单
- **目的地**：输入您想去的城市（必填）
- **出发/返程日期**：选择旅行日期范围（必填）
- **预算**：设置每人预算（可选）
- **人数**：选择旅行人数（默认1人）
- **旅行偏好**：多选您感兴趣的旅行类型

### 行程结果展示
- **行程亮点**：旅程的核心特色
- **详细行程**：每日具体安排
- **预算分析**：费用明细与总计
- **旅行建议**：实用的旅行贴士

## 技术栈

### 后端
- FastAPI - Web 框架
- LangGraph - Agent 编排
- LangChain - LLM 集成
- Pydantic - 数据验证

### 前端
- React 18 - UI 框架
- Vite - 构建工具
- Axios - HTTP 客户端
- CSS3 - 样式

## API 端点

### POST /api/v1/plan
生成旅行计划（同步）

**请求体：**
```json
{
  "preferences": {
    "destination": "杭州",
    "start_date": "2026-08-01",
    "end_date": "2026-08-05",
    "budget": 5000,
    "interests": ["历史文化", "美食"],
    "num_travelers": 2
  }
}
```

**响应：**
```json
{
  "plan_id": "uuid",
  "destination": "杭州",
  "itinerary": [...],
  "final_plan": {...},
  "total_budget_estimate": 10000,
  "created_at": "2026-07-10T12:00:00"
}
```

### POST /api/v1/plan/stream
生成旅行计划（流式，Server-Sent Events）

请求格式同上，返回 SSE 事件流。

## 开发说明

### 前端开发
```bash
cd frontend
npm run dev    # 开发模式
npm run build  # 生产构建
```

### 后端开发
```bash
# 自动重载模式
uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```

## 故障排查

### 后端启动失败
- 检查 `.env` 文件是否存在
- 确认 `OPENAI_API_KEY` 已配置
- 检查端口 8000 是否被占用

### 前端启动失败
- 确认 Node.js 版本 >= 16
- 删除 `node_modules` 重新安装
- 检查端口 3000 是否被占用

### API 调用失败
- 检查后端服务是否正常运行
- 查看浏览器控制台错误信息
- 确认 API 代理配置正确（`vite.config.js`）

## 下一步优化

- [ ] 添加流式输出支持（实时显示规划进度）
- [ ] 保存历史规划记录
- [ ] 支持修改和重新生成
- [ ] 导出行程为 PDF/图片
- [ ] 多语言支持
- [ ] 移动端适配优化
