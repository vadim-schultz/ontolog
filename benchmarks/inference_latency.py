#!/usr/bin/env python3
"""Benchmark inference latency."""

from __future__ import annotations

import time
from pathlib import Path

from ontolog import infer


def benchmark_inference(log_path: Path) -> dict[str, float]:
    """Return end-to-end inference timing for ``log_path``."""
    start = time.perf_counter()
    output = infer(log_path, format="markdown")
    total_ms = (time.perf_counter() - start) * 1000

    return {
        "total_ms": total_ms,
        "entity_count": float(len(output.model.entities)),
        "event_count": float(len(output.model.events)),
        "field_count": float(len(output.model.fields)),
    }


def main() -> None:
    """Benchmark committed fixtures."""
    fixtures = Path("tests/fixtures")
    for fixture in ("controlboard.log", "order_lifecycle.log"):
        result = benchmark_inference(fixtures / fixture)
        print(
            f"{fixture}: {result['total_ms']:.1f}ms total, "
            f"{int(result['entity_count'])} entities, {int(result['event_count'])} events"
        )


if __name__ == "__main__":
    main()
