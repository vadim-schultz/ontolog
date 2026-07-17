"""Generate GraphML and Neo4j CSV from a domain model."""

from __future__ import annotations

import io
from dataclasses import dataclass

import networkx as nx

from ontolog.errors import ExportError
from ontolog.export._extras import graph_extra_enabled
from ontolog.export.formats import ExportFormat
from ontolog.export.options import ExportOptions
from ontolog.export.view import ExportView, export_view
from ontolog.models.domain import ProbabilisticDomainModel, Relationship


def _node_id(kind: str, name: str) -> str:
    return f"{kind}:{name}"


def _build_export_graph(view: ExportView) -> nx.DiGraph:
    graph = nx.DiGraph()
    for entity in view.entities:
        node = _node_id("entity", entity.name)
        graph.add_node(node, kind="entity", label=entity.name, confidence=entity.confidence)
    for event in view.events:
        node = _node_id("event", event.name)
        graph.add_node(node, kind="event", label=event.name, confidence=event.confidence)
    for field in view.fields:
        node = _node_id("field", field.name)
        graph.add_node(
            node,
            kind="field",
            label=field.name,
            type_name=field.type_name.value,
            confidence=field.type_name.confidence,
        )
    for relationship in view.relationships:
        _add_relationship_edge(graph, relationship)
    return graph


def _add_relationship_edge(graph: nx.DiGraph, relationship: Relationship) -> None:
    source = _node_id("entity", relationship.source_name)
    target = _node_id("entity", relationship.target_name)
    if source not in graph:
        graph.add_node(source, kind="entity", label=relationship.source_name)
    if target not in graph:
        graph.add_node(target, kind="entity", label=relationship.target_name)
    graph.add_edge(
        source,
        target,
        kind=relationship.kind,
        confidence=relationship.confidence,
    )


def _graphml_string(graph: nx.DiGraph) -> str:
    buffer = io.StringIO()
    for line in nx.generate_graphml(graph):
        buffer.write(line)
    return buffer.getvalue()


@dataclass(frozen=True)
class Neo4jCsvBundle:
    """Neo4j bulk-import CSV payloads."""

    nodes: str
    relationships: str


def _neo4j_csv_bundle(graph: nx.DiGraph) -> Neo4jCsvBundle:
    node_lines = ["id:ID,name,:LABEL,confidence"]
    for node_id, attrs in graph.nodes(data=True):
        label = str(attrs.get("kind", "Node")).title()
        confidence = attrs.get("confidence", "")
        name = attrs.get("label", node_id)
        node_lines.append(f"{node_id},{name},{label},{confidence}")
    rel_lines = [":START_ID,:END_ID,:TYPE,confidence"]
    for source, target, attrs in graph.edges(data=True):
        rel_type = str(attrs.get("kind", "RELATED_TO")).upper()
        confidence = attrs.get("confidence", "")
        rel_lines.append(f"{source},{target},{rel_type},{confidence}")
    nodes = "\n".join(node_lines) + "\n"
    relationships = "\n".join(rel_lines) + "\n"
    return Neo4jCsvBundle(nodes=nodes, relationships=relationships)


class GraphMlExporter:
    """Export a domain model as GraphML."""

    @property
    def format_name(self) -> ExportFormat:
        """Return the exporter format identifier."""
        return ExportFormat.GRAPHML

    def export(
        self,
        model: ProbabilisticDomainModel,
        *,
        options: ExportOptions,
    ) -> str:
        """Return GraphML XML for ``model``."""
        view = export_view(model, options)
        graph = _build_export_graph(view)
        return _graphml_string(graph)


class Neo4jCsvExporter:
    """Export a domain model as Neo4j bulk-import CSV."""

    @property
    def format_name(self) -> ExportFormat:
        """Return the exporter format identifier."""
        return ExportFormat.NEO4J_CSV

    def export(
        self,
        model: ProbabilisticDomainModel,
        *,
        options: ExportOptions,
    ) -> str:
        """Return Neo4j CSV payloads separated by ``---``."""
        view = export_view(model, options)
        graph = _build_export_graph(view)
        bundle = _neo4j_csv_bundle(graph)
        return f"{bundle.nodes}---\n{bundle.relationships}"


def export_neo4j_csv(
    model: ProbabilisticDomainModel,
    *,
    options: ExportOptions | None = None,
) -> Neo4jCsvBundle:
    """Return separate Neo4j CSV payloads for ``model``."""
    if not graph_extra_enabled():
        msg = "neo4j-csv export requires the optional [graph] extra: pip install ontolog[graph]"
        raise ExportError(msg)
    view = export_view(model, options or ExportOptions())
    graph = _build_export_graph(view)
    return _neo4j_csv_bundle(graph)
