"""Temporal storage families: frames, description anchors, happens-before edges.

The temporal layer stores ONLY authored artifacts (CLAUDE.md; ``temporal.py``
docstring; ``docs/event-semantics.md`` §5): a :class:`TemporalFrameDoc` declares
a totally-ordered timeline, a :class:`DescriptionTemporalAnchorDoc` places a claim
on that timeline with optional endpoint bounds, and a
:class:`HappensBeforeEdgeDoc` posits that one claim strictly precedes another under
a named :class:`~propstore.core.lemon.temporal.HappensBeforeAccount`. A *derived*
order — the BFS result, the judgment, any transitive closure — is NEVER stored:
it is recomputed per query from the live rows by
:func:`propstore.app.temporal.temporal_order_between`, so revision that defeats an
edge upstream reaches every verdict at the next query.

These are canonical AUTHORED EVIDENCE, so they follow the canonical-family
placement conventions (master branch, like :class:`~propstore.families.relations.Stance`),
NOT the proposal branch. Rival edges — even a cycle ``a -> b`` and ``b -> a`` — are
legitimate rival evidence and coexist as rows; the order query surfaces the
conflict as ``CONFLICTED`` with both witnessing paths rather than a build-time
gate collapsing one (non-commitment; :meth:`TemporalRepository.build_sidecar`
never filters).

Each doc mirrors a lemon compute struct field for field; the app layer lowers a
stored doc to that struct at query time (there is no second in-memory spelling —
the lemon struct is the compute form, this charter is the storage form, and
lowering is a construction, not a conversion). The account is stored as the one
canonical :class:`~propstore.core.lemon.temporal.HappensBeforeAccount`, never a
str mirror; it is mandatory, because defaulting an epistemic commitment would
fabricate one.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from quire.charter_class import CharterDoc, charter, charter_field
from quire.charters import charter_catalog
from quire.family_store import DocumentFamilyStore
from quire.git_store import GitStore
from quire.references import ForeignKeySpec
from quire.sqlalchemy_schema import SqlAlchemySchema, build_sqlalchemy_schema
from quire.sqlalchemy_store import create_sqlalchemy_store, writable_session

from propstore.core.lemon.temporal import HappensBeforeAccount
from propstore.families import SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION
from propstore.provenance import Provenance, ProvenanceStatus

_TEMPORAL_CONTRACT_VERSION = "2026.07.21"


@charter(
    key="temporal_frame",
    name="temporal_frame",
    contract_version=_TEMPORAL_CONTRACT_VERSION,
    placement="temporal_frame",
    identity_field="frame_id",
)
class TemporalFrameDoc(CharterDoc):
    """A declared frame of reference whose own timeline is totally ordered.

    Mirrors :class:`~propstore.core.lemon.temporal.TemporalFrame`: ``frame_id`` is
    the identity, ``description`` names the clock/sensor/narrative the frame
    declares, and ``provenance`` records who declared it.
    """

    frame_id: Annotated[str, charter_field(primary_key=True)]
    description: str
    provenance: Annotated[Provenance, charter_field(json=True)]


@charter(
    key="description_temporal_anchor",
    name="description_temporal_anchor",
    contract_version=_TEMPORAL_CONTRACT_VERSION,
    placement="description_temporal_anchor",
    identity_field="anchor_id",
)
class DescriptionTemporalAnchorDoc(CharterDoc):
    """The validity interval of a description claim within one declared frame.

    Mirrors :class:`~propstore.core.lemon.temporal.DescriptionTemporalAnchor`.
    ``claim_id`` and ``frame_id`` are foreign keys into the claim and frame
    families. Bounds are OPTIONAL: an absent ``valid_from``/``valid_until`` is
    honest ignorance (CLAUDE.md), not a fabricated coordinate; a present pair must
    satisfy ``valid_from <= valid_until``, rejected here exactly as the lemon
    struct rejects it.
    """

    anchor_id: Annotated[str, charter_field(primary_key=True)]
    claim_id: Annotated[
        str,
        charter_field(
            foreign_key=ForeignKeySpec(
                name="description_temporal_anchor_claim",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="description_temporal_anchor",
                source_field="claim_id",
                target_family="claim",
                target_field="claim_id",
                required=False,
            )
        ),
    ]
    frame_id: Annotated[
        str,
        charter_field(
            foreign_key=ForeignKeySpec(
                name="description_temporal_anchor_frame",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="description_temporal_anchor",
                source_field="frame_id",
                target_family="temporal_frame",
                target_field="frame_id",
                required=False,
            )
        ),
    ]
    provenance: Annotated[Provenance, charter_field(json=True)]
    valid_from: float | None = None
    valid_until: float | None = None

    def __post_init__(self) -> None:
        if (
            self.valid_from is not None
            and self.valid_until is not None
            and self.valid_from > self.valid_until
        ):
            raise ValueError(
                "description temporal anchor requires valid_from <= valid_until"
            )


@charter(
    key="happens_before_edge",
    name="happens_before_edge",
    contract_version=_TEMPORAL_CONTRACT_VERSION,
    placement="happens_before_edge",
    identity_field="edge_id",
)
class HappensBeforeEdgeDoc(CharterDoc):
    """Provenance-bearing evidence that one description strictly precedes another.

    Mirrors :class:`~propstore.core.lemon.temporal.HappensBeforeEdge`.
    ``earlier_claim_id`` and ``later_claim_id`` are foreign keys into the claim
    family. ``account`` is the mandatory
    :class:`~propstore.core.lemon.temporal.HappensBeforeAccount` — there is no
    default, because defaulting whether a posit may be chained would fabricate an
    epistemic commitment; a bogus account value is rejected here.
    """

    edge_id: Annotated[str, charter_field(primary_key=True)]
    earlier_claim_id: Annotated[
        str,
        charter_field(
            foreign_key=ForeignKeySpec(
                name="happens_before_edge_earlier_claim",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="happens_before_edge",
                source_field="earlier_claim_id",
                target_family="claim",
                target_field="claim_id",
                required=False,
            )
        ),
    ]
    later_claim_id: Annotated[
        str,
        charter_field(
            foreign_key=ForeignKeySpec(
                name="happens_before_edge_later_claim",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="happens_before_edge",
                source_field="later_claim_id",
                target_family="claim",
                target_field="claim_id",
                required=False,
            )
        ),
    ]
    account: HappensBeforeAccount
    provenance: Annotated[Provenance, charter_field(json=True)]

    def __post_init__(self) -> None:
        # Validate the account even when constructed directly (msgspec type-checks
        # only on decode); a bogus value is a rejected posit, not a silent default.
        HappensBeforeAccount(self.account)
        if self.earlier_claim_id == self.later_claim_id:
            raise ValueError(
                "happens-before edge must relate two distinct descriptions"
            )


@dataclass(frozen=True)
class _StoreOwner:
    """Placement owner for the document stores (mirrors ``StanceRepository``)."""

    branch: str = "master"


class TemporalRepository:
    """Author temporal frames/anchors/edges to git and project EVERY row to a sidecar.

    One repository over the three canonical charters, each backed by its own
    charter-driven ``DocumentFamilyStore`` on a shared git backend (the same shape
    as :class:`~propstore.families.relations.StanceRepository`, extended to three
    families). :meth:`build_sidecar` projects all three tables into one fresh
    sqlite sidecar and NEVER filters — rival cyclic edges both land as rows; the
    order verdict is a per-query decision, never a build-time gate.
    """

    def __init__(self, backend: GitStore | None = None) -> None:
        store_backend = backend if backend is not None else GitStore.init_memory()
        owner = _StoreOwner()
        self._frames = DocumentFamilyStore(
            owner=owner,
            backend=store_backend,
            codec=TemporalFrameDoc.__charter__.document_codec(),
        )
        self._anchors = DocumentFamilyStore(
            owner=owner,
            backend=store_backend,
            codec=DescriptionTemporalAnchorDoc.__charter__.document_codec(),
        )
        self._edges = DocumentFamilyStore(
            owner=owner,
            backend=store_backend,
            codec=HappensBeforeEdgeDoc.__charter__.document_codec(),
        )
        self._frame_family = TemporalFrameDoc.__charter__.family.artifact_family
        self._anchor_family = (
            DescriptionTemporalAnchorDoc.__charter__.family.artifact_family
        )
        self._edge_family = HappensBeforeEdgeDoc.__charter__.family.artifact_family

    # ── frames ───────────────────────────────────────────────────────────────

    def author_frame(self, document: TemporalFrameDoc, *, message: str) -> str:
        """Store the frame keyed by ``frame_id``; return commit sha."""

        return self._frames.save(
            self._frame_family, document.frame_id, document, message=message
        )

    def get_frame(self, frame_id: str) -> TemporalFrameDoc | None:
        """Load one frame by identity, or ``None``."""

        return self._frames.load(self._frame_family, frame_id)

    def iter_frames(self) -> Iterator[TemporalFrameDoc]:
        """Iterate every authored frame in the git store."""

        for handle in self._frames.iter_handles(self._frame_family):
            yield handle.document

    # ── anchors ──────────────────────────────────────────────────────────────

    def author_anchor(
        self, document: DescriptionTemporalAnchorDoc, *, message: str
    ) -> str:
        """Store the anchor keyed by ``anchor_id``; return commit sha."""

        return self._anchors.save(
            self._anchor_family, document.anchor_id, document, message=message
        )

    def get_anchor(self, anchor_id: str) -> DescriptionTemporalAnchorDoc | None:
        """Load one anchor by identity, or ``None``."""

        return self._anchors.load(self._anchor_family, anchor_id)

    def iter_anchors(self) -> Iterator[DescriptionTemporalAnchorDoc]:
        """Iterate every authored anchor in the git store."""

        for handle in self._anchors.iter_handles(self._anchor_family):
            yield handle.document

    # ── edges ────────────────────────────────────────────────────────────────

    def author_edge(self, document: HappensBeforeEdgeDoc, *, message: str) -> str:
        """Store the happens-before edge keyed by ``edge_id``; return commit sha."""

        return self._edges.save(
            self._edge_family, document.edge_id, document, message=message
        )

    def get_edge(self, edge_id: str) -> HappensBeforeEdgeDoc | None:
        """Load one edge by identity, or ``None``."""

        return self._edges.load(self._edge_family, edge_id)

    def iter_edges(self) -> Iterator[HappensBeforeEdgeDoc]:
        """Iterate every authored happens-before edge in the git store."""

        for handle in self._edges.iter_handles(self._edge_family):
            yield handle.document

    # ── projection ─────────────────────────────────────────────────────────────
    #
    # Each family projects into its OWN single-charter sidecar, exactly as every
    # canonical family does (StanceRepository, ClaimRepository, …). A single-charter
    # catalog does not materialize cross-family foreign keys (the claim/frame FKs
    # are registry-graph metadata, enforced by the world build, not by these
    # family-scoped projections), so an anchor may be projected before its claim or
    # frame is canonical — the non-blocking authoring discipline (CLAUDE.md
    # checklist) all the way to the read surface.

    def build_frame_sidecar(self, path: Path) -> SqlAlchemySchema:
        """Project EVERY authored frame into a fresh single-charter sqlite sidecar."""

        schema = build_sqlalchemy_schema(charter_catalog(TemporalFrameDoc.__charter__))
        create_sqlalchemy_store(path, schema)
        with writable_session(path, schema) as session:
            for frame in self.iter_frames():
                session.add_family(
                    "temporal_frame",
                    {
                        "frame_id": frame.frame_id,
                        "description": frame.description,
                        "provenance": frame.provenance,
                    },
                )
            session.commit()
        return schema

    def build_anchor_sidecar(self, path: Path) -> SqlAlchemySchema:
        """Project EVERY authored anchor into a fresh single-charter sqlite sidecar."""

        schema = build_sqlalchemy_schema(
            charter_catalog(DescriptionTemporalAnchorDoc.__charter__)
        )
        create_sqlalchemy_store(path, schema)
        with writable_session(path, schema) as session:
            for anchor in self.iter_anchors():
                session.add_family(
                    "description_temporal_anchor",
                    {
                        "anchor_id": anchor.anchor_id,
                        "claim_id": anchor.claim_id,
                        "frame_id": anchor.frame_id,
                        "provenance": anchor.provenance,
                        "valid_from": anchor.valid_from,
                        "valid_until": anchor.valid_until,
                    },
                )
            session.commit()
        return schema

    def build_edge_sidecar(self, path: Path) -> SqlAlchemySchema:
        """Project EVERY authored happens-before edge into a fresh sqlite sidecar.

        Never filters: rival cyclic edges both land as rows. Whether an order
        holds — or conflicts — is a per-query decision made by the app layer from
        these live rows, never a build-time gate.
        """

        schema = build_sqlalchemy_schema(
            charter_catalog(HappensBeforeEdgeDoc.__charter__)
        )
        create_sqlalchemy_store(path, schema)
        with writable_session(path, schema) as session:
            for edge in self.iter_edges():
                session.add_family(
                    "happens_before_edge",
                    {
                        "edge_id": edge.edge_id,
                        "earlier_claim_id": edge.earlier_claim_id,
                        "later_claim_id": edge.later_claim_id,
                        "account": edge.account,
                        "provenance": edge.provenance,
                    },
                )
            session.commit()
        return schema


def stated_provenance() -> Provenance:
    """The default provenance for an authored temporal artifact.

    Authored temporal evidence carries ``STATED`` provenance — honest about being
    an assertion, never a fabricated measurement (CLAUDE.md).
    """

    return Provenance(status=ProvenanceStatus.STATED)
