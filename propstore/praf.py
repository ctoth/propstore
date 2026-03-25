"""Probabilistic argumentation over primitive relation worlds.

This module keeps uncertainty on primitive arguments, attacks, and supports,
then realizes semantic AFs per sampled world. Direct defeats are primitive
semantic relations; Cayrol derived defeats are world-derived consequences.

Monte Carlo uses Agresti-Coull stopping per Li et al. (2012, Algorithm 1).
Connected component decomposition follows Hunter & Thimm (2017, Prop 18)
over the primitive semantic dependency graph.
"""

from __future__ import annotations

import math

_Z_SCORES = {0.90: 1.645, 0.95: 1.960, 0.99: 2.576}


def _z_for_confidence(confidence: float) -> float:
    """Z-score for two-tailed confidence interval."""
    if confidence in _Z_SCORES:
        return _Z_SCORES[confidence]
    raise ValueError(f"Unsupported mc_confidence={confidence}; use 0.90, 0.95, or 0.99")
import random as _random_mod
from dataclasses import dataclass

from propstore.dung import (
    ArgumentationFramework,
    complete_extensions,
    grounded_extension,
    preferred_extensions,
    stable_extensions,
)
from propstore.opinion import Opinion, W, from_probability
from propstore.probabilistic_relations import (
    ProbabilisticRelation,
    relation_from_row,
)

# Threshold for treating P_D as deterministic (all defeats certain).
_DETERMINISTIC_THRESHOLD = 0.999


@dataclass(frozen=True)
class ProbabilisticAF:
    """Probabilistic AF with primitive-relation uncertainty.

    framework: the semantic AF envelope used for deterministic evaluation.
    p_args: dict[str, Opinion] — P_A per argument (existence probability).
    p_defeats: dict[tuple[str, str], Opinion] — direct defeat probabilities only.
    p_attacks: optional primitive attack probabilities when attacks and defeats differ.
    supports / p_supports: optional primitive support relations with existence probabilities.
    base_defeats: optional direct defeats before Cayrol closure; defaults to framework.defeats.
    attack_relations / support_relations / direct_defeat_relations preserve
    provenance-bearing primitive relation records.

    The MC sampler uses Opinion.expectation() (Jøsang 2001, Def 6: E(ω) = b + a·u)
    as the sampling probability for each element.
    """

    framework: ArgumentationFramework
    p_args: dict[str, Opinion]
    p_defeats: dict[tuple[str, str], Opinion]
    p_attacks: dict[tuple[str, str], Opinion] | None = None
    supports: frozenset[tuple[str, str]] = frozenset()
    p_supports: dict[tuple[str, str], Opinion] | None = None
    base_defeats: frozenset[tuple[str, str]] | None = None
    attack_relations: tuple[ProbabilisticRelation, ...] = ()
    support_relations: tuple[ProbabilisticRelation, ...] = ()
    direct_defeat_relations: tuple[ProbabilisticRelation, ...] = ()


@dataclass(frozen=True)
class PrAFResult:
    """Result of probabilistic extension computation.

    acceptance_probs: argument -> P(accepted), computed over all sampled worlds.
    strategy_used: "mc", "deterministic", "exact_enum".
    samples: MC sample count (None for non-MC strategies).
    confidence_interval_half: MC CI half-width (None for non-MC).
    semantics: which Dung semantics was used.
    """

    acceptance_probs: dict[str, float]
    strategy_used: str
    samples: int | None
    confidence_interval_half: float | None
    semantics: str


def p_arg_from_claim(claim: dict) -> Opinion:
    """Hook: derive P_A from a claim dict.

    Default: Opinion.dogmatic_true() — all active claims exist with certainty.
    Per Li et al. (2012, p.2): P_A(a) = probability that argument a exists.
    For active claims (already condition-filtered), existence is certain.
    """
    return Opinion.dogmatic_true()


