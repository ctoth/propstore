"""Reusable section and key/value rendering helpers."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from propstore.cli.output.console import emit


def emit_section(title: str, lines: Iterable[object] = (), *, err: bool = False) -> None:
    if title:
        emit(title, err=err)
    for line in lines:
        emit(f"  {line}", err=err)


def emit_key_values(rows: Sequence[tuple[str, object | None]], *, indent: str = "  ") -> None:
    for key, value in rows:
        if value is None:
            continue
        emit(f"{indent}{key}: {value}")
