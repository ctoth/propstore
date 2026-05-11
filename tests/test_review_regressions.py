from __future__ import annotations

import pytest

from propstore.praf import build_praf
from argumentation.dung import ArgumentationFramework
from argumentation.probabilistic import (
    ProbabilisticAF,
    compute_probabilistic_acceptance,
)
from propstore.aspic_bridge import build_aspic_projection
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.praf import (
    summarize_defeat_relations,
)

_EMPTY_BUNDLE = GroundedRulesBundle.empty()


def _claim(claim_id: str, concept_id: str, value: float) -> dict:
    return {
        "id": claim_id,
        "concept_id": concept_id,
        "type": "parameter",
        "value": value,
        "opinion_belief": 1.0,
        "opinion_disbelief": 0.0,
        "opinion_uncertainty": 0.0,
        "opinion_base_rate": 0.5,
    }


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
        p_args={"a": 1.0, "b": 1.0},
        p_defeats={},
    )

    result = compute_probabilistic_acceptance(
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
        p_args={"a": 1.0, "b": 1.0},
        p_defeats={},
    )

    result = compute_probabilistic_acceptance(
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
            _claim("claim_a", "c1", 1.0),
            _claim("claim_b", "c2", 2.0),
            _claim("claim_c", "c3", 3.0),
        ],
        stances=[
            {
                "claim_id": "claim_a",
                "target_claim_id": "claim_b",
                "stance_type": "supports",
                "opinion_belief": 1.0,
                "opinion_disbelief": 0.0,
                "opinion_uncertainty": 0.0,
                "opinion_base_rate": 0.5,
            },
            {
                "claim_id": "claim_c",
                "target_claim_id": "claim_a",
                "stance_type": "undercuts",
                "opinion_belief": 1.0,
                "opinion_disbelief": 0.0,
                "opinion_uncertainty": 0.0,
                "opinion_base_rate": 0.5,
            },
        ],
    )

    praf = build_praf(store, {"claim_a", "claim_b", "claim_c"})
    result = compute_probabilistic_acceptance(
        praf.kernel,
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
        p_args={"a": 1.0, "b": 1.0},
        p_defeats={},
    )

    with pytest.raises(
        ValueError,
        match="exact_dp only supports grounded semantics on defeat-only probabilistic frameworks",
    ):
        compute_probabilistic_acceptance(
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
            _claim("claim_a", "c1", 1.0),
            _claim("claim_b", "c1", 2.0),
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

    projection = build_aspic_projection(
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
            _claim("claim_a", "c1", 1.0),
            _claim("claim_b", "c2", 2.0),
            _claim("claim_c", "c3", 3.0),
        ],
        stances=[
            {
                "claim_id": "claim_a",
                "target_claim_id": "claim_b",
                "stance_type": "supports",
                "opinion_belief": 1.0,
                "opinion_disbelief": 0.0,
                "opinion_uncertainty": 0.0,
                "opinion_base_rate": 0.5,
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
