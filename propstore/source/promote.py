"""Source-branch promotion — the canonical ``master`` merge.

Promotion lowers a finalized source branch into the canonical store. It is the
load-bearing non-commitment surface, so two invariants govern every line here:

* **Quarantine, never drop.** A claim that cannot be promoted cleanly (an
  unresolved concept mapping, an unresolved context, a dangling justification
  reference) is *blocked*: it stays on the source branch, is recorded in the
  :class:`PromotionResult` with its reasons, and is never discarded or silently
  merged. The valid claims promote; the blocked ones are surfaced. Promotion only
  aborts when *every* claim is blocked (there is nothing to promote).

* **Calibration stamps, never gates.** Promote-time trust calibration projects an
  honestly typed prior-trust opinion and stamps it onto the source manifest. A
  low-trust (or vacuous) source still promotes its claims, carrying its honest
  calibrated provenance. Calibration is a stamp on the source, never a filter on
  the claims.

A promoted canonical claim is a NEW immutable artifact rebuilt from the source
claim plus its resolved concept foreign keys (source-of-truth storage is
immutable except by explicit migration); its identity is the source claim's
already-derived ``artifact_id``, so promotion mints no new claim identity. The
canonical write is one atomic head-bound transaction on ``master``; the promotion
provenance rides on a git note (``refs/notes/provenance``), never in identity.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

import msgspec
from quire.references import FamilyReferenceIndex

from propstore.core.lemon import (
    LexicalEntry,
    LexicalForm,
    LexicalSense,
    OntologyReference,
)
from propstore.families.claims import Claim
from propstore.families.concepts import Concept, ConceptStatus
from propstore.families.diagnostics import BuildDiagnostic
from propstore.families.identity.concepts import derive_concept_artifact_id
from propstore.families.identity.justifications import (
    derive_justification_artifact_id,
)
from propstore.families.identity.stances import derive_stance_artifact_id
from propstore.families.justifications import Justification
from propstore.families.micropublications import Micropublication
from propstore.families.registry import SourceRef
from propstore.families.relations import Stance
from propstore.families.sources import (
    SourceClaimDocument,
    SourceClaimsDocument,
    SourceConceptEntryDocument,
    SourceFinalizeReportDocument,
    SourceJustificationsDocument,
    SourceMicropublicationsDocument,
    SourceStancesDocument,
    SourceTrustDocument,
    SourceTrustPriorDocument,
)
from propstore.provenance import (
    Provenance,
    ProvenanceStatus,
    ProvenanceWitness,
    write_provenance_note,
)
from propstore.repository import Repository
from propstore.source_trust_argumentation import calibrate_source_trust

from .claim_concepts import build_promoted_claim, source_concept_ref_requires_mapping
from .common import (
    load_source_claims_document,
    load_source_concepts_document,
    load_source_document,
    load_source_finalize_report,
    load_source_justifications_document,
    load_source_micropubs_document,
    load_source_stances_document,
    normalize_source_slug,
    source_branch_name,
    source_paper_slug,
    utc_now,
)
from .reference_indexes import (
    primary_claim_index as build_primary_claim_index,
    resolve_source_or_primary_claim_id,
    source_claim_index as build_source_claim_index,
)
from .registry import (
    load_primary_branch_concepts,
    primary_branch_concept_id_by_name,
)
from .stages import SourcePromotionPlan


@dataclass(frozen=True)
class SourceConceptPromotionResolution:
    """The concept-handle → canonical-id resolution for one source branch."""

    concept_map: dict[str, str]
    promoted_concept_documents: dict[str, Concept]
    blocked_concept_refs: dict[str, str]


@dataclass(frozen=True)
class PromotionBlockedProjectionRows:
    """The world-sidecar mirror of a source branch's blocked-promotion state.

    The quarantine *invariant* is met without this (blocked claims stay on the
    source branch and are surfaced in :class:`PromotionResult`); this is the
    derived-store *projection* of that same state so a render/audit surface can
    read it back. In the charter rewrite the reference's ``CLAIM_CORE_PROJECTION``
    blocked rows collapse onto the world ``claim`` charter (which is the master
    projection only — no per-row ``branch`` column), so the branch-scoped blocked
    state rides entirely on :class:`~propstore.families.diagnostics.BuildDiagnostic`
    rows: each carries ``diagnostic_kind='promotion_blocked'`` and a
    ``source_ref`` of ``"<source-branch>:<artifact-id>"``. They are *present* in
    the sidecar (filtered at render via ``policy.show_quarantined``), never
    dropped (CLAUDE.md non-commitment).
    """

    diagnostics: tuple[BuildDiagnostic, ...]


@dataclass(frozen=True)
class PromotionResult:
    """The outcome of a source promotion.

    ``commit_sha`` is the atomic ``master`` commit. ``blocked_claims`` and
    ``blocked_diagnostics`` carry the quarantined per-item rivals that stayed on
    the source branch (present, never dropped).
    """

    commit_sha: str
    blocked_claims: tuple[SourceClaimDocument, ...]
    blocked_diagnostics: dict[str, tuple[tuple[str, str], ...]]
    sidecar_mirror_ok: bool = True
    sidecar_mirror_error: str | None = None


def load_finalize_report(
    repo: Repository, source_name: str
) -> SourceFinalizeReportDocument | None:
    """Load the source branch's finalize report (its promotability precondition)."""

    return load_source_finalize_report(repo, source_name)


