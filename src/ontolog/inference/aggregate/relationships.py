"""Aggregate relationship candidates into domain relationships."""

from __future__ import annotations

from ontolog.config import ConfidenceThresholds, EvidenceSourceWeights
from ontolog.inference.aggregate._grouping import aggregate_ranked_groups
from ontolog.models.candidate import RelationshipCandidate
from ontolog.models.domain import Alternative, Relationship


def _relationship_key(candidate: RelationshipCandidate) -> tuple[str, str, str]:
    return (candidate.kind, candidate.source_name, candidate.target_name)


def _relationship_from_primary(
    _key: tuple[str, str, str],
    primary: RelationshipCandidate,
    confidence: float,
    alternatives: tuple[Alternative, ...],
    export_eligible: bool,
) -> Relationship:
    """Map the winning relationship candidate to a domain relationship."""
    return Relationship(
        kind=primary.kind,
        source_name=primary.source_name,
        target_name=primary.target_name,
        confidence=confidence,
        evidence=primary.evidence,
        alternatives=alternatives,
        export_eligible=export_eligible,
    )


def aggregate_relationships(
    candidates: tuple[RelationshipCandidate, ...],
    *,
    weights: EvidenceSourceWeights,
    thresholds: ConfidenceThresholds,
) -> tuple[Relationship, ...]:
    """Merge relationship candidates grouped by kind and endpoints."""
    return aggregate_ranked_groups(
        candidates,
        key_fn=_relationship_key,
        alternative_value_fn=lambda candidate: candidate.kind,
        tie_key_fn=_relationship_key,
        build=_relationship_from_primary,
        weights=weights,
        export_threshold=thresholds.export,
    )
