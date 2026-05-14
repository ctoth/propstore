"""Verification workflows for semantic artifact codes."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

from propstore.artifact_codes import (
    claim_artifact_code,
    justification_artifact_code,
    source_artifact_code,
    stance_artifact_code,
)
from propstore.claims import claim_file_claims, claim_file_source_paper
from propstore.core.labels import Label
from propstore.families.claims.documents import ClaimDocument
from propstore.families.documents.justifications import JustificationDocument
from propstore.families.documents.sources import SourceDocument
from propstore.families.documents.stances import StanceDocument
from propstore.uri import ni_uri_for_file

if TYPE_CHECKING:
    from propstore.repository import Repository


def _load_claim_index(repo: Repository, commit: str | None) -> tuple[dict[str, ClaimDocument], dict[str, str]]:
    claims_by_id: dict[str, ClaimDocument] = {}
    claim_to_source_slug: dict[str, str] = {}
    for claim_file in repo.families.claims.iter_handles(commit=commit):
        source_slug = claim_file_source_paper(claim_file)
        for claim in claim_file_claims(claim_file):
            claim_id = claim.artifact_id
            if isinstance(claim_id, str) and claim_id:
                claims_by_id[claim_id] = claim
                claim_to_source_slug[claim_id] = source_slug
    return claims_by_id, claim_to_source_slug


def _load_sources(repo: Repository, commit: str | None) -> dict[str, SourceDocument]:
    return {
        handle.ref.name: handle.document
        for handle in repo.families.sources.iter_handles(commit=commit)
    }


def _load_justifications(repo: Repository, commit: str | None) -> dict[str, list[JustificationDocument]]:
    by_conclusion: dict[str, list[JustificationDocument]] = defaultdict(list)
    for handle in repo.families.justifications.iter_handles(commit=commit):
        doc = handle.document
        if isinstance(doc.conclusion, str):
            by_conclusion[doc.conclusion].append(doc)
    return by_conclusion


def _load_stances(repo: Repository, commit: str | None) -> dict[str, list[StanceDocument]]:
    by_source: dict[str, list[StanceDocument]] = defaultdict(list)
    for handle in repo.families.stances.iter_handles(commit=commit):
        doc = handle.document
        source_claim = doc.source_claim
        if isinstance(source_claim, str) and source_claim:
            by_source[source_claim].append(doc)
    return by_source


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
    claims_by_id, claim_to_source_slug = _load_claim_index(repo, commit)
    sources_by_slug = _load_sources(repo, commit)
    justifications_by_conclusion = _load_justifications(repo, commit)
    stances_by_source = _load_stances(repo, commit)

    claim_id = claim_ref
    if claim_id not in claims_by_id:
        from propstore.world import WorldQuery

        try:
            wm = WorldQuery(repo)
        except FileNotFoundError:
            wm = None
        if wm is not None:
            try:
                resolved = wm.resolve_claim(claim_ref)
            finally:
                wm.close()
            if isinstance(resolved, str):
                claim_id = resolved

    if claim_id not in claims_by_id:
        raise ValueError(f"Unknown claim reference: {claim_ref}")

    visited_claims: set[str] = set()
    visited_justifications: set[str] = set()
    visited_stances: set[tuple[str, str, str]] = set()
    claim_reports: list[dict[str, Any]] = []
    justification_reports: list[dict[str, Any]] = []
    stance_reports: list[dict[str, Any]] = []
    source_reports: dict[str, dict[str, Any]] = {}
    overall_status = "ok"

    def visit(current_claim_id: str) -> None:
        nonlocal overall_status
        if current_claim_id in visited_claims:
            return
        visited_claims.add(current_claim_id)
        claim = claims_by_id[current_claim_id]
        source_slug = claim_to_source_slug[current_claim_id]
        source_doc = sources_by_slug.get(source_slug)
        source_expected = None if source_doc is None else source_doc.artifact_code
        source_actual = source_artifact_code(source_doc) if source_doc else None
        source_status = "ok" if source_expected == source_actual else "mismatch"
        if source_slug not in source_reports:
            source_reports[source_slug] = {
                "source": source_slug,
                "expected": source_expected,
                "actual": source_actual,
                "status": source_status,
            }
        if source_status != "ok":
            overall_status = "mismatch"

        justifications = justifications_by_conclusion.get(current_claim_id, [])
        stance_entries = stances_by_source.get(current_claim_id, [])
        justification_codes = [justification_artifact_code(item) for item in justifications]
        stance_codes = [stance_artifact_code(item) for item in stance_entries]
        actual_claim_code = claim_artifact_code(
            claim,
            source_code=source_actual or "",
            justification_codes=justification_codes,
            stance_codes=stance_codes,
        )
        expected_claim_code = claim.artifact_code
        if not isinstance(expected_claim_code, str) or not expected_claim_code:
            expected_claim_code = actual_claim_code
        claim_status = "ok" if expected_claim_code == actual_claim_code else "mismatch"
        claim_reports.append(
            {
                "claim_id": current_claim_id,
                "expected": expected_claim_code,
                "actual": actual_claim_code,
                "status": claim_status,
            }
        )
        if claim_status != "ok":
            overall_status = "mismatch"

        for justification in justifications:
            justification_id = str(justification.id or "")
            if justification_id in visited_justifications:
                continue
            visited_justifications.add(justification_id)
            expected = justification.artifact_code
            actual = justification_artifact_code(justification)
            status = "ok" if expected == actual else "mismatch"
            justification_reports.append(
                {
                    "id": justification_id,
                    "expected": expected,
                    "actual": actual,
                    "status": status,
                }
            )
            if status != "ok":
                overall_status = "mismatch"
            for premise in justification.premises:
                if isinstance(premise, str) and premise in claims_by_id:
                    visit(premise)

        for stance in stance_entries:
            stance_key = (
                str(stance.source_claim or ""),
                str(stance.target or ""),
                str(stance.type or ""),
            )
            if stance_key in visited_stances:
                continue
            visited_stances.add(stance_key)
            expected = stance.artifact_code
            actual = stance_artifact_code(stance)
            status = "ok" if expected == actual else "mismatch"
            stance_reports.append(
                {
                    "source_claim": stance_key[0],
                    "target": stance_key[1],
                    "type": stance_key[2],
                    "expected": expected,
                    "actual": actual,
                    "status": status,
                }
            )
            if status != "ok":
                overall_status = "mismatch"
            target = stance.target
            if isinstance(target, str) and target in claims_by_id:
                visit(target)

    visit(claim_id)

    atms_label = None
    from propstore.world import WorldQuery
    from propstore.world.types import Environment

    try:
        wm = WorldQuery(repo)
    except FileNotFoundError:
        wm = None
    if wm is not None:
        try:
            bound = wm.bind(Environment())
            atms_label = _serialize_label(bound.atms_engine().claim_label(claim_id))
        finally:
            wm.close()

    source_slug = claim_to_source_slug[claim_id]
    origin_source_doc = sources_by_slug.get(source_slug)
    origin_verification = _verify_origin(
        repo,
        source_slug,
        {} if origin_source_doc is None else origin_source_doc.to_payload(),
    )

    return {
        "claim_id": claim_id,
        "status": overall_status if origin_verification["status"] != "mismatch" else "mismatch",
        "claim": claim_reports[0],
        "claims": claim_reports,
        "justifications": justification_reports,
        "stances": stance_reports,
        "sources": list(source_reports.values()),
        "origin_verification": origin_verification,
        "atms_label": atms_label,
    }
