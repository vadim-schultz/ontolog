"""Tests for TemporalProvider."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from ontolog.evidence.graph import EvidenceGraph
from ontolog.evidence.runner import run_providers
from ontolog.models.finding import ProviderInput
from ontolog.models.template import TemplateOccurrence
from ontolog.providers.temporal import TemporalProvider
from ontolog.templates.extractor import ExtractOptions, extract_templates

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_ordered_template_sequence_edge() -> None:
    templates = extract_templates(FIXTURES / "order_lifecycle.log", ExtractOptions())
    occurrences = tuple(
        TemplateOccurrence(
            template_id=template.id,
            timestamp=datetime(2024, 1, 15, 12, 0, index, tzinfo=UTC),
            message=template.examples[0] if template.examples else template.template,
            process="orderservice",
        )
        for index, template in enumerate(templates[:4], start=1)
    )
    graph = EvidenceGraph()
    run_providers(
        graph,
        ProviderInput(templates=tuple(templates), occurrences=occurrences),
        (TemporalProvider(),),
    )
    assert any(edge.label == "follows" for edge in graph.edges())


def test_same_template_not_self_loop() -> None:
    occurrences = (
        TemplateOccurrence(
            template_id="cluster_1",
            timestamp=datetime(2024, 1, 15, 12, 0, 1, tzinfo=UTC),
            message="repeat",
        ),
        TemplateOccurrence(
            template_id="cluster_1",
            timestamp=datetime(2024, 1, 15, 12, 0, 2, tzinfo=UTC),
            message="repeat",
        ),
    )
    graph = EvidenceGraph()
    run_providers(graph, ProviderInput(occurrences=occurrences), (TemporalProvider(),))
    assert not any(edge.label == "follows" for edge in graph.edges())


def test_score_reflects_sequence_length() -> None:
    short = (
        TemplateOccurrence(
            template_id="cluster_1",
            timestamp=datetime(2024, 1, 15, 12, 0, 1, tzinfo=UTC),
            message="a",
        ),
        TemplateOccurrence(
            template_id="cluster_2",
            timestamp=datetime(2024, 1, 15, 12, 0, 2, tzinfo=UTC),
            message="b",
        ),
    )
    long = short + tuple(
        TemplateOccurrence(
            template_id=f"cluster_{index}",
            timestamp=datetime(2024, 1, 15, 12, 0, index, tzinfo=UTC),
            message=f"msg-{index}",
        )
        for index in range(3, 8)
    )
    graph_short = EvidenceGraph()
    run_providers(graph_short, ProviderInput(occurrences=short), (TemporalProvider(),))
    graph_long = EvidenceGraph()
    run_providers(graph_long, ProviderInput(occurrences=long), (TemporalProvider(),))
    short_score = (
        next(edge for edge in graph_short.edges() if edge.label == "follows").evidence[0].score
    )
    long_score = max(
        edge.evidence[0].score for edge in graph_long.edges() if edge.label == "follows"
    )
    assert long_score > short_score
