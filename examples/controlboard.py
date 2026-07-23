"""Programmatic API usage: infer domain model from controlboard fixture."""

from __future__ import annotations

from pathlib import Path

from ontolog import infer


def main() -> None:
    """Run the library infer API and print a markdown summary."""
    fixture = Path(__file__).parent.parent / "tests/fixtures/controlboard.log"

    output = infer(fixture, format="markdown")
    print(output.artifact)


if __name__ == "__main__":
    main()
