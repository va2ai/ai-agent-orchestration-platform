# AI Orchestrator

A reusable Python library for AI agent orchestration and iterative document refinement. The library provides a framework for running "roundtable" sessions where multiple AI agents review and refine documents through iterative feedback loops.

## Features

- **Single Public API**: `run_roundtable()` - the only function you need to run a refinement session
- **Pluggable Agents**: Define custom agents with any LLM backend
- **Convergence Control**: Multiple stop conditions (no high issues, max iterations, delta threshold, custom)
- **Type-Safe**: Pydantic-based models and Python Protocol types
- **Multi-Provider**: Supports OpenAI, Google Gemini, and Anthropic models
- **Reference Applications**: Web dashboard (api/) and CLI (main.py) included

## Installation

### As a Library

```bash
# Basic installation (core only)
pip install -e .

# With LangChain support (recommended for most use cases)
pip install -e ".[langchain]"

# With all LLM providers
pip install -e ".[all-providers]"

# With development dependencies
pip install -e ".[dev]"
```

### Environment Setup

```bash
cp .env.example .env
# Add your API keys to .env:
# OPENAI_API_KEY=sk-...
# GOOGLE_API_KEY=...  (for Gemini)
```

## Quick Start

### Using the Library

```python
from ai_orchestrator import run_roundtable, RoundtableConfig, Issue, Review, Severity

# Define a simple agent
class MyAgent:
    @property
    def name(self) -> str:
        return "QualityCritic"

    def review(self, document: str, context=None) -> Review:
        # Your review logic here (can use any LLM)
        return Review(
            reviewer_name=self.name,
            issues=[
                Issue(
                    category="clarity",
                    description="Section 2 needs more detail",
                    severity=Severity.MEDIUM,
                    reviewer=self.name,
                )
            ],
            overall_assessment="Document is good but needs minor improvements",
        )

# Define a simple moderator
class MyModerator:
    def refine(self, document: str, reviews: list, context=None) -> str:
        # Your refinement logic here
        return document + "\n\n[Refined based on feedback]"

# Run the roundtable
result = run_roundtable(
    document="# My Document\n\nThis is the content to refine...",
    agents=[MyAgent()],
    moderator=MyModerator(),
    config=RoundtableConfig(max_iterations=3),
    title="My Refinement Session",
)

print(f"Converged: {result.converged}")
print(f"Reason: {result.convergence_reason}")
print(f"Final document:\n{result.final_document}")
```

### Using the CLI

```bash
# Run PRD refinement with built-in agents
python main.py --input document.md --title "My PRD" --max-iterations 3 --verbose
```

### Using the Web Dashboard

```bash
# Start the API server
python run_api.py

# Open http://localhost:8000 in your browser
```

## Public API

### Main Function

```python
run_roundtable(
    document: str,              # Initial document content
    agents: Sequence[Agent],    # List of review agents
    moderator: Moderator,       # Document refiner
    engine: OrchestratorEngine = None,  # Optional custom engine
    config: RoundtableConfig = None,    # Configuration
    context: dict = None,       # Optional context passed to agents
    title: str = "Untitled",    # Session title
    session_id: str = None,     # Optional custom session ID
    logger: OrchestratorLogger = None,  # Optional logger
) -> RoundtableResult
```

### Configuration

```python
RoundtableConfig(
    max_iterations: int = 3,           # Max refinement loops
    delta_threshold: float = 0.05,     # Stop if document changes < 5%
    stop_on_no_high_issues: bool = True,  # Stop when no High issues remain
    verbose: bool = False,             # Enable verbose logging
    metadata: dict = {},               # Custom metadata
    custom_stop_condition: Callable = None,  # Custom stop function
)
```

### Result

