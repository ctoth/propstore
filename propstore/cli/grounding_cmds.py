"""Click adapters for inspecting the grounded rule theory.

Thin wrappers over :mod:`propstore.grounding.loading` and
:mod:`propstore.grounding.inspection`: gather the authored grounding substrate,
ground it into the non-committal :class:`~propstore.grounding.bundle.GroundedRulesBundle`,
and render the surface state, facts, marking sections, and arguments. No grounding
logic lives here (CLAUDE.md "CLI adapter discipline").

The ``explain`` subcommand from the legacy surface is intentionally absent: the
rewrite grounding owner exposes no dialectical-tree / prose explanation builder,
so there is no owner to adapt (reported as a gap rather than reimplemented).
"""

from __future__ import annotations

from collections.abc import Mapping

import click
import gunray
from gunray.types import Atom, AtomTerm, Constant

from propstore.cli.helpers import CliContext, require_repo
from propstore.cli.output import emit, emit_section
from propstore.grounding.bundle import SECTION_NAMES, SectionRows
from propstore.grounding.inspection import (
    format_argument,
    format_ground_atom,
    format_ground_rule,
    grounding_surface_state,
    parse_query_atom,
)
from propstore.grounding.loading import build_grounded_bundle, load_grounding_repo


@click.group()
def grounding() -> None:
    """Inspect the grounded rule theory directly."""


@grounding.command("status")
@click.pass_obj
def grounding_status(obj: CliContext) -> None:
    """Report the grounding surface state and per-section fact counts."""
    repo = require_repo(obj)
    grounding_repo = load_grounding_repo(repo)
    state = grounding_surface_state(grounding_repo)
    emit(f"Predicates: {len(grounding_repo.predicates)}")
    emit(f"Rules: {len(grounding_repo.rules)}")
    emit(f"Grounding surface: {state}")
    if state == "invalid":
        emit("Rules are declared but no predicates exist; grounding cannot proceed.")
        return
    bundle = build_grounded_bundle(grounding_repo)
    emit(f"Facts: {len(bundle.source_facts)}")
    for section in SECTION_NAMES:
        count = sum(len(rows) for rows in bundle.sections[section].values())
        emit(f"  {section}: {count}")


@grounding.command("show")
@click.pass_obj
def grounding_show(obj: CliContext) -> None:
    """Show grounded facts, grounded rule instances, and marking sections."""
    repo = require_repo(obj)
    grounding_repo = load_grounding_repo(repo)
    if grounding_surface_state(grounding_repo) == "invalid":
        emit("Grounding surface: invalid (rules declared but no predicates exist).")
        return
    bundle = build_grounded_bundle(grounding_repo)

    facts = tuple(format_ground_atom(fact) for fact in bundle.source_facts)
    emit_section(f"Facts ({len(facts)}):", facts if facts else ("<empty>",))

    inspection = bundle.grounding_inspection
    rule_instances = (
        tuple(
            format_ground_rule(instance) for instance in inspection.all_rule_instances
        )
        if inspection is not None
        else ()
    )
    emit_section(
        f"Grounded rules ({len(rule_instances)}):",
        rule_instances if rule_instances else ("<empty>",),
    )

    emit("Sections:")
    for section in SECTION_NAMES:
        emit(f"  {section}:")
        atoms = _section_atoms(bundle.sections[section])
        if not atoms:
            emit("    <empty>")
            continue
        for atom in atoms:
            emit(f"    {atom}")


@grounding.command("query")
@click.argument("atom")
@click.pass_obj
def grounding_query(obj: CliContext, atom: str) -> None:
    """Report which marking sections a query atom appears in."""
    repo = require_repo(obj)
    parsed = parse_query_atom(atom)
    grounding_repo = load_grounding_repo(repo)
    matched: tuple[str, ...] = ()
    if grounding_surface_state(grounding_repo) == "ready":
        bundle = build_grounded_bundle(grounding_repo)
        matched = tuple(
            section
            for section in SECTION_NAMES
            if _atom_in_section(parsed, bundle.sections[section])
        )
    emit(atom)
    emit(f"  status: {', '.join(matched)}" if matched else "  status: absent")


@grounding.command("arguments")
@click.pass_obj
def grounding_arguments(obj: CliContext) -> None:
    """Show the arguments enumerated over the grounded theory."""
    repo = require_repo(obj)
    grounding_repo = load_grounding_repo(repo)
    if grounding_surface_state(grounding_repo) == "invalid":
        emit("Grounding surface: invalid (rules declared but no predicates exist).")
        return
    bundle = build_grounded_bundle(grounding_repo, return_arguments=True)
    arguments = tuple(format_argument(argument) for argument in bundle.arguments)
    emit_section(
        f"Arguments ({len(arguments)}):",
        arguments if arguments else ("<empty>",),
    )


def _section_atoms(inner: Mapping[str, SectionRows]) -> tuple[str, ...]:
    return tuple(
        sorted(
            format_ground_atom(gunray.GroundAtom(predicate=predicate, arguments=row))
            for predicate, rows in inner.items()
            for row in rows
        )
    )


def _atom_in_section(parsed: Atom, inner: Mapping[str, SectionRows]) -> bool:
    rows = inner.get(parsed.predicate)
    if not rows:
        return False
    return any(_row_matches_terms(row, parsed.terms) for row in rows)


def _row_matches_terms(
    row: tuple[gunray.Scalar, ...], terms: tuple[AtomTerm, ...]
) -> bool:
    if len(row) != len(terms):
        return False
    return all(
        term.value == value
        for value, term in zip(row, terms, strict=True)
        if isinstance(term, Constant)
    )
