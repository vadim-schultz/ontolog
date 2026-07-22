#!/usr/bin/env python3
"""Benchmark template extraction throughput."""

from __future__ import annotations

import time
from pathlib import Path

from ontolog.storage import SqliteTemplateStore
from ontolog.templates import ExtractOptions, extract_templates


def benchmark_file(log_path: Path) -> dict[str, float]:
    """Return throughput metrics for ``log_path``."""
    line_count = sum(1 for _ in log_path.open(encoding="utf-8"))
    start = time.perf_counter()
    with SqliteTemplateStore(":memory:") as store:
        extract_templates(log_path, ExtractOptions(), store=store)
        template_count = len(store.list_templates())
    elapsed = time.perf_counter() - start

    return {
        "lines_per_sec": line_count / elapsed if elapsed else 0.0,
        "templates_per_sec": template_count / elapsed if elapsed else 0.0,
        "elapsed_sec": elapsed,
        "line_count": float(line_count),
        "template_count": float(template_count),
    }


def main() -> None:
    """Benchmark committed fixtures."""
    fixtures = Path("tests/fixtures")
    for fixture in ("controlboard.log", "loghub/apache_2k.log"):
        result = benchmark_file(fixtures / fixture)
        print(
            f"{fixture}: {result['lines_per_sec']:.0f} lines/sec, "
            f"{int(result['template_count'])} templates in {result['elapsed_sec']:.2f}s"
        )


if __name__ == "__main__":
    main()
