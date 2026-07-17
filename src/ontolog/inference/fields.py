"""Field type inference from graph evidence.

Documented confidence targets on the controlboard fixture:

| Field | Type | Expected confidence | Evidence sources |
|-------|------|---------------------|------------------|
| ``destination`` | ``ipv4`` | >= 0.95 (typically ~1.0) | regex (0.95) + statistics reinforcement |
| ``payload`` | ``hex`` | >= 0.95 (typically ~0.98) | regex (0.95) + statistics reinforcement |
"""

from __future__ import annotations

import re

from ontolog.config import ConfidenceThresholds
from ontolog.evidence.graph import EvidenceGraph
from ontolog.inference.queries import collect_evidence, field_type_name, nodes_by_kind
from ontolog.inference.scoring import combine_scores
from ontolog.models.candidate import FieldCandidate, InferenceResult
from ontolog.models.evidence import Evidence, Node, NodeKind
from ontolog.models.finding import ProviderInput
from ontolog.models.template import Template
from ontolog.providers.ids import field_id

_MASK_PARAM_PATTERN = re.compile(r"(\w+)=<(\w+)>")


class FieldInferencePass:
    """Promote typed field nodes from provider evidence."""

    @property
    def name(self) -> str:
        """Return the inference pass identifier."""
        return "fields"

    def infer(
        self,
        graph: EvidenceGraph,
        data: ProviderInput,
        *,
        thresholds: ConfidenceThresholds,
    ) -> InferenceResult:
        """Return field candidates."""
        mask_tokens = _mask_tokens_from_templates(data.templates)
        candidates = _semantic_field_candidates(graph, data.templates, thresholds.field)
        _graph_field_candidates(candidates, graph, mask_tokens, thresholds.field)
        return InferenceResult(fields=tuple(candidates.values()))


def _merge_field_candidate(
    candidates: dict[str, FieldCandidate],
    candidate: FieldCandidate | None,
    min_confidence: float,
) -> None:
    """Insert ``candidate`` when it meets the threshold and beats any existing name."""
    if candidate is None or candidate.confidence < min_confidence:
        return
    existing = candidates.get(candidate.name)
    if existing is None or candidate.confidence > existing.confidence:
        candidates[candidate.name] = candidate


def _semantic_field_candidates(
    graph: EvidenceGraph,
    templates: tuple[Template, ...],
    min_confidence: float,
) -> dict[str, FieldCandidate]:
    """Build field candidates from semantic template parameter names."""
    candidates: dict[str, FieldCandidate] = {}
    for template in templates:
        _add_semantic_fields_for_template(candidates, graph, template, min_confidence)
    return candidates


def _add_semantic_fields_for_template(
    candidates: dict[str, FieldCandidate],
    graph: EvidenceGraph,
    template: Template,
    min_confidence: float,
) -> None:
    """Merge semantic fields inferred from one template's mask placeholders."""
    for semantic_name, mask_token in _semantic_param_map(template.template).items():
        _merge_field_candidate(
            candidates,
            _semantic_field_candidate(
                graph,
                template_id=template.id,
                semantic_name=semantic_name,
                mask_token=mask_token,
            ),
            min_confidence,
        )


def _graph_field_candidates(
    candidates: dict[str, FieldCandidate],
    graph: EvidenceGraph,
    mask_tokens: set[str],
    min_confidence: float,
) -> None:
    """Merge typed field nodes from the graph, excluding raw mask tokens."""
    for node in nodes_by_kind(graph, NodeKind.FIELD):
        if node.label in mask_tokens:
            continue
        _merge_field_candidate(candidates, _field_candidate(graph, node), min_confidence)


def _mask_tokens_from_templates(templates: tuple[Template, ...]) -> set[str]:
    """Return mask placeholder names used across templates."""
    tokens: set[str] = set()
    for template in templates:
        for _semantic_name, mask_token in _semantic_param_map(template.template).items():
            tokens.add(mask_token)
    return tokens


def _semantic_param_map(template_text: str) -> dict[str, str]:
    """Map semantic parameter names to mask tokens in ``template_text``."""
    return {match.group(1): match.group(2) for match in _MASK_PARAM_PATTERN.finditer(template_text)}


def _semantic_field_candidate(
    graph: EvidenceGraph,
    *,
    template_id: str,
    semantic_name: str,
    mask_token: str,
) -> FieldCandidate | None:
    typed_field_id = field_id(template_id, mask_token)
    type_name = field_type_name(graph, typed_field_id)
    if type_name is None:
        return None

    typed_node = graph.get_node(typed_field_id)
    semantic_node = graph.get_node(field_id(template_id, semantic_name))
    scores: list[float] = []
    evidence: list[Evidence] = []
    for node in (typed_node, semantic_node):
        if node is None:
            continue
        scores.extend(item.score for item in node.evidence)
        evidence.extend(collect_evidence(node))
    for edge in graph.edges():
        if edge.source_id == typed_field_id and edge.label == "has_type":
            scores.extend(item.score for item in edge.evidence)
            evidence.extend(edge.evidence)

    return FieldCandidate(
        name=semantic_name,
        type_name=type_name,
        confidence=combine_scores(scores),
        graph_node_id=field_id(template_id, semantic_name),
        evidence=tuple(evidence),
    )


def _field_candidate(graph: EvidenceGraph, node: Node) -> FieldCandidate | None:
    type_name = field_type_name(graph, node.id)
    if type_name is None:
        return None

    scores = [evidence.score for evidence in node.evidence]
    evidence = list(collect_evidence(node))
    for edge in graph.edges():
        if edge.source_id == node.id and edge.label == "has_type":
            scores.extend(item.score for item in edge.evidence)
            evidence.extend(edge.evidence)

    return FieldCandidate(
        name=node.label,
        type_name=type_name,
        confidence=combine_scores(scores),
        graph_node_id=node.id,
        evidence=tuple(evidence),
    )