def master_context_ids(repo: Repository) -> set[str]:
    git = repo.git
    if git is None:
        return set()
    tip = git.branch_sha(git.primary_branch_name())
    if tip is None:
        return set()
    return {handle.ref for handle in repo.families.context.iter_handles(commit=tip)}


def _source_claim_concept_refs(claim: SourceClaimDocument) -> tuple[str, ...]:
    """Every source-local concept handle a claim carries (any field)."""

    refs: list[str] = []
    for value in (claim.concept, claim.target_concept):
        if isinstance(value, str) and value:
            refs.append(value)
    refs.extend(value for value in claim.concepts if value)
    refs.extend(variable.concept for variable in claim.variables if variable.concept)
    refs.extend(parameter.concept for parameter in claim.parameters if parameter.concept)
    return tuple(refs)


def resolve_source_concept_promotions(
    repo: Repository, source_name: str
) -> SourceConceptPromotionResolution:
    """Map each proposed source concept to a canonical id (reusing or minting).

    A registry-matched or name-matched proposal reuses the existing canonical id;
    an unmatched proposal mints ``ps:concept:<sha>`` and a complete canonical
    :class:`Concept`. A minted id that collides with an existing concept, or with
    a second proposal carrying a different handle, is ambiguous: it is recorded
    in ``blocked_concept_refs`` (quarantined) rather than merging two rivals.
    """

    concepts_doc = load_source_concepts_document(repo, source_name)
    existing_by_id = load_primary_branch_concepts(repo)
    name_to_id = primary_branch_concept_id_by_name(repo)

    mapping: dict[str, str] = {}
    concept_documents: dict[str, Concept] = {}
    blocked_concept_refs: dict[str, str] = {}
    minted_by_handle: dict[str, str] = {}

    def handle_set(entry: SourceConceptEntryDocument, seed: str) -> set[str]:
        return {
            handle
            for handle in (entry.local_name, entry.proposed_name, seed)
            if isinstance(handle, str) and handle
        }

    def block_entry(
        entry: SourceConceptEntryDocument, seed: str, detail: str
    ) -> None:
        for handle in handle_set(entry, seed):
            blocked_concept_refs[handle] = detail
            mapping.pop(handle, None)

    entries: tuple[SourceConceptEntryDocument, ...] = (
        () if concepts_doc is None else concepts_doc.concepts
    )
    for entry in entries:
        registry_match = entry.registry_match
        if registry_match is not None and registry_match.artifact_id:
            for handle in (entry.local_name, entry.proposed_name):
                if isinstance(handle, str) and handle:
                    mapping[handle] = registry_match.artifact_id
            continue

        matched: str | None = None
        for handle in (entry.local_name, entry.proposed_name):
            if not isinstance(handle, str) or not handle:
                continue
            matched = name_to_id.get(normalize_source_slug(handle).casefold())
            if matched is not None:
                mapping[handle] = matched
        if matched is not None:
            continue

        seed = str(entry.proposed_name or entry.local_name or "concept").strip()
        slug = normalize_source_slug(seed)
        concept_id = derive_concept_artifact_id(slug)

        if concept_id in existing_by_id:
            block_entry(entry, seed, f"ambiguous concept mappings: {seed}")
            continue
        prior_seed = minted_by_handle.get(concept_id)
        if prior_seed is not None and prior_seed != seed:
            block_entry(entry, seed, f"ambiguous concept mappings: {seed}, {prior_seed}")
            concept_documents.pop(concept_id, None)
            minted_by_handle.pop(concept_id, None)
            continue

        minted_by_handle[concept_id] = seed
        form_parameters = entry.form_parameters
        concept_documents[concept_id] = Concept(
            concept_id=concept_id,
            canonical_name=seed,
            status=ConceptStatus.AUTHORED,
            definition=(entry.definition or None),
            category_values=(
                ()
                if form_parameters is None or form_parameters.values is None
                else form_parameters.values
            ),
            category_extensible=(
                True
                if form_parameters is None or form_parameters.extensible is None
                else form_parameters.extensible
            ),
            lexical_entry=LexicalEntry(
                identifier=f"entry:{slug}",
                canonical_form=LexicalForm(written_rep=seed, language="en"),
                senses=(
                    LexicalSense(
                        reference=OntologyReference(uri=concept_id),
                        usage=entry.definition or None,
                    ),
                ),
                physical_dimension_form=entry.form,
            ),
        )
        for handle in (entry.local_name, entry.proposed_name):
            if isinstance(handle, str) and handle:
                mapping[handle] = concept_id

    return SourceConceptPromotionResolution(
        concept_map=mapping,
        promoted_concept_documents=concept_documents,
        blocked_concept_refs=blocked_concept_refs,
    )