def p_relation_from_stance(stance: dict) -> Opinion:
    """Derive an edge-existence opinion from a stance's opinion columns.

    Fallback chain per phase5b plan:
    1. Opinion columns (b, d, u, a) → Opinion(b, d, u, a)
    2. Confidence float → from_probability(confidence, 1)
    3. No data → Opinion.dogmatic_true() (backward compat)

    Per Jøsang (2001, Def 6): E(ω) = b + a·u provides the sampling probability.
    """
    b = stance.get("opinion_belief")
    d = stance.get("opinion_disbelief")
    u = stance.get("opinion_uncertainty")
    a = stance.get("opinion_base_rate", 0.5)

    if b is not None and d is not None and u is not None:
        return Opinion(b, d, u, a)

    confidence = stance.get("confidence")
    if confidence is not None:
        if confidence >= 1.0 - 1e-12:
            return Opinion.dogmatic_true(a)
        if confidence <= 1e-12:
            return Opinion.dogmatic_false(a)
        # from_probability(p, n) with n=1 gives moderate uncertainty.
        return from_probability(confidence, 1)

    # No opinion or confidence data — certain defeat (backward compat).
    return Opinion.dogmatic_true()


def p_defeat_from_stance(stance: dict) -> Opinion:
    """Backward-compatible alias for relation-existence opinions."""
    return p_relation_from_stance(stance)


def enforce_coh(praf: ProbabilisticAF) -> ProbabilisticAF:
    """Enforce COH rationality postulate on argument existence probabilities.

    Per Hunter & Thimm (2017, p.9): for every attack (A, B) in the AF,
    P(A) + P(B) <= 1.  Self-attacks imply P(A) <= 0.5.

    Algorithm: iterative proportional scaling.  For each violating attack pair
    (A, B) where E(A) + E(B) > 1.0, scale both expectations proportionally so
    their sum equals 1.0, then rebuild opinions preserving evidence counts.

    Returns a new ProbabilisticAF with adjusted p_args.  p_defeats are unchanged
    (COH constrains P_A, not P_D).
    """
    attacks = praf.framework.attacks if praf.framework.attacks is not None else praf.framework.defeats

    # Work with mutable copy of expectations and evidence counts
    expectations: dict[str, float] = {}
    evidence_n: dict[str, float] = {}
    base_rates: dict[str, float] = {}

    for arg, op in praf.p_args.items():
        expectations[arg] = op.expectation()
        base_rates[arg] = op.a
        # Recover evidence count n from uncertainty: u = W / (r + s + W) = W / (n + W)
        # so n = W/u - W = W * (1/u - 1).  For dogmatic opinions (u~0), use default.
        if op.u > 1e-9:
            evidence_n[arg] = W * (1.0 / op.u - 1.0)
        else:
            evidence_n[arg] = 10.0  # default for dogmatic opinions

    changed = False
    max_iterations = 100
    for _ in range(max_iterations):
        any_violation = False
        for src, tgt in attacks:
            if src == tgt:
                # Self-attack: P(A) + P(A) <= 1 => P(A) <= 0.5
                if expectations[src] > 0.5 + 1e-12:
                    expectations[src] = 0.5
                    any_violation = True
                    changed = True
            else:
                total = expectations[src] + expectations[tgt]
                if total > 1.0 + 1e-12:
                    factor = 1.0 / total
                    expectations[src] *= factor
                    expectations[tgt] *= factor
                    any_violation = True
                    changed = True
        if not any_violation:
            break

    if not changed:
        return praf

    # Rebuild opinions from adjusted expectations.
    # from_probability(p, n, a) yields E = (p*n + a*W)/(n+W), not E = p.
    # Invert: p = (E_target*(n+W) - a*W) / n  to hit the desired expectation.
    new_p_args: dict[str, Opinion] = {}
    for arg in praf.p_args:
        if abs(expectations[arg] - praf.p_args[arg].expectation()) < 1e-12:
            # Unchanged — keep original opinion
            new_p_args[arg] = praf.p_args[arg]
        else:
            n = evidence_n[arg]
            a = base_rates[arg]
            e_target = expectations[arg]
            # Solve for p: E = (p*n + a*W)/(n+W) => p = (E*(n+W) - a*W)/n
            p = (e_target * (n + W) - a * W) / n if n > 1e-12 else e_target
            # Clamp to valid range
            p = max(0.0, min(1.0, p))
            new_p_args[arg] = from_probability(p, n, a)

    return ProbabilisticAF(
        framework=praf.framework,
        p_args=new_p_args,
        p_defeats=praf.p_defeats,
        p_attacks=praf.p_attacks,
        supports=praf.supports,
        p_supports=praf.p_supports,
        base_defeats=praf.base_defeats,
        attack_relations=praf.attack_relations,
        support_relations=praf.support_relations,
        direct_defeat_relations=praf.direct_defeat_relations,
    )


