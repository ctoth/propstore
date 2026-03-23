"""z3 SAT-backed Dung extension computation.

Provides SAT-encoded alternatives to the brute-force extension
computation in dung.py. Results are identical but scale better
for large argumentation frameworks.

References:
    Dung, P.M. (1995). On the acceptability of arguments and its
    fundamental role in nonmonotonic reasoning, logic programming
    and n-person games. Artificial Intelligence, 77(2), 321-357.
"""

from __future__ import annotations

from z3 import Bool, And, Or, Not, Implies, Solver, sat

from propstore.dung import ArgumentationFramework, attackers_of


def _make_vars(
    framework: ArgumentationFramework,
) -> dict[str, Bool]:
    """Create one z3 Bool variable per argument."""
    return {a: Bool(f"in_{a}") for a in sorted(framework.arguments)}


def _conflict_free_constraints(
    framework: ArgumentationFramework,
    v: dict[str, Bool],
) -> list:
    """Conflict-free: no two args in the set attack each other.

    Per Modgil & Prakken 2018 Def 14, uses attacks (pre-preference)
    when available, falls back to defeats for pure Dung AFs.
    """
    cf_relation = framework.attacks if framework.attacks is not None else framework.defeats
    return [Not(And(v[a], v[b])) for a, b in cf_relation]


def _extract_extension(
    v: dict[str, Bool],
    model,
) -> frozenset[str]:
    """Extract the extension (set of accepted args) from a z3 model."""
    return frozenset(a for a, var in v.items() if model[var])


def _block_solution(
    v: dict[str, Bool],
    extension: frozenset[str],
) -> list:
    """Add a blocking clause to exclude an already-found extension."""
    # The clause says: at least one variable must differ from this solution
    clause_parts = []
    for a, var in v.items():
        if a in extension:
            clause_parts.append(Not(var))
        else:
            clause_parts.append(var)
    return [Or(*clause_parts)] if clause_parts else []


# ── Stable extensions ──────────────────────────────────────────────


def z3_stable_extensions(
    framework: ArgumentationFramework,
) -> list[frozenset[str]]:
    """Compute all stable extensions using z3 SAT encoding.

    A stable extension S is conflict-free and every argument outside S
    is defeated by some member of S.
    """
    if not framework.arguments:
        return [frozenset()]

    v = _make_vars(framework)
    args = sorted(framework.arguments)
    defeats = framework.defeats

    base_constraints = []

    # Conflict-free
    base_constraints.extend(_conflict_free_constraints(framework, v))

    # Every outsider must be attacked by some member of S
    for a in args:
        atks = attackers_of(a, defeats)
        if atks:
            # If a is out, some attacker must be in
            base_constraints.append(
                Or(v[a], Or(*[v[b] for b in atks]))
            )
        else:
            # No attackers: a must be in (undefeated)
            base_constraints.append(v[a])

    # Enumerate all solutions
    results: list[frozenset[str]] = []
    solver = Solver()
    solver.add(*base_constraints)

    while solver.check() == sat:
        model = solver.model()
        ext = _extract_extension(v, model)
        results.append(ext)
        solver.add(*_block_solution(v, ext))

    return results


# ── Complete extensions ────────────────────────────────────────────


def z3_complete_extensions(
    framework: ArgumentationFramework,
) -> list[frozenset[str]]:
    """Compute all complete extensions using z3 SAT encoding.

    A complete extension S is admissible and a fixed point of F:
    S = {a | S defends a}.
    """
    if not framework.arguments:
        return [frozenset()]

    v = _make_vars(framework)
    args = sorted(framework.arguments)
    defeats = framework.defeats

    base_constraints = []

    # Conflict-free
    base_constraints.extend(_conflict_free_constraints(framework, v))

    # Defense: if a is in S, then for each attacker b of a,
    # some defender d in S must attack b
    for a in args:
        for b in attackers_of(a, defeats):
            defenders = [d for d in args if (d, b) in defeats]
            if defenders:
                base_constraints.append(
                    Implies(v[a], Or(*[v[d] for d in defenders]))
                )
            else:
                # b has no counter-attackers, so a can't be in S if b exists
                base_constraints.append(Not(v[a]))

    # Fixed point (completeness): if a is defended by S, then a must be in S.
    # defended(a) means: for every attacker b of a, some d in S attacks b.
    # We encode: if for every attacker b of a there exists d in S with (d,b),
    # then a must be in S.
    for a in args:
        atks = list(attackers_of(a, defeats))
        if not atks:
            # No attackers => always defended => must be in S
            base_constraints.append(v[a])
        else:
            # defended(a) = AND over attackers b: OR over defenders d: v[d]
            defended_parts = []
            all_defended = True
            for b in atks:
                defenders = [d for d in args if (d, b) in defeats]
                if defenders:
                    defended_parts.append(Or(*[v[d] for d in defenders]))
                else:
                    # b has no counter-attackers, so a is never defended
                    all_defended = False
                    break

            if all_defended and defended_parts:
                defended_a = And(*defended_parts) if len(defended_parts) > 1 else defended_parts[0]
                base_constraints.append(Implies(defended_a, v[a]))

    # Enumerate
    results: list[frozenset[str]] = []
    solver = Solver()
    solver.add(*base_constraints)

    while solver.check() == sat:
        model = solver.model()
        ext = _extract_extension(v, model)
        results.append(ext)
        solver.add(*_block_solution(v, ext))

    return results


# ── Preferred extensions (CEGAR) ───────────────────────────────────


def z3_preferred_extensions(
    framework: ArgumentationFramework,
) -> list[frozenset[str]]:
    """Compute all preferred extensions using CEGAR approach.

    Preferred extensions are maximal complete extensions.
    1. Find complete extensions
    2. Filter to those that are maximal (no strictly larger complete ext)
    """
    completes = z3_complete_extensions(framework)
    maximal: list[frozenset[str]] = []
    for ext in completes:
        if not any(ext < other for other in completes):
            maximal.append(ext)
    return maximal


# ── Acceptance queries ─────────────────────────────────────────────


def credulously_accepted(
    framework: ArgumentationFramework,
    arg: str,
    *,
    semantics: str = "preferred",
) -> bool:
    """Check if arg is credulously accepted (in at least one extension)."""
    extensions = _extensions_for_semantics(framework, semantics)
    return any(arg in ext for ext in extensions)


def skeptically_accepted(
    framework: ArgumentationFramework,
    arg: str,
    *,
    semantics: str = "preferred",
) -> bool:
    """Check if arg is skeptically accepted (in all extensions).

    If there are no extensions (e.g. no stable extension exists),
    returns False.
    """
    extensions = _extensions_for_semantics(framework, semantics)
    if not extensions:
        return False
    return all(arg in ext for ext in extensions)


def _extensions_for_semantics(
    framework: ArgumentationFramework,
    semantics: str,
) -> list[frozenset[str]]:
    """Dispatch to the appropriate z3 extension function."""
    if semantics == "stable":
        return z3_stable_extensions(framework)
    elif semantics == "complete":
        return z3_complete_extensions(framework)
    elif semantics == "preferred":
        return z3_preferred_extensions(framework)
    else:
        msg = f"Unknown semantics: {semantics}"
        raise ValueError(msg)
