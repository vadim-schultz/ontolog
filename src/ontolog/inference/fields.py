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
from ontolog.enum_slug import enum_type_slug, is_enum_type_slug
from ontolog.evidence.graph import EvidenceGraph
from ontolog.identifiers import is_valid_field_name
from ontolog.inference.queries import (
    collect_evidence,
    entity_slug_for_field,
    field_type_name,
    nodes_by_kind,
)
from ontolog.inference.scoring import combine_scores
from ontolog.inference.status_values import collect_status_values
from ontolog.models.candidate import FieldCandidate, InferenceResult
from ontolog.models.evidence import Evidence, Node, NodeKind
from ontolog.models.finding import ProviderInput
from ontolog.models.template import Template
from ontolog.providers.ids import field_id

_MASK_PARAM_PATTERN = re.compile(r"(\w+)=<(\w+)>")
_STATUS_PARAM = "status"
_MIN_STATUS_ENUM_VALUES = 2


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
        candidates = _semantic_field_candidates(graph, data.templates, thresholds.field, data=data)
        _graph_field_candidates(candidates, graph, data, mask_tokens, thresholds.field)
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
    *,
    data: ProviderInput,
) -> dict[str, FieldCandidate]:
    """Build field candidates from semantic template parameter names."""
    candidates: dict[str, FieldCandidate] = {}
    for template in templates:
        _add_semantic_fields_for_template(candidates, graph, template, min_confidence, data=data)
    return candidates


def _add_semantic_fields_for_template(
    candidates: dict[str, FieldCandidate],
    graph: EvidenceGraph,
    template: Template,
    min_confidence: float,
    *,
    data: ProviderInput,
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
                data=data,
            ),
            min_confidence,
        )


def _graph_field_candidates(
    candidates: dict[str, FieldCandidate],
    graph: EvidenceGraph,
    data: ProviderInput,
    mask_tokens: set[str],
    min_confidence: float,
) -> None:
    """Merge typed field nodes from the graph, excluding raw mask tokens."""
    for node in nodes_by_kind(graph, NodeKind.FIELD):
        if node.label in mask_tokens or not is_valid_field_name(node.label):
            continue
        _merge_field_candidate(
            candidates,
            _field_candidate(graph, node, data),
            min_confidence,
        )


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


def _collect_node_evidence(
    nodes: tuple[Node | None, ...],
) -> tuple[list[float], list[Evidence]]:
    """Collect scores and provenance from graph nodes."""
    scores: list[float] = []
    evidence: list[Evidence] = []
    for node in nodes:
        if node is None:
            continue
        scores.extend(item.score for item in node.evidence)
        evidence.extend(collect_evidence(node))
    return scores, evidence


def _semantic_field_candidate(
    graph: EvidenceGraph,
    *,
    template_id: str,
    semantic_name: str,
    mask_token: str,
    data: ProviderInput,
) -> FieldCandidate | None:
    if not is_valid_field_name(semantic_name):
        return None
    typed_field_id = field_id(template_id, mask_token)
    type_name = field_type_name(graph, typed_field_id)
    if type_name is None:
        return None

    typed_node = graph.get_node(typed_field_id)
    semantic_node = graph.get_node(field_id(template_id, semantic_name))
    scores, evidence = _collect_node_evidence((typed_node, semantic_node))
    _append_has_type_evidence(graph, typed_field_id, scores, evidence)

    return FieldCandidate(
        name=semantic_name,
        type_name=type_name,
        confidence=combine_scores(scores),
        graph_node_id=field_id(template_id, semantic_name),
        entity_slug=entity_slug_for_field(
            graph,
            field_id(template_id, semantic_name),
            data=data,
        ),
        evidence=tuple(evidence),
    )


def _field_candidate(
    graph: EvidenceGraph,
    node: Node,
    data: ProviderInput,
) -> FieldCandidate | None:
    """Return a field candidate promoted from a graph field node."""
    if not is_valid_field_name(node.label):
        return None
    type_name = _resolved_type_name(graph, node, data)
    if type_name is None:
        return None
    scores, evidence = _field_scores_and_evidence(graph, node, type_name)
    return _build_field_candidate(graph, node, type_name, scores, evidence, data=data)


def _resolved_type_name(
    graph: EvidenceGraph,
    node: Node,
    data: ProviderInput,
) -> str | None:
    """Return the inferred type slug for ``node``, including status enums."""
    type_name = field_type_name(graph, node.id)
    if type_name is not None:
        return type_name
    return _status_enum_type_name(node, data)


def _field_scores_and_evidence(
    graph: EvidenceGraph,
    node: Node,
    type_name: str,
) -> tuple[list[float], list[Evidence]]:
    """Collect confidence scores and provenance for a graph field."""
    scores = [item.score for item in node.evidence]
    evidence = list(collect_evidence(node))
    _append_has_type_evidence(graph, node.id, scores, evidence)
    _append_enum_evidence(type_name, scores, evidence)
    return scores, evidence


def _append_has_type_evidence(
    graph: EvidenceGraph,
    field_node_id: str,
    scores: list[float],
    evidence: list[Evidence],
) -> None:
    """Merge ``has_type`` edge evidence targeting ``field_node_id``."""
    for edge in graph.edges():
        if edge.source_id != field_node_id or edge.label != "has_type":
            continue
        scores.extend(item.score for item in edge.evidence)
        evidence.extend(edge.evidence)


def _append_enum_evidence(
    type_name: str,
    scores: list[float],
    evidence: list[Evidence],
) -> None:
    """Boost confidence when ``type_name`` encodes a closed enum."""
    if not is_enum_type_slug(type_name):
        return
    scores.append(0.95)
    evidence.append(
        Evidence(
            source="states",
            score=0.95,
            explanation="Closed lifecycle status enum inferred from templates",
        ),
    )


def _build_field_candidate(
    graph: EvidenceGraph,
    node: Node,
    type_name: str,
    scores: list[float],
    evidence: list[Evidence],
    *,
    data: ProviderInput,
) -> FieldCandidate:
    """Build a field candidate from resolved type and collected evidence."""
    return FieldCandidate(
        name=node.label,
        type_name=type_name,
        confidence=combine_scores(scores),
        graph_node_id=node.id,
        entity_slug=entity_slug_for_field(graph, node.id, data=data),
        evidence=tuple(evidence),
    )


def _status_enum_type_name(node: Node, data: ProviderInput) -> str | None:
    """Return an enum type slug for closed ``status`` parameter value sets."""
    if node.label != _STATUS_PARAM:
        return None
    values = collect_status_values(data.occurrences, data.templates)
    if len(values) < _MIN_STATUS_ENUM_VALUES:
        return None
    return enum_type_slug(values)
