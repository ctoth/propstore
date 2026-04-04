"""Git-backed source branch helpers."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from propstore.cli.repository import Repository
from propstore.identity import compute_claim_version_id, derive_claim_artifact_id, normalize_logical_value
from propstore.repo.branch import branch_head, create_branch


_DEFAULT_URI_AUTHORITY = "local@propstore,2026"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_slug(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in name.strip())
    cleaned = cleaned.strip("._-")
    return cleaned or "source"


def source_branch_name(name: str) -> str:
    return f"source/{_normalize_slug(name)}"


def source_tag_uri(name: str, *, authority: str = _DEFAULT_URI_AUTHORITY) -> str:
    return f"tag:{authority}:source/{_normalize_slug(name)}"


def initial_source_document(
    name: str,
    *,
    kind: str,
    origin_type: str,
    origin_value: str,
) -> dict[str, Any]:
    return {
        "id": source_tag_uri(name),
        "kind": kind,
        "origin": {
            "type": origin_type,
            "value": origin_value,
            "retrieved": _utc_now(),
            "content_ref": None,
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


def init_source_branch(
    repo: Repository,
    name: str,
    *,
    kind: str,
    origin_type: str,
    origin_value: str,
) -> str:
    if repo.git is None:
        raise ValueError("source operations require a git-backed repository")
    branch = source_branch_name(name)
    if branch_head(repo.git, branch) is None:
        create_branch(repo.git, branch)
    source_doc = initial_source_document(
        name,
        kind=kind,
        origin_type=origin_type,
        origin_value=origin_value,
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
        if isinstance(raw_id, str) and raw_id:
            normalized["source_local_id"] = raw_id
            local_to_canonical[raw_id] = stable_value
        normalized["logical_ids"] = [{"namespace": namespace, "value": stable_value}]
        normalized["artifact_id"] = derive_claim_artifact_id(namespace, stable_value)
        normalized["version_id"] = compute_claim_version_id(normalized)
        normalized_claims.append(normalized)

    normalized_data["claims"] = normalized_claims
    return normalized_data, local_to_canonical


def commit_source_claims_batch(repo: Repository, name: str, claims_file: Path) -> str:
    source_doc = load_source_document(repo, name)
    normalized, _ = normalize_source_claims_payload(
        yaml.safe_load(claims_file.read_text(encoding="utf-8")) or {},
        source_uri=str(source_doc.get("id") or source_tag_uri(name)),
        source_namespace=_normalize_slug(name),
    )
    return commit_source_file(
        repo,
        name,
        relpath="claims.yaml",
        content=yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True).encode("utf-8"),
        message=f"Write claims for {_normalize_slug(name)}",
    )


def _load_branch_yaml(repo: Repository, name: str, relpath: str) -> dict[str, Any] | None:
    branch = source_branch_name(name)
    tip = branch_head(repo.git, branch)
    if tip is None:
        raise ValueError(f"Source branch {branch!r} does not exist")
    try:
        return yaml.safe_load(repo.git.read_file(relpath, commit=tip)) or {}
    except FileNotFoundError:
        return None


def finalize_source_branch(repo: Repository, name: str) -> str:
    source_doc = load_source_document(repo, name)
    claims_doc = _load_branch_yaml(repo, name, "claims.yaml") or {}
    claims = claims_doc.get("claims", []) if isinstance(claims_doc, dict) else []
    claim_errors: list[str] = []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        if not isinstance(claim.get("artifact_id"), str):
            claim_errors.append(str(claim.get("id") or "?"))
    report = {
        "kind": "source_finalize_report",
        "source": str(source_doc.get("id") or source_tag_uri(name)),
        "status": "ready" if not claim_errors else "blocked",
        "claim_reference_errors": claim_errors,
        "stance_reference_errors": [],
        "concept_alignment_candidates": [],
        "parameterization_group_merges": [],
        "artifact_code_status": "complete" if not claim_errors else "incomplete",
        "calibration": {
            "prior_base_rate_status": "fallback",
            "source_quality_status": "vacuous",
            "fallback_to_default_base_rate": True,
        },
    }
    return commit_source_file(
        repo,
        name,
        relpath=f"merge/finalize/{_normalize_slug(name)}.yaml",
        content=yaml.safe_dump(report, sort_keys=False, allow_unicode=True).encode("utf-8"),
        message=f"Finalize {_normalize_slug(name)}",
    )
