"""Tests for RegexProvider."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from ontolog.evidence.graph import EvidenceGraph
from ontolog.evidence.runner import run_providers
from ontolog.models.finding import ProviderInput
from ontolog.models.template import TemplateOccurrence, TemplateParameter
from ontolog.providers.regex import RegexProvider
from ontolog.templates.extractor import ExtractOptions, extract_templates

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _occurrence(
    template_id: str,
    params: tuple[tuple[str, str], ...],
) -> TemplateOccurrence:
    return TemplateOccurrence(
        template_id=template_id,
        message="synthetic",
        parameters=tuple(TemplateParameter(name=name, value=value) for name, value in params),
    )


def test_ipv4_parameter_high_confidence() -> None:
    provider = RegexProvider()
    data = ProviderInput(
        occurrences=(_occurrence("cluster_1", (("destination", "192.168.1.10"),)),),
    )
    findings = provider.analyze(EvidenceGraph(), data)
    type_findings = [
        finding for finding in findings if finding.node and finding.node.id == "type:ipv4"
    ]
    assert type_findings
    assert type_findings[0].evidence.score >= 0.9
    assert type_findings[0].evidence.source == "regex"


def test_hex_parameter_high_confidence() -> None:
    provider = RegexProvider()
    data = ProviderInput(
        occurrences=(_occurrence("cluster_1", (("payload", "0xdeadbeef"),)),),
    )
    findings = provider.analyze(EvidenceGraph(), data)
    type_findings = [
        finding for finding in findings if finding.node and finding.node.id == "type:hex"
    ]
    assert type_findings
    assert type_findings[0].evidence.score >= 0.9


def test_unknown_value_no_type_node() -> None:
    provider = RegexProvider()
    data = ProviderInput(occurrences=(_occurrence("cluster_1", (("interface", "eth0"),)),))
    findings = provider.analyze(EvidenceGraph(), data)
    assert not any(finding.node and finding.node.kind.value == "type" for finding in findings)


def test_samples_capped() -> None:
    provider = RegexProvider()
    occurrences = tuple(
        _occurrence("cluster_1", (("destination", f"192.168.1.{index}"),)) for index in range(10)
    )
    findings = provider.analyze(EvidenceGraph(), ProviderInput(occurrences=occurrences))
    assert findings[0].evidence.samples
    assert len(findings[0].evidence.samples) <= 5


def test_controlboard_templates_via_extractor() -> None:
    templates = extract_templates(FIXTURES / "controlboard.log", ExtractOptions())
    occurrences: list[TemplateOccurrence] = []
    for template in templates:
        occurrences.append(
            TemplateOccurrence(
                template_id=template.id,
                timestamp=datetime(2024, 1, 15, tzinfo=UTC),
                message=template.examples[0] if template.examples else template.template,
                parameters=(
                    TemplateParameter(name="destination", value="192.168.1.10"),
                    TemplateParameter(name="payload", value="0xdeadbeef"),
                ),
                process="controlboard",
            )
        )
    graph = EvidenceGraph()
    run_providers(
        graph,
        ProviderInput(templates=tuple(templates), occurrences=tuple(occurrences)),
        (RegexProvider(),),
    )
    type_nodes = [node for node in graph.nodes() if node.kind.value == "type"]
    labels = {node.label for node in type_nodes}
    assert "ipv4" in labels
    assert "hex" in labels
