"""Ingest- and build-time CEL expression validation.

A single reusable validator that rejects CEL expressions which fail the
condition-ir type-checker (the most important case being a *structural* concept
used inside a quantitative/temporal expression) before they can reach the
sidecar, conflict detection, or Z3 translation. It composes condition-ir's own
``check_cel_expression`` directly — there is no propstore CEL front-end.

Two surfaces consume it: the source-authoring boundary (a later phase) and the
compiler pre-build pass (:mod:`propstore.compiler.workflows`), which iterates a
repository's claims and contexts and aborts the build early if any CEL
expression references a structural concept. The validator raises
:class:`CelIngestValidationError` (a ``ValueError`` subclass) whose message names
the offending artifact, carrier field, and expression index — preserving the
condition front-end error text inside a contextual envelope.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from cel_parser.ast import (
    Call,
    Comprehension,
    CreateList,
    CreateMap,
    CreateStruct,
    Expr,
    Ident,
    ParseError,
    Select,
)
from cel_parser.parser import parse
from condition_ir import KindType, check_cel_expression

if TYPE_CHECKING:
    from condition_ir import ConceptInfo


class CelIngestValidationError(ValueError):
    """Raised when a CEL expression is invalid at ingest or pre-build time.

    A ``ValueError`` subclass so existing ``except ValueError`` handlers surface
    the error cleanly.
    """


@dataclass(frozen=True)
class CelExpressionLocation:
    """Identifies one CEL expression inside a larger artifact.

    ``artifact_label`` is a human-readable string naming the owning artifact
    (e.g. ``"claim 'c6'"``, ``"context 'ctx_popadad'"``). ``field`` names the
    carrier (``"condition"``, ``"assumption"``). ``index`` is the zero-based
    position within the carrier tuple (the rendered message adds 1 so it reads
    naturally).
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

    Delegates to condition-ir's ``check_cel_expression`` and wraps any reported
    errors with a message that includes ``location`` context. A structural
    concept used in a typed expression is one specific failure the checker
    reports; other CEL type errors surface identically.
    """

    errors = check_cel_expression(expression, registry)
    if errors:
        detail = "; ".join(str(error) for error in errors)
        raise CelIngestValidationError(
            f"{location.render()} = {expression!r}: {detail}"
        )


def validate_cel_expressions(
    items: Iterable[tuple[str, CelExpressionLocation]],
    registry: Mapping[str, "ConceptInfo"],
) -> None:
    """Validate ``(expression, location)`` pairs; raise on the first failure.

    Deliberately fail-fast so an author sees one clear error at a time; the
    caller invokes this before any write-side operation.
    """

    for expression, location in items:
        if not expression:
            continue
        validate_cel_expression(expression, registry, location=location)


def _collect_identifiers(node: Expr, names: set[str]) -> None:
    """Walk a parsed CEL expression, collecting identifier names.

    Recurses over the concrete cel-parser node types (rather than reflecting over
    dataclass fields) so the traversal stays fully typed. Literal nodes carry no
    identifiers and terminate the recursion.
    """

    if isinstance(node, Ident):
        names.add(node.name)
    elif isinstance(node, Select):
        _collect_identifiers(node.operand, names)
    elif isinstance(node, Call):
        if node.target is not None:
            _collect_identifiers(node.target, names)
        for arg in node.args:
            _collect_identifiers(arg, names)
    elif isinstance(node, CreateList):
        for element in node.elements:
            _collect_identifiers(element, names)
    elif isinstance(node, CreateMap):
        for entry in node.entries:
            _collect_identifiers(entry.key, names)
            _collect_identifiers(entry.value, names)
    elif isinstance(node, CreateStruct):
        for struct_entry in node.entries:
            _collect_identifiers(struct_entry.value, names)
    elif isinstance(node, Comprehension):
        _collect_identifiers(node.iter_range, names)
        _collect_identifiers(node.accu_init, names)
        _collect_identifiers(node.loop_condition, names)
        _collect_identifiers(node.loop_step, names)
        _collect_identifiers(node.result, names)


def iter_cel_identifiers(expression: str) -> frozenset[str]:
    """Return the concept identifiers a CEL expression references.

    Parses the expression with condition-ir's own parser and walks the AST for
    identifier nodes. A syntactically invalid expression yields the empty set —
    a parse error is general claim semantic invalidity (quarantined by the claim
    pipeline), not the structural-concept architectural invariant this feeds.
    """

    try:
        ast = parse(expression)
    except ParseError:
        return frozenset()
    names: set[str] = set()
    _collect_identifiers(ast, names)
    return frozenset(names)


def structural_concepts_in_expression(
    expression: str,
    registry: Mapping[str, "ConceptInfo"],
) -> tuple[str, ...]:
    """Return the structural concepts a CEL expression references, if any.

    A structural concept must never appear in a CEL expression — it is a hard
    architectural invariant (it breaks Z3 translation), distinct from a general
    CEL type error. The compiler treats this as an abort-class failure, while
    ordinary CEL type errors quarantine. Identifiers that do not resolve to a
    structural concept (unknown names, quantities, categories) are ignored here;
    those are reported by the ordinary CEL type-checker.
    """

    structural: list[str] = []
    for name in sorted(iter_cel_identifiers(expression)):
        info = registry.get(name)
        if info is not None and info.kind == KindType.STRUCTURAL:
            structural.append(name)
    return tuple(structural)


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
                artifact_label=artifact_label, field="condition", index=index
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
                artifact_label=artifact_label, field="assumption", index=index
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
                artifact_label=artifact_label, field="condition", index=index
            ),
        )


__all__ = [
    "CelIngestValidationError",
    "CelExpressionLocation",
    "validate_cel_expression",
    "validate_cel_expressions",
    "iter_cel_identifiers",
    "structural_concepts_in_expression",
    "iter_claim_condition_expressions",
    "iter_context_assumption_expressions",
    "iter_lifting_rule_condition_expressions",
]
