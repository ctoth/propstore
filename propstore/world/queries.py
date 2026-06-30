"""SQL read helpers and query-error types for the repo-backed ``WorldQuery``.

The ``select_*`` functions read the materialized world sidecar through quire's
SQLAlchemy charter schema (``quire.sqlalchemy_store.readonly_session`` over the
:func:`propstore.derived_schema.build_world_sidecar_schema` schema) and rebuild
the ONE canonical charter / value type for each row. There is **no** ``*Row`` /
``*RowInput`` second spelling: quire's per-family generated ORM model is reduced
straight back to the authored charter (``Concept`` / ``Claim`` / ``Stance`` /
``Context`` / ``Micropublication``) via that charter's own msgspec field set
(:func:`_reconstruct`). Crossing the boundary is a read plus a reconstruction of
the canonical type, never a mirror.

Two derived families have no authored charter spelling on the read surface and
are reduced to their canonical value type instead: the ``conflict`` projection
to :class:`~propstore.conflict_detector.models.ConflictRecord` and the
``micropublication`` charter to
:class:`~propstore.core.micropublications.ActiveMicropublication`.

Parameterization edges are not a stored family in the charter rewrite; they are
*derived* at read time from the authored ``EQUATION`` claims (an equation claim's
``output_concept`` parameterized by the input ``concepts`` it references) — see
:func:`derive_parameterizations`. This keeps the parameterization graph a
render-time view over the claim charters rather than a duplicated projection.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, TypeGuard, TypeVar

import msgspec
from sqlalchemy import func, select

from condition_ir import CheckedConditionSet, checked_condition_set_from_json
from propstore.conflict_detector.models import (
    ConflictClass,
    ConflictRecord,
    coerce_conflict_class,
)
from propstore.core.graph_types import ParameterizationEdge
from propstore.core.id_types import to_concept_id, to_concept_ids, to_context_id
from propstore.core.micropublications import ActiveMicropublication
from propstore.core.store_results import ConceptSearchHit
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context, LiftingRule
from propstore.families.diagnostics import BuildDiagnostic
from propstore.families.forms import FormDefinition
from propstore.families.relations import Stance

if TYPE_CHECKING:
    from quire.sqlalchemy_store import DerivedSession

_StructT = TypeVar("_StructT", bound=msgspec.Struct)


class WorldQueryError(Exception):
    """Base class for expected world-query failures."""


class UnknownConceptError(WorldQueryError):
    """Raised when a concept reference does not resolve to any stored concept."""

    def __init__(self, target: str) -> None:
        super().__init__(f"Unknown concept: {target}")
        self.target = target


class UnknownClaimError(WorldQueryError):
    """Raised when a claim reference does not resolve to any stored claim."""

    def __init__(self, target: str) -> None:
        super().__init__(f"Unknown claim: {target}")
        self.target = target


def _reconstruct(cls: type[_StructT], model: object) -> _StructT:
    """Rebuild the ONE canonical charter ``cls`` from a sidecar ORM model row.

    The sidecar model carries exactly the charter's fields (quire derived its
    columns from them, and the ``json``/enum boundaries decode back to the
    authored python types on read), so reading the charter's own field names off
    the model and constructing the charter reproduces the authored document — it
    is not a second spelling.
    """

    fields = {field.name: getattr(model, field.name) for field in msgspec.structs.fields(cls)}
    return cls(**fields)


def _is_str_mapping(value: object) -> TypeGuard[Mapping[str, Any]]:
    return isinstance(value, Mapping)


def _checked_conditions(conditions_ir: str | None) -> CheckedConditionSet | None:
    """Rebuild a claim/edge's checked conditions from its stored ``conditions_ir``."""

    if not conditions_ir:
        return None
    decoded = json.loads(conditions_ir)
    if not _is_str_mapping(decoded):
        raise ValueError("conditions_ir must decode to a mapping")
    return checked_condition_set_from_json(decoded)


# ── concepts ─────────────────────────────────────────────────────────────────


def select_concepts(session: DerivedSession) -> list[Concept]:
    """Every authored concept in the sidecar, rebuilt as ``Concept``."""

    model = session.schema.model("concept")
    return [_reconstruct(Concept, row) for row in session.scalars(select(model))]


