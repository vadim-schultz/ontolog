"""CLI logging setup."""

from __future__ import annotations

import logging

from rich.logging import RichHandler


def setup_cli_logging(*, level: int = logging.INFO) -> None:
    """Configure stdlib logging with RichHandler for CLI use."""
    root = logging.getLogger()
    if root.handlers:
        return

    handler = RichHandler(show_path=False, rich_tracebacks=True)
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[handler],
    )
