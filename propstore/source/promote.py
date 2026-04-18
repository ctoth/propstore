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

import copy
import json
import sqlite3
from pathlib import Path
from typing import Any

from propstore.artifacts.codes import attach_source_artifact_codes
from propstore.artifacts import (
    CANONICAL_SOURCE_FAMILY,
    CLAIMS_FILE_FAMILY,
    ClaimReferenceResolver,
    CONCEPT_FILE_FAMILY,
    JUSTIFICATIONS_FILE_FAMILY,
    MICROPUBS_FILE_FAMILY,
    load_primary_branch_claim_reference_index,
    normalize_canonical_claim_payload,
    normalize_canonical_concept_payload,
    load_source_claim_reference_index,
    STANCE_FILE_FAMILY,
    CanonicalSourceRef,
    ClaimsFileRef,
    ConceptFileRef,
    JustificationsFileRef,
    MicropubsFileRef,
    StanceFileRef,
)
from propstore.artifacts.documents.concepts import ConceptDocument
from propstore.artifacts.documents.claims import ClaimsFileDocument
from propstore.artifacts.documents.micropubs import MicropublicationsFileDocument
from propstore.repository import Repository
from quire.documents import convert_document_value
from propstore.artifacts.documents.sources import (
    SourceConceptEntryDocument,
    SourceDocument,
    SourceJustificationsDocument,
)
from propstore.artifacts.documents.stances import StanceFileDocument

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
)
from .registry import load_primary_branch_concepts


def rewrite_claim_concept_refs(
    claim: dict[str, Any],
    concept_map: dict[str, str],
    *,
    unresolved: set[str],
) -> dict[str, Any]:
    normalized = copy.deepcopy(claim)

    def resolve(value: object) -> object:
        if not isinstance(value, str):
            return value
        if value.startswith("ps:concept:") or value.startswith("tag:"):
            return value
        resolved = concept_map.get(value)
        if resolved is None:
            unresolved.add(value)
            return value
        return resolved

    for field in ("concept", "target_concept"):
        if field in normalized:
            normalized[field] = resolve(normalized.get(field))
    if isinstance(normalized.get("concepts"), list):
        normalized["concepts"] = [resolve(value) for value in normalized["concepts"]]
    if isinstance(normalized.get("variables"), list):
        for variable in normalized["variables"]:
            if isinstance(variable, dict):
                variable["concept"] = resolve(variable.get("concept"))
    if isinstance(normalized.get("parameters"), list):
        for parameter in normalized["parameters"]:
            if isinstance(parameter, dict):
                parameter["concept"] = resolve(parameter.get("concept"))
    return normalize_canonical_claim_payload(normalized)


def _normalize_promoted_claim_context(claim: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(claim)
    context = normalized.get("context")
    if isinstance(context, str):
        normalized["context"] = {"id": context}
    return normalized


def _filter_promoted_micropubs(
    micropubs_doc: MicropublicationsFileDocument | None,
    *,
    valid_artifact_ids: set[str],
) -> MicropublicationsFileDocument | None:
    if micropubs_doc is None:
        return None
    kept = [
        micropub.to_payload()
        for micropub in micropubs_doc.micropubs
        if all(claim_id in valid_artifact_ids for claim_id in micropub.claims)
    ]
    if not kept:
        return None
    return convert_document_value(
        {
            "source": None if micropubs_doc.source is None else micropubs_doc.source.to_payload(),
            "micropubs": kept,
        },
        MicropublicationsFileDocument,
        source="micropubs/promoted.yaml",
    )


def resolve_source_concept_promotions(
    repo: Repository,
    source_name: str,
) -> tuple[dict[str, str], dict[str, ConceptDocument]]:
    concepts_doc = load_source_concepts_document(repo, source_name)
    concepts_by_artifact, handle_to_artifact = load_primary_branch_concepts(repo)
    mapping: dict[str, str] = {}
    concept_documents: dict[str, ConceptDocument] = {}
    new_concepts: list[tuple[SourceConceptEntryDocument, str, str]] = []
    seen_new_artifacts: dict[str, str] = {}

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
            if isinstance(handle, str) and handle in handle_to_artifact:
                matched_artifact_id = handle_to_artifact[handle]
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
            raise ValueError(f"Cannot promote source {source_name!r}; ambiguous concept mappings: {handle_seed}")
        prior_handle = seen_new_artifacts.get(artifact_id)
        if prior_handle is not None and prior_handle != handle_seed:
            raise ValueError(
                f"Cannot promote source {source_name!r}; ambiguous concept mappings: {handle_seed}, {prior_handle}"
            )
        seen_new_artifacts[artifact_id] = handle_seed
        new_concepts.append((entry, artifact_id, slug))
        for handle in (entry.local_name, entry.proposed_name):
            if isinstance(handle, str) and handle:
                mapping[handle] = artifact_id

    for raw_entry, artifact_id, slug in new_concepts:
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
                resolved = mapping.get(input_ref) or handle_to_artifact.get(input_ref)
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
            source=CONCEPT_FILE_FAMILY.resolve_ref(repo, concept_ref).relpath,
        )

    return mapping, concept_documents


