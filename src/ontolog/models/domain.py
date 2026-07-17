"""Probabilistic domain model types."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict
from pydantic import Field as PydanticField

from ontolog.models.evidence import Evidence

ConfidenceFloat = Annotated[float, PydanticField(ge=0.0, le=1.0)]


class Alternative(BaseModel):
    """A ranked alternative value for a probabilistic claim."""

    model_config = ConfigDict(frozen=True)

    value: str
    confidence: ConfidenceFloat
    evidence: tuple[Evidence, ...]


class ProbabilisticClaim(BaseModel):
    """One inferred value with confidence, provenance, and alternatives."""

    model_config = ConfigDict(frozen=True)

    value: str
    confidence: ConfidenceFloat
    evidence: tuple[Evidence, ...]
    alternatives: tuple[Alternative, ...] = ()
    export_eligible: bool


class Entity(BaseModel):
    """A merged domain entity."""

    model_config = ConfigDict(frozen=True)

    name: str
    slug: str
    confidence: ConfidenceFloat
    evidence: tuple[Evidence, ...]
    alternatives: tuple[Alternative, ...] = ()
    export_eligible: bool
    graph_node_id: str = ""


class Event(BaseModel):
    """A merged domain event."""

    model_config = ConfigDict(frozen=True)

    name: str
    slug: str
    verbs: frozenset[str] = PydanticField(default_factory=frozenset)
    confidence: ConfidenceFloat
    evidence: tuple[Evidence, ...]
    alternatives: tuple[Alternative, ...] = ()
    export_eligible: bool
    graph_node_id: str = ""


class Field(BaseModel):
    """A merged domain field with probabilistic type."""

    model_config = ConfigDict(frozen=True)

    name: str
    type_name: ProbabilisticClaim
    graph_node_id: str


class Relationship(BaseModel):
    """A merged relationship between domain concepts."""

    model_config = ConfigDict(frozen=True)

    kind: str
    source_name: str
    target_name: str
    confidence: ConfidenceFloat
    evidence: tuple[Evidence, ...]
    alternatives: tuple[Alternative, ...] = ()
    export_eligible: bool


class StateTransition(BaseModel):
    """One observed state transition in a merged state machine."""

    model_config = ConfigDict(frozen=True)

    from_state: str
    to_state: str
    count: int = PydanticField(ge=1)
    confidence: ConfidenceFloat


class StateMachine(BaseModel):
    """A merged lifecycle or process state machine."""

    model_config = ConfigDict(frozen=True)

    name: str
    states: tuple[str, ...]
    transitions: tuple[StateTransition, ...]
    confidence: ConfidenceFloat
    evidence: tuple[Evidence, ...]
    alternatives: tuple[Alternative, ...] = ()
    export_eligible: bool


class ProbabilisticDomainModel(BaseModel):
    """Canonical aggregated domain model with full provenance."""

    model_config = ConfigDict(frozen=True)

    schema_version: Literal["1"] = "1"
    entities: tuple[Entity, ...] = ()
    events: tuple[Event, ...] = ()
    fields: tuple[Field, ...] = ()
    relationships: tuple[Relationship, ...] = ()
    state_machines: tuple[StateMachine, ...] = ()
