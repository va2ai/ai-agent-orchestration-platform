# Dynamic Roundtable Refinement System

An AI-powered document refinement system that dynamically generates expert participants for any topic. Uses AI to create a custom "roundtable discussion" of experts who iteratively review and refine documents until convergence.

**NEW**: The system now uses AI to generate appropriate critics based on your topic, not just PRDs!

## Features

- **🤖 AI-Generated Roundtables**
  - System analyzes your topic and dynamically generates appropriate expert participants
  - Each participant has custom system prompts tailored to their role
  - Works for ANY document type: PRDs, architecture designs, code reviews, business strategies, etc.
  - Choose number of participants (2-6) or use presets

- **📋 Pre-built Templates** (or fully custom)
  - **PRD Mode**: Product Manager + Engineering Lead + AI Safety Expert
  - **Code Review**: Senior Dev + Security Expert + Performance Engineer
  - **Architecture**: System Architect + DevOps + Security + Operations
  - **Business Strategy**: Market Analyst + Financial Advisor + Operations Expert

- **🧠 Intelligent Moderator**: Refines documents based on participant feedback

- **Convergence Detection**: Automatically stops when:
  - No High severity issues remain
  - Max iterations reached
  - PRD delta < 5% (stable)

- **Version Control**: JSON-based PRD versioning with full audit trail

- **Structured Output**: Pydantic models ensure type safety and validation

- **Web Dashboard**: Real-time visualization with WebSocket updates (NEW)

- **REST API**: Full API for integration and automation (NEW)

- **Async Orchestration**: Parallel critic execution for 2-3x speed improvement (NEW)

## Installation

```bash
# Clone or navigate to the repository
cd /c/Users/ccdmn/code/round

# Install dependencies
pip install -r requirements.txt

# Set up environment (if not already in environment)
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

## Quick Start

### Web Dashboard (Recommended)

```bash
# Start the API server
python run_api.py

# Open in browser
# http://localhost:8000
```

**Try these examples**:
1. **Upload a Document**: Click "Choose File" → Upload PDF, Word, or text file → Content auto-populates

2. **Set a Goal**:
   - Document: "VA Rating Decision"
   - Goal: "Write a comprehensive appeal"
   - → AI generates: Veterans Law Attorney, Medical Expert, Appeals Specialist

3. **Custom Topic**: Enter any topic → AI generates appropriate experts
   - "Microservices Migration Strategy" → Cloud Architect, DevOps, Database Expert, Security
   - "Marketing Campaign Plan" → Marketing Strategist, Data Analyst, Content Creator

4. **Use Presets**: Select from dropdown (PRD, Code Review, Architecture, Business Strategy)

5. **Customize**: Choose number of participants (2-6 experts)

See [GOAL_AND_UPLOAD.md](GOAL_AND_UPLOAD.md) for detailed documentation on goal field and file upload.

### CLI (Original)

```bash
# Run with sample PRD
python main.py --input test_prd.md --title "AI Chatbot" --max-iterations 3

# Run with your own PRD
python main.py --input path/to/your/prd.md --title "Your Feature" --max-iterations 5
```

## Usage

```bash
python main.py --input <file> [--title <name>] [--max-iterations <num>]
```

### Arguments

- `--input`: Path to initial PRD markdown file (required)
- `--title`: PRD title (optional, defaults to filename)
- `--max-iterations`: Max refinement iterations (optional, default: 3)
- `--verbose`, `-v`: Enable verbose logging (optional, shows LLM outputs and token usage)

## Example Output

```
Starting PRD Refinement
   Title: AI Chatbot
   Max Iterations: 3

Created session: session_20260129_005523
Saved PRD v1

Iteration 1/3
  Critics reviewing...
    - prd_critic: 6 issues (4 high)
    - engineering_critic: 5 issues (3 high)
    - ai_risk_critic: 7 issues (5 high)
  Status: 12 high severity issues remain
  Moderator refining PRD...
Saved PRD v2

Iteration 2/3
  Critics reviewing...
    - prd_critic: 4 issues (1 high)
    - engineering_critic: 5 issues (2 high)
    - ai_risk_critic: 5 issues (1 high)
  Status: 4 high severity issues remain
  Moderator refining PRD...
Saved PRD v3

Iteration 3/3
  Critics reviewing...
    - prd_critic: 4 issues (0 high)
    - engineering_critic: 5 issues (2 high)
    - ai_risk_critic: 5 issues (1 high)
  Status: Max iterations reached (3). 3 high severity issues remain.
PRD converged!

Report saved to: session_20260129_005523/convergence_report.json

============================================================
REFINEMENT COMPLETE
============================================================
Final Version: 3
Converged: True
Reason: Max iterations reached (3). 3 high severity issues remain.
Final Issues: 3 high, 10 medium, 1 low

