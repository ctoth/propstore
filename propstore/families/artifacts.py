"""Family-owned artifact projection, stamping, and verification."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from importlib import import_module
from typing import TYPE_CHECKING, Any, TypeAlias

from quire.projections import artifact_digest

from propstore.families.claims.declaration import (
    ClaimDocument,
    SourceClaimDocument,
    SourceJustificationDocument,
)
from propstore.families.sources.declaration import SOURCE_CHARTER, SourceDocument
from propstore.families.stances.declaration import (
    SourceStanceEntryDocument,
    StanceDocument,
)

if TYPE_CHECKING:
    from propstore.repository import Repository

JustificationDocument: TypeAlias = Any


@dataclass(frozen=True)
class ArtifactReference:
    family: str
    identity: str


@dataclass(frozen=True)
class ArtifactVerificationRecord:
    reference: ArtifactReference
    expected: str | None
    actual: str | None
    dependencies: tuple[ArtifactReference, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def status(self) -> str:
        return "ok" if self.expected == self.actual else "mismatch"


@dataclass(frozen=True)
class ArtifactVerificationIndex:
    records: dict[ArtifactReference, ArtifactVerificationRecord]
    claim_lookup: dict[str, ArtifactReference]
    source_by_claim: dict[str, ArtifactReference]

    def require_claim(self, claim_ref: str) -> ArtifactReference:
        resolved = self.claim_lookup.get(claim_ref)
        if resolved is None:
            raise ValueError(f"Unknown claim reference: {claim_ref}")
        return resolved


def _justification_document_type() -> type[Any]:
    return getattr(
        import_module("propstore.families.claims.declaration"),
        "JustificationDocument",
    )


def source_artifact_code(source_doc: SourceDocument) -> str:
    return artifact_digest(SOURCE_CHARTER, source_doc, omit_none=True)


def stamp_canonical_artifacts(
    source_doc: SourceDocument,
    claims: Sequence[ClaimDocument],
    justifications: Sequence[JustificationDocument],
    stances: Sequence[StanceDocument],
) -> tuple[
    SourceDocument,
    tuple[ClaimDocument, ...],
    tuple[JustificationDocument, ...],
    tuple[StanceDocument, ...],
]:
    source_code = source_artifact_code(source_doc)
    updated_source = _stamp_document(
        source_doc,
        SourceDocument,
        artifact_code=source_code,
        source="family-artifacts:source",
    )

    rewritten_justifications = tuple(
        _stamp_document(
            justification,
            _justification_document_type(),
            artifact_code=justification_artifact_code(justification),
            source="family-artifacts:canonical-justification",
        )
        for justification in justifications
    )
    rewritten_stances = tuple(
        _stamp_document(
            stance,
            StanceDocument,
            artifact_code=stance_artifact_code(stance),
            source="family-artifacts:canonical-stance",
        )
        for stance in stances
    )
    return updated_source, tuple(claims), rewritten_justifications, rewritten_stances


def stamp_source_artifacts(
    source_doc: SourceDocument,
    claims_doc: tuple[SourceClaimDocument, ...] | None,
    justifications_doc: tuple[SourceJustificationDocument, ...] | None,
    stances_doc: tuple[SourceStanceEntryDocument, ...] | None,
) -> tuple[
    SourceDocument,
    tuple[SourceClaimDocument, ...] | None,
    tuple[SourceJustificationDocument, ...] | None,
    tuple[SourceStanceEntryDocument, ...] | None,
]:
    source_code = source_artifact_code(source_doc)
    updated_source = _stamp_document(
        source_doc,
        SourceDocument,
        artifact_code=source_code,
        source="family-artifacts:source",
    )

    justification_codes_by_conclusion: dict[str, list[str]] = defaultdict(list)
    rewritten_justifications: list[SourceJustificationDocument] = []
    for justification in () if justifications_doc is None else justifications_doc:
        artifact_code = justification_artifact_code(justification)
        rewritten = _stamp_document(
            justification,
            SourceJustificationDocument,
            artifact_code=artifact_code,
            source="family-artifacts:source-justification",
        )
        conclusion = rewritten.conclusion
        if isinstance(conclusion, str) and conclusion:
            justification_codes_by_conclusion[conclusion].append(artifact_code)
        rewritten_justifications.append(rewritten)

    stance_codes_by_source: dict[str, list[str]] = defaultdict(list)
    rewritten_stances: list[SourceStanceEntryDocument] = []
    for stance in () if stances_doc is None else stances_doc:
        artifact_code = stance_artifact_code(stance)
        rewritten = _stamp_document(
            stance,
            SourceStanceEntryDocument,
            artifact_code=artifact_code,
            source="family-artifacts:source-stance",
        )
        source_claim = rewritten.source_claim
        if isinstance(source_claim, str) and source_claim:
            stance_codes_by_source[source_claim].append(artifact_code)
        rewritten_stances.append(rewritten)

    rewritten_claims: list[SourceClaimDocument] = []
    for claim in () if claims_doc is None else claims_doc:
        claim_id = claim.artifact_id
        artifact_code = claim_artifact_code(
            claim,
            source_code=source_code,
            justification_codes=justification_codes_by_conclusion.get(
                str(claim_id), []
            ),
            stance_codes=stance_codes_by_source.get(str(claim_id), []),
        )
        rewritten_claims.append(
            _stamp_document(
                claim,
                SourceClaimDocument,
                artifact_code=artifact_code,
                source="family-artifacts:source-claim",
            )
        )

    return (
        updated_source,
        None if claims_doc is None else tuple(rewritten_claims),
        None if justifications_doc is None else tuple(rewritten_justifications),
        None if stances_doc is None else tuple(rewritten_stances),
    )


def build_artifact_verification_index(
    repo: Repository,
    *,
    commit: str | None = None,
) -> ArtifactVerificationIndex:
    records: dict[ArtifactReference, ArtifactVerificationRecord] = {}
    claim_lookup: dict[str, ArtifactReference] = {}
    source_by_claim: dict[str, ArtifactReference] = {}
    justifications_by_conclusion: dict[str, list[ArtifactReference]] = defaultdict(list)
    stances_by_source: dict[str, list[ArtifactReference]] = defaultdict(list)

    sources_by_slug = {
        handle.ref.name: handle.document
        for handle in repo.families.sources.iter_handles(commit=commit)
    }
    for source_slug, source_doc in sources_by_slug.items():
        ref = ArtifactReference("source", source_slug)
        records[ref] = ArtifactVerificationRecord(
            reference=ref,
            expected=source_doc.artifact_code,
            actual=source_artifact_code(source_doc),
            metadata={"source": source_slug},
        )

    for handle in repo.families.justifications.iter_handles(commit=commit):
        doc = handle.document
        identity = str(doc.id or handle.ref.artifact_id)
        ref = ArtifactReference("justification", identity)
        records[ref] = ArtifactVerificationRecord(
            reference=ref,
            expected=doc.artifact_code,
            actual=justification_artifact_code(doc),
            metadata={
                "id": identity,
                "conclusion": doc.conclusion,
                "premises": tuple(doc.premises),
            },
        )
        if isinstance(doc.conclusion, str) and doc.conclusion:
            justifications_by_conclusion[doc.conclusion].append(ref)

    for handle in repo.families.stances.iter_handles(commit=commit):
        doc = handle.document
        identity = str(doc.artifact_id or handle.ref.artifact_id)
        ref = ArtifactReference("stance", identity)
        records[ref] = ArtifactVerificationRecord(
            reference=ref,
            expected=doc.artifact_code,
            actual=stance_artifact_code(doc),
            metadata={
                "source_claim": doc.source_claim,
                "target": doc.target,
                "type": str(doc.type),
            },
        )
        if isinstance(doc.source_claim, str) and doc.source_claim:
            stances_by_source[doc.source_claim].append(ref)

    for handle in repo.families.claims.iter_handles(commit=commit):
        claim = handle.document
        claim_id = claim.artifact_id
        if not isinstance(claim_id, str) or not claim_id:
            continue
        source = claim.source
        provenance = claim.provenance
        source_slug = (
            source.paper
            if source is not None
            else (
                provenance.paper
                if provenance is not None and provenance.paper is not None
                else handle.ref.artifact_id
            )
        )
        source_ref = ArtifactReference("source", source_slug)
        source_record = records.get(source_ref)
        source_code = "" if source_record is None else str(source_record.actual or "")
        justification_refs = tuple(justifications_by_conclusion.get(claim_id, ()))
        stance_refs = tuple(stances_by_source.get(claim_id, ()))
        actual = claim_artifact_code(
            claim,
            source_code=source_code,
            justification_codes=[
                str(records[ref].actual or "") for ref in justification_refs
            ],
            stance_codes=[str(records[ref].actual or "") for ref in stance_refs],
        )
        claim_ref = ArtifactReference("claim", claim_id)
        records[claim_ref] = ArtifactVerificationRecord(
            reference=claim_ref,
            expected=claim.artifact_code or actual,
            actual=actual,
            dependencies=(source_ref, *justification_refs, *stance_refs),
            metadata={"claim_id": claim_id, "source": source_slug},
        )
        claim_lookup[claim_id] = claim_ref
        source_by_claim[claim_id] = source_ref
        primary_logical_id = getattr(claim, "primary_logical_id", None)
        if isinstance(primary_logical_id, str) and primary_logical_id:
            claim_lookup[primary_logical_id] = claim_ref
            claim_lookup[primary_logical_id.split(":", 1)[-1]] = claim_ref

    return ArtifactVerificationIndex(
        records=records,
        claim_lookup=claim_lookup,
        source_by_claim=source_by_claim,
    )