```python
RoundtableResult(
    session_id: str,                   # Session identifier
    title: str,                        # Session title
    initial_document: str,             # Original document
    final_document: str,               # Refined document
    iterations: List[RoundtableIteration],  # All iteration data
    converged: bool,                   # Whether convergence was reached
    convergence_reason: str,           # Why it stopped
    stopped_by: str,                   # "no_high_issues", "max_iterations", "delta_threshold", "custom"
    total_issues_identified: int,      # Total issues across all iterations
    final_issue_count: dict,           # {"high": 0, "medium": 3, "low": 5}
    token_usage: dict,                 # Token usage by agent
)
```

### Types

```python
from ai_orchestrator import (
    # Core types
    Issue,              # An issue found during review
    Review,             # A collection of issues from one agent
    Severity,           # HIGH, MEDIUM, LOW

    # Protocols (for custom implementations)
    Agent,              # Protocol for review agents
    Moderator,          # Protocol for document refiners
    OrchestratorEngine, # Protocol for custom engines

    # Iteration data
    RoundtableIteration,  # Data from one iteration
    StopDecision,         # Decision about stopping
)
```

### Convergence Functions

```python
from ai_orchestrator import (
    decide_stop,              # Main convergence decision function
    has_high_severity_issues, # Check for high issues
    calculate_document_delta, # Calculate document change
    count_issues_by_severity, # Count issues by severity
    ConvergenceChecker,       # Class-based interface (backwards compat)
)
```

## Architecture

```
ai-agent-orchestration-platform/
├── src/ai_orchestrator/        # Library package
│   ├── __init__.py             # Public API exports
│   ├── types.py                # Core types and protocols
│   ├── convergence.py          # Stop condition logic
│   ├── exceptions.py           # Custom exceptions
│   ├── logging.py              # Logging utilities
│   ├── orchestration/          # Orchestration logic
│   │   ├── runner.py           # run_roundtable implementation
│   │   ├── looping_orchestrator.py  # CLI orchestrator
│   │   └── dynamic_orchestrator.py  # Dynamic roundtable
│   ├── agents/                 # Built-in agents
│   │   ├── prd_critic.py       # Product quality reviewer
│   │   ├── engineering_critic.py # Technical reviewer
│   │   ├── ai_risk_critic.py   # AI safety reviewer
│   │   ├── moderator.py        # Document refiner
│   │   ├── dynamic_critic.py   # Configurable critic
│   │   └── meta_orchestrator.py # AI-generated roundtables
│   ├── models/                 # Data models
│   │   ├── prd_models.py       # PRD-specific models
│   │   └── document_models.py  # Generic document models
│   ├── prompts/                # System prompts
│   ├── storage/                # Persistence
│   └── utils/                  # Utilities (LLM factory, etc.)
├── api/                        # Reference API server
├── ui/                         # Reference web dashboard
├── tests/                      # Test suite
├── main.py                     # CLI entry point
├── run_api.py                  # API server entry point
└── pyproject.toml              # Package configuration
```

## Convergence Logic

The roundtable stops when any of these conditions is met:

1. **No High Severity Issues** (primary): All High issues resolved
2. **Max Iterations Reached** (fallback): Hit the iteration limit
3. **Document Stable** (stability): Document changed < 5% from previous iteration
4. **Custom Condition**: Your custom stop logic (if provided)

```python
from ai_orchestrator import decide_stop, RoundtableConfig

# Check if should stop
decision = decide_stop(config, iterations)
if decision.should_stop:
    print(f"Stopping: {decision.reason}")
    print(f"Stopped by: {decision.stopped_by}")
```

## Built-in Agents

The library includes pre-built agents for common use cases:

- **PRDCritic**: Reviews product requirements for quality and clarity
- **EngineeringCritic**: Reviews for technical feasibility
- **AIRiskCritic**: Reviews for AI safety and evaluation strategy
- **Moderator**: Refines documents based on reviews
- **DynamicCritic**: Configurable critic that takes any system prompt
- **MetaOrchestrator**: AI that generates appropriate roundtable participants

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ai_orchestrator

# Run specific test file
pytest tests/test_convergence.py -v
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/ai_orchestrator

# Linting
ruff check src/
```

## License

MIT

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