def load_finalize_report(repo: Repository, source_name: str):
    return load_source_finalize_report(repo, source_name)


def _compute_blocked_claim_artifact_ids(
    claims_doc,
    justifications_doc,
    stances_doc,
    resolver: ClaimReferenceResolver,
    source_claim_index,
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

    # (b) stances referencing unknown targets block the stance's source_claim.
    for stance in () if stances_doc is None else stances_doc.stances:
        source_claim = stance.source_claim
        target = stance.target
        if isinstance(source_claim, str) and source_claim:
            if not source_claim_index.has_artifact(source_claim):
                _record(
                    source_claim,
                    "stance_reference",
                    f"stance source_claim {source_claim!r} unresolved",
                )
            if not isinstance(target, str) or not target or not resolver.target_is_known(target):
                _record(
                    source_claim,
                    "stance_reference",
                    f"stance target {target!r} unresolved",
                )

    # (c) justifications with unresolved conclusion or premises block the
    # claims those references point at (when they resolve to valid
    # artifact ids on the source branch).
    for justification in () if justifications_doc is None else justifications_doc.justifications:
        conclusion = justification.conclusion
        if isinstance(conclusion, str) and not source_claim_index.has_artifact(conclusion):
            _record(
                conclusion,
                "justification_reference",
                f"justification conclusion {conclusion!r} unresolved",
            )
        for premise in justification.premises:
            if isinstance(premise, str) and not source_claim_index.has_artifact(premise):
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

    conn = sqlite3.connect(sidecar_path)
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        for claim in blocked_claims:
            artifact_id = claim.artifact_id
            if not isinstance(artifact_id, str) or not artifact_id:
                # Fall back to raw id — upstream shouldn't produce this,
                # but the path must not crash on a malformed claim.
                artifact_id = str(claim.id or "?")
            # Delete any prior mirror row for this (artifact_id, branch)
            # so re-promote after a fix doesn't leave stale rows.
            conn.execute(
                "DELETE FROM claim_core WHERE id = ? AND branch = ?",
                (artifact_id, source_branch),
            )
            conn.execute(
                "DELETE FROM build_diagnostics WHERE claim_id = ? "
                "AND diagnostic_kind = 'promotion_blocked'",
                (artifact_id,),
            )

            conn.execute(
                """
                INSERT INTO claim_core (
                    id, primary_logical_id, logical_ids_json, version_id,
                    content_hash, seq, type, concept_id, target_concept,
                    source_slug, source_paper, provenance_page,
                    provenance_json, context_id, premise_kind, branch,
                    build_status, stage, promotion_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        f"{source_branch}:{artifact_id}",
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


def promote_source_branch(
    repo: Repository,
    source_name: str,
    *,
    strict: bool = False,
) -> str:
    report = load_finalize_report(repo, source_name)
    if report is None:
        raise ValueError(
            f"Source {source_name!r} must be finalized before promotion "
            "(no finalize report found)"
        )
    # Per axis-1 finding 3.3: the all-or-nothing gate becomes a per-item
    # filter. ``strict=True`` preserves the old behavior for callers that
    # explicitly opt in (e.g., ``pks source promote --strict``).
    if strict and report.status != "ready":
        raise ValueError(
            f"Source {source_name!r} must be finalized successfully "
            "before promotion (strict mode)"
        )

    slug = normalize_source_slug(source_name)
    source_doc = load_source_document(repo, source_name)
    claims_doc = load_source_claims_document(repo, source_name)
    micropubs_doc = load_source_micropubs_document(repo, source_name)
    justifications_doc = load_source_justifications_document(repo, source_name)
    stances_doc = load_source_stances_document(repo, source_name)
    concept_map, promoted_concept_documents = resolve_source_concept_promotions(repo, source_name)
    unresolved_concepts: set[str] = set()

    source_claim_index = load_source_claim_reference_index(repo, source_name)
    resolver = ClaimReferenceResolver(
        source=source_claim_index,
        primary=load_primary_branch_claim_reference_index(repo),
    )

    blocked_artifact_ids, blocked_reasons = _compute_blocked_claim_artifact_ids(
        claims_doc,
        justifications_doc,
        stances_doc,
        resolver,
        source_claim_index,
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
        raise ValueError(
            f"Source {source_name!r}: all {len(blocked_claims)} claims blocked "
            "from promotion; see build_diagnostics for details"
        )

    promoted_claims = [
        rewrite_claim_concept_refs(claim.to_payload(), concept_map, unresolved=unresolved_concepts)
        for claim in valid_claims
    ]
    if unresolved_concepts:
        formatted = ", ".join(sorted(unresolved_concepts))
        raise ValueError(f"Cannot promote source {source_name!r}; unresolved concept mappings: {formatted}")

    # Filter justifications and stances to those referencing only valid claims.
    valid_artifact_ids = {
        claim.artifact_id
        for claim in valid_claims
        if isinstance(claim.artifact_id, str)
    }
    promoted_micropubs_document = _filter_promoted_micropubs(
        micropubs_doc,
        valid_artifact_ids=valid_artifact_ids,
    )

    promoted_stance_documents: dict[str, StanceFileDocument] = {}
    promoted_stances: list[dict[str, Any]] = []
    for stance in (() if stances_doc is None else stances_doc.stances):
        source_claim = stance.source_claim
        if not isinstance(source_claim, str) or not source_claim:
            raise ValueError("stance source_claim must be normalized before promotion")
        # Skip stances whose source_claim is blocked or whose target
        # cannot be resolved under the current resolver.
        if source_claim not in valid_artifact_ids:
            continue
        if not resolver.target_is_known(stance.target):
            continue
        target = resolver.resolve_promoted_target(stance.target)
        normalized = stance.to_payload()
        normalized["target"] = target
        promoted_stances.append(normalized)

    promoted_claims_doc = {
        "source": (
            {"paper": slug}
            if claims_doc is None or claims_doc.source is None
            else claims_doc.source.to_payload()
        ),
        "claims": promoted_claims,
    }

    # Per axis-1 finding 3.3: filter justifications to those whose
    # conclusion and all premises resolve to valid (non-blocked) source
    # claims. Blocked justifications stay on the source branch.
    if justifications_doc is None:
        filtered_justifications_payload = None
    else:
        valid_justification_entries: list[dict[str, Any]] = []
        for justification in justifications_doc.justifications:
            conclusion = justification.conclusion
            if not isinstance(conclusion, str):
                continue
            if conclusion not in valid_artifact_ids and not source_claim_index.has_artifact(conclusion):
                continue
            if any(
                not isinstance(premise, str)
                or (premise not in valid_artifact_ids and not source_claim_index.has_artifact(premise))
                for premise in justification.premises
            ):
                continue
            valid_justification_entries.append(justification.to_payload())
        justifications_payload = justifications_doc.to_payload()
        justifications_payload["justifications"] = valid_justification_entries
        filtered_justifications_payload = justifications_payload

    promoted_source_doc, promoted_claims_doc, promoted_justifications_doc, promoted_stances_doc = attach_source_artifact_codes(
        source_doc.to_payload(),
        promoted_claims_doc,
        filtered_justifications_payload,
        {"stances": promoted_stances},
    )
    promoted_claims = promoted_claims_doc.get("claims", []) or []
    promoted_source_paper = (
        str(promoted_claims_doc.get("source", {}).get("paper") or slug)
        if isinstance(promoted_claims_doc.get("source"), dict)
        else slug
    )

    for claim in promoted_claims:
        if isinstance(claim, dict):
            provenance = claim.get("provenance")
            if isinstance(provenance, dict) and not isinstance(provenance.get("paper"), str):
                updated_provenance = dict(provenance)
                updated_provenance["paper"] = promoted_source_paper
                claim["provenance"] = updated_provenance
            normalized_claim = _normalize_promoted_claim_context(claim)
            normalized_claim = normalize_canonical_claim_payload(
                normalized_claim,
                strip_source_local=True,
            )
            claim.clear()
            claim.update(normalized_claim)
    promoted_claims_doc["claims"] = promoted_claims

    stances_by_source: dict[str, list[dict[str, Any]]] = {}
    for stance in promoted_stances_doc.get("stances", []) or []:
        if not isinstance(stance, dict):
            continue
        source_claim = stance.get("source_claim")
        if isinstance(source_claim, str) and source_claim:
            stances_by_source.setdefault(source_claim, []).append(stance)

    for source_claim, entries in stances_by_source.items():
        stance_ref = StanceFileRef(source_claim)
        promoted_stance_documents[source_claim] = convert_document_value(
            {
                "source_claim": source_claim,
                "stances": entries,
            },
            StanceFileDocument,
            source=STANCE_FILE_FAMILY.resolve_ref(repo, stance_ref).relpath,
        )

    source_ref = CanonicalSourceRef(slug)
    claims_ref = ClaimsFileRef(slug)
    promoted_source_document = convert_document_value(
        promoted_source_doc,
        SourceDocument,
        source=CANONICAL_SOURCE_FAMILY.resolve_ref(repo, source_ref).relpath,
    )
    promoted_claims_document = convert_document_value(
        promoted_claims_doc,
        ClaimsFileDocument,
        source=CLAIMS_FILE_FAMILY.resolve_ref(repo, claims_ref).relpath,
    )

    with repo.artifacts.transact(
        message=f"Promote source {slug}",
        branch=repo.snapshot.primary_branch_name(),
    ) as transaction:
        transaction.save(
            CANONICAL_SOURCE_FAMILY,
            source_ref,
            promoted_source_document,
        )
        transaction.save(
            CLAIMS_FILE_FAMILY,
            claims_ref,
            promoted_claims_document,
        )
        if promoted_micropubs_document is not None:
            transaction.save(
                MICROPUBS_FILE_FAMILY,
                MicropubsFileRef(slug),
                promoted_micropubs_document,
            )
        for concept_slug, concept_document in promoted_concept_documents.items():
            transaction.save(
                CONCEPT_FILE_FAMILY,
                ConceptFileRef(concept_slug),
                concept_document,
            )
        if promoted_justifications_doc.get("justifications"):
            promoted_justifications_document = convert_document_value(
                promoted_justifications_doc,
                SourceJustificationsDocument,
                source=f"justifications/{slug}.yaml",
            )
            transaction.save(
                JUSTIFICATIONS_FILE_FAMILY,
                JustificationsFileRef(slug),
                promoted_justifications_document,
            )
        for source_claim, stance_document in promoted_stance_documents.items():
            transaction.save(
                STANCE_FILE_FAMILY,
                StanceFileRef(source_claim),
                stance_document,
            )
    sha = transaction.commit_sha
    if sha is None:
        raise ValueError("source promotion transaction did not produce a commit")
    repo.snapshot.sync_worktree()

    # Mirror blocked claims into the sidecar so the render layer can
    # surface them under opt-in policy flags (phase 4). If the sidecar
    # does not exist, this is a no-op.
    if blocked_claims:
        _write_promotion_blocked_sidecar_rows(
            repo.sidecar_path,
            source_branch_name(source_name),
            slug,
            blocked_claims,
            blocked_reasons,
        )

    return sha


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
        destination = papers_root / normalize_source_slug(source_name)
    destination.mkdir(parents=True, exist_ok=True)

    def copy_tree(relpath: str = "") -> None:
        for entry in repo.snapshot.list_dir_entries(relpath, commit=tip):
            target = destination / Path(*entry.relpath.split("/"))
            if entry.is_dir:
                target.mkdir(parents=True, exist_ok=True)
                copy_tree(entry.relpath)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(repo.snapshot.read_bytes(entry.relpath, commit=tip))

    copy_tree("")
    return destination
