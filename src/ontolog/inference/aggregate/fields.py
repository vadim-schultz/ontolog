"""Aggregate field candidates into domain fields."""

from __future__ import annotations

from ontolog.config import ConfidenceThresholds, EvidenceSourceWeights
from ontolog.inference.aggregate._grouping import aggregate_ranked_groups
from ontolog.models.candidate import FieldCandidate
from ontolog.models.domain import Alternative, Field, ProbabilisticClaim


def _field_from_primary(
    graph_node_id: str,
    primary: FieldCandidate,
    confidence: float,
    alternatives: tuple[Alternative, ...],
    export_eligible: bool,
) -> Field:
    """Map the winning field candidate to a domain field."""
    return Field(
        name=primary.name,
        graph_node_id=graph_node_id,
        entity_slug=primary.entity_slug,
        type_name=ProbabilisticClaim(
            value=primary.type_name,
            confidence=confidence,
            evidence=primary.evidence,
            alternatives=alternatives,
            export_eligible=export_eligible,
        ),
    )


def aggregate_fields(
    candidates: tuple[FieldCandidate, ...],
    *,
    weights: EvidenceSourceWeights,
    thresholds: ConfidenceThresholds,
) -> tuple[Field, ...]:
    """Merge field candidates grouped by graph node id."""
    return aggregate_ranked_groups(
        candidates,
        key_fn=lambda candidate: candidate.graph_node_id,
        alternative_value_fn=lambda candidate: candidate.type_name,
        tie_key_fn=lambda candidate: (candidate.type_name, candidate.name),
        build=_field_from_primary,
        weights=weights,
        export_threshold=thresholds.export,
    )
