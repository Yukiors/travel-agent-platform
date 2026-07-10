"""端到端测试：完整的旅行规划流程。

测试从用户输入到最终行程确认的完整流程：
1. 用户输入旅行需求
2. 系统收集偏好
3. 搜索航班、酒店、景点
4. 生成行程
5. 最终确认
"""

import asyncio
from langchain_core.messages import HumanMessage
from travel_agent.graphs.travel_planning_graph.graph import build_travel_planning_graph


async def test_travel_planning_full_flow():
    """测试完整的旅行规划流程。

    模拟用户输入旅行需求，验证系统能够正确执行所有节点并生成完整的旅行计划。
    """
    print("=" * 60)
    print("开始端到端测试：旅行规划完整流程")
    print("=" * 60)

    # 构建旅行规划图
    print("\n[1/6] 构建旅行规划图...")
    graph = build_travel_planning_graph()
    print("✓ 图构建成功")

    # 初始输入：用户的旅行需求
    print("\n[2/6] 准备用户输入...")
    initial_state = {
        "messages": [HumanMessage(content="我想去杭州旅游5天，从2026年7月15日到7月20日，预算5000元/人，1个人，喜欢历史文化和美食")]
    }
    print("✓ 用户输入：去杭州旅游5天，预算5000元/人，喜欢历史文化和美食")

    # 配置线程 ID 用于会话持久化
    config = {"configurable": {"thread_id": "test-e2e-001"}}

    # 执行图
    print("\n[3/6] 执行旅行规划流程...")
    print("-" * 60)
    result = await graph.ainvoke(initial_state, config)
    print("-" * 60)
    print("✓ 流程执行完成")

    # 验证结果
    print("\n[4/6] 验证结果...")

    # 验证偏好收集
    assert result.get("destination"), "❌ 目的地未提取"
    print(f"✓ 目的地: {result['destination']}")

    assert result.get("start_date"), "❌ 出发日期未提取"
    print(f"✓ 出发日期: {result['start_date']}")

    assert result.get("end_date"), "❌ 返程日期未提取"
    print(f"✓ 返程日期: {result['end_date']}")

    assert result.get("budget"), "❌ 预算未提取"
    print(f"✓ 预算: {result['budget']} 元/人")

    # 验证搜索结果
    assert result.get("flights"), "❌ 航班搜索失败"
    print(f"✓ 航班搜索: {len(result['flights'])} 个选项")

    assert result.get("hotels"), "❌ 酒店搜索失败"
    print(f"✓ 酒店搜索: {len(result['hotels'])} 个选项")

    assert result.get("attractions"), "❌ 景点搜索失败"
    print(f"✓ 景点搜索: {len(result['attractions'])} 个选项")

    # 验证行程生成
    assert result.get("itinerary"), "❌ 行程生成失败"
    print(f"✓ 行程生成: {len(result['itinerary'])} 天行程")

    # 验证最终确认
    assert result.get("final_plan"), "❌ 最终确认失败"
    final_plan = result["final_plan"]
    assert final_plan.get("status") == "confirmed", "❌ 计划状态不是 confirmed"
    print(f"✓ 最终确认: {final_plan.get('status')}")

    # 输出详细结果
    print("\n[5/6] 输出详细结果...")
    print("-" * 60)
    print(f"行程摘要: {final_plan.get('summary', '无')}")
    print(f"\n行程亮点:")
    for highlight in final_plan.get("highlights", []):
        print(f"  • {highlight}")
    print(f"\n旅行建议:")
    for tip in final_plan.get("tips", []):
        print(f"  • {tip}")

    budget_analysis = final_plan.get("budget_analysis", {})
    print(f"\n预算分析:")
    print(f"  总费用: {budget_analysis.get('total_per_person', 0)} 元/人")
    print(f"  是否在预算内: {'是' if budget_analysis.get('within_budget') else '否'}")
    breakdown = budget_analysis.get("breakdown", {})
    if breakdown:
        print(f"  费用明细:")
        print(f"    - 航班: {breakdown.get('flights', 0)} 元")
        print(f"    - 酒店: {breakdown.get('hotels', 0)} 元")
        print(f"    - 景点: {breakdown.get('attractions', 0)} 元")
        print(f"    - 餐饮: {breakdown.get('meals', 0)} 元")
    print("-" * 60)

    print("\n[6/6] 测试完成!")
    print("=" * 60)
    print("✓ 所有测试通过！旅行规划平台运行正常。")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_travel_planning_full_flow())
