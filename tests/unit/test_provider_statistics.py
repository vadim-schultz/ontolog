"""Tests for StatisticsProvider and scoring helpers."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from ontolog.evidence.graph import EvidenceGraph
from ontolog.evidence.runner import run_providers
from ontolog.evidence.scoring import reinforce_score
from ontolog.models.evidence import Node, NodeKind
from ontolog.models.finding import ProviderInput
from ontolog.models.template import TemplateOccurrence, TemplateParameter
from ontolog.providers.regex import RegexProvider
from ontolog.providers.statistics import StatisticsProvider


def _occurrences(values: list[str]) -> tuple[TemplateOccurrence, ...]:
    return tuple(
        TemplateOccurrence(
            template_id="cluster_1",
            message="msg",
            parameters=(TemplateParameter(name="destination", value=value),),
        )
        for value in values
    )


def test_frequency_increases_score() -> None:
    graph = EvidenceGraph()
    run_providers(
        graph, ProviderInput(occurrences=_occurrences(["192.168.1.1"])), (RegexProvider(),)
    )
    low = StatisticsProvider().analyze(
        graph, ProviderInput(occurrences=_occurrences(["192.168.1.1"]))
    )[0]

    graph_high = EvidenceGraph()
    run_providers(
        graph_high,
        ProviderInput(occurrences=_occurrences(["192.168.1.1"] * 20)),
        (RegexProvider(),),
    )
    high = StatisticsProvider().analyze(
        graph_high,
        ProviderInput(occurrences=_occurrences(["192.168.1.1"] * 20)),
    )[0]

    assert high.evidence.score > low.evidence.score


def test_cardinality_reported() -> None:
    provider = StatisticsProvider()
    constant = provider.analyze(
        EvidenceGraph(),
        ProviderInput(occurrences=_occurrences(["192.168.1.1"] * 5)),
    )[0]
    varied = provider.analyze(
        EvidenceGraph(),
        ProviderInput(occurrences=_occurrences([f"192.168.1.{index}" for index in range(5)])),
    )[0]
    assert constant.evidence.score > varied.evidence.score
    assert "cardinality=1" in constant.evidence.explanation
    assert "cardinality=5" in varied.evidence.explanation


def test_entropy_finding() -> None:
    provider = StatisticsProvider()
    finding = provider.analyze(
        EvidenceGraph(),
        ProviderInput(occurrences=_occurrences(["a", "b", "c", "d"])),
    )[0]
    assert "entropy=" in finding.evidence.explanation


@given(base=st.floats(min_value=0.0, max_value=1.0), count=st.integers(min_value=1, max_value=100))
def test_reinforce_score_monotonic(base: float, count: int) -> None:
    assert reinforce_score(base, count) <= reinforce_score(base, count + 1)


def test_reinforce_score_bounded() -> None:
    assert 0.0 <= reinforce_score(0.2, 1000) <= 1.0


def test_statistics_attaches_to_existing_field() -> None:
    graph = EvidenceGraph()
    graph.add_node(Node(id="field:cluster_1:destination", kind=NodeKind.FIELD, label="destination"))
    finding = StatisticsProvider().analyze(
        graph,
        ProviderInput(occurrences=_occurrences(["192.168.1.1", "192.168.1.2"])),
    )[0]
    assert finding.attach_to_node_id == "field:cluster_1:destination"
    run_providers(
        graph,
        ProviderInput(occurrences=_occurrences(["192.168.1.1", "192.168.1.2"])),
        (StatisticsProvider(),),
    )
    node = graph.get_node("field:cluster_1:destination")
    assert node is not None
    assert any(item.source == "statistics" for item in node.evidence)
