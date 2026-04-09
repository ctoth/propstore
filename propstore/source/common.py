from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from propstore.cli.repository import Repository
from propstore.repo.branch import branch_head, create_branch
from propstore.uri import ni_uri_for_file, source_tag_uri as mint_source_tag_uri


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_source_slug(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in name.strip())
    cleaned = cleaned.strip("._-")
    return cleaned or "source"


def source_branch_name(name: str) -> str:
    return f"source/{normalize_source_slug(name)}"


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
            "retrieved": utc_now(),
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
            "name": normalize_source_slug(name),
        },
    }


def load_yaml_from_branch(
    repo: Repository,
    branch: str,
    relpath: str,
) -> dict[str, Any] | None:
    tip = branch_head(repo.git, branch)
    if tip is None:
        return None
    try:
        return yaml.safe_load(repo.git.read_file(relpath, commit=tip)) or {}
    except FileNotFoundError:
        return None


def load_branch_yaml(
    repo: Repository,
    name: str,
    relpath: str,
) -> dict[str, Any] | None:
    return load_yaml_from_branch(repo, source_branch_name(name), relpath)


def write_yaml(
    repo: Repository,
    *,
    branch: str,
    relpath: str,
    data: dict[str, Any],
    message: str,
) -> str:
    payload = yaml.safe_dump(data, sort_keys=False, allow_unicode=True).encode("utf-8")
    return repo.git.commit_batch(adds={relpath: payload}, deletes=[], message=message, branch=branch)


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
    write_yaml(
        repo,
        branch=branch,
        relpath="source.yaml",
        data=source_doc,
        message=f"Initialize source {normalize_source_slug(name)}",
    )
    return branch


def commit_source_notes(repo: Repository, name: str, notes_file: Path) -> str:
    return commit_source_file(
        repo,
        name,
        relpath="notes.md",
        content=notes_file.read_bytes(),
        message=f"Write notes for {normalize_source_slug(name)}",
    )


def commit_source_metadata(repo: Repository, name: str, metadata_file: Path) -> str:
    loaded = json.loads(metadata_file.read_text(encoding="utf-8"))
    payload = json.dumps(loaded, indent=2, ensure_ascii=False).encode("utf-8")
    return commit_source_file(
        repo,
        name,
        relpath="metadata.json",
        content=payload,
        message=f"Write metadata for {normalize_source_slug(name)}",
    )


def load_source_document(repo: Repository, name: str) -> dict[str, Any]:
    branch = source_branch_name(name)
    tip = branch_head(repo.git, branch)
    if tip is None:
        raise ValueError(f"Source branch {branch!r} does not exist")
    return yaml.safe_load(repo.git.read_file("source.yaml", commit=tip)) or {}
