from __future__ import annotations

from dataclasses import dataclass
def normalize_source_slug(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in name.strip())
    cleaned = cleaned.strip("._-")
    return cleaned or "source"


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
