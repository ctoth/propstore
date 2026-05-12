"""Source-branch promotion.

Schema-v3 partial-promotion behavior (``reviews/2026-04-16-code-review/
workstreams/ws-z-render-gates.md`` axis-1 finding 3.3): the former
all-or-nothing ``report.status != 'ready'`` gate is replaced with a
per-item filter. Valid claims promote to the primary branch; claims with
per-item finalize errors stay on the source branch with a
``promotion_status='blocked'`` sidecar mirror row plus a
``build_diagnostics`` row (``diagnostic_kind='promotion_blocked'``,
``blocking=1``).

The ``strict=True`` keyword argument preserves the old abort behavior
for callers that explicitly opt in. Per the standing discipline (rule 6:
no backward-compat shims), ``strict`` is the *only* exception and is
documented here because Q explicitly authorized partial promotion as a
behavioral change.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from propstore.artifact_codes import stamp_canonical_artifact_codes
from propstore.families.identity.concepts import normalize_canonical_concept_payload
from propstore.claims import ClaimFileEntry, loaded_claim_file_from_payload
from propstore.compiler.context import build_compilation_context_from_loaded
from propstore.compiler.errors import CompilerWorkflowError
from propstore.families.claims.passes import run_claim_pipeline
from propstore.families.claims.stages import ClaimAuthoredFiles
from propstore.families.registry import (
    CanonicalSourceRef,
    ClaimRef,
    ConceptFileRef,
    JustificationRef,
    MicropublicationRef,
    SourceRef,
    StanceRef,
)
from propstore.families.concepts.documents import ConceptDocument
from propstore.families.concepts.stages import (
    LoadedConcept,
    parse_concept_record_document,
)
from propstore.families.claims.documents import ClaimDocument
from propstore.families.contexts.stages import parse_context_record_document
from propstore.families.documents.micropubs import MicropublicationDocument, MicropublicationsFileDocument
from propstore.families.documents.justifications import JustificationDocument
from propstore.families.forms.stages import parse_form
from propstore.provenance import (
    Provenance,
    ProvenanceStatus,
    ProvenanceWitness,
    write_provenance_note,
)
from propstore.repository import Repository
from propstore.sidecar.sqlite import connect_sidecar
from propstore.source.claim_concepts import (
    normalize_promoted_source_claim_artifact,
    source_concept_ref_requires_mapping,
)
from quire.documents import convert_document_value
from propstore.families.documents.sources import (
    SourceClaimDocument,
    SourceClaimsDocument,
    SourceConceptEntryDocument,
    SourceDocument,
    SourceJustificationsDocument,
    SourceStancesDocument,
    SourceTrustDocument,
)
from propstore.source_trust_argumentation import SourceTrustResult, calibrate_source_trust
from propstore.families.documents.stances import StanceDocument
from propstore.families.identity.justifications import derive_justification_artifact_id
from propstore.families.identity.stances import derive_stance_artifact_id

from .common import (
    load_source_claims_document,
    load_source_concepts_document,
    load_source_document,
    load_source_finalize_report,
    load_source_justifications_document,
    load_source_micropubs_document,
    load_source_stances_document,
    utc_now,
    normalize_source_slug,
    source_branch_name,
    source_paper_slug,
)
from .registry import load_primary_branch_concepts
from .reference_indexes import (
    primary_claim_index as build_primary_claim_index,
    resolve_source_or_primary_claim_id,
    source_claim_index as build_source_claim_index,
)
from .stages import SourcePromotionPlan


@dataclass(frozen=True)
class SourceConceptPromotionResolution:
    concept_map: dict[str, str]
    promoted_concept_documents: dict[str, ConceptDocument]
    blocked_concept_refs: dict[str, str]


@dataclass(frozen=True)
class PromotionResult:
    commit_sha: str
    blocked_claims: tuple[SourceClaimDocument, ...]
    blocked_diagnostics: dict[str, tuple[tuple[str, str], ...]]
    sidecar_mirror_ok: bool
    sidecar_mirror_error: str | None = None


def _validate_promoted_claims_before_commit(
    repo: Repository,
    *,
    promoted_claim_documents: dict[ClaimRef, ClaimDocument],
    promoted_concept_documents: dict[ConceptFileRef, ConceptDocument],
) -> None:
    """Validate the canonical claim view that promotion is about to commit."""

    head_sha = repo.snapshot.head_sha()
    tree = repo.snapshot.tree(commit=head_sha)

    concepts_by_name = {
        handle.ref.name: handle.document
        for handle in repo.families.concepts.iter_handles(commit=head_sha)
    }
    concepts_by_name.update(
        {
            concept_ref.name: concept_document
            for concept_ref, concept_document in promoted_concept_documents.items()
        }
    )
    concepts: list[LoadedConcept] = []
    for concept_name, concept_document in concepts_by_name.items():
        concept_ref = ConceptFileRef(concept_name)
        concepts.append(
            LoadedConcept(
                filename=concept_name,
                source_path=tree / repo.families.concepts.address(concept_ref).require_path(),
                knowledge_root=tree,
                record=parse_concept_record_document(concept_document),
                document=concept_document,
            )
        )

    form_registry = {}
    for handle in repo.families.forms.iter_handles(commit=head_sha):
        document = handle.document
        form_registry[document.name] = parse_form(document.name, document)

    context_ids: set[str] = set()
    for handle in repo.families.contexts.iter_handles(commit=head_sha):
        record = parse_context_record_document(handle.document)
        if record.context_id is not None:
            context_ids.add(str(record.context_id))

    claim_files: list[ClaimFileEntry] = [
        handle
        for handle in repo.families.claims.iter_handles(commit=head_sha)
        if handle.ref not in promoted_claim_documents
    ]
    for claim_ref, claim_document in promoted_claim_documents.items():
        claim_files.append(
            loaded_claim_file_from_payload(
                filename=claim_ref.artifact_id,
                source_path=tree / repo.families.claims.address(claim_ref).require_path(),
                data=claim_document.to_payload(),
                knowledge_root=tree,
            )
        )

    compilation_context = build_compilation_context_from_loaded(
        concepts,
        form_registry=form_registry,
        claim_files=claim_files,
        context_ids=context_ids or None,
    )
    claim_pipeline_result = run_claim_pipeline(
        ClaimAuthoredFiles.from_sequence(
            claim_files,
            compilation_context,
            context_ids=context_ids or None,
        )
    )
    claim_errors = tuple(
        diagnostic
        for diagnostic in claim_pipeline_result.diagnostics
        if diagnostic.level == "error"
        and (
            form_registry
            or "is missing a loaded form definition" not in diagnostic.message
        )
    )
    if claim_errors:
        raise CompilerWorkflowError(
            f"Source promotion aborted: {len(claim_errors)} promoted claim validation error(s)",
            claim_errors,
        )


def _source_trust_payload(result: SourceTrustResult) -> dict[str, Any]:
    trust = SourceTrustDocument(
        status=result.status,
        prior_base_rate=result.prior_base_rate,
        derived_from=tuple(firing.rule_id for firing in result.derived_from),
    )
    return trust.to_payload()


def _commit_promote_time_trust_calibration(
    repo: Repository,
    source_name: str,
    *,
    promotion_commit_sha: str,
) -> str | None:
    calibration = calibrate_source_trust(
        repo,
        source_name,
        world_snapshot=promotion_commit_sha,
    )
    source_doc = load_source_document(repo, source_name)
    updated_payload = source_doc.to_payload()
    updated_payload["trust"] = _source_trust_payload(calibration)
    if updated_payload["trust"] == source_doc.trust.to_payload():
        return None
    updated_source_doc = convert_document_value(
        updated_payload,
        SourceDocument,
        source=f"{source_branch_name(source_name)}:source.yaml",
    )
    return repo.families.source_documents.save(
        SourceRef(source_name),
        updated_source_doc,
        message=f"Calibrate source trust for {source_paper_slug(source_name)}",
    )


def _freeze_blocked_diagnostics(
    reasons: dict[str, list[tuple[str, str]]],
) -> dict[str, tuple[tuple[str, str], ...]]:
    return {claim_id: tuple(entries) for claim_id, entries in reasons.items()}


def _source_claim_concept_refs(claim) -> tuple[str, ...]:
    refs: list[str] = []
    for value in (claim.concept, claim.target_concept):
        if isinstance(value, str):
            refs.append(value)
    refs.extend(value for value in claim.concepts if isinstance(value, str))
    variables = claim.variables
    if isinstance(variables, tuple):
        refs.extend(
            variable.concept
            for variable in variables
            if isinstance(variable.concept, str)
        )
    refs.extend(
        parameter.concept
        for parameter in claim.parameters
        if isinstance(parameter.concept, str)
    )
    return tuple(refs)


def _promoted_claim_source_paper(
    claims_doc: SourceClaimsDocument | None,
    *,
    fallback_slug: str,
) -> str:
    if claims_doc is None or claims_doc.source is None:
        return fallback_slug
    return str(claims_doc.source.paper or fallback_slug)


def _promoted_claim_document(
    repo: Repository,
    claim: SourceClaimDocument,
    *,
    concept_map: dict[str, str],
    unresolved_concepts: set[str],
    source_paper: str,
) -> ClaimDocument:
    artifact_id = claim.artifact_id
    if not isinstance(artifact_id, str) or not artifact_id:
        raise ValueError("promoted claim is missing artifact_id")
    claim_ref = ClaimRef(artifact_id)
    return normalize_promoted_source_claim_artifact(
        claim,
        source_paper=source_paper,
        concept_map=concept_map,
        unresolved=unresolved_concepts,
        source=repo.families.claims.address(claim_ref).require_path(),
    ).document


def _filter_promoted_micropubs(
    micropubs_doc: MicropublicationsFileDocument | None,
    *,
    valid_artifact_ids: set[str],
) -> tuple[MicropublicationDocument, ...]:
    if micropubs_doc is None:
        return ()
    kept = tuple(
        micropub
        for micropub in micropubs_doc.micropubs
        if all(claim_id in valid_artifact_ids for claim_id in micropub.claims)
    )
    return kept


def _promoted_stance_documents(
    stances_doc: SourceStancesDocument | None,
    *,
    reference_resolves_to_promoted_or_primary,
    source_claim_index,
    primary_claim_index,
) -> tuple[StanceDocument, ...]:
    promoted: list[StanceDocument] = []
    for stance in (() if stances_doc is None else stances_doc.stances):
        source_claim = stance.source_claim
        if not isinstance(source_claim, str) or not source_claim:
            raise ValueError("stance source_claim must be normalized before promotion")
        if not reference_resolves_to_promoted_or_primary(source_claim):
            continue
        target = resolve_source_or_primary_claim_id(
            stance.target,
            source=source_claim_index,
            primary=primary_claim_index,
        )
        if target is None or not reference_resolves_to_promoted_or_primary(target):
            continue
        promoted.append(
            StanceDocument(
                source_claim=source_claim,
                perspective_source_claim_id=stance.perspective_source_claim_id,
                target=target,
                type=stance.type,
                strength=stance.strength,
                note=stance.note,
                conditions_differ=stance.conditions_differ,
                resolution=stance.resolution,
                target_justification_id=stance.target_justification_id,
                artifact_code=stance.artifact_code,
            )
        )
    return tuple(promoted)


def _promoted_justification_documents(
    justifications_doc: SourceJustificationsDocument | None,
    *,
    reference_resolves_to_promoted_or_primary,
) -> tuple[JustificationDocument, ...]:
    if justifications_doc is None:
        return ()
    promoted: list[JustificationDocument] = []
    for justification in justifications_doc.justifications:
        conclusion = justification.conclusion
        if not isinstance(conclusion, str):
            continue
        if not reference_resolves_to_promoted_or_primary(conclusion):
            continue
        if any(
            not reference_resolves_to_promoted_or_primary(premise)
            for premise in justification.premises
        ):
            continue
        promoted.append(
            JustificationDocument(
                id=justification.id,
                conclusion=conclusion,
                premises=justification.premises,
                rule_kind=justification.rule_kind,
                rule_strength=justification.rule_strength,
                provenance=justification.provenance,
                attack_target=justification.attack_target,
                artifact_code=justification.artifact_code,
            )
        )
    return tuple(promoted)


def _assemble_source_promotion_plan(
    repo: Repository,
    *,
    source_name: str,
    slug: str,
    source_doc: SourceDocument,
    claims_doc: SourceClaimsDocument | None,
    micropubs_doc: MicropublicationsFileDocument | None,
    justifications_doc: SourceJustificationsDocument | None,
    stances_doc: SourceStancesDocument | None,
    concept_map: dict[str, str],
    promoted_concept_documents: dict[str, ConceptDocument],
    valid_claims: list[SourceClaimDocument],
    blocked_claims: list[SourceClaimDocument],
    blocked_reasons: dict[str, list[tuple[str, str]]],
    source_claim_index,
    primary_claim_index,
) -> SourcePromotionPlan:
    source_paper = _promoted_claim_source_paper(
        claims_doc,
        fallback_slug=slug,
    )
    unresolved_concepts: set[str] = set()
    unstamped_claim_documents = [
        _promoted_claim_document(
            repo,
            claim,
            concept_map=concept_map,
            unresolved_concepts=unresolved_concepts,
            source_paper=source_paper,
        )
        for claim in valid_claims
    ]
    if unresolved_concepts:
        formatted = ", ".join(sorted(unresolved_concepts))
        raise ValueError(f"Cannot promote source {source_name!r}; unresolved concept mappings: {formatted}")

    valid_artifact_ids = {
        claim.artifact_id
        for claim in valid_claims
        if isinstance(claim.artifact_id, str)
    }

    def reference_resolves_to_promoted_or_primary(reference: object) -> bool:
        if not isinstance(reference, str) or not reference:
            return False
        source_target = source_claim_index.resolve_id(reference)
        if source_target is not None:
            return source_target in valid_artifact_ids
        return primary_claim_index.resolve_id(reference) is not None

    unstamped_justification_documents = _promoted_justification_documents(
        justifications_doc,
        reference_resolves_to_promoted_or_primary=reference_resolves_to_promoted_or_primary,
    )
    unstamped_stance_documents = _promoted_stance_documents(
        stances_doc,
        reference_resolves_to_promoted_or_primary=reference_resolves_to_promoted_or_primary,
        source_claim_index=source_claim_index,
        primary_claim_index=primary_claim_index,
    )
    promoted_micropubs = _filter_promoted_micropubs(
        micropubs_doc,
        valid_artifact_ids=valid_artifact_ids,
    )

    (
        promoted_source_document,
        stamped_claim_documents,
        stamped_justification_documents,
        stamped_stance_documents,
    ) = stamp_canonical_artifact_codes(
        source_doc,
        unstamped_claim_documents,
        unstamped_justification_documents,
        unstamped_stance_documents,
    )

    promoted_claim_documents: dict[ClaimRef, ClaimDocument] = {}
    for claim_document in stamped_claim_documents:
        artifact_id = claim_document.artifact_id
        if not isinstance(artifact_id, str) or not artifact_id:
            raise ValueError("promoted claim is missing artifact_id")
        promoted_claim_documents[ClaimRef(artifact_id)] = claim_document

    promoted_concept_plan_documents = {
        ConceptFileRef(concept_slug): concept_document
        for concept_slug, concept_document in promoted_concept_documents.items()
    }
    _validate_promoted_claims_before_commit(
        repo,
        promoted_claim_documents=promoted_claim_documents,
        promoted_concept_documents=promoted_concept_plan_documents,
    )

    promoted_stance_documents: dict[StanceRef, StanceDocument] = {}
    for stance_document in stamped_stance_documents:
        artifact_id = derive_stance_artifact_id(stance_document.to_payload())
        promoted_stance_documents[StanceRef(artifact_id)] = stance_document

    promoted_justification_documents: dict[JustificationRef, JustificationDocument] = {}
    for justification_document in stamped_justification_documents:
        artifact_id = derive_justification_artifact_id(justification_document.to_payload())
        promoted_justification_documents[JustificationRef(artifact_id)] = justification_document

    promoted_micropub_documents = {
        MicropublicationRef(micropub.artifact_id): micropub
        for micropub in promoted_micropubs
    }
    return SourcePromotionPlan(
        source_name=source_name,
        slug=slug,
        source_branch=source_branch_name(source_name),
        source_ref=CanonicalSourceRef(slug),
        promoted_source_document=promoted_source_document,
        promoted_claim_documents=promoted_claim_documents,
        promoted_micropub_documents=promoted_micropub_documents,
        promoted_concept_documents=promoted_concept_plan_documents,
        promoted_justification_documents=promoted_justification_documents,
        promoted_stance_documents=promoted_stance_documents,
        blocked_claims=tuple(blocked_claims),
        blocked_reasons=blocked_reasons,
    )


def resolve_source_concept_promotions(
    repo: Repository,
    source_name: str,
) -> SourceConceptPromotionResolution:
    concepts_doc = load_source_concepts_document(repo, source_name)
    concepts_by_artifact = load_primary_branch_concepts(repo)
    primary_tip = repo.snapshot.branch_head(repo.snapshot.primary_branch_name())
    primary_concept_index = (
        None
        if primary_tip is None
        else repo.families.concepts.reference_index(commit=primary_tip)
    )
    mapping: dict[str, str] = {}
    concept_documents: dict[str, ConceptDocument] = {}
    new_concepts: dict[str, tuple[SourceConceptEntryDocument, str, str, str]] = {}
    seen_new_artifacts: dict[str, str] = {}
    blocked_concept_refs: dict[str, str] = {}

    def resolve_primary_concept_id(reference: object) -> str | None:
        if primary_concept_index is None:
            return None
        return primary_concept_index.resolve_id(reference)

    def entry_handles(entry: SourceConceptEntryDocument, fallback: str) -> set[str]:
        handles = {
            handle
            for handle in (entry.local_name, entry.proposed_name, fallback)
            if isinstance(handle, str) and handle
        }
        return handles

    def block_entry(entry: SourceConceptEntryDocument, fallback: str, detail: str) -> None:
        for handle in entry_handles(entry, fallback):
            blocked_concept_refs[handle] = detail
            mapping.pop(handle, None)

    for entry in (() if concepts_doc is None else concepts_doc.concepts):
        registry_match = entry.registry_match
        if registry_match is not None:
            artifact_id = registry_match.artifact_id
            if isinstance(artifact_id, str) and artifact_id:
                for handle in (entry.local_name, entry.proposed_name):
                    if isinstance(handle, str) and handle:
                        mapping[handle] = artifact_id
                continue
        matched_artifact_id: str | None = None
        for handle in (entry.local_name, entry.proposed_name):
            if not isinstance(handle, str) or not handle:
                continue
            matched_artifact_id = resolve_primary_concept_id(handle)
            if matched_artifact_id is not None:
                mapping[handle] = matched_artifact_id
        if matched_artifact_id is not None:
            continue

        handle_seed = str(entry.proposed_name or entry.local_name or "concept").strip()
        slug = normalize_source_slug(handle_seed)
        concept_payload = normalize_canonical_concept_payload(
            {
                "canonical_name": str(entry.proposed_name or entry.local_name or slug).strip(),
                "status": "accepted",
                "definition": str(entry.definition or "").strip(),
                "domain": "source",
                "form": str(entry.form or "structural").strip(),
            },
            local_handle=slug,
        )
        artifact_id = concept_payload["artifact_id"]
        existing = concepts_by_artifact.get(artifact_id)
        if existing is not None:
            block_entry(
                entry,
                handle_seed,
                f"ambiguous concept mappings: {handle_seed}",
            )
            continue
        prior_handle = seen_new_artifacts.get(artifact_id)
        if prior_handle is not None and prior_handle != handle_seed:
            detail = f"ambiguous concept mappings: {handle_seed}, {prior_handle}"
            prior_entry = new_concepts.pop(artifact_id, None)
            if prior_entry is not None:
                block_entry(prior_entry[0], prior_entry[3], detail)
            block_entry(
                entry,
                handle_seed,
                detail,
            )
            seen_new_artifacts.pop(artifact_id, None)
            continue
        seen_new_artifacts[artifact_id] = handle_seed
        new_concepts[artifact_id] = (entry, artifact_id, slug, handle_seed)
        for handle in (entry.local_name, entry.proposed_name):
            if isinstance(handle, str) and handle:
                mapping[handle] = artifact_id

    for raw_entry, artifact_id, slug, _ in new_concepts.values():
        parameterization_relationships: list[dict[str, Any]] = []
        for relationship in raw_entry.parameterization_relationships:
            normalized_relationship = relationship.to_payload()
            normalized_inputs: list[str] = []
            for input_ref in normalized_relationship.get("inputs", []) or []:
                if not isinstance(input_ref, str) or not input_ref:
                    continue
                if input_ref.startswith("ps:concept:") or input_ref.startswith("tag:"):
                    normalized_inputs.append(input_ref)
                    continue
                resolved = mapping.get(input_ref) or resolve_primary_concept_id(input_ref)
                if resolved is None:
                    raise ValueError(
                        f"Cannot promote source {source_name!r}; unresolved parameterization concept: {input_ref}"
                    )
                normalized_inputs.append(resolved)
            normalized_relationship["inputs"] = normalized_inputs
            parameterization_relationships.append(normalized_relationship)

        concept_doc: dict[str, Any] = {
            "canonical_name": str(raw_entry.proposed_name or raw_entry.local_name or slug).strip(),
            "status": "accepted",
            "definition": str(raw_entry.definition or "").strip(),
            "domain": "source",
            "form": str(raw_entry.form or "structural").strip(),
        }
        if raw_entry.aliases:
            concept_doc["aliases"] = [alias.to_payload() for alias in raw_entry.aliases]
        if raw_entry.form_parameters is not None:
            concept_doc["form_parameters"] = raw_entry.form_parameters.to_payload()
        if parameterization_relationships:
            concept_doc["parameterization_relationships"] = parameterization_relationships
        concept_doc = normalize_canonical_concept_payload(concept_doc, local_handle=slug)
        concept_ref = ConceptFileRef(slug)
        concept_documents[slug] = convert_document_value(
            concept_doc,
            ConceptDocument,
            source=repo.families.concepts.address(concept_ref).require_path(),
        )

    return SourceConceptPromotionResolution(
        concept_map=mapping,
        promoted_concept_documents=concept_documents,
        blocked_concept_refs=blocked_concept_refs,
    )


def load_finalize_report(repo: Repository, source_name: str):
    return load_source_finalize_report(repo, source_name)


def _compute_blocked_claim_artifact_ids(
    claims_doc,
    justifications_doc,
    stances_doc,
    source_claim_index,
    *,
    concept_map: dict[str, str],
    blocked_concept_refs: dict[str, str] | None = None,
) -> tuple[set[str], dict[str, list[tuple[str, str]]]]:
    """Identify source-branch claims blocked from promotion by per-item errors.

    Per ``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``
    axis-1 finding 3.3: a claim is blocked if (a) it has no canonical
    ``artifact_id``, (b) a stance with this claim as ``source_claim``
    has an unknown ``target``, or (c) a justification with this claim as
    ``conclusion`` or a ``premise`` references unknown siblings.

    Returns a pair: the set of blocked artifact ids, and a map from each
    blocked artifact id to a list of ``(kind, detail)`` diagnostic tuples
    describing why it was blocked. ``detail`` is a short human-readable
    string suitable for the diagnostic ``message`` column.
    """

    blocked: set[str] = set()
    reasons: dict[str, list[tuple[str, str]]] = {}

    def _record(artifact_id: str, kind: str, detail: str) -> None:
        blocked.add(artifact_id)
        reasons.setdefault(artifact_id, []).append((kind, detail))

    blocked_concept_refs = blocked_concept_refs or {}

    # (a) claims without a canonical artifact_id.
    for claim in () if claims_doc is None else claims_doc.claims:
        artifact_id = claim.artifact_id
        if not isinstance(artifact_id, str) or not artifact_id:
            # Fall back to the raw id for reference; synthetic handling is
            # not needed because normalize_source_claims_payload fills
            # artifact_id eagerly, so this branch fires only if upstream
            # produced a malformed doc.
            raw_id = str(claim.id or "?")
            _record(raw_id, "claim_reference", f"claim {raw_id!r} missing artifact_id")
            continue
        for concept_ref in _source_claim_concept_refs(claim):
            detail = blocked_concept_refs.get(concept_ref)
            if (
                detail is None
                and source_concept_ref_requires_mapping(concept_ref)
                and concept_ref not in concept_map
            ):
                detail = f"unresolved concept mappings: {concept_ref}"
            if detail is not None:
                _record(
                    artifact_id,
                    "concept_mapping",
                    f"claim concept {concept_ref!r} blocked: {detail}",
                )

    # (b) justifications with unresolved conclusion or premises block the
    # claims those references point at (when they resolve to valid
    # artifact ids on the source branch).
    for justification in () if justifications_doc is None else justifications_doc.justifications:
        conclusion = justification.conclusion
        if isinstance(conclusion, str) and not source_claim_index.exists(conclusion):
            _record(
                conclusion,
                "justification_reference",
                f"justification conclusion {conclusion!r} unresolved",
            )
        for premise in justification.premises:
            if isinstance(premise, str) and not source_claim_index.exists(premise):
                _record(
                    premise,
                    "justification_reference",
                    f"justification premise {premise!r} unresolved",
                )

    return blocked, reasons


def _write_promotion_blocked_sidecar_rows(
    sidecar_path: Path,
    source_branch: str,
    source_paper: str,
    blocked_claims,
    reasons: dict[str, list[tuple[str, str]]],
) -> None:
    """Mirror blocked claims into the sidecar with promotion_status='blocked'.

    Each blocked claim becomes a row in ``claim_core`` with
    ``promotion_status='blocked'``, ``branch=<source_branch>``; each
    reason becomes a ``build_diagnostics`` row with
    ``diagnostic_kind='promotion_blocked'``, ``blocking=1``. The render
    layer joins these to surface per-claim promotion state under opt-in
    policy flags (phase 4).

    If the sidecar file does not exist yet, the write is a no-op — the
    primary use case (CLI ``pks source promote``) builds the sidecar at
    repo init and then uses it continuously, so the file usually exists.
    Tests that want to observe the mirror rows must ``build_sidecar``
    before calling promote.
    """

    if not sidecar_path.exists():
        return

    conn = connect_sidecar(sidecar_path)
    try:
        child_claim_tables = {
            row[0]
            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name IN (
                      'claim_concept_link',
                      'claim_numeric_payload',
                      'claim_text_payload',
                      'claim_algorithm_payload',
                      'micropublication_claim'
                  )
                """
            ).fetchall()
        }
        schema_tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        if "concept" not in schema_tables:
            # Minimal tests may create claim_concept_link without its
            # referenced concept table. In that schema there can be no
            # valid claim_concept_link children to preserve or delete.
            child_claim_tables.discard("claim_concept_link")
        for claim in blocked_claims:
            artifact_id = claim.artifact_id
            if not isinstance(artifact_id, str) or not artifact_id:
                # Fall back to raw id — upstream shouldn't produce this,
                # but the path must not crash on a malformed claim.
                artifact_id = str(claim.id or "?")
            source_ref = f"{source_branch}:{artifact_id}"
            # ``claim_core.id`` is PK. Delete by id alone so a prior
            # mirror row from any source branch is replaced cleanly.
            # (Scoping by (id, branch) left prior rows behind and the
            # subsequent INSERT collided on PK — reproduction in
            # ``tests/remediation/phase_7_race_atomicity/
            # test_T7_5d_promotion_blocked_id_collision.py``.)
            # The ``build_diagnostics`` DELETE stays scoped to this
            # source_ref so other branches' diagnostics survive.
            #
            # Bug 4 (v0.3.2): the sidecar connection runs with
            # ``PRAGMA foreign_keys = ON`` and four child tables FK to
            # ``claim_core(id)`` — ``claim_concept_link``,
            # ``claim_numeric_payload``, ``claim_text_payload``,
            # ``claim_algorithm_payload``, and ``micropublication_claim``.
            # If a sibling branch already
            # ingested this claim its payload children exist, and a bare
            # ``DELETE FROM claim_core`` raises
            # ``sqlite3.IntegrityError: FOREIGN KEY constraint failed``.
            # Drop the child rows first (they will not be re-inserted
            # below — the blocked-mirror row has no payload), then the
            # parent. Reproduction in
            # ``tests/remediation/phase_7_race_atomicity/
            # test_T7_5e_promotion_blocked_fk_payload.py``.
            for table_name in (
                "claim_concept_link",
                "claim_numeric_payload",
                "claim_text_payload",
                "claim_algorithm_payload",
                "micropublication_claim",
            ):
                if table_name not in child_claim_tables:
                    continue
                conn.execute(
                    f"DELETE FROM {table_name} WHERE claim_id = ?",
                    (artifact_id,),
                )
            conn.execute(
                "DELETE FROM claim_core WHERE id = ?",
                (artifact_id,),
            )
            conn.execute(
                "DELETE FROM build_diagnostics WHERE claim_id = ? "
                "AND diagnostic_kind = 'promotion_blocked' "
                "AND source_ref = ?",
                (artifact_id, source_ref),
            )

            conn.execute(
                """
                INSERT INTO claim_core (
                    id, primary_logical_id, logical_ids_json, version_id,
                    content_hash, seq, type, target_concept,
                    source_slug, source_paper, provenance_page,
                    provenance_json, context_id, premise_kind, branch,
                    build_status, stage, promotion_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact_id,
                    "",
                    "[]",
                    "",
                    "",
                    0,
                    "promotion_blocked",
                    None,
                    source_paper,
                    source_paper,
                    0,
                    None,
                    None,
                    "ordinary",
                    source_branch,
                    "ingested",
                    None,
                    "blocked",
                ),
            )

            for kind, detail in reasons.get(artifact_id, []):
                conn.execute(
                    """
                    INSERT INTO build_diagnostics (
                        claim_id, source_kind, source_ref, diagnostic_kind,
                        severity, blocking, message, file, detail_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        artifact_id,
                        "claim",
                        source_ref,
                        "promotion_blocked",
                        "error",
                        1,
                        detail,
                        None,
                        json.dumps(
                            {"reason_kind": kind, "source_branch": source_branch},
                            sort_keys=True,
                        ),
                    ),
                )
        conn.commit()
    finally:
        conn.close()