def compute_blocked_claim_artifact_ids(
    *,
    claims_doc: SourceClaimsDocument | None,
    justifications_doc: SourceJustificationsDocument | None,
    source_claim_index_exists: Callable[[object], bool],
    concept_map: dict[str, str],
    blocked_concept_refs: dict[str, str],
    master_context_ids: set[str],
) -> tuple[set[str], dict[str, list[tuple[str, str]]]]:
    """Identify source claims blocked from promotion by per-item errors.

    A claim is blocked when it has no canonical ``artifact_id``, references a
    concept handle that could not be lowered, names a context that is not on
    master, or is the conclusion/premise of a justification whose sibling
    references are unresolved. Returns the blocked-id set and, per id, a list of
    ``(kind, detail)`` diagnostics. Blocking is quarantine, not deletion.
    """

    blocked: set[str] = set()
    reasons: dict[str, list[tuple[str, str]]] = {}

    def record(artifact_id: str, kind: str, detail: str) -> None:
        blocked.add(artifact_id)
        reasons.setdefault(artifact_id, []).append((kind, detail))

    for claim in () if claims_doc is None else claims_doc.claims:
        artifact_id = claim.artifact_id
        if not isinstance(artifact_id, str) or not artifact_id:
            raw_id = str(claim.id or "?")
            record(raw_id, "claim_reference", f"claim {raw_id!r} missing artifact_id")
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
                record(
                    artifact_id,
                    "concept_mapping",
                    f"claim concept {concept_ref!r} blocked: {detail}",
                )
        context = claim.context
        if isinstance(context, str) and context and context not in master_context_ids:
            record(
                artifact_id,
                "context_reference",
                f"claim context {context!r} is not on the primary branch",
            )

    for justification in () if justifications_doc is None else justifications_doc.justifications:
        conclusion = justification.conclusion
        if isinstance(conclusion, str) and not source_claim_index_exists(conclusion):
            record(
                conclusion,
                "justification_reference",
                f"justification conclusion {conclusion!r} unresolved",
            )
        for premise in justification.premises:
            if not source_claim_index_exists(premise):
                record(
                    premise,
                    "justification_reference",
                    f"justification premise {premise!r} unresolved",
                )

    return blocked, reasons


