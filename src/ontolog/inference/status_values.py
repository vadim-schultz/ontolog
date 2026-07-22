"""Extract lifecycle status labels from templates and occurrences."""

from __future__ import annotations

from ontolog.models.template import Template, TemplateOccurrence

_STATUS_PARAM = "status"


def status_label_from_template(template_text: str) -> str | None:
    """Extract a lifecycle status label from template text."""
    first_token = template_text.split(maxsplit=1)[0] if template_text else ""
    if first_token.startswith("Order"):
        return first_token.removeprefix("Order").lower()
    for token in template_text.split():
        if token.startswith("status="):
            return token.removeprefix("status=").strip("<>").lower()
    if " status=" in template_text:
        _, remainder = template_text.split(" status=", maxsplit=1)
        return remainder.split()[0].strip("<>").lower()
    return None


def collect_status_values(
    occurrences: tuple[TemplateOccurrence, ...],
    templates: tuple[Template, ...],
) -> set[str]:
    """Return all observed lifecycle status labels."""
    values: set[str] = set()
    templates_by_id = {template.id: template for template in templates}
    for occurrence in occurrences:
        for param in occurrence.parameters:
            if param.name == _STATUS_PARAM:
                values.add(param.value)
        template = templates_by_id.get(occurrence.template_id)
        if template is not None:
            label = status_label_from_template(template.template)
            if label is not None:
                values.add(label)
    for template in templates:
        label = status_label_from_template(template.template)
        if label is not None:
            values.add(label)
    return values
