"""Run evidence providers against a graph."""

from __future__ import annotations

from ontolog.evidence.graph import EvidenceGraph
from ontolog.models.evidence import Edge, Evidence, Node, NodeKind
from ontolog.models.finding import EvidenceFinding, ProviderInput
from ontolog.types import EvidenceProvider


def _placeholder_node(node_id: str) -> Node:
    if node_id.startswith("template:"):
        label = node_id.removeprefix("template:")
        return Node(id=node_id, kind=NodeKind.EVENT, label=label)
    if node_id.startswith("field:"):
        label = node_id.rsplit(":", maxsplit=1)[-1]
        return Node(id=node_id, kind=NodeKind.FIELD, label=label)
    return Node(id=node_id, kind=NodeKind.ENTITY, label=node_id.split(":", maxsplit=1)[-1])


def _ensure_node(graph: EvidenceGraph, node_id: str) -> None:
    if graph.get_node(node_id) is None:
        graph.add_node(_placeholder_node(node_id))


def _ensure_edge_endpoints(graph: EvidenceGraph, edge: Edge) -> None:
    _ensure_node(graph, edge.source_id)
    _ensure_node(graph, edge.target_id)


def _upsert_node(graph: EvidenceGraph, node: Node, evidence: Evidence) -> None:
    if graph.get_node(node.id) is None:
        graph.add_node(node)
        return
    graph.attach_evidence_to_node(node.id, evidence)


def _upsert_edge(
    graph: EvidenceGraph,
    edge: Edge,
    evidence: Evidence,
    *,
    attach_if_duplicate: bool,
) -> None:
    _ensure_edge_endpoints(graph, edge)
    if graph.get_edge(edge.source_id, edge.target_id) is None:
        graph.add_edge(edge)
        return
    if attach_if_duplicate:
        graph.attach_evidence_to_edge(edge.source_id, edge.target_id, evidence)


def _apply_finding(graph: EvidenceGraph, finding: EvidenceFinding) -> None:
    if finding.node is not None:
        _upsert_node(graph, finding.node, finding.evidence)

    if finding.edge is not None:
        _upsert_edge(
            graph,
            finding.edge,
            finding.evidence,
            attach_if_duplicate=finding.node is None,
        )
        return

    if finding.attach_to_node_id is not None:
        graph.attach_evidence_to_node(finding.attach_to_node_id, finding.evidence)
        return

    if finding.attach_to_edge is not None:
        source_id, target_id = finding.attach_to_edge
        graph.attach_evidence_to_edge(source_id, target_id, finding.evidence)


def run_providers(
    graph: EvidenceGraph,
    data: ProviderInput,
    providers: tuple[EvidenceProvider, ...],
) -> None:
    """Run providers in order and apply their findings to the graph."""
    for provider in providers:
        for finding in provider.analyze(graph, data):
            _apply_finding(graph, finding)
