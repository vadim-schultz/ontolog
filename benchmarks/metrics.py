"""Clustering metrics for template accuracy benchmarks."""

from __future__ import annotations


def compute_clustering_f1(
    predicted: list[str],
    ground_truth: list[str],
) -> dict[str, float]:
    """Compute pairwise precision, recall, and F1 for cluster assignments."""
    if len(predicted) != len(ground_truth):
        message = "predicted and ground_truth must have the same length"
        raise ValueError(message)

    true_positive = 0
    false_positive = 0
    false_negative = 0
    total = len(predicted)

    for left in range(total):
        for right in range(left + 1, total):
            predicted_same = predicted[left] == predicted[right]
            truth_same = ground_truth[left] == ground_truth[right]
            if predicted_same and truth_same:
                true_positive += 1
            elif predicted_same:
                false_positive += 1
            elif truth_same:
                false_negative += 1

    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative
    precision = true_positive / precision_denominator if precision_denominator else 0.0
    recall = true_positive / recall_denominator if recall_denominator else 0.0
    f1_denominator = precision + recall
    f1 = (2 * precision * recall / f1_denominator) if f1_denominator else 0.0

    return {"precision": precision, "recall": recall, "f1": f1}
