"""Tests for inference scoring helpers."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from ontolog.inference.scoring import combine_scores


def test_combine_scores_single() -> None:
    assert combine_scores([0.8]) == 0.8


def test_combine_scores_empty() -> None:
    assert combine_scores([]) == 0.0


def test_combine_scores_bounded() -> None:
    assert 0.0 <= combine_scores([0.2, 0.5, 0.9]) <= 1.0


@given(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
def test_combine_scores_single_value_bounded(score: float) -> None:
    assert 0.0 <= combine_scores([score]) <= 1.0


@given(
    base=st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False),
    extra=st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False),
)
def test_combine_scores_monotonic_with_extra_evidence(base: float, extra: float) -> None:
    combined = combine_scores([base, extra])
    assert combined + 1e-12 >= combine_scores([base])
    assert combined + 1e-12 >= combine_scores([extra])
