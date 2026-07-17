"""Candidate aggregation into domain models."""

from __future__ import annotations

from ontolog.config import ConfidenceThresholds, EvidenceSourceWeights
from ontolog.inference.aggregate.entities import aggregate_entities
from ontolog.inference.aggregate.events import aggregate_events
from ontolog.inference.aggregate.fields import aggregate_fields
from ontolog.inference.aggregate.relationships import aggregate_relationships
from ontolog.inference.aggregate.states import aggregate_state_machines
from ontolog.models.candidate import InferenceResult
from ontolog.models.domain import ProbabilisticDomainModel


def aggregate_inference_result(
    result: InferenceResult,
    *,
    weights: EvidenceSourceWeights,
    thresholds: ConfidenceThresholds,
) -> ProbabilisticDomainModel:
    """Merge inference candidates into a canonical domain model."""
    return ProbabilisticDomainModel(
        entities=aggregate_entities(result.entities, weights=weights, thresholds=thresholds),
        events=aggregate_events(result.events, weights=weights, thresholds=thresholds),
        fields=aggregate_fields(result.fields, weights=weights, thresholds=thresholds),
        relationships=aggregate_relationships(
            result.relationships,
            weights=weights,
            thresholds=thresholds,
        ),
        state_machines=aggregate_state_machines(
            result.state_machines,
            weights=weights,
            thresholds=thresholds,
        ),
    )
