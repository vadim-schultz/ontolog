"""Event inference from graph evidence."""

from __future__ import annotations

from ontolog.config import ConfidenceThresholds
from ontolog.evidence.graph import EvidenceGraph
from ontolog.inference.queries import collect_evidence, nodes_by_kind
from ontolog.inference.scoring import combine_scores
from ontolog.models.candidate import EventCandidate, InferenceResult
from ontolog.models.evidence import Node, NodeKind
from ontolog.models.finding import ProviderInput

_VERB_PATTERNS: dict[str, tuple[str, ...]] = {
    "send": ("sent", "send"),
    "receive": ("received", "receive"),
    "connect": ("connect", "established"),
    "create": ("create", "created"),
    "delete": ("delete", "deleted", "removed"),
    "update": ("update", "updated", "validated"),
}


class EventInferencePass:
    """Promote event nodes and classify lifecycle verbs."""

    @property
    def name(self) -> str:
        """Return the inference pass identifier."""
        return "events"

    def infer(
        self,
        graph: EvidenceGraph,
        data: ProviderInput,
        *,
        thresholds: ConfidenceThresholds,
    ) -> InferenceResult:
        """Return event candidates."""
        del data  # not used, only here to satisfy the protocol
        return InferenceResult(events=_event_candidates(graph, thresholds.event))


def _event_candidates(
    graph: EvidenceGraph,
    min_confidence: float,
) -> tuple[EventCandidate, ...]:
    """Promote event nodes that meet the confidence threshold."""
    candidates: list[EventCandidate] = []
    for node in nodes_by_kind(graph, NodeKind.EVENT):
        candidate = _event_candidate_from_node(node, min_confidence)
        if candidate is not None:
            candidates.append(candidate)
    return tuple(candidates)


def _event_candidate_from_node(
    node: Node,
    min_confidence: float,
) -> EventCandidate | None:
    """Return an event candidate when node evidence clears the threshold."""
    confidence = combine_scores([evidence.score for evidence in node.evidence])
    if confidence < min_confidence:
        return None
    slug = node.id.removeprefix("event:")
    return _build_event_candidate(node, slug=slug, confidence=confidence)


def _build_event_candidate(
    node: Node,
    *,
    slug: str,
    confidence: float,
) -> EventCandidate:
    """Build an event candidate from a graph event node."""
    return EventCandidate(
        name=node.label,
        slug=slug,
        verbs=_verbs_for_slug(slug),
        confidence=confidence,
        graph_node_id=node.id,
        evidence=collect_evidence(node),
    )


def _verbs_for_slug(slug: str) -> frozenset[str]:
    """Return lifecycle verbs matched from an event slug."""
    lowered = slug.lower()
    return frozenset(
        verb
        for verb, patterns in _VERB_PATTERNS.items()
        if any(pattern in lowered for pattern in patterns)
    )
