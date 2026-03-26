"""ASPIC+ logical language and contrariness function.

Implements the foundational data structures for ASPIC+ structured
argumentation, following Modgil & Prakken (2018) Definitions 1-2.

This is a leaf module with ZERO imports from propstore.

References:
    Modgil, S. & Prakken, H. (2018). A general account of argumentation
    with preferences. Artificial Intelligence, 248, 51-104.
"""

from __future__ import annotations

import functools
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from propstore.dung import ArgumentationFramework


@dataclass(frozen=True)
class Literal:
    """A literal in the logical language L.

    A literal is an atom or its negation. The ``.contrary`` property
    returns the complementary literal (negation of this literal).

    Modgil & Prakken 2018, Def 1 (p.8): L is a logical language
    closed under the contrariness function — every formula's
    contraries/contradictories are also in L.

    Attributes:
        atom: The propositional atom name.
        negated: Whether this literal is the negation of the atom.
    """

    atom: str
    negated: bool = False

    @property
    def contrary(self) -> Literal:
        """Return the complementary literal.

        For atom p: p.contrary = ~p, and ~p.contrary = p.
        This is an involution: a.contrary.contrary == a.

        Modgil & Prakken 2018, Def 1 (p.8).
        """
        return Literal(self.atom, not self.negated)

    def __repr__(self) -> str:
        if self.negated:
            return f"~{self.atom}"
        return self.atom


@dataclass(frozen=True)
class ContrarinessFn:
    """Contrariness function over a logical language.

    Maps pairs of literals to their conflict relationship:
    contradictories (symmetric) or contraries (asymmetric).

    Modgil & Prakken 2018, Def 1 (p.8):
        - If phi in bar(psi) AND psi in bar(phi): contradictories
        - If phi in bar(psi) AND psi NOT in bar(phi): phi is a contrary of psi

    For Phase 1, only contradictories are stored. Asymmetric contraries
    will be added in later phases; for now ``is_contrary`` delegates
    to ``is_contradictory``.

    Attributes:
        contradictories: Frozenset of (Literal, Literal) pairs that are
            contradictory. Only one direction need be stored; lookup
            checks both orderings.
    """

    contradictories: frozenset[tuple[Literal, Literal]]

    def is_contradictory(self, a: Literal, b: Literal) -> bool:
        """True if a and b are contradictories (symmetric conflict).

        Modgil & Prakken 2018, Def 2 (p.8): phi and psi are
        contradictories iff phi in bar(psi) AND psi in bar(phi).
        """
        return (a, b) in self.contradictories or (b, a) in self.contradictories

    def is_contrary(self, a: Literal, b: Literal) -> bool:
        """True if a is a contrary of b.

        Modgil & Prakken 2018, Def 2 (p.8): phi is a contrary of psi
        iff phi in bar(psi). For Phase 1, only symmetric contradictories
        are supported, so this delegates to ``is_contradictory``.
        Asymmetric contraries will be added in later phases.
        """
        return self.is_contradictory(a, b)


@dataclass(frozen=True)
class Rule:
    """A strict or defeasible inference rule.

    Modgil & Prakken 2018, Def 2 (p.8).
    Strict rules: antecedents -> consequent (no exceptions).
    Defeasible rules: antecedents => consequent (presumptive).
    Defeasible rules have a name n(r) for undercutting attacks.

    Prakken 2010, Def 3.4 (p.47-48):
        - Strict rule: phi_1, ..., phi_n -> phi
        - Defeasible rule: phi_1, ..., phi_n => phi

    Attributes:
        antecedents: Tuple of literals forming the rule body.
        consequent: The literal concluded by the rule.
        kind: Either "strict" or "defeasible".
        name: n(r) for defeasible rules (Modgil & Prakken 2018, Def 2, p.8).
            Required for defeasible rules to enable undercutting attacks.
            None for strict rules.
    """

    antecedents: tuple[Literal, ...]
    consequent: Literal
    kind: str  # "strict" or "defeasible"
    name: str | None = None  # n(r) for defeasible rules


