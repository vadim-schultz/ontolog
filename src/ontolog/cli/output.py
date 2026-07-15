"""User-facing CLI output on stderr (stdout is for machine-readable payloads)."""

from __future__ import annotations

from rich.console import Console

stderr_console = Console(stderr=True)


def echo_status(message: str) -> None:
    """Print a dim status line to stderr."""
    stderr_console.print(message, style="dim")
