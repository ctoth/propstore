from __future__ import annotations

from propstore.belief_set.agm import (
    RevisionOutcome,
    SpohnEpistemicState,
    revision_trace,
)
from propstore.belief_set.core import BeliefSet
from propstore.belief_set.language import Formula, World


def lexicographic_revise(
    state: SpohnEpistemicState,
    formula: Formula,
) -> RevisionOutcome:
    """Nayak-Spohn lexicographic revision over a world preorder."""
    signature = state.alphabet | formula.atoms()
    working = _extend_state(state, signature)
    worlds = tuple(BeliefSet.all_worlds(signature))
    if not any(formula.evaluate(world) for world in worlds):
        return RevisionOutcome(
            belief_set=working.belief_set,
            state=working,
            trace=revision_trace("lexicographic_revise", state.belief_set),
        )
    keys: dict[World, tuple[int, int]] = {
        world: (0, working.ranks[world])
        if formula.evaluate(world)
        else (1, working.ranks[world])
        for world in worlds
    }
    revised_ranks = _dense_ranks(keys)
    revised_state = SpohnEpistemicState.from_ranks(signature, revised_ranks)
    return RevisionOutcome(
        belief_set=revised_state.belief_set,
        state=revised_state,
        trace=revision_trace("lexicographic_revise", state.belief_set),
    )


def restrained_revise(
    state: SpohnEpistemicState,
    formula: Formula,
) -> RevisionOutcome:
    """Booth-Meyer restrained revision over a world preorder.

    Booth and Meyer, JAIR 26 (2006), Definition 4 (RR): outside the
    post-revision minimal alpha-worlds, old strict order is preserved and
    same-rank alpha/not-alpha ties split in favor of alpha-worlds.
    """
    signature = state.alphabet | formula.atoms()
    working = _extend_state(state, signature)
    worlds = tuple(BeliefSet.all_worlds(signature))
    satisfying = tuple(world for world in worlds if formula.evaluate(world))
    if not satisfying:
        return RevisionOutcome(
            belief_set=working.belief_set,
            state=working,
            trace=revision_trace("restrained_revise", state.belief_set),
        )

    min_formula_rank = min(working.ranks[world] for world in satisfying)
    minimal_formula_worlds = frozenset(
        world for world in satisfying if working.ranks[world] == min_formula_rank
    )
    keys: dict[World, tuple[int, ...]] = {}
    for world in worlds:
        if world in minimal_formula_worlds:
            keys[world] = (0,)
            continue

        # RR keeps old strict order and splits only same-rank alpha/not-alpha ties.
        alpha_tie_priority = 0 if formula.evaluate(world) else 1
        keys[world] = (1, working.ranks[world], alpha_tie_priority)

    revised_state = SpohnEpistemicState.from_ranks(signature, _dense_ranks(keys))
    return RevisionOutcome(
        belief_set=revised_state.belief_set,
        state=revised_state,
        trace=revision_trace("restrained_revise", state.belief_set),
    )


def _dense_ranks(keys: dict[World, tuple[int, ...]]) -> dict[World, int]:
    ordered_keys = {
        key: index
        for index, key in enumerate(sorted(set(keys.values())))
    }
    return {world: ordered_keys[key] for world, key in keys.items()}


def _extend_state(state: SpohnEpistemicState, alphabet: frozenset[str]) -> SpohnEpistemicState:
    if alphabet == state.alphabet:
        return state
    extras = tuple(sorted(alphabet - state.alphabet))
    ranks: dict[World, int] = {}
    for world, rank in state.ranks.items():
        for extension in BeliefSet.all_worlds(frozenset(extras)):
            ranks[frozenset(set(world) | set(extension))] = rank
    return SpohnEpistemicState.from_ranks(alphabet, ranks)