@dataclass(frozen=True)
class PremiseArg:
    """Argument from a premise. Modgil & Prakken 2018, Def 5 clause 1."""
    premise: Literal
    is_axiom: bool  # True if in K_n, False if in K_p


@dataclass(frozen=True)
class StrictArg:
    """Argument via strict rule. Modgil & Prakken 2018, Def 5 clause 2."""
    sub_args: tuple[Argument, ...]
    rule: Rule  # must have kind == "strict"


@dataclass(frozen=True)
class DefeasibleArg:
    """Argument via defeasible rule. Modgil & Prakken 2018, Def 5 clause 3."""
    sub_args: tuple[Argument, ...]
    rule: Rule  # must have kind == "defeasible"


Argument = Union[PremiseArg, StrictArg, DefeasibleArg]


@dataclass(frozen=True)
class Attack:
    """An attack from argument A on sub-argument B' of B.

    Modgil & Prakken 2018, Def 8 (p.11): three types of attack:
    - Undermining (Def 8a): A attacks ordinary premise of B'
    - Rebutting (Def 8b): A attacks defeasible conclusion of B'
    - Undercutting (Def 8c): A attacks defeasible rule applicability of B'
    """
    attacker: Argument
    target: Argument       # B — the argument being attacked
    target_sub: Argument   # B' — the specific sub-argument targeted
    kind: str              # "undermining", "rebutting", or "undercutting"


@dataclass(frozen=True)
class KnowledgeBase:
    """KB = (K_n, K_p). Modgil & Prakken 2018, Def 4 (p.9)."""
    axioms: frozenset[Literal]    # K_n — not attackable
    premises: frozenset[Literal]  # K_p — attackable


@dataclass(frozen=True)
class PreferenceConfig:
    """Configuration for preference-based defeat filtering.

    Modgil & Prakken 2018, Defs 19-21 (p.21).

    Defeat filtering uses preference orderings to determine when attacks
    succeed as defeats. Undercutting always succeeds (Def 9, p.12).
    Rebutting and undermining succeed only when the attacker is not
    strictly weaker than the targeted sub-argument (Def 9, p.12).

    The preference ordering over arguments is derived from orderings
    over rules and premises via set comparison (Def 19) and either
    last-link (Def 20) or weakest-link (Def 21) principles.

    Attributes:
        rule_order: Pairs (weaker, stronger) of defeasible rules forming
            a strict partial order (irreflexive, transitive). Def 22 (p.22).
        premise_order: Pairs (weaker, stronger) of ordinary premises forming
            a strict partial order (irreflexive, transitive). Def 22 (p.22).
        comparison: Set comparison mode — "elitist" or "democratic" (Def 19, p.21).
        link: Preference principle — "last" or "weakest" (Defs 20-21, p.21).
    """
    rule_order: frozenset[tuple[Rule, Rule]]      # (weaker, stronger) pairs
    premise_order: frozenset[tuple[Literal, Literal]]  # (weaker, stronger) pairs
    comparison: str  # "elitist" or "democratic"
    link: str        # "last" or "weakest"


@dataclass(frozen=True)
class ArgumentationSystem:
    """AS = (L, contrariness, R_s, R_d, n). Modgil & Prakken 2018, Def 2."""
    language: frozenset[Literal]
    contrariness: ContrarinessFn
    strict_rules: frozenset[Rule]
    defeasible_rules: frozenset[Rule]


def _is_degenerate_rule(rule: Rule) -> bool:
    """Check if a strict rule is degenerate and should be excluded.

    A rule is degenerate if it has a contradictory pair among its
    antecedents (both φ and ~φ). Such rules can only fire when
    contradictory information is already present, and their
    transpositions produce ill-formed rules.

    Modgil & Prakken 2018, Def 12 (p.13): transposition closure requires
    well-formed rules. Rules with contradictory antecedent pairs cannot
    be properly closed under transposition.

    Note: rules where an antecedent is the contrary of the consequent
    (e.g., ~r, p -> ~p) are NOT degenerate — they are valid transpositions
    needed for the rationality postulates (Thm 14, p.18: direct consistency).
    """
    antes = rule.antecedents
    for lit in antes:
        if lit.contrary in antes:
            return True
    return False


