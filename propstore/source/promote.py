from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from propstore.artifact_codes import attach_source_artifact_codes
from propstore.cli.repository import Repository
from propstore.identity import compute_claim_version_id, compute_concept_version_id, derive_concept_artifact_id

from .claims import load_primary_branch_claim_index, load_source_claim_index
from .common import load_branch_yaml, load_source_document, normalize_source_slug, source_branch_name
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
    normalized["version_id"] = compute_claim_version_id(normalized)
    return normalized


def resolve_source_concept_promotions(repo: Repository, source_name: str) -> tuple[dict[str, str], dict[str, bytes]]:
    concepts_doc = load_branch_yaml(repo, source_name, "concepts.yaml") or {}
    concepts_by_artifact, handle_to_artifact = load_primary_branch_concepts(repo)
    mapping: dict[str, str] = {}
    concept_adds: dict[str, bytes] = {}
    new_concepts: list[tuple[dict[str, Any], str, str]] = []
    seen_new_artifacts: dict[str, str] = {}

    for entry in concepts_doc.get("concepts", []) or []:
        if not isinstance(entry, dict):
            continue
        registry_match = entry.get("registry_match")
        if isinstance(registry_match, dict):
            artifact_id = registry_match.get("artifact_id")
            if isinstance(artifact_id, str) and artifact_id:
                for key in ("local_name", "proposed_name"):
                    handle = entry.get(key)
                    if isinstance(handle, str) and handle:
                        mapping[handle] = artifact_id
                continue
        matched_artifact_id: str | None = None
        for key in ("local_name", "proposed_name"):
            handle = entry.get(key)
            if isinstance(handle, str) and handle in handle_to_artifact:
                matched_artifact_id = handle_to_artifact[handle]
                mapping[handle] = matched_artifact_id
        if matched_artifact_id is not None:
            continue

        handle_seed = str(entry.get("proposed_name") or entry.get("local_name") or "concept").strip()
        slug = normalize_source_slug(handle_seed)
        artifact_id = derive_concept_artifact_id("propstore", slug)
        existing = concepts_by_artifact.get(artifact_id)
        if existing is not None:
            raise ValueError(f"Cannot promote source {source_name!r}; ambiguous concept mappings: {handle_seed}")
        prior_handle = seen_new_artifacts.get(artifact_id)
        if prior_handle is not None and prior_handle != handle_seed:
            raise ValueError(
                f"Cannot promote source {source_name!r}; ambiguous concept mappings: {handle_seed}, {prior_handle}"
            )
        seen_new_artifacts[artifact_id] = handle_seed
        new_concepts.append((copy.deepcopy(entry), artifact_id, slug))
        for key in ("local_name", "proposed_name"):
            handle = entry.get(key)
            if isinstance(handle, str) and handle:
                mapping[handle] = artifact_id

    for raw_entry, artifact_id, slug in new_concepts:
        parameterization_relationships: list[dict[str, Any]] = []
        for relationship in raw_entry.get("parameterization_relationships", []) or []:
            if not isinstance(relationship, dict):
                continue
            normalized_relationship = copy.deepcopy(relationship)
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
            "canonical_name": str(raw_entry.get("proposed_name") or raw_entry.get("local_name") or slug).strip(),
            "status": "accepted",
            "definition": str(raw_entry.get("definition") or "").strip(),
            "domain": "source",
            "form": str(raw_entry.get("form") or "structural").strip(),
            "artifact_id": artifact_id,
            "logical_ids": [
                {"namespace": "source", "value": slug},
                {"namespace": "propstore", "value": slug},
            ],
        }
        aliases = raw_entry.get("aliases")
        if isinstance(aliases, list) and aliases:
            concept_doc["aliases"] = copy.deepcopy(aliases)
        if parameterization_relationships:
            concept_doc["parameterization_relationships"] = parameterization_relationships
        concept_doc["version_id"] = compute_concept_version_id(concept_doc)
        concept_adds[f"concepts/{slug}.yaml"] = yaml.safe_dump(
            concept_doc,
            sort_keys=False,
            allow_unicode=True,
        ).encode("utf-8")

    return mapping, concept_adds


def load_finalize_report(repo: Repository, source_name: str) -> dict[str, Any] | None:
    return load_branch_yaml(repo, source_name, f"merge/finalize/{normalize_source_slug(source_name)}.yaml")


