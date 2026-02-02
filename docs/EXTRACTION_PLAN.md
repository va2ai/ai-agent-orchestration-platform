# AI Orchestrator Core Extraction Plan

This document captures the extraction plan for turning the current repository layout into a
reusable Python library (`ai_orchestrator`) plus app/client implementations.

## Goals

- Preserve existing folder semantics while making the core runtime importable.
- Define a single public API entrypoint for external consumers.
- Isolate convergence logic as a reusable module.

## Proposed Package Layout

Promote the following folders into `src/ai_orchestrator/`:

- `orchestration/` → `src/ai_orchestrator/orchestration/`
- `agents/` → `src/ai_orchestrator/agents/`
- `models/` → `src/ai_orchestrator/models/`
- `prompts/` → `src/ai_orchestrator/prompts/`
- `storage/` → `src/ai_orchestrator/storage/`
- `utils/` → `src/ai_orchestrator/utils/`

Keep these as apps/clients (not library modules):

- `api/` (reference API server)
- `ui/` (reference client/dashboard)

## Public API Contract

Expose a single primary entrypoint to run a full roundtable loop, for example:

- `run_roundtable(...)`
- `generate_roundtable(...)`
- `refine_document(...)`

All other modules remain internal to the library and are not part of the public contract.

## Convergence Module

Create a dedicated `convergence.py` module containing stop conditions such as:

- No high-severity issues remaining.
- Maximum iterations reached.
- Document delta below a configured threshold.

This module should be reusable across loops such as PRD refinement, code review, and other
reflection workflows.

## Suggested Next Steps

1. Add `pyproject.toml` with `src/` layout and packaging metadata.
2. Move core directories into `src/ai_orchestrator/`.
3. Implement `ai_orchestrator.__init__` with the primary public entrypoint.
4. Extract convergence logic into `ai_orchestrator/convergence.py`.
5. Update README to document the new import path and library usage.
