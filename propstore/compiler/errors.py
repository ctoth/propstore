"""Compiler workflow error type."""

from __future__ import annotations

from propstore.semantic_passes.types import PassDiagnostic


class CompilerWorkflowError(Exception):
    """Raised when a compiler workflow hits a blocking (abort-class) failure.

    The Z1 discipline (gaps.md, PLAN.md §12.1) splits failures: a schema-
    structural / msgspec-undecodable document, or a form/concept/context
    validation failure, ABORTS the build with this error. Semantic claim and
    stance invalidity is *quarantined* (a blocked row plus a diagnostic), never
    aborted — so this error never carries a claim's semantic diagnostics.

    ``messages`` holds the abort-class :class:`PassDiagnostic` set so the CLI can
    present them; ``summary`` is the one-line headline.
    """

    def __init__(self, summary: str, messages: tuple[PassDiagnostic, ...] = ()) -> None:
        super().__init__(summary)
        self.summary = summary
        self.messages = messages
