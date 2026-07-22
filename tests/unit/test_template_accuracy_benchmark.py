"""Tests for template accuracy benchmark helpers."""

from __future__ import annotations

from pathlib import Path

from metrics import compute_clustering_f1
from template_accuracy import (
    benchmark_dataset,
    compute_metrics,
    load_loghub2k_labels,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "loghub"


def test_parse_loghub2k_labels() -> None:
    labels = load_loghub2k_labels(FIXTURES / "apache_2k_labels.csv")
    assert labels
    first_key = next(iter(labels))
    assert isinstance(first_key, str)
    assert labels[first_key].startswith("E")


def test_compute_accuracy_metrics() -> None:
    predicted = ["a", "a", "b", "b"]
    ground_truth = ["x", "x", "y", "z"]
    metrics = compute_metrics(predicted, ground_truth)

    assert metrics["precision"] == compute_clustering_f1(predicted, ground_truth)["precision"]
    assert 0.0 <= metrics["f1"] <= 1.0


def test_benchmark_runs_on_fixture() -> None:
    metrics = benchmark_dataset(
        FIXTURES / "apache_2k.log",
        FIXTURES / "apache_2k_labels.csv",
    )
    assert {"precision", "recall", "f1"} <= metrics.keys()
    assert metrics["f1"] >= 0.0