def _is_deterministic_opinion(opinion: Opinion | None) -> bool:
    if opinion is None:
        return True
    expectation = opinion.expectation()
    return (
        expectation >= _DETERMINISTIC_THRESHOLD
        or expectation <= (1.0 - _DETERMINISTIC_THRESHOLD)
    )


def _edge_is_present(opinion: Opinion | None) -> bool:
    if opinion is None:
        return True
    return opinion.expectation() >= _DETERMINISTIC_THRESHOLD


def _primitive_attacks(praf: ProbabilisticAF) -> frozenset[tuple[str, str]]:
    if praf.framework.attacks is not None:
        return praf.framework.attacks
    return praf.framework.defeats


def _direct_defeats(praf: ProbabilisticAF) -> frozenset[tuple[str, str]]:
    if praf.base_defeats is not None:
        return praf.base_defeats
    return praf.framework.defeats


def _attack_opinion(
    praf: ProbabilisticAF,
    edge: tuple[str, str],
) -> Opinion | None:
    for relation in praf.attack_relations:
        if relation.edge == edge:
            return relation.opinion
    if praf.p_attacks is not None and edge in praf.p_attacks:
        return praf.p_attacks[edge]
    if edge in _direct_defeats(praf) and edge in praf.p_defeats:
        return praf.p_defeats[edge]
    return None


def _support_opinion(
    praf: ProbabilisticAF,
    edge: tuple[str, str],
) -> Opinion | None:
    for relation in praf.support_relations:
        if relation.edge == edge:
            return relation.opinion
    if praf.p_supports is not None and edge in praf.p_supports:
        return praf.p_supports[edge]
    return None


def _sample_edge(
    rng: _random_mod.Random,
    opinion: Opinion | None,
) -> bool:
    if opinion is None:
        return True
    return rng.random() < opinion.expectation()


def _supports_structure(praf: ProbabilisticAF) -> bool:
    return bool(praf.supports)


def _uses_attack_only_conflicts(praf: ProbabilisticAF) -> bool:
    return (
        praf.framework.attacks is not None
        and praf.framework.attacks != praf.framework.defeats
    )


def _requires_relation_rich_worlds(praf: ProbabilisticAF) -> bool:
    return _supports_structure(praf) or _uses_attack_only_conflicts(praf)


def _all_structure_deterministic(praf: ProbabilisticAF) -> bool:
    if not all(_is_deterministic_opinion(p) for p in praf.p_args.values()):
        return False
    for edge in _primitive_attacks(praf):
        opinion = _attack_opinion(praf, edge)
        if not _is_deterministic_opinion(opinion):
            return False
    for edge in praf.supports:
        opinion = _support_opinion(praf, edge)
        if not _is_deterministic_opinion(opinion):
            return False
    return True


def _deterministic_world(
    praf: ProbabilisticAF,
    arg_subset: frozenset[str] | None = None,
) -> ArgumentationFramework:
    """Realize the unique deterministic world for a deterministic PrAF."""
    args_to_consider = arg_subset if arg_subset is not None else praf.framework.arguments
    sampled_args = frozenset(
        a for a in args_to_consider
        if _edge_is_present(praf.p_args[a])
    )
    sampled_attacks = frozenset(
        edge for edge in _primitive_attacks(praf)
        if edge[0] in sampled_args
        and edge[1] in sampled_args
        and _edge_is_present(_attack_opinion(praf, edge))
    )
    sampled_supports = frozenset(
        edge for edge in praf.supports
        if edge[0] in sampled_args
        and edge[1] in sampled_args
        and _edge_is_present(_support_opinion(praf, edge))
    )
    return _build_sampled_framework(praf, sampled_args, sampled_attacks, sampled_supports)


