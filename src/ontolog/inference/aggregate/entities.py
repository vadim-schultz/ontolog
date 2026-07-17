"""Aggregate entity candidates into domain entities."""

from __future__ import annotations

from ontolog.config import ConfidenceThresholds, EvidenceSourceWeights
from ontolog.inference.aggregate._grouping import aggregate_ranked_groups
from ontolog.models.candidate import EntityCandidate
from ontolog.models.domain import Alternative, Entity


def _entity_from_primary(
    slug: str,
    primary: EntityCandidate,
    confidence: float,
    alternatives: tuple[Alternative, ...],
    export_eligible: bool,
) -> Entity:
    """Map the winning entity candidate to a domain entity."""
    return Entity(
        name=primary.name,
        slug=slug,
        confidence=confidence,
        evidence=primary.evidence,
        alternatives=alternatives,
        export_eligible=export_eligible,
        graph_node_id=primary.graph_node_id,
    )


def aggregate_entities(
    candidates: tuple[EntityCandidate, ...],
    *,
    weights: EvidenceSourceWeights,
    thresholds: ConfidenceThresholds,
) -> tuple[Entity, ...]:
    """Merge entity candidates grouped by slug."""
    return aggregate_ranked_groups(
        candidates,
        key_fn=lambda candidate: candidate.slug,
        alternative_value_fn=lambda candidate: candidate.name,
        tie_key_fn=lambda candidate: (candidate.name, candidate.graph_node_id),
        build=_entity_from_primary,
        weights=weights,
        export_threshold=thresholds.export,
    )