def select_concept(session: DerivedSession, concept_id: str) -> Concept | None:
    """One concept by exact ``concept_id``, or ``None``."""

    model = session.schema.model("concept")
    row = session.scalars(
        select(model).where(model.concept_id == concept_id)
    ).first()
    return None if row is None else _reconstruct(Concept, row)


def resolve_concept_id(session: DerivedSession, name: str) -> str | None:
    """Resolve a concept by exact id, then by canonical name."""

    model = session.schema.model("concept")
    by_id = session.scalars(select(model).where(model.concept_id == name)).first()
    if by_id is not None:
        return str(by_id.concept_id)
    by_name = session.scalars(
        select(model).where(model.canonical_name == name)
    ).first()
    return None if by_name is None else str(by_name.concept_id)


def search_concepts(session: DerivedSession, query: str) -> list[ConceptSearchHit]:
    """Concepts whose canonical name contains ``query`` (case-insensitive)."""

    model = session.schema.model("concept")
    pattern = f"%{query}%"
    rows = session.scalars(
        select(model).where(model.canonical_name.ilike(pattern)).order_by(model.concept_id)
    )
    return [
        ConceptSearchHit(concept_id=to_concept_id(str(row.concept_id))) for row in rows
    ]


def count_concepts(session: DerivedSession) -> int:
    model = session.schema.model("concept")
    return int(session.scalar(select(func.count()).select_from(model)) or 0)


# ── claims ───────────────────────────────────────────────────────────────────


def select_claims(session: DerivedSession) -> list[Claim]:
    """Every authored claim in the sidecar, rebuilt as ``Claim``."""

    model = session.schema.model("claim")
    return [_reconstruct(Claim, row) for row in session.scalars(select(model))]


def select_claim(session: DerivedSession, claim_id: str) -> Claim | None:
    """One claim by exact ``claim_id``, or ``None``."""

    model = session.schema.model("claim")
    row = session.scalars(select(model).where(model.claim_id == claim_id)).first()
    return None if row is None else _reconstruct(Claim, row)


def resolve_claim_id(session: DerivedSession, name: str) -> str | None:
    """Resolve a claim by exact ``claim_id``."""

    model = session.schema.model("claim")
    row = session.scalars(select(model).where(model.claim_id == name)).first()
    return None if row is None else str(row.claim_id)


def count_claims(session: DerivedSession) -> int:
    model = session.schema.model("claim")
    return int(session.scalar(select(func.count()).select_from(model)) or 0)


# ── stances ──────────────────────────────────────────────────────────────────


def select_stances(session: DerivedSession) -> list[Stance]:
    """Every authored stance in the sidecar, rebuilt as ``Stance``."""

    model = session.schema.model("stance")
    return [_reconstruct(Stance, row) for row in session.scalars(select(model))]


def select_stances_between(
    session: DerivedSession, claim_ids: set[str]
) -> list[Stance]:
    """Stances whose source and target both lie in ``claim_ids``."""

    if not claim_ids:
        return []
    model = session.schema.model("stance")
    rows = session.scalars(
        select(model)
        .where(model.source_claim_id.in_(claim_ids))
        .where(model.target_claim_id.in_(claim_ids))
    )
    return [_reconstruct(Stance, row) for row in rows]


def select_incident_stances(session: DerivedSession, claim_id: str) -> list[Stance]:
    """Stances in which ``claim_id`` is the source or the target claim."""

    model = session.schema.model("stance")
    rows = session.scalars(
        select(model)
        .where(
            (model.source_claim_id == claim_id) | (model.target_claim_id == claim_id)
        )
        .order_by(model.stance_id)
    )
    return [_reconstruct(Stance, row) for row in rows]


# ── contexts + lifting rules ─────────────────────────────────────────────────


def select_contexts(session: DerivedSession) -> list[Context]:
    """Every authored context in the sidecar, rebuilt as ``Context``."""

    model = session.schema.model("context")
    return [_reconstruct(Context, row) for row in session.scalars(select(model))]


