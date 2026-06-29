"""The authored DeLP/Datalog *rule* entities — Phase 4 charters + repository.

A *rule* is an authored DeLP rule: a head atom derived (strictly or defeasibly)
from a body of literals, plus the rule's *kind* (strict / defeasible / proper or
blocking defeater). A *rule superiority* is an authored ``superior > inferior``
priority between two rule ids. This module owns the ONE canonical
:class:`DefeasibleRule` and :class:`RuleSuperiority` charters and the small
nested authored shapes (:class:`Term`, :class:`Atom`, :class:`BodyLiteral`) the
rule head/body are built from.

Substrate boundary (CLAUDE.md, PLAN.md §12):

* The authored rule charter is named ``DefeasibleRule`` — deliberately NOT
  ``Rule`` — so it never collides with :class:`gunray.Rule` (the surface-syntax
  string rule the translator compiles to). There is ONE spelling per thing: the
  authored structured rule here, lowered to ``gunray.Rule`` strings at the
  grounding boundary (:mod:`propstore.grounding.translator`).
* ``Term`` / ``Atom`` / ``BodyLiteral`` are frozen ``msgspec.Struct`` shapes
  carried as charter ``json`` fields; the git document, the sidecar json columns,
  and the contract all fall out of the charter — there is no second spelling and
  no ``to_payload`` / ``coerce_`` conversion.
* Non-commitment: :meth:`RuleRepository.build_sidecar` NEVER filters.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal, Protocol

import msgspec
from quire.charter_class import CharterDoc, charter, charter_field
from quire.charters import charter_catalog
from quire.family_store import DocumentFamilyStore
from quire.git_store import GitStore
from quire.references import ForeignKeySpec
from quire.sqlalchemy_schema import SqlAlchemySchema, build_sqlalchemy_schema
from quire.sqlalchemy_store import create_sqlalchemy_store, readonly_session, writable_session

from propstore.families import SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION
from sqlalchemy import select

RuleKind = Literal["strict", "defeasible", "proper_defeater", "blocking_defeater"]
TermKind = Literal["var", "const"]
BodyLiteralKind = Literal["positive", "default_negated"]


class Term(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """A single term in an atom: a variable (``name``) or a constant (``value``).

    ``var`` terms carry a ``name``; ``const`` terms carry a ``value``. The
    grounding translator (:mod:`propstore.grounding.translator`) lowers each to
    gunray surface syntax.
    """

    kind: TermKind
    name: str | None = None
    value: str | int | float | bool | None = None


class Atom(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """A (possibly strongly-negated) predicate applied to ordered terms.

    ``negated`` is strong negation (``~``), distinct from default negation, which
    lives on a :class:`BodyLiteral`. An arity-0 atom carries no ``terms``.
    """

    predicate: str
    terms: tuple[Term, ...] = ()
    negated: bool = False


class BodyLiteral(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """A body literal: an atom held either positively or under default negation."""

    kind: BodyLiteralKind
    atom: Atom


@charter(
    key="defeasible_rule",
    name="defeasible_rule",
    contract_version="2026.06.29",
    placement="defeasible_rule",
    identity_field="rule_id",
    semantic="propstore.defeasible_rule",
)
class DefeasibleRule(CharterDoc):
    """An authored DeLP rule (the ONE canonical structured rule type).

    ``kind`` selects the rule's defeasibility class; ``head`` is the derived atom
    and ``body`` the literals it derives from. Lowered to :class:`gunray.Rule`
    strings only at grounding time — never mirrored.
    """

    rule_id: Annotated[str, charter_field(primary_key=True)]
    kind: RuleKind
    head: Annotated[Atom, charter_field(json=True)]
    body: Annotated[tuple[BodyLiteral, ...], charter_field(json=True)] = ()
    source: str | None = None
    authoring_group: str | None = None
    promoted_from_sha: str | None = None


@charter(
    key="rule_superiority",
    name="rule_superiority",
    contract_version="2026.06.29",
    placement="rule_superiority",
    identity_field="superiority_id",
    semantic="propstore.rule_superiority",
)
class RuleSuperiority(CharterDoc):
    """An authored ``superior_rule_id > inferior_rule_id`` priority."""

    superiority_id: Annotated[str, charter_field(primary_key=True)]
    superior_rule_id: Annotated[
        str,
        charter_field(
            foreign_key=ForeignKeySpec(
                name="rule_superiority_superior_rule",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="rule_superiority",
                source_field="superior_rule_id",
                target_family="defeasible_rule",
                target_field="rule_id",
            )
        ),
    ]
    inferior_rule_id: Annotated[
        str,
        charter_field(
            foreign_key=ForeignKeySpec(
                name="rule_superiority_inferior_rule",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="rule_superiority",
                source_field="inferior_rule_id",
                target_family="defeasible_rule",
                target_field="rule_id",
            )
        ),
    ]
    source: str | None = None
    authoring_group: str | None = None
    promoted_from_sha: str | None = None


@dataclass(frozen=True)
class _StoreOwner:
    """Placement owner for the document stores (mirrors ``ContextRepository``)."""

    branch: str = "master"


class _RuleRow(Protocol):
    rule_id: str
    kind: RuleKind | str
    head: Atom
    body: tuple[BodyLiteral, ...]
    source: str | None
    authoring_group: str | None
    promoted_from_sha: str | None


class _SuperiorityRow(Protocol):
    superiority_id: str
    superior_rule_id: str
    inferior_rule_id: str
    source: str | None
    authoring_group: str | None
    promoted_from_sha: str | None


def _row_to_rule(row: _RuleRow) -> DefeasibleRule:
    return DefeasibleRule(
        rule_id=row.rule_id,
        kind=_coerce_kind(row.kind),
        head=row.head,
        body=tuple(row.body),
        source=row.source,
        authoring_group=row.authoring_group,
        promoted_from_sha=row.promoted_from_sha,
    )


def _coerce_kind(value: RuleKind | str) -> RuleKind:
    if value in ("strict", "defeasible", "proper_defeater", "blocking_defeater"):
        return value
    raise ValueError(f"unknown rule kind {value!r}")


def _row_to_superiority(row: _SuperiorityRow) -> RuleSuperiority:
    return RuleSuperiority(
        superiority_id=row.superiority_id,
        superior_rule_id=row.superior_rule_id,
        inferior_rule_id=row.inferior_rule_id,
        source=row.source,
        authoring_group=row.authoring_group,
        promoted_from_sha=row.promoted_from_sha,
    )


class RuleRepository:
    """Author rules and rule superiorities to git; project them into a sidecar.

    Same shape as :class:`~propstore.families.contexts.ContextRepository`: a
    charter-driven git store per family over a shared backend, plus a
    multi-table charter-derived sqlite sidecar.
    """

    def __init__(self, backend: GitStore | None = None) -> None:
        store_backend = backend if backend is not None else GitStore.init_memory()
        self._rule_store = DocumentFamilyStore(
            owner=_StoreOwner(),
            backend=store_backend,
            codec=DefeasibleRule.__charter__.document_codec(),
        )
        self._superiority_store = DocumentFamilyStore(
            owner=_StoreOwner(),
            backend=store_backend,
            codec=RuleSuperiority.__charter__.document_codec(),
        )
        self._rule_family = DefeasibleRule.__charter__.family.artifact_family
        self._superiority_family = RuleSuperiority.__charter__.family.artifact_family

    def author(self, rule: DefeasibleRule, *, message: str) -> str:
        """Store the authored rule keyed by ``rule_id``; return sha."""

        return self._rule_store.save(self._rule_family, rule.rule_id, rule, message=message)

    def author_superiority(self, superiority: RuleSuperiority, *, message: str) -> str:
        """Store an authored superiority keyed by ``superiority_id``; return sha."""

        return self._superiority_store.save(
            self._superiority_family, superiority.superiority_id, superiority, message=message
        )

    def get(self, rule_id: str) -> DefeasibleRule | None:
        return self._rule_store.load(self._rule_family, rule_id)

    def get_superiority(self, superiority_id: str) -> RuleSuperiority | None:
        return self._superiority_store.load(self._superiority_family, superiority_id)

    def iter_rules(self) -> Iterator[DefeasibleRule]:
        for handle in self._rule_store.iter_handles(self._rule_family):
            yield handle.document

    def iter_superiorities(self) -> Iterator[RuleSuperiority]:
        for handle in self._superiority_store.iter_handles(self._superiority_family):
            yield handle.document

    def build_sidecar(self, path: Path) -> SqlAlchemySchema:
        """Project EVERY authored rule and superiority into a fresh sqlite sidecar.

        Never filters: every authored rule and superiority lands as a row.
        Returns the built schema for reuse.
        """

        schema = build_sqlalchemy_schema(
            charter_catalog(DefeasibleRule.__charter__, RuleSuperiority.__charter__)
        )
        create_sqlalchemy_store(path, schema)
        with writable_session(path, schema) as session:
            for rule in self.iter_rules():
                session.add_family(
                    "defeasible_rule",
                    {
                        "rule_id": rule.rule_id,
                        "kind": rule.kind,
                        "head": rule.head,
                        "body": rule.body,
                        "source": rule.source,
                        "authoring_group": rule.authoring_group,
                        "promoted_from_sha": rule.promoted_from_sha,
                    },
                )
            for superiority in self.iter_superiorities():
                session.add_family(
                    "rule_superiority",
                    {
                        "superiority_id": superiority.superiority_id,
                        "superior_rule_id": superiority.superior_rule_id,
                        "inferior_rule_id": superiority.inferior_rule_id,
                        "source": superiority.source,
                        "authoring_group": superiority.authoring_group,
                        "promoted_from_sha": superiority.promoted_from_sha,
                    },
                )
            session.commit()
        return schema

    def render_rules(self, path: Path, schema: SqlAlchemySchema) -> list[DefeasibleRule]:
        model = schema.model("defeasible_rule")
        with readonly_session(path, schema) as session:
            rows = list(session.scalars(select(model)))
        return [_row_to_rule(row) for row in rows]

    def render_superiorities(
        self, path: Path, schema: SqlAlchemySchema
    ) -> list[RuleSuperiority]:
        model = schema.model("rule_superiority")
        with readonly_session(path, schema) as session:
            rows = list(session.scalars(select(model)))
        return [_row_to_superiority(row) for row in rows]
