"""LLM configuration and model factory.

Provides:
- Model initialization (OpenAI, Anthropic, etc.)
- Token counting and cost tracking
- Model switching based on task complexity
- Prompt caching setup
"""

from .factory import LLMFactory, get_llm

__all__ = ["LLMFactory", "get_llm"]
