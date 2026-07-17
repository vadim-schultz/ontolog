"""Build inference results from stored templates."""

from __future__ import annotations

from pathlib import Path

from ontolog.config import OntologConfig
from ontolog.evidence.graph import EvidenceGraph
from ontolog.evidence.runner import run_providers
from ontolog.inference.aggregate import aggregate_inference_result
from ontolog.inference.base import inference_registry
from ontolog.inference.runner import run_inference
from ontolog.models.candidate import InferenceResult
from ontolog.models.domain import ProbabilisticDomainModel
from ontolog.models.finding import ProviderInput
from ontolog.providers import provider_registry
from ontolog.storage import SqliteTemplateStore


def build_inference_result(
    store_path: Path,
    *,
    config: OntologConfig,
) -> InferenceResult:
    """Load templates, run providers, then run inference passes."""
    store = SqliteTemplateStore(store_path)
    try:
        templates = store.list_templates()
        occurrences = store.list_occurrences()
        data = ProviderInput(templates=tuple(templates), occurrences=tuple(occurrences))
        graph = EvidenceGraph()
        run_providers(graph, data, provider_registry(config.providers))
        return run_inference(
            graph,
            data,
            inference_registry(config.inference),
            thresholds=config.confidence,
        )
    finally:
        store.close()


def build_domain_model(
    store_path: Path,
    *,
    config: OntologConfig,
) -> ProbabilisticDomainModel:
    """Run the full pipeline and aggregate candidates into a domain model."""
    result = build_inference_result(store_path, config=config)
    return aggregate_inference_result(
        result,
        weights=config.source_weights,
        thresholds=config.confidence,
    )
