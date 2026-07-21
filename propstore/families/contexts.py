"""First-class ``ist(c, p)`` contexts, lifting rules, and lifting materialization.

A *context* is a flat first-class qualifier (McCarthy/Guha ``ist(c, p)``): a
logical object carrying structured *assumptions* (CEL), *parameters*, and a
*perspective*. There is deliberately **no visibility hierarchy and no ancestry** —
the only cross-context flow is through authored *lifting rules*. This module owns
the ONE canonical ``Context`` charter, the ONE ``LiftingRule`` charter, and the
``LiftingMaterialization`` projection charter; the git documents, the SQL sidecar
columns, and the contracts all fall out of field annotations exactly as for
:class:`~propstore.families.claims.Claim`.

Discipline (CLAUDE.md, PLAN.md §12):

* ONE spelling per thing. ``LiftingRule`` is a single charter used both as the
  stored document and by the lifting algebra in
  :mod:`propstore.context_lifting`; conditions are RAW authored CEL source
  strings, lowered to condition-ir only at evaluation time (no second spelling).
* No visibility hierarchy: a context document with an ``inherits`` or ``excludes``
  field is rejected at decode (``forbid_unknown_fields``); the sidecar has no
  exclusion table.
* Non-commitment: :meth:`ContextRepository.build_sidecar` NEVER filters. A
  ``BLOCKED`` or ``UNKNOWN`` lifting decision lands as a
  ``lifting_materialization`` row with its full provenance columns, exactly like
  a ``LIFTED`` one. Which decisions are *visible* is a render-time choice.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Protocol

from quire.charter_class import CharterDoc, charter, charter_field
from quire.charters import charter_catalog
from quire.family_store import DocumentFamilyStore
from quire.git_store import GitStore
from quire.sqlalchemy_schema import SqlAlchemySchema, build_sqlalchemy_schema
from quire.sqlalchemy_store import (
    create_sqlalchemy_store,
    readonly_session,
    writable_session,
)
from sqlalchemy import select

if TYPE_CHECKING:
    from propstore.context_lifting import LiftingDecision


class ContextStatus(StrEnum):
    """Authoring lifecycle status of a context (render-time visibility only)."""

    AUTHORED = "authored"
    DRAFT = "draft"
    BLOCKED = "blocked"


class LiftingMode(StrEnum):
    """The kind of cross-context lift an authored rule performs."""

    BRIDGE = "bridge"
    SPECIALIZATION = "specialization"
    DECONTEXTUALIZATION = "decontextualization"


class LiftingDecisionStatus(StrEnum):
    """The outcome of evaluating a lifting rule for a proposition.

    ``LIFTED`` — the rule's CEL gate is satisfied (or has no conditions) and no
    exception targets the lift. ``EXCEPTED`` — the gate holds but an authored
    :class:`LiftingException` targets the lift; per Bozzato 2018 (Def 12) the
    exception overrides only if its clashing set is established, so resolution
    is deferred to the argumentation framework (the lift's defeasible rule is
    still projected and the exception contributes defeats only from arguments
    concluding the clashing-set claims). ``BLOCKED`` — the gate is
    unsatisfiable. ``UNKNOWN`` — the gate could not be decided (no solver
    available, a solver ``UNKNOWN``, or an untranslatable condition); honest
    ignorance, distinct from blocked and from absent.
    """

    LIFTED = "lifted"
    EXCEPTED = "excepted"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


@charter(
    key="context",
    name="context",
    contract_version="2026.06.29",
    placement="context",
    identity_field="context_id",
    semantic="propstore.context",
)
class Context(CharterDoc):
    """A first-class ``ist(c, p)`` context.

    ``assumptions`` are RAW authored CEL source strings scoped to this context;
    they are NOT inherited from any other context (there is no ancestry).
    ``parameters`` carry the context's bound parameters (e.g. ``speaker``);
    ``perspective`` is the ``ist`` viewpoint. ``forbid_unknown_fields`` (from
    ``CharterDoc``) rejects the removed visibility-hierarchy keys ``inherits`` /
    ``excludes`` at decode.
    """

    context_id: Annotated[str, charter_field(primary_key=True)]
    name: str
    status: ContextStatus = ContextStatus.AUTHORED
    description: str | None = None
    assumptions: Annotated[tuple[str, ...], charter_field(json=True)] = ()
    parameters: Annotated[dict[str, str], charter_field(json=True)] = {}
    perspective: str | None = None


@charter(
    key="lifting_rule",
    name="lifting_rule",
    contract_version="2026.06.29",
    placement="lifting_rule",
    identity_field="rule_id",
    semantic="propstore.lifting_rule",
)
class LiftingRule(CharterDoc):
    """An authored rule that licenses lifting a proposition between two contexts.

    ``conditions`` are RAW authored CEL source strings forming the lift's gate;
    they are lowered to condition-ir only when a decision is evaluated
    (:mod:`propstore.context_lifting`). This is the single canonical lifting-rule
    type — there is no separate runtime spelling.
    """

    rule_id: Annotated[str, charter_field(primary_key=True)]
    source_context: str
    target_context: str
    conditions: Annotated[tuple[str, ...], charter_field(json=True)] = ()
    mode: LiftingMode = LiftingMode.BRIDGE
    justification: str | None = None


@charter(
    key="lifting_materialization",
    name="lifting_materialization",
    contract_version="2026.06.29",
    placement="lifting_materialization",
    identity_field="materialization_id",
    semantic="propstore.lifting_materialization",
)
class LiftingMaterialization(CharterDoc):
    """A recorded lifting decision — the non-commitment inspection record.

    EVERY decision (``LIFTED`` / ``BLOCKED`` / ``UNKNOWN``) is projected as one
    of these rows with its full provenance columns. The render layer decides
    which are visible; the build never drops a non-lifted decision.
    """

    materialization_id: Annotated[str, charter_field(primary_key=True)]
    # A lifting materialization is a non-commitment INSPECTION record: every
    # decision (LIFTED / BLOCKED / UNKNOWN) is projected, including ones whose
    # rule / context / proposition references do not (yet) resolve. These
    # references are therefore deliberately NOT declared as foreign keys — a hard
    # referential constraint would reject a blocked/unknown decision row, which
    # is exactly the drop the non-commitment discipline forbids.
    rule_id: str
    source_context_id: str
    target_context_id: str
    proposition_id: str
    status: LiftingDecisionStatus
    mode: LiftingMode = LiftingMode.BRIDGE
    exception_id: str | None = None
    justification: str | None = None
    clashing_set: Annotated[tuple[str, ...], charter_field(json=True)] = ()
    diagnostic: str | None = None


@dataclass(frozen=True)
class _StoreOwner:
    """Placement owner for the document stores (mirrors other repositories)."""

    branch: str = "master"


class _ContextRow(Protocol):
    context_id: str
    name: str
    status: ContextStatus | str
    description: str | None
    assumptions: tuple[str, ...]
    parameters: dict[str, str]
    perspective: str | None


class _LiftingRuleRow(Protocol):
    rule_id: str
    source_context: str
    target_context: str
    conditions: tuple[str, ...]
    mode: LiftingMode | str
    justification: str | None


class _MaterializationRow(Protocol):
    materialization_id: str
    rule_id: str
    source_context_id: str
    target_context_id: str
    proposition_id: str
    status: LiftingDecisionStatus | str
    mode: LiftingMode | str
    exception_id: str | None
    justification: str | None
    clashing_set: tuple[str, ...]
    diagnostic: str | None


def _row_to_context(row: _ContextRow) -> Context:
    status = (
        row.status
        if isinstance(row.status, ContextStatus)
        else ContextStatus(row.status)
    )
    return Context(
        context_id=row.context_id,
        name=row.name,
        status=status,
        description=row.description,
        assumptions=tuple(row.assumptions),
        parameters=dict(row.parameters),
        perspective=row.perspective,
    )


def _row_to_lifting_rule(row: _LiftingRuleRow) -> LiftingRule:
    mode = row.mode if isinstance(row.mode, LiftingMode) else LiftingMode(row.mode)
    return LiftingRule(
        rule_id=row.rule_id,
        source_context=row.source_context,
        target_context=row.target_context,
        conditions=tuple(row.conditions),
        mode=mode,
        justification=row.justification,
    )


def _row_to_materialization(row: _MaterializationRow) -> LiftingMaterialization:
    status = (
        row.status
        if isinstance(row.status, LiftingDecisionStatus)
        else LiftingDecisionStatus(row.status)
    )
    mode = row.mode if isinstance(row.mode, LiftingMode) else LiftingMode(row.mode)
    return LiftingMaterialization(
        materialization_id=row.materialization_id,
        rule_id=row.rule_id,
        source_context_id=row.source_context_id,
        target_context_id=row.target_context_id,
        proposition_id=row.proposition_id,
        status=status,
        mode=mode,
        exception_id=row.exception_id,
        justification=row.justification,
        clashing_set=tuple(row.clashing_set),
        diagnostic=row.diagnostic,
    )


def _materialization_id(decision: LiftingDecision) -> str:
    """A stable id for a materialized decision.

    Keyed by rule + proposition + status so that distinct recomputations of the
    same lift (e.g. an earlier ``UNKNOWN`` and a later ``LIFTED``) coexist as
    separate inspection rows rather than collapsing — the non-commitment
    discipline at the materialization surface.
    """

    return f"{decision.rule_id}::{decision.proposition_id}::{decision.status.value}"


class ContextRepository:
    """Author contexts and lifting rules to git; project them into a sidecar.

    Same shape as :class:`~propstore.families.claims.ClaimRepository`: a
    charter-driven git store per family plus a charter-derived sqlite sidecar.
    Lifting *materialization* rows are not authored — they are computed lifting
    decisions handed to :meth:`build_sidecar`, which projects every one of them.
    """

    def __init__(self, backend: GitStore | None = None) -> None:
        store_backend = backend if backend is not None else GitStore.init_memory()
        self._context_store = DocumentFamilyStore(
            owner=_StoreOwner(),
            backend=store_backend,
            codec=Context.__charter__.document_codec(),
        )
        self._rule_store = DocumentFamilyStore(
            owner=_StoreOwner(),
            backend=store_backend,
            codec=LiftingRule.__charter__.document_codec(),
        )
        self._context_family = Context.__charter__.family.artifact_family
        self._rule_family = LiftingRule.__charter__.family.artifact_family

    def author(self, context: Context, *, message: str) -> str:
        """Store the RAW authored context keyed by ``context_id``; return sha."""

        return self._context_store.save(
            self._context_family, context.context_id, context, message=message
        )

    def author_lifting_rule(self, rule: LiftingRule, *, message: str) -> str:
        """Store an authored lifting rule keyed by ``rule_id``; return sha."""

        return self._rule_store.save(
            self._rule_family, rule.rule_id, rule, message=message
        )

    def get(self, context_id: str) -> Context | None:
        return self._context_store.load(self._context_family, context_id)

    def get_lifting_rule(self, rule_id: str) -> LiftingRule | None:
        return self._rule_store.load(self._rule_family, rule_id)

    def iter_contexts(self) -> Iterator[Context]:
        for handle in self._context_store.iter_handles(self._context_family):
            yield handle.document

    def iter_lifting_rules(self) -> Iterator[LiftingRule]:
        for handle in self._rule_store.iter_handles(self._rule_family):
            yield handle.document

    def build_sidecar(
        self,
        path: Path,
        *,
        lifting_decisions: Iterable[LiftingDecision] = (),
    ) -> SqlAlchemySchema:
        """Project every context, lifting rule, and lifting decision into sqlite.

        Never filters: a ``DRAFT`` context and a ``BLOCKED`` / ``UNKNOWN`` lifting
        decision land as rows alongside clean ones. Visibility is decided later,
        at render.
        """

        schema = build_sqlalchemy_schema(
            charter_catalog(
                Context.__charter__,
                LiftingRule.__charter__,
                LiftingMaterialization.__charter__,
            )
        )
        create_sqlalchemy_store(path, schema)
        with writable_session(path, schema) as session:
            for context in self.iter_contexts():
                session.add_family(
                    "context",
                    {
                        "context_id": context.context_id,
                        "name": context.name,
                        "status": context.status,
                        "description": context.description,
                        "assumptions": context.assumptions,
                        "parameters": context.parameters,
                        "perspective": context.perspective,
                    },
                )
            for rule in self.iter_lifting_rules():
                session.add_family(
                    "lifting_rule",
                    {
                        "rule_id": rule.rule_id,
                        "source_context": rule.source_context,
                        "target_context": rule.target_context,
                        "conditions": rule.conditions,
                        "mode": rule.mode,
                        "justification": rule.justification,
                    },
                )
            for decision in lifting_decisions:
                session.add_family(
                    "lifting_materialization",
                    {
                        "materialization_id": _materialization_id(decision),
                        "rule_id": decision.rule_id,
                        "source_context_id": decision.source_context,
                        "target_context_id": decision.target_context,
                        "proposition_id": decision.proposition_id,
                        "status": decision.status,
                        "mode": decision.mode,
                        "exception_id": decision.exception_id,
                        "justification": decision.justification,
                        "clashing_set": decision.clashing_set,
                        "diagnostic": decision.diagnostic,
                    },
                )
            session.commit()
        return schema

    def render_contexts(self, path: Path, schema: SqlAlchemySchema) -> list[Context]:
        model = schema.model("context")
        with readonly_session(path, schema) as session:
            rows = list(session.scalars(select(model)))
        return [_row_to_context(row) for row in rows]

    def render_lifting_rules(
        self, path: Path, schema: SqlAlchemySchema
    ) -> list[LiftingRule]:
        model = schema.model("lifting_rule")
        with readonly_session(path, schema) as session:
            rows = list(session.scalars(select(model)))
        return [_row_to_lifting_rule(row) for row in rows]

    def render_materializations(
        self, path: Path, schema: SqlAlchemySchema
    ) -> list[LiftingMaterialization]:
        """Every projected lifting decision row, including BLOCKED / UNKNOWN."""

        model = schema.model("lifting_materialization")
        with readonly_session(path, schema) as session:
            rows = list(session.scalars(select(model)))
        return [_row_to_materialization(row) for row in rows]
