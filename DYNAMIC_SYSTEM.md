# Dynamic Roundtable System

## Overview

Transformed the PRD-specific refinement system into a **dynamic AI roundtable** that can handle any type of document or discussion topic. The system now uses AI to generate appropriate expert participants on-the-fly.

## Key Changes

### 1. Meta-Orchestrator (`agents/meta_orchestrator.py`)
**Purpose**: AI that generates AI participants

- Analyzes user's topic and content
- Generates N expert participants with:
  - Name/role (e.g., "Senior Backend Engineer")
  - Expertise areas
  - Perspective they bring
  - Complete system prompt tailored to their role
- Defines moderator focus and convergence criteria
- Supports presets (PRD, code-review, architecture, business-strategy)

**Example Output**:
```python
{
  "participants": [
    {
      "name": "Alex Morgan",
      "role": "AI Ethics Specialist",
      "expertise": "AI safety, bias detection, fairness",
      "perspective": "Ethical implications",
      "system_prompt": "You are an AI Ethics Specialist..."
    },
    {
      "name": "Jordan Lee",
      "role": "Technical Architect",
      "expertise": "System design, scalability, performance",
      "perspective": "Technical feasibility",
      "system_prompt": "You are a Technical Architect..."
    },
    {
      "name": "Taylor Kim",
      "role": "User Experience Designer",
      "expertise": "UX design, user research, accessibility",
      "perspective": "User experience",
      "system_prompt": "You are a UX Designer..."
    }
  ],
  "moderator_focus": "Balance feedback from all perspectives...",
  "convergence_criteria": "Converge when no High severity issues remain..."
}
```

### 2. Dynamic Critic (`agents/dynamic_critic.py`)
**Purpose**: Flexible critic that can take on any role

- Replaces hardcoded PRDCritic, EngineeringCritic, AIRiskCritic
- Accepts name, role, and system_prompt as parameters
- Can represent any expert perspective
- Uses same review structure (issues with severity)

**Example Usage**:
```python
critic = DynamicCritic(
    name="Security Architect",
    role="Review for security vulnerabilities",
    system_prompt="You are a Security Architect..."
)
```

### 3. Dynamic Moderator (`agents/dynamic_moderator.py`)
**Purpose**: Flexible moderator with configurable focus

- Takes moderator_focus instruction
- Refines documents based on any set of reviews
- Adapts to different document types

### 4. Generic Document Model (`models/document_models.py`)
**Purpose**: Content-agnostic data model

- Renamed `PRD` → `Document`
- Added `document_type` field (e.g., "prd", "architecture", "code-review")
- Works for any content type
- Backwards compatible (PRD = Document alias)

### 5. Dynamic Orchestrator (`orchestration/dynamic_orchestrator.py`)
**Purpose**: Main orchestration logic for dynamic system

- Generates roundtable participants before starting
- Creates dynamic critics from participant configs
- Runs parallel reviews
- Handles convergence
- Saves reports with participant info

### 6. API Integration
**Updated Files**:
- `api/models/api_models.py` - Added fields for document_type, num_participants, use_preset
- `api/services/dynamic_async_orchestrator.py` - Async version with WebSocket updates
- `api/routes/refinement.py` - Updated to use dynamic orchestrator

**New API Fields**:
```json
{
  "title": "Topic/Title",
  "content": "Initial content",
  "max_iterations": 3,
  "document_type": "architecture",
  "num_participants": 4,
  "use_preset": "architecture",  // optional
  "metadata": {}  // optional
}
```

**New WebSocket Event**:
- `roundtable_generated` - Broadcasts generated participants to UI

### 7. Updated UI (`ui/index.html`, `ui/static/js/app.js`)
**New Form Fields**:
- Document Type (text input)
- Use Preset Template (dropdown: custom, prd, code-review, architecture, business-strategy)
- Number of Participants (2-6)

**UI Changes**:
- Updated labels from "PRD" to generic "Document/Topic"
- Shows generated participants in activity log
- Button text: "Generate Roundtable & Start"

## Usage Examples

### Example 1: Custom Topic (AI-Generated Participants)
```python
POST /api/refinement/start
{
  "title": "Microservices Migration Strategy",
  "content": "Plan to migrate monolith to microservices...",
  "document_type": "architecture",
  "num_participants": 4,
  "max_iterations": 3
}
```

**AI Generates**:
- Cloud Architect
- DevOps Engineer
- Database Specialist
- Security Expert

### Example 2: Using PRD Preset
```python
POST /api/refinement/start
{
  "title": "AI Chatbot Feature",
  "content": "Build AI chatbot for customer support...",
  "document_type": "prd",
  "use_preset": "prd",
  "max_iterations": 3
}
```

**Preset Provides**:
- Product Manager
- Engineering Lead
- AI Safety Expert

### Example 3: Code Review Mode
```python
POST /api/refinement/start
{
  "title": "Authentication System Review",
  "content": "Review auth implementation code...",
  "document_type": "code-review",
  "use_preset": "code-review",
  "num_participants": 3,
  "max_iterations": 2
}
```

