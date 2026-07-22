"""High-level pipeline entry points."""

from __future__ import annotations

from pathlib import Path

from ontolog.config import OntologConfig, default_config
from ontolog.inference import build_domain_model_from_store
from ontolog.ingestion.formats import LogFormat
from ontolog.models.domain import ProbabilisticDomainModel
from ontolog.storage import SqliteTemplateStore
from ontolog.templates import ExtractOptions, extract_templates

_SHARED_MEMORY_URI = "file:ontolog_infer?mode=memory&cache=shared"


def _normalize_store_path(store_path: Path | str) -> Path | str:
    if store_path == ":memory:":
        return _SHARED_MEMORY_URI
    return store_path


def _prepare_store(store_path: Path | str, *, fresh: bool) -> Path | str:
    normalized = _normalize_store_path(store_path)
    if not fresh or normalized == _SHARED_MEMORY_URI:
        return normalized
    path = Path(store_path)
    if path.exists():
        path.unlink()
    return normalized


def infer(
    source: Path | str,
    store_path: Path | str = "ontolog.db",
    *,
    config: OntologConfig | None = None,
    format: LogFormat = LogFormat.AUTO,
    fresh: bool = True,
) -> ProbabilisticDomainModel:
    """Infer a domain model from a log source through the full pipeline."""
    config = config or default_config()
    resolved_store = _prepare_store(store_path, fresh=fresh)

    with SqliteTemplateStore(resolved_store) as store:
        extract_templates(
            source,
            ExtractOptions(format=format),
            config=config,
            store=store,
        )
        return build_domain_model_from_store(store, config=config)
