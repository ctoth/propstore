"""Coreference merge-argument proposals — the storage family for render-time
description-claim coreference.

Coreference between description claims is NOT a stored fact (CLAUDE.md
non-commitment; :mod:`propstore.core.lemon.coreference`). It is a defeasible
*merge argument* — a hypothesis that some description claims denote the same
thing — and rival hypotheses are stored side by side as **proposals**, never
collapsed and never promoted to a canonical edge. Whether any merge holds is
decided at RENDER time by running Dung argumentation under a chosen semantics; the
SAME stored arguments yield DIFFERENT clusters under grounded vs preferred.

This module owns the ONE storable spelling of a merge argument,
:class:`CoreferenceMergeArgumentDoc`, and its repository. The doc mirrors the
lemon :class:`~propstore.core.lemon.description_kinds.MergeArgument` data field for
field; the app layer lowers a stored doc to that lemon struct at query time (there
is no second in-memory spelling — the lemon struct is the compute form, this
charter is the storage form, and lowering is a construction, not a conversion).

Placement: every merge-argument proposal lives on the fixed ``proposal/coreference``
branch (mirroring :data:`~propstore.families.relations.STANCE_PROPOSAL_BRANCH`).
Non-commitment (design checklist): :meth:`CoreferenceMergeArgumentRepository.build_sidecar`
NEVER filters — two mutually-attacking rival hypotheses both land as rows; which (if
any) survives is a render-time verdict, not a build-time gate.

There is an UNRELATED ``MergeArgument`` in :mod:`propstore.merge.merge_classifier`
(branch-merge claim alternatives); this family is named ``CoreferenceMergeArgumentDoc``
to avoid that collision and imports neither it nor the lemon struct here.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from quire.artifacts import BranchPlacement, FlatYamlPlacement
from quire.canonical import canonical_json_sha256
from quire.charter_class import CharterDoc, charter, charter_field
from quire.charters import charter_catalog
from quire.family_store import DocumentFamilyStore
from quire.git_store import GitStore
from quire.references import ForeignKeySpec
from quire.refs import single_field_ref_type
from quire.sqlalchemy_schema import SqlAlchemySchema, build_sqlalchemy_schema
from quire.sqlalchemy_store import create_sqlalchemy_store, writable_session

from propstore.families import SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION
from propstore.provenance import Provenance, ProvenanceStatus

COREFERENCE_PROPOSAL_BRANCH = BranchPlacement(
    policy="fixed", fixed_branch="proposal/coreference"
)
"""Place every coreference merge-argument proposal on ``proposal/coreference``."""


def coreference_proposal_branch() -> str:
    """Return the branch every coreference merge-argument proposal is recorded on."""

    branch = COREFERENCE_PROPOSAL_BRANCH.fixed_branch
    if branch is None:
        raise ValueError("coreference proposal branch placement must be fixed")
    return branch


def derive_coreference_argument_id(supports: tuple[str, ...]) -> str:
    """Derive a deterministic ``cma:<sha>`` id from the supported claim ids.

    Identity is content-derived and provenance-free: proposing the same merge
    (the same set of supported claims) twice yields the same id, so a re-proposal
    is naturally idempotent and two distinct merges never collide. Order does not
    change the merge, so the ids are sorted before hashing.
    """

    payload = {"supports": sorted(supports)}
    return f"cma:{canonical_json_sha256(payload)}"


if TYPE_CHECKING:

    @dataclass(frozen=True)
    class CoreferenceMergeArgumentRef:
        argument_id: str

else:
    CoreferenceMergeArgumentRef = single_field_ref_type(
        "CoreferenceMergeArgumentRef", "argument_id", module=__name__
    )


_COREFERENCE_PLACEMENT: FlatYamlPlacement[object, CoreferenceMergeArgumentRef] = (
    FlatYamlPlacement(
        "coreference",
        CoreferenceMergeArgumentRef,
        ref_field="argument_id",
        codec="colon_to_double_underscore",
        branch=COREFERENCE_PROPOSAL_BRANCH,
    )
)


@charter(
    key="proposal_coreference",
    name="proposal_coreference",
    contract_version="2026.07.21",
    placement=_COREFERENCE_PLACEMENT,
    accessor="proposal_coreference",
    identity_field="argument_id",
)
class CoreferenceMergeArgumentDoc(CharterDoc):
    """A defeasible argument that some description claims corefer, stored as a proposal.

    The class *is* the document: ``argument_id`` is the content-derived identity,
    ``supports`` are the claim ids this argument would merge if accepted,
    ``description_claim_ids`` are the description claims it reasons over, and
    ``attacks`` are the ids of the rival merge arguments this one attacks. Every
    field mirrors the lemon
    :class:`~propstore.core.lemon.description_kinds.MergeArgument`; the app layer
    lowers a stored doc to that struct at render time.
    """

    argument_id: Annotated[str, charter_field(primary_key=True)]
    provenance: Annotated[Provenance, charter_field(json=True)]
    supports: Annotated[
        tuple[str, ...],
        charter_field(
            json=True,
            foreign_keys=(
                ForeignKeySpec(
                    name="coreference_supports",
                    contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                    source_family="proposal_coreference",
                    source_field="supports[]",
                    target_family="claim",
                    target_field="claim_id",
                    required=False,
                    many=True,
                ),
            ),
        ),
    ] = ()
    description_claim_ids: Annotated[
        tuple[str, ...],
        charter_field(
            json=True,
            foreign_keys=(
                ForeignKeySpec(
                    name="coreference_description_claims",
                    contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                    source_family="proposal_coreference",
                    source_field="description_claim_ids[]",
                    target_family="claim",
                    target_field="claim_id",
                    required=False,
                    many=True,
                ),
            ),
        ),
    ] = ()
    attacks: Annotated[tuple[str, ...], charter_field(json=True)] = ()
    note: str | None = None


@dataclass(frozen=True)
class _StoreOwner:
    """Placement owner for the document store (mirrors ``StanceRepository``)."""

    branch: str = "master"


class CoreferenceMergeArgumentRepository:
    """Author coreference merge-argument proposals and project EVERY one to a sidecar.

    Same shape as :class:`~propstore.families.relations.StanceRepository`: a
    charter-driven ``DocumentFamilyStore`` for the canonical document and a
    charter-derived sqlite sidecar. Because the charter's placement is fixed to
    ``proposal/coreference``, both authoring and iteration target that branch
    regardless of the store owner. The ``proposal_coreference`` table and its
    columns are exactly the charter's fields.
    """

    def __init__(self, backend: GitStore | None = None) -> None:
        self._store = DocumentFamilyStore(
            owner=_StoreOwner(),
            backend=backend if backend is not None else GitStore.init_memory(),
            codec=CoreferenceMergeArgumentDoc.__charter__.document_codec(),
        )
        self._family = CoreferenceMergeArgumentDoc.__charter__.family.artifact_family
        self._branch = coreference_proposal_branch()

    def author(self, document: CoreferenceMergeArgumentDoc, *, message: str) -> str:
        """Store the merge-argument proposal keyed by ``argument_id``; return sha."""

        return self._store.save(
            self._family,
            CoreferenceMergeArgumentRef(document.argument_id),
            document,
            message=message,
            branch=self._branch,
        )

    def get(self, argument_id: str) -> CoreferenceMergeArgumentDoc | None:
        """Load one merge-argument proposal by identity, or ``None``."""

        return self._store.load(
            self._family,
            CoreferenceMergeArgumentRef(argument_id),
            branch=self._branch,
        )

    def iter_arguments(self) -> Iterator[CoreferenceMergeArgumentDoc]:
        """Iterate every authored merge-argument proposal on the branch."""

        for handle in self._store.iter_handles(self._family, branch=self._branch):
            yield handle.document

    def build_sidecar(self, path: Path) -> SqlAlchemySchema:
        """Project EVERY authored merge-argument proposal into a fresh sqlite sidecar.

        Never filters: two mutually-attacking rival hypotheses both land as rows.
        Whether any merge survives is a render-time verdict under an argumentation
        semantics, never a build-time gate. Returns the built schema for reuse.
        """

        schema = build_sqlalchemy_schema(
            charter_catalog(CoreferenceMergeArgumentDoc.__charter__)
        )
        create_sqlalchemy_store(path, schema)
        with writable_session(path, schema) as session:
            for document in self.iter_arguments():
                session.add_family(
                    "proposal_coreference",
                    {
                        "argument_id": document.argument_id,
                        "supports": document.supports,
                        "description_claim_ids": document.description_claim_ids,
                        "attacks": document.attacks,
                        "provenance": document.provenance,
                        "note": document.note,
                    },
                )
            session.commit()
        return schema


def stated_provenance() -> Provenance:
    """The default provenance for an authored merge-argument proposal.

    A merge argument the author asserts carries ``STATED`` provenance — honest
    about being an assertion, never a fabricated measurement (CLAUDE.md).
    """

    return Provenance(status=ProvenanceStatus.STATED)
