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


def _verify_origin(repo: Repository, source_slug: str, source_doc: dict[str, Any]) -> dict[str, Any]:
    raw_origin = source_doc.get("origin")
    if raw_origin is None:
        origin: dict[str, Any] = {}
    elif isinstance(raw_origin, dict):
        origin = raw_origin
    else:
        raise ValueError(f"source {source_slug}: origin must be a mapping")
    expected = origin.get("content_ref")
    if not isinstance(expected, str) or not expected:
        return {"status": "unavailable", "path": None, "expected": expected, "actual": None}

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


def verify_claim_tree(repo: Repository, claim_ref: str, *, commit: str | None = None) -> dict[str, Any]:
    index = build_artifact_verification_index(repo, commit=commit)
    try:
        root_ref = index.require_claim(claim_ref)
    except ValueError:
        from propstore.world.model import WorldQuery

        try:
            wm = WorldQuery(repo)
        except FileNotFoundError:
            wm = None
        if wm is not None:
            try:
                resolved_claim = wm.get_claim(claim_ref)
            finally:
                wm.close()
            if resolved_claim is not None:
                root_ref = index.require_claim(str(resolved_claim.id))
            else:
                raise
        else:
            raise

    visited_claims: set[ArtifactReference] = set()
    visited_nonclaims: set[ArtifactReference] = set()
    claim_reports: list[dict[str, Any]] = []
    justification_reports: list[dict[str, Any]] = []
    stance_reports: list[dict[str, Any]] = []
    source_reports: dict[str, dict[str, Any]] = {}
    overall_status = "ok"

    def record_mismatch(record: ArtifactVerificationRecord) -> None:
        nonlocal overall_status
        if record.status != "ok":
            overall_status = "mismatch"

    def visit_claim(current_ref: ArtifactReference) -> None:
        if current_ref in visited_claims:
            return
        visited_claims.add(current_ref)
        record = index.records[current_ref]
        record_mismatch(record)
        claim_id = str(record.metadata["claim_id"])
        claim_reports.append(
            {
                "claim_id": claim_id,
                "expected": record.expected,
                "actual": record.actual,
                "status": record.status,
            }
        )

        for dependency in record.dependencies:
            dep_record = index.records.get(dependency)
            if dep_record is None:
                continue
            record_mismatch(dep_record)
            if dependency.family == "source":
                source_slug = str(dep_record.metadata["source"])
                if source_slug not in source_reports:
                    source_reports[source_slug] = {
                        "source": source_slug,
                        "expected": dep_record.expected,
                        "actual": dep_record.actual,
                        "status": dep_record.status,
                    }
                continue
            if dependency in visited_nonclaims:
                continue
            visited_nonclaims.add(dependency)
            if dependency.family == "justification":
                justification_reports.append(
                    {
                        "id": dep_record.metadata.get("id"),
                        "expected": dep_record.expected,
                        "actual": dep_record.actual,
                        "status": dep_record.status,
                    }
                )
            elif dependency.family == "stance":
                stance_reports.append(
                    {
                        "source_claim": dep_record.metadata.get("source_claim"),
                        "target": dep_record.metadata.get("target"),
                        "type": dep_record.metadata.get("type"),
                        "expected": dep_record.expected,
                        "actual": dep_record.actual,
                        "status": dep_record.status,
                    }
                )
        for target_claim_id in _claim_dependency_targets(record, index.records):
            target_ref = index.claim_lookup.get(target_claim_id)
            if target_ref is not None:
                visit_claim(target_ref)

    visit_claim(root_ref)

    atms_label = None
    from propstore.world.model import WorldQuery
    from propstore.world.types import Environment

    try:
        wm = WorldQuery(repo)
    except FileNotFoundError:
        wm = None
    if wm is not None:
        try:
            bound = wm.bind(Environment())
            atms_label = _serialize_label(bound.atms_engine().claim_label(root_ref.identity))
        finally:
            wm.close()

    source_ref = index.source_by_claim[root_ref.identity]
    source_slug = source_ref.identity
    source_doc = next(
        (
            handle.document
            for handle in repo.families.sources.iter_handles(commit=commit)
            if handle.ref.name == source_slug
        ),
        None,
    )
    origin_verification = _verify_origin(
        repo,
        source_slug,
        {} if source_doc is None else source_document_payload(source_doc),
    )

    return {
        "claim_id": root_ref.identity,
        "status": overall_status if origin_verification["status"] != "mismatch" else "mismatch",
        "claim": claim_reports[0],
        "claims": claim_reports,
        "justifications": justification_reports,
        "stances": stance_reports,
        "sources": list(source_reports.values()),
        "origin_verification": origin_verification,
        "atms_label": atms_label,
    }
