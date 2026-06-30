"""The semantic-import normalization pipeline.

This is the set of passes that turn an external import's typed candidate rows
(:mod:`propstore.importing.contract`) into the canonical source-branch shape
*before* they are written, then write them through the ordinary source-authoring
path (8-2). The passes are, per family:

* **type coercion** — map the typed import rows onto the source-branch nested
  structs (:class:`SourceConceptEntryDocument`, :class:`SourceClaimDocument`,
  :class:`SourceStanceEntryDocument`);
* **dedup-to-handle** — detect two rows colliding on one source-local handle and
  record a warning (never drop a rival — non-commitment);
* **identity assignment** — stamp each claim's content-stable ``artifact_id`` /
  ``version_id`` / ``logical_ids`` via :func:`normalize_source_claims_payload`;
* **reference lowering** — resolve a stance's source-local claim handles to the
  just-assigned canonical claim ids via quire's ``FamilyReferenceIndex``.

There is no separate pass-runner framework here: a repository import runs few,
fixed passes in foreign-key order (concepts, then claims, then stances), and the
ordering is expressed directly. The generic build/validate pass framework is a
Phase-9 concern.

Crucially, an imported row is *not* truth. It flows onto the source branch as a
defeasible claim with provenance and is then subject to the normal finalize ->
promote lifecycle — no truth-gate, no privileged write
([[feedback_imports_are_opinions]]).
"""

from __future__ import annotations

from dataclasses import dataclass

from propstore.families.registry import SourceRef
from propstore.families.sources import (
    ClaimSourceDocument,
    SourceClaimDocument,
    SourceClaimsDocument,
    SourceConceptEntryDocument,
    SourceConceptsDocument,
    SourceStanceEntryDocument,
    SourceStancesDocument,
)
from propstore.importing.contract import (
    ImportClaimRow,
    ImportConceptRow,
    ImportManifest,
    ImportStanceRow,
)
from propstore.repository import Repository
from propstore.source.claims import (
    normalize_source_claims_payload,
    validate_source_claim_cel_expressions,
    validate_source_claim_concepts,
    validate_source_claim_value_bounds,
)
from propstore.source.common import (
    load_source_document,
    normalize_source_slug,
    source_tag_uri,
)
from propstore.source.concepts import normalize_source_concepts_document
from propstore.source.reference_indexes import primary_claim_index, source_claim_index
from propstore.source.relations import normalize_source_stances_payload


@dataclass(frozen=True)
class ImportPipelineResult:
    """The per-family write counts and non-fatal warnings of one import run."""

    concept_count: int
    claim_count: int
    stance_count: int
    warnings: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Type-coercion passes: typed import rows -> source-branch nested structs
# ---------------------------------------------------------------------------


def coerce_concept_rows(
    rows: tuple[ImportConceptRow, ...],
) -> tuple[SourceConceptsDocument, tuple[str, ...]]:
    """Coerce concept rows to a raw concepts document, flagging handle collisions."""

    seen: set[str] = set()
    warnings: list[str] = []
    entries: list[SourceConceptEntryDocument] = []
    for row in rows:
        if row.local_name in seen:
            warnings.append(f"duplicate imported concept handle {row.local_name!r}")
        seen.add(row.local_name)
        entries.append(
            SourceConceptEntryDocument(
                local_name=row.local_name,
                proposed_name=row.local_name,
                definition=row.definition,
                form=row.form,
            )
        )
    return SourceConceptsDocument(concepts=tuple(entries)), tuple(warnings)


def coerce_claim_rows(
    rows: tuple[ImportClaimRow, ...],
    *,
    paper: str,
) -> tuple[SourceClaimsDocument, tuple[str, ...]]:
    """Coerce claim rows to a raw claims document, flagging handle collisions."""

    seen: set[str] = set()
    warnings: list[str] = []
    claims: list[SourceClaimDocument] = []
    for row in rows:
        if row.local_id in seen:
            warnings.append(f"duplicate imported claim handle {row.local_id!r}")
        seen.add(row.local_id)
        claims.append(
            SourceClaimDocument(
                id=row.local_id,
                type=row.claim_type,
                context=row.context,
                statement=row.statement,
                concept=row.concept,
                concepts=row.concepts,
                conditions=row.conditions,
                value=row.value,
                unit=row.unit,
                notes=row.notes,
            )
        )
    document = SourceClaimsDocument(
        claims=tuple(claims),
        source=ClaimSourceDocument(paper=paper),
    )
    return document, tuple(warnings)


