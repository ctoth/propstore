from __future__ import annotations

import ast
import json
from pathlib import Path

from propstore.argumentation import build_argumentation_framework
from propstore.structured_argument import SupportQuality, build_structured_projection
from tests.test_revision_bound_world import _operator_bound
from tests.test_revision_phase1 import _RevisionStore, _make_bound


def test_project_epistemic_state_builds_claim_graph_inputs_over_accepted_claims() -> None:
    from propstore.revision.af_adapter import project_epistemic_state_argumentation_view

    bound = _operator_bound()
    _, state = bound.iterated_revise(
        {"kind": "claim", "id": "synthetic", "value": 9.0},
        conflicts={"claim:synthetic": ("legacy",)},
        operator="restrained",
    )

    view = project_epistemic_state_argumentation_view(bound._store, state)
    claim_rows = view.store.claims_by_ids(set(view.active_claim_ids))
    af = build_argumentation_framework(view.store, set(view.active_claim_ids))

    assert "legacy" not in view.active_claim_ids
    assert "dependent" not in view.active_claim_ids
    assert "independent" in view.active_claim_ids
    assert "synthetic" in view.active_claim_ids
    assert claim_rows["synthetic"]["value"] == 9.0
    assert af.arguments == frozenset(view.active_claim_ids)


def test_project_epistemic_state_builds_structured_inputs_with_exact_support_metadata() -> None:
    from propstore.revision.af_adapter import project_epistemic_state_argumentation_view

    store = _RevisionStore(
        claims=[
            {
                "id": "claim_exact",
                "concept_id": "concept_exact",
                "type": "parameter",
                "value": 1.0,
                "conditions_cel": json.dumps(["x == 1"]),
            }
        ],
    )
    bound = _make_bound(store, bindings={"x": 1})
    state = bound.epistemic_state()

    view = project_epistemic_state_argumentation_view(bound._store, state)
    projection = build_structured_projection(
        view.store,
        list(view.active_claims),
        support_metadata=dict(view.support_metadata),
    )
    argument = next(arg for arg in projection.arguments if arg.claim_id == "claim_exact")

    assert set(view.active_claim_ids) == {"claim_exact"}
    assert {claim["id"] for claim in view.active_claims} == {"claim_exact"}
    assert view.support_metadata["claim_exact"][1] is SupportQuality.EXACT
    assert argument.support_quality is SupportQuality.EXACT
    assert argument.label == view.support_metadata["claim_exact"][0]


def test_revision_af_adapter_does_not_import_ic_merge() -> None:
    path = Path("propstore/revision/af_adapter.py")
    assert path.exists()

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
    assert "propstore.repo.ic_merge" not in imports
