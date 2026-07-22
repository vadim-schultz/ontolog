"""Infer CLI command."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ontolog import infer
from ontolog.cli.options import STORE_OPTION_HELP
from ontolog.cli.output import echo_status
from ontolog.errors import OntologError
from ontolog.ingestion.formats import LogFormat


def infer_command(
    path: Annotated[Path, typer.Argument(help="Log file or directory path.")],
    store_path: Annotated[
        Path,
        typer.Option("--store", help=STORE_OPTION_HELP),
    ] = Path("ontolog.db"),
    format_name: Annotated[
        str | None,
        typer.Option("--format", help="Log format (auto-detected by default)."),
    ] = None,
    fresh: Annotated[
        bool,
        typer.Option("--fresh/--no-fresh", help="Clear store before extraction."),
    ] = True,
) -> None:
    """Infer domain model from log source."""
    try:
        log_format = LogFormat[format_name.upper()] if format_name else LogFormat.AUTO
        model = infer(path, store_path, format=log_format, fresh=fresh)
    except OntologError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    echo_status(
        f"Inferred: {len(model.entities)} entities, "
        f"{len(model.events)} events, {len(model.fields)} fields"
    )
