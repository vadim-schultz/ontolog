"""Build inference results from stored templates."""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class InferenceContext:
    """Evidence graph and provider input retained through inference."""

    graph: EvidenceGraph
    data: ProviderInput
    result: InferenceResult


def build_inference_result(
    store_path: Path | str,
    *,
    config: OntologConfig,
) -> InferenceResult:
    """Load templates, run providers, then run inference passes."""
    store = SqliteTemplateStore(store_path)
    try:
        return build_inference_result_from_store(store, config=config)
    finally:
        store.close()


def build_inference_context_from_store(
    store: SqliteTemplateStore,
    *,
    config: OntologConfig,
) -> InferenceContext:
    """Run providers and inference passes using an open template store."""
    templates = store.list_templates()
    occurrences = store.list_occurrences()
    data = ProviderInput(templates=tuple(templates), occurrences=tuple(occurrences))
    graph = EvidenceGraph()
    run_providers(graph, data, provider_registry(config.providers))
    result = run_inference(
        graph,
        data,
        inference_registry(config.inference),
        thresholds=config.confidence,
    )
    return InferenceContext(graph=graph, data=data, result=result)


def build_inference_result_from_store(
    store: SqliteTemplateStore,
    *,
    config: OntologConfig,
) -> InferenceResult:
    """Run providers and inference passes using an open template store."""
    return build_inference_context_from_store(store, config=config).result


def build_domain_model(
    store_path: Path | str,
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


def build_domain_model_with_graph_from_store(
    store: SqliteTemplateStore,
    *,
    config: OntologConfig,
) -> tuple[ProbabilisticDomainModel, InferenceContext]:
    """Aggregate candidates and retain the evidence graph from an open store."""
    context = build_inference_context_from_store(store, config=config)
    model = aggregate_inference_result(
        context.result,
        weights=config.source_weights,
        thresholds=config.confidence,
    )
    return model, context


def build_domain_model_from_store(
    store: SqliteTemplateStore,
    *,
    config: OntologConfig,
) -> ProbabilisticDomainModel:
    """Aggregate candidates from an open template store into a domain model."""
    model, _context = build_domain_model_with_graph_from_store(store, config=config)
    return model
