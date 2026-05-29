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

from dataclasses import dataclass
from importlib import import_module
from typing import Any, TypeAlias, cast

from quire.lifecycle import FamilyRecordWrite
from propstore.families.artifacts import stamp_canonical_artifacts
from propstore.families.identity.concepts import normalize_canonical_concept_payload
from propstore.claims import LoadedClaimsFile
from propstore.compiler.context import build_compilation_context_from_loaded
from propstore.compiler.errors import CompilerWorkflowError
from propstore.families.claims.passes import run_claim_pipeline
from propstore.families.claims.stages import (
    ClaimAuthoredFiles,
    PromotionBlockedClaimFact,
    PromotionBlockedReason,
)
from propstore.families.registry import (
    CanonicalSourceRef,
    ClaimRef,
    ConceptFileRef,
    JustificationRef,
    MicropublicationRef,
    SourceRef,
    StanceRef,
)
from propstore.families.concepts.declaration import (
    ConceptDocument,
    SourceConceptEntryDocument,
)
from propstore.families.concepts.stages import (
    LoadedConcept,
    parse_concept_record_document,
)
from propstore.families.claims.declaration import (
    ClaimDocument,
    SourceClaimDocument,
    SourceJustificationDocument,
)
from propstore.families.claims.references import resolve_first_claim_reference_id
from propstore.families.claims.types import ClaimType
from propstore.families.contexts.stages import parse_context_record_document
from propstore.families.micropublications.declaration import MicropublicationDocument
from propstore.families.forms.stages import parse_form
from propstore.provenance import (
    Provenance,
    ProvenanceStatus,
    ProvenanceWitness,
    write_provenance_note,
)
from propstore.repository import Repository
from propstore.families.claims.lifecycle import (
    normalize_promoted_source_claim_artifact,
    source_concept_ref_requires_mapping,
)
from quire.documents import convert_document_value, document_to_payload
from propstore.families.sources.declaration import (
    SourceDocument,
    SourceTrustDocument,
    source_document_payload,
)
from propstore.source_trust_argumentation import SourceTrustResult, calibrate_source_trust
from propstore.families.stances.declaration import SourceStanceEntryDocument, StanceDocument
from propstore.families.identity.justifications import derive_justification_artifact_id
from propstore.families.identity.stances import derive_stance_artifact_id, stamp_stance_artifact_id

from .common import (
    utc_now,
    normalize_source_slug,
    source_paper_slug,
)
from propstore.families.concepts.lifecycle import load_primary_branch_concepts
from .reference_indexes import (
    primary_claim_index as build_primary_claim_index,
    source_claim_index as build_source_claim_index,
)
from .stages import SourcePromotionPlan

JustificationDocument: TypeAlias = Any


def _justification_document_type() -> type[Any]:
    return getattr(
        import_module("propstore.families.claims.declaration"),
        "JustificationDocument",
    )


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


def _promotion_write(
    family: str,
    identity: object,
    record: object,
) -> FamilyRecordWrite:
    return FamilyRecordWrite(
        family=family,
        identity=str(identity),
        state="canonical",
        record=record,
    )


def _save_promotion_write(transaction: Any, write: FamilyRecordWrite) -> None:
    if write.family == "sources":
        transaction.sources.save(
            CanonicalSourceRef(write.identity),
            cast(SourceDocument, write.record),
        )
        return
    if write.family == "claims":
        transaction.claims.save(
            ClaimRef(write.identity),
            cast(ClaimDocument, write.record),
        )
        return
    if write.family == "micropubs":
        transaction.micropubs.save(
            MicropublicationRef(write.identity),
            cast(MicropublicationDocument, write.record),
        )
        return
    if write.family == "concepts":
        transaction.concepts.save(
            ConceptFileRef(write.identity),
            cast(ConceptDocument, write.record),
        )
        return
    if write.family == "justifications":
        transaction.justifications.save(
            JustificationRef(write.identity),
            write.record,
        )
        return
    if write.family == "stances":
        transaction.stances.save(
            StanceRef(write.identity),
            cast(StanceDocument, write.record),
        )
        return
    raise ValueError(f"unknown source promotion write family: {write.family!r}")


