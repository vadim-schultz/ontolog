"""Tests for GraphML and Neo4j CSV export."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from helpers import aggregate_fixture
from ontolog.config import ConfidenceThresholds, OntologConfig
from ontolog.errors import ExportError
from ontolog.export._extras import enable_graph_extra, graph_extra_enabled
from ontolog.export.formats import ExportFormat
from ontolog.export.registry import export_domain_model, exporter_for

EXPORT_CONFIG = OntologConfig(confidence=ConfidenceThresholds(export=0.6))


@pytest.fixture(autouse=True)
def _enable_graph_extra() -> None:
    enable_graph_extra()


def test_graphml_well_formed_xml(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    output = export_domain_model(model, ExportFormat.GRAPHML)
    ET.fromstring(output)


def test_graphml_node_count(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    output = export_domain_model(model, ExportFormat.GRAPHML)
    root = ET.fromstring(output)
    namespace = {"g": "http://graphml.graphdrawing.org/xmlns"}
    nodes = root.findall(".//g:node", namespace)
    assert len(nodes) >= 3


def test_graphml_edges_from_relationships(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    output = export_domain_model(model, ExportFormat.GRAPHML)
    assert "entity:Controlboard" in output
    assert "entity:Interface" in output


def test_neo4j_csv_nodes_and_rels(tmp_path: Path) -> None:
    model = aggregate_fixture("controlboard.log", tmp_path, config=EXPORT_CONFIG)
    output = export_domain_model(model, ExportFormat.NEO4J_CSV)
    nodes_csv, relationships_csv = output.split("---\n", maxsplit=1)
    assert nodes_csv.startswith("id:ID,name,:LABEL,confidence")
    assert relationships_csv.startswith(":START_ID,:END_ID,:TYPE,confidence")
    assert "entity:Controlboard" in nodes_csv
    assert "OWNS" in relationships_csv


def test_neo4j_csv_requires_graph_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("ontolog.export._extras._GRAPH_EXTRA_STATE", {"enabled": False})
    assert not graph_extra_enabled()
    with pytest.raises(ExportError, match="graph"):
        exporter_for(ExportFormat.NEO4J_CSV)
