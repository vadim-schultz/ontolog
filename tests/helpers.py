"""Shared test helpers for fixture pipelines."""

from __future__ import annotations

from pathlib import Path

from ontolog.config import OntologConfig, default_config
from ontolog.evidence import load_evidence_graph
from ontolog.evidence.graph import EvidenceGraph
from ontolog.export import ExportFormat, ExportOptions, export_domain_model
from ontolog.inference import aggregate_inference_result, build_inference_result
from ontolog.models.candidate import InferenceResult
from ontolog.models.domain import ProbabilisticDomainModel
from ontolog.models.finding import ProviderInput
from ontolog.storage import SqliteTemplateStore
from ontolog.templates import ExtractOptions, extract_templates

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def extract_fixture_to_store(
    fixture_name: str,
    store_path: Path,
    *,
    config: OntologConfig | None = None,
) -> None:
    """Extract ``fixture_name`` from ``tests/fixtures`` into a SQLite store."""
    del config
    extract_templates(
        FIXTURES / fixture_name,
        ExtractOptions(),
        store=SqliteTemplateStore(store_path),
    )


def load_fixture_graph(
    fixture_name: str,
    tmp_path: Path,
    *,
    config: OntologConfig | None = None,
) -> tuple[EvidenceGraph, ProviderInput]:
    """Return a populated evidence graph and provider input for a fixture."""
    config = config or default_config()
    store_path = tmp_path / "ontolog.db"
    extract_fixture_to_store(fixture_name, store_path)
    store = SqliteTemplateStore(store_path)
    try:
        templates = store.list_templates()
        occurrences = store.list_occurrences()
        data = ProviderInput(templates=tuple(templates), occurrences=tuple(occurrences))
    finally:
        store.close()
    graph = load_evidence_graph(store_path, config=config)
    return graph, data


def infer_fixture(
    fixture_name: str,
    tmp_path: Path,
    *,
    config: OntologConfig | None = None,
) -> InferenceResult:
    """Run the full provider + inference pipeline for a fixture."""
    config = config or default_config()
    store_path = tmp_path / "ontolog.db"
    extract_fixture_to_store(fixture_name, store_path)
    return build_inference_result(store_path, config=config)


def aggregate_fixture(
    fixture_name: str,
    tmp_path: Path,
    *,
    config: OntologConfig | None = None,
) -> ProbabilisticDomainModel:
    """Run the full pipeline and aggregate into a domain model."""
    config = config or default_config()
    result = infer_fixture(fixture_name, tmp_path, config=config)
    return aggregate_inference_result(
        result,
        weights=config.source_weights,
        thresholds=config.confidence,
    )


def export_fixture(
    fixture_name: str,
    tmp_path: Path,
    format: ExportFormat,
    *,
    config: OntologConfig | None = None,
    options: ExportOptions | None = None,
) -> str:
    """Aggregate a fixture and export it in the requested format."""
    model = aggregate_fixture(fixture_name, tmp_path, config=config)
    return export_domain_model(model, format, options=options or ExportOptions())