def _validate_promoted_claims_before_commit(
    repo: Repository,
    *,
    promoted_claim_documents: dict[ClaimRef, ClaimDocument],
    promoted_concept_documents: dict[ConceptFileRef, ConceptDocument],
) -> None:
    """Validate the canonical claim view that promotion is about to commit."""

    head_sha = repo.require_git().head_sha()
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

    claim_files: list[LoadedClaimsFile] = [
        LoadedClaimsFile(
            filename=handle.ref.artifact_id,
            artifact_path=tree / handle.address.require_path(),
            store_root=tree,
            document=handle.document,
        )
        for handle in repo.families.claims.iter_handles(commit=head_sha)
        if handle.ref not in promoted_claim_documents
    ]
    for claim_ref, claim_document in promoted_claim_documents.items():
        claim_files.append(
            LoadedClaimsFile(
                filename=claim_ref.artifact_id,
                artifact_path=tree / repo.families.claims.address(claim_ref).require_path(),
                store_root=tree,
                document=claim_document,
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
    return cast(dict[str, Any], document_to_payload(trust))


def _commit_promote_time_trust_calibration(
    repo: Repository,
    source_name: str,
    *,
    promotion_commit_sha: str,
) -> str | None:
    branch = repo.families.source_documents.address(SourceRef(source_name)).branch
    calibration = calibrate_source_trust(
        repo,
        source_name,
        world_snapshot=promotion_commit_sha,
    )
    source_doc = repo.families.source_documents.require(SourceRef(source_name))
    updated_payload = source_document_payload(source_doc)
    updated_payload["trust"] = _source_trust_payload(calibration)
    if updated_payload["trust"] == document_to_payload(source_doc.trust):
        return None
    updated_source_doc = convert_document_value(
        updated_payload,
        SourceDocument,
        source=f"{branch}:source.yaml",
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
    claims_doc: tuple[SourceClaimDocument, ...] | None,
    *,
    fallback_slug: str,
) -> str:
    if claims_doc is None or not claims_doc or claims_doc[0].source is None:
        return fallback_slug
    return str(claims_doc[0].source.paper or fallback_slug)


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
    micropubs_doc: tuple[MicropublicationDocument, ...] | None,
    *,
    valid_artifact_ids: set[str],
) -> tuple[MicropublicationDocument, ...]:
    if micropubs_doc is None:
        return ()
    kept = tuple(
        micropub
        for micropub in micropubs_doc
        if all(claim_id in valid_artifact_ids for claim_id in micropub.claims)
    )
    return kept


def _promoted_stance_documents(
    stances_doc: tuple[SourceStanceEntryDocument, ...] | None,
    *,
    reference_resolves_to_promoted_or_primary,
    source_claim_index,
    primary_claim_index,
) -> tuple[StanceDocument, ...]:
    promoted: list[StanceDocument] = []
    for stance in (() if stances_doc is None else stances_doc):
        source_claim = stance.source_claim
        if not isinstance(source_claim, str) or not source_claim:
            raise ValueError("stance source_claim must be normalized before promotion")
        if not reference_resolves_to_promoted_or_primary(source_claim):
            continue
        target = resolve_first_claim_reference_id(
            stance.target,
            source_claim_index,
            primary_claim_index,
        )
        if target is None or not reference_resolves_to_promoted_or_primary(target):
            continue
        promoted_payload = stamp_stance_artifact_id(
            {
                "source_claim": source_claim,
                "perspective_source_claim_id": stance.perspective_source_claim_id,
                "target": target,
                "type": stance.type,
                "strength": stance.strength,
                "note": stance.note,
                "conditions_differ": stance.conditions_differ,
                "opinion": stance.opinion,
                "resolution": (
                    None
                    if stance.resolution is None
                    else document_to_payload(stance.resolution)
                ),
                "target_justification_id": stance.target_justification_id,
                "artifact_code": stance.artifact_code,
            }
        )
        promoted.append(
            convert_document_value(
                promoted_payload,
                StanceDocument,
                source=f"promoted-stance:{promoted_payload['artifact_id']}",
            )
        )
    return tuple(promoted)


def _promoted_justification_documents(
    justifications_doc: tuple[SourceJustificationDocument, ...] | None,
    *,
    reference_resolves_to_promoted_or_primary,
) -> tuple[JustificationDocument, ...]:
    if justifications_doc is None:
        return ()
    promoted: list[JustificationDocument] = []
    justification_document_type = _justification_document_type()
    for justification in justifications_doc:
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
            justification_document_type(
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
    claims_doc: tuple[SourceClaimDocument, ...] | None,
    micropubs_doc: tuple[MicropublicationDocument, ...] | None,
    justifications_doc: tuple[SourceJustificationDocument, ...] | None,
    stances_doc: tuple[SourceStanceEntryDocument, ...] | None,
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
    ) = stamp_canonical_artifacts(
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
        stance_payload = document_to_payload(stance_document)
        if not isinstance(stance_payload, dict):
            raise TypeError("promoted stance payload must be a mapping")
        artifact_id = derive_stance_artifact_id(stance_payload)
        promoted_stance_documents[StanceRef(artifact_id)] = stance_document

    promoted_justification_documents: dict[JustificationRef, JustificationDocument] = {}
    for justification_document in stamped_justification_documents:
        justification_payload = document_to_payload(justification_document)
        if not isinstance(justification_payload, dict):
            raise TypeError("promoted justification payload must be a mapping")
        artifact_id = derive_justification_artifact_id(justification_payload)
        promoted_justification_documents[JustificationRef(artifact_id)] = justification_document

    promoted_micropub_documents = {
        MicropublicationRef(micropub.artifact_id): micropub
        for micropub in promoted_micropubs
    }
    source_ref = CanonicalSourceRef(slug)
    writes = (
        _promotion_write("sources", source_ref.name, promoted_source_document),
        *(
            _promotion_write("claims", claim_ref.artifact_id, claim_document)
            for claim_ref, claim_document in promoted_claim_documents.items()
        ),
        *(
            _promotion_write("micropubs", micropub_ref.artifact_id, micropub_document)
            for micropub_ref, micropub_document in promoted_micropub_documents.items()
        ),
        *(
            _promotion_write("concepts", concept_ref.name, concept_document)
            for concept_ref, concept_document in promoted_concept_plan_documents.items()
        ),
        *(
            _promotion_write(
                "justifications",
                justification_ref.artifact_id,
                justification_document,
            )
            for justification_ref, justification_document in promoted_justification_documents.items()
        ),
        *(
            _promotion_write("stances", stance_ref.artifact_id, stance_document)
            for stance_ref, stance_document in promoted_stance_documents.items()
        ),
    )
    return SourcePromotionPlan(
        source_name=source_name,
        slug=slug,
        source_branch=repo.families.source_documents.address(
            SourceRef(source_name)
        ).branch,
        writes=writes,
        blocked_claims=tuple(blocked_claims),
        blocked_reasons=blocked_reasons,
    )


def resolve_source_concept_promotions(
    repo: Repository,
    source_name: str,
) -> SourceConceptPromotionResolution:
    concepts_doc = repo.families.source_concepts.load(SourceRef(source_name))
    concepts_by_artifact = load_primary_branch_concepts(repo)
    primary_tip = repo.require_git().branch_sha(repo.require_git().primary_branch_name())
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

    for entry in (() if concepts_doc is None else concepts_doc):
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
            normalized_relationship = cast(dict[str, Any], document_to_payload(relationship))
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
            concept_doc["aliases"] = [document_to_payload(alias) for alias in raw_entry.aliases]
        if raw_entry.form_parameters is not None:
            concept_doc["form_parameters"] = document_to_payload(raw_entry.form_parameters)
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
    return repo.families.source_finalize_reports.load(SourceRef(source_name))


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
    for claim in () if claims_doc is None else claims_doc:
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
    for justification in () if justifications_doc is None else justifications_doc:
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


def collect_source_promotion_blocked_facts(
    repo: Repository,
    source_name: str,
) -> tuple[PromotionBlockedClaimFact, ...]:
    claims_doc = repo.families.source_claims.load(SourceRef(source_name))
    if claims_doc is None:
        return ()
    if load_finalize_report(repo, source_name) is None:
        return ()

    concept_resolution = resolve_source_concept_promotions(repo, source_name)
    source_claim_index = build_source_claim_index(repo, source_name)
    blocked_artifact_ids, blocked_reasons = _compute_blocked_claim_artifact_ids(
        claims_doc,
        repo.families.source_justifications.load(SourceRef(source_name)),
        repo.families.source_stances.load(SourceRef(source_name)),
        source_claim_index,
        concept_map=concept_resolution.concept_map,
        blocked_concept_refs=concept_resolution.blocked_concept_refs,
    )
    slug = source_paper_slug(source_name)
    source_branch = repo.families.source_claims.address(SourceRef(source_name)).branch
    source_paper = _promoted_claim_source_paper(claims_doc, fallback_slug=slug)
    facts: list[PromotionBlockedClaimFact] = []
    for claim in claims_doc:
        raw_id = str(claim.id or "?")
        artifact_id = claim.artifact_id
        if not isinstance(artifact_id, str) or not artifact_id:
            artifact_id = raw_id
        if artifact_id not in blocked_artifact_ids:
            continue
        facts.append(
            PromotionBlockedClaimFact(
                artifact_id=artifact_id,
                claim_type=ClaimType(str(claim.type)),
                source_branch=source_branch,
                source_paper=source_paper,
                raw_id=raw_id,
                reasons=tuple(
                    PromotionBlockedReason(kind=kind, detail=detail)
                    for kind, detail in blocked_reasons.get(artifact_id, ())
                ),
            )
        )
    return tuple(facts)


def collect_all_source_promotion_blocked_facts(
    repo: Repository,
) -> tuple[PromotionBlockedClaimFact, ...]:
    facts: list[PromotionBlockedClaimFact] = []
    for branch in repo.snapshot.iter_branches():
        if branch.kind != "source":
            continue
        source_name = branch.name.removeprefix("source/")
        facts.extend(collect_source_promotion_blocked_facts(repo, source_name))
    return tuple(facts)


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
    source_doc = repo.families.source_documents.require(SourceRef(source_name))
    claims_doc = repo.families.source_claims.load(SourceRef(source_name))
    micropubs_doc = repo.families.source_micropubs.load(SourceRef(source_name))
    justifications_doc = repo.families.source_justifications.load(SourceRef(source_name))
    stances_doc = repo.families.source_stances.load(SourceRef(source_name))
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

    all_claims: tuple[SourceClaimDocument, ...] = tuple(
        () if claims_doc is None else claims_doc
    )
    blocked_claims: list[SourceClaimDocument] = [
        claim
        for claim in all_claims
        if isinstance(claim.artifact_id, str)
        and claim.artifact_id in blocked_artifact_ids
    ]
    valid_claims: list[SourceClaimDocument] = [
        claim
        for claim in all_claims
        if isinstance(claim.artifact_id, str)
        and claim.artifact_id not in blocked_artifact_ids
    ]

    if not valid_claims and blocked_claims:
        # All items blocked. The derived-store builder materializes the
        # mirror rows from source-branch state; promote raises so the CLI
        # can report exit code 1 without advancing master.
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

    sidecar_mirror_ok = True
    sidecar_mirror_error: str | None = None
    sha: str | None = None
    git = repo.git
    if git is None:
        raise ValueError("source promotion requires a git-backed repository")
    with git.head_bound_transaction(repo.require_git().primary_branch_name()) as head_txn:
        with head_txn.families_transact(repo.families, message=f"Promote source {slug}") as transaction:
            for write in promotion_plan.writes:
                _save_promotion_write(transaction, write)
        sha = head_txn.commit_sha
    if sha is None:
        raise ValueError("source promotion transaction did not produce a commit")
    source_branch_tip = repo.require_git().branch_sha(promotion_plan.source_branch)
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
