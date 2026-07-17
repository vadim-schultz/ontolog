"""Optional export extra detection."""

from __future__ import annotations

_GRAPH_EXTRA_STATE = {"enabled": False}


def graph_extra_enabled() -> bool:
    """Return whether the optional ``[graph]`` extra is enabled."""
    return bool(_GRAPH_EXTRA_STATE["enabled"])


def enable_graph_extra() -> None:
    """Enable graph extra features (used when ``[graph]`` is installed)."""
    _GRAPH_EXTRA_STATE["enabled"] = True