def _blocked_diagnostic_rows(
    branch: str, reasons: dict[str, list[tuple[str, str]]]
) -> tuple[BuildDiagnostic, ...]:
    """Lower per-claim block reasons to ``promotion_blocked`` diagnostic rows.

    One row per ``(claim, reason)`` pair: ``source_ref`` encodes the branch so the
    reader can scope by source branch (the world ``claim`` charter has no branch
    column), ``claim_id`` carries the blocked artifact id, and ``detail_json``
    keeps the structured ``reason_kind`` alongside the human message.
    """

    rows: list[BuildDiagnostic] = []
    for artifact_id in sorted(reasons):
        source_ref = f"{branch}:{artifact_id}"
        for index, (kind, detail) in enumerate(reasons[artifact_id]):
            rows.append(
                BuildDiagnostic(
                    diagnostic_id=f"diag:promotion_blocked:{source_ref}:{index}",
                    source_kind="claim",
                    diagnostic_kind="promotion_blocked",
                    severity="error",
                    blocking=1,
                    message=detail,
                    claim_id=artifact_id,
                    source_ref=source_ref,
                    detail_json=json.dumps(
                        {"reason_kind": kind, "source_branch": branch},
                        sort_keys=True,
                    ),
                )
            )
    return tuple(rows)


def compile_source_promotion_blocked_projection_rows(
    repo: Repository, source_name: str
) -> PromotionBlockedProjectionRows:
    """Project one source branch's blocked-promotion state for the sidecar.

    Recomputes the same per-item quarantine :func:`promote_source_branch` would
    apply (unresolved concept mapping, off-master context, dangling justification
    reference) and lowers each blocked claim's reasons to ``promotion_blocked``
    diagnostic rows. A branch with no finalize report, no claims, or no blocked
    claims projects nothing.
    """

    claims_doc = load_source_claims_document(repo, source_name)
    if claims_doc is None or not claims_doc.claims:
        return PromotionBlockedProjectionRows(())
    if load_finalize_report(repo, source_name) is None:
        return PromotionBlockedProjectionRows(())

    concept_resolution = resolve_source_concept_promotions(repo, source_name)
    source_index = build_source_claim_index(repo, source_name)
    _, reasons = compute_blocked_claim_artifact_ids(
        claims_doc=claims_doc,
        justifications_doc=load_source_justifications_document(repo, source_name),
        source_claim_index_exists=source_index.exists,
        concept_map=concept_resolution.concept_map,
        blocked_concept_refs=concept_resolution.blocked_concept_refs,
        master_context_ids=master_context_ids(repo),
    )
    if not reasons:
        return PromotionBlockedProjectionRows(())
    branch = source_branch_name(source_name)
    return PromotionBlockedProjectionRows(_blocked_diagnostic_rows(branch, reasons))


def compile_all_source_promotion_blocked_projection_rows(
    repo: Repository,
) -> PromotionBlockedProjectionRows:
    """Project the blocked-promotion state of *every* source branch for the build.

    Scanned at build time (the source branches are independent refs, current as of
    their own tips), so the world sidecar mirrors whatever each source branch's
    quarantine state is — present, never collapsed.
    """

    git = repo.git
    if git is None:
        return PromotionBlockedProjectionRows(())
    diagnostics: list[BuildDiagnostic] = []
    for branch in repo.snapshot.iter_branches():
        if branch.kind != "source":
            continue
        source_name = branch.name.removeprefix("source/")
        rows = compile_source_promotion_blocked_projection_rows(repo, source_name)
        diagnostics.extend(rows.diagnostics)
    return PromotionBlockedProjectionRows(tuple(diagnostics))


