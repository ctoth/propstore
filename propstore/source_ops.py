"""Git-backed source branch helpers."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from propstore.artifact_codes import attach_source_artifact_codes
from propstore.cli.repository import Repository
from propstore.identity import (
    compute_claim_version_id,
    compute_concept_version_id,
    derive_concept_artifact_id,
    derive_claim_artifact_id,
    format_logical_id,
    normalize_logical_value,
)
from propstore.parameterization_groups import build_groups
from propstore.repo.branch import branch_head, create_branch
from propstore.source_calibration import derive_source_trust
from propstore.uri import ni_uri_for_file, source_tag_uri as mint_source_tag_uri


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_slug(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in name.strip())
    cleaned = cleaned.strip("._-")
    return cleaned or "source"


def source_branch_name(name: str) -> str:
    return f"source/{_normalize_slug(name)}"


def source_tag_uri(repo: Repository, name: str) -> str:
    return mint_source_tag_uri(name, authority=repo.uri_authority)


def initial_source_document(
    repo: Repository,
    name: str,
    *,
    kind: str,
    origin_type: str,
    origin_value: str,
    content_file: Path | None = None,
) -> dict[str, Any]:
    return {
        "id": source_tag_uri(repo, name),
        "kind": kind,
        "origin": {
            "type": origin_type,
            "value": origin_value,
            "retrieved": _utc_now(),
            "content_ref": ni_uri_for_file(content_file) if content_file is not None else None,
        },
        "trust": {
            "prior_base_rate": 0.5,
            "quality": {
                "b": 0.0,
                "d": 0.0,
                "u": 1.0,
                "a": 0.5,
            },
            "derived_from": [],
        },
        "metadata": {
            "name": _normalize_slug(name),
        },
    }


def _write_yaml(repo: Repository, *, branch: str, relpath: str, data: dict[str, Any], message: str) -> str:
    payload = yaml.safe_dump(data, sort_keys=False, allow_unicode=True).encode("utf-8")
    return repo.git.commit_batch(adds={relpath: payload}, deletes=[], message=message, branch=branch)


def _load_yaml_from_branch(repo: Repository, branch: str, relpath: str) -> dict[str, Any] | None:
    tip = branch_head(repo.git, branch)
    if tip is None:
        return None
    try:
        return yaml.safe_load(repo.git.read_file(relpath, commit=tip)) or {}
    except FileNotFoundError:
        return None


def _load_master_concepts(repo: Repository) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    from propstore.validate import load_concepts

    master_tip = branch_head(repo.git, repo.git.primary_branch_name())
    if master_tip is None:
        return {}, {}

    tree = repo.tree(commit=master_tip)
    concepts_root = tree / "concepts"
    if not concepts_root.exists():
        return {}, {}

    concepts_by_artifact: dict[str, dict[str, Any]] = {}
    handle_to_artifact: dict[str, str] = {}
    for entry in load_concepts(concepts_root):
        concept = dict(entry.data)
        artifact_id = concept.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id:
            continue
        concepts_by_artifact[artifact_id] = concept
        canonical_name = concept.get("canonical_name")
        if isinstance(canonical_name, str) and canonical_name:
            handle_to_artifact[canonical_name] = artifact_id
        for alias in concept.get("aliases") or []:
            if not isinstance(alias, dict):
                continue
            alias_name = alias.get("name")
            if isinstance(alias_name, str) and alias_name:
                handle_to_artifact.setdefault(alias_name, artifact_id)
    return concepts_by_artifact, handle_to_artifact


def _load_master_concept_docs(repo: Repository) -> list[dict[str, Any]]:
    from propstore.validate import load_concepts

    master_tip = branch_head(repo.git, repo.git.primary_branch_name())
    if master_tip is None:
        return []

    tree = repo.tree(commit=master_tip)
    concepts_root = tree / "concepts"
    if not concepts_root.exists():
        return []

    docs: list[dict[str, Any]] = []
    for entry in load_concepts(concepts_root):
        if isinstance(entry.data, dict):
            docs.append(copy.deepcopy(entry.data))
    return docs


def _master_concept_match(repo: Repository, handle: str) -> dict[str, str] | None:
    concepts_by_artifact, handle_to_artifact = _load_master_concepts(repo)
    artifact_id = handle_to_artifact.get(handle)
    if artifact_id is None:
        return None
    concept = concepts_by_artifact[artifact_id]
    canonical_name = concept.get("canonical_name")
    if not isinstance(canonical_name, str) or not canonical_name:
        return None
    return {
        "artifact_id": artifact_id,
        "canonical_name": canonical_name,
    }


def _projected_source_concepts(
    repo: Repository,
    concepts_doc: dict[str, Any],
) -> tuple[list[dict[str, Any]], set[str]]:
    _concepts_by_artifact, master_handle_to_artifact = _load_master_concepts(repo)
    projected: list[dict[str, Any]] = []
    local_handle_to_artifact: dict[str, str] = {}
    parameterized_artifacts: set[str] = set()

    for entry in concepts_doc.get("concepts", []) or []:
        if not isinstance(entry, dict):
            continue
        registry_match = entry.get("registry_match")
        artifact_id: str | None = None
        if isinstance(registry_match, dict):
            matched = registry_match.get("artifact_id")
            if isinstance(matched, str) and matched:
                artifact_id = matched
        if artifact_id is None:
            for key in ("local_name", "proposed_name"):
                handle = entry.get(key)
                if isinstance(handle, str) and handle in master_handle_to_artifact:
                    artifact_id = master_handle_to_artifact[handle]
                    break
        handle_seed = str(entry.get("proposed_name") or entry.get("local_name") or "concept")
        if artifact_id is None:
            artifact_id = derive_concept_artifact_id("propstore", _normalize_slug(handle_seed))

        projected_entry = {
            "artifact_id": artifact_id,
            "canonical_name": handle_seed,
            "form": str(entry.get("form") or "structural"),
            "parameterization_relationships": [],
        }
        projected.append(projected_entry)
        for key in ("local_name", "proposed_name"):
            handle = entry.get(key)
            if isinstance(handle, str) and handle:
                local_handle_to_artifact[handle] = artifact_id

    for projected_entry, raw_entry in zip(projected, concepts_doc.get("concepts", []) or [], strict=False):
        if not isinstance(raw_entry, dict):
            continue
        params: list[dict[str, Any]] = []
        for param in raw_entry.get("parameterization_relationships", []) or []:
            if not isinstance(param, dict):
                continue
            resolved = copy.deepcopy(param)
            inputs: list[str] = []
            for input_ref in resolved.get("inputs", []) or []:
                if not isinstance(input_ref, str) or not input_ref:
                    continue
                if input_ref.startswith("ps:concept:") or input_ref.startswith("tag:"):
                    inputs.append(input_ref)
                    continue
                artifact_id = local_handle_to_artifact.get(input_ref) or master_handle_to_artifact.get(input_ref)
                if artifact_id is None:
                    artifact_id = derive_concept_artifact_id("propstore", _normalize_slug(input_ref))
                inputs.append(artifact_id)
            resolved["inputs"] = inputs
            params.append(resolved)
        projected_entry["parameterization_relationships"] = params
        if params:
            parameterized_artifacts.add(str(projected_entry["artifact_id"]))

    return projected, parameterized_artifacts


def _parameterization_group_merge_preview(
    master_concepts: list[dict[str, Any]],
    projected_concepts: list[dict[str, Any]],
    *,
    parameterized_artifacts: set[str],
) -> list[dict[str, Any]]:
    master_by_artifact: dict[str, dict[str, Any]] = {}
    master_ids: set[str] = set()
    for concept in master_concepts:
        if not isinstance(concept, dict):
            continue
        artifact_id = concept.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id:
            continue
        master_by_artifact[artifact_id] = copy.deepcopy(concept)
        master_ids.add(artifact_id)

    preview_by_artifact = {artifact_id: copy.deepcopy(doc) for artifact_id, doc in master_by_artifact.items()}
    for concept in projected_concepts:
        if not isinstance(concept, dict):
            continue
        artifact_id = concept.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id:
            continue
        if artifact_id in preview_by_artifact:
            merged = copy.deepcopy(preview_by_artifact[artifact_id])
            existing_params = list(merged.get("parameterization_relationships", []) or [])
            for param in concept.get("parameterization_relationships", []) or []:
                if param not in existing_params:
                    existing_params.append(copy.deepcopy(param))
            merged["parameterization_relationships"] = existing_params
            preview_by_artifact[artifact_id] = merged
        else:
            preview_by_artifact[artifact_id] = copy.deepcopy(concept)

    previous_groups = build_groups(list(master_by_artifact.values()))
    preview_groups = build_groups(list(preview_by_artifact.values()))
    previous_lookup: dict[str, frozenset[str]] = {}
    for group in previous_groups:
        frozen = frozenset(group)
        for member in group:
            previous_lookup[member] = frozen

    merges: list[dict[str, Any]] = []
    for group in sorted(preview_groups, key=lambda members: tuple(sorted(members))):
        existing_members = sorted(member for member in group if member in master_ids)
        collapsed = {
            previous_lookup.get(member, frozenset({member}))
            for member in existing_members
        }
        if len(collapsed) < 2:
            continue
        merges.append(
            {
                "merged_group": sorted(group),
                "previous_groups": [
                    sorted(previous_group)
                    for previous_group in sorted(collapsed, key=lambda members: tuple(sorted(members)))
                ],
                "introduced_by": sorted(member for member in group if member in parameterized_artifacts),
            }
        )
    return merges


def _preview_source_parameterization_group_merges(
    repo: Repository,
    concepts_doc: dict[str, Any],
) -> list[dict[str, Any]]:
    master_concepts = _load_master_concept_docs(repo)
    projected_concepts, parameterized_artifacts = _projected_source_concepts(repo, concepts_doc)
    return _parameterization_group_merge_preview(
        master_concepts,
        projected_concepts,
        parameterized_artifacts=parameterized_artifacts,
    )


def init_source_branch(
    repo: Repository,
    name: str,
    *,
    kind: str,
    origin_type: str,
    origin_value: str,
    content_file: Path | None = None,
) -> str:
    if repo.git is None:
        raise ValueError("source operations require a git-backed repository")
    branch = source_branch_name(name)
    if branch_head(repo.git, branch) is None:
        create_branch(repo.git, branch)
    source_doc = initial_source_document(
        repo,
        name,
        kind=kind,
        origin_type=origin_type,
        origin_value=origin_value,
        content_file=content_file,
    )
    _write_yaml(
        repo,
        branch=branch,
        relpath="source.yaml",
        data=source_doc,
        message=f"Initialize source {_normalize_slug(name)}",
    )
    return branch


def commit_source_file(
    repo: Repository,
    name: str,
    *,
    relpath: str,
    content: bytes,
    message: str,
) -> str:
    if repo.git is None:
        raise ValueError("source operations require a git-backed repository")
    branch = source_branch_name(name)
    if branch_head(repo.git, branch) is None:
        raise ValueError(f"Source branch {branch!r} does not exist")
    return repo.git.commit_batch(adds={relpath: content}, deletes=[], message=message, branch=branch)


def commit_source_notes(repo: Repository, name: str, notes_file: Path) -> str:
    return commit_source_file(
        repo,
        name,
        relpath="notes.md",
        content=notes_file.read_bytes(),
        message=f"Write notes for {_normalize_slug(name)}",
    )


def commit_source_metadata(repo: Repository, name: str, metadata_file: Path) -> str:
    loaded = json.loads(metadata_file.read_text(encoding="utf-8"))
    payload = json.dumps(loaded, indent=2, ensure_ascii=False).encode("utf-8")
    return commit_source_file(
        repo,
        name,
        relpath="metadata.json",
        content=payload,
        message=f"Write metadata for {_normalize_slug(name)}",
    )


def load_source_document(repo: Repository, name: str) -> dict[str, Any]:
    branch = source_branch_name(name)
    tip = branch_head(repo.git, branch)
    if tip is None:
        raise ValueError(f"Source branch {branch!r} does not exist")
    return yaml.safe_load(repo.git.read_file("source.yaml", commit=tip)) or {}


def _stable_claim_logical_value(claim: dict[str, Any], *, source_uri: str) -> str:
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


def _source_concept_handles(repo: Repository, name: str) -> set[str]:
    concepts_doc = _load_yaml_from_branch(repo, source_branch_name(name), "concepts.yaml") or {}
    handles: set[str] = set()
    for entry in concepts_doc.get("concepts", []) or []:
        if not isinstance(entry, dict):
            continue
        for key in ("local_name", "proposed_name"):
            value = entry.get(key)
            if isinstance(value, str) and value:
                handles.add(value)
    return handles


def _iter_claim_concept_refs(claim: dict[str, Any]) -> list[str]:
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


def _validate_source_claim_concepts(repo: Repository, name: str, data: dict[str, Any]) -> None:
    known_handles = _source_concept_handles(repo, name)
    unknown: set[str] = set()
    for claim in data.get("claims", []) or []:
        if not isinstance(claim, dict):
            continue
        for concept_ref in _iter_claim_concept_refs(claim):
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
    namespace = _normalize_slug(source_namespace)

    for claim in list(normalized_data.get("claims", [])):
        if not isinstance(claim, dict):
            normalized_claims.append(claim)
            continue
        normalized = copy.deepcopy(claim)
        raw_id = normalized.get("id")
        stable_value = _stable_claim_logical_value(normalized, source_uri=source_uri)
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


def _load_source_claim_index(repo: Repository, name: str) -> tuple[dict[str, str], dict[str, str], set[str]]:
    claims_doc = _load_yaml_from_branch(repo, source_branch_name(name), "claims.yaml") or {}
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


def _load_master_claim_index(repo: Repository) -> tuple[dict[str, str], set[str]]:
    from propstore.validate_claims import load_claim_files

    master_tip = branch_head(repo.git, repo.git.primary_branch_name())
    if master_tip is None:
        return {}, set()

    tree = repo.tree(commit=master_tip)
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


def commit_source_claims_batch(repo: Repository, name: str, claims_file: Path) -> str:
    source_doc = load_source_document(repo, name)
    raw = yaml.safe_load(claims_file.read_text(encoding="utf-8")) or {}
    _validate_source_claim_concepts(repo, name, raw)
    normalized, _ = normalize_source_claims_payload(
        raw,
        source_uri=str(source_doc.get("id") or source_tag_uri(repo, name)),
        source_namespace=_normalize_slug(name),
    )
    return commit_source_file(
        repo,
        name,
        relpath="claims.yaml",
        content=yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True).encode("utf-8"),
        message=f"Write claims for {_normalize_slug(name)}",
    )


def _resolve_local_claim_reference(reference: object, local_to_artifact: dict[str, str]) -> str:
    if not isinstance(reference, str) or not reference:
        raise ValueError("claim reference must be a non-empty string")
    if reference.startswith("ps:claim:"):
        return reference
    artifact_id = local_to_artifact.get(reference)
    if artifact_id is None:
        raise ValueError(f"unresolved local claim reference: {reference}")
    return artifact_id


def normalize_source_justifications_payload(
    data: dict[str, Any],
    *,
    local_to_artifact: dict[str, str],
) -> dict[str, Any]:
    normalized_data = dict(data)
    normalized_justifications: list[Any] = []
    for justification in data.get("justifications", []) or []:
        if not isinstance(justification, dict):
            normalized_justifications.append(justification)
            continue
        normalized = copy.deepcopy(justification)
        normalized["conclusion"] = _resolve_local_claim_reference(
            normalized.get("conclusion"),
            local_to_artifact,
        )
        premises = normalized.get("premises") or []
        if not isinstance(premises, list):
            raise ValueError("justification premises must be a list")
        normalized["premises"] = [
            _resolve_local_claim_reference(premise, local_to_artifact)
            for premise in premises
        ]
        attack_target = normalized.get("attack_target")
        if isinstance(attack_target, dict) and isinstance(attack_target.get("target_claim"), str):
            updated_target = dict(attack_target)
            updated_target["target_claim"] = _resolve_local_claim_reference(
                updated_target["target_claim"],
                local_to_artifact,
            )
            normalized["attack_target"] = updated_target
        normalized_justifications.append(normalized)
    normalized_data["justifications"] = normalized_justifications
    return normalized_data


def commit_source_justifications_batch(repo: Repository, name: str, justifications_file: Path) -> str:
    local_to_artifact, _logical_to_artifact, _artifact_ids = _load_source_claim_index(repo, name)
    normalized = normalize_source_justifications_payload(
        yaml.safe_load(justifications_file.read_text(encoding="utf-8")) or {},
        local_to_artifact=local_to_artifact,
    )
    return commit_source_file(
        repo,
        name,
        relpath="justifications.yaml",
        content=yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True).encode("utf-8"),
        message=f"Write justifications for {_normalize_slug(name)}",
    )


def normalize_source_stances_payload(
    data: dict[str, Any],
    *,
    local_to_artifact: dict[str, str],
) -> dict[str, Any]:
    normalized_data = dict(data)
    normalized_stances: list[Any] = []
    for stance in data.get("stances", []) or []:
        if not isinstance(stance, dict):
            normalized_stances.append(stance)
            continue
        normalized = copy.deepcopy(stance)
        normalized["source_claim"] = _resolve_local_claim_reference(
            normalized.get("source_claim"),
            local_to_artifact,
        )
        target = normalized.get("target")
        if isinstance(target, str) and target in local_to_artifact:
            normalized["target"] = local_to_artifact[target]
        normalized_stances.append(normalized)
    normalized_data["stances"] = normalized_stances
    return normalized_data


def commit_source_stances_batch(repo: Repository, name: str, stances_file: Path) -> str:
    local_to_artifact, _logical_to_artifact, _artifact_ids = _load_source_claim_index(repo, name)
    normalized = normalize_source_stances_payload(
        yaml.safe_load(stances_file.read_text(encoding="utf-8")) or {},
        local_to_artifact=local_to_artifact,
    )
    return commit_source_file(
        repo,
        name,
        relpath="stances.yaml",
        content=yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True).encode("utf-8"),
        message=f"Write stances for {_normalize_slug(name)}",
    )


def commit_source_claim_proposal(
    repo: Repository,
    name: str,
    *,
    claim_id: str,
    claim_type: str,
    statement: str | None = None,
    concept: str | None = None,
    value: float | None = None,
    unit: str | None = None,
    page: int | None = None,
) -> dict[str, Any]:
    """Propose a single claim on a source branch.

    Returns the normalized claim entry (with artifact_id).
    """
    branch = source_branch_name(name)
    source_doc = load_source_document(repo, name)
    existing = _load_yaml_from_branch(repo, branch, "claims.yaml") or {"claims": []}
    claims = list(existing.get("claims", []) or [])

    # Restore existing claims to pre-normalized form so re-normalization
    # produces consistent content hashes.
    _NORM_KEYS = {"source_local_id", "logical_ids", "artifact_id", "version_id"}
    restored: list[dict[str, Any]] = []
    for c in claims:
        if not isinstance(c, dict):
            restored.append(c)
            continue
        # Skip the claim being replaced (dedup)
        if c.get("source_local_id") == claim_id or c.get("id") == claim_id:
            continue
        rc = {k: v for k, v in c.items() if k not in _NORM_KEYS}
        # Restore original local id
        local_id = c.get("source_local_id")
        if local_id:
            rc["id"] = local_id
        restored.append(rc)
    claims = restored

    # Build claim dict
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
        source_uri=str(source_doc.get("id") or source_tag_uri(repo, name)),
        source_namespace=_normalize_slug(name),
    )

    commit_source_file(
        repo,
        name,
        relpath="claims.yaml",
        content=yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True).encode("utf-8"),
        message=f"Propose claim for {_normalize_slug(name)}",
    )

    # Find the entry we just added
    for entry in normalized.get("claims", []):
        if isinstance(entry, dict) and entry.get("source_local_id") == claim_id:
            return entry
    # Fallback: return the last claim
    return normalized["claims"][-1]


def commit_source_justification_proposal(
    repo: Repository,
    name: str,
    *,
    just_id: str,
    conclusion: str,
    premises: list[str],
    rule_kind: str,
    page: int | None = None,
) -> dict[str, Any]:
    """Propose a single justification on a source branch.

    Returns the normalized justification entry.
    """
    branch = source_branch_name(name)
    local_to_artifact, _logical, _artifacts = _load_source_claim_index(repo, name)
    existing = _load_yaml_from_branch(repo, branch, "justifications.yaml") or {"justifications": []}
    justs = list(existing.get("justifications", []) or [])

    # Dedup by id
    justs = [j for j in justs if not (isinstance(j, dict) and j.get("id") == just_id)]

    # Build justification dict
    just: dict[str, Any] = {
        "id": just_id,
        "conclusion": conclusion,
        "premises": premises,
        "rule_kind": rule_kind,
    }
    if page is not None:
        just["provenance"] = {"page": page}

    justs.append(just)
    data: dict[str, Any] = dict(existing)
    data["justifications"] = justs

    normalized = normalize_source_justifications_payload(
        data,
        local_to_artifact=local_to_artifact,
    )

    commit_source_file(
        repo,
        name,
        relpath="justifications.yaml",
        content=yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True).encode("utf-8"),
        message=f"Propose justification for {_normalize_slug(name)}",
    )

    # Find the entry we just added
    for entry in normalized.get("justifications", []):
        if isinstance(entry, dict) and entry.get("id") == just_id:
            return entry
    return normalized["justifications"][-1]


def commit_source_stance_proposal(
    repo: Repository,
    name: str,
    *,
    source_claim: str,
    target: str,
    stance_type: str,
    strength: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """Propose a single stance on a source branch.

    Returns the normalized stance entry.
    """
    branch = source_branch_name(name)
    local_to_artifact, _logical, _artifacts = _load_source_claim_index(repo, name)
    existing = _load_yaml_from_branch(repo, branch, "stances.yaml") or {"stances": []}
    stances = list(existing.get("stances", []) or [])

    # Build stance dict (no dedup for stances per spec)
    stance: dict[str, Any] = {
        "source_claim": source_claim,
        "target": target,
        "type": stance_type,
    }
    if strength is not None:
        stance["strength"] = strength
    if note is not None:
        stance["note"] = note

    stances.append(stance)
    data: dict[str, Any] = dict(existing)
    data["stances"] = stances

    normalized = normalize_source_stances_payload(
        data,
        local_to_artifact=local_to_artifact,
    )

    commit_source_file(
        repo,
        name,
        relpath="stances.yaml",
        content=yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True).encode("utf-8"),
        message=f"Propose stance for {_normalize_slug(name)}",
    )

    # Return the last stance (the one we just added)
    return normalized["stances"][-1]


def _load_branch_yaml(repo: Repository, name: str, relpath: str) -> dict[str, Any] | None:
    return _load_yaml_from_branch(repo, source_branch_name(name), relpath)


def finalize_source_branch(repo: Repository, name: str) -> str:
    source_doc = derive_source_trust(repo, load_source_document(repo, name))
    claims_doc = _load_branch_yaml(repo, name, "claims.yaml") or {}
    justifications_doc = _load_branch_yaml(repo, name, "justifications.yaml") or {}
    stances_doc = _load_branch_yaml(repo, name, "stances.yaml") or {}
    concepts_doc = _load_branch_yaml(repo, name, "concepts.yaml") or {}

    local_to_artifact, logical_to_artifact, local_artifact_ids = _load_source_claim_index(repo, name)
    master_logical_to_artifact, master_artifact_ids = _load_master_claim_index(repo)

    claims = claims_doc.get("claims", []) if isinstance(claims_doc, dict) else []
    claim_errors: list[str] = []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        if not isinstance(claim.get("artifact_id"), str):
            claim_errors.append(str(claim.get("id") or "?"))

    justification_errors: list[str] = []
    for justification in justifications_doc.get("justifications", []) or []:
        if not isinstance(justification, dict):
            continue
        conclusion = justification.get("conclusion")
        if not isinstance(conclusion, str) or conclusion not in local_artifact_ids:
            justification_errors.append(str(conclusion))
        for premise in justification.get("premises") or []:
            if not isinstance(premise, str) or premise not in local_artifact_ids:
                justification_errors.append(str(premise))

    stance_errors: list[str] = []
    for stance in stances_doc.get("stances", []) or []:
        if not isinstance(stance, dict):
            continue
        source_claim = stance.get("source_claim")
        if not isinstance(source_claim, str) or source_claim not in local_artifact_ids:
            stance_errors.append(str(source_claim))
        target = stance.get("target")
        if not isinstance(target, str) or not target:
            stance_errors.append(str(target))
            continue
        if target in local_artifact_ids or target in master_artifact_ids:
            continue
        if target in logical_to_artifact or target in master_logical_to_artifact:
            continue
        stance_errors.append(target)

    concept_alignment_candidates = sorted(
        {
            f"align:{_normalize_slug(str(entry.get('proposed_name') or entry.get('local_name') or 'concept'))}"
            for entry in concepts_doc.get("concepts", []) or []
            if isinstance(entry, dict) and not isinstance(entry.get("registry_match"), dict)
        }
    )
    parameterization_group_merges = _preview_source_parameterization_group_merges(repo, concepts_doc)

    trust = source_doc.get("trust") if isinstance(source_doc.get("trust"), dict) else {}
    derived_from = trust.get("derived_from") if isinstance(trust.get("derived_from"), list) else []
    covered = bool(derived_from)
    artifact_code_status = "incomplete"
    adds: dict[str, bytes] = {}
    if not claim_errors and not justification_errors and not stance_errors:
        source_doc, claims_doc, justifications_doc, stances_doc = attach_source_artifact_codes(
            source_doc,
            claims_doc,
            justifications_doc,
            stances_doc,
        )
        adds["source.yaml"] = yaml.safe_dump(
            source_doc,
            sort_keys=False,
            allow_unicode=True,
        ).encode("utf-8")
        if claims_doc.get("claims"):
            adds["claims.yaml"] = yaml.safe_dump(
                claims_doc,
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8")
        if justifications_doc.get("justifications"):
            adds["justifications.yaml"] = yaml.safe_dump(
                justifications_doc,
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8")
        if stances_doc.get("stances"):
            adds["stances.yaml"] = yaml.safe_dump(
                stances_doc,
                sort_keys=False,
                allow_unicode=True,
            ).encode("utf-8")
        artifact_code_status = "complete"

    report = {
        "kind": "source_finalize_report",
        "source": str(source_doc.get("id") or source_tag_uri(repo, name)),
        "status": (
            "ready"
            if not claim_errors and not justification_errors and not stance_errors
            else "blocked"
        ),
        "claim_reference_errors": sorted(claim_errors),
        "justification_reference_errors": sorted(justification_errors),
        "stance_reference_errors": sorted(stance_errors),
        "concept_alignment_candidates": concept_alignment_candidates,
        "parameterization_group_merges": parameterization_group_merges,
        "artifact_code_status": artifact_code_status,
        "calibration": {
            "prior_base_rate_status": "covered" if covered else "fallback",
            "source_quality_status": "vacuous",
            "fallback_to_default_base_rate": not covered,
        },
    }
    adds[f"merge/finalize/{_normalize_slug(name)}.yaml"] = yaml.safe_dump(
        report,
        sort_keys=False,
        allow_unicode=True,
    ).encode("utf-8")
    return repo.git.commit_batch(
        adds=adds,
        deletes=[],
        message=f"Finalize {_normalize_slug(name)}",
        branch=source_branch_name(name),
    )


def _rewrite_claim_concept_refs(claim: dict[str, Any], concept_map: dict[str, str], *, unresolved: set[str]) -> dict[str, Any]:
    normalized = copy.deepcopy(claim)

    def _resolve(value: object) -> object:
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
            normalized[field] = _resolve(normalized.get(field))
    if isinstance(normalized.get("concepts"), list):
        normalized["concepts"] = [_resolve(value) for value in normalized["concepts"]]
    if isinstance(normalized.get("variables"), list):
        for variable in normalized["variables"]:
            if isinstance(variable, dict):
                variable["concept"] = _resolve(variable.get("concept"))
    if isinstance(normalized.get("parameters"), list):
        for parameter in normalized["parameters"]:
            if isinstance(parameter, dict):
                parameter["concept"] = _resolve(parameter.get("concept"))
    normalized["version_id"] = compute_claim_version_id(normalized)
    return normalized


def _resolve_source_concept_promotions(repo: Repository, name: str) -> tuple[dict[str, str], dict[str, bytes]]:
    concepts_doc = _load_branch_yaml(repo, name, "concepts.yaml") or {}
    concepts_by_artifact, handle_to_artifact = _load_master_concepts(repo)
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
        slug = _normalize_slug(handle_seed)
        artifact_id = derive_concept_artifact_id("propstore", slug)
        existing = concepts_by_artifact.get(artifact_id)
        if existing is not None:
            raise ValueError(
                f"Cannot promote source {name!r}; ambiguous concept mappings: {handle_seed}"
            )
        prior_handle = seen_new_artifacts.get(artifact_id)
        if prior_handle is not None and prior_handle != handle_seed:
            raise ValueError(
                f"Cannot promote source {name!r}; ambiguous concept mappings: {handle_seed}, {prior_handle}"
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
                        f"Cannot promote source {name!r}; unresolved parameterization concept: {input_ref}"
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


def _load_finalize_report(repo: Repository, name: str) -> dict[str, Any] | None:
    return _load_branch_yaml(repo, name, f"merge/finalize/{_normalize_slug(name)}.yaml")


def promote_source_branch(repo: Repository, name: str) -> str:
    report = _load_finalize_report(repo, name)
    if not isinstance(report, dict) or report.get("status") != "ready":
        raise ValueError(f"Source {name!r} must be finalized successfully before promotion")

    slug = _normalize_slug(name)
    source_doc = load_source_document(repo, name)
    claims_doc = _load_branch_yaml(repo, name, "claims.yaml") or {}
    justifications_doc = _load_branch_yaml(repo, name, "justifications.yaml") or {}
    stances_doc = _load_branch_yaml(repo, name, "stances.yaml") or {}
    concept_map, promoted_concept_files = _resolve_source_concept_promotions(repo, name)
    unresolved_concepts: set[str] = set()

    promoted_claims = [
        _rewrite_claim_concept_refs(claim, concept_map, unresolved=unresolved_concepts)
        if isinstance(claim, dict)
        else claim
        for claim in claims_doc.get("claims", []) or []
    ]
    if unresolved_concepts:
        formatted = ", ".join(sorted(unresolved_concepts))
        raise ValueError(f"Cannot promote source {name!r}; unresolved concept mappings: {formatted}")

    local_to_artifact, logical_to_artifact, _local_artifact_ids = _load_source_claim_index(repo, name)
    master_logical_to_artifact, master_artifact_ids = _load_master_claim_index(repo)

    promoted_stance_files: dict[str, bytes] = {}
    stances_by_source: dict[str, list[dict[str, Any]]] = {}
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
        elif target in master_logical_to_artifact:
            target = master_logical_to_artifact[target]
        elif target not in master_artifact_ids and not target.startswith("ps:claim:"):
            raise ValueError(f"Unresolved promoted stance target: {target}")
        normalized = copy.deepcopy(stance)
        normalized["target"] = target
        promoted_stances.append(normalized)
        stances_by_source.setdefault(source_claim, []).append(normalized)

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

    stances_by_source = {}
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
        f"claims/{slug}.yaml": yaml.safe_dump(promoted_claims_doc, sort_keys=False, allow_unicode=True).encode("utf-8"),
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
    name: str,
    *,
    output_dir: Path | None = None,
) -> Path:
    branch = source_branch_name(name)
    tip = branch_head(repo.git, branch)
    if tip is None:
        raise ValueError(f"Source branch {branch!r} does not exist")

    destination = output_dir
    if destination is None:
        papers_root = repo.root.parent / "papers"
        destination = papers_root / _normalize_slug(name)
    destination.mkdir(parents=True, exist_ok=True)

    def _copy_tree(relpath: str = "") -> None:
        for child_name, is_dir in repo.git.list_dir_entries(relpath, commit=tip):
            child_relpath = f"{relpath}/{child_name}" if relpath else child_name
            target = destination / Path(*child_relpath.split("/"))
            if is_dir:
                target.mkdir(parents=True, exist_ok=True)
                _copy_tree(child_relpath)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(repo.git.read_file(child_relpath, commit=tip))

    _copy_tree("")
    return destination
