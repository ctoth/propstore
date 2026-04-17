from __future__ import annotations

from propstore.belief_set.agm import RevisionOutcome, SpohnEpistemicState, _trace, revise
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
            trace=_trace("lexicographic_revise", state.belief_set),
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
        trace=_trace("lexicographic_revise", state.belief_set),
    )


def restrained_revise(
    state: SpohnEpistemicState,
    formula: Formula,
) -> RevisionOutcome:
    """Booth-Meyer restrained revision represented by conservative Spohn update."""
    result = revise(state, formula)
    return RevisionOutcome(
        belief_set=result.belief_set,
        state=result.state,
        trace=_trace("restrained_revise", state.belief_set),
    )


def _dense_ranks(keys: dict[World, tuple[int, int]]) -> dict[World, int]:
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