def _revalidate_promoted_claims(
    repo: Repository,
    *,
    valid_claims: list[SourceClaimDocument],
    concept_map: dict[str, str],
    promoted_concepts: dict[str, Concept],
    master_commit: str | None,
) -> dict[str, str]:
    """Run the full claim CEL/contract pipeline over the about-to-promote claims.

    The registry's commit-time foreign-key gate already enforces canonical
    reference integrity; this adds the semantic claim check (type contract, CEL
    condition type-checking, context resolution) the source-promote path deferred
    in 8-3b. It composes the shared compiler (a downward call from the promote
    orchestrator) over the immutable promoted-claim rebuilds, with the master
    concept/form/context state plus the about-to-mint promoted concepts in scope so
    a claim's lowered references resolve. Returns ``{claim_id: message}`` for each
    semantically invalid claim. Per the Z1 split, a semantically invalid claim is
    *quarantined* by the caller (added to the blocked set) — not aborted; only a
    schema-undecodable document aborts, and the promoted claims here are already
    decoded source claims.
    """

    from propstore.compiler.context import build_compilation_context
    from propstore.compiler.ir import ClaimCheckedBundle
    from propstore.families.claims_passes import (
        ClaimFiles,
        LoadedClaim,
        run_claim_pipeline,
    )
    from propstore.families.concepts_passes import (
        ConceptCheckedRegistry,
        ConceptPipelineContext,
        LoadedConcept,
        run_concept_pipeline,
    )
    from propstore.families.forms import FormDefinition

    promoted: dict[str, Claim] = {}
    unresolved: set[str] = set()
    for claim in valid_claims:
        artifact_id = claim.artifact_id
        if not isinstance(artifact_id, str) or not artifact_id:
            continue
        promoted[artifact_id] = build_promoted_claim(
            claim, concept_map=concept_map, unresolved=unresolved
        )
    master_concepts = [
        handle.document
        for handle in repo.families.concept.iter_handles(commit=master_commit)
        if isinstance(handle.document, Concept)
    ]
    concepts = [*master_concepts, *promoted_concepts.values()]
    form_registry = {
        handle.document.name: handle.document
        for handle in repo.families.by_name("form").iter_handles(commit=master_commit)
        if isinstance(handle.document, FormDefinition)
    }
    concept_result = run_concept_pipeline(
        [LoadedConcept(concept=concept) for concept in concepts],
        context=ConceptPipelineContext(form_registry=form_registry),
    )
    if not isinstance(concept_result.output, ConceptCheckedRegistry):
        message = "; ".join(
            diagnostic.message for diagnostic in concept_result.diagnostics
        )
        raise ValueError(f"concept validation failed during promotion: {message}")
    if not promoted:
        return {}
    compilation_context = build_compilation_context(
        concept_result.output,
        form_registry=form_registry,
        claims=tuple(promoted.values()),
        context_ids=master_context_ids(repo),
    )
    result = run_claim_pipeline(
        ClaimFiles.from_sequence(
            [LoadedClaim(claim=claim) for claim in promoted.values()],
            compilation_context,
        )
    )
    bundle = result.output
    if not isinstance(bundle, ClaimCheckedBundle):
        return {}
    errors: dict[str, str] = {}
    for checked in bundle.claims:
        if checked.blocked:
            errors[checked.claim.claim_id] = (
                "; ".join(diagnostic.message for diagnostic in checked.diagnostics)
                or "claim failed semantic validation"
            )
    return errors


