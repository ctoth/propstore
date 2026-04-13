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


def worldline_relpath(name: str) -> str:
    return f"worldlines/{name}.yaml"


def canonical_source_relpath(name: str) -> str:
    return f"sources/{name}.yaml"


def claims_file_relpath(name: str) -> str:
    return f"claims/{name}.yaml"


def concept_file_relpath(name: str) -> str:
    return f"concepts/{name}.yaml"


def justifications_file_relpath(name: str) -> str:
    return f"justifications/{name}.yaml"


def stance_file_relpath(source_claim: str) -> str:
    return f"stances/{source_claim.replace(':', '__')}.yaml"


def concept_alignment_relpath(slug: str) -> str:
    return f"merge/concepts/{slug}.yaml"


@dataclass(frozen=True)
class SourceRef:
    name: str


@dataclass(frozen=True)
class ContextRef:
    name: str


@dataclass(frozen=True)
class FormRef:
    name: str


@dataclass(frozen=True)
class WorldlineRef:
    name: str


@dataclass(frozen=True)
class CanonicalSourceRef:
    name: str


@dataclass(frozen=True)
class ClaimsFileRef:
    name: str


@dataclass(frozen=True)
class ConceptFileRef:
    name: str


@dataclass(frozen=True)
class JustificationsFileRef:
    name: str


@dataclass(frozen=True)
class StanceFileRef:
    source_claim: str


@dataclass(frozen=True)
class ConceptAlignmentRef:
    slug: str
