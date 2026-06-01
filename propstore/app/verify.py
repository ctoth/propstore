"""Application-layer verification workflows.

The claim-tree verification entry point lives here, in the render/app layer,
because it reaches into ``propstore.world`` (WorldQuery/ATMS, Environment) to
attach an ATMS label to the verified claim. The family-projection layer
(``propstore.families.artifacts``) owns artifact-code derivation and the
verification index, neither of which may depend on the world layer; keeping the
world-touching traversal here preserves the six-layer import contract.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from propstore.core.labels import Label
from propstore.families.artifacts import (
    ArtifactReference,
    ArtifactVerificationRecord,
    build_artifact_verification_index,
)
from propstore.families.sources.declaration import source_document_payload
from propstore.repository import Repository
from propstore.uri import ni_uri_for_file


def _claim_dependency_targets(
    record: ArtifactVerificationRecord,
    records: dict[ArtifactReference, ArtifactVerificationRecord],
) -> Iterable[str]:
    for dependency in record.dependencies:
        dep_record = records.get(dependency)
        if dep_record is None:
            continue
        if dependency.family == "justification":
            premises = dep_record.metadata.get("premises", ())
            if not isinstance(premises, tuple):
                continue
            for premise in premises:
                if isinstance(premise, str) and premise:
                    yield premise
        elif dependency.family == "stance":
            target = dep_record.metadata.get("target")
            if isinstance(target, str) and target:
                yield target


def _serialize_label(label: Label | None) -> list[list[str]] | None:
    if label is None:
        return None
    return [list(environment.assumption_ids) for environment in label.environments]


def _verify_origin(
    repo: Repository, source_slug: str, source_doc: dict[str, Any]
) -> dict[str, Any]:
    raw_origin = source_doc.get("origin")
    if raw_origin is None:
        origin: dict[str, Any] = {}
    elif isinstance(raw_origin, dict):
        origin = raw_origin
    else:
        raise ValueError(f"source {source_slug}: origin must be a mapping")
    expected = origin.get("content_ref")
    if not isinstance(expected, str) or not expected:
        return {
            "status": "unavailable",
            "path": None,
            "expected": expected,
            "actual": None,
        }

    value = origin.get("value")
    candidates: list[Path] = []
    if isinstance(value, str) and value:
        value_path = Path(value)
        if value_path.is_absolute():
            candidates.append(value_path)
        candidates.append(repo.root.parent / "papers" / source_slug / value_path.name)
    candidates.append(repo.root.parent / "papers" / source_slug / "paper.pdf")

    for candidate in candidates:
        if not candidate.exists() or not candidate.is_file():
            continue
        actual = ni_uri_for_file(candidate)
        return {
            "status": "matched" if actual == expected else "mismatch",
            "path": str(candidate),
            "expected": expected,
            "actual": actual,
        }
    return {"status": "unavailable", "path": None, "expected": expected, "actual": None}
