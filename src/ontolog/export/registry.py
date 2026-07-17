"""Export format registry and orchestration."""

from __future__ import annotations

from ontolog.errors import ExportError
from ontolog.export._extras import graph_extra_enabled
from ontolog.export.formats import ExportFormat
from ontolog.export.graphml import GraphMlExporter, Neo4jCsvExporter
from ontolog.export.json_schema import JsonSchemaExporter
from ontolog.export.markdown_report import MarkdownReportExporter
from ontolog.export.mermaid import MermaidExporter
from ontolog.export.options import ExportOptions
from ontolog.export.pydantic_gen import PydanticGenExporter
from ontolog.models.domain import ProbabilisticDomainModel
from ontolog.types import Exporter

_CORE_EXPORTERS: tuple[Exporter, ...] = (
    PydanticGenExporter(),
    JsonSchemaExporter(),
    MermaidExporter(),
    MarkdownReportExporter(),
    GraphMlExporter(),
)


def _build_exporter_map() -> dict[ExportFormat, Exporter]:
    exporters: dict[ExportFormat, Exporter] = {
        exporter.format_name: exporter for exporter in _CORE_EXPORTERS
    }
    if graph_extra_enabled():
        exporters[ExportFormat.NEO4J_CSV] = Neo4jCsvExporter()
    return exporters


def registered_formats() -> tuple[ExportFormat, ...]:
    """Return export formats available with the current install."""
    return tuple(_build_exporter_map())


def parse_export_format(name: str) -> ExportFormat:
    """Parse a CLI or API format name into :class:`ExportFormat`."""
    try:
        return ExportFormat(name)
    except ValueError as exc:
        msg = f"unknown export format: {name}"
        raise ExportError(msg) from exc


def exporter_for(format_name: ExportFormat) -> Exporter:
    """Return the exporter for ``format_name``."""
    if format_name == ExportFormat.NEO4J_CSV and not graph_extra_enabled():
        msg = "neo4j-csv export requires the optional [graph] extra: pip install ontolog[graph]"
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
