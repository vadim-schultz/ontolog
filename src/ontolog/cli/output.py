"""User-facing CLI output on stderr (stdout is for machine-readable payloads)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from rich.console import Console
from rich.table import Table

from ontolog.models.template import Template

stderr_console = Console(stderr=True)
stdout_console = Console()


def echo_status(message: str) -> None:
    """Print a dim status line to stderr."""
    stderr_console.print(message, style="dim")


def _format_timestamp(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.isoformat()


def _truncate(value: str, *, max_length: int = 80) -> str:
    if len(value) <= max_length:
        return value
    return value[: max_length - 1] + "…"


def _add_template_row(table: Table, template: Template) -> None:
    """Append one template summary row to ``table``."""
    example = template.examples[0] if template.examples else ""
    table.add_row(
        template.id,
        str(template.occurrence_count),
        _truncate(template.template),
        _format_timestamp(template.first_seen),
        _format_timestamp(template.last_seen),
        _truncate(example),
    )


def render_template_table(
    templates: Sequence[Template],
    *,
    console: Console | None = None,
) -> None:
    """Render a summary table of mined templates."""
    table = Table(show_header=True, header_style="bold")
    table.add_column("ID")
    table.add_column("Count", justify="right")
    table.add_column("Template")
    table.add_column("First")
    table.add_column("Last")
    table.add_column("Example")

    for template in templates:
        _add_template_row(table, template)

    (console or stdout_console).print(table)