def transposition_closure(
    rules: frozenset[Rule],
    language: frozenset[Literal],
    contrariness: ContrarinessFn,
) -> frozenset[Rule]:
    """Compute the transposition closure of strict rules.

    Modgil & Prakken 2018, Def 12 (p.13); Prakken 2010, Def 5.1 (p.141).

    For each strict rule A1,...,An -> C and each i (1 <= i <= n):
    the transposed rule A1,...,~C,...,An -> ~Ai must also be in R_s.

    Iterates until fixpoint (no new rules produced).

    Only strict rules are transposed. Defeasible rules are never transposed
    (Def 12 applies to R_s only). The fixpoint always terminates because L
    is finite, bounding the number of possible rules.

    Rules with contradictory antecedent pairs (both φ and ~φ) are excluded:
    they are degenerate (ex falso quodlibet) and their transpositions
    produce rules where the consequent appears in the antecedents,
    violating well-formedness. Similarly, any generated transposition
    whose consequent appears in its own antecedents is excluded.

    Args:
        rules: The initial set of strict rules.
        language: The logical language L (set of all valid literals).
        contrariness: The contrariness function (unused directly — contraries
            are computed via Literal.contrary — but required for interface
            completeness since the language and contrariness are coupled).

    Returns:
        The smallest frozenset of well-formed Rules closed under
        transposition, containing all well-formed input rules.
    """
    # Filter out degenerate seed rules with contradictory antecedent pairs
    closed: set[Rule] = {
        r for r in rules
        if not _is_degenerate_rule(r)
    }
    changed = True
    while changed:
        changed = False
        new_rules: set[Rule] = set()
        for r in closed:
            if r.kind != "strict":
                continue
            for i, ante_i in enumerate(r.antecedents):
                # Transposed antecedents: replace a_i with ~C
                transposed_antes = list(r.antecedents)
                transposed_antes[i] = r.consequent.contrary
                # Transposed consequent: ~a_i
                transposed_consequent = ante_i.contrary
                # Filter: all literals must be in L
                if transposed_consequent not in language:
                    continue
                if any(a not in language for a in transposed_antes):
                    continue
                # Skip degenerate rules: consequent in antecedents
                if transposed_consequent in transposed_antes:
                    continue
                new_rule = Rule(
                    antecedents=tuple(transposed_antes),
                    consequent=transposed_consequent,
                    kind="strict",
                    name=None,
                )
                # Skip rules with contradictory antecedent pairs
                if _is_degenerate_rule(new_rule):
                    continue
                if new_rule not in closed:
                    new_rules.add(new_rule)
                    changed = True
        closed.update(new_rules)

    # Axiom consistency check (Def 12, p.13): verify that no single
    # literal's strict closure is self-contradictory. If Cl_Rs({φ})
    # contains ~φ for any φ in L, the rule set makes ANY knowledge base
    # containing φ axiom-inconsistent. Such rule sets cannot form
    # well-defined c-SAFs, so we prune to the empty set.
    # This catches multi-step contradiction chains (e.g., ~p -> q, q -> p
    # makes Cl_Rs({~p}) = {~p, q, p} which is inconsistent).
    result = frozenset(closed)
    for lit in language:
        cl = strict_closure(frozenset({lit}), result)
        if lit.contrary in cl:
            return frozenset()
    return result


