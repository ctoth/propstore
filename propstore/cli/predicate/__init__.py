"""``pks predicate`` — read views over the predicate family plus the predicate
proposal record/promote path.

Thin Click adapters (CLAUDE.md "CLI adapter discipline"). The read side projects
directly over the :class:`~propstore.families.predicates.Predicate` family store
(``repo.families.predicate``); the proposal side wires to the recorder/promoter
owners in :mod:`propstore.proposals_predicates`
(:func:`~propstore.proposals_predicates.propose_predicates`,
:func:`~propstore.proposals_predicates.plan_predicate_proposal_promotion`,
:func:`~propstore.proposals_predicates.promote_predicate_proposals`). No predicate
read view, proposal recording, or promotion math lives here.

This package ``__init__`` owns the ``predicate`` Click group; the sibling command
modules are imported at the bottom so they can attach commands via
``@predicate.command``. The LLM predicate-extraction path that *produces* the
declarations is the agent-workflow layer's concern (Phase 10-4) and is not built
here — ``predicate declare`` records explicitly-supplied (``stated``) declarations.
"""

from __future__ import annotations

import click


@click.group()
def predicate() -> None:
    """Read views over predicates and the predicate proposal record/promote path."""


# Import the command modules last so they can attach to the ``predicate`` group.
from propstore.cli.predicate import display, mutation  # noqa: E402

__all__ = ["display", "mutation", "predicate"]
