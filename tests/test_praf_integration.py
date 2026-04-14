"""Tests for ReasoningBackend.PRAF integration.

Phase 5B-2: PrAF integration into resolution pipeline.
Per Li et al. (2012), Jøsang (2001), Denoeux (2019).
"""

from __future__ import annotations

import pytest

from propstore.dung import ArgumentationFramework
from propstore.opinion import Opinion
from propstore.stances import StanceType


# ---------------------------------------------------------------------------
# Helpers: minimal mock store and belief space for resolution tests
# ---------------------------------------------------------------------------

class _MockStore:
    """Minimal ArtifactStore mock for PrAF integration tests."""

    def __init__(self, claims: list[dict], stances: list[dict]):
        self._claims = {c["id"]: c for c in claims}
        self._stances = stances

    def claims_by_ids(self, claim_ids: set[str]) -> dict[str, dict]:
        return {cid: self._claims[cid] for cid in claim_ids if cid in self._claims}

    def stances_between(self, claim_ids: set[str]) -> list[dict]:
        return [
            s for s in self._stances
            if s["claim_id"] in claim_ids and s["target_claim_id"] in claim_ids
        ]

    def has_table(self, name: str) -> bool:
        return name == "relation_edge"

    def claims_for(self, concept_id: str | None) -> list[dict]:
        if concept_id is None:
            return list(self._claims.values())
        return [c for c in self._claims.values() if c.get("concept_id") == concept_id]

    def get_concept(self, concept_id: str) -> dict | None:
        return None


class _MockBeliefSpace:
    """Minimal BeliefSpace mock returning conflicted claims for a concept."""

    def __init__(self, claims: list[dict]):
        self._claims = claims

    def value_of(self, concept_id: str):
        from propstore.world.types import ValueResult, ValueStatus
        matching = [c for c in self._claims if c.get("concept_id") == concept_id]
        if len(matching) == 0:
            return ValueResult(concept_id=concept_id, status=ValueStatus.NO_CLAIMS)
        if len(matching) == 1:
            return ValueResult(concept_id=concept_id, status=ValueStatus.DETERMINED, claims=matching)
        return ValueResult(concept_id=concept_id, status=ValueStatus.CONFLICTED, claims=matching)

    def active_claims(self, concept_id: str | None = None) -> list[dict]:
        if concept_id is None:
            return list(self._claims)
        return [c for c in self._claims if c.get("concept_id") == concept_id]


# ---------------------------------------------------------------------------
# Test data factories
# ---------------------------------------------------------------------------

def _make_claims_and_stances_deterministic():
    """Two claims for the same concept, one defeats the other, all opinions dogmatic.

    A rebuts B with opinion expectation ~1.0. Under grounded semantics, A wins.
    """
    claims = [
        {"id": "c1", "concept_id": "temp", "type": "parameter", "value": 100.0,
         "sample_size": 50, "provenance_json": '{"date": "2024-01-01"}'},
        {"id": "c2", "concept_id": "temp", "type": "parameter", "value": 200.0,
         "sample_size": 10, "provenance_json": '{"date": "2023-01-01"}'},
    ]
    stances = [
        {
            "claim_id": "c1", "target_claim_id": "c2",
            "stance_type": "rebuts", "confidence": 0.9,
            "opinion_belief": 0.95, "opinion_disbelief": 0.03,
            "opinion_uncertainty": 0.02, "opinion_base_rate": 0.5,
        },
    ]
    return claims, stances


