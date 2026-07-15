"""Sphinx configuration for Ontolog."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

project = "ontolog"
author = "Vadim Schultz"
copyright = "2026, Vadim Schultz"
release = "0.0.1"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
]

html_theme = "sphinx_rtd_theme"
html_static_path: list[str] = []

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
suppress_warnings = ["sphinx_autodoc_typehints.forward_reference"]

autodoc_member_order = "bysource"
typehints_defaults = "comma"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
}
