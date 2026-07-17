"""Aggregate event candidates into domain events."""

from __future__ import annotations

from ontolog.config import ConfidenceThresholds, EvidenceSourceWeights
from ontolog.inference.aggregate._grouping import aggregate_ranked_groups
from ontolog.models.candidate import EventCandidate
from ontolog.models.domain import Alternative, Event


def _event_from_primary(
    slug: str,
    primary: EventCandidate,
    confidence: float,
    alternatives: tuple[Alternative, ...],
    export_eligible: bool,
) -> Event:
    """Map the winning event candidate to a domain event."""
    return Event(
        name=primary.name,
        slug=slug,
        verbs=primary.verbs,
        confidence=confidence,
        evidence=primary.evidence,
        alternatives=alternatives,
        export_eligible=export_eligible,
        graph_node_id=primary.graph_node_id,
    )


def aggregate_events(
    candidates: tuple[EventCandidate, ...],
    *,
    weights: EvidenceSourceWeights,
    thresholds: ConfidenceThresholds,
) -> tuple[Event, ...]:
    """Merge event candidates grouped by slug."""
    return aggregate_ranked_groups(
        candidates,
        key_fn=lambda candidate: candidate.slug,
        alternative_value_fn=lambda candidate: candidate.name,
        tie_key_fn=lambda candidate: (candidate.name, candidate.graph_node_id),
        build=_event_from_primary,
        weights=weights,
        export_threshold=thresholds.export,
    )
