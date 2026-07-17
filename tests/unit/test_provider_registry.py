"""Tests for provider registry and orchestrator."""

from __future__ import annotations

from ontolog.config import ProviderConfig, ProviderKind, default_config
from ontolog.evidence.graph import EvidenceGraph
from ontolog.evidence.runner import _apply_finding, run_providers
from ontolog.models.evidence import Evidence, Node, NodeKind
from ontolog.models.finding import EvidenceFinding, ProviderInput
from ontolog.providers import provider_registry


def test_evidence_finding_construct() -> None:
    evidence = Evidence(source="regex", score=0.9, explanation="test")
    node = Node(id="entity:test", kind=NodeKind.ENTITY, label="Test")
    finding = EvidenceFinding(evidence=evidence, node=node)
    assert finding.evidence.source == "regex"
    assert finding.node is not None


def test_provider_input_construct() -> None:
    data = ProviderInput()
    assert data.templates == ()
    assert data.occurrences == ()


def test_registry_default_all_enabled() -> None:
    providers = provider_registry(default_config().providers)
    assert len(providers) == 6


def test_registry_respects_disabled() -> None:
    config = ProviderConfig(
        enabled=frozenset(kind for kind in ProviderKind if kind != ProviderKind.REGEX)
    )
    providers = provider_registry(config)
    assert all(provider.name != "regex" for provider in providers)
    assert len(providers) == 5


def test_run_providers_empty_input() -> None:
    graph = EvidenceGraph()
    run_providers(graph, ProviderInput(), provider_registry(default_config().providers))
    assert graph.node_count() == 0


def test_apply_finding_adds_node_with_evidence() -> None:
    graph = EvidenceGraph()
    evidence = Evidence(source="regex", score=0.95, explanation="IPv4 pattern")
    node = Node(id="type:ipv4", kind=NodeKind.TYPE, label="ipv4", evidence=(evidence,))
    finding = EvidenceFinding(evidence=evidence, node=node)
    run_providers(graph, ProviderInput(), ())

    _apply_finding(graph, finding)
    loaded = graph.get_node("type:ipv4")
    assert loaded is not None
    assert loaded.evidence[0].score == 0.95