def _make_claims_and_stances_uncertain():
    """Two claims, mutual attack, one with low opinion expectation.

    c1 rebuts c2 with opinion E ~ 0.3 (weak).
    c2 rebuts c1 with opinion E ~ 0.95 (strong).
    Under PrAF, c2 should often survive because c1's defeat of c2 rarely fires.
    """
    claims = [
        {"id": "c1", "concept_id": "temp", "type": "parameter", "value": 100.0,
         "sample_size": 50, "provenance_json": '{"date": "2024-01-01"}'},
        {"id": "c2", "concept_id": "temp", "type": "parameter", "value": 200.0,
         "sample_size": 10, "provenance_json": '{"date": "2023-01-01"}'},
    ]
    stances = [
        {
            "claim_id": "c1", "target_claim_id": "c2",
            "stance_type": "rebuts", "confidence": 0.3,
            "opinion_belief": 0.2, "opinion_disbelief": 0.1,
            "opinion_uncertainty": 0.7, "opinion_base_rate": 0.15,
            # E(omega) = 0.2 + 0.15 * 0.7 = 0.305
        },
        {
            "claim_id": "c2", "target_claim_id": "c1",
            "stance_type": "rebuts", "confidence": 0.95,
            "opinion_belief": 0.90, "opinion_disbelief": 0.03,
            "opinion_uncertainty": 0.07, "opinion_base_rate": 0.5,
            # E(omega) = 0.90 + 0.5 * 0.07 = 0.935
        },
    ]
    return claims, stances


# ---------------------------------------------------------------------------
# 1. test_reasoning_backend_praf_exists
# ---------------------------------------------------------------------------
def test_reasoning_backend_praf_exists():
    """ReasoningBackend.PRAF is a valid enum value."""
    from propstore.world.types import ReasoningBackend

    assert hasattr(ReasoningBackend, "PRAF")
    assert ReasoningBackend.PRAF.value == "praf"
    # Round-trip from string
    assert ReasoningBackend("praf") == ReasoningBackend.PRAF


# ---------------------------------------------------------------------------
# 2. test_render_policy_praf_defaults
# ---------------------------------------------------------------------------
def test_render_policy_praf_defaults():
    """RenderPolicy() has praf_strategy='auto', praf_mc_epsilon=0.01, etc."""
    from propstore.world.types import RenderPolicy

    policy = RenderPolicy()
    assert policy.praf_strategy == "auto"
    assert policy.praf_mc_epsilon == 0.01
    assert policy.praf_mc_confidence == 0.95
    assert policy.praf_treewidth_cutoff == 12
    assert policy.praf_mc_seed is None


# ---------------------------------------------------------------------------
# 3. test_resolved_result_acceptance_probs
# ---------------------------------------------------------------------------
def test_resolved_result_acceptance_probs():
    """ResolvedResult can carry acceptance_probs dict."""
    from propstore.world.types import ResolvedResult, ValueStatus

    result = ResolvedResult(
        concept_id="test",
        status=ValueStatus.RESOLVED,
        acceptance_probs={"c1": 0.8, "c2": 0.2},
    )
    assert result.acceptance_probs == {"c1": 0.8, "c2": 0.2}

    # Default is None
    result2 = ResolvedResult(concept_id="test", status=ValueStatus.RESOLVED)
    assert result2.acceptance_probs is None


# ---------------------------------------------------------------------------
# 4. test_resolve_praf_end_to_end
# ---------------------------------------------------------------------------
def test_resolve_praf_end_to_end():
    """End-to-end per Li et al. (2012): claims -> PrAF -> MC -> acceptance
    probabilities -> resolution."""
    from propstore.world.resolution import resolve
    from propstore.world.types import (
        ReasoningBackend,
        RenderPolicy,
        ResolutionStrategy,
    )

    claims, stances = _make_claims_and_stances_deterministic()
    store = _MockStore(claims, stances)
    view = _MockBeliefSpace(claims)

    policy = RenderPolicy(
        reasoning_backend=ReasoningBackend.PRAF,
        strategy=ResolutionStrategy.ARGUMENTATION,
        praf_mc_seed=42,
    )

    result = resolve(view, "temp", policy=policy, world=store)

    # Should produce a result with acceptance_probs populated
    assert result.acceptance_probs is not None
    assert isinstance(result.acceptance_probs, dict)
    assert "c1" in result.acceptance_probs
    assert "c2" in result.acceptance_probs
    # All probs in [0, 1]
    for prob in result.acceptance_probs.values():
        assert 0.0 <= prob <= 1.0