def _build_sampled_framework(
    praf: ProbabilisticAF,
    sampled_args: frozenset[str],
    sampled_attacks: frozenset[tuple[str, str]],
    sampled_supports: frozenset[tuple[str, str]],
) -> ArgumentationFramework:
    """Build one sampled world, deriving Cayrol defeats after sampling primitives."""
    direct_defeats = frozenset(
        edge for edge in sampled_attacks if edge in _direct_defeats(praf)
    )
    all_defeats = set(direct_defeats)
    if sampled_supports and direct_defeats:
        from propstore.argumentation import _cayrol_derived_defeats

        all_defeats |= _cayrol_derived_defeats(set(direct_defeats), set(sampled_supports))

    sampled_attacks_relation: frozenset[tuple[str, str]] | None = None
    if praf.framework.attacks is not None:
        sampled_attacks_relation = sampled_attacks

    return ArgumentationFramework(
        arguments=sampled_args,
        defeats=frozenset(all_defeats),
        attacks=sampled_attacks_relation,
    )


def _enumerate_worlds(
    praf: ProbabilisticAF,
    sampled_args: frozenset[str],
):
    """Enumerate all sampled worlds induced by a fixed argument subset."""
    deterministic_attacks: set[tuple[str, str]] = set()
    probabilistic_attacks: list[tuple[tuple[str, str], float]] = []
    for edge in sorted(_primitive_attacks(praf)):
        if edge[0] not in sampled_args or edge[1] not in sampled_args:
            continue
        opinion = _attack_opinion(praf, edge)
        if opinion is None:
            deterministic_attacks.add(edge)
        else:
            probabilistic_attacks.append((edge, opinion.expectation()))

    deterministic_supports: set[tuple[str, str]] = set()
    probabilistic_supports: list[tuple[tuple[str, str], float]] = []
    for edge in sorted(praf.supports):
        if edge[0] not in sampled_args or edge[1] not in sampled_args:
            continue
        opinion = _support_opinion(praf, edge)
        if opinion is None:
            deterministic_supports.add(edge)
        else:
            probabilistic_supports.append((edge, opinion.expectation()))

    n_prob_attacks = len(probabilistic_attacks)
    n_prob_supports = len(probabilistic_supports)

    for attack_mask in range(1 << n_prob_attacks):
        sampled_attacks = set(deterministic_attacks)
        p_attacks_config = 1.0
        for idx, (edge, p_edge) in enumerate(probabilistic_attacks):
            if attack_mask & (1 << idx):
                p_attacks_config *= p_edge
                sampled_attacks.add(edge)
            else:
                p_attacks_config *= (1.0 - p_edge)
        if p_attacks_config < 1e-15:
            continue

        for support_mask in range(1 << n_prob_supports):
            sampled_supports = set(deterministic_supports)
            p_supports_config = 1.0
            for idx, (edge, p_edge) in enumerate(probabilistic_supports):
                if support_mask & (1 << idx):
                    p_supports_config *= p_edge
                    sampled_supports.add(edge)
                else:
                    p_supports_config *= (1.0 - p_edge)

            total_prob = p_attacks_config * p_supports_config
            if total_prob < 1e-15:
                continue

            yield total_prob, _build_sampled_framework(
                praf,
                sampled_args,
                frozenset(sampled_attacks),
                frozenset(sampled_supports),
            )


