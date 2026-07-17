"""Relationship inference from graph evidence."""

from __future__ import annotations

from ontolog.config import ConfidenceThresholds
from ontolog.evidence.graph import EvidenceGraph
from ontolog.inference.queries import collect_evidence, edges_with_label, nodes_by_kind
from ontolog.inference.scoring import combine_scores
from ontolog.models.candidate import InferenceResult, RelationshipCandidate
from ontolog.models.evidence import Edge, Node, NodeKind
from ontolog.models.finding import ProviderInput

_ENTITY_FIELD_LABELS: frozenset[str] = frozenset({"interface"})


class RelationshipInferencePass:
    """Infer ownership and dependency relationships."""

    @property
    def name(self) -> str:
        """Return the inference pass identifier."""
        return "relationships"

    def infer(
        self,
        graph: EvidenceGraph,
        data: ProviderInput,
        *,
        thresholds: ConfidenceThresholds,
    ) -> InferenceResult:
        """Return relationship candidates."""
        del data  # not used, only here to satisfy the protocol
        return InferenceResult(
            relationships=_ownership_candidates(graph, thresholds.relationship),
        )


def _ownership_candidates(
    graph: EvidenceGraph,
    min_confidence: float,
) -> tuple[RelationshipCandidate, ...]:
    """Infer ``owns`` relationships from ``has_field`` edges."""
    entity_names = _entity_display_names(graph)
    candidates: list[RelationshipCandidate] = []
    for edge in edges_with_label(graph, "has_field"):
        candidate = _owns_candidate_from_has_field(
            graph,
            edge,
            entity_names,
            min_confidence,
        )
        if candidate is not None:
            candidates.append(candidate)
    return tuple(candidates)


def _entity_display_names(graph: EvidenceGraph) -> dict[str, str]:
    """Return display labels for entity nodes keyed by node id."""
    return {node.id: node.label for node in nodes_by_kind(graph, NodeKind.ENTITY)}


def _owns_candidate_from_has_field(
    graph: EvidenceGraph,
    edge: Edge,
    entity_names: dict[str, str],
    min_confidence: float,
) -> RelationshipCandidate | None:
    """Return an ``owns`` candidate when a structural field links to an entity."""
    source = graph.get_node(edge.source_id)
    target = graph.get_node(edge.target_id)
    if source is None or target is None:
        return None
    if not _is_structural_entity_field(target.label):
        return None
    confidence = _owns_confidence(edge, source)
    if confidence < min_confidence:
        return None
    return _build_owns_candidate(edge, source, target, entity_names, confidence)


def _is_structural_entity_field(label: str) -> bool:
    """Return whether ``label`` names a field promoted to an entity."""
    return label.lower() in _ENTITY_FIELD_LABELS


def _owns_confidence(edge: Edge, source: Node) -> float:
    """Combine relationship evidence from the edge and owning entity."""
    scores = [item.score for item in edge.evidence] + [item.score for item in source.evidence]
    return combine_scores(scores)


def _build_owns_candidate(
    edge: Edge,
    source: Node,
    target: Node,
    entity_names: dict[str, str],
    confidence: float,
) -> RelationshipCandidate:
    """Build an ``owns`` relationship between an entity and a structural field."""
    return RelationshipCandidate(
        kind="owns",
        source_name=entity_names.get(source.id, source.label),
        target_name=_title_case(target.label.lower()),
        confidence=confidence,
        evidence=(*collect_evidence(edge), *collect_evidence(source)),
    )


def _title_case(value: str) -> str:
    """Return a title-cased display name."""
    return value.replace("_", " ").title()
