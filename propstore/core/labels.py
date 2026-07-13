"""Core label types for the semantic kernel.

The ATMS label / environment / nogood antichain algebra is owned by the
``provenance-semiring`` package (it is a thin polynomial-native layer over the
provenance semiring). propstore imports those canonical types directly —
:class:`Label`, :class:`EnvironmentKey`, :class:`NogoodSet`,
:func:`combine_labels`, :func:`merge_labels`, :func:`normalize_environments`,
and :class:`JustificationRecord` — rather than carrying a second spelling.

This module re-exports them as the propstore-local door, adds the
:class:`SupportQuality` grading and :data:`SupportMetadata` mapping the
structured-projection and analyzer-result layers attach to projected supports,
and owns the deterministic JSON (de)serialization of a :class:`Label`. The
propstore-specific *meaning* of a label's variables (an assumption id versus a
context id, and the ``ps:source:*`` encoding) lives with the world-layer
engine, not here.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

from condition_ir import CelExpr, to_cel_expr, to_cel_exprs
from provenance_semiring import (
    EnvironmentKey,
    JustificationRecord,
    Label,
    NogoodSet,
    SourceVariableId,
    SupportQuality,
    combine_labels,
    merge_labels,
    normalize_environments,
)

from propstore.core.id_types import AssumptionId, ContextId, to_assumption_id, to_context_id

if TYPE_CHECKING:
    from propstore.core.environment import AssumptionRef

__all__ = [
    "EnvironmentKey",
    "JustificationRecord",
    "Label",
    "NogoodSet",
    "SourceVariableId",
    "SupportMetadata",
    "SupportQuality",
    "assumption_label",
    "assumption_variable",
    "binding_condition_to_cel",
    "cel_to_binding",
    "combine_labels",
    "compile_environment_assumptions",
    "context_label",
    "context_variable",
    "environment_assumption_ids",
    "environment_context_ids",
    "make_environment_key",
    "merge_labels",
    "normalize_environments",
]


SupportMetadata = Mapping[str, tuple["Label | None", SupportQuality]]



def binding_condition_to_cel(key: str, value: Any) -> CelExpr:
    """Render a query binding into the CEL string the world model reasons over."""

    if isinstance(value, bool):
        return to_cel_expr(f"{key} == {'true' if value else 'false'}")
    if isinstance(value, str):
        return to_cel_expr(f"{key} == '{value}'")
    return to_cel_expr(f"{key} == {value}")


_ASSUMPTION_VARIABLE_PREFIX = "ps:source:assumption:"
_CONTEXT_VARIABLE_PREFIX = "ps:source:context:"


def assumption_variable(assumption_id: AssumptionId | str) -> SourceVariableId:
    """Encode an assumption id as a provenance-polynomial indeterminate.

    The carved ``EnvironmentKey`` is generic over ``SourceVariableId``; propstore
    owns the *meaning* of a variable (assumption vs context) through this
    ``ps:source:*`` naming scheme (CLAUDE.md substrate boundary — the
    propstore-specific knowledge is supplied at the call site, not by wrapping the
    package). :func:`environment_assumption_ids` is the matching decode.
    """

    return SourceVariableId(f"{_ASSUMPTION_VARIABLE_PREFIX}{to_assumption_id(assumption_id)}")


def context_variable(context_id: ContextId | str) -> SourceVariableId:
    """Encode a context id as a provenance-polynomial indeterminate."""

    return SourceVariableId(f"{_CONTEXT_VARIABLE_PREFIX}{to_context_id(context_id)}")


def assumption_label(assumption_id: AssumptionId | str) -> Label:
    """A label whose single environment is the one supporting assumption."""

    return Label.from_variable(assumption_variable(assumption_id))


def context_label(context_id: ContextId | str) -> Label:
    """A label whose single environment is the one supporting context."""

    return Label.from_variable(context_variable(context_id))


def make_environment_key(
    *,
    assumption_ids: Sequence[AssumptionId | str] = (),
    context_ids: Sequence[ContextId | str] = (),
) -> EnvironmentKey:
    """Build an :class:`EnvironmentKey` from assumption and context ids.

    Each id is encoded to its ``ps:source:*`` ``SourceVariableId``; the carved
    ``EnvironmentKey`` then normalizes (dedups + sorts) the variable set.
    """

    variables = tuple(assumption_variable(value) for value in assumption_ids) + tuple(
        context_variable(value) for value in context_ids
    )
    return EnvironmentKey(variables)


def environment_assumption_ids(environment: EnvironmentKey) -> tuple[AssumptionId, ...]:
    """Decode the assumption ids carried by an environment's variables."""

    return tuple(
        to_assumption_id(str(variable)[len(_ASSUMPTION_VARIABLE_PREFIX) :])
        for variable in environment.variables
        if str(variable).startswith(_ASSUMPTION_VARIABLE_PREFIX)
    )