def strict_closure(
    conclusions: frozenset[Literal],
    strict_rules: frozenset[Rule],
) -> frozenset[Literal]:
    """Closure of literal set under strict rules.

    Modgil & Prakken 2018, Def 3 (p.8).
    Cl_Rs(S) = smallest superset of S closed under R_s.

    If all antecedents of a strict rule are in the set, the consequent
    is added. Iterates until fixpoint (no new literals produced).

    Args:
        conclusions: The initial set of literals to close.
        strict_rules: The set of strict rules R_s.

    Returns:
        The smallest frozenset containing conclusions that is closed
        under strict_rules.
    """
    result = set(conclusions)
    changed = True
    while changed:
        changed = False
        for rule in strict_rules:
            if rule.kind == "strict" and all(a in result for a in rule.antecedents):
                if rule.consequent not in result:
                    result.add(rule.consequent)
                    changed = True
    return frozenset(result)


# ── Computed property functions ───────────────────────────────────
# All per Modgil & Prakken 2018, Def 5 (pp.9-10) unless noted.


@functools.cache
def conc(a: Argument) -> Literal:
    """Conclusion of argument. Modgil & Prakken 2018, Def 5."""
    if isinstance(a, PremiseArg):
        return a.premise
    if isinstance(a, (StrictArg, DefeasibleArg)):
        return a.rule.consequent
    raise TypeError(f"Unknown argument type: {type(a)}")


@functools.cache
def prem(a: Argument) -> frozenset[Literal]:
    """All premises (recursive). Modgil & Prakken 2018, Def 5."""
    if isinstance(a, PremiseArg):
        return frozenset({a.premise})
    if isinstance(a, (StrictArg, DefeasibleArg)):
        return frozenset().union(*(prem(s) for s in a.sub_args))
    raise TypeError(f"Unknown argument type: {type(a)}")


@functools.cache
def sub(a: Argument) -> frozenset[Argument]:
    """All sub-arguments including self. Modgil & Prakken 2018, Def 5."""
    if isinstance(a, PremiseArg):
        return frozenset({a})
    if isinstance(a, (StrictArg, DefeasibleArg)):
        return frozenset({a}).union(*(sub(s) for s in a.sub_args))
    raise TypeError(f"Unknown argument type: {type(a)}")


@functools.cache
def top_rule(a: Argument) -> Rule | None:
    """Top-level rule. None for PremiseArg. Modgil & Prakken 2018, Def 5."""
    if isinstance(a, PremiseArg):
        return None
    if isinstance(a, (StrictArg, DefeasibleArg)):
        return a.rule
    raise TypeError(f"Unknown argument type: {type(a)}")


@functools.cache
def def_rules(a: Argument) -> frozenset[Rule]:
    """All defeasible rules used. Modgil & Prakken 2018, Def 5."""
    if isinstance(a, PremiseArg):
        return frozenset()
    if isinstance(a, StrictArg):
        return frozenset().union(*(def_rules(s) for s in a.sub_args))
    if isinstance(a, DefeasibleArg):
        return frozenset({a.rule}).union(*(def_rules(s) for s in a.sub_args))
    raise TypeError(f"Unknown argument type: {type(a)}")


@functools.cache
def last_def_rules(a: Argument) -> frozenset[Rule]:
    """Last defeasible rules before strict-only chain.

    Modgil & Prakken 2018, p.10: LastDefRules returns the set of
    defeasible rules at the boundary between defeasible and strict
    inference in the argument tree.
    """
    if isinstance(a, PremiseArg):
        return frozenset()
    if isinstance(a, DefeasibleArg):
        return frozenset({a.rule})
    if isinstance(a, StrictArg):
        return frozenset().union(*(last_def_rules(s) for s in a.sub_args))
    raise TypeError(f"Unknown argument type: {type(a)}")


@functools.cache
def prem_p(a: Argument) -> frozenset[Literal]:
    """Ordinary premises only (K_p members). Modgil & Prakken 2018, p.10."""
    if isinstance(a, PremiseArg):
        return frozenset() if a.is_axiom else frozenset({a.premise})
    if isinstance(a, (StrictArg, DefeasibleArg)):
        return frozenset().union(*(prem_p(s) for s in a.sub_args))
    raise TypeError(f"Unknown argument type: {type(a)}")


