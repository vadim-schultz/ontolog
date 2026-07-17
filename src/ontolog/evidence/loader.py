"""Load evidence graphs from persistence."""

from __future__ import annotations

from pathlib import Path

from ontolog.config import OntologConfig, default_config
from ontolog.evidence.graph import EvidenceGraph
from ontolog.evidence.runner import run_providers
from ontolog.models.finding import ProviderInput
from ontolog.providers import provider_registry
from ontolog.storage import SqliteTemplateStore


def load_evidence_graph(store_path: Path, *, config: OntologConfig) -> EvidenceGraph:
    """Load templates and occurrences from the store and populate the evidence graph."""
    store = SqliteTemplateStore(store_path)
    try:
        templates = store.list_templates()
        occurrences = store.list_occurrences()
        graph = EvidenceGraph()
        providers = provider_registry(config.providers)
        run_providers(
            graph,
            ProviderInput(templates=tuple(templates), occurrences=tuple(occurrences)),
            providers,
        )
        return graph
    finally:
        store.close()


def load_default_evidence_graph(store_path: Path) -> EvidenceGraph:
    """Load the evidence graph using :func:`~ontolog.config.default_config`."""
    return load_evidence_graph(store_path, config=default_config())
