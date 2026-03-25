from __future__ import annotations

import pytest

from propstore.argumentation import build_praf
from propstore.dung import ArgumentationFramework
from propstore.opinion import Opinion
from propstore.praf import ProbabilisticAF, compute_praf_acceptance
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
    """Attack-only edges must still constrain grounded acceptance.

    Modgil & Prakken 2018 use attack-based conflict-free semantics. If an
    attack survives in ``framework.attacks`` but not in ``framework.defeats``,
    exact probabilistic evaluation still has to preserve that attack relation.
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

    assert result.acceptance_probs["a"] == pytest.approx(1.0)
    assert result.acceptance_probs["b"] == pytest.approx(0.0)


def test_praf_mc_respects_attack_only_edges_when_decomposing() -> None:
    """MC decomposition must not separate components connected only by attacks.

    Hunter & Thimm's separability result applies to the graph relevant to the
    semantics. Under attack-based conflict-free semantics, an attack-only edge
    still couples the two arguments and cannot be dropped for component
    decomposition.
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

    assert result.acceptance_probs["a"] == pytest.approx(1.0)
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
    """The exact-DP path must preserve attack-only semantics, even via fallback."""
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

    assert result.acceptance_probs["a"] == pytest.approx(1.0)
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


def test_build_praf_does_not_make_derived_defeats_certain() -> None:
    """Derived defeats should inherit uncertainty from the generating chain.

    A Cayrol supported defeat exists only when the underlying defeating edge
    exists. Promoting the derived defeat to certainty overstates the support
    chain and distorts Li-style probabilistic semantics.
    """
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

    base = praf.p_defeats[("claim_b", "claim_c")].expectation()
    derived = praf.p_defeats[("claim_a", "claim_c")].expectation()

    assert derived == pytest.approx(base)