def is_firm(a: Argument) -> bool:
    """True if all premises are axioms (K_n). Prakken 2010, Def 3.8."""
    return len(prem_p(a)) == 0


def is_strict(a: Argument) -> bool:
    """True if no defeasible rules used. Prakken 2010, Def 3.8."""
    return len(def_rules(a)) == 0


# ── Argument construction ─────────────────────────────────────────


def build_arguments(
    system: ArgumentationSystem, kb: KnowledgeBase
) -> frozenset[Argument]:
    """Bottom-up fixpoint argument construction.

    Modgil & Prakken 2018, Def 5 (pp.9-10); Prakken 2010, Def 3.6 (p.36).

    1. Seed: create PremiseArg for each literal in K_n (axiom) and K_p (ordinary).
    2. Index arguments by their conclusion literal.
    3. Iterate until fixpoint: for each rule, enumerate all combinations of
       existing arguments whose conclusions match the rule's antecedents,
       and create the corresponding StrictArg or DefeasibleArg.
    4. Return frozenset of all arguments.

    Terminates because L is finite, bounding the number of distinct conclusions,
    and arguments are deduplicated (frozen dataclasses are hashable).
    """
    import itertools

    # Step 1: Seed with premise arguments
    all_args: set[Argument] = set()
    # Index: conclusion literal -> set of arguments with that conclusion
    conc_index: dict[Literal, set[Argument]] = {}

    def _add(arg: Argument) -> bool:
        """Add argument to set and index. Returns True if new."""
        if arg in all_args:
            return False
        all_args.add(arg)
        c = conc(arg)
        if c not in conc_index:
            conc_index[c] = set()
        conc_index[c].add(arg)
        return True

    for lit in kb.axioms:
        _add(PremiseArg(premise=lit, is_axiom=True))
    for lit in kb.premises:
        _add(PremiseArg(premise=lit, is_axiom=False))

    def _all_concs(arg: Argument) -> frozenset[Literal]:
        """All conclusions reachable in the sub-argument tree."""
        if isinstance(arg, PremiseArg):
            return frozenset({arg.premise})
        if isinstance(arg, (StrictArg, DefeasibleArg)):
            return frozenset({arg.rule.consequent}).union(
                *(_all_concs(s) for s in arg.sub_args)
            )
        return frozenset()  # pragma: no cover

    # Step 2-3: Iterate until fixpoint
    all_rules = list(system.strict_rules | system.defeasible_rules)
    changed = True
    while changed:
        changed = False
        for rule in all_rules:
            # For each rule, get the sets of arguments matching each antecedent
            ante_arg_sets = []
            skip = False
            for ante_lit in rule.antecedents:
                args_for_lit = conc_index.get(ante_lit)
                if not args_for_lit:
                    skip = True
                    break
                ante_arg_sets.append(args_for_lit)
            if skip:
                continue

            # Enumerate all combinations via Cartesian product
            for combo in itertools.product(*ante_arg_sets):
                # Acyclicity: the rule's consequent must not already
                # appear as a conclusion in any sub-argument tree.
                # This prevents infinite nesting from rule cycles
                # (e.g., p->q, q->p producing ever-deeper arguments).
                # ASPIC+ arguments are finite trees (Def 5); a conclusion
                # appearing in a sub-argument would create a cycle.
                combo_concs = frozenset().union(
                    *(_all_concs(s) for s in combo)
                )
                if rule.consequent in combo_concs:
                    continue

                if rule.kind == "strict":
                    new_arg = StrictArg(sub_args=combo, rule=rule)
                else:
                    new_arg = DefeasibleArg(sub_args=combo, rule=rule)
                if _add(new_arg):
                    changed = True

    return frozenset(all_args)


# ── Attack determination ─────────────────────────────────────────


