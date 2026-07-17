"""Export CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ontolog.cli.options import STORE_OPTION_HELP
from ontolog.cli.output import echo_status
from ontolog.config import default_config
from ontolog.errors import ExportError
from ontolog.export.formats import ExportFormat
from ontolog.export.graphml import export_neo4j_csv
from ontolog.export.options import ExportOptions
from ontolog.export.registry import export_domain_model, parse_export_format
from ontolog.inference import build_domain_model
from ontolog.models.domain import ProbabilisticDomainModel


def export(
    format_name: Annotated[str, typer.Argument(help="Export format name.")],
    store_path: Annotated[
        Path,
        typer.Option("--store", help=STORE_OPTION_HELP),
    ] = Path("ontolog.db"),
    include_all: Annotated[
        bool,
        typer.Option("--all", help="Include ineligible claims."),
    ] = False,
    provenance: Annotated[
        bool,
        typer.Option("--provenance", help="Include provenance in supported formats."),
    ] = False,
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", help="Write multi-file exports to this directory."),
    ] = None,
) -> None:
    """Export the aggregated domain model from a template store."""
    try:
        export_format = parse_export_format(format_name)
    except ExportError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    config = default_config()
    model = build_domain_model(store_path, config=config)
    options = ExportOptions(
        include_ineligible=include_all,
        include_provenance=provenance,
    )

    if export_format == ExportFormat.NEO4J_CSV:
        _export_neo4j_csv(model, options=options, output_dir=output_dir)
        return

    try:
        payload = export_domain_model(model, export_format, options=options)
    except ExportError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(payload, nl=False)


def _export_neo4j_csv(
    model: ProbabilisticDomainModel,
    *,
    options: ExportOptions,
    output_dir: Path | None,
) -> None:
    try:
        bundle = export_neo4j_csv(model, options=options)
    except ExportError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    if output_dir is None:
        typer.echo(bundle.nodes, nl=False)
        typer.echo("---")
        typer.echo(bundle.relationships, nl=False)
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    nodes_path = output_dir / "nodes.csv"
    relationships_path = output_dir / "relationships.csv"
    nodes_path.write_text(bundle.nodes, encoding="utf-8")
    relationships_path.write_text(bundle.relationships, encoding="utf-8")
    echo_status(f"wrote {nodes_path} and {relationships_path}")
