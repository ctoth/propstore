from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from propstore.cli.repository import Repository
from propstore.identity import (
    compute_claim_version_id,
    derive_claim_artifact_id,
    format_logical_id,
    normalize_logical_value,
)

from .common import (
    commit_source_file,
    load_source_document,
    load_yaml_from_branch,
    normalize_source_slug,
    source_branch_name,
    source_tag_uri,
)


def stable_claim_logical_value(claim: dict[str, Any], *, source_uri: str) -> str:
    canonical = copy.deepcopy(claim)
    canonical.pop("id", None)
    canonical.pop("artifact_id", None)
    canonical.pop("version_id", None)
    canonical.pop("logical_ids", None)
    canonical.pop("source_local_id", None)
    payload = json.dumps(
        {"source_uri": source_uri, "claim": canonical},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"claim_{digest}"


def source_concept_handles(repo: Repository, source_name: str) -> set[str]:
    concepts_doc = load_yaml_from_branch(repo, source_branch_name(source_name), "concepts.yaml") or {}
    handles: set[str] = set()
    for entry in concepts_doc.get("concepts", []) or []:
        if not isinstance(entry, dict):
            continue
        for key in ("local_name", "proposed_name"):
            value = entry.get(key)
            if isinstance(value, str) and value:
                handles.add(value)
    return handles


def iter_claim_concept_refs(claim: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for field in ("concept", "target_concept"):
        value = claim.get(field)
        if isinstance(value, str):
            refs.append(value)
    concepts = claim.get("concepts")
    if isinstance(concepts, list):
        refs.extend(value for value in concepts if isinstance(value, str))
    variables = claim.get("variables")
    if isinstance(variables, list):
        for entry in variables:
            if isinstance(entry, dict):
                value = entry.get("concept")
                if isinstance(value, str):
                    refs.append(value)
    parameters = claim.get("parameters")
    if isinstance(parameters, list):
        for entry in parameters:
            if isinstance(entry, dict):
                value = entry.get("concept")
                if isinstance(value, str):
                    refs.append(value)
    return refs


def validate_source_claim_concepts(repo: Repository, source_name: str, data: dict[str, Any]) -> None:
    known_handles = source_concept_handles(repo, source_name)
    unknown: set[str] = set()
    for claim in data.get("claims", []) or []:
        if not isinstance(claim, dict):
            continue
        for concept_ref in iter_claim_concept_refs(claim):
            if concept_ref.startswith("ps:concept:") or concept_ref.startswith("tag:"):
                continue
            if concept_ref not in known_handles:
                unknown.add(concept_ref)
    if unknown:
        formatted = ", ".join(sorted(unknown))
        raise ValueError(f"unknown concept reference(s): {formatted}")


def normalize_source_claims_payload(
    data: dict[str, Any],
    *,
    source_uri: str,
    source_namespace: str,
) -> tuple[dict[str, Any], dict[str, str]]:
    normalized_data = dict(data)
    normalized_claims: list[Any] = []
    local_to_canonical: dict[str, str] = {}
    namespace = normalize_source_slug(source_namespace)

    for claim in list(normalized_data.get("claims", [])):
        if not isinstance(claim, dict):
            normalized_claims.append(claim)
            continue
        normalized = copy.deepcopy(claim)
        raw_id = normalized.get("id")
        stable_value = stable_claim_logical_value(normalized, source_uri=source_uri)
        normalized["id"] = stable_value
        logical_ids = [{"namespace": namespace, "value": stable_value}]
        if isinstance(raw_id, str) and raw_id:
            normalized["source_local_id"] = raw_id
            local_to_canonical[raw_id] = stable_value
            local_value = normalize_logical_value(raw_id)
            if local_value != stable_value:
                logical_ids.append({"namespace": namespace, "value": local_value})
        normalized["logical_ids"] = logical_ids
        normalized["artifact_id"] = derive_claim_artifact_id(namespace, stable_value)
        normalized["version_id"] = compute_claim_version_id(normalized)
        normalized_claims.append(normalized)

    normalized_data["claims"] = normalized_claims
    return normalized_data, local_to_canonical


def load_source_claim_index(repo: Repository, source_name: str) -> tuple[dict[str, str], dict[str, str], set[str]]:
    claims_doc = load_yaml_from_branch(repo, source_branch_name(source_name), "claims.yaml") or {}
    local_to_artifact: dict[str, str] = {}
    logical_to_artifact: dict[str, str] = {}
    artifact_ids: set[str] = set()
    for claim in claims_doc.get("claims", []) or []:
        if not isinstance(claim, dict):
            continue
        artifact_id = claim.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id:
            continue
        artifact_ids.add(artifact_id)
        local_id = claim.get("source_local_id")
        if isinstance(local_id, str) and local_id:
            local_to_artifact[local_id] = artifact_id
        for logical_id in claim.get("logical_ids") or []:
            if not isinstance(logical_id, dict):
                continue
            formatted = format_logical_id(logical_id)
            if formatted:
                logical_to_artifact[formatted] = artifact_id
    return local_to_artifact, logical_to_artifact, artifact_ids


def load_primary_branch_claim_index(repo: Repository) -> tuple[dict[str, str], set[str]]:
    from propstore.validate_claims import load_claim_files

    primary_tip = repo.git.branch_sha(repo.git.primary_branch_name())
    if primary_tip is None:
        return {}, set()

    tree = repo.tree(commit=primary_tip)
    claims_root = tree / "claims"
    if not claims_root.exists():
        return {}, set()

    logical_to_artifact: dict[str, str] = {}
    artifact_ids: set[str] = set()
    for claim_file in load_claim_files(claims_root):
        for claim in claim_file.data.get("claims", []) or []:
            if not isinstance(claim, dict):
                continue
            artifact_id = claim.get("artifact_id")
            if not isinstance(artifact_id, str) or not artifact_id:
                continue
            artifact_ids.add(artifact_id)
            for logical_id in claim.get("logical_ids") or []:
                if not isinstance(logical_id, dict):
                    continue
                formatted = format_logical_id(logical_id)
                if formatted:
                    logical_to_artifact[formatted] = artifact_id
    return logical_to_artifact, artifact_ids


def commit_source_claims_batch(repo: Repository, source_name: str, claims_file: Path) -> str:
    source_doc = load_source_document(repo, source_name)
    raw = yaml.safe_load(claims_file.read_text(encoding="utf-8")) or {}
    validate_source_claim_concepts(repo, source_name, raw)
    normalized, _ = normalize_source_claims_payload(
        raw,
        source_uri=str(source_doc.get("id") or source_tag_uri(repo, source_name)),
        source_namespace=normalize_source_slug(source_name),
    )
    return commit_source_file(
        repo,
        source_name,
        relpath="claims.yaml",
        content=yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True).encode("utf-8"),
        message=f"Write claims for {normalize_source_slug(source_name)}",
    )


def commit_source_claim_proposal(
    repo: Repository,
    source_name: str,
    *,
    claim_id: str,
    claim_type: str,
    statement: str | None = None,
    concept: str | None = None,
    value: float | None = None,
    unit: str | None = None,
    page: int | None = None,
) -> dict[str, Any]:
    branch = source_branch_name(source_name)
    source_doc = load_source_document(repo, source_name)
    existing = load_yaml_from_branch(repo, branch, "claims.yaml") or {"claims": []}
    claims = list(existing.get("claims", []) or [])

    norm_keys = {"source_local_id", "logical_ids", "artifact_id", "version_id"}
    restored: list[dict[str, Any]] = []
    for claim in claims:
        if not isinstance(claim, dict):
            restored.append(claim)
            continue
        if claim.get("source_local_id") == claim_id or claim.get("id") == claim_id:
            continue
        restored_claim = {key: value for key, value in claim.items() if key not in norm_keys}
        local_id = claim.get("source_local_id")
        if local_id:
            restored_claim["id"] = local_id
        restored.append(restored_claim)
    claims = restored

    claim: dict[str, Any] = {"id": claim_id, "type": claim_type}
    if statement is not None:
        claim["statement"] = statement
    if concept is not None:
        claim["concept"] = concept
    if value is not None:
        claim["value"] = value
    if unit is not None:
        claim["unit"] = unit
    if page is not None:
        claim["provenance"] = {"page": page}

    claims.append(claim)
    data: dict[str, Any] = dict(existing)
    data["claims"] = claims

    normalized, _ = normalize_source_claims_payload(
        data,
        source_uri=str(source_doc.get("id") or source_tag_uri(repo, source_name)),
        source_namespace=normalize_source_slug(source_name),
    )

    commit_source_file(
        repo,
        source_name,
        relpath="claims.yaml",
        content=yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True).encode("utf-8"),
        message=f"Propose claim for {normalize_source_slug(source_name)}",
    )

    for entry in normalized.get("claims", []):
        if isinstance(entry, dict) and entry.get("source_local_id") == claim_id:
            return entry
    return normalized["claims"][-1]