def coerce_stance_rows(
    rows: tuple[ImportStanceRow, ...],
) -> SourceStancesDocument:
    """Coerce stance rows to a raw stances document (handles lowered later)."""

    return SourceStancesDocument(
        stances=tuple(
            SourceStanceEntryDocument(
                source_claim=row.source_claim,
                target=row.target,
                type=row.stance_type,
                strength=row.strength,
                note=row.note,
            )
            for row in rows
        )
    )


# ---------------------------------------------------------------------------
# The pipeline: coerce -> validate -> normalize -> write, in FK order
# ---------------------------------------------------------------------------


def run_import_pipeline(
    repo: Repository,
    source_name: str,
    manifest: ImportManifest,
) -> ImportPipelineResult:
    """Normalize and write a manifest's rows onto an existing source branch.

    The source branch must already exist (see
    :func:`propstore.source.common.init_source_branch`). Families are written in
    foreign-key order — concepts first (so a claim's concept handle is known to
    the branch), then claims (so their canonical ids exist), then stances (whose
    handles are lowered against the just-written claims).
    """

    warnings: list[str] = list(manifest.warnings)
    slug = normalize_source_slug(source_name)
    ref = SourceRef(source_name)

    concept_count = _write_concepts(repo, source_name, ref, manifest, warnings)
    claim_count = _write_claims(repo, source_name, ref, slug, manifest, warnings)
    stance_count = _write_stances(repo, source_name, ref, manifest, warnings)

    return ImportPipelineResult(
        concept_count=concept_count,
        claim_count=claim_count,
        stance_count=stance_count,
        warnings=tuple(warnings),
    )


def _write_concepts(
    repo: Repository,
    source_name: str,
    ref: SourceRef,
    manifest: ImportManifest,
    warnings: list[str],
) -> int:
    if not manifest.concepts:
        return 0
    raw, concept_warnings = coerce_concept_rows(manifest.concepts)
    warnings.extend(concept_warnings)
    normalized = normalize_source_concepts_document(repo, raw)
    repo.families.source_concepts.save(
        ref,
        normalized,
        message=f"Import concepts for {normalize_source_slug(source_name)}",
    )
    return len(normalized.concepts)


def _write_claims(
    repo: Repository,
    source_name: str,
    ref: SourceRef,
    slug: str,
    manifest: ImportManifest,
    warnings: list[str],
) -> int:
    if not manifest.claims:
        return 0
    raw, claim_warnings = coerce_claim_rows(manifest.claims, paper=slug)
    warnings.extend(claim_warnings)
    validate_source_claim_concepts(repo, source_name, raw)
    validate_source_claim_cel_expressions(repo, source_name, raw)
    validate_source_claim_value_bounds(repo, source_name, raw)
    source_doc = load_source_document(repo, source_name)
    normalized, _ = normalize_source_claims_payload(
        raw,
        source_uri=source_doc.id or source_tag_uri(repo, source_name),
        source_namespace=slug,
    )
    repo.families.source_claims.save(
        ref,
        normalized,
        message=f"Import claims for {slug}",
    )
    return len(normalized.claims)


def _write_stances(
    repo: Repository,
    source_name: str,
    ref: SourceRef,
    manifest: ImportManifest,
    warnings: list[str],
) -> int:
    del warnings
    if not manifest.stances:
        return 0
    raw = coerce_stance_rows(manifest.stances)
    normalized = normalize_source_stances_payload(
        raw,
        claim_index=source_claim_index(repo, source_name),
        primary_claim_index=primary_claim_index(repo),
    )
    repo.families.source_stances.save(
        ref,
        normalized,
        message=f"Import stances for {normalize_source_slug(source_name)}",
    )
    return len(normalized.stances)
