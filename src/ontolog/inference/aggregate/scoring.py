"""Aggregation scoring helpers."""

from __future__ import annotations

from collections.abc import Sequence

from ontolog.config import EvidenceSourceTier, EvidenceSourceWeights
from ontolog.inference.scoring import combine_scores
from ontolog.models.evidence import Evidence

_LLM_PREFIXES = ("llm", "semantic", "openai", "ollama", "anthropic", "gemini")
_TIER_ORDER = (
    EvidenceSourceTier.HUMAN,
    EvidenceSourceTier.DETERMINISTIC,
    EvidenceSourceTier.LLM,
)


def classify_source(source: str) -> EvidenceSourceTier:
    """Map an evidence source string to its aggregation tier."""
    lowered = source.lower()
    if lowered == "human":
        return EvidenceSourceTier.HUMAN
    if any(lowered == prefix or lowered.startswith(f"{prefix}_") for prefix in _LLM_PREFIXES):
        return EvidenceSourceTier.LLM
    return EvidenceSourceTier.DETERMINISTIC


def tier_weight(tier: EvidenceSourceTier, weights: EvidenceSourceWeights) -> float:
    """Return the configured multiplier for ``tier``."""
    if tier == EvidenceSourceTier.HUMAN:
        return weights.human
    if tier == EvidenceSourceTier.LLM:
        return weights.llm
    return weights.deterministic


def _winning_tier(evidence: Sequence[Evidence]) -> EvidenceSourceTier:
    present = {classify_source(item.source) for item in evidence}
    for tier in _TIER_ORDER:
        if tier in present:
            return tier
    return EvidenceSourceTier.DETERMINISTIC


def _tier_evidence(evidence: Sequence[Evidence], tier: EvidenceSourceTier) -> tuple[Evidence, ...]:
    return tuple(item for item in evidence if classify_source(item.source) == tier)


def weighted_confidence(
    evidence: Sequence[Evidence],
    weights: EvidenceSourceWeights,
) -> float:
    """Combine evidence using tier priority and per-tier weights.

    Only the highest present tier contributes. Within that tier each score is
    multiplied by the tier weight (capped at 1.0), then merged via noisy-OR.
    """
    if not evidence:
        return 0.0
    tier = _winning_tier(evidence)
    tier_items = _tier_evidence(evidence, tier)
    multiplier = tier_weight(tier, weights)
    adjusted = [min(item.score * multiplier, 1.0) for item in tier_items]
    return combine_scores(adjusted)
