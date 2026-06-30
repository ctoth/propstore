"""``pks rule`` — read projections over the DeLP rule families.

Thin Click adapters (CLAUDE.md "CLI adapter discipline"): the read commands
project directly over the
:class:`~propstore.families.rules.DefeasibleRule` and
:class:`~propstore.families.rules.RuleSuperiority` family stores
(``repo.families.defeasible_rule`` / ``repo.families.rule_superiority``). No rule
view or filtering logic lives here.

This package ``__init__`` owns the ``rule`` Click group; the sibling ``display``
module is imported at the bottom so it can attach commands via ``@rule.command``.
Rule authoring (add / remove / superiority mutation) has no owner in the rewrite
app layer, and the LLM rule-extraction proposal path is Phase 10-4, so no
``mutation`` module is built here — fabricating a mutation command with no owner is
out of scope.
"""
from __future__ import annotations

import click


@click.group()
def rule() -> None:
    """Read views over authored DeLP rules and rule superiorities."""


# Import the command module last so it can attach to the ``rule`` group.
from propstore.cli.rule import display  # noqa: E402

__all__ = ["display", "rule"]