def select_lifting_rules(session: DerivedSession) -> list[LiftingRule]:
    """Every authored lifting rule in the sidecar, rebuilt as ``LiftingRule``."""

    model = session.schema.model("lifting_rule")
    return [_reconstruct(LiftingRule, row) for row in session.scalars(select(model))]


# ── forms ────────────────────────────────────────────────────────────────────


def select_forms(session: DerivedSession) -> list[FormDefinition]:
    """Every authored form definition in the sidecar, rebuilt as ``FormDefinition``."""

    model = session.schema.model("form")
    return [_reconstruct(FormDefinition, row) for row in session.scalars(select(model))]


# ── micropublications ────────────────────────────────────────────────────────


def select_micropublications(
    session: DerivedSession,
) -> list[ActiveMicropublication]:
    """Micropublication bundles rebuilt as :class:`ActiveMicropublication`.

    A bundle with no claims cannot form a valid active micropublication (its
    meaning is the claims it bundles); such a bundle is already surfaced as a
    quarantine ``build_diagnostic`` at build time, so it is not yielded here.
    """

    model = session.schema.model("micropublication")
    active: list[ActiveMicropublication] = []
    for row in session.scalars(select(model)):
        claim_ids = tuple(row.claims)
        if not claim_ids:
            continue
        active.append(
            ActiveMicropublication(
                artifact_id=str(row.artifact_id),
                context_id=to_context_id(str(row.context_id)),
                claim_ids=claim_ids,
                assumptions=tuple(row.assumptions),
            )
        )
    return active


# ── conflicts ────────────────────────────────────────────────────────────────


def select_conflicts(session: DerivedSession) -> list[ConflictRecord]:
    """The detected pairwise conflicts, rebuilt as :class:`ConflictRecord`.

    The ``conflict`` projection stores the rendered conflicting values and the
    conflict class; the per-claim CEL condition lists are not projected (they are
    not read by the graph-witness lowering), so they rebuild as empty.
    """

    model = session.schema.model("conflict")
    records: list[ConflictRecord] = []
    for row in session.scalars(select(model)):
        records.append(
            ConflictRecord(
                concept_id=str(row.concept_id),
                claim_a_id=str(row.claim_a_id),
                claim_b_id=str(row.claim_b_id),
                warning_class=coerce_conflict_class(row.warning_class)
                or ConflictClass.UNKNOWN,
                conditions_a=[],
                conditions_b=[],
                value_a=str(row.value_a),
                value_b=str(row.value_b),
                derivation_chain=row.derivation_chain,
            )
        )
    return records


def count_conflicts(session: DerivedSession) -> int:
    model = session.schema.model("conflict")
    return int(session.scalar(select(func.count()).select_from(model)) or 0)


# ── build diagnostics (quarantine surface) ───────────────────────────────────


def select_build_diagnostics(session: DerivedSession) -> list[BuildDiagnostic]:
    """Every build diagnostic row, rebuilt as ``BuildDiagnostic``."""

    model = session.schema.model("build_diagnostic")
    return [
        _reconstruct(BuildDiagnostic, row) for row in session.scalars(select(model))
    ]


# ── derived parameterization graph ───────────────────────────────────────────


def derive_parameterizations(claims: Sequence[Claim]) -> list[ParameterizationEdge]:
    """Derive parameterization edges from the authored ``EQUATION`` claims.

    An equation claim names the concept it computes (``output_concept``) and the
    concepts it is computed from (the other ``concepts`` it references). That is a
    parameterization edge ``output <- inputs``; the formula/sympy and the claim's
    checked conditions ride on the edge. A claim with no output concept or no
    distinct input concepts contributes no edge.
    """

    edges: list[ParameterizationEdge] = []
    for claim in claims:
        if claim.claim_type is not ClaimType.EQUATION:
            continue
        output = claim.output_concept
        if output is None:
            continue
        inputs = tuple(
            concept_id for concept_id in claim.concepts if concept_id != output
        )
        if not inputs:
            continue
        edges.append(
            ParameterizationEdge(
                output_concept_id=to_concept_id(output),
                input_concept_ids=to_concept_ids(inputs),
                formula=claim.expression,
                sympy=claim.sympy,
                checked_conditions=_checked_conditions(claim.conditions_ir),
            )
        )
    return edges
