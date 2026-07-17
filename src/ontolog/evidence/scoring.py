"""Evidence scoring helpers."""

from __future__ import annotations


def reinforce_score(base: float, observation_count: int) -> float:
    """Increase confidence monotonically with repeated observations."""
    if observation_count <= 1:
        return min(1.0, base)
    bonus = min(0.04 * (observation_count - 1), 1.0 - base)
    return min(1.0, base + bonus)
