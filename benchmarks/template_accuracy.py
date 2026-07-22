#!/usr/bin/env python3
"""Benchmark template extraction accuracy vs LogHub-2.0 labels."""

from __future__ import annotations

import csv
from pathlib import Path

from metrics import compute_clustering_f1
from ontolog.storage import SqliteTemplateStore
from ontolog.templates import ExtractOptions, extract_templates


def load_loghub2k_labels(csv_path: Path) -> dict[str, str]:
    """Parse LogHub-2.0 CSV into ``{content: event_id}``."""
    labels: dict[str, str] = {}
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            labels[row["Content"]] = row["EventId"]
    return labels


def collect_assignments(
    log_path: Path,
    labels_path: Path,
) -> tuple[list[str], list[str]]:
    """Return predicted and ground-truth cluster ids for labeled messages."""
    ground_truth = load_loghub2k_labels(labels_path)
    with SqliteTemplateStore(":memory:") as store:
        extract_templates(log_path, ExtractOptions(), store=store)
        occurrences = store.list_occurrences()

    predicted: list[str] = []
    truth: list[str] = []
    for occurrence in occurrences:
        event_id = ground_truth.get(occurrence.message)
        if event_id is None:
            continue
        predicted.append(occurrence.template_id)
        truth.append(event_id)
    return predicted, truth


def compute_metrics(predicted: list[str], ground_truth: list[str]) -> dict[str, float]:
    """Compute precision, recall, and F1 for template clustering."""
    return compute_clustering_f1(predicted, ground_truth)


def benchmark_dataset(log_path: Path, labels_path: Path) -> dict[str, float]:
    """Run benchmark on a single dataset."""
    predicted, truth = collect_assignments(log_path, labels_path)
    return compute_metrics(predicted, truth)


def main() -> None:
    """Benchmark committed LogHub 2k fixtures."""
    fixtures = Path("tests/fixtures/loghub")
    datasets = (
        ("apache_2k.log", "apache_2k_labels.csv"),
        ("openssh_2k.log", "openssh_2k_labels.csv"),
    )
    for log_name, label_name in datasets:
        metrics = benchmark_dataset(fixtures / log_name, fixtures / label_name)
        print(
            f"{log_name}: P={metrics['precision']:.3f} "
            f"R={metrics['recall']:.3f} F1={metrics['f1']:.3f}"
        )


if __name__ == "__main__":
    main()
