"""测试 API 端点的简单脚本。"""

import asyncio
import sys
from datetime import datetime

import httpx


async def test_health():
    """测试健康检查端点。"""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/health")
        print(f"Health Check: {response.status_code}")
        print(f"Response: {response.json()}")
        print()


async def test_create_plan():
    """测试创建旅行计划端点。"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        data = {
            "preferences": {
                "destination": "杭州",
                "start_date": "2026-08-01",
                "end_date": "2026-08-03",
                "budget": 3000,
                "interests": ["历史文化", "美食"],
                "num_travelers": 2,
            }
        }

        print("发送旅行计划请求...")
        print(f"目的地: {data['preferences']['destination']}")
        print(f"日期: {data['preferences']['start_date']} - {data['preferences']['end_date']}")
        print()

        try:
            response = await client.post("http://localhost:8000/api/v1/plan", json=data)

            if response.status_code == 200:
                result = response.json()
                print("✅ 规划成功！")
                print(f"Plan ID: {result['plan_id']}")
                print(f"目的地: {result['destination']}")
                print(f"总预算: {result['total_budget_estimate']} 元")
                print()
            else:
                print(f"❌ 请求失败: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ 错误: {e}")


async def main():
    """主测试函数。"""
    print("=" * 60)
    print("Travel Agent Platform API 测试")
    print("=" * 60)
    print()

    await test_health()

    if len(sys.argv) > 1 and sys.argv[1] == "--plan":
        await test_create_plan()


if __name__ == "__main__":
    asyncio.run(main())