def _assemble_source_promotion_plan(
    repo: Repository,
    *,
    source_name: str,
    slug: str,
    claims_doc: SourceClaimsDocument | None,
    micropubs_doc: SourceMicropublicationsDocument | None,
    justifications_doc: SourceJustificationsDocument | None,
    stances_doc: SourceStancesDocument | None,
    concept_map: dict[str, str],
    promoted_concept_documents: dict[str, Concept],
    valid_claims: list[SourceClaimDocument],
    blocked_claims: list[SourceClaimDocument],
    blocked_reasons: dict[str, list[tuple[str, str]]],
    source_claim_index: FamilyReferenceIndex[SourceClaimDocument],
    primary_claim_index: FamilyReferenceIndex[Claim],
) -> SourcePromotionPlan:
    unresolved: set[str] = set()
    promoted_claims: dict[str, Claim] = {
        claim.artifact_id: build_promoted_claim(
            claim, concept_map=concept_map, unresolved=unresolved
        )
        for claim in valid_claims
        if isinstance(claim.artifact_id, str)
    }
    if unresolved:
        formatted = ", ".join(sorted(unresolved))
        raise ValueError(
            f"Cannot promote source {source_name!r}; unresolved concept mappings: {formatted}"
        )

    valid_artifact_ids = set(promoted_claims)

    def resolve_claim(reference: object) -> str | None:
        if not isinstance(reference, str) or not reference:
            return None
        resolved = resolve_source_or_primary_claim_id(
            reference, source=source_claim_index, primary=primary_claim_index
        )
        if resolved is None:
            return None
        if source_claim_index.resolve_id(reference) is not None:
            return resolved if resolved in valid_artifact_ids else None
        return resolved

    promoted_justifications: dict[str, Justification] = {}
    for justification in () if justifications_doc is None else justifications_doc.justifications:
        conclusion = resolve_claim(justification.conclusion)
        if conclusion is None:
            continue
        premises = tuple(resolve_claim(premise) for premise in justification.premises)
        if any(premise is None for premise in premises):
            continue
        resolved_premises = tuple(premise for premise in premises if premise is not None)
        justification_id = derive_justification_artifact_id(
            conclusion=conclusion,
            premises=resolved_premises,
            rule_kind=justification.rule_kind,
            rule_strength=justification.rule_strength,
        )
        promoted_justifications[justification_id] = Justification(
            justification_id=justification_id,
            conclusion=conclusion,
            premises=resolved_premises,
            rule_kind=justification.rule_kind,
            rule_strength=justification.rule_strength,
        )

    promoted_stances: dict[str, Stance] = {}
    for stance in () if stances_doc is None else stances_doc.stances:
        source_claim_id = resolve_claim(stance.source_claim)
        target_claim_id = resolve_claim(stance.target)
        if source_claim_id is None or target_claim_id is None:
            continue
        stance_type = stance.type.value if stance.type is not None else None
        stance_id = derive_stance_artifact_id(
            source_claim_id=source_claim_id,
            target_claim_id=target_claim_id,
            stance_type=stance_type,
        )
        promoted_stances[stance_id] = Stance(
            stance_id=stance_id,
            source_claim_id=source_claim_id,
            target_claim_id=target_claim_id,
            stance_type=stance.type,
        )

    promoted_micropubs: dict[str, Micropublication] = {}
    context_ids = master_context_ids(repo)
    for micropub in () if micropubs_doc is None else micropubs_doc.micropubs:
        if micropub.context_id not in context_ids:
            continue
        if any(claim_id not in valid_artifact_ids for claim_id in micropub.claims):
            continue
        promoted_micropubs[micropub.artifact_id] = Micropublication(
            artifact_id=micropub.artifact_id,
            context_id=micropub.context_id,
            claims=micropub.claims,
            version_id=micropub.version_id,
            evidence=micropub.evidence,
            assumptions=micropub.assumptions,
            stance=micropub.stance,
            source=micropub.source,
        )

    return SourcePromotionPlan(
        source_name=source_name,
        slug=slug,
        source_branch=source_branch_name(source_name),
        promoted_concept_documents=promoted_concept_documents,
        promoted_claim_documents=promoted_claims,
        promoted_micropub_documents=promoted_micropubs,
        promoted_justification_documents=promoted_justifications,
        promoted_stance_documents=promoted_stances,
        blocked_claims=tuple(blocked_claims),
        blocked_reasons={
            claim_id: tuple(entries) for claim_id, entries in blocked_reasons.items()
        },
    )


