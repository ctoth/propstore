"""YAML output helpers for CLI commands with structured payloads."""

from __future__ import annotations

from quire.documents import render_yaml_value

from propstore.cli.output.console import emit


def emit_yaml(value: object, *, rstrip: bool = False) -> None:
    rendered = render_yaml_value(value)
    emit(rendered.rstrip() if rstrip else rendered, nl=not rendered.endswith("\n"))
