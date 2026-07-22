"""Inference candidate models."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from ontolog.models.evidence import Evidence


class EntityCandidate(BaseModel):
    """A promoted domain entity."""

    model_config = ConfigDict(frozen=True)

    name: str
    slug: str
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    graph_node_id: str
    evidence: tuple[Evidence, ...] = ()


class EventCandidate(BaseModel):
    """A promoted domain event."""

    model_config = ConfigDict(frozen=True)

    name: str
    slug: str
    verbs: frozenset[str] = Field(default_factory=frozenset)
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    graph_node_id: str
    evidence: tuple[Evidence, ...] = ()


class FieldCandidate(BaseModel):
    """A promoted field with inferred type."""

    model_config = ConfigDict(frozen=True)

    name: str
    type_name: str
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    graph_node_id: str
    entity_slug: str | None = None
    evidence: tuple[Evidence, ...] = ()


class RelationshipCandidate(BaseModel):
    """A suggested relationship between domain concepts."""

    model_config = ConfigDict(frozen=True)

    kind: str
    source_name: str
    target_name: str
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    evidence: tuple[Evidence, ...] = ()


class StateTransition(BaseModel):
    """One observed state transition."""

    model_config = ConfigDict(frozen=True)

    from_state: str
    to_state: str
    count: int = Field(ge=1)
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]


class StateMachineCandidate(BaseModel):
    """A inferred lifecycle or process state machine."""

    model_config = ConfigDict(frozen=True)

    name: str
    states: tuple[str, ...]
    transitions: tuple[StateTransition, ...]
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    evidence: tuple[Evidence, ...] = ()


class InferenceResult(BaseModel):
    """Bundled output from all inference passes."""

    model_config = ConfigDict(frozen=True)

    entities: tuple[EntityCandidate, ...] = ()
    events: tuple[EventCandidate, ...] = ()
    fields: tuple[FieldCandidate, ...] = ()
    relationships: tuple[RelationshipCandidate, ...] = ()
    state_machines: tuple[StateMachineCandidate, ...] = ()
