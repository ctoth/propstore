"""Build canonical semantic graphs from existing sidecar-backed stores."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from propstore.core.environment import (
    ClaimCatalogStore,
    ClaimStanceInventoryStore,
    ConceptCatalogStore,
    ConflictStore,
    ParameterizationCatalogStore,
    RelationshipCatalogStore,
    StanceStore,
)
from propstore.core.id_types import (
    ConceptId,
    to_claim_id,
    to_concept_id,
    to_concept_ids,
)
from propstore.core.graph_types import (
    ClaimNode,
    CompiledWorldGraph,
    ConceptNode,
    ConflictWitness,
    ParameterizationEdge,
    ProvenanceRecord,
    RelationEdge,
)
from propstore.core.row_types import (
    coerce_conflict_row,
    coerce_parameterization_row,
    coerce_stance_row,
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


def _concept_attributes(row: Mapping[str, Any]) -> tuple[tuple[str, Any], ...]:
    known = {"id", "canonical_name", "status", "form", "kind_type"}
    return tuple(
        (str(key), value)
        for key, value in row.items()
        if key not in known and value is not None
    )


def _claim_attributes(row: Mapping[str, Any]) -> tuple[tuple[str, Any], ...]:
    known = {
        "id",
        "artifact_id",
        "type",
        "concept_id",
        "target_concept",
        "value",
        "source_paper",
        "provenance_page",
        "provenance_json",
        "content_hash",
        "logical_id",
        "logical_ids",
        "logical_ids_json",
        "primary_logical_id",
        "version_id",
    }
    return tuple(
        (str(key), value)
        for key, value in row.items()
        if key not in known and value is not None
    )


def _display_claim_id_from_row(row: Mapping[str, Any]) -> str:
    logical_id = row.get("logical_id") or row.get("primary_logical_id")
    if isinstance(logical_id, str) and logical_id:
        return logical_id.split(":", 1)[1] if ":" in logical_id else logical_id

    logical_ids = row.get("logical_ids")
    if isinstance(logical_ids, list):
        for entry in logical_ids:
            if not isinstance(entry, Mapping):
                continue
            value = entry.get("value")
            if isinstance(value, str) and value:
                return value

    logical_ids_json = row.get("logical_ids_json")
    if isinstance(logical_ids_json, str) and logical_ids_json:
        try:
            loaded = json.loads(logical_ids_json)
        except json.JSONDecodeError:
            loaded = []
        if isinstance(loaded, list):
            for entry in loaded:
                if not isinstance(entry, Mapping):
                    continue
                value = entry.get("value")
                if isinstance(value, str) and value:
                    return value

    return str(row["id"])


def _display_claim_id(store, claim_id: str) -> str:
    getter = getattr(store, "get_claim", None)
    if callable(getter):
        row = getter(claim_id)
        if isinstance(row, Mapping):
            return _display_claim_id_from_row(row)
    return str(claim_id)


def _relation_attributes(
    row: Mapping[str, Any],
    *,
    known: set[str],
) -> tuple[tuple[str, Any], ...]:
    return tuple(
        (str(key), value)
        for key, value in row.items()
        if key not in known and value is not None
    )


def _parse_json_list(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        loaded = json.loads(value)
        return tuple(str(item) for item in loaded)
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value)
    return tuple(str(item) for item in value)


def _parse_json_concept_ids(value: Any) -> tuple[ConceptId, ...]:
    return to_concept_ids(_parse_json_list(value))


def build_compiled_world_graph(store, *, prefer_logical_claim_ids: bool = True) -> CompiledWorldGraph:
    if not isinstance(store, ConceptCatalogStore):
        raise TypeError("build_compiled_world_graph requires all_concepts()")
    if not isinstance(store, ClaimCatalogStore):
        raise TypeError("build_compiled_world_graph requires claims_for()")
    if not isinstance(store, ParameterizationCatalogStore):
        raise TypeError("build_compiled_world_graph requires all_parameterizations()")
    if not isinstance(store, ConflictStore):
        raise TypeError("build_compiled_world_graph requires conflicts()")

    concept_rows = store.all_concepts()
    claim_rows = store.claims_for(None)
    relationship_rows = (
        store.all_relationships()
        if isinstance(store, RelationshipCatalogStore)
        else []
    )
    parameterization_rows = [
        coerce_parameterization_row(row)
        for row in store.all_parameterizations()
    ]
    conflict_rows = [
        coerce_conflict_row(row)
        for row in store.conflicts()
    ]

    if isinstance(store, ClaimStanceInventoryStore):
        claim_stance_rows = [
            coerce_stance_row(row)
            for row in store.all_claim_stances()
        ]
    elif isinstance(store, StanceStore):
        claim_ids = {
            str(row["id"])
            for row in claim_rows
            if row.get("id") is not None
        }
        claim_stance_rows = [
            coerce_stance_row(row)
            for row in store.stances_between(claim_ids)
        ]
    else:
        raise TypeError(
            "build_compiled_world_graph requires all_claim_stances() or stances_between()"
        )

    concepts = tuple(
        ConceptNode(
            concept_id=to_concept_id(row["id"]),
            canonical_name=str(row["canonical_name"]),
            status=(None if row.get("status") is None else str(row["status"])),
            form=(None if row.get("form") is None else str(row["form"])),
            kind_type=(None if row.get("kind_type") is None else str(row["kind_type"])),
            attributes=_concept_attributes(row),
        )
        for row in concept_rows
    )

    claim_display_ids = {
        str(row["id"]): (
            _display_claim_id_from_row(row)
            if prefer_logical_claim_ids
            else str(row["id"])
        )
        for row in claim_rows
        if row.get("id") is not None
    }

    claims = tuple(
        sorted(
            (
                ClaimNode(
                    claim_id=to_claim_id(claim_display_ids[str(row["id"])]),
                    concept_id=to_concept_id(row.get("concept_id") or row.get("target_concept") or ""),
                    claim_type=str(row.get("type") or "unknown"),
                    scalar_value=row.get("value"),
                    provenance=_row_provenance(
                        row,
                        source_table="claim",
                        source_id=claim_display_ids[str(row["id"])],
                    ),
                    attributes=_claim_attributes(row),
                )
                for row in claim_rows
            )
        )
    )

    concept_relationships = tuple(
        sorted(
            (
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
                for row in relationship_rows
            )
        )
    )
    claim_stances = tuple(
        sorted(
            (
                RelationEdge(
                    source_id=claim_display_ids.get(
                        stance.claim_id,
                        (
                            _display_claim_id(store, stance.claim_id)
                            if prefer_logical_claim_ids
                            else stance.claim_id
                        ),
                    ),
                    target_id=claim_display_ids.get(
                        stance.target_claim_id,
                        (
                            _display_claim_id(store, stance.target_claim_id)
                            if prefer_logical_claim_ids
                            else stance.target_claim_id
                        ),
                    ),
                    relation_type=stance.stance_type,
                    provenance=_row_provenance(
                        stance.to_dict(),
                        source_table="relation_edge",
                        source_id=(
                            f"{claim_display_ids.get(stance.claim_id, (_display_claim_id(store, stance.claim_id) if prefer_logical_claim_ids else stance.claim_id))}->"
                            f"{claim_display_ids.get(stance.target_claim_id, (_display_claim_id(store, stance.target_claim_id) if prefer_logical_claim_ids else stance.target_claim_id))}:{stance.stance_type}"
                        ),
                    ),
                    attributes=tuple(stance.attributes.items()),
                )
                for stance in claim_stance_rows
            )
        )
    )

    parameterizations = tuple(
        sorted(
            (
                ParameterizationEdge(
                    output_concept_id=parameterization.output_concept_id,
                    input_concept_ids=_parse_json_concept_ids(parameterization.concept_ids),
                    formula=parameterization.formula,
                    sympy=parameterization.sympy,
                    exactness=parameterization.exactness,
                    conditions=_parse_json_list(parameterization.conditions_cel),
                    provenance=_row_provenance(
                        {
                            **parameterization.attributes,
                            "output_concept_id": parameterization.output_concept_id,
                            "concept_ids": parameterization.concept_ids,
                            "formula": parameterization.formula,
                            "sympy": parameterization.sympy,
                            "exactness": parameterization.exactness,
                            "conditions_cel": parameterization.conditions_cel,
                        },
                        source_table="parameterization",
                        source_id=(
                            f"{parameterization.output_concept_id}:"
                            f"{parameterization.formula or parameterization.sympy or 'parameterization'}"
                        ),
                    ),
                )
                for parameterization in parameterization_rows
            )
        )
    )

    conflicts = tuple(
        sorted(
            (
                ConflictWitness(
                    left_claim_id=claim_display_ids.get(
                        conflict.claim_a_id,
                        (
                            _display_claim_id(store, conflict.claim_a_id)
                            if prefer_logical_claim_ids
                            else conflict.claim_a_id
                        ),
                    ),
                    right_claim_id=claim_display_ids.get(
                        conflict.claim_b_id,
                        (
                            _display_claim_id(store, conflict.claim_b_id)
                            if prefer_logical_claim_ids
                            else conflict.claim_b_id
                        ),
                    ),
                    kind=str(conflict.warning_class or conflict.conflict_class or "conflict"),
                    details=tuple(
                        entry
                        for entry in (
                            (
                                ("concept_id", conflict.concept_id)
                                if conflict.concept_id is not None
                                else None
                            ),
                            *tuple(conflict.attributes.items()),
                        )
                        if entry is not None
                    ),
                )
                for conflict in conflict_rows
            )
        )
    )

    return CompiledWorldGraph(
        concepts=concepts,
        claims=claims,
        relations=concept_relationships + claim_stances,
        parameterizations=parameterizations,
        conflicts=conflicts,
    )