def compute_attacks(
    arguments: frozenset[Argument], system: ArgumentationSystem
) -> frozenset[Attack]:
    """Compute all attacks between arguments.

    Modgil & Prakken 2018, Def 8 (p.11): three attack types.

    For each ordered pair (A, B) in arguments, and each B' in sub(B):

    (a) Undermining: A undermines B on B' iff B' is a PremiseArg with
        is_axiom=False (ordinary premise) and conc(A) is contrary or
        contradictory to B'.premise. (Def 8a, p.11)

    (b) Rebutting: A rebuts B on B' iff top_rule(B') is defeasible and
        conc(A) is contrary or contradictory to conc(B'). (Def 8b, p.11;
        Pollock 1987, Def 2.4, p.485)

    (c) Undercutting: A undercuts B on B' iff top_rule(B') is a defeasible
        rule r with name n(r), and conc(A) is contrary or contradictory to
        Literal(n(r), False). (Def 8c, p.11; Pollock 1987, Def 2.5, p.485)

    Firm+strict sub-arguments are never targeted: they have no ordinary
    premises (so no undermining) and no defeasible rules (so no rebutting
    or undercutting). This is a consequence of Def 18 (p.16).

    Args:
        arguments: The set of all arguments built from the system and KB.
        system: The argumentation system providing the contrariness function.

    Returns:
        Frozenset of all Attack instances.
    """
    cfn = system.contrariness
    attacks: set[Attack] = set()

    # Pre-compute sub-arguments for each argument
    sub_cache: dict[Argument, frozenset[Argument]] = {
        b: sub(b) for b in arguments
    }

    for a in arguments:
        conc_a = conc(a)
        for b in arguments:
            for b_prime in sub_cache[b]:
                # Skip firm+strict sub-arguments — unattackable
                # (Def 18, p.16: no ordinary premises, no defeasible rules)
                if is_firm(b_prime) and is_strict(b_prime):
                    continue

                # (a) Undermining (Def 8a, p.11)
                if isinstance(b_prime, PremiseArg) and not b_prime.is_axiom:
                    if (cfn.is_contrary(conc_a, b_prime.premise)
                            or cfn.is_contradictory(conc_a, b_prime.premise)):
                        attacks.add(Attack(
                            attacker=a, target=b,
                            target_sub=b_prime, kind="undermining",
                        ))

                # (b) Rebutting (Def 8b, p.11)
                # A rebuts B on B' iff TopRule(B') is defeasible and
                # Conc(A) is contrary or contradictory to Conc(B').
                # No constraint on the attacker beyond its conclusion.
                tr = top_rule(b_prime)
                if tr is not None and tr.kind == "defeasible":
                    conc_b_prime = conc(b_prime)
                    if (cfn.is_contrary(conc_a, conc_b_prime)
                            or cfn.is_contradictory(
                                conc_a, conc_b_prime)):
                        attacks.add(Attack(
                            attacker=a, target=b,
                            target_sub=b_prime, kind="rebutting",
                        ))

                    # (c) Undercutting (Def 8c, p.11)
                    # No attacker eligibility constraint — undercutting
                    # is preference-independent (Def 9, p.12).
                    if tr.name is not None:
                        name_lit = Literal(tr.name, False)
                        if (cfn.is_contrary(conc_a, name_lit)
                                or cfn.is_contradictory(conc_a, name_lit)):
                            attacks.add(Attack(
                                attacker=a, target=b,
                                target_sub=b_prime, kind="undercutting",
                            ))

    return frozenset(attacks)


# ── Defeat determination ──────────────────────────────────────────


