"""State definition for the travel planning graph."""

from dataclasses import dataclass, field
from typing import Annotated, Optional, Sequence

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


@dataclass(kw_only=True)
class TravelPlanningState:
    """Shared state for the travel planning LangGraph workflow.

    This state flows through all nodes in the graph and accumulates
    messages, intermediate results, and the final plan.
    """

    # Conversation messages (accumulated via add_messages reducer)
    messages: Annotated[Sequence[BaseMessage], add_messages] = field(
        default_factory=list
    )

    # User input
    destination: str = ""
    start_date: str = ""
    end_date: str = ""
    budget: Optional[float] = None
    interests: list[str] = field(default_factory=list)
    num_travelers: int = 1

    # Intermediate results from tool calls
    flights: list[dict] = field(default_factory=list)
    hotels: list[dict] = field(default_factory=list)
    attractions: list[dict] = field(default_factory=list)

    # Final output
    itinerary: list[dict] = field(default_factory=list)
    total_budget_estimate: float = 0.0

    # Routing
    next_step: str = ""
