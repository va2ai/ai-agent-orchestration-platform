# Looping PRD Refinement Agent

## Project Overview
Automated PRD quality improvement system using 3 critic agents (product, engineering, AI risk).

## Architecture
- **Framework:** LangChain + OpenAI
- **Pattern:** Looping refinement with convergence checking
- **Storage:** JSON file-based versioning

## Directory Structure
```
round/
├── api/                    # NEW: FastAPI web layer
│   ├── main.py             # FastAPI app entry point
│   ├── routes/             # API endpoints
│   │   ├── sessions.py     # Session CRUD
│   │   ├── refinement.py   # Refinement start/status
│   │   └── websocket.py    # WebSocket handler
│   ├── models/
│   │   └── api_models.py   # Request/response models
│   └── services/
│       └── async_orchestrator.py  # Async refinement
├── ui/                     # NEW: Web dashboard
│   ├── index.html          # Main dashboard
│   └── static/
│       ├── css/styles.css
│       └── js/
│           ├── app.js      # Main app logic
│           ├── websocket.js # WebSocket client
│           └── visualization.js # Progress display
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
│   └── logger.py
├── data/prds/              # Versioned PRD storage
├── main.py                 # CLI entry point
└── run_api.py              # NEW: API server startup
```

## Usage

### Installation
```bash
pip install -r requirements.txt
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

### Option 1: Web Dashboard (NEW)
```bash
python run_api.py
```
Then open http://localhost:8000 in your browser.

Features:
- Real-time progress visualization
- WebSocket live updates
- Session history
- Interactive API docs at /docs

See [API_DASHBOARD.md](docs/API_DASHBOARD.md) for full documentation.

### Option 2: CLI (Original)
```bash
python main.py --input initial_prd.md --title "Feature X" --max-iterations 3
```

### CLI Arguments
- `--input`: Path to initial PRD markdown file (required)
- `--title`: PRD title (default: filename)
- `--max-iterations`: Max refinement iterations (default: 3)

## Agents

### 1. PRDCritic
Reviews for product quality and clarity.
Focus areas: user value proposition, success metrics, MVP scope, competitive analysis, acceptance criteria, edge cases, product-market fit.

### 2. EngineeringCritic
Reviews for engineering feasibility.
Focus areas: technical feasibility, scalability, security risks, performance concerns, architectural complexity, implementation clarity, resource requirements.

### 3. AIRiskCritic
Reviews for AI safety and evaluation strategy.
Focus areas: hallucination risks, bias and fairness, adversarial robustness, evaluation metrics, test datasets, monitoring strategy, guardrails, human-in-the-loop requirements.

### 4. Moderator
Refines PRD based on critic feedback.
Rules: Fix ALL High severity issues, fix Medium issues if they materially improve clarity/feasibility, preserve MVP focus, maintain clear structure.

## Convergence

The system stops when:
1. **No High severity issues remain** (primary convergence), OR
2. **Max iterations reached** (fallback), OR
3. **PRD delta < 5%** (stable PRD)

## Output Structure

Each session creates a directory: `data/prds/session_<timestamp>/`

Files generated:
- `prd_v1.json`, `prd_v2.json`, ... - Versioned PRDs
- `reviews_v1.json`, `reviews_v2.json`, ... - Critic reviews per version
- `convergence_report.json` - Final convergence report

### Convergence Report Schema
```json
{
  "session_id": "session_20260129_...",
  "title": "Feature X",
  "initial_version": 1,
  "final_version": 2,
  "iterations": 2,
  "converged": true,
  "convergence_reason": "No high severity issues (0 remaining)",
  "total_issues_identified": 15,
  "final_issue_count": {
    "high": 0,
    "medium": 3,
    "low": 5
  },
  "timestamps": {
    "start": "2026-01-29T10:00:00",
    "end": "2026-01-29T10:05:00"
  },
  "history": [...]
}
```

## Implementation Details

### Models (Pydantic)
- **PRD**: Version, title, content, metadata, created_at, reviews
- **PRDReview**: Reviewer name, issues, overall_assessment, timestamp
- **PRDIssue**: Category, description, severity (High/Medium/Low), suggested_fix, reviewer

### Severity Guidelines
- **High**: Missing core features, unclear success metrics, major architectural flaws, security vulnerabilities, missing evaluation strategy, high hallucination risk
- **Medium**: Improvements to clarity or feasibility
- **Low**: Minor enhancements

### LangChain Integration
- Uses `ChatOpenAI` for LLM calls
- Uses `JsonOutputParser` for structured outputs
- Uses `SystemMessage` + `HumanMessage` for prompts
- Model: `gpt-4-turbo` (temperature: 0.2 for critics, 0.3 for moderator)

## Testing

### Create a sample PRD
```bash
cat > test_prd.md << 'EOF'
# AI Chatbot Feature

