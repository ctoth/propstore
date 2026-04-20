"""Rich-backed console emission for the CLI layer."""

from __future__ import annotations

import sys
from typing import TextIO

from rich.console import Console


def _console(stderr: bool) -> Console:
    stream: TextIO = sys.stderr if stderr else sys.stdout
    return Console(
        file=stream,
        force_terminal=False,
        color_system=None,
        highlight=False,
        width=240,
    )


def emit(message: object = "", *, err: bool = False, nl: bool = True) -> None:
    """Emit one terminal line through the shared Rich console.

    Markup is disabled so existing literal CLI output remains stable under
    tests and command-line capture. Styling can be layered later by passing
    Rich renderables through dedicated helpers rather than raw strings.
    """
    _console(err).print(
        "" if message is None else str(message),
        markup=False,
        highlight=False,
        soft_wrap=True,
        end="\n" if nl else "",
    )


def emit_error(message: object) -> None:
    emit(message, err=True)


def emit_warning(message: object) -> None:
    emit(message, err=True)


def emit_success(message: object) -> None:
    emit(message)
