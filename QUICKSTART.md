# 🚀 快速启动指南

## 前提条件

- Python 3.10+
- Node.js 16+
- OpenAI API Key

## 启动步骤

### 1️⃣ 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
OPENAI_API_KEY=sk-your-api-key-here
```

### 2️⃣ 一键启动（最简单）

```bash
./start.sh
```

启动后访问：
- **Web UI**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs

### 3️⃣ 分别启动（可选）

**终端 1 - 后端：**
```bash
pip install -e .
python -m apps.api.main
```

**终端 2 - 前端：**
```bash
cd frontend
npm install
npm run dev
```

## 使用示例

### 通过 Web UI

1. 打开 http://localhost:3000
2. 填写旅行信息：
   - 目的地：杭州
   - 日期：2026-08-01 至 2026-08-03
   - 预算：3000 元/人
   - 人数：2 人
   - 偏好：历史文化、美食
3. 点击"开始规划"
4. 查看生成的旅行计划

### 通过 API

```bash
# 测试健康检查
python test_api.py

# 测试创建旅行计划
python test_api.py --plan
```

### 通过 curl

```bash
curl -X POST "http://localhost:8000/api/v1/plan" \
  -H "Content-Type: application/json" \
  -d '{
    "preferences": {
      "destination": "杭州",
      "start_date": "2026-08-01",
      "end_date": "2026-08-03",
      "budget": 3000,
      "interests": ["历史文化", "美食"],
      "num_travelers": 2
    }
  }'
```

## 功能特性

### 前端界面

✅ 简洁优雅的表单设计  
✅ 多选旅行偏好  
✅ 实时预算计算  
✅ 详细行程展示  
✅ 响应式设计（移动端友好）

### 后端 API

✅ FastAPI 框架  
✅ 完整的 LangGraph 工作流  
✅ 并行搜索航班/酒店/景点  
✅ 智能预算分析  
✅ 流式输出支持（SSE）  
✅ 自动 API 文档

## 故障排查

### 后端启动失败

**问题**：`OPENAI_API_KEY not found`  
**解决**：确保 `.env` 文件存在并包含有效的 API key

**问题**：端口 8000 已被占用  
**解决**：修改 `apps/api/main.py` 中的端口号

### 前端启动失败

**问题**：`node_modules` 安装失败  
**解决**：
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**问题**：端口 3000 已被占用  
**解决**：修改 `frontend/vite.config.js` 中的端口号

### API 调用失败

**问题**：API 返回 500 错误  
**解决**：查看后端日志，确认 OpenAI API key 正确

**问题**：前端无法连接后端  
**解决**：确认后端服务正在运行（http://localhost:8000/health）

## 下一步

- 📖 查看 [Web UI 使用指南](./docs/WEB_UI_GUIDE.md)
- 📚 阅读 [完整文档](./docs/README.md)
- 🧪 运行测试：`pytest tests/`
- 🔧 自定义配置：编辑 `test_settings.py`

## 技术支持

如有问题，请查看：
- API 文档：http://localhost:8000/docs
- 项目文档：`./docs/`
- 测试脚本：`test_api.py`

Happy coding! 🎉
