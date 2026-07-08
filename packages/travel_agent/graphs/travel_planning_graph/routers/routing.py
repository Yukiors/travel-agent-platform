"""Conditional edge routing logic for the travel planning graph."""

from langgraph.graph import END

from travel_agent.graphs.travel_planning_graph.state import TravelPlanningState


def route_after_gather(state: TravelPlanningState) -> str:
    """Determine the next step after gathering preferences.

    Returns the name of the next node to execute, or END if complete.
    """
    return state.next_step or "search_flights"


def route_after_search(state: TravelPlanningState) -> str:
    """Determine the next step after a search node.

    Checks which searches have been completed and routes accordingly.
    """
    return state.next_step or END
