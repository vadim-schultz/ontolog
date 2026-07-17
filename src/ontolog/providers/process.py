"""Process mining evidence for repeated template subsequences."""

from __future__ import annotations

from collections import Counter

from ontolog.evidence.graph import EvidenceGraph
from ontolog.models.evidence import Edge, Evidence
from ontolog.models.finding import EvidenceFinding, ProviderInput
from ontolog.providers.ids import template_node_id

_DEFAULT_MIN_SUPPORT = 2
_SUBSEQUENCE_LENGTH = 3


class ProcessProvider:
    """Detect repeated template activity patterns."""

    def __init__(self, *, min_support: int = _DEFAULT_MIN_SUPPORT) -> None:
        """Initialize with the minimum subsequence support count."""
        self._min_support = min_support

    @property
    def name(self) -> str:
        """Return the provider identifier."""
        return "process"

    def analyze(
        self,
        graph: EvidenceGraph,
        data: ProviderInput,
    ) -> tuple[EvidenceFinding, ...]:
        """Return repeated subsequence findings."""
        sequence = [occurrence.template_id for occurrence in data.occurrences]
        counts = Counter(
            tuple(sequence[index : index + _SUBSEQUENCE_LENGTH])
            for index in range(len(sequence) - _SUBSEQUENCE_LENGTH + 1)
        )
        findings: list[EvidenceFinding] = []
        for subsequence, count in counts.items():
            if count < self._min_support:
                continue
            score = min(1.0, 0.6 + 0.05 * count)
            evidence = Evidence(
                source="process",
                score=score,
                explanation=f"Subsequence repeated {count} times: {' -> '.join(subsequence)}",
            )
            left_id = template_node_id(subsequence[0])
            right_id = template_node_id(subsequence[-1])
            edge = Edge(
                source_id=left_id,
                target_id=right_id,
                label="repeats_in_process",
                evidence=(evidence,),
            )
            findings.append(EvidenceFinding(evidence=evidence, edge=edge))
        return tuple(findings)
