"""High-level pipeline entry points."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ontolog.config import OntologConfig, default_config
from ontolog.evidence.graph import EvidenceGraph
from ontolog.export.formats import ExportFormat
from ontolog.export.options import ExportOptions
from ontolog.export.registry import (
    export_domain_model,
    export_with_graph,
    graph_export_formats,
    parse_export_format,
)
from ontolog.inference.builder import build_domain_model_with_graph_from_store
from ontolog.ingestion.formats import LogFormat
from ontolog.models.domain import ProbabilisticDomainModel
from ontolog.models.finding import ProviderInput
from ontolog.storage import SqliteTemplateStore
from ontolog.templates.extractor import ExtractOptions, extract_templates

_SHARED_MEMORY_URI = "file:ontolog_infer?mode=memory&cache=shared"


@dataclass(frozen=True)
class InferOutput:
    """Result of the unified infer pipeline."""

    model: ProbabilisticDomainModel
    artifact: str
    graph: EvidenceGraph


def _normalize_store_path(store_path: Path | str) -> Path | str:
    if store_path == ":memory:":
        return _SHARED_MEMORY_URI
    return store_path


def _ephemeral_store() -> SqliteTemplateStore:
    return SqliteTemplateStore(_normalize_store_path(":memory:"))


def _resolve_extract_options(
    log_format: LogFormat,
    extract_options: ExtractOptions | None,
) -> ExtractOptions:
    if extract_options is None:
        return ExtractOptions(format=log_format)
    if extract_options.format is LogFormat.AUTO and log_format is not LogFormat.AUTO:
        return ExtractOptions(
            format=log_format,
            preprocessors=extract_options.preprocessors,
            skip_errors=extract_options.skip_errors,
            limit=extract_options.limit,
        )
    return extract_options


def _extract(
    source: Path | str,
    store: SqliteTemplateStore,
    *,
    config: OntologConfig,
    options: ExtractOptions,
) -> None:
    extract_templates(source, options, config=config, store=store)


def _export(
    model: ProbabilisticDomainModel,
    export_format: ExportFormat,
    *,
    options: ExportOptions,
    graph: EvidenceGraph,
    data: ProviderInput,
) -> str:
    if export_format in graph_export_formats():
        return export_with_graph(
            model,
            graph,
            data,
            export_format,
            options=options,
        )
    return export_domain_model(model, export_format, options=options)


def infer(
    source: Path | str,
    *,
    format: ExportFormat | str,
    config: OntologConfig | None = None,
    log_format: LogFormat = LogFormat.AUTO,
    export_options: ExportOptions | None = None,
    extract_options: ExtractOptions | None = None,
) -> InferOutput:
    """Infer a domain model from a log source and export it."""
    config = config or default_config()
    export_format = parse_export_format(format) if isinstance(format, str) else format
    resolved_export = export_options or ExportOptions()
    resolved_extract = _resolve_extract_options(log_format, extract_options)

    with _ephemeral_store() as store:
        _extract(source, store, config=config, options=resolved_extract)
        model, context = build_domain_model_with_graph_from_store(store, config=config)
        artifact = _export(
            model,
            export_format,
            options=resolved_export,
            graph=context.graph,
            data=context.data,
        )

    return InferOutput(model=model, artifact=artifact, graph=context.graph)
