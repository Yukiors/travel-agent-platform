# Travel Agent Platform

AI-powered travel planning agent platform built with LangGraph and FastAPI.

## Project Structure

```
travel-agent-platform/
├── apps/
│   └── api/              # FastAPI web application
├── packages/
│   ├── travel_agent/     # Core travel agent logic
│   │   ├── domain/       # Business entities
│   │   ├── application/  # Use cases
│   │   ├── graphs/       # LangGraph workflows
│   │   ├── tools/        # LangChain tools
│   │   ├── prompts/      # LLM prompt templates
│   │   ├── llm/          # Model configuration
│   │   ├── memory/       # Conversation memory
│   │   ├── repositories/ # Data access
│   │   └── observability/# Monitoring
│   └── common/           # Shared utilities
├── tests/                # Test suite
├── evals/                # LLM evaluation harness
├── infra/                # Infrastructure as code
└── docs/                 # Documentation
```

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the API server
uvicorn apps.api.main:app --reload
```

## Architecture

The platform uses a **LangGraph**-based agent architecture:

1. **Gather Preferences** — Extract user travel requirements
2. **Search** — Query flights, hotels, attractions in parallel
3. **Build Itinerary** — Compile results into a structured plan
4. **Present** — Return the itinerary with reasoning

State is managed through LangGraph's checkpoint system with configurable memory backends.
