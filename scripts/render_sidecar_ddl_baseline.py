from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from quire.projections import FtsProjection, ProjectionTable, VecProjection, projection_name
from propstore.families.projection_catalog import PROPSTORE_WORLD_PROJECTION_SCHEMA


def projection_kind(projection: object) -> str:
    if isinstance(projection, ProjectionTable):
        return "table"
    if isinstance(projection, FtsProjection):
        return "fts5"
    if isinstance(projection, VecProjection):
        return "vec0"
    return type(projection).__name__


def projection_record(
    projection: object,
    *,
    bindings: dict[str, str],
) -> dict[str, Any]:
    if not isinstance(projection, (ProjectionTable, FtsProjection, VecProjection)):
        raise TypeError(f"unsupported projection: {type(projection).__name__}")

    name = projection_name(projection)
    ddl = projection.ddl_statements(bindings)
    record: dict[str, Any] = {
        "name": name,
        "rendered_name": projection.projection_name(bindings),
        "kind": projection_kind(projection),
        "columns": projection.column_names,
        "ddl": ddl,
        "schema_hash_material": projection.schema_hash_material(),
    }
    if isinstance(projection, FtsProjection):
        record["population_plan"] = projection.population_plan()
        if projection.source_query is not None:
            record["population_sql"] = projection.population_sql(bindings)
    if isinstance(projection, (ProjectionTable, FtsProjection, VecProjection)):
        record["insert_sql"] = projection.insert_sql(bindings=bindings)
    if isinstance(projection, VecProjection):
        record["insert_rowid_sql"] = projection.insert_rowid_sql(bindings)
        record["delete_rowid_sql"] = projection.delete_rowid_sql(bindings)
        record["search_sql"] = projection.search_sql(bindings=bindings)
    return record


def build_baseline(*, model_identity_hash: str, dimensions: int) -> dict[str, Any]:
    bindings = {
        "model_identity_hash": model_identity_hash,
        "dimensions": str(dimensions),
    }
    projections = [
        projection_record(projection, bindings=bindings)
        for projection in PROPSTORE_WORLD_PROJECTION_SCHEMA.projections
    ]
    return {
        "schema_version": 1,
        "bindings": bindings,
        "schema_metadata": dict(PROPSTORE_WORLD_PROJECTION_SCHEMA.metadata),
        "schema_hash_material": PROPSTORE_WORLD_PROJECTION_SCHEMA.schema_hash_material(),
        "ddl_statements": PROPSTORE_WORLD_PROJECTION_SCHEMA.ddl_statements(bindings),
        "catalog": projections,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the sidecar DDL baseline.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model-identity-hash", default="baseline_model")
    parser.add_argument("--dimensions", type=int, default=3)
    args = parser.parse_args()

    baseline = build_baseline(
        model_identity_hash=args.model_identity_hash,
        dimensions=args.dimensions,
    )
    text = json.dumps(baseline, indent=2, sort_keys=True)
    if args.output is None:
        print(text)
    else:
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
