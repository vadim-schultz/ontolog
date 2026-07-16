"""Load evidence graphs from persistence."""

from __future__ import annotations

from pathlib import Path

from ontolog.evidence.graph import EvidenceGraph
from ontolog.storage import SqliteTemplateStore


def load_evidence_graph(store_path: Path) -> EvidenceGraph:
    """Load the evidence graph from the Ontolog SQLite store.

    Chapter 4 stub: validates the store opens and returns an empty in-memory graph.
    Graph persistence and provider population arrive in later chapters.
    """
    store = SqliteTemplateStore(store_path)
    try:
        store.list_templates()
        return EvidenceGraph()
    finally:
        store.close()
