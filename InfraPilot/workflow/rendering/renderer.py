"""Minimal template rendering helpers for workflow-generated files."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_TEMPLATE_ROOT = Path(__file__).resolve().parents[1] / "templates"
_ENVIRONMENT = Environment(
    loader=FileSystemLoader(_TEMPLATE_ROOT),
    autoescape=False,
    keep_trailing_newline=True,
)


def render_template(template_name: str, variables: dict[str, object]) -> str:
    """Render a template from the workflow template directory."""

    template = _ENVIRONMENT.get_template(template_name)
    return template.render(**variables)

