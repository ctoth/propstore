from __future__ import annotations

import pytest

from propstore.praf import build_praf
from propstore.dung import ArgumentationFramework
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.opinion import Opinion
from propstore.praf import (
    ProbabilisticAF,
    compute_praf_acceptance,
    summarize_defeat_relations,
)
from propstore.structured_projection import build_structured_projection

_EMPTY_BUNDLE = GroundedRulesBundle.empty()


class _MiniStore:
    def __init__(self, claims: list[dict], stances: list[dict]) -> None:
        self._claims = list(claims)
        self._stances = list(stances)

    def claims_for(self, concept_id: str | None = None) -> list[dict]:
        if concept_id is None:
            return list(self._claims)
        return [c for c in self._claims if c.get("concept_id") == concept_id]

    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, dict]:
        return {c["id"]: c for c in self._claims if c["id"] in claim_ids}

    def stances_between(self, claim_ids: set[str]) -> list[dict]:
        return [
            s for s in self._stances
            if s["claim_id"] in claim_ids and s["target_claim_id"] in claim_ids
        ]


def test_praf_exact_enum_respects_attack_only_edges() -> None:
    """Attack-only edges must not affect grounded acceptance without defeats."""
    fw = ArgumentationFramework(
        arguments=frozenset({"a", "b"}),
        defeats=frozenset(),
        attacks=frozenset({("a", "b")}),
    )
    praf = ProbabilisticAF(
        framework=fw,
        p_args={"a": Opinion.dogmatic_true(), "b": Opinion.dogmatic_true()},
        p_defeats={},
    )

    result = compute_praf_acceptance(
        praf,
        semantics="grounded",
        strategy="exact_enum",
    )

    assert result.acceptance_probs["a"] == pytest.approx(1.0)
    assert result.acceptance_probs["b"] == pytest.approx(1.0)


def test_praf_mc_respects_attack_only_edges_when_decomposing() -> None:
    """MC decomposition must preserve grounded defeat-only semantics."""
    fw = ArgumentationFramework(
        arguments=frozenset({"a", "b"}),
        defeats=frozenset(),
        attacks=frozenset({("a", "b")}),
    )
    praf = ProbabilisticAF(
        framework=fw,
        p_args={"a": Opinion.dogmatic_true(), "b": Opinion.dogmatic_true()},
        p_defeats={},
    )

    result = compute_praf_acceptance(
        praf,
        semantics="grounded",
        strategy="mc",
        rng_seed=42,
    )

    assert result.acceptance_probs["a"] == pytest.approx(1.0)
    assert result.acceptance_probs["b"] == pytest.approx(1.0)


def test_praf_mc_respects_support_coupling_when_decomposing() -> None:
    """Support edges still couple components because they induce Cayrol defeats."""
    store = _MiniStore(
        claims=[
            {"id": "claim_a", "concept_id": "c1", "type": "parameter", "value": 1.0},
            {"id": "claim_b", "concept_id": "c2", "type": "parameter", "value": 2.0},
            {"id": "claim_c", "concept_id": "c3", "type": "parameter", "value": 3.0},
        ],
        stances=[
            {
                "claim_id": "claim_a",
                "target_claim_id": "claim_b",
                "stance_type": "supports",
                "confidence": 1.0,
            },
            {
                "claim_id": "claim_c",
                "target_claim_id": "claim_a",
                "stance_type": "undercuts",
                "confidence": 1.0,
            },
        ],
    )

    praf = build_praf(store, {"claim_a", "claim_b", "claim_c"})
    result = compute_praf_acceptance(
        praf,
        semantics="grounded",
        strategy="mc",
        rng_seed=42,
    )

    assert result.acceptance_probs["claim_c"] == pytest.approx(1.0)
    assert result.acceptance_probs["claim_a"] == pytest.approx(0.0)
    assert result.acceptance_probs["claim_b"] == pytest.approx(0.0)


def test_praf_exact_dp_rejects_attack_only_edges() -> None:
    """The exact-DP path must fail on attack-only frameworks instead of downgrading."""
    fw = ArgumentationFramework(
        arguments=frozenset({"a", "b"}),
        defeats=frozenset(),
        attacks=frozenset({("a", "b")}),
    )
    praf = ProbabilisticAF(
        framework=fw,
        p_args={"a": Opinion.dogmatic_true(), "b": Opinion.dogmatic_true()},
        p_defeats={},
    )

    with pytest.raises(
        ValueError,
        match="exact_dp only supports grounded semantics on defeat-only probabilistic frameworks",
    ):
        compute_praf_acceptance(
            praf,
            semantics="grounded",
            strategy="exact_dp",
        )


def test_structured_projection_keeps_vacuous_attack_edges() -> None:
    """Vacuous stances should remain in the AF structure.

    Li et al.'s PrAF interpretation and the repo's claim-graph backend both
    treat vacuous opinions as uncertain edges, not as build-time exclusion
    gates. The structured projection backend should preserve the same attack.
    """
    store = _MiniStore(
        claims=[
            {"id": "claim_a", "concept_id": "c1", "type": "parameter", "value": 1.0},
            {"id": "claim_b", "concept_id": "c1", "type": "parameter", "value": 2.0},
        ],
        stances=[
            {
                "claim_id": "claim_a",
                "target_claim_id": "claim_b",
                "stance_type": "rebuts",
                "opinion_uncertainty": 1.0,
                "confidence": 0.4,
            }
        ],
    )

    projection = build_structured_projection(
        store,
        store.claims_for(None),
        bundle=_EMPTY_BUNDLE,
    )

    # Look up argument IDs by claim (bridge uses sequential IDs, not arg:claim_id)
    claim_a_args = projection.claim_to_argument_ids["claim_a"]
    claim_b_args = projection.claim_to_argument_ids["claim_b"]
    assert projection.framework.attacks is not None, "attacks relation should be populated"
    assert any(
        (a_arg, b_arg) in projection.framework.attacks
        for a_arg in claim_a_args
        for b_arg in claim_b_args
    )


def test_build_praf_keeps_direct_defeats_separate_from_derived_summaries() -> None:
    """Derived defeat marginals should be queried explicitly, not stored as inputs."""
    store = _MiniStore(
        claims=[
            {"id": "claim_a", "concept_id": "c1", "type": "parameter", "value": 1.0},
            {"id": "claim_b", "concept_id": "c2", "type": "parameter", "value": 2.0},
            {"id": "claim_c", "concept_id": "c3", "type": "parameter", "value": 3.0},
        ],
        stances=[
            {
                "claim_id": "claim_a",
                "target_claim_id": "claim_b",
                "stance_type": "supports",
                "confidence": 1.0,
            },
            {
                "claim_id": "claim_b",
                "target_claim_id": "claim_c",
                "stance_type": "undercuts",
                "opinion_belief": 0.2,
                "opinion_disbelief": 0.3,
                "opinion_uncertainty": 0.5,
                "opinion_base_rate": 0.5,
            },
        ],
    )

    praf = build_praf(store, {"claim_a", "claim_b", "claim_c"})

    assert ("claim_a", "claim_c") not in praf.p_defeats
    base = praf.p_defeats[("claim_b", "claim_c")].expectation()
    summary = {relation.edge: relation.opinion for relation in summarize_defeat_relations(praf)}
    derived = summary[("claim_a", "claim_c")].expectation()

    assert derived == pytest.approx(base)
