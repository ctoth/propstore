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
    """Dung's abstract argumentation framework AF = (Args, Defeats).

    Arguments are string identifiers. Defeats is a set of
    (attacker, target) pairs representing the defeat relation.
    """

    arguments: frozenset[str]
    defeats: frozenset[tuple[str, str]]


def attackers_of(arg: str, defeats: frozenset[tuple[str, str]]) -> frozenset[str]:
    """Return the set of all arguments that defeat `arg`."""
    return frozenset(a for a, t in defeats if t == arg)


def conflict_free(s: frozenset[str], defeats: frozenset[tuple[str, str]]) -> bool:
    """Check if s is conflict-free: no argument in s defeats another in s."""
    for a, t in defeats:
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
) -> bool:
    """Check if s is admissible: conflict-free and defends all its members.

    Reference: Dung 1995, Definition 6.
    """
    if not conflict_free(s, defeats):
        return False
    for a in s:
        if not defends(s, a, all_args, defeats):
            return False
    return True


def grounded_extension(framework: ArgumentationFramework) -> frozenset[str]:
    """Compute the unique grounded extension.

    The grounded extension is the least fixed point of F.
    Start with S = {} and iterate F until fixed point.

    Reference: Dung 1995, Definition 20 + Theorem 25.
    """
    s: frozenset[str] = frozenset()
    while True:
        next_s = characteristic_fn(s, framework.arguments, framework.defeats)
        if next_s == s:
            return s
        s = next_s


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
    results: list[frozenset[str]] = []

    for size in range(len(args) + 1):
        for subset in combinations(sorted(args), size):
            s = frozenset(subset)
            if characteristic_fn(s, args, defeats) == s and admissible(s, args, defeats):
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
    results: list[frozenset[str]] = []

    for size in range(len(args) + 1):
        for subset in combinations(sorted(args), size):
            s = frozenset(subset)
            if not conflict_free(s, defeats):
                continue
            outsiders = args - s
            if all(any((d, out) in defeats for d in s) for out in outsiders):
                results.append(s)

    return results
