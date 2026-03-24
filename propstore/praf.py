"""Probabilistic Argumentation Frameworks.

Implements PrAF = (A, P_A, D, P_D) per Li et al. (2012, Def 2).
Monte Carlo sampler with Agresti-Coull stopping per Li et al. (2012, Algorithm 1).
Connected component decomposition per Hunter & Thimm (2017, Prop 18).
"""

from __future__ import annotations

import math
import random as _random_mod
from dataclasses import dataclass

from propstore.dung import (
    ArgumentationFramework,
    complete_extensions,
    grounded_extension,
    preferred_extensions,
    stable_extensions,
)
from propstore.opinion import Opinion, from_probability

# Threshold for treating P_D as deterministic (all defeats certain).
_DETERMINISTIC_THRESHOLD = 0.999


@dataclass(frozen=True)
class ProbabilisticAF:
    """PrAF = (A, P_A, D, P_D) per Li et al. (2012, Def 2).

    framework: the full Dung AF envelope (A, D).
    p_args: dict[str, Opinion] — P_A per argument (existence probability).
    p_defeats: dict[tuple[str, str], Opinion] — P_D per defeat (existence probability).

    The MC sampler uses Opinion.expectation() (Jøsang 2001, Def 6: E(ω) = b + a·u)
    as the sampling probability for each element.
    """

    framework: ArgumentationFramework
    p_args: dict[str, Opinion]
    p_defeats: dict[tuple[str, str], Opinion]


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


def p_defeat_from_stance(stance: dict) -> Opinion:
    """Derive P_D from a stance's opinion columns.

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
        # from_probability(p, n) with n=1 gives moderate uncertainty.
        return from_probability(confidence, 1)

    # No opinion or confidence data — certain defeat (backward compat).
    return Opinion.dogmatic_true()


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
    """
    if strategy == "deterministic":
        return _deterministic_fallback(praf, semantics)
    if strategy == "mc":
        return _compute_mc(praf, semantics, mc_epsilon, mc_confidence, rng_seed)
    if strategy == "exact_enum":
        return _compute_exact_enumeration(praf, semantics)

    # Auto dispatch
    # Fast path: if all P_D expectations are ~1.0 and all P_A expectations are ~1.0,
    # this is a deterministic AF — no sampling needed.
    # Per Li (2012, p.2): PrAF with P_A=1, P_D=1 equals standard Dung evaluation.
    all_deterministic = (
        all(p.expectation() >= _DETERMINISTIC_THRESHOLD for p in praf.p_defeats.values())
        and all(p.expectation() >= _DETERMINISTIC_THRESHOLD for p in praf.p_args.values())
    )
    if all_deterministic:
        return _deterministic_fallback(praf, semantics)

    # Small AF: exact enumeration (Li 2012, p.8: exact beats MC below ~13 args)
    n_args = len(praf.framework.arguments)
    if n_args <= 13:
        return _compute_exact_enumeration(praf, semantics)

    # Default: MC
    return _compute_mc(praf, semantics, mc_epsilon, mc_confidence, rng_seed)


def _deterministic_fallback(praf: ProbabilisticAF, semantics: str) -> PrAFResult:
    """All P_D ≈ 1.0 case: run standard Dung evaluation.

    Per Li (2012, p.2): PrAF with P_A=1, P_D=1 yields acceptance probabilities
    of exactly 0.0 or 1.0, matching standard Dung extension computation.
    """
    ext = _evaluate_semantics(praf.framework, semantics)

    acceptance: dict[str, float] = {}
    for arg in praf.framework.arguments:
        acceptance[arg] = 1.0 if arg in ext else 0.0

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


def _connected_components(framework: ArgumentationFramework) -> list[set[str]]:
    """Decompose AF into connected components of the undirected attack/defeat graph.

    Per Hunter & Thimm (2017, Prop 18): acceptance probability separates
    over connected components. Each component can be solved independently.
    """
    # Build adjacency from defeats (undirected)
    adj: dict[str, set[str]] = {a: set() for a in framework.arguments}
    for src, tgt in framework.defeats:
        adj[src].add(tgt)
        adj[tgt].add(src)

    visited: set[str] = set()
    components: list[set[str]] = []

    for start in framework.arguments:
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
    """Sample one induced DAF from the PrAF.

    Per Li et al. (2012, Algorithm 1, p.5):
    1. For each argument a, include with probability P_A(a).expectation()
    2. For each defeat (f,t) where both f,t are included,
       include with probability P_D((f,t)).expectation()

    Step 2 enforces Definition 3: defeats only sampled when both endpoints present.
    """
    args_to_sample = arg_subset if arg_subset is not None else praf.framework.arguments

    # Step 1: Sample arguments
    sampled_args: set[str] = set()
    for a in args_to_sample:
        p_a = praf.p_args[a].expectation()
        if rng.random() < p_a:
            sampled_args.add(a)

    # Step 2: Sample defeats — only if both endpoints present (Li 2012, p.5, step 2c)
    sampled_defeats: set[tuple[str, str]] = set()
    for f, t in praf.framework.defeats:
        if f in sampled_args and t in sampled_args:
            p_d = praf.p_defeats[(f, t)].expectation()
            if rng.random() < p_d:
                sampled_defeats.add((f, t))

    # Also filter attacks if present
    sampled_attacks: frozenset[tuple[str, str]] | None = None
    if praf.framework.attacks is not None:
        sampled_attacks = frozenset(
            (f, t) for f, t in praf.framework.attacks
            if f in sampled_args and t in sampled_args
        )

    return ArgumentationFramework(
        arguments=frozenset(sampled_args),
        defeats=frozenset(sampled_defeats),
        attacks=sampled_attacks,
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
    components = _connected_components(praf.framework)

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

        comp_praf = ProbabilisticAF(
            framework=comp_af,
            p_args=comp_p_args,
            p_defeats=comp_p_defeats,
        )

        # Check if this component is deterministic
        comp_all_det = (
            all(p.expectation() >= _DETERMINISTIC_THRESHOLD for p in comp_p_defeats.values())
            and all(p.expectation() >= _DETERMINISTIC_THRESHOLD for p in comp_p_args.values())
        )
        if comp_all_det:
            ext = _evaluate_semantics(comp_af, semantics)
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
                ci = 1.96 * math.sqrt(p_hat * (1.0 - p_hat) / n) if n > 1 else 1.0
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
    defeats_list = sorted(praf.framework.defeats)
    n_args = len(args_list)
    n_defeats = len(defeats_list)

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
        valid_defeats = [
            (j, (f, t)) for j, (f, t) in enumerate(defeats_list)
            if f in sampled_args and t in sampled_args
        ]
        n_valid = len(valid_defeats)

        # Enumerate all subsets of valid defeats
        for def_mask in range(1 << n_valid):
            sampled_defeats = frozenset(
                valid_defeats[k][1]
                for k in range(n_valid)
                if def_mask & (1 << k)
            )

            # Compute probability of this defeat subset
            p_defeats_config = 1.0
            for k, (j, (f, t)) in enumerate(valid_defeats):
                p_d = praf.p_defeats[(f, t)].expectation()
                if def_mask & (1 << k):
                    p_defeats_config *= p_d
                else:
                    p_defeats_config *= (1.0 - p_d)

            total_prob = p_args_present * p_defeats_config
            if total_prob < 1e-15:
                continue

            # Build sub-AF and evaluate
            sub_af = ArgumentationFramework(
                arguments=sampled_args,
                defeats=sampled_defeats,
            )
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
