"""
Prompt templates for LLM interactions.

Structured prompts for:
- Travel preference extraction
- Flight, hotel, attraction search
- Itinerary generation
- Plan finalization

Usage:
    from travel_agent.prompts import PREFERENCES_SYSTEM_PROMPT, PREFERENCES_USER_TEMPLATE
    from travel_agent.prompts import FLIGHTS_SYSTEM_PROMPT, FLIGHTS_USER_TEMPLATE
    from travel_agent.prompts import ITINERARY_SYSTEM_PROMPT, ITINERARY_USER_TEMPLATE
    from travel_agent.prompts import FINALIZE_SYSTEM_PROMPT, FINALIZE_USER_TEMPLATE
"""

from travel_agent.prompts.preferences import (
    PREFERENCES_SYSTEM_PROMPT,
    PREFERENCES_USER_TEMPLATE,
)
from travel_agent.prompts.itinerary import (
    ITINERARY_SYSTEM_PROMPT,
    ITINERARY_USER_TEMPLATE,
)

from travel_agent.prompts.search import (
    FLIGHTS_SYSTEM_PROMPT,
    FLIGHTS_USER_TEMPLATE,
    HOTELS_SYSTEM_PROMPT,
    HOTELS_USER_TEMPLATE,
    ATTRACTIONS_SYSTEM_PROMPT,
    ATTRACTIONS_USER_TEMPLATE,
)

from travel_agent.prompts.finalize import (
    FINALIZE_SYSTEM_PROMPT,
    FINALIZE_USER_TEMPLATE,
)

__all__ = [
    "PREFERENCES_SYSTEM_PROMPT",
    "PREFERENCES_USER_TEMPLATE",
    "ITINERARY_SYSTEM_PROMPT",
    "ITINERARY_USER_TEMPLATE",
    "FLIGHTS_SYSTEM_PROMPT",
    "FLIGHTS_USER_TEMPLATE",
    "HOTELS_SYSTEM_PROMPT",
    "HOTELS_USER_TEMPLATE",
    "ATTRACTIONS_SYSTEM_PROMPT",
    "ATTRACTIONS_USER_TEMPLATE",
    "FINALIZE_SYSTEM_PROMPT",
    "FINALIZE_USER_TEMPLATE",
]
