"""Run inference passes over a populated evidence graph."""

from __future__ import annotations

from ontolog.config import ConfidenceThresholds
from ontolog.evidence.graph import EvidenceGraph
from ontolog.models.candidate import InferenceResult
from ontolog.models.finding import ProviderInput
from ontolog.types import InferencePass


def _merge_results(left: InferenceResult, right: InferenceResult) -> InferenceResult:
    return InferenceResult(
        entities=(*left.entities, *right.entities),
        events=(*left.events, *right.events),
        fields=(*left.fields, *right.fields),
        relationships=(*left.relationships, *right.relationships),
        state_machines=(*left.state_machines, *right.state_machines),
    )


def run_inference(
    graph: EvidenceGraph,
    data: ProviderInput,
    passes: tuple[InferencePass, ...],
    *,
    thresholds: ConfidenceThresholds,
) -> InferenceResult:
    """Run inference passes in order and merge their outputs."""
    result = InferenceResult()
    for inference_pass in passes:
        partial = inference_pass.infer(graph, data, thresholds=thresholds)
        result = _merge_results(result, partial)
    return result
