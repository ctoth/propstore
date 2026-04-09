from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from propstore.cli.repository import Repository

from .claims import load_source_claim_index
from .common import commit_source_file, load_yaml_from_branch, normalize_source_slug, source_branch_name


def resolve_local_claim_reference(reference: object, local_to_artifact: dict[str, str]) -> str:
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
        normalized["conclusion"] = resolve_local_claim_reference(
            normalized.get("conclusion"),
            local_to_artifact,
        )
        premises = normalized.get("premises") or []
        if not isinstance(premises, list):
            raise ValueError("justification premises must be a list")
        normalized["premises"] = [
            resolve_local_claim_reference(premise, local_to_artifact)
            for premise in premises
        ]
        attack_target = normalized.get("attack_target")
        if isinstance(attack_target, dict) and isinstance(attack_target.get("target_claim"), str):
            updated_target = dict(attack_target)
            updated_target["target_claim"] = resolve_local_claim_reference(
                updated_target["target_claim"],
                local_to_artifact,
            )
            normalized["attack_target"] = updated_target
        normalized_justifications.append(normalized)
    normalized_data["justifications"] = normalized_justifications
    return normalized_data


def commit_source_justifications_batch(repo: Repository, source_name: str, justifications_file: Path) -> str:
    local_to_artifact, _logical_to_artifact, _artifact_ids = load_source_claim_index(repo, source_name)
    normalized = normalize_source_justifications_payload(
        yaml.safe_load(justifications_file.read_text(encoding="utf-8")) or {},
        local_to_artifact=local_to_artifact,
    )
    return commit_source_file(
        repo,
        source_name,
        relpath="justifications.yaml",
        content=yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True).encode("utf-8"),
        message=f"Write justifications for {normalize_source_slug(source_name)}",
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
        normalized["source_claim"] = resolve_local_claim_reference(
            normalized.get("source_claim"),
            local_to_artifact,
        )
        target = normalized.get("target")
        if isinstance(target, str) and target in local_to_artifact:
            normalized["target"] = local_to_artifact[target]
        normalized_stances.append(normalized)
    normalized_data["stances"] = normalized_stances
    return normalized_data


def commit_source_stances_batch(repo: Repository, source_name: str, stances_file: Path) -> str:
    local_to_artifact, _logical_to_artifact, _artifact_ids = load_source_claim_index(repo, source_name)
    normalized = normalize_source_stances_payload(
        yaml.safe_load(stances_file.read_text(encoding="utf-8")) or {},
        local_to_artifact=local_to_artifact,
    )
    return commit_source_file(
        repo,
        source_name,
        relpath="stances.yaml",
        content=yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True).encode("utf-8"),
        message=f"Write stances for {normalize_source_slug(source_name)}",
    )


def commit_source_justification_proposal(
    repo: Repository,
    source_name: str,
    *,
    just_id: str,
    conclusion: str,
    premises: list[str],
    rule_kind: str,
    page: int | None = None,
) -> dict[str, Any]:
    branch = source_branch_name(source_name)
    local_to_artifact, _logical, _artifacts = load_source_claim_index(repo, source_name)
    existing = load_yaml_from_branch(repo, branch, "justifications.yaml") or {"justifications": []}
    justifications = list(existing.get("justifications", []) or [])
    justifications = [entry for entry in justifications if not (isinstance(entry, dict) and entry.get("id") == just_id)]

    justification: dict[str, Any] = {
        "id": just_id,
        "conclusion": conclusion,
        "premises": premises,
        "rule_kind": rule_kind,
    }
    if page is not None:
        justification["provenance"] = {"page": page}

    justifications.append(justification)
    data: dict[str, Any] = dict(existing)
    data["justifications"] = justifications

    normalized = normalize_source_justifications_payload(
        data,
        local_to_artifact=local_to_artifact,
    )

    commit_source_file(
        repo,
        source_name,
        relpath="justifications.yaml",
        content=yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True).encode("utf-8"),
        message=f"Propose justification for {normalize_source_slug(source_name)}",
    )

    for entry in normalized.get("justifications", []):
        if isinstance(entry, dict) and entry.get("id") == just_id:
            return entry
    return normalized["justifications"][-1]


def commit_source_stance_proposal(
    repo: Repository,
    source_name: str,
    *,
    source_claim: str,
    target: str,
    stance_type: str,
    strength: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    branch = source_branch_name(source_name)
    local_to_artifact, _logical, _artifacts = load_source_claim_index(repo, source_name)
    existing = load_yaml_from_branch(repo, branch, "stances.yaml") or {"stances": []}
    stances = list(existing.get("stances", []) or [])

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
        source_name,
        relpath="stances.yaml",
        content=yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True).encode("utf-8"),
        message=f"Propose stance for {normalize_source_slug(source_name)}",
    )

    return normalized["stances"][-1]
