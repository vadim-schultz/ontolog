"""Export the evidence graph as JSON."""

from __future__ import annotations

from dataclasses import dataclass, field

from ontolog.evidence.graph import EvidenceGraph
from ontolog.export.formats import ExportFormat
from ontolog.export.options import ExportOptions
from ontolog.export.rendering.renderer import JsonRenderer, Renderer
from ontolog.models.domain import ProbabilisticDomainModel
from ontolog.models.finding import ProviderInput
from ontolog.types import JsonValue


@dataclass(frozen=True)
class EvidenceGraphExporter:
    """Export the evidence graph as JSON."""

    format_name: ExportFormat = ExportFormat.EVIDENCE_GRAPH
    renderer: Renderer[JsonValue] = field(default_factory=JsonRenderer)

    def export(
        self,
        model: ProbabilisticDomainModel,
        *,
        graph: EvidenceGraph,
        data: ProviderInput,
        options: ExportOptions,
    ) -> str:
        """Serialize the evidence graph as JSON."""
        del model, data, options
        return self.renderer.render(graph.to_payload())
