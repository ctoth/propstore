"""Semantic artifact-code computation and verification helpers."""

from __future__ import annotations

import copy
import json
import hashlib
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from propstore.core.labels import Label
from propstore.identity import canonicalize_claim_for_version
from propstore.knowledge_path import KnowledgePath
from propstore.uri import ni_uri_for_file

if TYPE_CHECKING:
    from propstore.cli.repository import Repository


def _hash_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def source_artifact_code(source_doc: dict[str, Any]) -> str:
    canonical = copy.deepcopy(source_doc)
    canonical.pop("artifact_code", None)
    return _hash_payload(canonical)


def justification_artifact_code(justification: dict[str, Any]) -> str:
    canonical = copy.deepcopy(justification)
    canonical.pop("artifact_code", None)
    premises = canonical.get("premises")
    if isinstance(premises, list):
        canonical["premises"] = sorted(str(premise) for premise in premises)
    return _hash_payload(canonical)


def stance_artifact_code(stance: dict[str, Any]) -> str:
    canonical = copy.deepcopy(stance)
    canonical.pop("artifact_code", None)
    return _hash_payload(canonical)


def claim_artifact_code(
    claim: dict[str, Any],
    *,
    source_code: str,
    justification_codes: list[str],
    stance_codes: list[str],
) -> str:
    canonical = canonicalize_claim_for_version(claim)
    canonical.pop("artifact_code", None)
    return _hash_payload(
        {
            "source_artifact_code": source_code,
            "claim": canonical,
            "justification_codes": sorted(justification_codes),
            "stance_codes": sorted(stance_codes),
        }
    )


