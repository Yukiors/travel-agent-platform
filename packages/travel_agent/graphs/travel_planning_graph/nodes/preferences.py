"""Node for gathering and validating user travel preferences."""

from langchain_core.messages import AIMessage

from travel_agent.graphs.travel_planning_graph.state import TravelPlanningState


async def gather_preferences(state: TravelPlanningState) -> dict:
    """Extract and validate travel preferences from the conversation.

    If preferences are incomplete, this node asks clarifying questions.
    If complete, it routes to the first search node.
    """
    # TODO: Implement preference extraction via LLM
    return {
        "messages": [AIMessage(content="Processing your travel preferences...")],
        "next_step": "search_flights",
    }
