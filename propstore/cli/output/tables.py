"""Small stable table renderer for command output."""

from __future__ import annotations

from collections.abc import Sequence

from propstore.cli.output.console import emit


def emit_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[object]],
    *,
    empty_message: str | None = None,
    indent: str = "",
    show_header_when_empty: bool = False,
) -> None:
    if not rows:
        if show_header_when_empty:
            emit(indent + "  ".join(str(header) for header in headers))
        if empty_message is not None:
            emit(empty_message)
        return

    widths = [
        max(len(str(header)), *(len(str(row[index])) for row in rows))
        for index, header in enumerate(headers)
    ]
    emit(
        indent
        + "  ".join(str(header).ljust(widths[index]) for index, header in enumerate(headers))
    )
    emit(indent + "  ".join("-" * width for width in widths))
    for row in rows:
        emit(indent + "  ".join(str(value).ljust(widths[index]) for index, value in enumerate(row)))