def compute_praf_acceptance(
    praf: ProbabilisticAF,
    *,
    semantics: str = "grounded",
    strategy: str = "auto",
    mc_epsilon: float = 0.01,
    mc_confidence: float = 0.95,
    treewidth_cutoff: int = 12,
    rng_seed: int | None = None,
) -> PrAFResult:
    """Main dispatch for PrAF acceptance computation.

    Per Li et al. (2012, Algorithm 1): MC sampler with Agresti-Coull stopping.
    Per Hunter & Thimm (2017, Prop 18): connected component decomposition.

    strategy:
        "auto" — deterministic fallback if all P_D ≈ 1.0, else MC.
        "mc" — force Monte Carlo sampling.
        "deterministic" — force deterministic Dung evaluation.
        "exact_enum" — brute-force enumeration (small AFs only).
        "exact_dp" — tree-decomposition DP (Popescu & Wallner 2024).
    """
    if strategy == "deterministic":
        return _deterministic_fallback(praf, semantics)
    if strategy == "mc":
        return _compute_mc(praf, semantics, mc_epsilon, mc_confidence, rng_seed)
    if strategy == "exact_enum":
        return _compute_exact_enumeration(praf, semantics)
    if strategy == "exact_dp":
        return _compute_exact_dp(praf, semantics)
    if strategy == "dfquad":
        return _compute_dfquad(praf, semantics)

    # Auto dispatch
    # Fast path: if all P_D expectations are ~1.0 and all P_A expectations are ~1.0,
    # this is a deterministic AF — no sampling needed.
    # Per Li (2012, p.2): PrAF with P_A=1, P_D=1 equals standard Dung evaluation.
    all_deterministic = _all_structure_deterministic(praf)
    if all_deterministic:
        return _deterministic_fallback(praf, semantics)

    # Small AF: exact enumeration (Li 2012, p.8: exact beats MC below ~13 args)
    n_args = len(praf.framework.arguments)
    if n_args <= 13:
        return _compute_exact_enumeration(praf, semantics)

    # Relation-rich worlds currently require exact enumeration or MC.
    if _requires_relation_rich_worlds(praf):
        return _compute_mc(praf, semantics, mc_epsilon, mc_confidence, rng_seed)

    # Medium AF with low treewidth: exact DP (Popescu & Wallner 2024)
    # Per plan Section 2.4: estimate treewidth, use DP if below cutoff.
    from propstore.praf_treedecomp import estimate_treewidth

    tw = estimate_treewidth(praf.framework)
    if tw <= treewidth_cutoff:
        return _compute_exact_dp(praf, semantics)

    # Default: MC
    return _compute_mc(praf, semantics, mc_epsilon, mc_confidence, rng_seed)


def _deterministic_fallback(praf: ProbabilisticAF, semantics: str) -> PrAFResult:
    """All P_D ≈ 1.0 case: run standard Dung evaluation.

    Per Li (2012, p.2): PrAF with P_A=1, P_D=1 yields acceptance probabilities
    of exactly 0.0 or 1.0, matching standard Dung extension computation.
    """
    deterministic_af = _deterministic_world(praf)
    ext = _evaluate_semantics(deterministic_af, semantics)

    acceptance: dict[str, float] = {}
    for arg in deterministic_af.arguments:
        acceptance[arg] = 1.0 if arg in ext else 0.0
    for arg in praf.framework.arguments - deterministic_af.arguments:
        acceptance[arg] = 0.0

    return PrAFResult(
        acceptance_probs=acceptance,
        strategy_used="deterministic",
        samples=None,
        confidence_interval_half=None,
        semantics=semantics,
    )


def _evaluate_semantics(
    af: ArgumentationFramework, semantics: str
) -> frozenset[str]:
    """Evaluate a single extension under the chosen semantics.

    For grounded: returns the unique grounded extension.
    For preferred/stable/complete: returns the union of all extensions
    (credulous acceptance — an argument is accepted if it appears in ANY extension).
    """
    if semantics == "grounded":
        return grounded_extension(af)
    elif semantics == "preferred":
        exts = preferred_extensions(af, backend="brute")
        return frozenset().union(*exts) if exts else frozenset()
    elif semantics == "stable":
        exts = stable_extensions(af, backend="brute")
        return frozenset().union(*exts) if exts else frozenset()
    elif semantics == "complete":
        exts = complete_extensions(af, backend="brute")
        return frozenset().union(*exts) if exts else frozenset()
    else:
        raise ValueError(f"Unknown semantics: {semantics}")


