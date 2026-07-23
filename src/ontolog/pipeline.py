"""High-level pipeline entry points."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ontolog.config import OntologConfig, default_config
from ontolog.export.formats import ExportFormat
from ontolog.export.graphml import Neo4jCsvBundle
from ontolog.export.options import ExportOptions
from ontolog.export.registry import export_domain_model, parse_export_format
from ontolog.inference.builder import build_domain_model_from_store
from ontolog.ingestion.formats import LogFormat
from ontolog.models.domain import ProbabilisticDomainModel
from ontolog.storage import SqliteTemplateStore
from ontolog.templates.extractor import ExtractOptions, extract_templates

_SHARED_MEMORY_URI = "file:ontolog_infer?mode=memory&cache=shared"


@dataclass(frozen=True)
class InferOutput:
    """Result of the unified infer pipeline."""

    model: ProbabilisticDomainModel
    artifact: str


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


def _infer_model(
    store: SqliteTemplateStore,
    *,
    config: OntologConfig,
) -> ProbabilisticDomainModel:
    return build_domain_model_from_store(store, config=config)


def _export(
    model: ProbabilisticDomainModel,
    export_format: ExportFormat,
    *,
    options: ExportOptions,
) -> str:
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
        model = _infer_model(store, config=config)
        artifact = _export(model, export_format, options=resolved_export)

    return InferOutput(model=model, artifact=artifact)


def write_neo4j_csv_files(
    bundle: Neo4jCsvBundle,
    output_dir: Path,
) -> tuple[Path, Path]:
    """Write Neo4j CSV payloads to ``output_dir``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    nodes_path = output_dir / "nodes.csv"
    relationships_path = output_dir / "relationships.csv"
    nodes_path.write_text(bundle.nodes, encoding="utf-8")
    relationships_path.write_text(bundle.relationships, encoding="utf-8")
    return nodes_path, relationships_path
