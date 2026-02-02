"""
Plugin types for ai_orchestrator.

These are lightweight, dependency-free reference types used across plugin interfaces.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, MutableMapping, Optional, Sequence, Union


JsonPrimitive = Union[str, int, float, bool, None]
JsonValue = Union[JsonPrimitive, Sequence["JsonValue"], Mapping[str, "JsonValue"]]

Role = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """A message in a chat conversation."""
    role: Role
    content: str
    name: Optional[str] = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ModelUsage:
    """Token usage and cost information from a model call."""
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    input_cost_usd: Optional[float] = None
    output_cost_usd: Optional[float] = None


@dataclass(frozen=True, slots=True)
class ModelResponse:
    """Response from a model provider."""
    text: str
    model: Optional[str] = None
    usage: Optional[ModelUsage] = None
    raw: Optional[Any] = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    """A chunk of a document for indexing/retrieval."""
    chunk_id: str
    text: str
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """A retrieved chunk with relevance score."""
    chunk: DocumentChunk
    score: float
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MemoryItem:
    """An item stored in long-term memory."""
    key: str
    value: MutableMapping[str, JsonValue]
    created_at_iso: str
    updated_at_iso: str
    score: Optional[float] = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)
