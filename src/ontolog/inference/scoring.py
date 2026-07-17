"""Inference scoring helpers."""

from __future__ import annotations

from collections.abc import Sequence


def combine_scores(scores: Sequence[float]) -> float:
    """Combine independent evidence scores into one confidence in ``[0, 1]``."""
    if not scores:
        return 0.0
    product = 1.0
    for score in scores:
        product *= 1.0 - score
    return 1.0 - product
