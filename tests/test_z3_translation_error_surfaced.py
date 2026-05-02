from __future__ import annotations

from propstore.merge import merge_classifier
from propstore.core.conditions.solver import Z3TranslationError
from tests.ws_l_merge_helpers import merge_claim_from_payload, param_claim


def test_z3_translation_error_is_not_relabelled_as_phi_node(monkeypatch) -> None:
    def raise_translation_error(claims, concept_registry, cel_registry):
        raise Z3TranslationError("cannot translate condition")

    monkeypatch.setattr(
        "propstore.conflict_detector.detect_conflicts",
        raise_translation_error,
    )
    left = merge_claim_from_payload(
        param_claim("left", "concept_x", 1.0, conditions=["T < 100"]),
    )
    right = merge_claim_from_payload(
        param_claim("right", "concept_x", 2.0, conditions=["T >= 100"]),
    )

    assert merge_classifier._classify_pair(left, right) is merge_classifier._DiffKind.UNTRANSLATABLE
