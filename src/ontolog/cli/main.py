"""Typer CLI entry point."""

from __future__ import annotations

from typing import Annotated

import typer

from ontolog import __version__
from ontolog.cli.logging import setup_cli_logging

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
    _version: Annotated[
        bool | None,
        typer.Option("--version", callback=_version_callback, is_eager=True),
    ] = None,
) -> None:
    """Ontolog — probabilistic domain-model inference from application logs."""
    setup_cli_logging()
