"""Ingest-time CEL expression validation.

This module provides a single reusable validator that rejects CEL
expressions which reference structural concepts (or are otherwise
malformed per the CEL type-checker) at the authoring boundary, before
they can reach the sidecar, conflict detection, or Z3 translation.

Three call sites consume this validator:

1. ``propstore.source.claims.commit_source_claims_batch`` — for each
   claim in a batch, every CEL expression in ``conditions[]`` is
   checked against the repository's concept registry.
2. ``propstore.app.contexts.add_context`` — each CEL assumption on
   a new context is checked against the repository's concept registry.
3. ``propstore.compiler.workflows.validate_repository`` /
   ``build_repository`` — a pre-validation pass iterates master's
   claims and contexts and rejects the build early if any CEL
   expression references a structural concept.

The validator raises ``CelIngestValidationError`` (a ``ValueError``
subclass) with a clear message that names the offending artifact,
condition index, and concept. This preserves the exact text emitted by
``propstore.cel_checker.check_cel_expr`` while wrapping it in a
contextual envelope.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from propstore.cel_checker import ConceptInfo


class CelIngestValidationError(ValueError):
    """Raised when a CEL expression is invalid at ingest time.

    A ``ValueError`` subclass so existing ``except ValueError`` handlers
    (notably ``propstore.cli.source.batch``) surface the error cleanly.
    """


@dataclass(frozen=True)
class CelExpressionLocation:
    """Identifies one CEL expression inside a larger artifact.

    ``artifact_label`` is a human-readable string naming the owning
    artifact (e.g. ``"claim 'claim6' in paper 'Gaziano_2018'"``,
    ``"context 'ctx_belch_2008_popadad'"``).

    ``field`` names the carrier (e.g. ``"condition"``, ``"assumption"``).

    ``index`` is the zero-based position of the expression within the
    carrier tuple (the emitted message adds 1 so it reads naturally).
    """

    artifact_label: str
    field: str
    index: int

    def render(self) -> str:
        return f"{self.artifact_label}: {self.field}[{self.index}]"


def validate_cel_expression(
    expression: str,
    registry: Mapping[str, "ConceptInfo"],
    *,
    location: CelExpressionLocation,
) -> None:
    """Type-check one CEL expression; raise ``CelIngestValidationError`` on failure.

    Delegates to ``propstore.cel_checker.check_cel_expr`` and wraps its
    ``ValueError`` with a message that includes ``location`` context.
    Structural concept rejection is one specific failure the checker
    reports; other CEL type errors are surfaced identically.
    """
    # Import inside the function to avoid a module-load cycle: cel_checker
    # is a heavy module and this file is imported from CLI paths that do
    # not always need it.
    from propstore.cel_checker import check_cel_expr

    try:
        check_cel_expr(expression, registry)
    except ValueError as exc:
        raise CelIngestValidationError(
            f"{location.render()} = {expression!r}: {exc}"
        ) from exc


def validate_cel_expressions(
    items: Iterable[tuple[str, CelExpressionLocation]],
    registry: Mapping[str, "ConceptInfo"],
) -> None:
    """Validate a sequence of expressions. Raises on the first failure.

    ``items`` is an iterable of ``(expression, location)`` pairs. The
    function is deliberately fail-fast: the first structural-concept
    offense aborts ingest so the author sees one error at a time. No
    claim in the batch is committed when any expression fails — the
    caller must invoke this before any write-side operation.
    """
    for expression, location in items:
        if not isinstance(expression, str) or not expression:
            continue
        validate_cel_expression(expression, registry, location=location)


def iter_claim_condition_expressions(
    claim_conditions: Sequence[str],
    *,
    artifact_label: str,
) -> Iterable[tuple[str, CelExpressionLocation]]:
    """Yield ``(expression, location)`` pairs for every claim condition."""
    for index, expression in enumerate(claim_conditions):
        yield (
            expression,
            CelExpressionLocation(
                artifact_label=artifact_label,
                field="condition",
                index=index,
            ),
        )


def iter_context_assumption_expressions(
    assumptions: Sequence[str],
    *,
    artifact_label: str,
) -> Iterable[tuple[str, CelExpressionLocation]]:
    """Yield ``(expression, location)`` pairs for every context assumption."""
    for index, expression in enumerate(assumptions):
        yield (
            expression,
            CelExpressionLocation(
                artifact_label=artifact_label,
                field="assumption",
                index=index,
            ),
        )


def iter_lifting_rule_condition_expressions(
    conditions: Sequence[str],
    *,
    artifact_label: str,
) -> Iterable[tuple[str, CelExpressionLocation]]:
    """Yield ``(expression, location)`` pairs for every lifting-rule condition."""
    for index, expression in enumerate(conditions):
        yield (
            expression,
            CelExpressionLocation(
                artifact_label=artifact_label,
                field="condition",
                index=index,
            ),
        )


__all__ = [
    "CelIngestValidationError",
    "CelExpressionLocation",
    "validate_cel_expression",
    "validate_cel_expressions",
    "iter_claim_condition_expressions",
    "iter_context_assumption_expressions",
    "iter_lifting_rule_condition_expressions",
]
