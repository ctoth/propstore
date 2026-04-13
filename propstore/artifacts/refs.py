from __future__ import annotations

from dataclasses import dataclass


def normalize_source_slug(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in name.strip())
    cleaned = cleaned.strip("._-")
    return cleaned or "source"


def source_branch_name(name: str) -> str:
    return f"source/{normalize_source_slug(name)}"


def source_finalize_relpath(name: str) -> str:
    return f"merge/finalize/{normalize_source_slug(name)}.yaml"


@dataclass(frozen=True)
class SourceRef:
    name: str


@dataclass(frozen=True)
class ContextRef:
    name: str


@dataclass(frozen=True)
class FormRef:
    name: str
