"""Tests for ontolog.evidence.loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from ontolog.config import ProviderConfig, ProviderKind, default_config
from ontolog.errors import StorageError
from ontolog.evidence import load_evidence_graph
from ontolog.models.template import Template, TemplateOccurrence, TemplateParameter
from ontolog.storage import SqliteTemplateStore
from ontolog.templates.extractor import ExtractOptions, extract_templates

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_load_empty_store_returns_empty_graph(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    graph = load_evidence_graph(store_path, config=default_config())
    assert graph.node_count() == 0
    assert graph.edge_count() == 0


def test_load_opens_store_at_path(tmp_path: Path) -> None:
    store_path = tmp_path / "nested" / "ontolog.db"
    store_path.parent.mkdir()
    graph = load_evidence_graph(store_path, config=default_config())
    assert graph.node_count() == 0


def test_load_missing_parent_raises_storage_error(tmp_path: Path) -> None:
    store_path = tmp_path / "nested" / "ontolog.db"
    with pytest.raises(StorageError):
        load_evidence_graph(store_path, config=default_config())


def test_load_invalid_path_raises_storage_error(tmp_path: Path) -> None:
    invalid_path = tmp_path / "not-a-database"
    invalid_path.mkdir()
    with pytest.raises(StorageError):
        load_evidence_graph(invalid_path, config=default_config())


def test_load_after_templates_populates_graph(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    extract_templates(
        FIXTURES / "controlboard.log",
        ExtractOptions(),
        store=SqliteTemplateStore(store_path),
    )
    graph = load_evidence_graph(store_path, config=default_config())
    assert graph.node_count() > 0


def test_load_respects_provider_config(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    store = SqliteTemplateStore(store_path)
    try:
        store.upsert_template(Template(id="cluster_1", template="PacketSent destination=<IP>"))
        store.insert_occurrence(
            TemplateOccurrence(
                template_id="cluster_1",
                message="PacketSent destination=192.168.1.1",
                parameters=(TemplateParameter(name="destination", value="192.168.1.1"),),
                process="controlboard",
            )
        )
    finally:
        store.close()

    all_enabled = load_evidence_graph(store_path, config=default_config())
    disabled = load_evidence_graph(
        store_path,
        config=default_config().model_copy(
            update={"providers": ProviderConfig(enabled=frozenset({ProviderKind.NAMESPACE}))}
        ),
    )
    assert all_enabled.node_count() > disabled.node_count()
