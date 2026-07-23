"""Jinja2 rendering for text export formats."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TypeVar

from jinja2 import Environment, PackageLoader, select_autoescape

from ontolog.export.rendering.formatting import confidence_suffix

T = TypeVar("T", bound=Mapping[str, object])


def _confidence_pct(value: float) -> str:
    return f"{value * 100:.0f}%"


def _build_environment() -> Environment:
    environment = Environment(
        loader=PackageLoader("ontolog.export.rendering", "templates"),
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=select_autoescape(enabled_extensions=()),
    )
    environment.filters["confidence_pct"] = _confidence_pct
    environment.filters["confidence_suffix"] = confidence_suffix
    return environment


_ENVIRONMENT = _build_environment()


@dataclass(frozen=True)
class Jinja2Renderer:
    """Render export payloads through a packaged Jinja2 template."""

    template_name: str

    def render(self, payload: Mapping[str, object]) -> str:
        """Render ``payload`` as template context."""
        template = _ENVIRONMENT.get_template(self.template_name)
        return template.render(**payload)
