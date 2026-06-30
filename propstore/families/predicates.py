"""The ``Predicate`` entity — Phase 4 charter, plus its git+sidecar repository.

A *predicate* is a declared Datalog/DeLP predicate symbol: a name, an arity, the
ordered argument types it ranges over, and an optional ``derived_from`` spec that
says how ground facts for it are mined from the concept/claim substrate. This
module owns the ONE canonical ``Predicate`` charter; the git document, the SQL
sidecar columns, and the serialized contract all fall out of its field
annotations exactly as for :class:`~propstore.families.claims.Claim`.

Substrate boundary (CLAUDE.md, PLAN.md §12):

* ONE canonical ``Predicate`` type — there is no ``PredicateDocument`` /
  ``PredicateRecord`` / ``PredicateRow`` second spelling and no ``to_payload`` /
  ``from_payload`` / ``coerce_`` conversion. The grounding registry
  (:mod:`propstore.grounding.predicates`) consumes *this* charter directly.
* The ``arity``/``arg_types`` agreement and the ``arg_types`` vocabulary are NOT
  validated in the charter — those are authoring-workflow concerns
  (:mod:`propstore.grounding.authoring`). The charter only declares the shape.
* Non-commitment: :meth:`PredicateRepository.build_sidecar` NEVER filters. Every
  authored predicate lands as a row; visibility is a render-time decision.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Protocol

import msgspec
from quire.artifacts import BranchPlacement, SubdirFixedFilePlacement
from quire.charter_class import CharterDoc, charter, charter_field
from quire.charters import charter_catalog
from quire.family_store import DocumentFamilyStore
from quire.git_store import GitStore
from quire.refs import single_field_ref_type
from quire.sqlalchemy_schema import SqlAlchemySchema, build_sqlalchemy_schema
from quire.sqlalchemy_store import create_sqlalchemy_store, readonly_session, writable_session
from sqlalchemy import select


@charter(
    key="predicate",
    name="predicate",
    contract_version="2026.06.29",
    placement="predicate",
    identity_field="predicate_id",
    semantic="propstore.predicate",
)
class Predicate(CharterDoc):
    """A declared predicate symbol.

    The class *is* the document: its annotated attributes are exactly the stored
    document fields and the sidecar ``predicate`` columns. ``predicate_id`` is the
    identity; ``arity`` is the declared number of arguments and ``arg_types`` the
    ordered argument-type names. ``derived_from`` is an optional fact-mining DSL
    spec (see :func:`propstore.grounding.predicates.parse_derived_from`).
    """

    predicate_id: Annotated[str, charter_field(primary_key=True)]
    arity: int
    arg_types: Annotated[tuple[str, ...], charter_field(json=True)] = ()
    derived_from: str | None = None
    description: str | None = None
    authoring_group: str | None = None
    promoted_from_sha: str | None = None


@dataclass(frozen=True)
class _StoreOwner:
    """Placement owner for the document store (mirrors ``ClaimRepository``)."""

    branch: str = "master"


class _PredicateRow(Protocol):
    """Structural view of a sidecar ``predicate`` row (charter-derived columns)."""

    predicate_id: str
    arity: int
    arg_types: tuple[str, ...]
    derived_from: str | None
    description: str | None
    authoring_group: str | None
    promoted_from_sha: str | None


def _row_to_predicate(row: _PredicateRow) -> Predicate:
    """Rebuild the one ``Predicate`` from a sidecar row (not a second spelling)."""

    return Predicate(
        predicate_id=row.predicate_id,
        arity=row.arity,
        arg_types=tuple(row.arg_types),
        derived_from=row.derived_from,
        description=row.description,
        authoring_group=row.authoring_group,
        promoted_from_sha=row.promoted_from_sha,
    )


class PredicateRepository:
    """Author predicates to git and project them into a SQL sidecar.

    Same shape as :class:`~propstore.families.claims.ClaimRepository`: a
    charter-driven ``DocumentFamilyStore`` for the canonical document and a
    charter-derived sqlite sidecar. The ``predicate`` table and columns are the
    charter's fields. Storage is keyed by ``predicate_id`` — the authoring group
    or file never determines the storage path.
    """

    def __init__(self, backend: GitStore | None = None) -> None:
        self._store = DocumentFamilyStore(
            owner=_StoreOwner(),
            backend=backend if backend is not None else GitStore.init_memory(),
            codec=Predicate.__charter__.document_codec(),
        )
        self._family = Predicate.__charter__.family.artifact_family

    def author(self, predicate: Predicate, *, message: str) -> str:
        """Store the RAW authored predicate keyed by ``predicate_id``; return sha."""

        return self._store.save(
            self._family, predicate.predicate_id, predicate, message=message
        )

    def get(self, predicate_id: str) -> Predicate | None:
        """Load a predicate by identity from the git store, or ``None``."""

        return self._store.load(self._family, predicate_id)

    def exists(self, predicate_id: str) -> bool:
        """Whether a predicate with ``predicate_id`` is stored."""

        return self._store.exists(self._family, predicate_id)

    def delete(self, predicate_id: str, *, message: str) -> str:
        """Remove the stored predicate keyed by ``predicate_id``; return sha."""

        return self._store.delete(self._family, predicate_id, message=message)

    def iter_predicates(self) -> Iterator[Predicate]:
        """Iterate every authored predicate document in the git store."""

        for handle in self._store.iter_handles(self._family):
            yield handle.document

    def build_sidecar(self, path: Path) -> SqlAlchemySchema:
        """Project EVERY authored predicate into a fresh sqlite sidecar.

        Never filters: every authored predicate lands as a row. Visibility is
        decided later, at render. Returns the built schema for reuse.
        """

        schema = build_sqlalchemy_schema(charter_catalog(Predicate.__charter__))
        create_sqlalchemy_store(path, schema)
        with writable_session(path, schema) as session:
            for predicate in self.iter_predicates():
                session.add_family(
                    "predicate",
                    {
                        "predicate_id": predicate.predicate_id,
                        "arity": predicate.arity,
                        "arg_types": predicate.arg_types,
                        "derived_from": predicate.derived_from,
                        "description": predicate.description,
                        "authoring_group": predicate.authoring_group,
                        "promoted_from_sha": predicate.promoted_from_sha,
                    },
                )
            session.commit()
        return schema

    def render_predicates(self, path: Path, schema: SqlAlchemySchema) -> list[Predicate]:
        """Return every predicate from the sidecar, rebuilt as ``Predicate``."""

        model = schema.model("predicate")
        with readonly_session(path, schema) as session:
            rows = list(session.scalars(select(model)))
        return [_row_to_predicate(row) for row in rows]


# ---------------------------------------------------------------------------
# Predicate proposal artifact (heuristic layer 3)
# ---------------------------------------------------------------------------
#
# A *predicate proposal* is a heuristic-layer candidate vocabulary for one source
# paper (CLAUDE.md layer 3): the declarations a heuristic/LLM extracted, plus the
# provenance of that extraction. It lives on the ``proposal/predicates`` branch and
# is never canonical until an explicit promotion writes a :class:`Predicate`.

_BASE_PREDICATE_ARG_TYPES = frozenset({"paper_id", "int", "float", "str", "bool"})
_ENUM_ARG_TYPE_RE = re.compile(r"^enum:[A-Za-z0-9_-]+(\|[A-Za-z0-9_-]+)+$")


def validate_predicate_arg_type(arg_type: str) -> None:
    """Accept a base sort or an ``enum:a|b|...`` tag; reject anything else.

    The argument-type vocabulary is a closed set (Diller/Borg/Bex 2025 §3): the
    grounder enumerates substitutions only over declared sorts, so an unknown tag
    is a proposal error, not a free-form string.
    """

    if arg_type in _BASE_PREDICATE_ARG_TYPES:
        return
    if _ENUM_ARG_TYPE_RE.match(arg_type):
        return
    raise ValueError(f"unsupported predicate arg type: {arg_type!r}")


class PredicateDeclaration(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """One proposed predicate: a name, its arity, and the per-position sorts.

    The invariants are Datalog/DeLP signature rules: ``arity >= 0`` and
    ``len(arg_types) == arity`` (Garcia & Simari 2004 §3), and every argument type
    is drawn from the closed sort vocabulary (:func:`validate_predicate_arg_type`).
    """

    name: str
    arity: int
    description: str
    arg_types: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.arity < 0:
            raise ValueError("predicate arity must be >= 0")
        if len(self.arg_types) != self.arity:
            raise ValueError(
                f"predicate {self.name!r}: arg_types length {len(self.arg_types)} "
                f"does not match arity {self.arity}"
            )
        for arg_type in self.arg_types:
            validate_predicate_arg_type(arg_type)


class PredicateExtractionProvenance(
    msgspec.Struct, frozen=True, forbid_unknown_fields=True
):
    """Prompt/source provenance for a batch of proposed predicate declarations."""

    operations: tuple[str, ...]
    agent: str
    model: str
    prompt_sha: str
    notes_sha: str
    status: str


PREDICATE_PROPOSAL_BRANCH = BranchPlacement(
    policy="fixed", fixed_branch="proposal/predicates"
)
"""Place every predicate proposal on ``proposal/predicates``."""


if TYPE_CHECKING:

    @dataclass(frozen=True)
    class PredicateProposalRef:
        source_paper: str

else:
    PredicateProposalRef = single_field_ref_type(
        "PredicateProposalRef", "source_paper", module=__name__
    )


_PREDICATE_PROPOSAL_PLACEMENT: SubdirFixedFilePlacement[object, PredicateProposalRef] = (
    SubdirFixedFilePlacement(
        namespace="predicates",
        filename="declarations.yaml",
        ref_factory=PredicateProposalRef,
        ref_field="source_paper",
        branch=PREDICATE_PROPOSAL_BRANCH,
    )
)


@charter(
    key="proposal_predicates",
    name="proposal_predicates",
    contract_version="2026.06.29",
    placement=_PREDICATE_PROPOSAL_PLACEMENT,
    accessor="proposal_predicates",
    identity_field="source_paper",
)
class PredicateProposal(CharterDoc):
    """A paper's proposed predicate vocabulary, with extraction provenance.

    The class *is* the document: ``source_paper`` is the identity (one proposal
    batch per paper); the declarations and provenance project to JSON columns.
    ``promoted_from_sha`` records the proposal commit a promotion consumed.
    """

    source_paper: Annotated[str, charter_field(primary_key=True)]
    proposed_declarations: Annotated[
        tuple[PredicateDeclaration, ...], charter_field(json=True)
    ] = ()
    extraction_provenance: Annotated[
        PredicateExtractionProvenance | None, charter_field(json=True)
    ] = None
    extraction_date: str | None = None
    promoted_from_sha: str | None = None