Build an AI-powered chatbot for customer support.

## Features
- Answer customer questions
- Handle basic queries
- Escalate complex issues

## Success Metrics
- User satisfaction
EOF
```

### Run refinement
```bash
python main.py --input test_prd.md --title "AI Chatbot" --max-iterations 3
```

### Verify output
```bash
# Check generated files
ls data/prds/session_*/

# View convergence report
cat data/prds/session_*/convergence_report.json
```

## Token Budget
- Average PRD: ~2K tokens
- Reviews: ~1K tokens each
- Refinement: ~3K tokens
- Total per iteration: ~10K tokens
- Budget: ~30K tokens for 3 iterations

## Future Enhancements
1. Parallel critic execution (async for 3x speedup)
2. Flask web UI (visual PRD editor and review interface)
3. Custom models (allow model selection per agent)
4. Human-in-the-loop (approve changes before refinement)
5. Metrics dashboard (track convergence trends)
6. Export formats (PDF, Notion, Confluence)

## Notes
- All PRD content stored as markdown strings
- Reviews embedded in PRD model for easy persistence
- Atomic writes with JSON for data integrity
- Session-based directory structure for organization
- Complete history captured for audit trail

## Test Results

Successfully tested with `test_prd.md` on 2026-01-29:
- Initial PRD: 7 lines (basic chatbot description)
- Final PRD: Comprehensive 4KB document with detailed specifications
- Iterations: 3
- Issues identified: 46 total (12 high in iteration 1, reduced to 3 by iteration 3)
- Refinement time: ~4 minutes
- Convergence: Max iterations reached (3 remaining high issues in engineering/AI risk)
- Output quality: Production-ready PRD with complete sections for MVP scope, success metrics, technical specifications, security measures, AI safety, and edge cases

## Enhancements (2026-01-29)

### Enhanced Logging System
- Added comprehensive logging of all LLM interactions
- Token usage tracking per agent
- Separate log files for each critic and moderator
- Verbose mode (`--verbose` or `-v`) for detailed console output
- Token usage displayed in console and convergence report
- Full request/response logging to `refinement.log`
- Critic assessments saved to separate response logs
- Moderator outputs logged to dedicated file

### New Files
- `utils/logger.py` - Enhanced logging infrastructure
- `LOGGING.md` - Complete logging documentation
- Session logs: `refinement.log`, `*_critic_responses.log`, `moderator_outputs.log`

### Token Usage Tracking
- Per-agent token tracking (prd_critic, engineering_critic, ai_risk_critic, moderator)
- Console display of total and per-agent tokens
- Token data included in convergence report
- Verbose mode shows tokens after each LLM call

## API + Dashboard (2026-01-29)

### Web-Based Refinement System
Added FastAPI backend and real-time dashboard for browser-based PRD refinement.

### New Components

**Backend (api/)**
- `api/main.py` - FastAPI application with CORS and static file serving
- `api/routes/sessions.py` - Session CRUD endpoints
- `api/routes/refinement.py` - Refinement start/status with background tasks
- `api/routes/websocket.py` - WebSocket connection manager for real-time updates
- `api/models/api_models.py` - Pydantic request/response models
- `api/services/async_orchestrator.py` - Async version with parallel critic execution

**Frontend (ui/)**
- `ui/index.html` - Main dashboard with Tailwind CSS
- `ui/static/js/app.js` - Main application logic
- `ui/static/js/websocket.js` - WebSocket client with reconnection
- `ui/static/js/visualization.js` - Progress visualization
- `ui/static/css/styles.css` - Custom styles

**Infrastructure**
- `run_api.py` - Server startup script
- `test_api.py` - Comprehensive API test suite
- `API_DASHBOARD.md` - Full API documentation

### Key Features

1. **Real-time Updates**: WebSocket broadcasts 7 event types for live progress
2. **Async Orchestration**: Critics run in parallel (2-3x faster than CLI)
3. **Session History**: Browse and reload past refinement sessions
4. **Interactive Docs**: Auto-generated OpenAPI docs at /docs
5. **Dual Interface**: CLI still available, API runs independently

### API Endpoints

- `POST /api/refinement/start` - Start refinement
- `GET /api/refinement/status/{session_id}` - Get status
- `GET /api/sessions/` - List sessions
- `GET /api/sessions/{id}/prd/{version}` - Get PRD version
- `GET /api/sessions/{id}/report` - Get convergence report
- `WS /ws/refinement/{session_id}` - Real-time updates

### WebSocket Events

1. session_created
2. iteration_start
3. critic_review_start/complete
4. convergence_check
5. moderator_start/complete
6. refinement_complete

### Usage

**Start Server:**
```bash
python run_api.py
```

**Access Dashboard:**
http://localhost:8000/

**Run Tests:**
```bash
python test_api.py
```

### Performance

- Async orchestrator: 2-3 minutes vs 4 minutes (CLI)
- Parallel critic execution
- Non-blocking WebSocket updates
- Background task processing

### Storage Enhancement

Added methods to `prd_storage.py`:
- `list_sessions()` - List all sessions
- `get_session_metadata()` - Get session info
- `session_exists()` - Check existence
- `load_convergence_report()` - Load report
- `load_reviews()` - Load reviews

### Dependencies Added

- fastapi==0.115.6
- uvicorn[standard]==0.34.0
- websockets==14.1
- python-multipart==0.0.20
- jinja2==3.1.5
- aiofiles==24.1.0

## Continuation Feature (2026-01-29)

### Continue Refinement After Max Iterations

Added ability to continue refinement when max iterations reached but high severity issues remain.

### Key Features

1. **Smart Detection**: UI automatically detects when:
   - Convergence reason is "Max iterations reached"
   - High severity issues remain (> 0)

2. **Continue Button**: Orange "Continue Refinement" button appears in results view
   - Shows count of remaining high issues
   - Opens dialog to specify additional iterations (1-10)

3. **Session Resumption**:
   - Loads existing roundtable configuration
   - Reconstructs critics and moderator with same settings
   - Continues from last document version
   - Preserves all previous work and history

4. **Updated Report**: Final convergence report includes:
   - `continued_from_iteration` field
   - Updated iteration count
   - New convergence status

### API Endpoint

```
POST /api/refinement/continue/{session_id}?additional_iterations=3
```

**Response:**
```json
{
  "session_id": "session_20260129_...",
  "status": "continued",
  "previous_iterations": 4,
  "new_max_iterations": 7,
  "additional_iterations": 3
}
```

### Usage Flow

1. User runs refinement, reaches max iterations (e.g., 4)
2. System shows: "Max iterations reached (4). 6 high severity issues remain."
3. User sees orange "Continue Refinement (6 high issues)" button
4. User clicks button, specifies 3 additional iterations
5. System resumes refinement from iteration 5, runs up to iteration 7
6. New convergence report saved with final status

### Implementation Files

**Backend:**
- `api/routes/refinement.py` - Added `/continue` endpoint and `run_continuation()` function
- `api/services/dynamic_async_orchestrator.py` - Added `continue_from()` method

**Frontend:**
- `ui/static/js/app.js` - Added:
  - `startMonitoring()` - WebSocket monitoring with event handlers
  - `showContinueButtonIfNeeded()` - Detects and displays continue option
  - `showContinueDialog()` - User input for additional iterations
  - `continueRefinement()` - API call to resume refinement

### Benefits

- No work lost when hitting iteration limits
- Allows incremental refinement based on remaining issues
- Preserves roundtable consistency
- Full audit trail with continuation tracking

## Gemini Model Support (2026-01-29)

### Multi-Provider LLM Support

Added support for Google Gemini models alongside OpenAI GPT models.

### Supported Models

**Google Gemini:**
- `gemini-3-pro-preview` - Latest Gemini 3 Pro (1M context, $2-4/$12-18 per 1M tokens)
- `gemini-3-flash-preview` - Latest Gemini 3 Flash (1M context, $0.50/$3 per 1M tokens)
- `gemini-2.5-flash` - Stable Gemini 2.5 Flash
- `gemini-2.5-pro` - Stable Gemini 2.5 Pro
- `gemini-flash-latest` - Latest Flash (auto-updates)
- `gemini-pro-latest` - Latest Pro (auto-updates)
- `gemini-1.5-pro` - Gemini 1.5 Pro
- `gemini-1.5-flash` - Gemini 1.5 Flash

**OpenAI GPT:**
- `gpt-5.2` (Recommended)
- `gpt-5.2-pro`
- `gpt-5`, `gpt-5-mini`, `gpt-5-nano`
- `gpt-4.1`, `gpt-4o`, `gpt-4-turbo`

**Anthropic Claude:**
- `claude-3-5-sonnet-20240620`
- `claude-3-opus-20240229`

### LLM Factory

**New File:** `utils/llm_factory.py`

Factory pattern for creating LLM instances:
- `create_llm(model, temperature)` - Auto-detects provider from model name
- `get_model_provider(model)` - Returns "openai" or "google"
- `is_gemini_model(model)` - Check if model is Gemini
- `is_openai_model(model)` - Check if model is OpenAI

### Environment Setup

Add to `.env`:
```bash
# OpenAI (for GPT models)
OPENAI_API_KEY=sk-your-key-here

