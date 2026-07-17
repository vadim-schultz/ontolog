"""Co-occurrence relationship evidence."""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations

from ontolog.evidence.graph import EvidenceGraph
from ontolog.models.evidence import Edge, Evidence
from ontolog.models.finding import EvidenceFinding, ProviderInput
from ontolog.providers.ids import field_id


class CoOccurrenceProvider:
    """Detect parameters that appear together in occurrences."""

    @property
    def name(self) -> str:
        """Return the provider identifier."""
        return "co_occurrence"

    def analyze(
        self,
        graph: EvidenceGraph,
        data: ProviderInput,
    ) -> tuple[EvidenceFinding, ...]:
        """Return co-occurrence relationship findings."""
        pair_counts: dict[tuple[tuple[str, str], tuple[str, str]], int] = defaultdict(int)

        for occurrence in data.occurrences:
            params = [(occurrence.template_id, param.name) for param in occurrence.parameters]
            for left, right in combinations(sorted(params), 2):
                pair_counts[(left, right)] += 1

        findings: list[EvidenceFinding] = []
        for (left, right), count in pair_counts.items():
            score = min(1.0, 0.5 + 0.05 * count)
            source_id = field_id(left[0], left[1])
            target_id = field_id(right[0], right[1])
            evidence = Evidence(
                source="co_occurrence",
                score=score,
                explanation=f"Parameters co-occurred {count} times",
            )
            edge = Edge(
                source_id=source_id, target_id=target_id, label="co_occurs", evidence=(evidence,)
            )
            findings.append(EvidenceFinding(evidence=evidence, edge=edge))

        return tuple(findings)