def _prepare_promotion_blocked_sidecar(
    sidecar_path: Path,
    source_branch: str,
    source_paper: str,
    blocked_claims,
    reasons: dict[str, list[tuple[str, str]]],
) -> Path | None:
    if not sidecar_path.exists():
        return None
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{sidecar_path.name}.promotion.",
        suffix=".tmp",
        dir=sidecar_path.parent,
    )
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        shutil.copy2(sidecar_path, temp_path)
        _write_promotion_blocked_sidecar_rows(
            temp_path,
            source_branch,
            source_paper,
            blocked_claims,
            reasons,
        )
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    return temp_path


def promote_source_branch(
    repo: Repository,
    source_name: str,
    *,
    strict: bool = False,
) -> PromotionResult:
    report = load_finalize_report(repo, source_name)
    if report is None:
        raise ValueError(
            f"Source {source_name!r} must be finalized before promotion "
            "(no finalize report found)"
        )
    # Per axis-1 finding 3.3: the all-or-nothing gate becomes a per-item
    # filter. ``strict=True`` preserves all-or-nothing behavior for
    # claim-affecting errors while still treating stance-only validation
    # failures as metadata quarantine rather than claim blockers.
    has_strict_blocking_errors = any(
        (
            report.claim_reference_errors,
            report.micropub_coverage_errors,
            report.justification_reference_errors,
        )
    )
    if strict and report.status != "ready" and has_strict_blocking_errors:
        raise ValueError(
            f"Source {source_name!r} must be finalized successfully "
            "before promotion (strict mode)"
        )

    slug = source_paper_slug(source_name)
    source_doc = load_source_document(repo, source_name)
    claims_doc = load_source_claims_document(repo, source_name)
    micropubs_doc = load_source_micropubs_document(repo, source_name)
    justifications_doc = load_source_justifications_document(repo, source_name)
    stances_doc = load_source_stances_document(repo, source_name)
    concept_resolution = resolve_source_concept_promotions(repo, source_name)
    concept_map = concept_resolution.concept_map
    promoted_concept_documents = concept_resolution.promoted_concept_documents
    unresolved_concepts: set[str] = set()

    source_claim_index = build_source_claim_index(repo, source_name)
    primary_claim_index = build_primary_claim_index(repo)

    blocked_artifact_ids, blocked_reasons = _compute_blocked_claim_artifact_ids(
        claims_doc,
        justifications_doc,
        stances_doc,
        source_claim_index,
        concept_map=concept_map,
        blocked_concept_refs=concept_resolution.blocked_concept_refs,
    )

    all_claims = tuple(() if claims_doc is None else claims_doc.claims)
    blocked_claims = [
        claim
        for claim in all_claims
        if isinstance(claim.artifact_id, str)
        and claim.artifact_id in blocked_artifact_ids
    ]
    valid_claims = [
        claim
        for claim in all_claims
        if isinstance(claim.artifact_id, str)
        and claim.artifact_id not in blocked_artifact_ids
    ]

    if not valid_claims and blocked_claims:
        # All items blocked — still write mirror rows so the render layer
        # can surface them, then raise so the CLI can report exit code 1.
        _write_promotion_blocked_sidecar_rows(
            repo.sidecar_path,
            source_branch_name(source_name),
            slug,
            blocked_claims,
            blocked_reasons,
        )
        details = sorted(
            {
                detail
                for reason_entries in blocked_reasons.values()
                for _, detail in reason_entries
            }
        )
        detail_suffix = f": {'; '.join(details)}" if details else ""
        raise ValueError(
            f"Source {source_name!r}: all {len(blocked_claims)} claims blocked "
            f"from promotion; see build_diagnostics for details{detail_suffix}"
        )

    promotion_plan = _assemble_source_promotion_plan(
        repo,
        source_name=source_name,
        slug=slug,
        source_doc=source_doc,
        claims_doc=claims_doc,
        micropubs_doc=micropubs_doc,
        justifications_doc=justifications_doc,
        stances_doc=stances_doc,
        concept_map=concept_map,
        promoted_concept_documents=promoted_concept_documents,
        valid_claims=valid_claims,
        blocked_claims=blocked_claims,
        blocked_reasons=blocked_reasons,
        source_claim_index=source_claim_index,
        primary_claim_index=primary_claim_index,
    )

    prepared_sidecar_path: Path | None = None
    sidecar_mirror_ok = True
    sidecar_mirror_error: str | None = None
    sha: str | None = None
    try:
        with repo.head_bound_transaction(repo.snapshot.primary_branch_name(), path="promote") as head_txn:
            if promotion_plan.blocked_claims:
                head_txn.assert_current()
                prepared_sidecar_path = _prepare_promotion_blocked_sidecar(
                    repo.sidecar_path,
                    promotion_plan.source_branch,
                    promotion_plan.slug,
                    promotion_plan.blocked_claims,
                    promotion_plan.blocked_reasons,
                )

            with head_txn.families_transact(message=f"Promote source {slug}") as transaction:
                transaction.sources.save(
                    promotion_plan.source_ref,
                    promotion_plan.promoted_source_document,
                )
                for claim_ref, claim_document in promotion_plan.promoted_claim_documents.items():
                    transaction.claims.save(
                        claim_ref,
                        claim_document,
                    )
                for micropub_ref, micropub_document in promotion_plan.promoted_micropub_documents.items():
                    transaction.micropubs.save(
                        micropub_ref,
                        micropub_document,
                    )
                for concept_ref, concept_document in promotion_plan.promoted_concept_documents.items():
                    transaction.concepts.save(
                        concept_ref,
                        concept_document,
                    )
                for justification_ref, justification_document in promotion_plan.promoted_justification_documents.items():
                    transaction.justifications.save(
                        justification_ref,
                        justification_document,
                    )
                for stance_ref, stance_document in promotion_plan.promoted_stance_documents.items():
                    transaction.stances.save(
                        stance_ref,
                        stance_document,
                    )
            if prepared_sidecar_path is not None:
                try:
                    prepared_sidecar_path.replace(repo.sidecar_path)
                except OSError as exc:
                    sidecar_mirror_ok = False
                    sidecar_mirror_error = str(exc)
            sha = head_txn.commit_sha
    finally:
        if prepared_sidecar_path is not None and prepared_sidecar_path.exists():
            prepared_sidecar_path.unlink(missing_ok=True)
    if sha is None:
        raise ValueError("source promotion transaction did not produce a commit")
    source_branch_tip = repo.snapshot.branch_head(promotion_plan.source_branch)
    git = repo.git
    if git is None:
        raise ValueError("source promotion provenance requires a git-backed repository")
    write_provenance_note(
        git.raw_repo,
        sha,
        Provenance(
            status=ProvenanceStatus.STATED,
            graph_name=f"urn:propstore:source-promote:{sha}",
            witnesses=(
                ProvenanceWitness(
                    asserter="urn:propstore:agent:source-promote",
                    timestamp=utc_now(),
                    source_artifact_code=promotion_plan.source_branch,
                    method="promote",
                ),
            ),
            derived_from=(() if source_branch_tip is None else (source_branch_tip,)),
            operations=("promote",),
        ),
    )
    _commit_promote_time_trust_calibration(
        repo,
        source_name,
        promotion_commit_sha=sha,
    )

    return PromotionResult(
        commit_sha=sha,
        blocked_claims=promotion_plan.blocked_claims,
        blocked_diagnostics=_freeze_blocked_diagnostics(promotion_plan.blocked_reasons),
        sidecar_mirror_ok=sidecar_mirror_ok,
        sidecar_mirror_error=sidecar_mirror_error,
    )