# Google Gemini (for Gemini models)
GOOGLE_API_KEY=your-gemini-api-key-here
# Alternative: GEMINI_API_KEY=your-gemini-api-key-here
```

Get Gemini API key: https://aistudio.google.com/apikey

### Diverse Model Strategy

When `model_strategy: "diverse"` is selected, critics use round-robin assignment from:
1. gpt-5.2
2. gemini-3-pro-preview
3. gpt-5.2-pro
4. gemini-3-flash-preview
5. claude-3-5-sonnet-20240620
6. gpt-5
7. gemini-2.5-flash
8. gpt-4o
9. gemini-1.5-pro
10. gpt-4.1

### Implementation

**Updated Files:**
- `agents/dynamic_critic.py` - Uses LLM factory for both critic and moderator
- `api/services/dynamic_async_orchestrator.py` - Updated diverse model list
- `ui/index.html` - Added Gemini models to dropdown with organized optgroups
- `requirements.txt` - Added `langchain-google-genai==2.0.8`
- `.env.example` - Added GOOGLE_API_KEY placeholder

### Pricing Comparison (per 1M tokens)

| Model | Input | Output | Context |
|-------|-------|--------|---------|
| gemini-3-flash-preview | $0.50 | $3 | 1M |
| gemini-3-pro-preview | $2-4 | $12-18 | 1M |
| gpt-5.2 | TBD | TBD | TBD |
| claude-3-5-sonnet | $3 | $15 | 200K |

### Notes

- Gemini models support 1M token context window (much larger than GPT-4)
- Gemini doesn't support system messages - automatically converted to human messages
- Preview models may have rate limits and require 2-week deprecation notice
- Latest aliases (`gemini-flash-latest`) auto-update to newest versions
