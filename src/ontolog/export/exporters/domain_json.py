"""Export the full probabilistic domain model as JSON."""

from __future__ import annotations

from dataclasses import dataclass, field

from ontolog.export.formats import ExportFormat
from ontolog.export.options import ExportOptions
from ontolog.export.rendering.renderer import JsonRenderer, Renderer
from ontolog.models.domain import ProbabilisticDomainModel
from ontolog.types import JsonValue


@dataclass(frozen=True)
class DomainJsonExporter:
    """Export the unfiltered domain model as JSON."""

    format_name: ExportFormat = ExportFormat.DOMAIN_JSON
    renderer: Renderer[JsonValue] = field(default_factory=JsonRenderer)

    def export(
        self,
        model: ProbabilisticDomainModel,
        *,
        options: ExportOptions,
    ) -> str:
        """Serialize the full domain model as JSON."""
        del options
        return self.renderer.render(model.model_dump(mode="json"))
