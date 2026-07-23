"""Tests for ontolog.evidence.graph."""

from __future__ import annotations

import json

import networkx as nx
import pytest

from ontolog.errors import InferenceError
from ontolog.evidence.graph import EvidenceGraph
from ontolog.models.evidence import Edge, Evidence, Node, NodeKind


@pytest.fixture
def sample_evidence() -> Evidence:
    return Evidence(
        source="regex",
        score=0.95,
        explanation="IPv4 pattern",
        samples=("192.168.1.1",),
    )


def graphs_equal(left: EvidenceGraph, right: EvidenceGraph) -> bool:
    return sorted(left.nodes(), key=lambda node: node.id) == sorted(
        right.nodes(), key=lambda node: node.id
    ) and sorted(
        left.edges(),
        key=lambda edge: (edge.source_id, edge.target_id),
    ) == sorted(right.edges(), key=lambda edge: (edge.source_id, edge.target_id))


def test_empty_graph_counts() -> None:
    graph = EvidenceGraph()
    assert graph.node_count() == 0
    assert graph.edge_count() == 0


def test_add_node_and_get() -> None:
    graph = EvidenceGraph()
    node = Node(id="entity:cb", kind=NodeKind.ENTITY, label="ControlBoard")
    graph.add_node(node)
    assert graph.get_node("entity:cb") == node


def test_add_edge_and_get() -> None:
    graph = EvidenceGraph()
    graph.add_node(Node(id="entity:a", kind=NodeKind.ENTITY, label="A"))
    graph.add_node(Node(id="entity:b", kind=NodeKind.ENTITY, label="B"))
    edge = Edge(source_id="entity:a", target_id="entity:b", label="owns")
    graph.add_edge(edge)
    assert graph.get_edge("entity:a", "entity:b") == edge


def test_add_node_duplicate_raises() -> None:
    graph = EvidenceGraph()
    node = Node(id="entity:cb", kind=NodeKind.ENTITY, label="ControlBoard")
    graph.add_node(node)
    with pytest.raises(InferenceError, match="duplicate node"):
        graph.add_node(node)


def test_add_edge_missing_endpoint_raises() -> None:
    graph = EvidenceGraph()
    edge = Edge(source_id="missing", target_id="also-missing")
    with pytest.raises(InferenceError, match="missing source node"):
        graph.add_edge(edge)


def test_nodes_and_edges_lists() -> None:
    graph = EvidenceGraph()
    node_a = Node(id="entity:a", kind=NodeKind.ENTITY, label="A")
    node_b = Node(id="entity:b", kind=NodeKind.ENTITY, label="B")
    edge = Edge(source_id="entity:a", target_id="entity:b")
    graph.add_node(node_a)
    graph.add_node(node_b)
    graph.add_edge(edge)
    assert set(graph.nodes()) == {node_a, node_b}
    assert graph.edges() == [edge]


def test_underlying_networkx_graph() -> None:
    graph = EvidenceGraph()
    graph.add_node(Node(id="entity:a", kind=NodeKind.ENTITY, label="A"))
    graph.add_node(Node(id="entity:b", kind=NodeKind.ENTITY, label="B"))
    graph.add_edge(Edge(source_id="entity:a", target_id="entity:b"))
    assert isinstance(graph.nx_graph, nx.DiGraph)
    assert graph.nx_graph.number_of_nodes() == 2
    assert graph.nx_graph.number_of_edges() == 1


def test_attach_evidence_to_node(sample_evidence: Evidence) -> None:
    graph = EvidenceGraph()
    graph.add_node(Node(id="entity:a", kind=NodeKind.ENTITY, label="A"))
    prior = Evidence(source="stats", score=0.5, explanation="count")
    graph.attach_evidence_to_node("entity:a", prior)
    graph.attach_evidence_to_node("entity:a", sample_evidence)
    node = graph.get_node("entity:a")
    assert node is not None
    assert node.evidence == (prior, sample_evidence)


def test_attach_evidence_to_node_missing_raises(sample_evidence: Evidence) -> None:
    graph = EvidenceGraph()
    with pytest.raises(InferenceError, match="unknown node"):
        graph.attach_evidence_to_node("missing", sample_evidence)


def test_attach_evidence_to_edge(sample_evidence: Evidence) -> None:
    graph = EvidenceGraph()
    graph.add_node(Node(id="entity:a", kind=NodeKind.ENTITY, label="A"))
    graph.add_node(Node(id="entity:b", kind=NodeKind.ENTITY, label="B"))
    graph.add_edge(Edge(source_id="entity:a", target_id="entity:b"))
    graph.attach_evidence_to_edge("entity:a", "entity:b", sample_evidence)
    edge = graph.get_edge("entity:a", "entity:b")
    assert edge is not None
    assert edge.evidence == (sample_evidence,)


def test_attach_evidence_to_edge_missing_raises(sample_evidence: Evidence) -> None:
    graph = EvidenceGraph()
    with pytest.raises(InferenceError, match="unknown edge"):
        graph.attach_evidence_to_edge("a", "b", sample_evidence)


def test_json_round_trip_empty() -> None:
    graph = EvidenceGraph()
    restored = EvidenceGraph.from_json(graph.to_json())
    assert restored.node_count() == 0
    assert restored.edge_count() == 0


def test_json_round_trip_populated(sample_evidence: Evidence) -> None:
    graph = EvidenceGraph()
    node_a = Node(
        id="entity:a",
        kind=NodeKind.ENTITY,
        label="A",
        evidence=(sample_evidence,),
    )
    node_b = Node(id="entity:b", kind=NodeKind.ENTITY, label="B")
    edge = Edge(source_id="entity:a", target_id="entity:b", evidence=(sample_evidence,))
    graph.add_node(node_a)
    graph.add_node(node_b)
    graph.add_edge(edge)

    restored = EvidenceGraph.from_json(graph.to_json())
    assert graphs_equal(graph, restored)


def test_json_round_trip_preserves_evidence_order() -> None:
    graph = EvidenceGraph()
    graph.add_node(Node(id="entity:a", kind=NodeKind.ENTITY, label="A"))
    first = Evidence(source="a", score=0.1, explanation="first")
    second = Evidence(source="b", score=0.2, explanation="second")
    graph.attach_evidence_to_node("entity:a", first)
    graph.attach_evidence_to_node("entity:a", second)

    restored = EvidenceGraph.from_json(graph.to_json())
    node = restored.get_node("entity:a")
    assert node is not None
    assert node.evidence == (first, second)


def test_to_payload_matches_to_json_body() -> None:
    graph = EvidenceGraph()
    graph.add_node(Node(id="entity:a", kind=NodeKind.ENTITY, label="A"))

    assert json.loads(graph.to_json()) == graph.to_payload()
