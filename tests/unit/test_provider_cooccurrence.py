"""Tests for CoOccurrenceProvider."""

from __future__ import annotations

from pathlib import Path

from ontolog.evidence.graph import EvidenceGraph
from ontolog.evidence.runner import run_providers
from ontolog.models.finding import ProviderInput
from ontolog.models.template import TemplateOccurrence, TemplateParameter
from ontolog.providers import NamespaceProvider
from ontolog.providers.co_occurrence import CoOccurrenceProvider
from ontolog.providers.regex import RegexProvider
from ontolog.templates.extractor import ExtractOptions, extract_templates

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _build_order_graph() -> EvidenceGraph:
    templates = extract_templates(FIXTURES / "order_cooccurrence.log", ExtractOptions())
    occurrences = tuple(
        TemplateOccurrence(
            template_id=template.id,
            message=template.examples[0] if template.examples else template.template,
            parameters=(
                TemplateParameter(name="OrderID", value=f"ORD-00{index}"),
                TemplateParameter(name="CustomerID", value=f"CUST-4{index}"),
            ),
            process="orderservice",
        )
        for index, template in enumerate(templates[:4], start=1)
    )
    graph = EvidenceGraph()
    data = ProviderInput(templates=tuple(templates), occurrences=occurrences)
    run_providers(graph, data, (NamespaceProvider(), RegexProvider(), CoOccurrenceProvider()))
    return graph


def test_co_occurring_params_create_relationship_edge() -> None:
    graph = _build_order_graph()
    edges = [edge for edge in graph.edges() if edge.label == "co_occurs"]
    assert edges


def test_relationship_score_increases_with_co_occurrence_count() -> None:
    few = TemplateOccurrence(
        template_id="cluster_1",
        message="OrderCreated OrderID=ORD-001 CustomerID=CUST-42",
        parameters=(
            TemplateParameter(name="OrderID", value="ORD-001"),
            TemplateParameter(name="CustomerID", value="CUST-42"),
        ),
        process="orderservice",
    )
    many = tuple(
        TemplateOccurrence(
            template_id="cluster_1",
            message="OrderCreated OrderID=ORD-001 CustomerID=CUST-42",
            parameters=(
                TemplateParameter(name="OrderID", value="ORD-001"),
                TemplateParameter(name="CustomerID", value="CUST-42"),
            ),
            process="orderservice",
        )
        for _ in range(10)
    )
    graph_few = EvidenceGraph()
    run_providers(
        graph_few,
        ProviderInput(occurrences=(few,)),
        (NamespaceProvider(), CoOccurrenceProvider()),
    )
    graph_many = EvidenceGraph()
    run_providers(
        graph_many,
        ProviderInput(occurrences=many),
        (NamespaceProvider(), CoOccurrenceProvider()),
    )
    few_score = (
        next(edge for edge in graph_few.edges() if edge.label == "co_occurs").evidence[0].score
    )
    many_score = (
        next(edge for edge in graph_many.edges() if edge.label == "co_occurs").evidence[0].score
    )
    assert many_score > few_score


def test_non_co_occurring_params_no_edge() -> None:
    left = TemplateOccurrence(
        template_id="cluster_1",
        message="a",
        parameters=(TemplateParameter(name="OrderID", value="ORD-001"),),
        process="orderservice",
    )
    right = TemplateOccurrence(
        template_id="cluster_2",
        message="b",
        parameters=(TemplateParameter(name="CustomerID", value="CUST-42"),),
        process="orderservice",
    )
    graph = EvidenceGraph()
    run_providers(
        graph,
        ProviderInput(occurrences=(left, right)),
        (NamespaceProvider(), CoOccurrenceProvider()),
    )
    assert not any(edge.label == "co_occurs" for edge in graph.edges())
