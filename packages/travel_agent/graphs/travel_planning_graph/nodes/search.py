"""Nodes for searching flights, hotels, and attractions."""

from langchain_core.messages import AIMessage

from travel_agent.graphs.travel_planning_graph.state import TravelPlanningState


async def search_flights(state: TravelPlanningState) -> dict:
    """Search for available flights to the destination."""
    # TODO: Integrate with flight search tools (Amadeus, Skyscanner, etc.)
    return {
        "messages": [AIMessage(content="Searching for flights...")],
        "next_step": "search_hotels",
    }


async def search_hotels(state: TravelPlanningState) -> dict:
    """Search for hotels at the destination."""
    # TODO: Integrate with hotel search tools (Booking.com, Expedia, etc.)
    return {
        "messages": [AIMessage(content="Searching for hotels...")],
        "next_step": "search_attractions",
    }


async def search_attractions(state: TravelPlanningState) -> dict:
    """Search for attractions and activities at the destination."""
    # TODO: Integrate with attraction/activity APIs (Google Places, Viator, etc.)
    return {
        "messages": [AIMessage(content="Searching for attractions...")],
        "next_step": "build_itinerary",
    }
