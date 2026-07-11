"""SQL read helpers and query-error types for the repo-backed ``WorldQuery``.

The ``select_*`` functions read the materialized world sidecar through Quire's
SQLAlchemy charter schema. Quire maps each canonical charter class as the ORM
model, so selected rows already are ``Concept`` / ``Claim`` / ``Stance`` /
``Context`` / ``Micropublication`` objects. Propstore does not reconstruct them.

The derived ``conflict`` family has no authored charter spelling on the read
surface and is reduced to its canonical
:class:`~propstore.conflict_detector.models.ConflictRecord` value type instead.

Parameterization edges are not a stored family in the charter rewrite; they are
*derived* at read time from the authored ``EQUATION`` claims (an equation claim's
``output_concept`` parameterized by the input ``concepts`` it references) — see
:func:`derive_parameterizations`. This keeps the parameterization graph a
render-time view over the claim charters rather than a duplicated projection.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, TypeGuard

from sqlalchemy import func, select

from condition_ir import CheckedConditionSet, checked_condition_set_from_json
from propstore.conflict_detector.models import (
    ConflictClass,
    ConflictRecord,
    coerce_conflict_class,
)
from propstore.core.graph_types import ParameterizationEdge
from propstore.core.id_types import to_concept_id, to_concept_ids
from propstore.core.store_results import ConceptSearchHit
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context, LiftingRule
from propstore.families.diagnostics import BuildDiagnostic
from propstore.families.forms import FormDefinition
from propstore.families.micropublications import Micropublication
from propstore.families.relations import Stance

if TYPE_CHECKING:
    from quire.sqlalchemy_store import DerivedSession

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
    """Every authored concept in the sidecar."""

    model = session.schema.model("concept")
    return [
        Concept.__charter__.document_from_model(row, Concept)
        for row in session.scalars(select(model))
    ]


def select_concept(session: DerivedSession, concept_id: str) -> Concept | None:
    """One concept by exact ``concept_id``, or ``None``."""

    model = session.schema.model("concept")
    row = session.scalars(
        select(model).where(model.concept_id == concept_id)
    ).first()
    return (
        None
        if row is None
        else Concept.__charter__.document_from_model(row, Concept)
    )


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
    """Every authored claim in the sidecar."""

    model = session.schema.model("claim")
    return [
        Claim.__charter__.document_from_model(row, Claim)
        for row in session.scalars(select(model))
    ]


def select_claim(session: DerivedSession, claim_id: str) -> Claim | None:
    """One claim by exact ``claim_id``, or ``None``."""

    model = session.schema.model("claim")
    row = session.scalars(select(model).where(model.claim_id == claim_id)).first()
    return (
        None
        if row is None
        else Claim.__charter__.document_from_model(row, Claim)
    )


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
    """Every authored stance in the sidecar."""

    model = session.schema.model("stance")
    return [
        Stance.__charter__.document_from_model(row, Stance)
        for row in session.scalars(select(model))
    ]


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
    return [Stance.__charter__.document_from_model(row, Stance) for row in rows]


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
    return [Stance.__charter__.document_from_model(row, Stance) for row in rows]


# ── contexts + lifting rules ─────────────────────────────────────────────────


def select_contexts(session: DerivedSession) -> list[Context]:
    """Every authored context in the sidecar."""

    model = session.schema.model("context")
    return [
        Context.__charter__.document_from_model(row, Context)
        for row in session.scalars(select(model))
    ]


def select_lifting_rules(session: DerivedSession) -> list[LiftingRule]:
    """Every authored lifting rule in the sidecar."""

    model = session.schema.model("lifting_rule")
    return [
        LiftingRule.__charter__.document_from_model(row, LiftingRule)
        for row in session.scalars(select(model))
    ]


# ── forms ────────────────────────────────────────────────────────────────────


def select_forms(session: DerivedSession) -> list[FormDefinition]:
    """Every authored form definition in the sidecar."""

    model = session.schema.model("form")
    return [
        FormDefinition.__charter__.document_from_model(row, FormDefinition)
        for row in session.scalars(select(model))
    ]


# ── micropublications ────────────────────────────────────────────────────────


def select_micropublications(
    session: DerivedSession,
) -> list[Micropublication]:
    """Every canonical micropublication in the sidecar."""

    model = session.schema.model("micropublication")
    return [
        Micropublication.__charter__.document_from_model(row, Micropublication)
        for row in session.scalars(select(model))
    ]


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
    """Every canonical build diagnostic in the sidecar."""

    model = session.schema.model("build_diagnostic")
    return [
        BuildDiagnostic.__charter__.document_from_model(row, BuildDiagnostic)
        for row in session.scalars(select(model))
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
