"""The ``Stance`` entity — a typed relation between two claims — and its repository.

A *stance* records that one claim takes a typed position toward another (it
rebuts, undercuts, supports, …), optionally carrying a subjective-logic opinion
about how strongly. This module owns the ONE canonical ``Stance`` charter; the git
document, the SQL sidecar columns, and the serialized contract all fall out of its
field annotations exactly as for :class:`~propstore.families.claims.Claim`.

Substrate boundary (CLAUDE.md): there is no ``StanceDocument`` / ``StanceRecord`` /
``StanceRow`` second spelling. The stance vocabulary is the one
:class:`~propstore.stances.StanceType`. An attached opinion is stored as the four
Jøsang components ``opinion_belief/disbelief/uncertainty/base_rate``; when read
back it is rebuilt as ``doxa``'s canonical :class:`doxa.Opinion` — never a
re-spelled opinion.

Non-commitment (CLAUDE.md design checklist): :meth:`StanceRepository.build_sidecar`
NEVER filters. A ``SUPPORTS`` edge, an ``ABSTAIN`` edge, and a vacuous-opinion edge
all land as rows. Whether a stance becomes an attack is read off
:data:`~propstore.stances.NON_ATTACK_TYPES` at render time
(:func:`stance_summary`), not gated at build time.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Protocol

from doxa import Opinion
from quire.charter_class import CharterDoc, charter, charter_field
from quire.charters import charter_catalog
from quire.family_store import DocumentFamilyStore
from quire.git_store import GitStore
from quire.references import ForeignKeySpec
from quire.sqlalchemy_schema import SqlAlchemySchema, build_sqlalchemy_schema
from quire.sqlalchemy_store import (
    create_sqlalchemy_store,
    readonly_session,
    writable_session,
)
from sqlalchemy import select

from propstore.families import SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION
from propstore.stances import NON_ATTACK_TYPES, StanceType, coerce_stance_type

_DOGMATIC_TOL = 1e-9


@charter(
    key="stance",
    name="stance",
    contract_version="2026.06.29",
    placement="stance",
    identity_field="stance_id",
    semantic="propstore.stance",
)
class Stance(CharterDoc):
    """A typed relation one claim takes toward another, with optional opinion.

    The class *is* the document: its annotated attributes are exactly the stored
    fields and the sidecar ``stance`` columns. ``stance_id`` is the identity. The
    four ``opinion_*`` columns are nullable: a stance with no authored opinion
    leaves them ``None`` (honest absence), not a fabricated default.
    """

    stance_id: Annotated[str, charter_field(primary_key=True)]
    source_claim_id: Annotated[
        str | None,
        charter_field(
            foreign_key=ForeignKeySpec(
                name="stance_source_claim",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="stance",
                source_field="source_claim_id",
                target_family="claim",
                target_field="claim_id",
                required=False,
            )
        ),
    ] = None
    target_claim_id: Annotated[
        str | None,
        charter_field(
            foreign_key=ForeignKeySpec(
                name="stance_target_claim",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="stance",
                source_field="target_claim_id",
                target_family="claim",
                target_field="claim_id",
                required=False,
            )
        ),
    ] = None
    stance_type: StanceType | None = None
    resolution_model: str | None = None
    confidence: float | None = None
    opinion_belief: float | None = None
    opinion_disbelief: float | None = None
    opinion_uncertainty: float | None = None
    opinion_base_rate: float | None = None

    def opinion(self) -> Opinion | None:
        """Rebuild the attached opinion as ``doxa.Opinion``, or ``None``.

        Returns ``None`` unless all four Jøsang components are present — a partial
        opinion is treated as no opinion, never completed with a fabricated mass.
        """

        b = self.opinion_belief
        d = self.opinion_disbelief
        u = self.opinion_uncertainty
        a = self.opinion_base_rate
        if b is None or d is None or u is None or a is None:
            return None
        return Opinion(b, d, u, a, allow_dogmatic=u < _DOGMATIC_TOL)


@dataclass(frozen=True)
class _StoreOwner:
    """Placement owner for the document store (mirrors ``ClaimRepository``)."""

    branch: str = "master"


class _StanceRow(Protocol):
    """Structural view of a sidecar ``stance`` row.

    The sidecar model is built dynamically from the charter, so it has no static
    class to import; this names the charter-derived columns the repository reads
    back, giving typed access without a cast or ignore.
    """

    stance_id: str
    source_claim_id: str | None
    target_claim_id: str | None
    stance_type: StanceType | str | None
    resolution_model: str | None
    confidence: float | None
    opinion_belief: float | None
    opinion_disbelief: float | None
    opinion_uncertainty: float | None
    opinion_base_rate: float | None


def _row_to_stance(row: _StanceRow) -> Stance:
    """Rebuild the one ``Stance`` from a sidecar row (not a second spelling)."""

    return Stance(
        stance_id=row.stance_id,
        source_claim_id=row.source_claim_id,
        target_claim_id=row.target_claim_id,
        stance_type=coerce_stance_type(row.stance_type),
        resolution_model=row.resolution_model,
        confidence=row.confidence,
        opinion_belief=row.opinion_belief,
        opinion_disbelief=row.opinion_disbelief,
        opinion_uncertainty=row.opinion_uncertainty,
        opinion_base_rate=row.opinion_base_rate,
    )


class StanceRepository:
    """Author stances to git and project EVERY one into a SQL sidecar.

    Same shape as :class:`~propstore.families.claims.ClaimRepository`: a
    charter-driven ``DocumentFamilyStore`` for the canonical document and a
    charter-derived sqlite sidecar. The ``stance`` table and columns are the
    charter's fields.
    """

    def __init__(self, backend: GitStore | None = None) -> None:
        self._store = DocumentFamilyStore(
            owner=_StoreOwner(),
            backend=backend if backend is not None else GitStore.init_memory(),
            codec=Stance.__charter__.document_codec(),
        )
        self._family = Stance.__charter__.family.artifact_family

    def author(self, stance: Stance, *, message: str) -> str:
        """Store the stance keyed by ``stance_id``; return commit sha."""

        return self._store.save(self._family, stance.stance_id, stance, message=message)

    def get(self, stance_id: str) -> Stance | None:
        """Load a stance by identity from the git store, or ``None``."""

        return self._store.load(self._family, stance_id)

    def iter_stances(self) -> Iterator[Stance]:
        """Iterate every authored stance document in the git store."""

        for handle in self._store.iter_handles(self._family):
            yield handle.document

    def build_sidecar(self, path: Path) -> SqlAlchemySchema:
        """Project EVERY authored stance into a fresh sqlite sidecar.

        Never filters: a non-attacking ``SUPPORTS`` stance, an ``ABSTAIN``, or a
        stance carrying a vacuous opinion all land as rows. Whether a stance
        participates as an attack is a render-time decision. Returns the built
        schema for reuse.
        """

        schema = build_sqlalchemy_schema(charter_catalog(Stance.__charter__))
        create_sqlalchemy_store(path, schema)
        with writable_session(path, schema) as session:
            for stance in self.iter_stances():
                session.add_family(
                    "stance",
                    {
                        "stance_id": stance.stance_id,
                        "source_claim_id": stance.source_claim_id,
                        "target_claim_id": stance.target_claim_id,
                        "stance_type": stance.stance_type,
                        "resolution_model": stance.resolution_model,
                        "confidence": stance.confidence,
                        "opinion_belief": stance.opinion_belief,
                        "opinion_disbelief": stance.opinion_disbelief,
                        "opinion_uncertainty": stance.opinion_uncertainty,
                        "opinion_base_rate": stance.opinion_base_rate,
                    },
                )
            session.commit()
        return schema

    def render_stances(self, path: Path, schema: SqlAlchemySchema) -> list[Stance]:
        """Return every stance from the sidecar, rebuilt as ``Stance``."""

        model = schema.model("stance")
        with readonly_session(path, schema) as session:
            rows = list(session.scalars(select(model)))
        return [_row_to_stance(row) for row in rows]


@dataclass(frozen=True)
class StanceSummary:
    """Render-time summary of which stances participate as attacks.

    All stances are counted; none are pruned. ``excluded_non_attack`` counts the
    :data:`~propstore.stances.NON_ATTACK_TYPES` edges (support/explains/none) that
    do not become attacks, and ``vacuous_count`` counts included attack edges whose
    opinion is (near-)vacuous (Jøsang 2001, p.8) — both are honest signals, not a
    gate. ``mean_uncertainty`` is ``None`` when no included edge carried one.
    """

    total_stances: int
    included_as_attacks: int
    vacuous_count: int
    excluded_non_attack: int
    models: tuple[str, ...]
    mean_uncertainty: float | None


def stance_summary(stances: Iterable[Stance]) -> StanceSummary:
    """Summarize stances for argumentation-facing render explanations.

    Every stance participates in AF construction regardless of opinion
    uncertainty, per the CLAUDE.md design checklist (no gate before render time).
    Vacuous opinions (Jøsang 2001, p.8) are counted but never pruned; filtering is
    deferred to render and resolution time.
    """

    total = 0
    included = 0
    vacuous_count = 0
    excluded_non_attack = 0
    models: set[str] = set()
    uncertainties: list[float] = []

    for stance in stances:
        total += 1
        if stance.stance_type in NON_ATTACK_TYPES:
            excluded_non_attack += 1
            continue

        included += 1
        if stance.resolution_model:
            models.add(stance.resolution_model)
        opinion_u = stance.opinion_uncertainty
        if opinion_u is not None:
            uncertainties.append(opinion_u)
            if opinion_u > 0.99:
                vacuous_count += 1

    mean_uncertainty = (
        sum(uncertainties) / len(uncertainties) if uncertainties else None
    )
    return StanceSummary(
        total_stances=total,
        included_as_attacks=included,
        vacuous_count=vacuous_count,
        excluded_non_attack=excluded_non_attack,
        models=tuple(sorted(models)),
        mean_uncertainty=mean_uncertainty,
    )
