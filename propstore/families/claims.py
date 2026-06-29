"""The ``Claim`` entity — Phase 3 charter, plus its git+sidecar repository.

A *claim* is a propositional assertion authored against a context: a typed
statement (parameter, equation, observation, …) that may carry a numeric value,
an equation/expression, free concept references, and a tuple of CEL *conditions*
qualifying when it holds. This module owns the ONE canonical ``Claim`` charter;
the git document, the SQL sidecar columns, and the serialized contract all fall
out of its field annotations exactly as for :class:`~propstore.families.concepts.Concept`
and :class:`~propstore.families.forms.FormDefinition`.

Substrate boundary (CLAUDE.md, PLAN.md §12):

* ONE canonical ``Claim`` type — there is no ``ClaimDocument`` / ``ClaimRecord``
  / ``ClaimRow`` second spelling and no ``to_payload`` / ``from_payload`` /
  ``coerce_`` conversion. ``ConflictClaim`` / ``MergeClaim`` (later phases) are
  field-subset VIEWS over this one charter, never independent storage.
* Conditions are authored as CEL source strings (``conditions``). Their checked
  form is condition-ir's own ``CheckedConditionSet``, serialized with that
  package's json codec into ``conditions_ir`` (see
  :mod:`propstore.claim_conditions`). propstore never mirrors a condition type.
* Non-commitment: :meth:`ClaimRepository.build_sidecar` NEVER filters, drops, or
  aborts. A ``DRAFT`` / ``BLOCKED`` claim, an unsatisfiable condition, or a claim
  with no resolved type all land as rows; visibility is a render-time decision.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Annotated, Protocol

from quire.charter_class import CharterDoc, charter, charter_field
from quire.charters import charter_catalog
from quire.family_store import DocumentFamilyStore
from quire.git_store import GitStore
from quire.references import ForeignKeySpec
from quire.sqlalchemy_schema import SqlAlchemySchema, build_sqlalchemy_schema
from quire.sqlalchemy_store import create_sqlalchemy_store, readonly_session, writable_session
from sqlalchemy import select

from propstore.families import SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION


class ClaimType(str, Enum):
    """The kind of assertion a claim makes.

    Mirrors the reference claim taxonomy. ``UNKNOWN`` is a sentinel for an
    unrecognized authored type; it is excluded from the claim-type contract
    table (:mod:`propstore.claim_contracts`) — every other member has a contract.
    """

    PARAMETER = "parameter"
    EQUATION = "equation"
    OBSERVATION = "observation"
    MECHANISM = "mechanism"
    COMPARISON = "comparison"
    LIMITATION = "limitation"
    MODEL = "model"
    MEASUREMENT = "measurement"
    ALGORITHM = "algorithm"
    UNKNOWN = "unknown"


class ClaimStatus(str, Enum):
    """Authoring lifecycle status of a claim.

    Like :class:`~propstore.families.concepts.ConceptStatus`, a claim's status
    never gates whether it reaches storage — every authored claim is stored and
    projected. The status is read only at render time, where a render policy
    decides which statuses are visible.
    """

    AUTHORED = "authored"
    DRAFT = "draft"
    BLOCKED = "blocked"


@charter(
    key="claim",
    name="claim",
    contract_version="2026.06.29",
    placement="claim",
    identity_field="claim_id",
    semantic="propstore.claim",
)
class Claim(CharterDoc):
    """A propositional claim authored against a context.

    The class *is* the document: its annotated attributes are exactly the stored
    fields and the sidecar ``claim`` columns. ``claim_id`` is the identity.
    ``conditions`` holds the RAW authored CEL source; ``conditions_ir`` holds the
    serialized condition-ir ``CheckedConditionSet`` (that package's json codec) —
    a deterministic, fingerprint-bearing compile of ``conditions``, not a second
    spelling. No provenance field exists, so identity is provenance-free.
    """

    claim_id: Annotated[str, charter_field(primary_key=True)]
    context_id: Annotated[
        str | None,
        charter_field(
            foreign_key=ForeignKeySpec(
                name="claim_context",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="claim",
                source_field="context_id",
                target_family="context",
                target_field="context_id",
                required=False,
            )
        ),
    ] = None
    claim_type: ClaimType | None = None
    status: ClaimStatus = ClaimStatus.AUTHORED
    statement: str | None = None
    name: str | None = None
    body: str | None = None
    expression: str | None = None
    sympy: str | None = None
    measure: str | None = None
    methodology: str | None = None
    notes: str | None = None
    output_concept: Annotated[
        str | None,
        charter_field(
            foreign_key=ForeignKeySpec(
                name="claim_output_concept",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="claim",
                source_field="output_concept",
                target_family="concept",
                target_field="concept_id",
                required=False,
            )
        ),
    ] = None
    target_concept: Annotated[
        str | None,
        charter_field(
            foreign_key=ForeignKeySpec(
                name="claim_target_concept",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="claim",
                source_field="target_concept",
                target_family="concept",
                target_field="concept_id",
                required=False,
            )
        ),
    ] = None
    concepts: Annotated[
        tuple[str, ...],
        charter_field(
            json=True,
            foreign_keys=(
                ForeignKeySpec(
                    name="claim_concepts",
                    contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                    source_family="claim",
                    source_field="concepts[]",
                    target_family="concept",
                    target_field="concept_id",
                    required=False,
                    many=True,
                ),
            ),
        ),
    ] = ()
    equations: Annotated[tuple[str, ...], charter_field(json=True)] = ()
    conditions: Annotated[tuple[str, ...], charter_field(json=True)] = ()
    conditions_ir: str | None = None
    value: float | None = None
    lower_bound: float | None = None
    upper_bound: float | None = None
    uncertainty: float | None = None
    uncertainty_type: str | None = None
    confidence: float | None = None
    unit: str | None = None
    sample_size: int | None = None


@dataclass(frozen=True)
class _StoreOwner:
    """Placement owner for the document store (mirrors ``ConceptRepository``)."""

    branch: str = "master"


class _ClaimRow(Protocol):
    """Structural view of a sidecar ``claim`` row.

    The sidecar model is built dynamically from the charter, so it has no static
    class to import; this names the charter-derived columns the repository reads
    back, giving typed access without a cast or ignore.
    """

    claim_id: str
    context_id: str | None
    claim_type: ClaimType | str | None
    status: ClaimStatus | str
    statement: str | None
    name: str | None
    body: str | None
    expression: str | None
    sympy: str | None
    measure: str | None
    methodology: str | None
    notes: str | None
    output_concept: str | None
    target_concept: str | None
    concepts: tuple[str, ...]
    equations: tuple[str, ...]
    conditions: tuple[str, ...]
    conditions_ir: str | None
    value: float | None
    lower_bound: float | None
    upper_bound: float | None
    uncertainty: float | None
    uncertainty_type: str | None
    confidence: float | None
    unit: str | None
    sample_size: int | None


def _row_to_claim(row: _ClaimRow) -> Claim:
    """Rebuild the one ``Claim`` from a sidecar row (not a second spelling)."""

    claim_type = row.claim_type
    if claim_type is not None and not isinstance(claim_type, ClaimType):
        claim_type = ClaimType(claim_type)
    status = row.status if isinstance(row.status, ClaimStatus) else ClaimStatus(row.status)
    return Claim(
        claim_id=row.claim_id,
        context_id=row.context_id,
        claim_type=claim_type,
        status=status,
        statement=row.statement,
        name=row.name,
        body=row.body,
        expression=row.expression,
        sympy=row.sympy,
        measure=row.measure,
        methodology=row.methodology,
        notes=row.notes,
        output_concept=row.output_concept,
        target_concept=row.target_concept,
        concepts=row.concepts,
        equations=row.equations,
        conditions=row.conditions,
        conditions_ir=row.conditions_ir,
        value=row.value,
        lower_bound=row.lower_bound,
        upper_bound=row.upper_bound,
        uncertainty=row.uncertainty,
        uncertainty_type=row.uncertainty_type,
        confidence=row.confidence,
        unit=row.unit,
        sample_size=row.sample_size,
    )


class ClaimRepository:
    """Author claims to git and project them into a SQL sidecar.

    Same shape as ``propstore.storage.ConceptRepository`` and
    ``propstore.families.forms.FormRepository``: a charter-driven
    ``DocumentFamilyStore`` for the canonical document and a charter-derived
    sqlite sidecar. The ``claim`` table and columns are the charter's fields.
    """

    def __init__(self, backend: GitStore | None = None) -> None:
        self._store = DocumentFamilyStore(
            owner=_StoreOwner(),
            backend=backend if backend is not None else GitStore.init_memory(),
            codec=Claim.__charter__.document_codec(),
        )
        self._family = Claim.__charter__.family.artifact_family

    def author(self, claim: Claim, *, message: str) -> str:
        """Store the RAW authored claim keyed by ``claim_id``; return commit sha."""

        return self._store.save(self._family, claim.claim_id, claim, message=message)

    def get(self, claim_id: str) -> Claim | None:
        """Load a claim by identity from the git store, or ``None``."""

        return self._store.load(self._family, claim_id)

    def iter_claims(self) -> Iterator[Claim]:
        """Iterate every authored claim document in the git store."""

        for handle in self._store.iter_handles(self._family):
            yield handle.document

    def build_sidecar(self, path: Path) -> SqlAlchemySchema:
        """Project EVERY authored claim into a fresh sqlite sidecar.

        Never filters: a ``DRAFT`` / ``BLOCKED`` claim, or one carrying an
        unsatisfiable condition, lands as a row just like a clean one. Visibility
        is decided later, at render. Returns the built schema for reuse.
        """

        schema = build_sqlalchemy_schema(charter_catalog(Claim.__charter__))
        create_sqlalchemy_store(path, schema)
        with writable_session(path, schema) as session:
            for claim in self.iter_claims():
                session.add_family(
                    "claim",
                    {
                        "claim_id": claim.claim_id,
                        "context_id": claim.context_id,
                        "claim_type": claim.claim_type,
                        "status": claim.status,
                        "statement": claim.statement,
                        "name": claim.name,
                        "body": claim.body,
                        "expression": claim.expression,
                        "sympy": claim.sympy,
                        "measure": claim.measure,
                        "methodology": claim.methodology,
                        "notes": claim.notes,
                        "output_concept": claim.output_concept,
                        "target_concept": claim.target_concept,
                        "concepts": claim.concepts,
                        "equations": claim.equations,
                        "conditions": claim.conditions,
                        "conditions_ir": claim.conditions_ir,
                        "value": claim.value,
                        "lower_bound": claim.lower_bound,
                        "upper_bound": claim.upper_bound,
                        "uncertainty": claim.uncertainty,
                        "uncertainty_type": claim.uncertainty_type,
                        "confidence": claim.confidence,
                        "unit": claim.unit,
                        "sample_size": claim.sample_size,
                    },
                )
            session.commit()
        return schema

    def render_claims(self, path: Path, schema: SqlAlchemySchema) -> list[Claim]:
        """Return every claim from the sidecar, rebuilt as ``Claim``."""

        model = schema.model("claim")
        with readonly_session(path, schema) as session:
            rows = list(session.scalars(select(model)))
        return [_row_to_claim(row) for row in rows]
