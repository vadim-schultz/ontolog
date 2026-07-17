"""Tests for ProcessProvider."""

from __future__ import annotations

from pathlib import Path

from ontolog.evidence.graph import EvidenceGraph
from ontolog.evidence.runner import run_providers
from ontolog.models.finding import ProviderInput
from ontolog.models.template import TemplateOccurrence
from ontolog.providers.process import ProcessProvider
from ontolog.templates.extractor import ExtractOptions, extract_templates

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_repeated_subsequence_detected() -> None:
    templates = extract_templates(FIXTURES / "controlboard.log", ExtractOptions())
    template_ids = [template.id for template in templates[:3]]
    sequence = template_ids * 3
    occurrences = tuple(
        TemplateOccurrence(template_id=template_id, message="msg", process="controlboard")
        for template_id in sequence
    )
    graph = EvidenceGraph()
    run_providers(
        graph,
        ProviderInput(templates=tuple(templates), occurrences=occurrences),
        (ProcessProvider(),),
    )
    assert any(edge.label == "repeats_in_process" for edge in graph.edges())


def test_activity_graph_edge() -> None:
    occurrences = tuple(
        TemplateOccurrence(template_id=f"cluster_{index % 3 + 1}", message="msg")
        for index in range(9)
    )
    graph = EvidenceGraph()
    run_providers(graph, ProviderInput(occurrences=occurrences), (ProcessProvider(),))
    edge = next(edge for edge in graph.edges() if edge.label == "repeats_in_process")
    assert edge.source_id.startswith("template:")
    assert edge.target_id.startswith("template:")


def test_min_support_threshold() -> None:
    occurrences = tuple(
        TemplateOccurrence(template_id=f"cluster_{index + 1}", message="msg") for index in range(3)
    )
    graph = EvidenceGraph()
    run_providers(graph, ProviderInput(occurrences=occurrences), (ProcessProvider(min_support=2),))
    assert not any(edge.label == "repeats_in_process" for edge in graph.edges())
