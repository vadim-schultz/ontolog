"""Regex-based type inference for template parameters."""

from __future__ import annotations

import re
from collections import defaultdict

from ontolog.evidence.graph import EvidenceGraph
from ontolog.models.evidence import Edge, Evidence, Node, NodeKind
from ontolog.models.finding import EvidenceFinding, ProviderInput
from ontolog.models.template import TemplateOccurrence
from ontolog.providers.ids import field_id, type_id
from ontolog.templates.patterns import STRONG_TYPE_SCORES, TYPE_PATTERNS, WEAK_TYPE_SCORE

_MAX_SAMPLES = 5
_TYPE_ORDER = tuple(TYPE_PATTERNS.keys())
_ParamKey = tuple[str, str]


class RegexProvider:
    """Infer parameter types from regex patterns."""

    @property
    def name(self) -> str:
        """Return the provider identifier."""
        return "regex"

    def analyze(
        self,
        graph: EvidenceGraph,
        data: ProviderInput,
    ) -> tuple[EvidenceFinding, ...]:
        """Return type findings for parameter values."""
        findings: list[EvidenceFinding] = []
        for key, values in _collect_parameter_samples(data.occurrences).items():
            param_findings = _findings_for_parameter(key, values)
            if param_findings is not None:
                findings.extend(param_findings)
        return tuple(findings)


def _collect_parameter_samples(
    occurrences: tuple[TemplateOccurrence, ...],
) -> dict[_ParamKey, list[str]]:
    samples: dict[_ParamKey, list[str]] = defaultdict(list)
    for occurrence in occurrences:
        for param in occurrence.parameters:
            key = (occurrence.template_id, param.name)
            if len(samples[key]) < _MAX_SAMPLES and param.value not in samples[key]:
                samples[key].append(param.value)
    return samples


def _findings_for_parameter(
    key: _ParamKey,
    values: list[str],
) -> tuple[EvidenceFinding, ...] | None:
    template_id, param_name = key
    matched_type = _dominant_type(values)
    if matched_type is None:
        return None
    score = STRONG_TYPE_SCORES.get(matched_type, WEAK_TYPE_SCORE)
    return _type_findings(
        field_node_id=field_id(template_id, param_name),
        type_node_id=type_id(matched_type),
        param_name=param_name,
        matched_type=matched_type,
        score=score,
        values=values,
    )


def _dominant_type(values: list[str]) -> str | None:
    counts: dict[str, int] = defaultdict(int)
    for value in values:
        matched = _match_type(value)
        if matched is not None:
            counts[matched] += 1
    if not counts:
        return None
    return max(counts, key=lambda name: counts[name])


def _match_type(value: str) -> str | None:
    for type_name in _TYPE_ORDER:
        if re.search(TYPE_PATTERNS[type_name], value):
            return type_name
    return None


def _type_findings(
    *,
    field_node_id: str,
    type_node_id: str,
    param_name: str,
    matched_type: str,
    score: float,
    values: list[str],
) -> tuple[EvidenceFinding, ...]:
    evidence = Evidence(
        source="regex",
        score=score,
        explanation=f"Parameter value matches {matched_type} pattern",
        samples=tuple(values[:_MAX_SAMPLES]),
    )
    field_node = Node(id=field_node_id, kind=NodeKind.FIELD, label=param_name, evidence=(evidence,))
    type_node = Node(id=type_node_id, kind=NodeKind.TYPE, label=matched_type)
    edge = Edge(source_id=field_node_id, target_id=type_node_id, label="has_type")
    return (
        EvidenceFinding(evidence=evidence, node=field_node),
        EvidenceFinding(evidence=evidence, node=type_node),
        EvidenceFinding(evidence=evidence, edge=edge),
    )
