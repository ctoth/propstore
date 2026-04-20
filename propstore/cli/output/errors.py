"""Error output helpers for CLI adapters."""

from __future__ import annotations

from propstore.cli.output.console import emit_error


def emit_prefixed_error(message: object) -> None:
    emit_error(f"ERROR: {message}")
