"""Relationship inference from graph evidence."""

from __future__ import annotations

from ontolog.config import ConfidenceThresholds
from ontolog.evidence.graph import EvidenceGraph
from ontolog.inference.hierarchy import build_hierarchy_index
from ontolog.inference.queries import collect_evidence, nodes_by_kind
from ontolog.inference.scoring import combine_scores
from ontolog.models.candidate import InferenceResult, RelationshipCandidate
from ontolog.models.evidence import Evidence, NodeKind
from ontolog.models.finding import ProviderInput


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
        return InferenceResult(
            relationships=_ownership_candidates(graph, data, thresholds.relationship),
        )


def _ownership_candidates(
    graph: EvidenceGraph,
    data: ProviderInput,
    min_confidence: float,
) -> tuple[RelationshipCandidate, ...]:
    """Infer chained ``owns`` relationships from template occurrence order."""
    index = build_hierarchy_index(data)
    candidates: list[RelationshipCandidate] = []
    for parent_slug, child_slug in sorted(index.owns_edges):
        support = index.owns_counts[(parent_slug, child_slug)]
        candidate = _owns_candidate(
            graph,
            parent_slug,
            child_slug,
            support,
            min_confidence,
        )
        if candidate is not None:
            candidates.append(candidate)
    return tuple(candidates)


def _owns_candidate(
    graph: EvidenceGraph,
    parent_slug: str,
    child_slug: str,
    template_support: int,
    min_confidence: float,
) -> RelationshipCandidate | None:
    """Return an ``owns`` candidate when confidence meets the threshold."""
    confidence = _chain_owns_confidence(
        graph,
        parent_slug,
        child_slug,
        template_support=template_support,
    )
    if confidence < min_confidence:
        return None
    return RelationshipCandidate(
        kind="owns",
        source_name=_display_name(graph, parent_slug),
        target_name=_display_name(graph, child_slug),
        confidence=confidence,
        evidence=_chain_owns_evidence(
            graph,
            parent_slug,
            child_slug,
            template_support=template_support,
        ),
    )


def _chain_owns_confidence(
    graph: EvidenceGraph,
    parent_slug: str,
    child_slug: str,
    *,
    template_support: int,
) -> float:
    """Combine graph and template-order evidence for an ``owns`` edge."""
    scores = [min(0.95, 0.7 + 0.1 * template_support)]
    for slug in (parent_slug, child_slug):
        node = graph.get_node(f"entity:{slug}")
        if node is not None:
            scores.extend(evidence.score for evidence in node.evidence)
    return combine_scores(scores)


def _chain_owns_evidence(
    graph: EvidenceGraph,
    parent_slug: str,
    child_slug: str,
    *,
    template_support: int,
) -> tuple[Evidence, ...]:
    """Return provenance for a chained ``owns`` relationship."""
    evidence: list[Evidence] = [
        Evidence(
            source="namespace",
            score=min(0.95, 0.7 + 0.1 * template_support),
            explanation=(
                f"Entity {child_slug!r} follows {parent_slug!r} in template occurrence order "
                f"({template_support} templates)"
            ),
        ),
    ]
    for slug in (parent_slug, child_slug):
        node = graph.get_node(f"entity:{slug}")
        if node is not None:
            evidence.extend(collect_evidence(node))
    return tuple(evidence)


def _display_name(graph: EvidenceGraph, slug: str) -> str:
    """Return a display label for an entity slug."""
    node = graph.get_node(f"entity:{slug}")
    if node is not None:
        return node.label
    for entity in nodes_by_kind(graph, NodeKind.ENTITY):
        if entity.id.removeprefix("entity:") == slug:
            return entity.label
    return slug.replace("_", " ").title()
