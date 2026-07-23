"""Export a combined domain model, evidence graph, and template summary."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast

from ontolog.evidence.graph import EvidenceGraph
from ontolog.export.formats import ExportFormat
from ontolog.export.options import ExportOptions
from ontolog.export.renderer import JsonRenderer, Renderer
from ontolog.models.domain import ProbabilisticDomainModel
from ontolog.models.finding import ProviderInput
from ontolog.models.template import Template
from ontolog.types import JsonValue


def _template_summary(templates: tuple[Template, ...]) -> list[dict[str, JsonValue]]:
    return [
        {
            "id": template.id,
            "template": template.template,
            "occurrence_count": template.occurrence_count,
            "examples": list(template.examples),
        }
        for template in templates
    ]


@dataclass(frozen=True)
class FullBundleExporter:
    """Export domain model, evidence graph, and template summary as JSON."""

    format_name: ExportFormat = ExportFormat.FULL
    renderer: Renderer[JsonValue] = field(default_factory=JsonRenderer)

    def export(
        self,
        model: ProbabilisticDomainModel,
        *,
        graph: EvidenceGraph,
        data: ProviderInput,
        options: ExportOptions,
    ) -> str:
        """Serialize the full inference bundle as JSON."""
        del options
        payload: dict[str, JsonValue] = {
            "schema_version": "1",
            "domain_model": model.model_dump(mode="json"),
            "evidence_graph": graph.to_payload(),
            "templates": cast("JsonValue", _template_summary(data.templates)),
        }
        return self.renderer.render(payload)
