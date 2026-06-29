"""A small read/inspection surface over the grounding substrate and results.

This is the behavioral subset the inspection view needs: classifying whether a
grounding surface is absent / invalid / ready, parsing a query atom through
gunray, and formatting ground atoms, ground rule instances, and arguments for
display. It owns no CLI rendering — the CLI adapter calls these and prints.
"""

from __future__ import annotations

from typing import Literal

import gunray
from gunray.types import Atom

from propstore.grounding.loading import GroundingRepo

GroundingSurfaceState = Literal["none", "invalid", "ready"]


def grounding_surface_state(repo: GroundingRepo) -> GroundingSurfaceState:
    """Classify a grounding surface.

    ``none`` — no predicates and no rules; ``invalid`` — rules present but no
    predicates declared; ``ready`` — predicates declared.
    """

    if not repo.predicates:
        return "invalid" if repo.rules else "none"
    return "ready"


def parse_query_atom(text: str) -> Atom:
    """Parse a query atom string through gunray's own parser."""

    stripped = text.strip()
    if stripped == "":
        raise ValueError("query atom text must be non-empty")
    return gunray.parse_atom_text(stripped)


def format_ground_atom(atom: gunray.GroundAtom) -> str:
    """Render a ground atom as ``pred(a, b)`` or bare ``pred`` for arity 0."""

    if not atom.arguments:
        return atom.predicate
    rendered = ", ".join(str(argument) for argument in atom.arguments)
    return f"{atom.predicate}({rendered})"


def format_ground_rule(instance: gunray.GroundRuleInstance) -> str:
    """Render a ground rule instance as ``id: head <- b1, b2`` (or just the head)."""

    head = format_ground_atom(instance.head)
    if not instance.body:
        return f"{instance.rule_id}: {head}"
    body = ", ".join(format_ground_atom(literal) for literal in instance.body)
    return f"{instance.rule_id}: {head} <- {body}"


def format_argument(argument: gunray.Argument) -> str:
    """Render an argument as ``{rule ids} |- conclusion``."""

    rule_ids = ", ".join(sorted(rule.rule_id for rule in argument.rules))
    conclusion = format_ground_atom(argument.conclusion)
    if rule_ids == "":
        return f"|- {conclusion}"
    return f"{{{rule_ids}}} |- {conclusion}"
