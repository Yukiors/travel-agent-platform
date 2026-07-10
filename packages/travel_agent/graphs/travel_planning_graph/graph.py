"""LangGraph definition for the travel planning workflow."""

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from travel_agent.graphs.travel_planning_graph.state import TravelPlanningState
from travel_agent.graphs.travel_planning_graph.nodes import (
    gather_preferences,
    search_all_parallel,
    build_itinerary,
)
from travel_agent.graphs.travel_planning_graph.nodes.finalize import finalize_plan
from travel_agent.graphs.travel_planning_graph.routers import (
    route_after_gather,
    route_after_search,
)


def build_travel_planning_graph() -> StateGraph:
    """构建并编译旅行规划 LangGraph 工作流。

    创建完整的旅行规划图，包含偏好收集、并行搜索、行程生成和确认所有节点。

    Returns:
        编译后的 StateGraph 实例，可直接调用执行旅行规划流程。

    流程说明：
        1. gather_preferences：收集用户旅行偏好
        2. search_all_parallel：并行搜索航班、酒店、景点和餐厅
        3. build_itinerary：生成每日行程计划
        4. finalize_plan：最终确认和优化
    """
    workflow = StateGraph(TravelPlanningState)  # type: ignore

    # 添加所有节点
    workflow.add_node("gather_preferences", gather_preferences) # type: ignore
    workflow.add_node("search_all_parallel", search_all_parallel) # type: ignore
    workflow.add_node("build_itinerary", build_itinerary) # type: ignore
    workflow.add_node("finalize_plan", finalize_plan) # type: ignore

    # 设置入口节点
    workflow.set_entry_point("gather_preferences")

    # 添加条件边：根据 next_step 决定流转
    workflow.add_conditional_edges("gather_preferences", route_after_gather, {"search_all_parallel": "search_all_parallel", "build_itinerary": "build_itinerary", END: END})

    workflow.add_conditional_edges("search_all_parallel", route_after_search, {"build_itinerary": "build_itinerary", END: END})

    workflow.add_conditional_edges("build_itinerary", route_after_search, {"finalize_plan": "finalize_plan", END: END})

    workflow.add_conditional_edges("finalize_plan", route_after_search, {END: END})

    # 使用 MemorySaver 编译图，支持检查点和会话持久化
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