**Preset Provides**:
- Senior Backend Developer
- Security Auditor
- Performance Engineer

### Example 4: Business Strategy
```python
POST /api/refinement/start
{
  "title": "SaaS Pricing Strategy",
  "content": "Define pricing tiers and models...",
  "document_type": "business-strategy",
  "use_preset": "business-strategy",
  "max_iterations": 3
}
```

**Preset Provides**:
- Market Analyst
- Financial Advisor
- Operations Expert

## Presets Available

### 1. `prd` - Product Requirements Document
- **Participants**: 3
- **Focus**: Product quality, engineering feasibility, AI safety
- **Use for**: Product features, new capabilities, user-facing functionality

### 2. `code-review` - Code Review & Improvement
- **Participants**: 3
- **Focus**: Code quality, security, performance
- **Use for**: Code reviews, refactoring plans, implementation reviews

### 3. `architecture` - System Architecture Design
- **Participants**: 4
- **Focus**: Scalability, security, maintainability, operations
- **Use for**: System designs, architecture proposals, technical designs

### 4. `business-strategy` - Business Strategy Document
- **Participants**: 3
- **Focus**: Market analysis, financial viability, operational feasibility
- **Use for**: Business plans, strategy documents, market analysis

## Benefits

### 1. Flexibility
- Works for ANY topic or document type
- Not limited to PRDs
- Adapts to user needs

### 2. AI-Powered Intelligence
- AI understands the topic and generates appropriate experts
- System prompts tailored to each participant's role
- Ensures comprehensive coverage

### 3. Customization
- Choose preset or fully custom
- Control number of participants (2-6)
- Metadata for additional context

### 4. Backwards Compatibility
- Old PRD-specific code still works (via aliases)
- CLI unchanged
- Existing sessions still load

## Architecture

```
User Request
    ↓
Meta-Orchestrator (AI)
    ↓
Generates Participants
    - Names
    - Roles
    - System Prompts
    ↓
Dynamic Critics Created
    ↓
Parallel Reviews
    ↓
Dynamic Moderator Refines
    ↓
Iterative Loop Until Convergence
    ↓
Final Document + Report
```

## File Structure

```
round/
├── agents/
│   ├── meta_orchestrator.py     # NEW: AI that generates participants
│   ├── dynamic_critic.py         # NEW: Flexible critic
│   ├── prd_critic.py             # OLD: Still works for CLI
│   ├── engineering_critic.py     # OLD: Still works for CLI
│   ├── ai_risk_critic.py         # OLD: Still works for CLI
│   └── moderator.py              # OLD: Still works for CLI
├── models/
│   ├── document_models.py        # NEW: Generic document model
│   └── prd_models.py             # OLD: Aliases to document_models
├── orchestration/
│   ├── dynamic_orchestrator.py   # NEW: Dynamic orchestration
│   └── looping_orchestrator.py   # OLD: Still works for CLI
├── api/
│   ├── services/
│   │   ├── dynamic_async_orchestrator.py  # NEW: API version
│   │   └── async_orchestrator.py          # OLD: PRD-specific
│   ├── routes/
│   │   └── refinement.py         # UPDATED: Uses dynamic system
│   └── models/
│       └── api_models.py         # UPDATED: New fields
└── ui/
    ├── index.html                # UPDATED: New form fields
    └── static/js/
        └── app.js                # UPDATED: New event handlers
```

## Token Usage

**Meta-Orchestrator**:
- Generates participants: ~2,000-3,000 tokens (one-time cost)
- Adds ~$0.02 per session

**Dynamic Critics**:
- Same as before: ~1,000 tokens per review
- 3 participants × 3 iterations = ~9,000 tokens

**Total**: Similar to before + one-time participant generation

## Future Enhancements

1. **Save Custom Presets**: Allow users to save their own roundtable configurations
2. **Participant Templates**: Library of pre-configured expert personas
3. **Human-in-the-Loop**: Review and modify generated participants before starting
4. **Adaptive Participants**: Add/remove participants mid-discussion
5. **Cross-Document Refinement**: Refine multiple related documents together
6. **Export Transcripts**: Save full discussion as readable transcript

## Testing

Start the server:
```bash
python run_api.py
```

Open dashboard:
```
http://localhost:8000
```

Try:
1. Custom topic with AI-generated participants
2. PRD preset
3. Architecture preset
4. Code review preset

## Success Criteria

✅ Meta-orchestrator generates appropriate participants
✅ Dynamic critics work with any role/prompt
✅ Generic document model handles all types
✅ API accepts new parameters
✅ UI shows generated participants
✅ WebSocket broadcasts roundtable info
✅ Backwards compatible with old CLI
✅ All sessions cleared successfully

## Migration Notes

- **Existing CLI**: No changes needed, still works
- **Old API calls**: Still work (use default document_type="document", num_participants=3)
- **Sessions**: Old sessions load correctly
- **PRD models**: Aliased to Document models (backwards compatible)
