"""Typer CLI entry point."""

from __future__ import annotations

from typing import Annotated

import typer

from ontolog import __version__
from ontolog.cli.export import export
from ontolog.cli.graph import graph
from ontolog.cli.infer import infer_command
from ontolog.cli.ingest import ingest
from ontolog.cli.logging import setup_cli_logging
from ontolog.cli.templates import templates

app = typer.Typer(
    name="ontolog",
    help="Probabilistic domain-model inference from application logs.",
    no_args_is_help=True,
    add_completion=False,
)

app.command("ingest")(ingest)
app.command("templates")(templates)
app.command("graph")(graph)
app.command("export")(export)
app.command("infer")(infer_command)


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


if __name__ == "__main__":
    app()