# ---------------------------------------------------------------------------
# 5. test_resolve_praf_deterministic_matches_claim_graph
# ---------------------------------------------------------------------------
def test_resolve_praf_deterministic_matches_claim_graph():
    """When all opinion expectations ~ 1.0, PRAF produces the same winner
    as CLAIM_GRAPH. Backward compatibility."""
    from propstore.world.resolution import resolve
    from propstore.world.types import (
        ReasoningBackend,
        RenderPolicy,
        ResolutionStrategy,
    )

    claims, stances = _make_claims_and_stances_deterministic()
    store = _MockStore(claims, stances)
    view = _MockBeliefSpace(claims)

    # CLAIM_GRAPH result
    cg_policy = RenderPolicy(
        reasoning_backend=ReasoningBackend.CLAIM_GRAPH,
        strategy=ResolutionStrategy.ARGUMENTATION,
    )
    cg_result = resolve(view, "temp", policy=cg_policy, world=store)

    # PRAF result
    praf_policy = RenderPolicy(
        reasoning_backend=ReasoningBackend.PRAF,
        strategy=ResolutionStrategy.ARGUMENTATION,
        praf_mc_seed=42,
    )
    praf_result = resolve(view, "temp", policy=praf_policy, world=store)

    # Both should pick the same winner
    assert cg_result.winning_claim_id == praf_result.winning_claim_id


# ---------------------------------------------------------------------------
# 6. test_resolve_praf_with_uncertainty_differs
# ---------------------------------------------------------------------------
def test_resolve_praf_with_uncertainty_differs():
    """When some stances have low opinion expectations (e.g., 0.3),
    PRAF may produce a different winner than CLAIM_GRAPH. This is the whole point."""
    from propstore.world.resolution import resolve
    from propstore.world.types import (
        ReasoningBackend,
        RenderPolicy,
        ResolutionStrategy,
    )

    claims, stances = _make_claims_and_stances_uncertain()
    store = _MockStore(claims, stances)
    view = _MockBeliefSpace(claims)

    # PRAF result
    praf_policy = RenderPolicy(
        reasoning_backend=ReasoningBackend.PRAF,
        strategy=ResolutionStrategy.ARGUMENTATION,
        praf_mc_seed=42,
    )
    praf_result = resolve(view, "temp", policy=praf_policy, world=store)

    assert praf_result.acceptance_probs is not None
    # With uncertain stances, acceptance probs should NOT all be 0.0 or 1.0
    probs = list(praf_result.acceptance_probs.values())
    has_fractional = any(0.0 < p < 1.0 for p in probs)
    assert has_fractional, (
        f"Expected fractional acceptance probs with uncertain stances, got {probs}"
    )


# ---------------------------------------------------------------------------
# 7. test_praf_strategy_mc_seeded
# ---------------------------------------------------------------------------
def test_praf_strategy_mc_seeded():
    """resolve() with praf_strategy='mc' and praf_mc_seed=42 produces
    deterministic results."""
    from propstore.world.resolution import resolve
    from propstore.world.types import (
        ReasoningBackend,
        RenderPolicy,
        ResolutionStrategy,
    )

    claims, stances = _make_claims_and_stances_uncertain()
    store = _MockStore(claims, stances)
    view = _MockBeliefSpace(claims)

    policy = RenderPolicy(
        reasoning_backend=ReasoningBackend.PRAF,
        strategy=ResolutionStrategy.ARGUMENTATION,
        praf_strategy="mc",
        praf_mc_seed=42,
    )

    result1 = resolve(view, "temp", policy=policy, world=store)
    result2 = resolve(view, "temp", policy=policy, world=store)

    assert result1.acceptance_probs is not None
    assert result2.acceptance_probs is not None
    assert result1.acceptance_probs == result2.acceptance_probs


