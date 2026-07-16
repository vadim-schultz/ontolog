"""Typer CLI entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ontolog import __version__
from ontolog.cli.logging import setup_cli_logging
from ontolog.cli.output import echo_status, render_template_table
from ontolog.config import OntologConfig
from ontolog.ingestion import IngestOptions, LogFormat, ingest_path
from ontolog.storage import SqliteTemplateStore
from ontolog.templates import ExtractOptions, TemplateExtractor

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


@app.command("templates")
def templates(
    path: Annotated[
        Path,
        typer.Argument(help="Log file, directory of log files, or '-' for stdin."),
    ],
    store_path: Annotated[
        Path,
        typer.Option("--store", help="SQLite database path for template persistence."),
    ] = Path("ontolog.db"),
    no_store: Annotated[
        bool,
        typer.Option("--no-store", help="Do not persist templates to SQLite."),
    ] = False,
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
        typer.Option("--limit", help="Maximum number of records to process."),
    ] = None,
) -> None:
    """Extract log templates and print a summary table."""
    source: Path | str = "-" if str(path) == "-" else path
    options = ExtractOptions(
        format=log_format,
        preprocessors=tuple(preprocessor or ()),
        skip_errors=skip_errors,
        limit=limit,
    )
    config = OntologConfig(storage_path=store_path)
    store: SqliteTemplateStore | None = None
    if not no_store:
        store = SqliteTemplateStore(store_path)

    try:
        ingest_options = IngestOptions(
            format=options.format,
            preprocessors=options.preprocessors,
            skip_errors=options.skip_errors,
            limit=options.limit,
        )
        extractor = TemplateExtractor(config=config, store=store)
        record_count = 0
        for record in ingest_path(source, ingest_options):
            extractor.ingest(record)
            record_count += 1

        mined = extractor.templates()
        render_template_table(mined)
        echo_status(f"extracted {len(mined)} templates from {record_count} records")
    finally:
        if store is not None:
            store.close()