def _connected_components(praf: ProbabilisticAF) -> list[set[str]]:
    """Decompose into components of the primitive semantic dependency graph.

    Per Hunter & Thimm (2017, Prop 18): acceptance probability separates
    over connected components. Each component can be solved independently.
    """
    adj: dict[str, set[str]] = {a: set() for a in praf.framework.arguments}
    relations = set(_primitive_attacks(praf)) | set(praf.supports)
    for src, tgt in relations:
        adj[src].add(tgt)
        adj[tgt].add(src)

    visited: set[str] = set()
    components: list[set[str]] = []

    for start in praf.framework.arguments:
        if start in visited:
            continue
        # BFS
        component: set[str] = set()
        queue = [start]
        while queue:
            node = queue.pop()
            if node in visited:
                continue
            visited.add(node)
            component.add(node)
            for neighbor in adj[node]:
                if neighbor not in visited:
                    queue.append(neighbor)
        components.append(component)

    return components


def _sample_subgraph(
    praf: ProbabilisticAF,
    rng: _random_mod.Random,
    arg_subset: set[str] | None = None,
) -> ArgumentationFramework:
    """Sample one semantic AF world from primitive probabilistic relations.

    Per Li et al. (2012, Algorithm 1, p.5):
    1. For each argument a, include with probability P_A(a).expectation()
    2. For each primitive attack/support where both endpoints are included,
       sample existence from its opinion expectation
    3. Derive direct defeats from sampled attacks and direct-defeat policy
    4. Derive Cayrol defeats from sampled direct defeats and supports
    """
    args_to_sample = arg_subset if arg_subset is not None else praf.framework.arguments

    # Step 1: Sample arguments
    sampled_args: set[str] = set()
    for a in args_to_sample:
        p_a = praf.p_args[a].expectation()
        if rng.random() < p_a:
            sampled_args.add(a)

    sampled_attacks: set[tuple[str, str]] = set()
    for edge in _primitive_attacks(praf):
        if edge[0] in sampled_args and edge[1] in sampled_args:
            if _sample_edge(rng, _attack_opinion(praf, edge)):
                sampled_attacks.add(edge)

    sampled_supports: set[tuple[str, str]] = set()
    for edge in praf.supports:
        if edge[0] in sampled_args and edge[1] in sampled_args:
            if _sample_edge(rng, _support_opinion(praf, edge)):
                sampled_supports.add(edge)

    return _build_sampled_framework(
        praf,
        frozenset(sampled_args),
        frozenset(sampled_attacks),
        frozenset(sampled_supports),
    )