# ---------------------------------------------------------------------------
# 8. test_worldline_policy_praf_roundtrip
# ---------------------------------------------------------------------------
def test_worldline_policy_praf_roundtrip():
    """RenderPolicy with praf fields serializes to dict and back without loss."""
    from propstore.world.types import ReasoningBackend, RenderPolicy, ResolutionStrategy

    policy = RenderPolicy(
        reasoning_backend=ReasoningBackend.PRAF,
        strategy=ResolutionStrategy.ARGUMENTATION,
        praf_strategy="mc",
        praf_mc_epsilon=0.005,
        praf_mc_confidence=0.99,
        praf_treewidth_cutoff=8,
        praf_mc_seed=123,
    )

    d = policy.to_dict()
    restored = RenderPolicy.from_dict(d)

    assert restored.reasoning_backend == ReasoningBackend.PRAF
    assert restored.strategy == ResolutionStrategy.ARGUMENTATION
    assert restored.praf_strategy == "mc"
    assert restored.praf_mc_epsilon == 0.005
    assert restored.praf_mc_confidence == 0.99
    assert restored.praf_treewidth_cutoff == 8
    assert restored.praf_mc_seed == 123


# ---------------------------------------------------------------------------
# 9. test_worldline_policy_backward_compat
# ---------------------------------------------------------------------------
def test_worldline_policy_backward_compat():
    """RenderPolicy.from_dict({}) uses defaults for all praf fields."""
    from propstore.world.types import RenderPolicy

    policy = RenderPolicy.from_dict({})

    assert policy.praf_strategy == "auto"
    assert policy.praf_mc_epsilon == 0.01
    assert policy.praf_mc_confidence == 0.95
    assert policy.praf_treewidth_cutoff == 12
    assert policy.praf_mc_seed is None


# ---------------------------------------------------------------------------
# 10. test_praf_strategy_dfquad_baf_dispatch
# ---------------------------------------------------------------------------
def test_praf_strategy_dfquad_baf_dispatch():
    """praf_strategy='dfquad_baf' dispatches through resolution and returns acceptance probs."""
    from propstore.world.resolution import resolve
    from propstore.world.types import (
        ReasoningBackend,
        RenderPolicy,
        ResolutionStrategy,
    )

    claims, stances = _make_claims_and_stances_deterministic()
    store = _MockStore(claims, stances)
    view = _MockBeliefSpace(claims)

    policy = RenderPolicy(
        reasoning_backend=ReasoningBackend.PRAF,
        strategy=ResolutionStrategy.ARGUMENTATION,
        praf_strategy="dfquad_baf",
    )

    result = resolve(view, "temp", policy=policy, world=store)

    # DF-QuAD should produce acceptance_probs
    assert result.acceptance_probs is not None
    assert isinstance(result.acceptance_probs, dict)
    # All probs in [0, 1]
    for prob in result.acceptance_probs.values():
        assert 0.0 <= prob <= 1.0


# ---------------------------------------------------------------------------
# 11. test_build_praf_coverage (F31)
# ---------------------------------------------------------------------------
def test_build_praf_deterministic():
    """build_praf() constructs a ProbabilisticAF from store with opinion data.

    Coverage gap from audit-praf-probabilistic.md: build_praf() had zero
    direct test coverage.  All existing tests went through the resolution
    pipeline, never calling build_praf() directly.

    Per Li et al. (2012, Def 2): PrAF = (A, P_A, D, P_D).
    """
    from propstore.praf import build_praf
    from propstore.praf import ProbabilisticAF

    claims, stances = _make_claims_and_stances_deterministic()
    store = _MockStore(claims, stances)

    praf = build_praf(store, {"c1", "c2"})

    # Type check
    assert isinstance(praf, ProbabilisticAF)

    # Arguments match the active claim IDs
    assert praf.framework.arguments == frozenset({"c1", "c2"})

    # P_A: every argument should have an Opinion
    assert set(praf.p_args.keys()) == {"c1", "c2"}
    for arg_id, opinion in praf.p_args.items():
        e = opinion.expectation()
        assert 0.0 <= e <= 1.0, f"P_A({arg_id}) expectation {e} out of range"

    # Defeats: c1 rebuts c2 with high confidence — should produce a defeat
    assert len(praf.framework.defeats) >= 1
    assert ("c1", "c2") in praf.framework.defeats

    # P_D: every defeat has an Opinion with expectation in [0, 1]
    for defeat, opinion in praf.p_defeats.items():
        e = opinion.expectation()
        assert 0.0 <= e <= 1.0, f"P_D{defeat} expectation {e} out of range"
        assert defeat in praf.framework.defeats, (
            f"P_D has key {defeat} not in framework.defeats"
        )

    # Primitive relation records preserve provenance-bearing uncertainty.
    assert len(praf.attack_relations) == 1
    attack_relation = praf.attack_relations[0]
    assert attack_relation.kind == "attack"
    assert attack_relation.edge == ("c1", "c2")
    assert attack_relation.provenance is not None
    assert attack_relation.provenance.stance_type is StanceType.REBUTS
    assert len(praf.direct_defeat_relations) == 1
    assert praf.direct_defeat_relations[0].edge == ("c1", "c2")


