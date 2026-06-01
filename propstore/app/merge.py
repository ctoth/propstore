"""Application-layer repository merge workflows."""

from __future__ import annotations

from dataclasses import dataclass

from propstore.families.registry import MergeManifestRef
from propstore.repository import Repository


@dataclass(frozen=True)
class MergeInspectRequest:
    branch_a: str
    branch_b: str
    semantics: str = "grounded"


@dataclass(frozen=True)
class MergeCommitRequest:
    branch_a: str
    branch_b: str
    message: str = ""
    target_branch: str | None = None
