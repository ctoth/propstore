from __future__ import annotations

import pytest

from propstore.argumentation import build_praf
from propstore.dung import ArgumentationFramework
from propstore.opinion import Opinion
from propstore.praf import (
    ProbabilisticAF,
    compute_praf_acceptance,
    summarize_defeat_relations,
)
from propstore.structured_argument import build_structured_projection


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
    """Attack-only edges must not create a fake grounded winner.

    If an edge exists only in ``framework.attacks`` and no complete extension
    survives under the hybrid semantics, probabilistic grounded evaluation
    must stay skeptical instead of promoting the attacker.
    """
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

    assert result.acceptance_probs["a"] == pytest.approx(0.0)
    assert result.acceptance_probs["b"] == pytest.approx(0.0)


def test_praf_mc_respects_attack_only_edges_when_decomposing() -> None:
    """MC decomposition must preserve skeptical attack-only grounded behavior.

    Components connected only by attacks still interact under the grounded
    semantics used here, so decomposition must not turn an attack-only pair
    into an artificial winner.
    """
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

    assert result.acceptance_probs["a"] == pytest.approx(0.0)
    assert result.acceptance_probs["b"] == pytest.approx(0.0)


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


def test_praf_exact_dp_respects_attack_only_edges_via_fallback() -> None:
    """The exact-DP path must preserve skeptical attack-only semantics."""
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
        strategy="exact_dp",
    )

    assert result.acceptance_probs["a"] == pytest.approx(0.0)
    assert result.acceptance_probs["b"] == pytest.approx(0.0)


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

    projection = build_structured_projection(store, store.claims_for(None))

    assert ("arg:claim_a", "arg:claim_b") in projection.framework.attacks


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