def test_build_praf_uncertain_defeat_probabilities():
    """build_praf() with uncertain stances produces sub-unity P_D expectations.

    When stance opinions have high uncertainty (low belief, high u),
    the defeat probability E(omega) should be fractional, not 1.0.

    Note: "rebuts" is a preference-type stance (Modgil 2018 Def 9).
    Under elitist comparison, c1 (sample_size=50) defeats c2 (sample_size=10)
    but NOT vice versa, because c2 is weaker. Both directions are *attacks*,
    but only c1->c2 is a *defeat*. We use equal sample sizes here to get
    mutual defeats for testing P_D values.
    """
    from propstore.praf import build_praf

    # Override claims with equal sample_size so both rebuts pass preference filter
    claims = [
        {"id": "c1", "concept_id": "temp", "type": "parameter", "value": 100.0,
         "sample_size": 50, "provenance_json": '{"date": "2024-01-01"}'},
        {"id": "c2", "concept_id": "temp", "type": "parameter", "value": 200.0,
         "sample_size": 50, "provenance_json": '{"date": "2023-01-01"}'},
    ]
    stances = [
        {
            "claim_id": "c1", "target_claim_id": "c2",
            "stance_type": "rebuts", "confidence": 0.3,
            "opinion_belief": 0.2, "opinion_disbelief": 0.1,
            "opinion_uncertainty": 0.7, "opinion_base_rate": 0.15,
            # E(omega) = 0.2 + 0.15 * 0.7 = 0.305
        },
        {
            "claim_id": "c2", "target_claim_id": "c1",
            "stance_type": "rebuts", "confidence": 0.95,
            "opinion_belief": 0.90, "opinion_disbelief": 0.03,
            "opinion_uncertainty": 0.07, "opinion_base_rate": 0.5,
            # E(omega) = 0.90 + 0.5 * 0.07 = 0.935
        },
    ]
    store = _MockStore(claims, stances)

    praf = build_praf(store, {"c1", "c2"})

    # Both directions should have defeats (equal strength, mutual rebuts)
    assert ("c1", "c2") in praf.framework.defeats
    assert ("c2", "c1") in praf.framework.defeats

    # c1 -> c2 defeat has low opinion (E ~ 0.305), should be fractional
    e_c1_c2 = praf.p_defeats[("c1", "c2")].expectation()
    assert 0.0 < e_c1_c2 < 1.0, (
        f"Expected fractional P_D for weak stance, got {e_c1_c2}"
    )

    # c2 -> c1 defeat has high opinion (E ~ 0.935), should be near 1.0
    e_c2_c1 = praf.p_defeats[("c2", "c1")].expectation()
    assert e_c2_c1 > 0.8, f"Expected high P_D for strong stance, got {e_c2_c1}"


def test_build_praf_no_stances():
    """build_praf() with no stances produces AF with no defeats.

    Edge case: claims exist but no stances between them.
    """
    from propstore.praf import build_praf

    claims = [
        {"id": "c1", "concept_id": "temp", "type": "parameter", "value": 100.0,
         "sample_size": 50, "provenance_json": '{"date": "2024-01-01"}'},
        {"id": "c2", "concept_id": "temp", "type": "parameter", "value": 200.0,
         "sample_size": 10, "provenance_json": '{"date": "2023-01-01"}'},
    ]
    store = _MockStore(claims, stances=[])

    praf = build_praf(store, {"c1", "c2"})

    assert praf.framework.arguments == frozenset({"c1", "c2"})
    assert len(praf.framework.defeats) == 0
    assert len(praf.p_defeats) == 0
    # P_A still populated for both arguments
    assert set(praf.p_args.keys()) == {"c1", "c2"}