def sync_source_branch(
    repo: Repository,
    source_name: str,
    *,
    output_dir: Path | None = None,
) -> Path:
    branch = source_branch_name(source_name)
    tip = repo.snapshot.branch_head(branch)
    if tip is None:
        raise ValueError(f"Source branch {branch!r} does not exist")

    destination = output_dir
    if destination is None:
        papers_root = repo.root.parent / "papers"
        destination = papers_root / source_paper_slug(source_name)
    destination.mkdir(parents=True, exist_ok=True)
    destination_root = destination.resolve()

    def copy_tree(relpath: str = "") -> None:
        for entry in repo.snapshot.iter_dir_entries(relpath, commit=tip):
            target = _source_sync_target_path(destination_root, entry.relpath)
            if entry.is_dir:
                target.mkdir(parents=True, exist_ok=True)
                copy_tree(entry.relpath)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(repo.snapshot.read_bytes(entry.relpath, commit=tip))

    copy_tree("")
    return destination


def _source_sync_target_path(destination_root: Path, relpath: str) -> Path:
    """Resolve a source-sync relpath under ``destination_root``.

    Zip Slip (Snyk Security, 2018) is the relevant path-traversal pattern:
    never trust archive or snapshot entry paths until they have been proven
    relative to the intended extraction root.
    """
    normalized_relpath = relpath.replace("\\", "/")
    posix_relpath = PurePosixPath(normalized_relpath)
    windows_relpath = PureWindowsPath(relpath)
    if (
        posix_relpath.is_absolute()
        or windows_relpath.is_absolute()
        or ".." in posix_relpath.parts
    ):
        raise ValueError(f"path escapes output_dir: {relpath}")
    target = (destination_root / Path(*posix_relpath.parts)).resolve()
    try:
        target.relative_to(destination_root)
    except ValueError as exc:
        raise ValueError(f"path escapes output_dir: {relpath}") from exc
    return target
