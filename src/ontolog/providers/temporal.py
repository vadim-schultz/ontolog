"""Temporal sequence evidence between template occurrences."""

from __future__ import annotations

from itertools import pairwise

from ontolog.evidence.graph import EvidenceGraph
from ontolog.models.evidence import Edge, Evidence
from ontolog.models.finding import EvidenceFinding, ProviderInput
from ontolog.providers.ids import template_node_id


class TemporalProvider:
    """Detect ordered template sequences from timestamps."""

    @property
    def name(self) -> str:
        """Return the provider identifier."""
        return "temporal"

    def analyze(
        self,
        graph: EvidenceGraph,
        data: ProviderInput,
    ) -> tuple[EvidenceFinding, ...]:
        """Return temporal sequence findings."""
        ordered = sorted(
            data.occurrences,
            key=lambda item: (item.timestamp is None, item.timestamp or ""),
        )
        findings: list[EvidenceFinding] = []
        for left, right in pairwise(ordered):
            if left.template_id == right.template_id:
                continue
            score = min(1.0, 0.55 + 0.05 * len(ordered))
            evidence = Evidence(
                source="temporal",
                score=score,
                explanation=(f"Template {left.template_id!r} followed by {right.template_id!r}"),
            )
            source_id = template_node_id(left.template_id)
            target_id = template_node_id(right.template_id)
            edge = Edge(
                source_id=source_id, target_id=target_id, label="follows", evidence=(evidence,)
            )
            findings.append(EvidenceFinding(evidence=evidence, edge=edge))
        return tuple(findings)