def test_analyze_praf_metadata_exposes_query_kind_and_inference_mode():
    """Analyzer metadata must preserve the explicit PrAF query contract."""
    from propstore.core.analyzers import analyze_praf, shared_analyzer_input_from_store

    claims, stances = _make_claims_and_stances_uncertain()
    store = _MockStore(claims, stances)
    shared = shared_analyzer_input_from_store(store, {"c1", "c2"})

    result = analyze_praf(
        shared,
        semantics="preferred",
        strategy="exact_enum",
        query_kind="argument_acceptance",
        inference_mode="skeptical",
        target_claim_ids=("c1", "c2"),
    )

    metadata = dict(result.metadata)
    assert metadata["query_kind"] == "argument_acceptance"
    assert metadata["inference_mode"] == "skeptical"
    assert metadata["strategy_used"] == "exact_enum"


# ---------------------------------------------------------------------------
# Decision Criteria in Resolution (Phase 4 Red)
# ---------------------------------------------------------------------------

def _make_claims_and_stances_decision_criterion_tie():
    """Two claims that tie on PrAF acceptance probability but differ in opinion.

    Both claims mutually defeat each other with identical stance opinions
    (symmetric), so PrAF acceptance probabilities are equal. But the claims
    carry different opinion components (b,d,u,a) that produce different
    values under different decision criteria.

    Claim A: opinion b=0.6, d=0.1, u=0.3, a=0.5
        pignistic = 0.6 + 0.5*0.3 = 0.75
        lower_bound = 0.6
        upper_bound = 1.0 - 0.1 = 0.9

    Claim B: opinion b=0.7, d=0.2, u=0.1, a=0.5
        pignistic = 0.7 + 0.5*0.1 = 0.75
        lower_bound = 0.7
        upper_bound = 1.0 - 0.2 = 0.8

    Under pignistic: tie (both 0.75).
    Under lower_bound: B wins (0.7 > 0.6).
    Under upper_bound: A wins (0.9 > 0.8).
    Under hurwicz(alpha=1.0): same as lower_bound, B wins.

    Per Denoeux (2019, p.17-18): decision criteria determine how belief
    function uncertainty maps to actionable values.
    Per Jøsang (2001, p.5, Def 6): E(ω) = b + a·u is pignistic for binary.
    """
    # Equal sample_size so mutual rebuts both pass preference filter
    claims = [
        {"id": "cA", "concept_id": "temp", "type": "parameter", "value": 100.0,
         "sample_size": 50, "provenance_json": '{"date": "2024-01-01"}',
         "opinion_belief": 0.6, "opinion_disbelief": 0.1,
         "opinion_uncertainty": 0.3, "opinion_base_rate": 0.5},
        {"id": "cB", "concept_id": "temp", "type": "parameter", "value": 200.0,
         "sample_size": 50, "provenance_json": '{"date": "2024-01-01"}',
         "opinion_belief": 0.7, "opinion_disbelief": 0.2,
         "opinion_uncertainty": 0.1, "opinion_base_rate": 0.5},
    ]
    # Symmetric mutual defeats with identical opinions — produces a PrAF tie
    symmetric_opinion = {
        "opinion_belief": 0.8, "opinion_disbelief": 0.05,
        "opinion_uncertainty": 0.15, "opinion_base_rate": 0.5,
        "confidence": 0.9,
    }
    stances = [
        {"claim_id": "cA", "target_claim_id": "cB",
         "stance_type": "rebuts", **symmetric_opinion},
        {"claim_id": "cB", "target_claim_id": "cA",
         "stance_type": "rebuts", **symmetric_opinion},
    ]
    return claims, stances


