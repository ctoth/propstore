from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


STANCE_PROPOSAL_BRANCH = "proposal/stances"


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


def micropubs_file_relpath(name: str) -> str:
    return f"micropubs/{name}.yaml"


def concept_file_relpath(name: str) -> str:
    return f"concepts/{name}.yaml"


def justifications_file_relpath(name: str) -> str:
    return f"justifications/{name}.yaml"


def predicate_file_relpath(name: str) -> str:
    return f"predicates/{name}.yaml"


def rule_file_relpath(name: str) -> str:
    return f"rules/{name}.yaml"


def stance_file_relpath(source_claim: str) -> str:
    return f"stances/{source_claim.replace(':', '__')}.yaml"


def source_claim_from_stance_path(path: str | Path) -> str:
    normalized = str(path).replace("\\", "/")
    filename = Path(normalized).name
    if not filename.endswith(".yaml"):
        raise ValueError(f"expected stance yaml path, got {normalized!r}")
    return filename.removesuffix(".yaml").replace("__", ":")


def concept_alignment_relpath(slug: str) -> str:
    return f"merge/concepts/{slug}.yaml"


def merge_manifest_relpath() -> str:
    return "merge/manifest.yaml"


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
class MicropubsFileRef:
    name: str


@dataclass(frozen=True)
class ConceptFileRef:
    name: str


@dataclass(frozen=True)
class JustificationsFileRef:
    name: str


@dataclass(frozen=True)
class PredicateFileRef:
    name: str


@dataclass(frozen=True)
class RuleFileRef:
    name: str


@dataclass(frozen=True)
class StanceFileRef:
    source_claim: str


@dataclass(frozen=True)
class ConceptAlignmentRef:
    slug: str


@dataclass(frozen=True)
class MergeManifestRef:
    pass
