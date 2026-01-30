# Logging Documentation

## Overview

The PRD Refinement Agent includes comprehensive logging to track all LLM interactions, token usage, and refinement progress.

## Log Files

Each session creates multiple log files in `data/prds/session_<timestamp>/`:

### 1. `refinement.log`
**Main log file** containing all debug and info messages.

**Contents:**
- Session initialization
- Iteration progress
- LLM request/response details
- Token usage per call
- Issue breakdowns
- Convergence checks
- Final summary

**Example:**
```
2026-01-29 02:42:41 - INFO - ============================================================
2026-01-29 02:42:41 - INFO - PRD Refinement Session: Test Logging
2026-01-29 02:42:41 - INFO - ============================================================
2026-01-29 02:42:41 - INFO - Session ID: session_20260129_024241
2026-01-29 02:42:41 - INFO - Max iterations: 1
2026-01-29 02:42:41 - INFO - Initial PRD length: 202 chars
...
2026-01-29 02:43:01 - INFO - [prd_critic] Token usage: 242 prompt + 647 completion = 889 total
```

### 2. `prd_critic_responses.log`
**PRD Critic assessments** - All overall assessment summaries from the product critic.

**Format:**
```
============================================================
Timestamp: 2026-01-29T02:43:01.754387
============================================================
The PRD lacks critical details necessary for the successful development...
```

### 3. `engineering_critic_responses.log`
**Engineering Critic assessments** - Technical feasibility assessments.

### 4. `ai_risk_critic_responses.log`
**AI Risk Critic assessments** - AI safety and evaluation assessments.

### 5. `moderator_outputs.log`
**Moderator outputs** - Full refined PRD content from each refinement iteration.

**Contains:**
- Complete refined PRD markdown
- Timestamp for each refinement
- All versions concatenated with separators

### 6. `convergence_report.json`
**Final report** with token usage statistics.

**New fields:**
```json
{
  "token_usage": {
    "prd_critic": 889,
    "engineering_critic": 708,
    "ai_risk_critic": 673,
    "moderator": 3245
  }
}
```

## Verbosity Modes

### Normal Mode (default)
```bash
python main.py --input my_prd.md
```

**Console output:**
- Session creation
- Iteration progress
- Issue counts per critic
- Convergence status
- Final summary with token usage

**Log files:**
- All debug logs written to `refinement.log`
- Critic responses to separate files
- No verbose output to console

### Verbose Mode
```bash
python main.py --input my_prd.md --verbose
# or
python main.py --input my_prd.md -v
```

**Additional console output:**
- Token usage per LLM call
- Preview of critic assessments (first 300 chars)
- Preview of issues found
- Preview of moderator refinements
- Content length changes
- Token breakdown by agent

**Example verbose output:**
```
[prd_critic] Tokens: 889 (242 in / 647 out)

[prd_critic] Overall Assessment Preview:
The PRD lacks critical details necessary for the successful development...

Issue 1 [High]: The user value proposition is not clearly defined...
Issue 2 [High]: Success metrics are too vague...
```

## Token Usage Tracking

### Per-Agent Tracking

Each agent's token usage is tracked separately:
- `prd_critic`: Product review tokens
- `engineering_critic`: Engineering review tokens
- `ai_risk_critic`: AI safety review tokens
- `moderator`: Refinement tokens

### Console Output

**Normal mode:**
```
Token Usage:
  prd_critic: 889 tokens
  engineering_critic: 708 tokens
  ai_risk_critic: 673 tokens
  moderator: 3,245 tokens
  TOTAL: 5,515 tokens
```

**Verbose mode:**
Shows tokens after each LLM call:
```
[prd_critic] Tokens: 889 (242 in / 647 out)
```

### Log File

All token usage logged with detail:
```
2026-01-29 02:43:01 - INFO - [prd_critic] Token usage: 242 prompt + 647 completion = 889 total
```

## Log Analysis

### Find High Severity Issues
```bash
grep "High" data/prds/session_*/refinement.log
```

### Count Total Tokens
```bash
grep "Token usage:" data/prds/session_*/refinement.log | awk '{sum+=$NF} END {print sum}'
```

### View All Critic Assessments
```bash
cat data/prds/session_*/*_critic_responses.log
```

### Extract Moderator Outputs
```bash
cat data/prds/session_*/moderator_outputs.log
```

### Track Convergence
```bash
grep "CONVERGED\|CONTINUING" data/prds/session_*/refinement.log
```

## Log Rotation

Currently, logs append to existing files within a session. Each new session creates a fresh set of log files.

**Log retention:**
- Logs persist indefinitely in `data/prds/`
- Manually clean old sessions as needed
- Consider implementing log rotation for long-running deployments

## Debugging with Logs

### Issue: LLM returns invalid JSON
**Check:**
```bash
grep "Response:" data/prds/session_*/refinement.log | less
```

### Issue: Token usage too high
**Check:**
```bash
grep "Token usage:" data/prds/session_*/refinement.log
```

### Issue: Moderator not improving PRD
**Check:**
```bash
cat data/prds/session_*/moderator_outputs.log
```

### Issue: Critics missing key issues
**Check:**
```bash
cat data/prds/session_*/*_critic_responses.log
```

## Log Levels

### DEBUG
- LLM request prompts (preview)
- Full LLM responses
- Detailed issue breakdowns

### INFO
- Session information
- Iteration progress
- Token usage
- Convergence status
- File operations

### WARNING
- Unusual conditions
- Fallback behaviors

### ERROR
- LLM errors
- Parsing failures
- File I/O errors

## Performance Impact

**Logging overhead:**
- File I/O: ~10-20ms per log entry
- Minimal CPU impact
- Negligible memory usage

**Verbose mode overhead:**
- Console printing: ~50-100ms per iteration
- No impact on LLM calls
- Recommended for debugging only

## Best Practices

### Development
```bash
# Use verbose mode to see what's happening
python main.py --input my_prd.md --verbose
```

### Production
```bash
# Use normal mode for cleaner output
python main.py --input my_prd.md
# Review logs after completion
cat data/prds/session_*/refinement.log
```

### Debugging
```bash
# Enable verbose and review all logs
python main.py --input my_prd.md --verbose
grep -i error data/prds/session_*/refinement.log
```

### Token Cost Estimation
```bash
# Sum all tokens across sessions
find data/prds -name "convergence_report.json" -exec jq '.token_usage | add' {} \;
```

## Log Privacy

**Sensitive data in logs:**
- Full PRD content (including proprietary information)
- LLM responses
- All issues and suggestions

**Recommendations:**
- Restrict access to `data/prds/` directory
- Do not commit logs to version control (covered by `.gitignore`)
- Consider encryption for production deployments
- Implement log rotation and retention policies

## Future Enhancements

1. **Structured logging** - JSON format for easier parsing
2. **Log rotation** - Automatic cleanup of old sessions
3. **Real-time streaming** - WebSocket streaming for UI
4. **Cost tracking** - Automatic cost calculation based on model pricing
5. **Alert system** - Notify on high token usage or errors
6. **Log compression** - Gzip old log files automatically
