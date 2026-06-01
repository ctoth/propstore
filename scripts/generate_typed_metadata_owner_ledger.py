from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


LEDGER_COLUMNS = (
    "field_name",
    "declaring_file",
    "declaration_kind",
    "nullability",
    "default",
    "check",
    "fk",
    "enum_coercion",
    "required",
    "current_role",
    "owner_category",
    "target_owner_file",
    "target_descriptor",
    "deletion_proof",
    "pinned_tests",
    "metric_id",
    "baseline_count",
    "target_count",
    "quire_dependency_id",
    "sidecar_disposition",
    "slice_id",
    "status",
)


TEST_PINS = {
    "concepts": "tests/test_concept_views.py; tests/test_sidecar_concept_projection.py; tests/test_sidecar_projection_fts_contract.py",
    "claims": "tests/test_claim_views.py; tests/test_sidecar_projection_contract.py; tests/test_sidecar_projection_fts_contract.py",
    "contexts": "tests/test_sidecar_contexts.py; tests/architecture/test_ist_projection_contract.py",
    "relations": "tests/test_sidecar_relation_edge_projection.py; tests/test_relate_opinions.py",
    "micropublications": "tests/test_micropub_identity_dedupe_shape.py; tests/remediation/phase_7_race_atomicity/test_T7_5g_sidecar_build_duplicate_micropublication.py",
    "sources": "tests/test_sidecar_source_projection.py; tests/test_source_promotion_alignment.py",
    "diagnostics": "tests/test_cli_source_status.py; tests/remediation/phase_2_gates/test_T2_3c_embedding_restore_diagnostics.py",
    "rules": "tests/test_sidecar_grounded_facts.py",
    "calibration": "tests/test_sidecar_calibration_counts_projection.py; tests/test_calibrate.py",
    "embedding": "tests/test_sidecar_projection_vec_contract.py; tests/test_no_embedding_key_collision.py; tests/test_embed_operational_error.py",
    "world": "tests/test_world_query.py; tests/test_world_layer_boundary.py",
}


def _summary(data: dict[str, Any]) -> dict[str, int]:
    raw = data.get("summary", {})
    if not isinstance(raw, dict):
        return {}
    return {
        str(key): int(value) for key, value in raw.items() if isinstance(value, int)
    }


def _target_for_name(name: str) -> tuple[str, str, str]:
    lower = name.lower()
    if "concept" in lower or lower in {
        "alias",
        "form",
        "form_algebra",
        "parameterization",
        "parameterization_group",
    }:
        return ("concepts", "propstore/families/concepts/declaration.py", "concept")
    if "claim" in lower or lower in {"justification"}:
        return ("claims", "propstore/families/claims/declaration.py", "claim")
    if "context" in lower:
        return ("contexts", "propstore/families/contexts/declaration.py", "context")
    if (
        "relation" in lower
        or "conflict" in lower
        or "stance" in lower
        or "opinion" in lower
    ):
        return ("relations", "propstore/families/relations/declaration.py", "relation")
    if "micropublication" in lower:
        return (
            "micropublications",
            "propstore/families/micropublications/declaration.py",
            "micropublication",
        )
    if "source" in lower:
        return ("sources", "propstore/families/sources/declaration.py", "source")
    if "diagnostic" in lower or "quarantine" in lower:
        return (
            "diagnostics",
            "propstore/families/diagnostics/declaration.py",
            "diagnostic",
        )
    if "grounded" in lower or "rule" in lower or "bundle" in lower:
        return ("rules", "propstore/families/rules/declaration.py", "rule")
    if "calibration" in lower:
        return (
            "calibration",
            "propstore/families/calibration/declaration.py",
            "calibration",
        )
    if "embedding" in lower or "vec" in lower:
        return (
            "embedding",
            "propstore/families/embeddings/declaration.py",
            "embedding",
        )
    return ("world", "propstore/families/_generated/catalog.py", "catalog")


def _role_for_field(field_name: str, declaration_kind: str) -> str:
    if declaration_kind in {"fts_source"}:
        return "search"
    if declaration_kind in {"vector_source"}:
        return "vector"
    if (
        declaration_kind in {"foreign_key"}
        or field_name.endswith("_id")
        or field_name in {"id"}
    ):
        return "reference"
    if "provenance" in field_name or "source" in field_name:
        return "provenance"
    if "diagnostic" in field_name or "status" in field_name:
        return "diagnostic"
    if "text" in field_name or "statement" in field_name or "description" in field_name:
        return "payload_text"
    if "value" in field_name or "count" in field_name or "distance" in field_name:
        return "payload_numeric"
    return "context"


def _sidecar_disposition_for_path(path: str, data: dict[str, Any]) -> str:
    for record in data.get("sidecar_dispositions", []):
        if isinstance(record, dict) and record.get("path") == path:
            disposition = str(record.get("suggested_disposition", "needs-ledger"))
            if disposition == "derived-declaration-owner":
                return "deleted"
            if disposition == "vector-declaration-owner":
                return "semantic-owner-moved"
            if disposition == "quire-owned-candidate":
                return "quire-owned"
            if disposition == "retained-product-escape-hatch-candidate":
                return "retained-product-escape-hatch"
    return ""


