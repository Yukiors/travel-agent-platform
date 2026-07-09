"""
Prompt templates for LLM interactions.

Structured prompts for:
- Travel preference extraction
- Itinerary generation

Usage:
    from travel_agent.prompts import PREFERENCES_SYSTEM_PROMPT, PREFERENCES_USER_TEMPLATE
    from travel_agent.prompts import ITINERARY_SYSTEM_PROMPT, ITINERARY_USER_TEMPLATE
"""

from travel_agent.prompts.preferences import (
    PREFERENCES_SYSTEM_PROMPT,
    PREFERENCES_USER_TEMPLATE,
)
from travel_agent.prompts.itinerary import (
    ITINERARY_SYSTEM_PROMPT,
    ITINERARY_USER_TEMPLATE,
)

__all__ = [
    "PREFERENCES_SYSTEM_PROMPT",
    "PREFERENCES_USER_TEMPLATE",
    "ITINERARY_SYSTEM_PROMPT",
    "ITINERARY_USER_TEMPLATE",
]