def _set_strictly_less(
    gamma: frozenset,
    gamma_prime: frozenset,
    base_order: frozenset[tuple],
    comparison: str,
) -> bool:
    """Set comparison Gamma <_s Gamma' per Modgil & Prakken 2018, Def 19 (p.21).

    Determines if set ``gamma`` is strictly less than ``gamma_prime``
    under a base ordering, using either Elitist or Democratic comparison.

    Def 19 (p.21):
    - Empty Gamma is never strictly less than anything.
    - Elitist: exists X in Gamma s.t. forall Y in Gamma', (X, Y) in base_order.
    - Democratic: forall X in Gamma, exists Y in Gamma' s.t. (X, Y) in base_order.

    The base_order contains (weaker, stronger) pairs — i.e., (X, Y) means X < Y.

    Args:
        gamma: The candidate weaker set.
        gamma_prime: The candidate stronger set.
        base_order: Pairs (weaker, stronger) forming a strict partial order.
        comparison: "elitist" or "democratic" (Def 19, p.21).

    Returns:
        True if gamma <_s gamma_prime.
    """
    # Def 19 (p.21): empty set is never strictly less than anything.
    # When gamma_prime is empty with non-empty gamma, the elitist
    # formula "forall Y in gamma'" is vacuously true, but this would
    # make every non-empty set weaker than the empty set, which is
    # wrong: an argument with defeasible components is not weaker
    # than one with none just because the "none" set is empty.
    # Both sets must be non-empty for a meaningful comparison.
    if not gamma or not gamma_prime:
        return False

    if comparison == "elitist":
        # Def 19 (p.21), Elitist: Gamma <_Eli Gamma' iff
        # exists Y in Gamma' s.t. forall X in Gamma, X < Y.
        # Gamma is weaker if some element in Gamma' dominates all of Gamma.
        for y in gamma_prime:
            if all((x, y) in base_order for x in gamma):
                return True
        return False
    elif comparison == "democratic":
        # Def 19 (p.21), Democratic: Gamma <_Dem Gamma' iff
        # forall X in Gamma, exists Y in Gamma' s.t. X < Y.
        # Gamma is weaker if every element in Gamma is dominated by
        # something in Gamma'.
        for x in gamma:
            if not any((x, y) in base_order for y in gamma_prime):
                return False
        return True
    else:
        raise ValueError(f"Unknown comparison mode: {comparison}")


def _strictly_weaker(
    a: Argument,
    b: Argument,
    pref: PreferenceConfig,
    kb: KnowledgeBase,
) -> bool:
    """Determine if argument ``a`` is strictly weaker than ``b``.

    Uses the configured preference principle to derive argument ordering
    from the base orderings over rules and premises.

    Modgil & Prakken 2018:
    - Def 20 (p.21): Last-link principle.
    - Def 21 (p.21): Weakest-link principle.
    - Def 22 (p.22): The inducing ordering is a strict partial order.

    Args:
        a: Candidate weaker argument.
        b: Candidate stronger argument.
        pref: Preference configuration with orderings and comparison mode.
        kb: Knowledge base (needed to determine firm/strict status).

    Returns:
        True if a is strictly weaker than b (a prec b).
    """
    if pref.link == "last":
        # Def 20 (p.21): Last-link principle
        # a prec b iff:
        #   LastDefRules(a) <_s LastDefRules(b)
        #   OR (both have empty LastDefRules AND Prem_p(a) <_s Prem_p(b))
        ldr_a = last_def_rules(a)
        ldr_b = last_def_rules(b)
        if ldr_a or ldr_b:
            # At least one has last defeasible rules — compare rules
            return _set_strictly_less(
                ldr_a, ldr_b, pref.rule_order, pref.comparison
            )
        else:
            # Both have empty LastDefRules — compare ordinary premises
            return _set_strictly_less(
                prem_p(a), prem_p(b), pref.premise_order, pref.comparison
            )
    elif pref.link == "weakest":
        # Def 21 (p.21): Weakest-link principle
        # a prec b iff:
        #   If both strict: Prem_p(a) <_s Prem_p(b)
        #   If both firm: DefRules(a) <_s DefRules(b)
        #   Otherwise: Prem_p(a) <_s Prem_p(b) AND DefRules(a) <_s DefRules(b)
        a_strict = is_strict(a)
        b_strict = is_strict(b)
        a_firm = is_firm(a)
        b_firm = is_firm(b)

        if a_strict and b_strict:
            # Both strict — compare ordinary premises only
            return _set_strictly_less(
                prem_p(a), prem_p(b), pref.premise_order, pref.comparison
            )
        elif a_firm and b_firm:
            # Both firm — compare defeasible rules only
            return _set_strictly_less(
                def_rules(a), def_rules(b), pref.rule_order, pref.comparison
            )
        else:
            # General case — both conditions must hold
            return (
                _set_strictly_less(
                    prem_p(a), prem_p(b), pref.premise_order, pref.comparison
                )
                and _set_strictly_less(
                    def_rules(a), def_rules(b), pref.rule_order, pref.comparison
                )
            )
    else:
        raise ValueError(f"Unknown link mode: {pref.link}")


