"""Tests for aggregation scoring helpers."""

from __future__ import annotations

from ontolog.config import EvidenceSourceTier, default_config
from ontolog.inference.aggregate.scoring import classify_source, weighted_confidence
from ontolog.models.evidence import Evidence


def test_classify_source_human() -> None:
    assert classify_source("human") == EvidenceSourceTier.HUMAN


def test_classify_source_deterministic() -> None:
    assert classify_source("regex") == EvidenceSourceTier.DETERMINISTIC
    assert classify_source("namespace") == EvidenceSourceTier.DETERMINISTIC


def test_classify_source_llm() -> None:
    assert classify_source("openai") == EvidenceSourceTier.LLM
    assert classify_source("llm") == EvidenceSourceTier.LLM


def test_weighted_confidence_human_beats_llm_at_same_score() -> None:
    weights = default_config().source_weights
    human = Evidence(source="human", score=0.6, explanation="approved")
    llm = Evidence(source="openai", score=0.6, explanation="guessed")
    assert weighted_confidence((human,), weights) > weighted_confidence((llm,), weights)


def test_tier_priority_human_suppresses_llm() -> None:
    weights = default_config().source_weights
    mixed = (
        Evidence(source="human", score=0.5, explanation="approved"),
        Evidence(source="openai", score=0.99, explanation="guessed"),
    )
    human_only = weighted_confidence((mixed[0],), weights)
    assert weighted_confidence(mixed, weights) == human_only
