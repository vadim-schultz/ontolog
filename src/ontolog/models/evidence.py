"""Evidence graph domain models."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class NodeKind(StrEnum):
    """Semantic category of a graph node."""

    ENTITY = "entity"
    FIELD = "field"
    EVENT = "event"
    TYPE = "type"
    STATE = "state"
    RELATIONSHIP = "relationship"


class Evidence(BaseModel):
    """One provenance-backed signal attached to a node or edge."""

    model_config = ConfigDict(frozen=True)

    source: str
    score: Annotated[float, Field(ge=0.0, le=1.0)]
    explanation: str
    samples: tuple[str, ...] = ()


class Node(BaseModel):
    """A node in the evidence graph."""

    model_config = ConfigDict(frozen=True)

    id: str
    kind: NodeKind
    label: str
    evidence: tuple[Evidence, ...] = ()


class Edge(BaseModel):
    """A directed edge in the evidence graph."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    target_id: str
    label: str | None = None
    evidence: tuple[Evidence, ...] = ()