def attach_source_artifact_codes(
    source_doc: dict[str, Any],
    claims_doc: dict[str, Any] | None,
    justifications_doc: dict[str, Any] | None,
    stances_doc: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    updated_source = copy.deepcopy(source_doc)
    updated_claims = copy.deepcopy(claims_doc or {"claims": []})
    updated_justifications = copy.deepcopy(justifications_doc or {"justifications": []})
    updated_stances = copy.deepcopy(stances_doc or {"stances": []})

    source_code = source_artifact_code(updated_source)
    updated_source["artifact_code"] = source_code

    justification_codes_by_conclusion: dict[str, list[str]] = defaultdict(list)
    rewritten_justifications: list[Any] = []
    for justification in updated_justifications.get("justifications", []) or []:
        if not isinstance(justification, dict):
            rewritten_justifications.append(justification)
            continue
        rewritten = copy.deepcopy(justification)
        rewritten["artifact_code"] = justification_artifact_code(rewritten)
        conclusion = rewritten.get("conclusion")
        if isinstance(conclusion, str) and conclusion:
            justification_codes_by_conclusion[conclusion].append(rewritten["artifact_code"])
        rewritten_justifications.append(rewritten)
    updated_justifications["justifications"] = rewritten_justifications

    stance_codes_by_source: dict[str, list[str]] = defaultdict(list)
    rewritten_stances: list[Any] = []
    for stance in updated_stances.get("stances", []) or []:
        if not isinstance(stance, dict):
            rewritten_stances.append(stance)
            continue
        rewritten = copy.deepcopy(stance)
        rewritten["artifact_code"] = stance_artifact_code(rewritten)
        source_claim = rewritten.get("source_claim")
        if isinstance(source_claim, str) and source_claim:
            stance_codes_by_source[source_claim].append(rewritten["artifact_code"])
        rewritten_stances.append(rewritten)
    updated_stances["stances"] = rewritten_stances

    rewritten_claims: list[Any] = []
    for claim in updated_claims.get("claims", []) or []:
        if not isinstance(claim, dict):
            rewritten_claims.append(claim)
            continue
        rewritten = copy.deepcopy(claim)
        claim_id = rewritten.get("artifact_id")
        justification_codes = justification_codes_by_conclusion.get(str(claim_id), [])
        stance_codes = stance_codes_by_source.get(str(claim_id), [])
        rewritten["artifact_code"] = claim_artifact_code(
            rewritten,
            source_code=source_code,
            justification_codes=justification_codes,
            stance_codes=stance_codes,
        )
        rewritten_claims.append(rewritten)
    updated_claims["claims"] = rewritten_claims
    return updated_source, updated_claims, updated_justifications, updated_stances


def _load_yaml_from_tree(tree: KnowledgePath, relpath: str) -> dict[str, Any] | None:
    path = tree / relpath
    if not path.exists() or not path.is_file():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _load_claim_index(tree: KnowledgePath) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    from propstore.validate_claims import load_claim_files

    claims_root = tree / "claims"
    if not claims_root.exists():
        return {}, {}

    claims_by_id: dict[str, dict[str, Any]] = {}
    claim_to_source_slug: dict[str, str] = {}
    for claim_file in load_claim_files(claims_root):
        source_slug = claim_file.filename
        for claim in claim_file.data.get("claims", []) or []:
            if not isinstance(claim, dict):
                continue
            claim_id = claim.get("artifact_id")
            if isinstance(claim_id, str) and claim_id:
                claims_by_id[claim_id] = copy.deepcopy(claim)
                claim_to_source_slug[claim_id] = source_slug
    return claims_by_id, claim_to_source_slug


def _load_sources(tree: KnowledgePath) -> dict[str, dict[str, Any]]:
    sources_root = tree / "sources"
    if not sources_root.exists():
        return {}
    return {
        entry.stem: yaml.safe_load(entry.read_text(encoding="utf-8")) or {}
        for entry in sources_root.iterdir()
        if entry.is_file() and entry.suffix == ".yaml"
    }


def _load_justifications(tree: KnowledgePath) -> dict[str, list[dict[str, Any]]]:
    justifications_root = tree / "justifications"
    if not justifications_root.exists():
        return {}
    by_conclusion: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in justifications_root.iterdir():
        if not entry.is_file() or entry.suffix != ".yaml":
            continue
        doc = yaml.safe_load(entry.read_text(encoding="utf-8")) or {}
        for justification in doc.get("justifications", []) or []:
            if isinstance(justification, dict) and isinstance(justification.get("conclusion"), str):
                by_conclusion[justification["conclusion"]].append(copy.deepcopy(justification))
    return by_conclusion


def _load_stances(tree: KnowledgePath) -> dict[str, list[dict[str, Any]]]:
    stances_root = tree / "stances"
    if not stances_root.exists():
        return {}
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in stances_root.iterdir():
        if not entry.is_file() or entry.suffix != ".yaml":
            continue
        doc = yaml.safe_load(entry.read_text(encoding="utf-8")) or {}
        source_claim = doc.get("source_claim")
        if not isinstance(source_claim, str):
            continue
        for stance in doc.get("stances", []) or []:
            if isinstance(stance, dict):
                by_source[source_claim].append(copy.deepcopy(stance))
    return by_source


def _serialize_label(label: Label | None) -> list[list[str]] | None:
    if label is None:
        return None
    return [list(environment.assumption_ids) for environment in label.environments]


def _verify_origin(repo: Repository, source_slug: str, source_doc: dict[str, Any]) -> dict[str, Any]:
    origin = source_doc.get("origin") if isinstance(source_doc.get("origin"), dict) else {}
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
    tree = repo.tree(commit=commit)
    claims_by_id, claim_to_source_slug = _load_claim_index(tree)
    sources_by_slug = _load_sources(tree)
    justifications_by_conclusion = _load_justifications(tree)
    stances_by_source = _load_stances(tree)

    claim_id = claim_ref
    if claim_id not in claims_by_id:
        from propstore.world import WorldModel

        if repo.sidecar_path.exists():
            wm = WorldModel(repo)
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
        source_doc = copy.deepcopy(sources_by_slug.get(source_slug, {}))
        source_expected = source_doc.get("artifact_code")
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
        expected_claim_code = claim.get("artifact_code")
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
            justification_id = str(justification.get("id") or "")
            if justification_id in visited_justifications:
                continue
            visited_justifications.add(justification_id)
            expected = justification.get("artifact_code")
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
            for premise in justification.get("premises") or []:
                if isinstance(premise, str) and premise in claims_by_id:
                    visit(premise)

        for stance in stance_entries:
            stance_key = (
                str(stance.get("source_claim") or ""),
                str(stance.get("target") or ""),
                str(stance.get("type") or ""),
            )
            if stance_key in visited_stances:
                continue
            visited_stances.add(stance_key)
            expected = stance.get("artifact_code")
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
            target = stance.get("target")
            if isinstance(target, str) and target in claims_by_id:
                visit(target)

    visit(claim_id)

    atms_label = None
    if repo.sidecar_path.exists():
        try:
            from propstore.world import WorldModel
            from propstore.world.types import Environment

            wm = WorldModel(repo)
            try:
                bound = wm.bind(Environment())
                atms_label = _serialize_label(bound.atms_engine().claim_label(claim_id))
            finally:
                wm.close()
        except Exception:
            atms_label = None

    source_slug = claim_to_source_slug[claim_id]
    origin_verification = _verify_origin(repo, source_slug, sources_by_slug.get(source_slug, {}))

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
