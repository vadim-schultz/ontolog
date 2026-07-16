"""Typer CLI entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ontolog import __version__
from ontolog.cli.logging import setup_cli_logging
from ontolog.cli.output import echo_status
from ontolog.ingestion import IngestOptions, LogFormat, ingest_path

app = typer.Typer(
    name="ontolog",
    help="Probabilistic domain-model inference from application logs.",
    no_args_is_help=True,
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = None,
) -> None:
    """Ontolog — probabilistic domain-model inference from application logs."""
    setup_cli_logging()


@app.command("ingest")
def ingest(
    path: Annotated[
        Path,
        typer.Argument(help="Log file, directory of log files, or '-' for stdin."),
    ],
    log_format: Annotated[
        LogFormat,
        typer.Option("--format", help="Input log format."),
    ] = LogFormat.AUTO,
    preprocessor: Annotated[
        list[str] | None,
        typer.Option("--preprocessor", help="Additional preprocessors after strip."),
    ] = None,
    skip_errors: Annotated[
        bool,
        typer.Option("--skip-errors", help="Skip unparseable lines instead of failing."),
    ] = False,
    limit: Annotated[
        int | None,
        typer.Option("--limit", help="Maximum number of records to emit."),
    ] = None,
) -> None:
    """Normalize raw logs to JSON Lines on stdout."""
    source: Path | str = "-" if str(path) == "-" else path
    options = IngestOptions(
        format=log_format,
        preprocessors=tuple(preprocessor or ()),
        skip_errors=skip_errors,
        limit=limit,
    )

    count = 0
    for record in ingest_path(source, options):
        typer.echo(record.model_dump_json())
        count += 1

    echo_status(f"ingested {count} records from {path}")
