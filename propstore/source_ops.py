"""Git-backed source branch helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from propstore.cli.repository import Repository
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
