from __future__ import annotations

import json
import sqlite3

from propstore.context_lifting import (
    IstProposition,
    LiftingException,
    LiftingMaterializationStatus,
    LiftingRule,
    LiftingSystem,
)
from propstore.core.assertions import ContextReference
from propstore.sidecar.passes import compile_context_lifting_materialization_rows
from propstore.sidecar.schema import create_context_tables, populate_contexts
from propstore.sidecar.stages import ContextSidecarRows


def test_lifting_materializes_ist_assertion_with_rule_provenance() -> None:
    source = ContextReference("ctx_source")
    target = ContextReference("ctx_target")
    system = LiftingSystem(
        contexts=(source, target),
        lifting_rules=(
            LiftingRule(
                id="lift-source-target",
                source=source,
                target=target,
                justification="Guha DCR-T bridge",
            ),
        ),
    )

    materializations = system.materialize_lifted_assertions(
        (IstProposition(context=source, proposition_id="claim_alpha"),)
    )

    assert len(materializations) == 1
    lifted = materializations[0]
    assert lifted.status is LiftingMaterializationStatus.LIFTED
    assert lifted.assertion == IstProposition(
        context=target,
        proposition_id="claim_alpha",
    )
    assert lifted.source_assertion == IstProposition(
        context=source,
        proposition_id="claim_alpha",
    )
    assert lifted.rule_id == "lift-source-target"
    assert lifted.provenance.items() >= {
        "rule_id": "lift-source-target",
        "source_context_id": "ctx_source",
        "target_context_id": "ctx_target",
        "source_proposition_id": "claim_alpha",
        "status": "lifted",
    }.items()
    assert lifted.provenance["justification"] == "Guha DCR-T bridge"


def test_lifting_exception_is_local_and_blocks_only_matching_target() -> None:
    source = ContextReference("ctx_source")
    target = ContextReference("ctx_target")
    sibling = ContextReference("ctx_sibling")
    system = LiftingSystem(
        contexts=(source, target, sibling),
        lifting_rules=(
            LiftingRule(id="lift-source-target", source=source, target=target),
            LiftingRule(id="lift-source-sibling", source=source, target=sibling),
        ),
        lifting_exceptions=(
            LiftingException(
                id="except-target-alpha",
                rule_id="lift-source-target",
                target=target,
                proposition_id="claim_alpha",
                clashing_set=("ctx_target:claim_beta",),
                justification="local target clashing set",
            ),
        ),
    )

    materializations = system.materialize_lifted_assertions(
        (IstProposition(context=source, proposition_id="claim_alpha"),)
    )

    by_target = {
        str(item.target_context.id): item
        for item in materializations
    }
    assert by_target["ctx_target"].status is LiftingMaterializationStatus.BLOCKED
    assert by_target["ctx_target"].exception_id == "except-target-alpha"
    assert by_target["ctx_sibling"].status is LiftingMaterializationStatus.LIFTED


def test_sidecar_stores_lifting_materialization_provenance() -> None:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    create_context_tables(conn)

    source = ContextReference("ctx_source")
    target = ContextReference("ctx_target")
    system = LiftingSystem(
        contexts=(source, target),
        lifting_rules=(
            LiftingRule(id="lift-source-target", source=source, target=target),
        ),
    )
    materializations = system.materialize_lifted_assertions(
        (IstProposition(context=source, proposition_id="claim_alpha"),)
    )
    materialization_rows = compile_context_lifting_materialization_rows(
        materializations
    )

    populate_contexts(
        conn,
        ContextSidecarRows(
            context_rows=(),
            assumption_rows=(),
            lifting_rule_rows=(),
            lifting_materialization_rows=materialization_rows,
        ),
    )

    row = conn.execute(
        "SELECT * FROM context_lifting_materialization"
    ).fetchone()
    assert row["rule_id"] == "lift-source-target"
    assert row["source_context_id"] == "ctx_source"
    assert row["target_context_id"] == "ctx_target"
    assert row["proposition_id"] == "claim_alpha"
    assert row["status"] == "lifted"
    assert json.loads(row["provenance_json"])["source_proposition_id"] == "claim_alpha"
