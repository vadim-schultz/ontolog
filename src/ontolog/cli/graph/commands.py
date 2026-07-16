"""Graph CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ontolog.cli.options import STORE_OPTION_HELP
from ontolog.cli.output import echo_status
from ontolog.evidence import load_evidence_graph


def graph(
    show: Annotated[
        bool,
        typer.Option("--show", help="Print graph summary."),
    ] = False,
    store_path: Annotated[
        Path,
        typer.Option("--store", help=STORE_OPTION_HELP),
    ] = Path("ontolog.db"),
) -> None:
    """Inspect the evidence graph (stub)."""
    if not show:
        typer.echo("Use --show to print graph summary.", err=True)
        raise typer.Exit(code=1)

    evidence_graph = load_evidence_graph(store_path)
    echo_status(f"nodes: {evidence_graph.node_count()}, edges: {evidence_graph.edge_count()}")
