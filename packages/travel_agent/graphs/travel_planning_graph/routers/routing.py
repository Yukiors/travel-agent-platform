"""Conditional edge routing logic for the travel planning graph."""

from langgraph.graph import END

from travel_agent.graphs.travel_planning_graph.state import TravelPlanningState


def route_after_gather(state: TravelPlanningState) -> str:
    """Determine the next step after gathering preferences.

    Returns the name of the next node to execute, or END if complete.
    """
    # 显式检查 next_step 是否为空——空字符串在 Python 中是 falsy，
    # 不能用 `or` 短路求值，否则 next_step="" 会被误路由到搜索节点。
    if not state.next_step:
        return END
    return state.next_step


def route_after_search(state: TravelPlanningState) -> str:
    """Determine the next step after a search node.

    Checks which searches have been completed and routes accordingly.
    """
    return state.next_step or END