def _compute_mc(
    praf: ProbabilisticAF,
    semantics: str,
    epsilon: float,
    confidence: float,
    seed: int | None,
) -> PrAFResult:
    """Monte Carlo sampler with per-argument acceptance and Agresti-Coull stopping.

    Per Li et al. (2012, Algorithm 1, p.5): sample DAFs, evaluate semantics,
    accumulate per-argument acceptance counts.

    Stopping criterion per Li et al. (2012, Eq. 5, p.7):
    N > 4 * p' * (1 - p') / epsilon^2 - 4
    where p' is the observed proportion for the argument with widest CI.

    Min 30 samples before convergence check.
    """
    rng = _random_mod.Random(seed)

    # Decompose into connected components per Hunter & Thimm (2017, Prop 18)
    components = _connected_components(praf)

    # Compute acceptance per component independently
    all_acceptance: dict[str, float] = {}
    total_samples = 0
    max_ci_half = 0.0

    for comp_args in components:
        # Build sub-PrAF for this component
        comp_defeats = frozenset(
            (f, t) for f, t in praf.framework.defeats
            if f in comp_args and t in comp_args
        )
        comp_attacks = None
        if praf.framework.attacks is not None:
            comp_attacks = frozenset(
                (f, t) for f, t in praf.framework.attacks
                if f in comp_args and t in comp_args
            )
        comp_supports = frozenset(
            (f, t) for f, t in praf.supports
            if f in comp_args and t in comp_args
        )
        comp_base_defeats = frozenset(
            (f, t) for f, t in _direct_defeats(praf)
            if f in comp_args and t in comp_args
        )

        comp_af = ArgumentationFramework(
            arguments=frozenset(comp_args),
            defeats=comp_defeats,
            attacks=comp_attacks,
        )
        comp_p_args = {a: praf.p_args[a] for a in comp_args}
        comp_p_defeats = {
            d: praf.p_defeats[d] for d in comp_defeats
            if d in praf.p_defeats
        }
        comp_p_attacks = None
        if praf.p_attacks is not None:
            comp_p_attacks = {
                d: praf.p_attacks[d] for d in comp_attacks or frozenset()
                if d in praf.p_attacks
            }
        comp_p_supports = None
        if praf.p_supports is not None:
            comp_p_supports = {
                d: praf.p_supports[d] for d in comp_supports
                if d in praf.p_supports
            }

        comp_praf = ProbabilisticAF(
            framework=comp_af,
            p_args=comp_p_args,
            p_defeats=comp_p_defeats,
            p_attacks=comp_p_attacks,
            supports=comp_supports,
            p_supports=comp_p_supports,
            base_defeats=comp_base_defeats,
        )

        # Check if this component is deterministic
        comp_all_det = _all_structure_deterministic(comp_praf)
        if comp_all_det:
            ext = _evaluate_semantics(_deterministic_world(comp_praf), semantics)
            for arg in comp_args:
                all_acceptance[arg] = 1.0 if arg in ext else 0.0
            continue

        # MC sampling for this component
        counts: dict[str, int] = {a: 0 for a in comp_args}
        n = 0
        min_samples = 30

        while True:
            n += 1
            sub_af = _sample_subgraph(comp_praf, rng, comp_args)
            ext = _evaluate_semantics(sub_af, semantics)

            for a in comp_args:
                if a in ext:
                    counts[a] += 1

            # Agresti-Coull stopping (Li 2012, Eq. 5, p.7)
            if n >= min_samples:
                converged = True
                for a in comp_args:
                    p_hat = counts[a] / n
                    # Required N per Agresti-Coull: N > 4*p*(1-p)/eps^2 - 4
                    required_n = (4.0 * p_hat * (1.0 - p_hat)) / (epsilon ** 2) - 4.0
                    if n <= required_n:
                        converged = False
                        break
                if converged:
                    break

            # Safety cap to prevent infinite loops
            if n >= 100000:
                break

        for a in comp_args:
            all_acceptance[a] = counts[a] / n

        total_samples = max(total_samples, n)

        # Compute CI half-width for this component
        for a in comp_args:
            p_hat = all_acceptance[a]
            if n > 0:
                z = _z_for_confidence(confidence)
                ci = z * math.sqrt(p_hat * (1.0 - p_hat) / n) if n > 1 else 1.0
                max_ci_half = max(max_ci_half, ci)

    return PrAFResult(
        acceptance_probs=all_acceptance,
        strategy_used="mc",
        samples=total_samples,
        confidence_interval_half=max_ci_half,
        semantics=semantics,
    )


def _compute_exact_enumeration(
    praf: ProbabilisticAF,
    semantics: str,
) -> PrAFResult:
    """Brute-force exact computation for small AFs.

    Per Li et al. (2012, p.3-4): enumerate all inducible DAFs, compute
    P_PrAF(AF) for each, sum probabilities where argument is in extension.

    Complexity: O(2^(|A|+|D|)) — only feasible for small AFs.
    """
    args_list = sorted(praf.framework.arguments)
    n_args = len(args_list)

    # Per-argument acceptance probability accumulator
    acceptance: dict[str, float] = {a: 0.0 for a in args_list}

    # Enumerate all subsets of arguments
    for arg_mask in range(1 << n_args):
        sampled_args = frozenset(
            args_list[i] for i in range(n_args) if arg_mask & (1 << i)
        )

        # Compute probability of this argument subset
        p_args_present = 1.0
        for i, a in enumerate(args_list):
            p_a = praf.p_args[a].expectation()
            if arg_mask & (1 << i):
                p_args_present *= p_a
            else:
                p_args_present *= (1.0 - p_a)

        if p_args_present < 1e-15:
            continue

        # Find valid defeats (both endpoints present)
        for p_world, sub_af in _enumerate_worlds(praf, sampled_args):
            total_prob = p_args_present * p_world
            if total_prob < 1e-15:
                continue
            ext = _evaluate_semantics(sub_af, semantics)

            for a in sampled_args:
                if a in ext:
                    acceptance[a] += total_prob

    return PrAFResult(
        acceptance_probs=acceptance,
        strategy_used="exact_enum",
        samples=None,
        confidence_interval_half=None,
        semantics=semantics,
    )


