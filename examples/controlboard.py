"""Programmatic API usage: infer domain model from controlboard fixture."""

from __future__ import annotations

from pathlib import Path

from ontolog import infer
from ontolog.export import ExportFormat, ExportOptions, export_domain_model


def main() -> None:
    """Run the library infer API and print a markdown summary."""
    fixture = Path(__file__).parent.parent / "tests/fixtures/controlboard.log"
    store_path = Path("example_output.db")

    model = infer(fixture, store_path)
    markdown = export_domain_model(
        model,
        ExportFormat.MARKDOWN,
        options=ExportOptions(),
    )
    print(markdown)

    store_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
