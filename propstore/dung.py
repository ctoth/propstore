"""Dung's abstract argumentation framework and extension semantics.

Implements grounded, preferred, stable, and complete extensions
over an abstract argumentation framework AF = (Args, Defeats).

References:
    Dung, P.M. (1995). On the acceptability of arguments and its
    fundamental role in nonmonotonic reasoning, logic programming
    and n-person games. Artificial Intelligence, 77(2), 321-357.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations


@dataclass(frozen=True)
class ArgumentationFramework:
    """Argumentation framework with attack and defeat relations.

    Arguments are string identifiers. Defeats is a set of
    (attacker, target) pairs representing the defeat relation
    (attacks surviving preference filter). Attacks is the full
    set of attacks before preference filtering.

    When attacks is None (pure Dung AF without preferences),
    the defeat relation is used for both conflict-free and defense.

    References:
        Dung 1995: AF = (Args, Defeats)
        Modgil & Prakken 2018 Def 14: conflict-free uses attacks, not defeats
    """

    arguments: frozenset[str]
    defeats: frozenset[tuple[str, str]]
    attacks: frozenset[tuple[str, str]] | None = None


def attackers_of(arg: str, defeats: frozenset[tuple[str, str]]) -> frozenset[str]:
    """Return the set of all arguments that defeat `arg`."""
    return frozenset(a for a, t in defeats if t == arg)


def conflict_free(s: frozenset[str], relation: frozenset[tuple[str, str]]) -> bool:
    """Check if s is conflict-free w.r.t. a binary relation.

    No argument in s is related to another in s under the given relation.
    Per Modgil & Prakken 2018 Def 14, this should be the attack relation
    (pre-preference), not the defeat relation. When only defeats are
    available (pure Dung AF), pass defeats.
    """
    for a, t in relation:
        if a in s and t in s:
            return False
    return True


def defends(
    s: frozenset[str],
    arg: str,
    all_args: frozenset[str],  # noqa: ARG001
    defeats: frozenset[tuple[str, str]],
) -> bool:
    """Check if s defends arg: for every attacker of arg, s counter-attacks it."""
    for attacker in attackers_of(arg, defeats):
        if not any((d, attacker) in defeats for d in s):
            return False
    return True


def characteristic_fn(
    s: frozenset[str],
    all_args: frozenset[str],
    defeats: frozenset[tuple[str, str]],
) -> frozenset[str]:
    """Characteristic function F(S) = {A in Args | A is defended by S}.

    Reference: Dung 1995, Definition 17.
    """
    return frozenset(a for a in all_args if defends(s, a, all_args, defeats))


def admissible(
    s: frozenset[str],
    all_args: frozenset[str],
    defeats: frozenset[tuple[str, str]],
    *,
    attacks: frozenset[tuple[str, str]] | None = None,
) -> bool:
    """Check if s is admissible: conflict-free and defends all its members.

    Conflict-free is checked against attacks (Modgil & Prakken 2018 Def 14).
    Defense is checked against defeats (Dung 1995 Def 6).
    When attacks is None, defeats is used for both.
    """
    cf_relation = attacks if attacks is not None else defeats
    if not conflict_free(s, cf_relation):
        return False
    for a in s:
        if not defends(s, a, all_args, defeats):
            return False
    return True


def grounded_extension(framework: ArgumentationFramework) -> frozenset[str]:
    """Compute the unique grounded extension.

    The grounded extension is the least fixed point of F, filtered
    for attack-based conflict-freeness.

    Start with S = {} and iterate F until fixed point, then enforce
    conflict-freeness w.r.t. attacks (not just defeats).

    References:
        Dung 1995, Definition 20 + Theorem 25 (least fixed point).
        Modgil & Prakken 2018, Definition 14 (attack-based conflict-free).
    """
    s: frozenset[str] = frozenset()
    while True:
        next_s = characteristic_fn(s, framework.arguments, framework.defeats)
        if next_s == s:
            break
        s = next_s

    # Modgil & Prakken 2018 Def 14: conflict-free uses attacks, not defeats.
    # The characteristic function computes defense via defeats (correct per
    # Dung 1995), but the result must also be conflict-free w.r.t. attacks.
    cf_relation = framework.attacks if framework.attacks is not None else framework.defeats
    if cf_relation != framework.defeats:
        # Remove arguments attacked by peers, then re-verify the fixpoint.
        # Iterate until stable: removing an argument may leave another undefended.
        while True:
            attacked_in_ext = frozenset(
                b for (a, b) in cf_relation if a in s and b in s
            )
            if not attacked_in_ext:
                break
            s = s - attacked_in_ext
            # Re-compute fixpoint on the reduced set: some members may now
            # lack defenders, so shrink to the grounded kernel.
            while True:
                next_s = frozenset(
                    a for a in s
                    if defends(s, a, framework.arguments, framework.defeats)
                )
                if next_s == s:
                    break
                s = next_s

    return s


def complete_extensions(
    framework: ArgumentationFramework, *, backend: str = "brute_force"
) -> list[frozenset[str]]:
    """Compute all complete extensions.

    A complete extension is a fixed point of F that is admissible.

    Reference: Dung 1995, Definition 10.
    """
    if backend == "z3":
        from propstore.dung_z3 import z3_complete_extensions

        return z3_complete_extensions(framework)
    args = framework.arguments
    defeats = framework.defeats
    attacks = framework.attacks
    results: list[frozenset[str]] = []

    for size in range(len(args) + 1):
        for subset in combinations(sorted(args), size):
            s = frozenset(subset)
            if characteristic_fn(s, args, defeats) == s and admissible(
                s, args, defeats, attacks=attacks
            ):
                results.append(s)

    return results


def preferred_extensions(
    framework: ArgumentationFramework, *, backend: str = "brute_force"
) -> list[frozenset[str]]:
    """Compute all preferred extensions.

    A preferred extension is a maximal (w.r.t. set inclusion) admissible set,
    equivalently a maximal complete extension.

    Reference: Dung 1995, Definition 8.
    """
    if backend == "z3":
        from propstore.dung_z3 import z3_preferred_extensions

        return z3_preferred_extensions(framework)
    completes = complete_extensions(framework)
    maximal: list[frozenset[str]] = []
    for ext in completes:
        if not any(ext < other for other in completes):
            maximal.append(ext)
    return maximal


def stable_extensions(
    framework: ArgumentationFramework, *, backend: str = "brute_force"
) -> list[frozenset[str]]:
    """Compute all stable extensions.

    A stable extension is conflict-free and defeats every argument not in it.

    Reference: Dung 1995, Definition 12.
    WARNING: Stable extensions may not exist.
    """
    if backend == "z3":
        from propstore.dung_z3 import z3_stable_extensions

        return z3_stable_extensions(framework)
    args = framework.arguments
    defeats = framework.defeats
    cf_relation = framework.attacks if framework.attacks is not None else defeats
    results: list[frozenset[str]] = []

    for size in range(len(args) + 1):
        for subset in combinations(sorted(args), size):
            s = frozenset(subset)
            if not conflict_free(s, cf_relation):
                continue
            outsiders = args - s
            if all(any((d, out) in defeats for d in s) for out in outsiders):
                results.append(s)

    return results
