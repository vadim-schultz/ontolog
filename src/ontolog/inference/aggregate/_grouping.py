"""Stable grouping and ranking helpers for aggregation."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol, TypeVar

from ontolog.config import EvidenceSourceTier, EvidenceSourceWeights
from ontolog.inference.aggregate.scoring import classify_source, weighted_confidence
from ontolog.models.domain import Alternative
from ontolog.models.evidence import Evidence

T = TypeVar("T", bound="EvidenceCarrier")
K = TypeVar("K", str, tuple[str, str, str])
R = TypeVar("R")


class EvidenceCarrier(Protocol):
    """Candidate with provenance attached."""

    @property
    def evidence(self) -> tuple[Evidence, ...]:
        """Return evidence backing the candidate."""
        ...


_TIER_ORDER = (
    EvidenceSourceTier.HUMAN,
    EvidenceSourceTier.DETERMINISTIC,
    EvidenceSourceTier.LLM,
)
_TIER_RANK = {
    EvidenceSourceTier.HUMAN: 0,
    EvidenceSourceTier.DETERMINISTIC: 1,
    EvidenceSourceTier.LLM: 2,
}


def export_eligible(confidence: float, export_threshold: float) -> bool:
    """Return whether ``confidence`` meets the export threshold."""
    return confidence >= export_threshold


def group_by_key(
    items: Sequence[T],
    key_fn: Callable[[T], K],
) -> dict[K, list[T]]:
    """Group ``items`` by ``key_fn`` preserving first-seen order."""
    groups: dict[K, list[T]] = {}
    for item in items:
        key = key_fn(item)
        groups.setdefault(key, []).append(item)
    return groups


def aggregate_ranked_groups(
    candidates: Sequence[T],
    *,
    key_fn: Callable[[T], K],
    alternative_value_fn: Callable[[T], str],
    tie_key_fn: Callable[[T], tuple[str, ...]],
    build: Callable[[K, T, float, tuple[Alternative, ...], bool], R],
    weights: EvidenceSourceWeights,
    export_threshold: float,
) -> tuple[R, ...]:
    """Group candidates, rank by tier and confidence, then map to domain values."""
    grouped = group_by_key(candidates, key_fn)
    results: list[R] = []
    for key in sorted(grouped):
        results.append(
            _aggregate_group(
                key,
                grouped[key],
                alternative_value_fn=alternative_value_fn,
                tie_key_fn=tie_key_fn,
                build=build,
                weights=weights,
                export_threshold=export_threshold,
            ),
        )
    return tuple(results)


def _aggregate_group(
    key: K,
    items: list[T],
    *,
    alternative_value_fn: Callable[[T], str],
    tie_key_fn: Callable[[T], tuple[str, ...]],
    build: Callable[[K, T, float, tuple[Alternative, ...], bool], R],
    weights: EvidenceSourceWeights,
    export_threshold: float,
) -> R:
    """Rank one candidate group and build its domain value."""
    ranked = rank_by_confidence(
        items,
        evidence_fn=lambda candidate: candidate.evidence,
        value_fn=alternative_value_fn,
        weights=weights,
        tie_key_fn=tie_key_fn,
    )
    primary, confidence = ranked[0]
    alternatives = build_alternatives(
        ranked,
        value_fn=alternative_value_fn,
        evidence_fn=lambda candidate: candidate.evidence,
    )
    eligible = export_eligible(confidence, export_threshold)
    return build(key, primary, confidence, alternatives, eligible)


def _best_tier(evidence: Sequence[Evidence]) -> EvidenceSourceTier:
    if not evidence:
        return EvidenceSourceTier.DETERMINISTIC
    present = {classify_source(item.source) for item in evidence}
    for tier in _TIER_ORDER:
        if tier in present:
            return tier
    return EvidenceSourceTier.DETERMINISTIC


def rank_by_confidence(
    items: Sequence[T],
    *,
    evidence_fn: Callable[[T], Sequence[Evidence]],
    value_fn: Callable[[T], str],
    weights: EvidenceSourceWeights,
    tie_key_fn: Callable[[T], tuple[str, ...]],
) -> list[tuple[T, float]]:
    """Rank items by evidence tier, then weighted confidence."""
    _ = value_fn
    ranked: list[tuple[T, float, int, tuple[str, ...]]] = []
    for item in items:
        evidence = evidence_fn(item)
        confidence = weighted_confidence(evidence, weights)
        tier_rank = _TIER_RANK[_best_tier(evidence)]
        ranked.append((item, confidence, tier_rank, tie_key_fn(item)))
    ranked.sort(key=lambda row: (row[2], -row[1], row[3]))
    return [(item, confidence) for item, confidence, _tier, _tie in ranked]


def build_alternatives(
    ranked: Sequence[tuple[T, float]],
    *,
    value_fn: Callable[[T], str],
    evidence_fn: Callable[[T], Sequence[Evidence]],
) -> tuple[Alternative, ...]:
    """Build alternatives from ranked items after the primary winner."""
    if len(ranked) <= 1:
        return ()
    return tuple(
        Alternative(
            value=value_fn(item),
            confidence=confidence,
            evidence=tuple(evidence_fn(item)),
        )
        for item, confidence in ranked[1:]
    )
