"""Tests for reinforce_score."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from ontolog.evidence.scoring import reinforce_score


@given(base=st.floats(min_value=0.0, max_value=1.0), count=st.integers(min_value=1, max_value=100))
def test_reinforce_score_monotonic(base: float, count: int) -> None:
    assert reinforce_score(base, count) <= reinforce_score(base, count + 1)


def test_reinforce_score_bounded() -> None:
    assert 0.0 <= reinforce_score(0.2, 1000) <= 1.0
