"""Provider input and output models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from ontolog.models.evidence import Edge, Evidence, Node
from ontolog.models.template import Template, TemplateOccurrence


class ProviderInput(BaseModel):
    """Templates and occurrences passed to evidence providers."""

    model_config = ConfigDict(frozen=True)

    templates: tuple[Template, ...] = ()
    occurrences: tuple[TemplateOccurrence, ...] = ()


class EvidenceFinding(BaseModel):
    """One graph mutation with attached evidence."""

    model_config = ConfigDict(frozen=True)

    evidence: Evidence
    node: Node | None = None
    edge: Edge | None = None
    attach_to_node_id: str | None = None
    attach_to_edge: tuple[str, str] | None = None