def promote_source_branch(repo: Repository, source_name: str) -> str:
    report = load_finalize_report(repo, source_name)
    if not isinstance(report, dict) or report.get("status") != "ready":
        raise ValueError(f"Source {source_name!r} must be finalized successfully before promotion")

    slug = normalize_source_slug(source_name)
    source_doc = load_source_document(repo, source_name)
    claims_doc = load_branch_yaml(repo, source_name, "claims.yaml") or {}
    justifications_doc = load_branch_yaml(repo, source_name, "justifications.yaml") or {}
    stances_doc = load_branch_yaml(repo, source_name, "stances.yaml") or {}
    concept_map, promoted_concept_files = resolve_source_concept_promotions(repo, source_name)
    unresolved_concepts: set[str] = set()

    promoted_claims = [
        rewrite_claim_concept_refs(claim, concept_map, unresolved=unresolved_concepts)
        if isinstance(claim, dict)
        else claim
        for claim in claims_doc.get("claims", []) or []
    ]
    if unresolved_concepts:
        formatted = ", ".join(sorted(unresolved_concepts))
        raise ValueError(f"Cannot promote source {source_name!r}; unresolved concept mappings: {formatted}")

    local_to_artifact, logical_to_artifact, _local_artifact_ids = load_source_claim_index(repo, source_name)
    primary_logical_to_artifact, primary_artifact_ids = load_primary_branch_claim_index(repo)

    promoted_stance_files: dict[str, bytes] = {}
    promoted_stances: list[dict[str, Any]] = []
    for stance in stances_doc.get("stances", []) or []:
        if not isinstance(stance, dict):
            continue
        source_claim = stance.get("source_claim")
        if not isinstance(source_claim, str) or not source_claim:
            raise ValueError("stance source_claim must be normalized before promotion")
        target = stance.get("target")
        if not isinstance(target, str) or not target:
            raise ValueError("stance target must be a non-empty string")
        if target in local_to_artifact:
            target = local_to_artifact[target]
        elif target in logical_to_artifact:
            target = logical_to_artifact[target]
        elif target in primary_logical_to_artifact:
            target = primary_logical_to_artifact[target]
        elif target not in primary_artifact_ids and not target.startswith("ps:claim:"):
            raise ValueError(f"Unresolved promoted stance target: {target}")
        normalized = copy.deepcopy(stance)
        normalized["target"] = target
        promoted_stances.append(normalized)

    promoted_claims_doc = {
        "source": claims_doc.get("source") or {"paper": slug},
        "claims": promoted_claims,
    }
    source_doc, promoted_claims_doc, justifications_doc, promoted_stances_doc = attach_source_artifact_codes(
        source_doc,
        promoted_claims_doc,
        justifications_doc,
        {"stances": promoted_stances},
    )
    promoted_claims = promoted_claims_doc.get("claims", []) or []

    source_only_fields = {"id", "source_local_id", "artifact_code"}
    for claim in promoted_claims:
        if isinstance(claim, dict):
            for field in source_only_fields:
                claim.pop(field, None)
            claim["version_id"] = compute_claim_version_id(claim)
    promoted_claims_doc["claims"] = promoted_claims

    stances_by_source: dict[str, list[dict[str, Any]]] = {}
    for stance in promoted_stances_doc.get("stances", []) or []:
        if not isinstance(stance, dict):
            continue
        source_claim = stance.get("source_claim")
        if isinstance(source_claim, str) and source_claim:
            stances_by_source.setdefault(source_claim, []).append(stance)

    for source_claim, entries in stances_by_source.items():
        file_name = source_claim.replace(":", "__") + ".yaml"
        payload = {
            "source_claim": source_claim,
            "stances": entries,
        }
        promoted_stance_files[f"stances/{file_name}"] = yaml.safe_dump(
            payload,
            sort_keys=False,
            allow_unicode=True,
        ).encode("utf-8")

    adds = {
        f"sources/{slug}.yaml": yaml.safe_dump(source_doc, sort_keys=False, allow_unicode=True).encode("utf-8"),
        f"claims/{slug}.yaml": yaml.safe_dump(promoted_claims_doc, sort_keys=False, allow_unicode=True).encode(
            "utf-8"
        ),
    }
    adds.update(promoted_concept_files)

    if justifications_doc.get("justifications"):
        adds[f"justifications/{slug}.yaml"] = yaml.safe_dump(
            justifications_doc,
            sort_keys=False,
            allow_unicode=True,
        ).encode("utf-8")
    adds.update(promoted_stance_files)

    sha = repo.git.commit_batch(
        adds=adds,
        deletes=[],
        message=f"Promote source {slug}",
        branch=repo.git.primary_branch_name(),
    )
    repo.git.sync_worktree()
    return sha


def sync_source_branch(
    repo: Repository,
    source_name: str,
    *,
    output_dir: Path | None = None,
) -> Path:
    branch = source_branch_name(source_name)
    tip = repo.git.branch_sha(branch)
    if tip is None:
        raise ValueError(f"Source branch {branch!r} does not exist")

    destination = output_dir
    if destination is None:
        papers_root = repo.root.parent / "papers"
        destination = papers_root / normalize_source_slug(source_name)
    destination.mkdir(parents=True, exist_ok=True)

    def copy_tree(relpath: str = "") -> None:
        for child_name, is_dir in repo.git.list_dir_entries(relpath, commit=tip):
            child_relpath = f"{relpath}/{child_name}" if relpath else child_name
            target = destination / Path(*child_relpath.split("/"))
            if is_dir:
                target.mkdir(parents=True, exist_ok=True)
                copy_tree(child_relpath)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(repo.git.read_file(child_relpath, commit=tip))

    copy_tree("")
    return destination
