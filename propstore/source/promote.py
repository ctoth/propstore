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
from propstore.families.sources.declaration import (
    SourceDocument,
)
from propstore.families.stances.declaration import (
    StanceDocument,
)

from .common import (
    utc_now,
    source_paper_slug,
)
from .reference_indexes import (
    primary_claim_index as build_primary_claim_index,
    source_claim_index as build_source_claim_index,
)

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
                source_path=tree
                / repo.families.concepts.address(concept_ref).require_path(),
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
                artifact_path=tree
                / repo.families.claims.address(claim_ref).require_path(),
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


def load_finalize_report(repo: Repository, source_name: str):
    return repo.families.source_finalize_reports.load(SourceRef(source_name))


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
    source_branch = repo.families.source_claims.address(
        SourceRef(source_name)
    ).require_branch()
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
    justifications_doc = repo.families.source_justifications.load(
        SourceRef(source_name)
    )
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
    with git.head_bound_transaction(
        repo.require_git().primary_branch_name()
    ) as head_txn:
        with head_txn.families_transact(
            repo.families, message=f"Promote source {slug}"
        ) as transaction:
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
