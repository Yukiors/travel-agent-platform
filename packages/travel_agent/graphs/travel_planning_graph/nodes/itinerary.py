"""Node for building the final travel itinerary."""

from datetime import datetime

from langchain_core.messages import AIMessage

from travel_agent.graphs.travel_planning_graph.state import TravelPlanningState


async def build_itinerary(state: TravelPlanningState) -> dict:
    """Compile search results into a structured daily itinerary.

    This is the final graph node. It produces the complete travel plan
    with day-by-day activities, timing, and budget breakdown.
    """
    # TODO: Implement LLM-powered itinerary generation from search results
    return {
        "messages": [
            AIMessage(
                content=f"Here is your travel plan for {state.destination} "
                f"({state.start_date} to {state.end_date}). Enjoy your trip!"
            )
        ],
        "itinerary": [],
        "total_budget_estimate": state.budget or 0.0,
        "next_step": "",
    }