class TestDecisionCriteriaInResolution:
    """Tests for decision criterion integration in the PrAF resolution path.

    The problem: apply_decision_criterion() is never called from the
    resolution path. The winner is always picked by bare max(acceptance_probs),
    ignoring the decision_criterion policy field.

    Per Denoeux (2019, p.17-18): decision criteria determine how belief
    function uncertainty maps to actionable values at render time.
    Per Jøsang (2001, p.5, Def 6): E(ω) = b + a·u is pignistic for binary.
    """

    def test_praf_decision_criterion_lower_bound_changes_winner(self):
        """lower_bound criterion (Bel = b) should break PrAF ties differently than pignistic.

        Claim A: b=0.6, pignistic=0.75, lower_bound=0.6
        Claim B: b=0.7, pignistic=0.75, lower_bound=0.7
        Under lower_bound: B wins (0.7 > 0.6).

        Currently fails because decision_criterion is never applied in
        _resolve_praf() — the tied acceptance probs produce CONFLICTED
        instead of using the criterion as tiebreaker.

        Per Jøsang (2001, p.4): Bel(x) = b.
        Per Denoeux (2019, p.15): lower expected utility = Bel.
        """
        from propstore.world.resolution import resolve
        from propstore.world.types import (
            ReasoningBackend,
            RenderPolicy,
            ResolutionStrategy,
            ValueStatus,
        )

        claims, stances = _make_claims_and_stances_decision_criterion_tie()
        store = _MockStore(claims, stances)
        view = _MockBeliefSpace(claims)

        policy = RenderPolicy(
            reasoning_backend=ReasoningBackend.PRAF,
            strategy=ResolutionStrategy.ARGUMENTATION,
            decision_criterion="lower_bound",
            praf_mc_seed=42,
        )
        result = resolve(view, "temp", policy=policy, world=store)

        # With lower_bound tiebreaker, B should win (0.7 > 0.6)
        assert result.status == ValueStatus.RESOLVED, (
            f"Expected RESOLVED with lower_bound tiebreaker, got {result.status}: {result.reason}"
        )
        assert result.winning_claim_id == "cB", (
            f"Expected cB to win under lower_bound (b=0.7 > 0.6), "
            f"got {result.winning_claim_id}"
        )

    def test_praf_decision_criterion_hurwicz_pessimistic(self):
        """Hurwicz at α=1.0 (fully pessimistic) should match lower_bound behavior.

        Per Denoeux (2019, p.17): Hurwicz = α·Bel + (1-α)·Pl.
        At α=1.0: Hurwicz = Bel = lower_bound.

        Claim A: Bel=0.6, Pl=0.9 → Hurwicz(1.0) = 0.6
        Claim B: Bel=0.7, Pl=0.8 → Hurwicz(1.0) = 0.7
        B wins.
        """
        from propstore.world.resolution import resolve
        from propstore.world.types import (
            ReasoningBackend,
            RenderPolicy,
            ResolutionStrategy,
            ValueStatus,
        )

        claims, stances = _make_claims_and_stances_decision_criterion_tie()
        store = _MockStore(claims, stances)
        view = _MockBeliefSpace(claims)

        policy = RenderPolicy(
            reasoning_backend=ReasoningBackend.PRAF,
            strategy=ResolutionStrategy.ARGUMENTATION,
            decision_criterion="hurwicz",
            pessimism_index=1.0,
            praf_mc_seed=42,
        )
        result = resolve(view, "temp", policy=policy, world=store)

        # Fully pessimistic Hurwicz = lower_bound; B wins (0.7 > 0.6)
        assert result.status == ValueStatus.RESOLVED, (
            f"Expected RESOLVED with hurwicz(1.0) tiebreaker, got {result.status}: {result.reason}"
        )
        assert result.winning_claim_id == "cB", (
            f"Expected cB to win under hurwicz(1.0), got {result.winning_claim_id}"
        )

    def test_praf_default_pignistic_backward_compat(self):
        """Default pignistic criterion preserves existing behavior — tied claims stay tied.

        Claim A: pignistic = 0.75
        Claim B: pignistic = 0.75
        Under pignistic: tie → CONFLICTED (same as current bare max behavior).

        This test documents the backward-compatible case: when both claims have
        equal pignistic values, the result is CONFLICTED (no arbitrary winner).
        """
        from propstore.world.resolution import resolve
        from propstore.world.types import (
            ReasoningBackend,
            RenderPolicy,
            ResolutionStrategy,
            ValueStatus,
        )

        claims, stances = _make_claims_and_stances_decision_criterion_tie()
        store = _MockStore(claims, stances)
        view = _MockBeliefSpace(claims)

        policy = RenderPolicy(
            reasoning_backend=ReasoningBackend.PRAF,
            strategy=ResolutionStrategy.ARGUMENTATION,
            # decision_criterion defaults to "pignistic"
            praf_mc_seed=42,
        )
        result = resolve(view, "temp", policy=policy, world=store)

        # Pignistic tie → CONFLICTED (no arbitrary winner selected)
        assert result.status == ValueStatus.CONFLICTED, (
            f"Expected CONFLICTED under pignistic tie, got {result.status}"
        )
        # acceptance_probs must still be populated
        assert result.acceptance_probs is not None

    def test_decision_criterion_result_carries_acceptance_probs(self):
        """ResolvedResult.acceptance_probs must be populated regardless of decision_criterion.

        Even when a decision criterion breaks a tie and produces RESOLVED,
        the raw acceptance_probs from PrAF computation must still be present
        for transparency/audit.
        """
        from propstore.world.resolution import resolve
        from propstore.world.types import (
            ReasoningBackend,
            RenderPolicy,
            ResolutionStrategy,
        )

        claims, stances = _make_claims_and_stances_decision_criterion_tie()
        store = _MockStore(claims, stances)
        view = _MockBeliefSpace(claims)

        policy = RenderPolicy(
            reasoning_backend=ReasoningBackend.PRAF,
            strategy=ResolutionStrategy.ARGUMENTATION,
            decision_criterion="lower_bound",
            praf_mc_seed=42,
        )
        result = resolve(view, "temp", policy=policy, world=store)

        # acceptance_probs must be present regardless of criterion
        assert result.acceptance_probs is not None, (
            "acceptance_probs must be populated when decision_criterion is used"
        )
        assert isinstance(result.acceptance_probs, dict)
        assert "cA" in result.acceptance_probs
        assert "cB" in result.acceptance_probs
        for prob in result.acceptance_probs.values():
            assert 0.0 <= prob <= 1.0