def _compute_exact_dp(
    praf: ProbabilisticAF,
    semantics: str,
) -> PrAFResult:
    """Exact computation via tree-decomposition DP.

    Per Popescu & Wallner (2024): compute extension probabilities using
    dynamic programming on tree decompositions. Tractable for low-treewidth
    AFs (complexity O(3^k * n) where k is treewidth).
    """
    from propstore.praf_treedecomp import compute_exact_dp

    acceptance = compute_exact_dp(praf, semantics)

    return PrAFResult(
        acceptance_probs=acceptance,
        strategy_used="exact_dp",
        samples=None,
        confidence_interval_half=None,
        semantics=semantics,
    )


def summarize_defeat_relations(
    praf: ProbabilisticAF,
    *,
    include_derived: bool = True,
) -> tuple[ProbabilisticRelation, ...]:
    """Compute exact defeat marginals as derived query results.

    This helper is explicit and potentially exponential. It is intended for
    explanation and diagnostics, not as an input to the semantic core.
    """
    args_list = sorted(praf.framework.arguments)
    n_args = len(args_list)
    acceptance: dict[tuple[str, str], float] = {}

    for arg_mask in range(1 << n_args):
        sampled_args = frozenset(
            args_list[i] for i in range(n_args) if arg_mask & (1 << i)
        )

        p_args_present = 1.0
        for i, a in enumerate(args_list):
            p_a = praf.p_args[a].expectation()
            if arg_mask & (1 << i):
                p_args_present *= p_a
            else:
                p_args_present *= (1.0 - p_a)

        if p_args_present < 1e-15:
            continue

        for p_world, sub_af in _enumerate_worlds(praf, sampled_args):
            total_prob = p_args_present * p_world
            if total_prob < 1e-15:
                continue
            for defeat in sub_af.defeats:
                acceptance[defeat] = acceptance.get(defeat, 0.0) + total_prob

    records: list[ProbabilisticRelation] = []
    direct_defeats = _direct_defeats(praf)
    for edge in sorted(acceptance):
        if not include_derived and edge not in direct_defeats:
            continue
        kind = "direct_defeat" if edge in direct_defeats else "derived_defeat"
        records.append(
            relation_from_row(
                kind=kind,
                source=edge[0],
                target=edge[1],
                opinion=Opinion(acceptance[edge], 1.0 - acceptance[edge], 0.0, 0.5),
                row=None,
                derived_from=(),
            )
        )

    return tuple(records)


def _compute_dfquad(
    praf: ProbabilisticAF,
    semantics: str,
    supports: dict[tuple[str, str], float] | None = None,
) -> PrAFResult:
    """DF-QuAD gradual semantics for QBAFs.

    Per Freedman et al. (2025, p.3): computes continuous strengths in [0,1]
    by propagating base scores through attack and support relations.

    Complementary to PrAF MC/exact strategies which compute extension
    membership probabilities. DF-QuAD computes graded argument strengths.

    **Design note:** Li 2012's P_A (argument existence probability for MC sampling)
    is currently used as Rago 2016's τ (intrinsic strength for DF-QuAD gradual
    semantics). These are conceptually distinct: a rarely-existing argument is not
    the same as a weak argument. A principled separation would maintain P_A for
    sampling and τ as an independent parameter.
    """
    from propstore.praf_dfquad import compute_dfquad_strengths

    if supports is None:
        supports = {}

    strengths = compute_dfquad_strengths(praf, supports)

    return PrAFResult(
        acceptance_probs=strengths,
        strategy_used="dfquad",
        samples=None,
        confidence_interval_half=None,
        semantics=semantics,
    )
