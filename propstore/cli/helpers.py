"""Shared helpers for CLI subcommands."""

from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn, TypedDict

import click

from propstore.core.scalars import ScalarValue

if TYPE_CHECKING:
    from pathlib import Path

    from propstore.repository import Repository


class CliContext(TypedDict, total=False):
    """Typed shape of the Click root context object (``ctx.obj``).

    The root group stores a lazily-resolved repository handle under ``repo``;
    ``init`` instead stores the resolved start directory under ``start``. Both
    keys are optional because the two top-level flows populate different members.
    """

    repo: "Repository"
    start: "Path | None"
    traceback: bool


# -- Key=value parsing ------------------------------------------------


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
        parsed[key] = coerce_cli_scalar(value) if coerce else value
    return parsed, remaining


def coerce_cli_scalar(value: str) -> ScalarValue:
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


# -- Exit codes -------------------------------------------------------

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_VALIDATION = 2


class PropstoreClickError(click.ClickException):
    """Click-rendered CLI failure with an explicit exit code."""

    def __init__(self, message: object, *, exit_code: int = EXIT_ERROR) -> None:
        super().__init__(str(message))
        self.exit_code = exit_code


def require_repo(obj: CliContext) -> "Repository":
    """Return the repository handle attached to the Click context object.

    The root group stores the handle lazily, so this returns it untouched (a
    later attribute access on the owner side resolves it). It only fails when a
    command runs without the root group having attached a handle at all.
    """
    repo = obj.get("repo")
    if repo is None:
        raise RuntimeError("CLI context has no repository handle")
    return repo


def fail(message: object, *, exit_code: int = EXIT_ERROR) -> NoReturn:
    raise PropstoreClickError(message, exit_code=exit_code)


def exit_with_code(code: int) -> NoReturn:
    raise click.exceptions.Exit(code)
