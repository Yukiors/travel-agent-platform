"""LangGraph definition for the travel planning workflow."""

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from travel_agent.graphs.travel_planning_graph.state import TravelPlanningState
from travel_agent.graphs.travel_planning_graph.nodes import (
    gather_preferences,
    search_flights,
    search_hotels,
    search_attractions,
    build_itinerary,
)
from travel_agent.graphs.travel_planning_graph.routers import (
    route_after_gather,
    route_after_search,
)


def build_travel_planning_graph() -> StateGraph:
    """Build and compile the travel planning LangGraph workflow.

    Returns:
        A compiled StateGraph ready for invocation.
    """
    workflow = StateGraph(TravelPlanningState)

    # Add nodes
    workflow.add_node("gather_preferences", gather_preferences)
    workflow.add_node("search_flights", search_flights)
    workflow.add_node("search_hotels", search_hotels)
    workflow.add_node("search_attractions", search_attractions)
    workflow.add_node("build_itinerary", build_itinerary)

    # Set entry point
    workflow.set_entry_point("gather_preferences")

    # Add conditional edges
    workflow.add_conditional_edges(
        "gather_preferences",
        route_after_gather,
        {
            "search_flights": "search_flights",
            "search_hotels": "search_hotels",
            "search_attractions": "search_attractions",
            "build_itinerary": "build_itinerary",
            END: END,
        },
    )

    workflow.add_conditional_edges(
        "search_flights",
        route_after_search,
        {
            "search_hotels": "search_hotels",
            "search_attractions": "search_attractions",
            "build_itinerary": "build_itinerary",
            END: END,
        },
    )

    workflow.add_conditional_edges(
        "search_hotels",
        route_after_search,
        {
            "search_attractions": "search_attractions",
            "build_itinerary": "build_itinerary",
            END: END,
        },
    )

    workflow.add_edge("search_attractions", "build_itinerary")
    workflow.add_edge("build_itinerary", END)

    # Compile with memory for checkpointing / conversation persistence
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
