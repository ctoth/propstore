"""Build canonical semantic graphs from existing sidecar-backed stores."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from propstore.core.graph_types import (
    ClaimNode,
    CompiledWorldGraph,
    ConceptNode,
    ConflictWitness,
    ParameterizationEdge,
    ProvenanceRecord,
    RelationEdge,
)


def _row_provenance(
    row: Mapping[str, Any],
    *,
    source_table: str,
    source_id: str | None = None,
) -> ProvenanceRecord | None:
    if source_table == "claim":
        provenance_json = row.get("provenance_json")
        extras: dict[str, Any] = {}
        if provenance_json:
            try:
                loaded = json.loads(provenance_json)
                if isinstance(loaded, dict):
                    extras.update(loaded)
            except json.JSONDecodeError:
                extras["provenance_json"] = provenance_json
        if row.get("source_paper") is not None:
            extras.setdefault("paper", row.get("source_paper"))
        if row.get("provenance_page") is not None:
            extras.setdefault("page", row.get("provenance_page"))
        extras["source_table"] = source_table
        extras["source_id"] = source_id or row.get("id")
        return ProvenanceRecord.from_mapping(extras)

    extras = dict(row)
    extras["source_table"] = source_table
    if source_id is not None:
        extras["source_id"] = source_id
    return ProvenanceRecord.from_mapping(extras)


def _concept_attributes(row: Mapping[str, Any]) -> dict[str, Any]:
    known = {"id", "canonical_name", "status", "form", "kind_type"}
    return {
        str(key): value
        for key, value in row.items()
        if key not in known and value is not None
    }


def _claim_attributes(row: Mapping[str, Any]) -> dict[str, Any]:
    known = {
        "id",
        "type",
        "concept_id",
        "target_concept",
        "value",
        "source_paper",
        "provenance_page",
        "provenance_json",
    }
    return {
        str(key): value
        for key, value in row.items()
        if key not in known and value is not None
    }


def _relation_attributes(row: Mapping[str, Any], *, known: set[str]) -> dict[str, Any]:
    return {
        str(key): value
        for key, value in row.items()
        if key not in known and value is not None
    }


def _parse_json_list(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        loaded = json.loads(value)
        return tuple(str(item) for item in loaded)
    return tuple(str(item) for item in value)


def build_compiled_world_graph(store) -> CompiledWorldGraph:
    concepts = tuple(
        ConceptNode(
            concept_id=str(row["id"]),
            canonical_name=str(row["canonical_name"]),
            status=(None if row.get("status") is None else str(row["status"])),
            form=(None if row.get("form") is None else str(row["form"])),
            kind_type=(None if row.get("kind_type") is None else str(row["kind_type"])),
            attributes=_concept_attributes(row),
        )
        for row in store.all_concepts()
    )

    claims = tuple(
        ClaimNode(
            claim_id=str(row["id"]),
            concept_id=str(row.get("concept_id") or row.get("target_concept") or ""),
            claim_type=str(row.get("type") or "unknown"),
            scalar_value=row.get("value"),
            provenance=_row_provenance(row, source_table="claim", source_id=str(row["id"])),
            attributes=_claim_attributes(row),
        )
        for row in store.claims_for(None)
    )

    concept_relationships = tuple(
        RelationEdge(
            source_id=str(row["source_id"]),
            target_id=str(row["target_id"]),
            relation_type=str(row["type"]),
            provenance=_row_provenance(
                row,
                source_table="relationship",
                source_id=f"{row['source_id']}->{row['target_id']}:{row['type']}",
            ),
            attributes=_relation_attributes(row, known={"source_id", "target_id", "type"}),
        )
        for row in store.all_relationships()
    )
    claim_stances = tuple(
        RelationEdge(
            source_id=str(row["claim_id"]),
            target_id=str(row["target_claim_id"]),
            relation_type=str(row["stance_type"]),
            provenance=_row_provenance(
                row,
                source_table="claim_stance",
                source_id=f"{row['claim_id']}->{row['target_claim_id']}:{row['stance_type']}",
            ),
            attributes=_relation_attributes(
                row,
                known={"claim_id", "target_claim_id", "stance_type"},
            ),
        )
        for row in store.all_claim_stances()
    )

    parameterizations = tuple(
        ParameterizationEdge(
            output_concept_id=str(row["output_concept_id"]),
            input_concept_ids=_parse_json_list(row.get("concept_ids")),
            formula=(None if row.get("formula") is None else str(row["formula"])),
            sympy=(None if row.get("sympy") is None else str(row["sympy"])),
            exactness=(None if row.get("exactness") is None else str(row["exactness"])),
            conditions=_parse_json_list(row.get("conditions_cel")),
            provenance=_row_provenance(
                row,
                source_table="parameterization",
                source_id=f"{row['output_concept_id']}:{row.get('formula') or row.get('sympy') or 'parameterization'}",
            ),
        )
        for row in store.all_parameterizations()
    )

    conflicts = tuple(
        ConflictWitness(
            left_claim_id=str(row["claim_a_id"]),
            right_claim_id=str(row["claim_b_id"]),
            kind=str(row.get("warning_class") or row.get("conflict_class") or "conflict"),
            details={
                str(key): value
                for key, value in row.items()
                if key not in {"claim_a_id", "claim_b_id", "warning_class", "conflict_class"} and value is not None
            },
        )
        for row in store.conflicts()
        if row.get("claim_a_id") is not None and row.get("claim_b_id") is not None
    )

    return CompiledWorldGraph(
        concepts=concepts,
        claims=claims,
        relations=concept_relationships + claim_stances,
        parameterizations=parameterizations,
        conflicts=conflicts,
    )
