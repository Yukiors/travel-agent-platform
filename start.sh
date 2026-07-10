#!/bin/bash

# Travel Agent Platform - 启动脚本

echo "🚀 启动 Travel Agent Platform"
echo ""

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查 Node.js 环境
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    exit 1
fi

# 启动后端
echo "📦 启动后端服务..."
cd "$(dirname "$0")"

if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 文件，请先配置 OPENAI_API_KEY"
    exit 1
fi

# 安装 Python 依赖
pip install -e . > /dev/null 2>&1

# 启动 FastAPI
python -m apps.api.main &
BACKEND_PID=$!
echo "✅ 后端服务启动成功 (PID: $BACKEND_PID)"
echo "   访问地址: http://localhost:8000"
echo ""

# 启动前端
echo "📦 启动前端服务..."
cd frontend

# 安装 npm 依赖
if [ ! -d "node_modules" ]; then
    echo "   安装前端依赖..."
    npm install > /dev/null 2>&1
fi

# 启动 Vite
npm run dev &
FRONTEND_PID=$!
echo "✅ 前端服务启动成功 (PID: $FRONTEND_PID)"
echo "   访问地址: http://localhost:3000"
echo ""

echo "✨ 所有服务启动完成！"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 等待用户中断
trap "echo ''; echo '🛑 停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" INT
wait
