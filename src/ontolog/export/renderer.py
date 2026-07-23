"""Renderer adapters for export formats."""

from __future__ import annotations

import io
import json
from typing import Protocol, TypeVar

import networkx as nx

from ontolog.types import JsonValue

T_contra = TypeVar("T_contra", contravariant=True)


class Renderer(Protocol[T_contra]):
    """Render a typed payload into a serialized export artifact."""

    def render(self, payload: T_contra) -> str:
        """Serialize ``payload`` to a string."""
        ...


class JsonRenderer:
    """Render JSON-serializable payloads as indented JSON."""

    def render(self, payload: JsonValue) -> str:
        """Return ``payload`` as indented JSON."""
        return json.dumps(payload, indent=2)


class GraphmlRenderer:
    """Render NetworkX graphs as GraphML XML."""

    def render(self, payload: nx.DiGraph) -> str:
        """Return GraphML XML for ``payload``."""
        buffer = io.StringIO()
        for line in nx.generate_graphml(payload):
            buffer.write(line)
        return buffer.getvalue()
