"""Infer CLI command."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ontolog import infer
from ontolog.cli.output import echo_status
from ontolog.errors import OntologError
from ontolog.export.formats import ExportFormat
from ontolog.export.options import ExportOptions
from ontolog.ingestion.formats import LogFormat
from ontolog.pipeline import InferOutput
from ontolog.templates import ExtractOptions


def _build_export_options(
    *,
    include_all: bool,
    provenance: bool,
) -> ExportOptions:
    """Return export options from CLI flags."""
    return ExportOptions(
        include_ineligible=include_all,
        include_provenance=provenance,
    )


def _build_extract_options(
    *,
    log_format: LogFormat,
    preprocessor: list[str] | None,
    skip_errors: bool,
    limit: int | None,
) -> ExtractOptions:
    """Return extraction options from CLI flags."""
    return ExtractOptions(
        format=log_format,
        preprocessors=tuple(preprocessor or ()),
        skip_errors=skip_errors,
        limit=limit,
    )


def _echo_summary(output: InferOutput) -> None:
    """Print inference summary to stderr."""
    echo_status(
        f"Inferred: {len(output.model.entities)} entities, "
        f"{len(output.model.events)} events, {len(output.model.fields)} fields"
    )


def infer_command(
    path: Annotated[
        Path,
        typer.Argument(help="Log file, directory of log files, or '-' for stdin."),
    ],
    export_format: Annotated[
        ExportFormat,
        typer.Option("--format", help="Export format."),
    ],
    log_format: Annotated[
        LogFormat,
        typer.Option("--log-format", help="Input log format."),
    ] = LogFormat.AUTO,
    include_all: Annotated[
        bool,
        typer.Option("--all", help="Include ineligible claims."),
    ] = False,
    provenance: Annotated[
        bool,
        typer.Option("--provenance", help="Include provenance in supported formats."),
    ] = False,
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
    """Infer a domain model from logs and export it."""
    source: Path | str = "-" if str(path) == "-" else path
    export_options = _build_export_options(include_all=include_all, provenance=provenance)
    extract_options = _build_extract_options(
        log_format=log_format,
        preprocessor=preprocessor,
        skip_errors=skip_errors,
        limit=limit,
    )

    try:
        output = infer(
            source,
            format=export_format,
            export_options=export_options,
            extract_options=extract_options,
        )
    except OntologError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    _echo_summary(output)
    typer.echo(output.artifact, nl=False)