def _commit_promote_time_trust_calibration(
    repo: Repository, source_name: str, *, promotion_commit_sha: str
) -> None:
    """Calibrate and STAMP source trust onto the manifest (never a gate).

    Computes an honestly typed prior-trust opinion and writes it onto the source
    manifest's ``trust``. It never rejects a claim — a low-trust source has
    already promoted by the time this runs; this only records the calibrated
    provenance. A no-op calibration (trust unchanged) writes nothing.
    """

    calibration = calibrate_source_trust(
        repo, source_name, world_snapshot=promotion_commit_sha
    )
    source_doc = load_source_document(repo, source_name)
    prior: SourceTrustPriorDocument | None = None
    if calibration.status is ProvenanceStatus.CALIBRATED:
        opinion = calibration.prior_base_rate
        prior = SourceTrustPriorDocument(
            b=opinion.b, d=opinion.d, u=opinion.u, a=opinion.a
        )
    updated_trust = SourceTrustDocument(
        status=calibration.status,
        quality=source_doc.trust.quality,
        prior_base_rate=prior,
        derived_from=tuple(firing.rule_id for firing in calibration.derived_from),
    )
    if updated_trust == source_doc.trust:
        return None
    updated_source = msgspec.structs.replace(source_doc, trust=updated_trust)
    repo.families.source_documents.save(
        SourceRef(source_name),
        updated_source,
        message=f"Calibrate source trust for {source_paper_slug(source_name)}",
    )
    return None


