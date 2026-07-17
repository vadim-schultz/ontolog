"""Tests for inference graph query helpers."""

from __future__ import annotations

from ontolog.evidence.graph import EvidenceGraph
from ontolog.inference.queries import (
    edges_with_label,
    entity_fields,
    field_type_name,
    max_evidence_score,
    nodes_by_kind,
)
from ontolog.models.evidence import Edge, Evidence, Node, NodeKind


def _sample_graph() -> EvidenceGraph:
    graph = EvidenceGraph()
    entity = Node(id="entity:controlboard", kind=NodeKind.ENTITY, label="Controlboard")
    field = Node(
        id="field:cluster_1:destination",
        kind=NodeKind.FIELD,
        label="destination",
        evidence=(Evidence(source="namespace", score=0.7, explanation="field"),),
    )
    type_node = Node(id="type:ipv4", kind=NodeKind.TYPE, label="ipv4")
    graph.add_node(entity)
    graph.add_node(field)
    graph.add_node(type_node)
    graph.add_edge(
        Edge(
            source_id="entity:controlboard",
            target_id="field:cluster_1:destination",
            label="has_field",
            evidence=(Evidence(source="namespace", score=0.7, explanation="link"),),
        )
    )
    graph.add_edge(
        Edge(
            source_id="field:cluster_1:destination",
            target_id="type:ipv4",
            label="has_type",
            evidence=(Evidence(source="regex", score=0.95, explanation="ipv4"),),
        )
    )
    return graph


def test_nodes_by_kind() -> None:
    graph = _sample_graph()
    fields = nodes_by_kind(graph, NodeKind.FIELD)
    assert len(fields) == 1
    assert fields[0].label == "destination"


def test_edges_with_label() -> None:
    graph = _sample_graph()
    edges = edges_with_label(graph, "has_type")
    assert len(edges) == 1


def test_field_type_name() -> None:
    graph = _sample_graph()
    assert field_type_name(graph, "field:cluster_1:destination") == "ipv4"


def test_entity_fields() -> None:
    graph = _sample_graph()
    assert entity_fields(graph, "entity:controlboard") == ("field:cluster_1:destination",)


def test_max_evidence_score_filtered() -> None:
    graph = _sample_graph()
    field = graph.get_node("field:cluster_1:destination")
    assert field is not None
    assert max_evidence_score(field, source="namespace") == 0.7
