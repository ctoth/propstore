"""Support-revision to argumentation adapter tests."""

from __future__ import annotations

import ast
from pathlib import Path

from propstore.aspic_bridge import build_aspic_projection
from propstore.core.labels import SupportQuality
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.support_revision.af_adapter import (
    project_epistemic_state_argumentation_view,
)
from tests.atms_feed import ClaimSpec, build_bound

_EMPTY_BUNDLE = GroundedRulesBundle.empty()


def test_project_epistemic_state_builds_structured_inputs_with_exact_support_metadata() -> None:
    bound = build_bound(
        claims=[ClaimSpec("claim_exact", "concept_exact", value=1.0, conditions=("x == 1",))],
        bindings={"x": 1},
    )
    state = bound.epistemic_state()

    view = project_epistemic_state_argumentation_view(bound._store, state)
    projection = build_aspic_projection(
        view.store,
        list(view.active_claims),
        bundle=_EMPTY_BUNDLE,
        support_metadata=dict(view.support_metadata),
    )
    argument = next(arg for arg in projection.arguments if arg.claim_id == "claim_exact")

    assert set(view.active_claim_ids) == {"claim_exact"}
    assert {str(claim.claim_id) for claim in view.active_claims} == {"claim_exact"}
    assert view.support_metadata["claim_exact"][1] is SupportQuality.EXACT
    assert argument.support_quality is SupportQuality.EXACT
    assert argument.label == view.support_metadata["claim_exact"][0]


def test_revision_af_adapter_does_not_import_belief_set_or_ic_merge() -> None:
    path = Path("propstore/support_revision/af_adapter.py")
    assert path.exists()

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
    assert "propstore.storage.ic_merge" not in imports
    assert all("belief_set" not in module for module in imports)