def promote_source_branch(
    repo: Repository, source_name: str, *, strict: bool = False
) -> PromotionResult:
    """Promote a finalized source branch into ``master``.

    Valid claims (and their resolved concepts, stances, justifications, and
    micropublications) are written in one atomic commit; blocked claims are
    quarantined on the source branch and surfaced in the result. After the commit
    the promotion provenance is attached as a git note and the source's prior
    trust is calibrated and stamped onto its manifest.
    """

    report = load_finalize_report(repo, source_name)
    if report is None:
        raise ValueError(
            f"Source {source_name!r} must be finalized before promotion "
            "(no finalize report found)"
        )
    if strict and report.status != "ready":
        raise ValueError(
            f"Source {source_name!r} must be finalized successfully before "
            "promotion (strict mode)"
        )

    git = repo.git
    if git is None:
        raise ValueError("source promotion requires a git-backed repository")

    slug = source_paper_slug(source_name)
    claims_doc = load_source_claims_document(repo, source_name)
    micropubs_doc = load_source_micropubs_document(repo, source_name)
    justifications_doc = load_source_justifications_document(repo, source_name)
    stances_doc = load_source_stances_document(repo, source_name)

    concept_resolution = resolve_source_concept_promotions(repo, source_name)
    source_claim_index = build_source_claim_index(repo, source_name)
    primary_claim_index = build_primary_claim_index(repo)
    context_ids = master_context_ids(repo)

    blocked_artifact_ids, blocked_reasons = compute_blocked_claim_artifact_ids(
        claims_doc=claims_doc,
        justifications_doc=justifications_doc,
        source_claim_index_exists=source_claim_index.exists,
        concept_map=concept_resolution.concept_map,
        blocked_concept_refs=concept_resolution.blocked_concept_refs,
        master_context_ids=context_ids,
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

    cel_errors = _revalidate_promoted_claims(
        repo,
        valid_claims=valid_claims,
        concept_map=concept_resolution.concept_map,
        promoted_concepts=concept_resolution.promoted_concept_documents,
        master_commit=git.branch_sha(git.primary_branch_name()),
    )
    if cel_errors:
        for claim_id, message in cel_errors.items():
            blocked_artifact_ids.add(claim_id)
            blocked_reasons.setdefault(claim_id, []).append(
                ("claim_validation", message)
            )
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
        details = sorted(
            {
                detail
                for entries in blocked_reasons.values()
                for _, detail in entries
            }
        )
        suffix = f": {'; '.join(details)}" if details else ""
        raise ValueError(
            f"Source {source_name!r}: all {len(blocked_claims)} claims blocked "
            f"from promotion; see blocked diagnostics for details{suffix}"
        )

    plan = _assemble_source_promotion_plan(
        repo,
        source_name=source_name,
        slug=slug,
        claims_doc=claims_doc,
        micropubs_doc=micropubs_doc,
        justifications_doc=justifications_doc,
        stances_doc=stances_doc,
        concept_map=concept_resolution.concept_map,
        promoted_concept_documents=concept_resolution.promoted_concept_documents,
        valid_claims=valid_claims,
        blocked_claims=blocked_claims,
        blocked_reasons=blocked_reasons,
        source_claim_index=source_claim_index,
        primary_claim_index=primary_claim_index,
    )

    with git.head_bound_transaction(git.primary_branch_name()) as head_txn:
        with head_txn.families_transact(
            repo.families, message=f"Promote source {slug}"
        ) as transaction:
            for concept_id, concept in plan.promoted_concept_documents.items():
                transaction.concept.save(concept_id, concept)
            for claim_id, claim in plan.promoted_claim_documents.items():
                transaction.claim.save(claim_id, claim)
            for justification_id, justification in plan.promoted_justification_documents.items():
                transaction.justification.save(justification_id, justification)
            for stance_id, stance in plan.promoted_stance_documents.items():
                transaction.stance.save(stance_id, stance)
            for micropub_id, micropub in plan.promoted_micropub_documents.items():
                transaction.micropublication.save(micropub_id, micropub)
        sha = head_txn.commit_sha
    if sha is None:
        raise ValueError("source promotion transaction did not produce a commit")

    source_branch_tip = git.branch_sha(plan.source_branch)
    write_provenance_note(
        git.raw_repo,
        sha,
        Provenance(
            status=ProvenanceStatus.STATED,
            witnesses=(
                ProvenanceWitness(
                    asserter="urn:propstore:agent:source-promote",
                    timestamp=utc_now(),
                    source_artifact_code=plan.source_branch,
                    method="promote",
                ),
            ),
            graph_name=f"urn:propstore:source-promote:{sha}",
            derived_from=() if source_branch_tip is None else (source_branch_tip,),
            operations=("promote",),
        ),
    )

    _commit_promote_time_trust_calibration(
        repo, source_name, promotion_commit_sha=sha
    )

    return PromotionResult(
        commit_sha=sha,
        blocked_claims=plan.blocked_claims,
        blocked_diagnostics=plan.blocked_reasons,
    )


def sync_source_branch(
    repo: Repository,
    source_name: str,
    *,
    output_dir: Path | None = None,
) -> Path:
    """Materialize a source branch's tree to a directory (default ``../papers``)."""

    branch = source_branch_name(source_name)
    tip = repo.require_git().branch_sha(branch)
    if tip is None:
        raise ValueError(f"Source branch {branch!r} does not exist")

    destination = output_dir
    if destination is None:
        destination = repo.root.parent / "papers" / source_paper_slug(source_name)
    destination.mkdir(parents=True, exist_ok=True)
    destination_root = destination.resolve()

    for tree_file in repo.require_git().iter_tree_files(commit=tip):
        target = _source_sync_target_path(destination_root, tree_file.relpath)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(tree_file.content)
    return destination


def _source_sync_target_path(destination_root: Path, relpath: str) -> Path:
    """Resolve a sync relpath under *destination_root*, rejecting path escapes.

    Zip Slip (Snyk Security, 2018): never trust a snapshot entry path until it has
    been proven relative to the intended extraction root.
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