Session: session_20260129_005523
```

## Output Files

Each session creates a directory: `data/prds/session_<timestamp>/`

Generated files:
- `prd_v1.json`, `prd_v2.json`, `prd_v3.json` - Versioned PRDs
- `reviews_v1.json`, `reviews_v2.json`, `reviews_v3.json` - Critic reviews
- `convergence_report.json` - Final convergence report with token usage
- `refinement.log` - Detailed log of all operations
- `prd_critic_responses.log` - Product critic assessments
- `engineering_critic_responses.log` - Engineering critic assessments
- `ai_risk_critic_responses.log` - AI safety critic assessments
- `moderator_outputs.log` - All refined PRD versions

## Logging

The system provides comprehensive logging of all LLM interactions and refinement steps.

### Normal Mode (default)
```bash
python main.py --input test_prd.md
```
- Displays progress and final token usage
- All details saved to log files

### Verbose Mode
```bash
python main.py --input test_prd.md --verbose
# or
python main.py --input test_prd.md -v
```
- Shows LLM response previews
- Displays token usage per call
- Shows issue previews as they're found
- Displays content length changes

### Log Files

**`refinement.log`** - Complete debug log with:
- All LLM requests and responses
- Token usage per call
- Issue details
- Convergence checks

**`*_critic_responses.log`** - Critic assessment summaries

**`moderator_outputs.log`** - Full refined PRD content

See [LOGGING.md](LOGGING.md) for detailed logging documentation.

## Web Dashboard Features

- **🎯 Dynamic Roundtable Generation**: AI creates expert participants for your specific topic
- **📊 Real-time Progress**: Live updates via WebSocket
- **📝 Activity Log**: See participant reviews as they happen
- **📈 Metrics**: Track High/Medium issues and token usage
- **🗂️ Session History**: Browse and reload past refinements
- **📄 Markdown Rendering**: Beautiful document display
- **📚 API Documentation**: Interactive docs at /docs
- **🎭 Participant View**: See generated experts and their roles

## Dynamic Capabilities

### How It Works
1. **Enter your topic** (e.g., "Microservices Architecture for E-commerce")
2. **AI analyzes** the topic and generates appropriate expert participants
3. **Participants review** the document from their unique perspectives
4. **Moderator refines** based on all feedback
5. **Iterate** until convergence

### Use Cases

**Product Development**
- Product Requirements Documents (PRDs)
- Feature specifications
- User stories

**Technical Design**
- System architecture proposals
- API design documents
- Database schema designs
- Migration plans

**Code Quality**
- Code review summaries
- Refactoring plans
- Implementation reviews

**Business Strategy**
- Business plans
- Market analysis
- Pricing strategies
- Go-to-market plans

**Documentation**
- Technical documentation
- User guides
- API documentation

See [DYNAMIC_SYSTEM.md](DYNAMIC_SYSTEM.md) for complete documentation on the dynamic roundtable system.

## Architecture

```
round/
├── api/                    # FastAPI backend (NEW)
│   ├── main.py             # FastAPI app
│   ├── routes/             # REST endpoints + WebSocket
│   ├── models/             # API request/response models
│   └── services/           # Async orchestrator
├── ui/                     # Web dashboard (NEW)
│   ├── index.html          # Main dashboard
│   └── static/             # CSS + JavaScript
├── agents/                 # Critic and moderator agents
│   ├── prd_critic.py       # Product quality reviewer
│   ├── engineering_critic.py # Technical feasibility reviewer
│   ├── ai_risk_critic.py   # AI safety & evaluation reviewer
│   └── moderator.py        # PRD refiner
├── models/                 # Pydantic data models
│   └── prd_models.py       # PRD, PRDIssue, PRDReview
├── orchestration/          # Main loop coordinator (CLI)
│   └── looping_orchestrator.py
├── storage/                # JSON persistence
│   └── prd_storage.py
├── prompts/                # System prompts
│   └── system_prompts.py
├── utils/                  # Helper utilities
│   ├── convergence.py      # Convergence checking logic
│   └── logger.py           # Enhanced logging
├── data/prds/              # Versioned PRD storage
├── main.py                 # CLI entry point
└── run_api.py              # API server startup (NEW)
```

## How It Works

1. **Initialization**: System reads initial PRD and creates a session
2. **Review Phase**: 3 critic agents independently review the PRD
3. **Convergence Check**: System checks if High severity issues remain
4. **Refinement Phase**: Moderator refines PRD based on critic feedback
5. **Iteration**: Steps 2-4 repeat until convergence or max iterations
6. **Reporting**: Final convergence report generated with full history

## Severity Levels

- **High**: Missing core features, unclear success metrics, major architectural flaws, security vulnerabilities, missing evaluation strategy
- **Medium**: Improvements to clarity or feasibility
- **Low**: Minor enhancements

## Models Used

- **Critics**: `gpt-4-turbo` (temperature: 0.2)
- **Moderator**: `gpt-4-turbo` (temperature: 0.3)

## Token Budget

- Average PRD: ~2K tokens
- Reviews: ~1K tokens each
- Refinement: ~3K tokens
- Total per iteration: ~10K tokens
- Budget: ~30K tokens for 3 iterations

## API Documentation

See [API_DASHBOARD.md](API_DASHBOARD.md) for complete API documentation including:
- REST endpoints
- WebSocket events
- Request/response schemas
- Usage examples
- Deployment guide

## Testing

### API Tests
```bash
python test_api.py
```

### Manual Testing
1. Start server: `python run_api.py`
2. Open http://localhost:8000
3. Submit a test PRD
4. Watch real-time refinement
5. View results

## Future Enhancements

1. ~~Parallel critic execution (async for 3x speedup)~~ ✓ DONE
2. ~~Web UI (visual PRD editor and review interface)~~ ✓ DONE
3. Custom models (allow model selection per agent)
4. Human-in-the-loop (approve changes before refinement)
5. Metrics dashboard (track convergence trends)
6. Export formats (PDF, Notion, Confluence)
7. Database integration (PostgreSQL for sessions)
8. Authentication (OAuth2/JWT)

## License

MIT

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## Support

For issues or questions, please open an issue on GitHub.