# ---------------------------------------------------------------------------
# Hypothesis property test: lower_bound <= pignistic <= upper_bound
# ---------------------------------------------------------------------------

class TestDecisionCriterionProperties:
    """Property-based tests for decision criterion ordering invariants.

    Per Denoeux (2019, p.15, 18): Bel <= E_BetP <= Pl,
    i.e., lower_bound <= pignistic <= upper_bound for any valid opinion.
    """

    def test_lower_bound_leq_pignistic_leq_upper_bound(self):
        """Bel(x) <= E(ω) <= Pl(x) for any valid opinion.

        Per Denoeux (2019, p.15, 18): the pignistic expected utility always
        falls within the [lower, upper] bounds defined by belief and plausibility.
        Per Jøsang (2001, p.4-5): Bel = b, Pl = 1-d, E = b + a·u.

        Uses hypothesis for exhaustive property checking.
        """
        from hypothesis import given, settings, assume
        from hypothesis import strategies as st
        from propstore.world.types import apply_decision_criterion

        @given(
            b=st.floats(min_value=0.0, max_value=1.0),
            d=st.floats(min_value=0.0, max_value=1.0),
            a=st.floats(min_value=0.0, max_value=1.0),
        )
        @settings(deadline=None)
        def _check(b, d, a):
            u = 1.0 - b - d
            assume(u >= 0.0)
            assume(u <= 1.0)

            lower = apply_decision_criterion(b, d, u, a, None, "lower_bound")
            pignistic = apply_decision_criterion(b, d, u, a, None, "pignistic")
            upper = apply_decision_criterion(b, d, u, a, None, "upper_bound")

            assert lower is not None
            assert pignistic is not None
            assert upper is not None
            assert lower <= pignistic + 1e-12, (
                f"lower_bound ({lower}) > pignistic ({pignistic}) for b={b}, d={d}, u={u}, a={a}"
            )
            assert pignistic <= upper + 1e-12, (
                f"pignistic ({pignistic}) > upper_bound ({upper}) for b={b}, d={d}, u={u}, a={a}"
            )

        _check()
