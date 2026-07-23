"""Export format registry and orchestration."""

from __future__ import annotations

from ontolog.errors import ExportError
from ontolog.evidence.graph import EvidenceGraph
from ontolog.export.exporters.domain_json import DomainJsonExporter
from ontolog.export.exporters.graphml import GraphMlExporter
from ontolog.export.exporters.json_schema import JsonSchemaExporter
from ontolog.export.exporters.markdown_report import MarkdownReportExporter
from ontolog.export.exporters.mermaid import MermaidExporter
from ontolog.export.exporters.pydantic_gen import PydanticGenExporter
from ontolog.export.formats import ExportFormat
from ontolog.export.graph_exporters.evidence_graph_export import EvidenceGraphExporter
from ontolog.export.graph_exporters.full_bundle import FullBundleExporter
from ontolog.export.options import ExportOptions
from ontolog.models.domain import ProbabilisticDomainModel
from ontolog.models.finding import ProviderInput
from ontolog.types import Exporter, GraphExporter

_CORE_EXPORTERS: tuple[Exporter, ...] = (
    PydanticGenExporter(),
    JsonSchemaExporter(),
    MermaidExporter(),
    MarkdownReportExporter(),
    GraphMlExporter(),
    DomainJsonExporter(),
)

_GRAPH_EXPORTERS: tuple[GraphExporter, ...] = (
    EvidenceGraphExporter(),
    FullBundleExporter(),
)


def _build_exporter_map() -> dict[ExportFormat, Exporter]:
    return {exporter.format_name: exporter for exporter in _CORE_EXPORTERS}


def _build_graph_exporter_map() -> dict[ExportFormat, GraphExporter]:
    return {exporter.format_name: exporter for exporter in _GRAPH_EXPORTERS}


def registered_formats() -> tuple[ExportFormat, ...]:
    """Return export formats available with the current install."""
    return tuple(_build_exporter_map()) + tuple(_build_graph_exporter_map())


def graph_export_formats() -> frozenset[ExportFormat]:
    """Return formats that require graph-aware export."""
    return frozenset(_build_graph_exporter_map())


def parse_export_format(name: str) -> ExportFormat:
    """Parse a CLI or API format name into :class:`ExportFormat`."""
    try:
        return ExportFormat(name)
    except ValueError as exc:
        msg = f"unknown export format: {name}"
        raise ExportError(msg) from exc


def exporter_for(format_name: ExportFormat) -> Exporter:
    """Return the exporter for ``format_name``."""
    if format_name in graph_export_formats():
        msg = (
            f"{format_name} requires graph-aware export; use export_with_graph() or ontolog.infer()"
        )
        raise ExportError(msg)
    try:
        return _build_exporter_map()[format_name]
    except KeyError as exc:
        msg = f"unknown export format: {format_name}"
        raise ExportError(msg) from exc


def export_domain_model(
    model: ProbabilisticDomainModel,
    format_name: ExportFormat,
    *,
    options: ExportOptions | None = None,
) -> str:
    """Export ``model`` in the requested ``format_name``."""
    exporter = exporter_for(format_name)
    return exporter.export(model, options=options or ExportOptions())


def export_with_graph(
    model: ProbabilisticDomainModel,
    graph: EvidenceGraph,
    data: ProviderInput,
    format_name: ExportFormat,
    *,
    options: ExportOptions | None = None,
) -> str:
    """Export ``model`` with graph context in the requested ``format_name``."""
    try:
        exporter = _build_graph_exporter_map()[format_name]
    except KeyError as exc:
        msg = f"unknown graph export format: {format_name}"
        raise ExportError(msg) from exc
    return exporter.export(model, graph=graph, data=data, options=options or ExportOptions())