def compute_defeats(
    attacks: frozenset[Attack],
    arguments: frozenset[Argument],
    system: ArgumentationSystem,
    kb: KnowledgeBase,
    pref: PreferenceConfig,
) -> frozenset[Attack]:
    """Filter attacks into defeats using preference orderings.

    Modgil & Prakken 2018, Def 9 (p.12):
    - Undercutting: ALWAYS a defeat. No preference check.
      (Pollock 1987, Def 2.5, p.485)
    - Rebutting A on B': defeat iff A is NOT strictly weaker than B'.
    - Undermining A on B': defeat iff A is NOT strictly weaker than B'.

    The preference comparison is between the attacker A and the targeted
    sub-argument B' (attack.target_sub), not the whole target B.

    Args:
        attacks: The set of all attacks from compute_attacks.
        arguments: The set of all arguments.
        system: The argumentation system.
        kb: The knowledge base.
        pref: Preference configuration (orderings, comparison, link).

    Returns:
        Frozenset of Attack instances that succeed as defeats.
    """
    defeats: set[Attack] = set()

    for atk in attacks:
        if atk.kind == "undercutting":
            # Undercutting always succeeds (Def 9, p.12;
            # Pollock 1987, Def 2.5, p.485)
            defeats.add(atk)
        elif atk.attacker == atk.target:
            # Self-attacks always succeed as defeats. An argument that
            # attacks itself is already self-conflicted; the preference
            # comparison A vs B' (where B' is a sub-argument of A = B)
            # is moot because A cannot be in any admissible extension
            # with itself regardless. This follows from irreflexivity of
            # the argument ordering (Def 22, p.22): A ⊁ A, and by
            # extension no argument can be "defeated by itself" in a
            # way that preferences could prevent.
            defeats.add(atk)
        else:
            # Rebutting or undermining: defeat iff attacker is NOT
            # strictly weaker than the targeted sub-argument (Def 9, p.12)
            if not _strictly_weaker(atk.attacker, atk.target_sub, pref, kb):
                defeats.add(atk)

    return frozenset(defeats)


# ── Complete Structured Argumentation Framework ──────────────────


@dataclass(frozen=True)
class CSAF:
    """Complete Structured Argumentation Framework.

    Bundles all components of a well-formed c-SAF for property testing:
    the argumentation system, knowledge base, preference configuration,
    computed arguments/attacks/defeats, and the derived Dung AF.

    Modgil & Prakken 2018, Def 12 (p.13): a c-SAF is well-defined iff
    it is axiom consistent, well-formed, and closed under transposition.

    Attributes:
        system: The argumentation system (L, contrariness, R_s, R_d).
        kb: The knowledge base (K_n, K_p).
        pref: The preference configuration (orderings, comparison, link).
        arguments: All arguments built from the system and KB.
        attacks: All attacks between arguments (Attack objects).
        defeats: Defeat pairs (attacker, target) after preference filtering.
        framework: The derived Dung AF for extension computation.
        arg_to_id: Mapping from Argument to string ID.
        id_to_arg: Mapping from string ID to Argument.
    """
    system: ArgumentationSystem
    kb: KnowledgeBase
    pref: PreferenceConfig
    arguments: frozenset[Argument]
    attacks: frozenset[Attack]
    defeats: frozenset[tuple[Argument, Argument]]
    framework: ArgumentationFramework  # from dung.py
    arg_to_id: dict  # Argument -> str
    id_to_arg: dict  # str -> Argument
