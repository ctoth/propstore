"""Family-owned artifact projection, stamping, and verification."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeAlias, cast

from quire import canonical_json_sha256
from quire.charters import FamilyCharter
from quire.documents import convert_document_value, document_to_payload
from quire.projections import artifact_digest, artifact_payload

from propstore.core.labels import Label
from propstore.families.claims.declaration import (
    AUTHORED_CLAIM_CHARTER,
    JUSTIFICATION_CHARTER,
    ClaimDocument,
)
from propstore.families.documents.sources import (
    SourceClaimDocument,
    SourceJustificationDocument,
    SourceStanceEntryDocument,
)
from propstore.families.identity.claims import canonicalize_claim_for_version
from propstore.families.sources.declaration import SOURCE_CHARTER, SourceDocument
from propstore.families.sources.declaration import source_document_payload
from propstore.families.stances.declaration import STANCE_CHARTER, StanceDocument
from propstore.uri import ni_uri_for_file

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


def _projected_payload(
    charter: FamilyCharter,
    document: object,
    *,
    omit_none: bool = False,
) -> dict[str, Any]:
    payload = artifact_payload(charter, document, omit_none=omit_none)
    if not isinstance(payload, dict):
        raise TypeError(f"{charter.family.name} artifact payload must be a mapping")
    return payload


def _hash_payload(payload: object) -> str:
    return canonical_json_sha256(payload)


def source_artifact_code(source_doc: SourceDocument) -> str:
    return artifact_digest(SOURCE_CHARTER, source_doc, omit_none=True)


def justification_artifact_code(
    justification: JustificationDocument | SourceJustificationDocument,
) -> str:
    canonical = (
        _projected_payload(JUSTIFICATION_CHARTER, justification, omit_none=True)
        if hasattr(justification, "conclusion_claim_id")
        else document_to_payload(justification)
    )
    if not isinstance(canonical, dict):
        raise TypeError("justification artifact payload must be a mapping")
    canonical.pop("artifact_code", None)
    premises = canonical.get("premises")
    if isinstance(premises, list):
        canonical["premises"] = [str(premise) for premise in sorted(premises, key=str)]
    return _hash_payload(canonical)


def stance_artifact_code(stance: StanceDocument | SourceStanceEntryDocument) -> str:
    canonical = (
        _projected_payload(STANCE_CHARTER, stance, omit_none=True)
        if hasattr(stance, "artifact_id")
        else document_to_payload(stance)
    )
    if not isinstance(canonical, dict):
        raise TypeError("stance artifact payload must be a mapping")
    canonical.pop("artifact_id", None)
    canonical.pop("artifact_code", None)
    for field_name in tuple(canonical):
        if canonical[field_name] is None:
            canonical.pop(field_name)
    return _hash_payload(canonical)


def claim_artifact_code(
    claim: ClaimDocument | SourceClaimDocument,
    *,
    source_code: str,
    justification_codes: Sequence[str],
    stance_codes: Sequence[str],
) -> str:
    projected = (
        _projected_payload(AUTHORED_CLAIM_CHARTER, claim, omit_none=True)
        if isinstance(claim, ClaimDocument)
        else document_to_payload(claim)
    )
    if not isinstance(projected, dict):
        raise TypeError("claim artifact payload must be a mapping")
    canonical = canonicalize_claim_for_version(cast(dict[str, Any], projected))
    canonical.pop("artifact_code", None)
    return _hash_payload(
        {
            "source_artifact_code": source_code,
            "claim": canonical,
            "justification_codes": sorted(justification_codes),
            "stance_codes": sorted(stance_codes),
        }
    )


def _stamp_document(
    document: object,
    document_type: type[Any],
    *,
    artifact_code: str,
    source: str,
) -> Any:
    payload = document_to_payload(document)
    if not isinstance(payload, dict):
        raise TypeError("artifact-stamped document payload must be a mapping")
    payload["artifact_code"] = artifact_code
    return convert_document_value(payload, document_type, source=source)


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
    for justification in (() if justifications_doc is None else justifications_doc):
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
    for stance in (() if stances_doc is None else stances_doc):
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
    for claim in (() if claims_doc is None else claims_doc):
        claim_id = claim.artifact_id
        artifact_code = claim_artifact_code(
            claim,
            source_code=source_code,
            justification_codes=justification_codes_by_conclusion.get(str(claim_id), []),
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
                str(records[ref].actual or "")
                for ref in justification_refs
            ],
            stance_codes=[
                str(records[ref].actual or "")
                for ref in stance_refs
            ],
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


def _claim_dependency_targets(
    record: ArtifactVerificationRecord,
    records: dict[ArtifactReference, ArtifactVerificationRecord],
) -> Iterable[str]:
    for dependency in record.dependencies:
        dep_record = records.get(dependency)
        if dep_record is None:
            continue
        if dependency.family == "justification":
            premises = dep_record.metadata.get("premises", ())
            if not isinstance(premises, tuple):
                continue
            for premise in premises:
                if isinstance(premise, str) and premise:
                    yield premise
        elif dependency.family == "stance":
            target = dep_record.metadata.get("target")
            if isinstance(target, str) and target:
                yield target


def _serialize_label(label: Label | None) -> list[list[str]] | None:
    if label is None:
        return None
    return [list(environment.assumption_ids) for environment in label.environments]


def _verify_origin(repo: Repository, source_slug: str, source_doc: dict[str, Any]) -> dict[str, Any]:
    raw_origin = source_doc.get("origin")
    if raw_origin is None:
        origin: dict[str, Any] = {}
    elif isinstance(raw_origin, dict):
        origin = raw_origin
    else:
        raise ValueError(f"source {source_slug}: origin must be a mapping")
    expected = origin.get("content_ref")
    if not isinstance(expected, str) or not expected:
        return {"status": "unavailable", "path": None, "expected": expected, "actual": None}

    value = origin.get("value")
    candidates: list[Path] = []
    if isinstance(value, str) and value:
        value_path = Path(value)
        if value_path.is_absolute():
            candidates.append(value_path)
        candidates.append(repo.root.parent / "papers" / source_slug / value_path.name)
    candidates.append(repo.root.parent / "papers" / source_slug / "paper.pdf")

    for candidate in candidates:
        if not candidate.exists() or not candidate.is_file():
            continue
        actual = ni_uri_for_file(candidate)
        return {
            "status": "matched" if actual == expected else "mismatch",
            "path": str(candidate),
            "expected": expected,
            "actual": actual,
        }
    return {"status": "unavailable", "path": None, "expected": expected, "actual": None}


def verify_claim_tree(repo: Repository, claim_ref: str, *, commit: str | None = None) -> dict[str, Any]:
    index = build_artifact_verification_index(repo, commit=commit)
    try:
        root_ref = index.require_claim(claim_ref)
    except ValueError:
        from propstore.world.model import WorldQuery

        try:
            wm = WorldQuery(repo)
        except FileNotFoundError:
            wm = None
        if wm is not None:
            try:
                resolved_claim = wm.get_claim(claim_ref)
            finally:
                wm.close()
            if resolved_claim is not None:
                root_ref = index.require_claim(str(resolved_claim.id))
            else:
                raise
        else:
            raise

    visited_claims: set[ArtifactReference] = set()
    visited_nonclaims: set[ArtifactReference] = set()
    claim_reports: list[dict[str, Any]] = []
    justification_reports: list[dict[str, Any]] = []
    stance_reports: list[dict[str, Any]] = []
    source_reports: dict[str, dict[str, Any]] = {}
    overall_status = "ok"

    def record_mismatch(record: ArtifactVerificationRecord) -> None:
        nonlocal overall_status
        if record.status != "ok":
            overall_status = "mismatch"

    def visit_claim(current_ref: ArtifactReference) -> None:
        if current_ref in visited_claims:
            return
        visited_claims.add(current_ref)
        record = index.records[current_ref]
        record_mismatch(record)
        claim_id = str(record.metadata["claim_id"])
        claim_reports.append(
            {
                "claim_id": claim_id,
                "expected": record.expected,
                "actual": record.actual,
                "status": record.status,
            }
        )

        for dependency in record.dependencies:
            dep_record = index.records.get(dependency)
            if dep_record is None:
                continue
            record_mismatch(dep_record)
            if dependency.family == "source":
                source_slug = str(dep_record.metadata["source"])
                if source_slug not in source_reports:
                    source_reports[source_slug] = {
                        "source": source_slug,
                        "expected": dep_record.expected,
                        "actual": dep_record.actual,
                        "status": dep_record.status,
                    }
                continue
            if dependency in visited_nonclaims:
                continue
            visited_nonclaims.add(dependency)
            if dependency.family == "justification":
                justification_reports.append(
                    {
                        "id": dep_record.metadata.get("id"),
                        "expected": dep_record.expected,
                        "actual": dep_record.actual,
                        "status": dep_record.status,
                    }
                )
            elif dependency.family == "stance":
                stance_reports.append(
                    {
                        "source_claim": dep_record.metadata.get("source_claim"),
                        "target": dep_record.metadata.get("target"),
                        "type": dep_record.metadata.get("type"),
                        "expected": dep_record.expected,
                        "actual": dep_record.actual,
                        "status": dep_record.status,
                    }
                )
        for target_claim_id in _claim_dependency_targets(record, index.records):
            target_ref = index.claim_lookup.get(target_claim_id)
            if target_ref is not None:
                visit_claim(target_ref)

    visit_claim(root_ref)

    atms_label = None
    from propstore.world.model import WorldQuery
    from propstore.world.types import Environment

    try:
        wm = WorldQuery(repo)
    except FileNotFoundError:
        wm = None
    if wm is not None:
        try:
            bound = wm.bind(Environment())
            atms_label = _serialize_label(bound.atms_engine().claim_label(root_ref.identity))
        finally:
            wm.close()

    source_ref = index.source_by_claim[root_ref.identity]
    source_slug = source_ref.identity
    source_doc = next(
        (
            handle.document
            for handle in repo.families.sources.iter_handles(commit=commit)
            if handle.ref.name == source_slug
        ),
        None,
    )
    origin_verification = _verify_origin(
        repo,
        source_slug,
        {} if source_doc is None else source_document_payload(source_doc),
    )

    return {
        "claim_id": root_ref.identity,
        "status": overall_status if origin_verification["status"] != "mismatch" else "mismatch",
        "claim": claim_reports[0],
        "claims": claim_reports,
        "justifications": justification_reports,
        "stances": stance_reports,
        "sources": list(source_reports.values()),
        "origin_verification": origin_verification,
        "atms_label": atms_label,
    }
