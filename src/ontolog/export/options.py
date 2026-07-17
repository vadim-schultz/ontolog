"""Export option models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ExportOptions(BaseModel):
    """Options controlling domain model export behavior."""

    model_config = ConfigDict(frozen=True)

    include_ineligible: bool = False
    include_provenance: bool = False
