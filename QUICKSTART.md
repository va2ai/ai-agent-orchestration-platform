# Quick Start Guide

## Prerequisites

- Python 3.13+ installed
- OpenAI API key (in environment variable `OPENAI_API_KEY`)

## Installation (One-time)

```bash
cd /c/Users/ccdmn/code/round
pip install -r requirements.txt
```

## Basic Usage

### 1. Create a PRD file

Create a markdown file with your initial PRD:

```markdown
# My Feature

Brief description of the feature.

## Features
- Feature 1
- Feature 2

## Success Metrics
- Metric 1
```

### 2. Run the refinement

```bash
python main.py --input my_prd.md --title "My Feature" --max-iterations 3
```

### 3. Review the output

Check the `data/prds/session_<timestamp>/` directory:
- `prd_v<N>.json` - Versioned PRDs
- `reviews_v<N>.json` - Critic feedback
- `convergence_report.json` - Final report

## Example Session

```bash
# Use the included test PRD
python main.py --input test_prd.md --title "AI Chatbot" --max-iterations 3

# Expected output:
# - Initial PRD: 7 lines
# - Final PRD: Comprehensive document with 10+ sections
# - Time: ~3-5 minutes
# - Iterations: 3
# - Issues resolved: 12 high → 3 high
```

## Understanding the Output

### Console Output

```
Iteration 1/3
  Critics reviewing...
    - prd_critic: 6 issues (4 high)
    - engineering_critic: 5 issues (3 high)
    - ai_risk_critic: 7 issues (5 high)
  Status: 12 high severity issues remain
```

This shows:
- How many issues each critic found
- Number of High severity issues (blocking)
- Current convergence status

### Convergence Report

```json
{
  "final_version": 3,
  "converged": true,
  "convergence_reason": "Max iterations reached (3). 3 high severity issues remain.",
  "final_issue_count": {
    "high": 3,
    "medium": 10,
    "low": 1
  }
}
```

This shows:
- Final PRD version number
- Whether convergence was achieved
- Reason for stopping
- Remaining issues by severity

## Tips

1. **Start simple**: Begin with a basic PRD outline
2. **Iterate more**: Use `--max-iterations 5` for complex PRDs
3. **Review feedback**: Check `reviews_v1.json` to understand initial issues
4. **Track progress**: Compare `prd_v1.json` vs `prd_v3.json` to see improvements

## Common Issues

### No OPENAI_API_KEY

```bash
# Set the API key
export OPENAI_API_KEY=sk-your-key-here
```

### Import errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### File not found

```bash
# Use absolute path
python main.py --input /c/Users/ccdmn/code/round/my_prd.md
```

## What Gets Improved

The critics focus on:

### Product Critic
- User value proposition
- Success metrics (quantifiable)
- MVP scope definition
- Competitive analysis
- Acceptance criteria
- Edge cases

### Engineering Critic
- Technical feasibility
- Scalability considerations
- Security risks
- Performance concerns
- Architecture clarity
- Implementation details

### AI Risk Critic
- Hallucination risks
- Bias and fairness
- Evaluation metrics
- Test datasets
- Monitoring strategy
- Guardrails
- Human-in-the-loop requirements

## Next Steps

1. Review your refined PRD in `data/prds/session_<timestamp>/prd_v<N>.json`
2. Extract the `content` field (markdown)
3. Use the refined PRD for implementation planning
4. Iterate again if High severity issues remain
