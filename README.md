# AI Agent Orchestration Platform

> **A production-ready multi-agent AI system** demonstrating full-stack engineering, real-time systems, and modern Python architecture.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-00a393.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3+-orange.svg)](https://langchain.com/)
[![React](https://img.shields.io/badge/React-18+-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178c6.svg)](https://www.typescriptlang.org/)
[![WebSocket](https://img.shields.io/badge/WebSocket-Real--time-brightgreen.svg)](#)

---

## What This Project Demonstrates

| Skill Area | What I Built |
|------------|--------------|
| **Backend Engineering** | FastAPI REST API with async endpoints, background tasks, and comprehensive error handling |
| **Real-time Systems** | WebSocket server with pub/sub pattern, connection management, and reconnection logic |
| **AI/LLM Integration** | Multi-provider LLM abstraction (OpenAI, Gemini, Claude) with factory pattern |
| **System Design** | Clean architecture with protocol-based interfaces, dependency injection, and plugin system |
| **Frontend Development** | React + TypeScript dashboard with hooks, state management, and responsive design |
| **DevOps Practices** | Docker-ready, comprehensive logging, environment configuration, and test coverage |

---

## The Problem & Solution

**Problem:** Document review by multiple stakeholders is slow, inconsistent, and often misses critical issues.

**Solution:** An orchestration platform that coordinates multiple AI "critic" agents to review documents in parallel, identify issues by severity, and iteratively refine content until quality thresholds are met.

### Key Metrics
- **2-3 minute** automated refinement vs hours of manual review
- **3x throughput** improvement via parallel agent execution
- **100% audit trail** with versioned documents and convergence reports

---

## Tech Stack

### Backend
- **Python 3.10+** — Type hints, async/await, dataclasses
- **FastAPI** — High-performance async API framework
- **Pydantic** — Data validation and serialization
- **LangChain** — LLM orchestration and prompt management
- **WebSockets** — Real-time bidirectional communication
- **SQLite** — Lightweight persistence option

### Frontend
- **React 18** — Component-based UI with hooks
- **TypeScript** — Type-safe JavaScript
- **Vite** — Fast build tooling
- **Tailwind CSS** — Utility-first styling

### AI/ML Providers
- **OpenAI** — GPT-4, GPT-5 series
- **Google Gemini** — 1M token context window
- **Anthropic Claude** — Claude 3.5 Sonnet, Opus

### Architecture Patterns
- Protocol-based interfaces (Python `Protocol`)
- Factory pattern for LLM providers
- Repository pattern for storage
- Event-driven WebSocket pub/sub
- Strategy pattern for convergence algorithms

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                            │
│                  (TypeScript, Hooks, Tailwind)                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │ REST + WebSocket
┌─────────────────────────▼───────────────────────────────────────┐
│                      FastAPI Backend                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ REST Routes  │  │  WebSocket   │  │  Background Tasks    │   │
│  │  /api/*      │  │  Manager     │  │  (async refinement)  │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
└─────────┼─────────────────┼─────────────────────┼───────────────┘
          │                 │                     │
┌─────────▼─────────────────▼─────────────────────▼───────────────┐
│                   Orchestration Engine                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   Parallel Execution                        │ │
│  │   ┌──────────┐   ┌──────────┐   ┌──────────┐              │ │
│  │   │ Product  │   │ Engineer │   │ AI Risk  │   (Critics)  │ │
│  │   │ Critic   │   │ Critic   │   │ Critic   │              │ │
│  │   └────┬─────┘   └────┬─────┘   └────┬─────┘              │ │
│  │        └──────────────┼──────────────┘                     │ │
│  │                       ▼                                     │ │
│  │              ┌────────────────┐                             │ │
│  │              │   Moderator    │  (Document Refiner)        │ │
│  │              └────────┬───────┘                             │ │
│  │                       ▼                                     │ │
│  │              ┌────────────────┐                             │ │
│  │              │  Convergence   │  (Stop Conditions)         │ │
│  │              │    Checker     │                             │ │
│  │              └────────────────┘                             │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
          │
┌─────────▼───────────────────────────────────────────────────────┐
│                      LLM Factory                                 │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐                   │
│   │  OpenAI  │   │  Gemini  │   │  Claude  │                   │
│   │   GPT    │   │  Google  │   │Anthropic │                   │
│   └──────────┘   └──────────┘   └──────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Features Built

### Core Orchestration
- **Parallel agent execution** with asyncio for concurrent LLM calls
- **Convergence detection** — stops when no high-severity issues remain
- **Session persistence** — JSON versioning with full audit trail
- **Continuation support** — resume refinement from any checkpoint

### Real-time Dashboard
- **Live progress updates** via WebSocket (7 event types)
- **Issue visualization** by severity (High/Medium/Low)
- **Session history** — browse and reload past refinements
- **Responsive design** — works on desktop and mobile

### Plugin Architecture
- **Memory stores** — In-memory and SQLite implementations
- **Model providers** — Abstract interface for custom LLM integrations
- **Retrievers** — RAG-ready interface for context injection

### Developer Experience
- **Clean public API** — simple `run_roundtable()` function
- **Interactive API docs** — auto-generated OpenAPI at `/docs`
- **Comprehensive logging** — per-agent token tracking
- **Type safety** — full type hints throughout

---

## Code Sample

```python
from ai_orchestrator import run_roundtable, RoundtableConfig

# Simple, clean API for orchestrating AI agents
result = run_roundtable(
    document="# Feature Spec\n\nBuild an AI chatbot...",
    agents=[ProductCritic(), EngineeringCritic(), AIRiskCritic()],
    moderator=DocumentModerator(),
    config=RoundtableConfig(max_iterations=3),
)

print(f"Converged: {result.converged}")
print(f"Issues resolved: {result.total_issues_resolved}")
print(f"Final document:\n{result.final_document}")
```

---

## Project Structure

```
ai-agent-orchestration-platform/
├── src/ai_orchestrator/        # Core library (installable package)
│   ├── types.py                # Protocol-based interfaces
│   ├── convergence.py          # Stop condition algorithms
│   ├── orchestration/          # Orchestration engines
│   ├── agents/                 # Pluggable AI agents
│   ├── plugins/                # Extensibility system
│   └── utils/                  # LLM factory, logging
├── api/                        # FastAPI REST + WebSocket server
│   ├── routes/                 # Endpoint handlers
│   └── services/               # Business logic
├── execution-gui/              # React frontend (TypeScript/Vite)
│   └── src/
│       ├── components/         # React components
│       ├── pages/              # Page components
│       └── hooks/              # Custom React hooks
├── tests/                      # Test suite
├── docs/                       # Documentation
└── data/prds/                  # Session storage
```

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/va2ai/ai-agent-orchestration-platform.git
cd ai-agent-orchestration-platform
pip install -e ".[all-providers]"

# Configure API keys
cp .env.example .env
# Add: OPENAI_API_KEY (required), GOOGLE_API_KEY (optional)

# Run the API server
python run_api.py
# Open http://localhost:8000

# Or run the React frontend
cd execution-gui && npm install && npm run dev
# Open http://localhost:5173
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [API Reference](docs/API_DASHBOARD.md) | REST API and WebSocket documentation |
| [Agents Guide](docs/AGENTS.md) | Built-in agents and custom agent development |
| [Dynamic System](docs/DYNAMIC_SYSTEM.md) | AI-generated roundtable configuration |
| [Gemini Setup](docs/GEMINI_SETUP.md) | Google Gemini integration guide |

---

## Testing

```bash
pytest                      # Run all tests
pytest --cov=ai_orchestrator  # With coverage
python test_api.py          # API integration tests
```

---

## Why I Built This

This project showcases my ability to:

1. **Design complex systems** — Multi-agent coordination with convergence logic
2. **Build production-grade APIs** — FastAPI with proper error handling and validation
3. **Implement real-time features** — WebSocket architecture with reliable delivery
4. **Write maintainable code** — Clean architecture, type safety, and documentation
5. **Integrate AI/ML services** — Multi-provider LLM abstraction with graceful fallbacks
6. **Create full-stack applications** — React frontend with TypeScript and modern tooling

---

## License

MIT

---

## Contact

Open to opportunities! Feel free to reach out about this project or potential roles.
