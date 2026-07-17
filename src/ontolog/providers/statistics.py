"""Statistical evidence for template parameters."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import NamedTuple

from ontolog.evidence.graph import EvidenceGraph
from ontolog.evidence.scoring import reinforce_score
from ontolog.models.evidence import Evidence, Node, NodeKind
from ontolog.models.finding import EvidenceFinding, ProviderInput
from ontolog.models.template import TemplateOccurrence
from ontolog.providers.ids import field_id

_ParamKey = tuple[str, str]


class _ValueStats(NamedTuple):
    top_value: str
    frequency: float
    cardinality: int
    entropy: float


class StatisticsProvider:
    """Attach frequency, cardinality, and entropy evidence to fields."""

    @property
    def name(self) -> str:
        """Return the provider identifier."""
        return "statistics"

    def analyze(
        self,
        graph: EvidenceGraph,
        data: ProviderInput,
    ) -> tuple[EvidenceFinding, ...]:
        """Return statistical findings per parameter."""
        findings: list[EvidenceFinding] = []
        for key, values in _collect_values_by_field(data.occurrences).items():
            template_id, param_name = key
            findings.append(_field_stat_finding(template_id, param_name, values, graph))
        return tuple(findings)


def _collect_values_by_field(
    occurrences: tuple[TemplateOccurrence, ...],
) -> dict[_ParamKey, list[str]]:
    values_by_field: dict[_ParamKey, list[str]] = defaultdict(list)
    for occurrence in occurrences:
        for param in occurrence.parameters:
            values_by_field[(occurrence.template_id, param.name)].append(param.value)
    return values_by_field


def _field_stat_finding(
    template_id: str,
    param_name: str,
    values: list[str],
    graph: EvidenceGraph,
) -> EvidenceFinding:
    node_id = field_id(template_id, param_name)
    existing = graph.get_node(node_id)
    stats = _value_stats(values)
    score = _score_from_stats(stats, values, existing)
    evidence = _statistics_evidence(stats, score)
    return _finding_for_field(node_id, param_name, evidence, existing)


def _value_stats(values: list[str]) -> _ValueStats:
    counts = Counter(values)
    top_value, top_count = counts.most_common(1)[0]
    return _ValueStats(
        top_value=top_value,
        frequency=top_count / len(values),
        cardinality=len(counts),
        entropy=_shannon_entropy(values),
    )


def _score_from_stats(
    stats: _ValueStats,
    values: list[str],
    existing: Node | None,
) -> float:
    base_score = min(1.0, 0.4 + stats.frequency * 0.5)
    if existing is not None and existing.evidence:
        return reinforce_score(existing.evidence[-1].score, len(values))
    return base_score


def _statistics_evidence(stats: _ValueStats, score: float) -> Evidence:
    return Evidence(
        source="statistics",
        score=score,
        explanation=(
            f"frequency={stats.frequency:.2f}, cardinality={stats.cardinality}, "
            f"entropy={stats.entropy:.2f}, dominant={stats.top_value!r}"
        ),
        samples=(stats.top_value,),
    )


def _finding_for_field(
    node_id: str,
    param_name: str,
    evidence: Evidence,
    existing: Node | None,
) -> EvidenceFinding:
    if existing is None:
        node = Node(id=node_id, kind=NodeKind.FIELD, label=param_name, evidence=(evidence,))
        return EvidenceFinding(evidence=evidence, node=node)
    return EvidenceFinding(evidence=evidence, attach_to_node_id=node_id)


def _shannon_entropy(values: list[str]) -> float:
    if not values:
        return 0.0
    counts = Counter(values)
    total = len(values)
    entropy = 0.0
    for count in counts.values():
        probability = count / total
        entropy -= probability * math.log2(probability)
    return entropy
