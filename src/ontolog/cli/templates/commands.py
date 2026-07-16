"""Templates CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ontolog.cli.options import STORE_OPTION_HELP
from ontolog.cli.output import echo_status, render_template_table
from ontolog.config import OntologConfig
from ontolog.ingestion import IngestOptions, LogFormat, ingest_path
from ontolog.storage import SqliteTemplateStore
from ontolog.templates import ExtractOptions, TemplateExtractor


def templates(
    path: Annotated[
        Path,
        typer.Argument(help="Log file, directory of log files, or '-' for stdin."),
    ],
    store_path: Annotated[
        Path,
        typer.Option("--store", help=STORE_OPTION_HELP),
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