def environment_context_ids(environment: EnvironmentKey) -> tuple[ContextId, ...]:
    """Decode the context ids carried by an environment's variables."""

    return tuple(
        to_context_id(str(variable)[len(_CONTEXT_VARIABLE_PREFIX) :])
        for variable in environment.variables
        if str(variable).startswith(_CONTEXT_VARIABLE_PREFIX)
    )


def cel_to_binding(cel: str | CelExpr) -> tuple[str, Any] | None:
    """Reverse of :func:`binding_condition_to_cel`: parse ``key == value``.

    Returns ``None`` when the CEL is not a simple binding equality. Used by the
    world engine to project a queryable assumption back into a binding so a future
    replay can rebuild the bound world under it.
    """

    parts = str(cel).split(" == ", 1)
    if len(parts) != 2:
        return None
    key, raw = parts[0].strip(), parts[1].strip()
    if not key:
        return None
    if raw.startswith("'") and raw.endswith("'"):
        return (key, raw[1:-1])
    if raw == "true":
        return (key, True)
    if raw == "false":
        return (key, False)
    try:
        if "." in raw:
            return (key, float(raw))
        return (key, int(raw))
    except ValueError:
        return None


def _stable_id(kind: str, source: str, body: str) -> AssumptionId:
    """A deterministic assumption id over an assumption's kind/source/body."""

    digest = hashlib.sha256(f"{kind}\0{source}\0{body}".encode()).hexdigest()
    return to_assumption_id(f"{kind}:{source}:{digest}")


def compile_environment_assumptions(
    *,
    bindings: Mapping[str, Any],
    effective_assumptions: Sequence[str | CelExpr] = (),
    context_id: ContextId | str | None = None,
) -> tuple[AssumptionRef, ...]:
    """Compile bindings and inherited context assumptions into stable refs.

    Each binding becomes a ``binding`` assumption whose CEL is the rendered
    equality; each inherited context CEL becomes a ``context`` assumption. The
    result is ordered by ``assumption_id`` so the compiled frame is deterministic.
    """

    from propstore.core.environment import AssumptionRef

    compiled: list[AssumptionRef] = []

    for key in sorted(bindings):
        value = bindings[key]
        rendered_value = json.dumps(value, sort_keys=True, default=str)
        compiled.append(
            AssumptionRef(
                assumption_id=_stable_id("binding", key, rendered_value),
                kind="binding",
                source=key,
                cel=binding_condition_to_cel(key, value),
            )
        )

    normalized_context_id = None if context_id is None else to_context_id(context_id)
    context_source = str(normalized_context_id) if normalized_context_id is not None else "<context>"
    for cel in sorted(dict.fromkeys(to_cel_exprs(effective_assumptions))):
        compiled.append(
            AssumptionRef(
                assumption_id=_stable_id("context", context_source, str(cel)),
                kind="context",
                source=context_source,
                cel=cel,
            )
        )

    return tuple(sorted(compiled, key=lambda ref: ref.assumption_id))