def _row(
    *,
    data: dict[str, Any],
    field_name: str,
    declaring_file: str,
    declaration_kind: str,
    owner_category: str,
    metric_id: str,
    baseline_count: int,
    target_count: int,
    quire_dependency_id: str,
    status: str = "pending",
) -> dict[str, str]:
    family, owner_file, descriptor = _target_for_name(field_name + " " + declaring_file)
    sidecar_disposition = _sidecar_disposition_for_path(declaring_file, data)
    deletion_proof = f"{metric_id}: {baseline_count} -> {target_count}"
    return {
        "field_name": field_name,
        "declaring_file": declaring_file,
        "declaration_kind": declaration_kind,
        "nullability": "ledger-required",
        "default": "ledger-required",
        "check": "ledger-required",
        "fk": "ledger-required" if declaration_kind == "foreign_key" else "",
        "enum_coercion": "ledger-required",
        "required": "ledger-required",
        "current_role": _role_for_field(field_name, declaration_kind),
        "owner_category": owner_category,
        "target_owner_file": owner_file,
        "target_descriptor": descriptor,
        "deletion_proof": deletion_proof,
        "pinned_tests": TEST_PINS.get(family, ""),
        "metric_id": metric_id,
        "baseline_count": str(baseline_count),
        "target_count": str(target_count),
        "quire_dependency_id": quire_dependency_id,
        "sidecar_disposition": sidecar_disposition,
        "slice_id": family,
        "status": status,
    }


def build_rows(data: dict[str, Any]) -> list[dict[str, str]]:
    summary = _summary(data)
    rows: list[dict[str, str]] = []
    for file_record in data.get("files", []):
        if not isinstance(file_record, dict):
            continue
        path = str(file_record.get("path", ""))
        if not path.startswith("propstore/"):
            continue
        for field_name in file_record.get("projection_columns", []):
            rows.append(
                _row(
                    data=data,
                    field_name=str(field_name),
                    declaring_file=path,
                    declaration_kind="projection_column",
                    owner_category="propstore-derived-store-declaration",
                    metric_id="sidecar_projection_columns",
                    baseline_count=summary.get("sidecar_projection_columns", 0),
                    target_count=0,
                    quire_dependency_id="QD-001",
                )
            )
        for field_name in file_record.get("projection_foreign_keys", []):
            rows.append(
                _row(
                    data=data,
                    field_name=str(field_name),
                    declaring_file=path,
                    declaration_kind="foreign_key",
                    owner_category="quire-artifact-family",
                    metric_id="handwritten_fk_edges",
                    baseline_count=summary.get("handwritten_fk_edges", 0),
                    target_count=0,
                    quire_dependency_id="QD-008",
                )
            )
        for field_name in file_record.get("fts_projections", []):
            rows.append(
                _row(
                    data=data,
                    field_name=str(field_name),
                    declaring_file=path,
                    declaration_kind="fts_source",
                    owner_category="propstore-derived-store-declaration",
                    metric_id="handwritten_fts_projections",
                    baseline_count=summary.get("handwritten_fts_projections", 0),
                    target_count=0,
                    quire_dependency_id="QD-002",
                )
            )
        for field_name in file_record.get(
            "rowid_vec_projections", []
        ) + file_record.get("embedding_status_projections", []):
            rows.append(
                _row(
                    data=data,
                    field_name=str(field_name),
                    declaring_file=path,
                    declaration_kind="vector_source",
                    owner_category="propstore-derived-store-declaration",
                    metric_id="handwritten_vec_declarations",
                    baseline_count=summary.get("handwritten_vec_declarations", 0),
                    target_count=0,
                    quire_dependency_id="QD-003",
                )
            )
        if not path.startswith("propstore/sidecar/"):
            for field_name in file_record.get("table_name_mentions", []):
                rows.append(
                    _row(
                        data=data,
                        field_name=str(field_name),
                        declaring_file=path,
                        declaration_kind="sql_literal",
                        owner_category="typed-query-api",
                        metric_id="table_name_mentions_outside_sidecar",
                        baseline_count=summary.get(
                            "table_name_mentions_outside_sidecar", 0
                        ),
                        target_count=0,
                        quire_dependency_id="QD-005",
                    )
                )
        for class_name in file_record.get("class_surfaces", []):
            owner_category = "typed-query-api"
            metric_id = "class_surfaces_total"
            target_count = summary.get("class_surfaces_total", 0)
            if path.startswith("propstore/worldline/") or path.startswith(
                "propstore/support_revision/"
            ):
                owner_category = "runtime-wire-report"
            elif path.startswith("propstore/app/"):
                owner_category = "presentation-adapter"
                metric_id = "class_surfaces_app_world"
                target_count = 0
            elif path.startswith("propstore/world/"):
                metric_id = "class_surfaces_app_world"
            rows.append(
                _row(
                    data=data,
                    field_name=str(class_name),
                    declaring_file=path,
                    declaration_kind="app_request_report_shape",
                    owner_category=owner_category,
                    metric_id=metric_id,
                    baseline_count=summary.get(metric_id, 0),
                    target_count=target_count,
                    quire_dependency_id="",
                )
            )
        for method_name in file_record.get("codec_methods", []):
            metric_id = "codec_methods_total"
            target_count = summary.get(metric_id, 0)
            if path.startswith("propstore/families/") or path.startswith(
                "propstore/source/"
            ):
                metric_id = "codec_methods_families_source"
                target_count = 0
            rows.append(
                _row(
                    data=data,
                    field_name=str(method_name),
                    declaring_file=path,
                    declaration_kind="family_payload_field",
                    owner_category="io-boundary-codec"
                    if "source" in path
                    else "propstore-semantic-declaration",
                    metric_id=metric_id,
                    baseline_count=summary.get(metric_id, 0),
                    target_count=target_count,
                    quire_dependency_id="",
                )
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate typed metadata owner ledger CSV."
    )
    parser.add_argument("baseline", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    data = json.loads(args.baseline.read_text(encoding="utf-8"))
    rows = build_rows(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} ledger rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
