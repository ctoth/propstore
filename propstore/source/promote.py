from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from propstore.artifacts.codes import attach_source_artifact_codes
from propstore.artifacts import (
    CANONICAL_SOURCE_FAMILY,
    CLAIMS_FILE_FAMILY,
    ClaimReferenceResolver,
    CONCEPT_FILE_FAMILY,
    JUSTIFICATIONS_FILE_FAMILY,
    load_primary_branch_claim_reference_index,
    normalize_canonical_claim_payload,
    normalize_canonical_concept_payload,
    load_source_claim_reference_index,
    STANCE_FILE_FAMILY,
    CanonicalSourceRef,
    ClaimsFileRef,
    ConceptFileRef,
    JustificationsFileRef,
    StanceFileRef,
)
from propstore.artifacts.documents.concepts import ConceptDocument
from propstore.claim_documents import ClaimsFileDocument
from propstore.cli.repository import Repository
from propstore.artifacts.schema import convert_document_value
from propstore.artifacts.documents.sources import SourceDocument, SourceJustificationsDocument
from propstore.stance_documents import StanceFileDocument

from .common import (
    load_source_claims_document,
    load_source_concepts_document,
    load_source_document,
    load_source_finalize_report,
    load_source_justifications_document,
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


def resolve_source_concept_promotions(
    repo: Repository,
    source_name: str,
) -> tuple[dict[str, str], dict[str, ConceptDocument]]:
    concepts_doc = load_source_concepts_document(repo, source_name)
    concepts_by_artifact, handle_to_artifact = load_primary_branch_concepts(repo)
    mapping: dict[str, str] = {}
    concept_documents: dict[str, ConceptDocument] = {}
    new_concepts: list[tuple[object, str, str]] = []
    seen_new_artifacts: dict[str, str] = {}

    for entry in (() if concepts_doc is None else concepts_doc.concepts):
        registry_match = entry.registry_match
        if registry_match is not None:
            artifact_id = registry_match.artifact_id
            if isinstance(artifact_id, str) and artifact_id:
                for key in ("local_name", "proposed_name"):
                    handle = getattr(entry, key)
                    if isinstance(handle, str) and handle:
                        mapping[handle] = artifact_id
                continue
        matched_artifact_id: str | None = None
        for key in ("local_name", "proposed_name"):
            handle = getattr(entry, key)
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
        for key in ("local_name", "proposed_name"):
            handle = getattr(entry, key)
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
        concept_documents[slug] = convert_document_value(
            concept_doc,
            ConceptDocument,
            source=f"concepts/{slug}.yaml",
        )

    return mapping, concept_documents


def load_finalize_report(repo: Repository, source_name: str):
    return load_source_finalize_report(repo, source_name)


def promote_source_branch(repo: Repository, source_name: str) -> str:
    report = load_finalize_report(repo, source_name)
    if report is None or report.status != "ready":
        raise ValueError(f"Source {source_name!r} must be finalized successfully before promotion")

    slug = normalize_source_slug(source_name)
    source_doc = load_source_document(repo, source_name)
    claims_doc = load_source_claims_document(repo, source_name)
    justifications_doc = load_source_justifications_document(repo, source_name)
    stances_doc = load_source_stances_document(repo, source_name)
    concept_map, promoted_concept_documents = resolve_source_concept_promotions(repo, source_name)
    unresolved_concepts: set[str] = set()

    promoted_claims = [
        rewrite_claim_concept_refs(claim.to_payload(), concept_map, unresolved=unresolved_concepts)
        for claim in (() if claims_doc is None else claims_doc.claims)
    ]
    if unresolved_concepts:
        formatted = ", ".join(sorted(unresolved_concepts))
        raise ValueError(f"Cannot promote source {source_name!r}; unresolved concept mappings: {formatted}")

    resolver = ClaimReferenceResolver(
        source=load_source_claim_reference_index(repo, source_name),
        primary=load_primary_branch_claim_reference_index(repo),
    )

    promoted_stance_documents: dict[str, StanceFileDocument] = {}
    promoted_stances: list[dict[str, Any]] = []
    for stance in (() if stances_doc is None else stances_doc.stances):
        source_claim = stance.source_claim
        if not isinstance(source_claim, str) or not source_claim:
            raise ValueError("stance source_claim must be normalized before promotion")
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
    promoted_source_doc, promoted_claims_doc, promoted_justifications_doc, promoted_stances_doc = attach_source_artifact_codes(
        source_doc.to_payload(),
        promoted_claims_doc,
        None if justifications_doc is None else justifications_doc.to_payload(),
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
            normalized_claim = normalize_canonical_claim_payload(claim, strip_source_local=True)
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
        promoted_stance_documents[source_claim] = convert_document_value(
            {
                "source_claim": source_claim,
                "stances": entries,
            },
            StanceFileDocument,
            source=f"stances/{source_claim.replace(':', '__')}.yaml",
        )

    promoted_source_document = convert_document_value(
        promoted_source_doc,
        SourceDocument,
        source=f"sources/{slug}.yaml",
    )
    promoted_claims_document = convert_document_value(
        promoted_claims_doc,
        ClaimsFileDocument,
        source=f"claims/{slug}.yaml",
    )

    with repo.artifacts.transact(
        message=f"Promote source {slug}",
        branch=repo.snapshot.primary_branch_name(),
    ) as transaction:
        transaction.save(
            CANONICAL_SOURCE_FAMILY,
            CanonicalSourceRef(slug),
            promoted_source_document,
        )
        transaction.save(
            CLAIMS_FILE_FAMILY,
            ClaimsFileRef(slug),
            promoted_claims_document,
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
