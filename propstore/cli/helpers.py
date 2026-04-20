"""Shared helpers for CLI subcommands."""
from __future__ import annotations

from typing import NoReturn

import click

# ── Key=value parsing ────────────────────────────────────────────────

def parse_kv_pairs(
    args: tuple[str, ...] | list[str],
    *,
    coerce: bool = False,
) -> tuple[dict[str, object], list[str]]:
    """Parse ``key=value`` arguments into a dict.

    Returns ``(parsed_dict, remaining)`` where *remaining* holds every
    element of *args* that did not contain ``=``.

    Parameters
    ----------
    coerce:
        When ``True``, apply basic scalar coercion (booleans, ints,
        floats) to values.  When ``False`` (the default), values stay
        as plain strings.
    """
    parsed: dict[str, object] = {}
    remaining: list[str] = []
    for arg in args:
        if "=" not in arg:
            remaining.append(arg)
            continue
        key, _, value = arg.partition("=")
        parsed[key] = _coerce_cli_scalar(value) if coerce else value
    return parsed, remaining


def _coerce_cli_scalar(value: str) -> object:
    """Coerce basic CLI scalars while leaving ordinary strings untouched."""
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    signless = value.lstrip("+-")
    if signless.isdigit():
        try:
            return int(value)
        except ValueError:
            pass

    try:
        if any(ch in value for ch in (".", "e", "E")):
            return float(value)
    except ValueError:
        pass

    return value


# ── Exit codes ───────────────────────────────────────────────────────

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_VALIDATION = 2


class PropstoreClickError(click.ClickException):
    """Click-rendered CLI failure with an explicit exit code."""

    def __init__(self, message: object, *, exit_code: int = EXIT_ERROR) -> None:
        super().__init__(str(message))
        self.exit_code = exit_code


def fail(message: object, *, exit_code: int = EXIT_ERROR) -> NoReturn:
    raise PropstoreClickError(message, exit_code=exit_code)


def exit_with_code(code: int) -> NoReturn:
    raise click.exceptions.Exit(code)
