"""Claim-side compilation helpers for the sidecar."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from typing import TYPE_CHECKING

import yaml

from propstore.loaded import LoadedEntry
from propstore.knowledge_path import KnowledgePath
from propstore.sidecar.claim_utils import (
    claim_reference_map_from_conn,
    coerce_stance_resolution,
    collect_claim_reference_map,
    extract_deferred_stance_rows,
    insert_claim_row,
    insert_claim_stance_row,
    prepare_claim_insert_row,
    resolve_claim_reference,
)
from propstore.stances import VALID_STANCE_TYPES

if TYPE_CHECKING:
    from propstore.compiler.ir import ClaimCompilationBundle


def populate_stances_from_files(
    conn: sqlite3.Connection,
    stances_root: KnowledgePath,
) -> int:
    """Read stance YAML files and insert them into normalized relation storage."""
    if not stances_root.exists():
        return 0
    stance_entries = [
        (entry.stem, yaml.safe_load(entry.read_bytes()) or {})
        for entry in stances_root.iterdir()
        if entry.is_file() and entry.suffix == ".yaml"
    ]
    if not stance_entries:
        return 0

    claim_reference_map = claim_reference_map_from_conn(conn)
    valid_claims = set(claim_reference_map.values())
    count = 0

    for filename, data in stance_entries:
        source_claim = resolve_claim_reference(
            data.get("source_claim", ""),
            claim_reference_map,
        ) or ""
        if source_claim not in valid_claims:
            raise sqlite3.IntegrityError(
                f"stance file {filename} references nonexistent source claim '{source_claim}'"
            )

        stances = data.get("stances", [])
        if not isinstance(stances, list):
            raise ValueError(f"stance file {filename} has non-list 'stances'")

        for index, stance in enumerate(stances, start=1):
            if not isinstance(stance, dict):
                raise ValueError(f"stance file {filename} stance #{index} must be a mapping")
            target = resolve_claim_reference(
                stance.get("target", ""),
                claim_reference_map,
            ) or ""
            stance_type = stance.get("type", "")
            if target not in valid_claims:
                raise sqlite3.IntegrityError(
                    f"stance file {filename} references nonexistent target claim '{target}'"
                )
            if stance_type not in VALID_STANCE_TYPES:
                raise ValueError(
                    f"stance file {filename} uses unrecognized stance type '{stance_type}'"
                )

            resolution = coerce_stance_resolution(
                stance.get("resolution"),
                f"stance file {filename} stance #{index}",
            )
            conditions_differ = stance.get("conditions_differ")

            insert_claim_stance_row(
                conn,
                (
                    source_claim,
                    target,
                    stance_type,
                    stance.get("target_justification_id"),
                    stance.get("strength"),
                    conditions_differ,
                    stance.get("note"),
                    resolution.get("method"),
                    resolution.get("model"),
                    resolution.get("embedding_model"),
                    resolution.get("embedding_distance"),
                    resolution.get("pass_number"),
                    resolution.get("confidence"),
                    resolution.get("opinion_belief"),
                    resolution.get("opinion_disbelief"),
                    resolution.get("opinion_uncertainty"),
                    resolution.get("opinion_base_rate"),
                ),
            )
            count += 1
    return count


def populate_authored_justifications_from_files(
    conn: sqlite3.Connection,
    justifications_root: KnowledgePath,
) -> int:
    """Read authored justification YAML files and insert them into the sidecar."""
    if not justifications_root.exists():
        return 0

    justification_entries = [
        (entry.stem, yaml.safe_load(entry.read_bytes()) or {})
        for entry in justifications_root.iterdir()
        if entry.is_file() and entry.suffix == ".yaml"
    ]
    if not justification_entries:
        return 0

    claim_reference_map = claim_reference_map_from_conn(conn)
    valid_claims = set(claim_reference_map.values())
    count = 0

    for filename, data in justification_entries:
        justifications = data.get("justifications", [])
        if not isinstance(justifications, list):
            raise ValueError(f"justification file {filename} has non-list 'justifications'")

        for index, justification in enumerate(justifications, start=1):
            if not isinstance(justification, dict):
                raise ValueError(f"justification file {filename} entry #{index} must be a mapping")
            justification_id = justification.get("id")
            conclusion = resolve_claim_reference(
                justification.get("conclusion"),
                claim_reference_map,
            )
            premises = justification.get("premises") or []
            if not isinstance(justification_id, str) or not justification_id:
                raise ValueError(f"justification file {filename} entry #{index} missing id")
            if not isinstance(conclusion, str) or conclusion not in valid_claims:
                raise sqlite3.IntegrityError(
                    f"justification file {filename} entry #{index} references nonexistent conclusion '{conclusion}'"
                )
            if not isinstance(premises, list):
                raise ValueError(f"justification file {filename} entry #{index} premises must be a list")
            resolved_premises = [
                resolve_claim_reference(premise, claim_reference_map)
                for premise in premises
            ]
            if any(
                not isinstance(premise, str) or premise not in valid_claims
                for premise in resolved_premises
            ):
                raise sqlite3.IntegrityError(
                    f"justification file {filename} entry #{index} references nonexistent premise"
                )

            provenance = justification.get("provenance")
            attack_target = justification.get("attack_target")
            provenance_payload: dict[str, object] = {}
            if isinstance(provenance, dict):
                provenance_payload.update(provenance)
            if isinstance(attack_target, dict):
                provenance_payload["attack_target"] = attack_target

            conn.execute(
                "INSERT OR IGNORE INTO justification "
                "(id, justification_kind, conclusion_claim_id, premise_claim_ids, "
                "source_relation_type, source_claim_id, provenance_json, rule_strength) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    justification_id,
                    str(justification.get("rule_kind") or "reported_claim"),
                    conclusion,
                    json.dumps(resolved_premises),
                    None,
                    None,
                    json.dumps(provenance_payload) if provenance_payload else None,
                    str(justification.get("rule_strength") or "defeasible"),
                ),
            )
            count += 1
    return count


def populate_claims(
    conn: sqlite3.Connection,
    claim_files: Sequence[LoadedEntry],
    concept_registry: dict | None = None,
    *,
    form_registry: dict | None = None,
    semantic_bundle: ClaimCompilationBundle | None = None,
) -> None:
    """Populate normalized claim storage from authored claim files."""
    claim_seq = 0
    deferred_stances: list[tuple] = []
    reference_source = (
        list(semantic_bundle.normalized_claim_files)
        if semantic_bundle is not None
        else list(claim_files)
    )
    claim_reference_map = collect_claim_reference_map(reference_source)
    if semantic_bundle is not None:
        for semantic_file in semantic_bundle.semantic_files:
            for semantic_claim in semantic_file.claims:
                claim_seq += 1
                row = prepare_claim_insert_row(
                    semantic_claim,
                    semantic_claim.source_paper,
                    claim_seq=claim_seq,
                    concept_registry=concept_registry,
                    form_registry=form_registry,
                )
                insert_claim_row(conn, row)
                deferred_stances.extend(
                    extract_deferred_stance_rows(
                        semantic_claim,
                        claim_reference_map,
                        source_paper=semantic_claim.source_paper,
                    )
                )
    else:
        for claim_file in claim_files:
            source_paper = claim_file.data.get("source", {}).get("paper", claim_file.filename)
            for claim in claim_file.data.get("claims", []):
                claim_seq += 1
                row = prepare_claim_insert_row(
                    claim,
                    source_paper,
                    claim_seq=claim_seq,
                    concept_registry=concept_registry,
                    form_registry=form_registry,
                )
                insert_claim_row(conn, row)
                deferred_stances.extend(
                    extract_deferred_stance_rows(
                        claim,
                        claim_reference_map,
                        source_paper=source_paper,
                    )
                )

    for stance_row in deferred_stances:
        insert_claim_stance_row(conn, stance_row)


def populate_conflicts(
    conn: sqlite3.Connection,
    claim_files: Sequence[LoadedEntry],
    concept_registry: dict,
    context_hierarchy=None,
) -> None:
    from propstore.conflict_detector import detect_conflicts, detect_transitive_conflicts

    records = detect_conflicts(
        claim_files,
        concept_registry,
        context_hierarchy=context_hierarchy,
    )
    transitive_records = detect_transitive_conflicts(
        claim_files,
        concept_registry,
        context_hierarchy=context_hierarchy,
    )
    records.extend(transitive_records)
    for record in records:
        conn.execute(
            "INSERT INTO conflict_witness (concept_id, claim_a_id, claim_b_id, "
            "warning_class, conditions_a, conditions_b, value_a, value_b, "
            "derivation_chain) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                record.concept_id,
                record.claim_a_id,
                record.claim_b_id,
                record.warning_class.value,
                json.dumps(record.conditions_a),
                json.dumps(record.conditions_b),
                record.value_a,
                record.value_b,
                record.derivation_chain,
            ),
        )


def build_claim_fts_index(conn: sqlite3.Connection, claim_files: Sequence[LoadedEntry]) -> None:
    """Build the FTS5 index over claim statements, conditions, and expressions."""
    for claim_file in claim_files:
        for claim in claim_file.data.get("claims", []):
            claim_id = claim.get("artifact_id")
            if not isinstance(claim_id, str) or not claim_id:
                continue
            statement = claim.get("statement", "") or ""
            expression = claim.get("expression", "") or ""
            conditions = claim.get("conditions", []) or []
            conditions_text = " ".join(conditions)

            conn.execute(
                "INSERT INTO claim_fts (claim_id, statement, conditions, expression) "
                "VALUES (?, ?, ?, ?)",
                (claim_id, statement, conditions_text, expression),
            )
