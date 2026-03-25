"""Tests for ReasoningBackend.PRAF integration.

Phase 5B-2: PrAF integration into resolution pipeline.
Per Li et al. (2012), Jøsang (2001), Denoeux (2019).
"""

from __future__ import annotations

import pytest

from propstore.dung import ArgumentationFramework
from propstore.opinion import Opinion


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
        return name == "claim_stance"

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
    """WorldlinePolicy with praf fields serializes to dict and back without loss."""
    from propstore.worldline import WorldlinePolicy

    policy = WorldlinePolicy(
        reasoning_backend="praf",
        strategy="argumentation",
        praf_strategy="mc",
        praf_mc_epsilon=0.005,
        praf_mc_confidence=0.99,
        praf_treewidth_cutoff=8,
        praf_mc_seed=123,
    )

    d = policy.to_dict()
    restored = WorldlinePolicy.from_dict(d)

    assert restored.reasoning_backend == "praf"
    assert restored.praf_strategy == "mc"
    assert restored.praf_mc_epsilon == 0.005
    assert restored.praf_mc_confidence == 0.99
    assert restored.praf_treewidth_cutoff == 8
    assert restored.praf_mc_seed == 123


# ---------------------------------------------------------------------------
# 9. test_worldline_policy_backward_compat
# ---------------------------------------------------------------------------
def test_worldline_policy_backward_compat():
    """WorldlinePolicy.from_dict({}) uses defaults for all praf fields."""
    from propstore.worldline import WorldlinePolicy

    policy = WorldlinePolicy.from_dict({})

    assert policy.praf_strategy == "auto"
    assert policy.praf_mc_epsilon == 0.01
    assert policy.praf_mc_confidence == 0.95
    assert policy.praf_treewidth_cutoff == 12
    assert policy.praf_mc_seed is None


# ---------------------------------------------------------------------------
# 10. test_praf_strategy_dfquad_dispatch
# ---------------------------------------------------------------------------
def test_praf_strategy_dfquad_dispatch():
    """praf_strategy='dfquad' dispatches through resolution and returns acceptance probs."""
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
        praf_strategy="dfquad",
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
    from propstore.argumentation import build_praf
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
    from propstore.argumentation import build_praf

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
    from propstore.argumentation import build_praf

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
