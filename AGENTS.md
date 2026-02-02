# AI Orchestrator - Agent Instructions

Instructions for AI coding agents working on this codebase.

## Setup Commands

```bash
# Install the package (editable mode)
pip install -e ".[dev,langchain]"

# Verify installation
python -c "from ai_orchestrator import run_roundtable; print('OK')"

# Run tests
pytest

# Run verification script
python verify_setup.py
```

## Project Structure

```
src/ai_orchestrator/          # Main library package
├── __init__.py               # Public API exports
├── types.py                  # Core types (RoundtableConfig, RoundtableResult, etc.)
├── convergence.py            # Stop condition logic
├── exceptions.py             # Custom exceptions
├── logging.py                # Logging utilities
├── orchestration/            # Orchestration logic
│   ├── runner.py             # run_roundtable() implementation
│   ├── looping_orchestrator.py
│   └── dynamic_orchestrator.py
├── agents/                   # Built-in agents
├── models/                   # Pydantic data models
├── prompts/                  # System prompts
├── storage/                  # Persistence layer
└── utils/                    # Utilities (LLM factory, etc.)

api/                          # Reference FastAPI application
ui/                           # Reference web dashboard
tests/                        # Test suite
```

## Key Conventions

### Single Public API

The library exposes **one primary entrypoint**: `run_roundtable()`.

```python
from ai_orchestrator import run_roundtable, RoundtableConfig

result = run_roundtable(
    document="...",
    agents=[...],
    moderator=...,
    config=RoundtableConfig(max_iterations=3),
)
```

All other exports are supporting types, not additional entrypoints.

### Imports

**Inside the library** (src/ai_orchestrator/): Use **relative imports**

```python
# Good
from ..types import Issue, Review
from ..convergence import decide_stop

# Bad
from ai_orchestrator.types import Issue
```

**In applications** (api/, main.py, tests/): Use **package imports**

```python
# Good
from ai_orchestrator import run_roundtable, RoundtableConfig
from ai_orchestrator.agents.prd_critic import PRDCritic

# Bad
from ..agents.prd_critic import PRDCritic
```

### Convergence Logic

All stop conditions live in `src/ai_orchestrator/convergence.py`:

- No high severity issues remaining
- Maximum iterations reached
- Document delta below threshold
- Custom stop conditions

Do not add convergence logic elsewhere. Use `decide_stop()`.

### No Provider Lock-in

The core library should not hard-depend on any single LLM provider.
Provider-specific code belongs in:
- `utils/llm_factory.py` for the factory pattern
- Optional dependencies in `pyproject.toml`

### Type Safety

- Use Pydantic models for data structures
- Use Python Protocols for interfaces (Agent, Moderator, OrchestratorEngine)
- Add type hints to all public functions

## How to Add a New Agent

1. Create `src/ai_orchestrator/agents/your_agent.py`

2. Implement the Agent protocol:

```python
from typing import Optional, Dict, Any
from ..types import Review, Issue, Severity

class YourAgent:
    @property
    def name(self) -> str:
        return "your_agent"

    def review(
        self,
        document: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Review:
        # Your review logic
        return Review(
            reviewer_name=self.name,
            issues=[...],
            overall_assessment="...",
        )
```

3. Add tests in `tests/test_your_agent.py`

4. Optionally export from `agents/__init__.py`

## How to Add a Stop Condition

1. Add the condition to `decide_stop()` in `convergence.py`

2. Add a new `stopped_by` value to the StopDecision

3. Add tests in `tests/test_convergence.py`

## Running Tests

```bash
# All tests
pytest

# With verbose output
pytest -v

# Specific file
pytest tests/test_convergence.py

# With coverage
pytest --cov=ai_orchestrator
```

## Code Style

- Line length: 100 characters
- Use ruff for linting: `ruff check src/`
- Use mypy for type checking: `mypy src/ai_orchestrator`

## Git Workflow

- Keep the library (`src/ai_orchestrator/`) independent of apps (`api/`, `ui/`)
- Test changes with `pytest` before committing
- Update tests when changing public API

## Common Tasks

### Update dependencies

Edit `pyproject.toml`, then:
```bash
pip install -e ".[dev,langchain]"
```

### Add a new export to public API

Edit `src/ai_orchestrator/__init__.py` and add to `__all__`.

### Debug imports

```bash
python -c "from ai_orchestrator import run_roundtable; print('OK')"
```

### Check package structure

```bash
pip show ai-orchestrator
python -c "import ai_orchestrator; print(ai_orchestrator.__file__)"
```
