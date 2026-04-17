"""Exact merge operators over tiny argumentation-framework profiles."""
from __future__ import annotations

from itertools import combinations, product

from propstore.dung import ArgumentationFramework
from propstore.storage.merge_framework import (
    PartialArgumentationFramework,
    merge_framework_edit_distance,
)

AttackPair = tuple[str, str]


def _attack_relation(framework: ArgumentationFramework) -> frozenset[AttackPair]:
    return framework.attacks if framework.attacks is not None else framework.defeats


def consensual_expand(
    framework: ArgumentationFramework,
    universe: frozenset[str],
) -> PartialArgumentationFramework:
    """Expand an AF to a shared universe using ignorance outside source scope."""
    source_arguments = frozenset(framework.arguments)
    attack_relation = _attack_relation(framework)
    attacks: set[AttackPair] = set()
    ignorance: set[AttackPair] = set()
    non_attacks: set[AttackPair] = set()

    for pair in product(universe, universe):
        attacker, target = pair
        if attacker in source_arguments and target in source_arguments:
            if pair in attack_relation:
                attacks.add(pair)
            else:
                non_attacks.add(pair)
        else:
            ignorance.add(pair)

    return PartialArgumentationFramework(
        arguments=universe,
        attacks=frozenset(attacks),
        ignorance=frozenset(ignorance),
        non_attacks=frozenset(non_attacks),
    )


def _candidate_frameworks(arguments: frozenset[str]) -> list[ArgumentationFramework]:
    ordered_pairs = sorted(product(arguments, arguments))
    candidates: list[ArgumentationFramework] = []
    for size in range(len(ordered_pairs) + 1):
        for selected in combinations(ordered_pairs, size):
            attacks = frozenset(selected)
            candidates.append(
                ArgumentationFramework(
                    arguments=arguments,
                    defeats=attacks,
                    attacks=attacks,
                )
            )
    return candidates


def _expanded_profile(
    profile: dict[str, ArgumentationFramework],
    universe: frozenset[str],
) -> dict[str, PartialArgumentationFramework]:
    return {
        source: consensual_expand(framework, universe)
        for source, framework in profile.items()
    }


def _framework_key(framework: ArgumentationFramework) -> tuple[tuple[str, str], ...]:
    return tuple(sorted(_attack_relation(framework)))


def _shared_universe(profile: dict[str, ArgumentationFramework]) -> frozenset[str]:
    if not profile:
        raise ValueError("merge profile must not be empty")
    return frozenset().union(*(framework.arguments for framework in profile.values()))


def sum_merge_frameworks(
    profile: dict[str, ArgumentationFramework],
) -> list[ArgumentationFramework]:
    """Return exact Sum-minimizing AFs over the shared argument universe."""
    universe = _shared_universe(profile)
    expanded = _expanded_profile(profile, universe)
    candidates = _candidate_frameworks(universe)

    best_score: int | None = None
    winners: list[ArgumentationFramework] = []
    for candidate in candidates:
        score = sum(
            merge_framework_edit_distance(candidate, source_framework)
            for source_framework in expanded.values()
        )
        if best_score is None or score < best_score:
            best_score = score
            winners = [candidate]
        elif score == best_score:
            winners.append(candidate)
    return sorted(winners, key=_framework_key)


def max_merge_frameworks(
    profile: dict[str, ArgumentationFramework],
) -> list[ArgumentationFramework]:
    """Return exact Max-minimizing AFs over the shared argument universe."""
    universe = _shared_universe(profile)
    expanded = _expanded_profile(profile, universe)
    candidates = _candidate_frameworks(universe)

    best_score: int | None = None
    winners: list[ArgumentationFramework] = []
    for candidate in candidates:
        score = max(
            merge_framework_edit_distance(candidate, source_framework)
            for source_framework in expanded.values()
        )
        if best_score is None or score < best_score:
            best_score = score
            winners = [candidate]
        elif score == best_score:
            winners.append(candidate)
    return sorted(winners, key=_framework_key)


def leximax_merge_frameworks(
    profile: dict[str, ArgumentationFramework],
) -> list[ArgumentationFramework]:
    """Return exact Leximax-minimizing AFs over the shared argument universe."""
    universe = _shared_universe(profile)
    expanded = _expanded_profile(profile, universe)
    max_winners = max_merge_frameworks(profile)

    best_vector: tuple[int, ...] | None = None
    winners: list[ArgumentationFramework] = []
    for candidate in max_winners:
        vector = tuple(
            sorted(
                (
                    merge_framework_edit_distance(candidate, source_framework)
                    for source_framework in expanded.values()
                ),
                reverse=True,
            )
        )
        if best_vector is None or vector < best_vector:
            best_vector = vector
            winners = [candidate]
        elif vector == best_vector:
            winners.append(candidate)
    return sorted(winners, key=_framework_key)


__all__ = [
    "consensual_expand",
    "sum_merge_frameworks",
    "max_merge_frameworks",
    "leximax_merge_frameworks",
]
