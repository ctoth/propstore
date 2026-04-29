from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone

from propstore.belief_set.core import BeliefSet
from propstore.belief_set.language import Formula, World, negate
from propstore.core.anytime import EnumerationExceeded
from propstore.provenance import Provenance, ProvenanceStatus, ProvenanceWitness


MAX_ALPHABET_SIZE = 16


@dataclass(frozen=True, slots=True)
class RevisionTrace:
    operator: str
    pre_image_fingerprint: str
    provenance: Provenance
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class RevisionOutcome:
    belief_set: BeliefSet
    state: SpohnEpistemicState
    trace: RevisionTrace


@dataclass(frozen=True, slots=True)
class SpohnEpistemicState:
    """Finite ordinal conditional function over propositional worlds."""

    alphabet: frozenset[str]
    ranks: dict[World, int | float]

    def __post_init__(self) -> None:
        signature = frozenset(self.alphabet)
        worlds = BeliefSet.all_worlds(signature)
        if set(self.ranks) != set(worlds):
            raise ValueError("SpohnEpistemicState ranks must cover every world in the alphabet")
        if all(math.isinf(float(rank)) for rank in self.ranks.values()):
            normalized_ranks = {frozenset(world): math.inf for world in self.ranks}
            object.__setattr__(self, "ranks", normalized_ranks)
            object.__setattr__(self, "alphabet", signature)
            return

        finite_ranks = [
            float(rank)
            for rank in self.ranks.values()
            if not math.isinf(float(rank))
        ]
        min_rank = min(finite_ranks, default=0.0)
        object.__setattr__(
            self,
            "ranks",
            {
                frozenset(world): _normalize_rank(rank, min_rank)
                for world, rank in self.ranks.items()
            },
        )
        object.__setattr__(self, "alphabet", signature)

    @classmethod
    def from_ranks(
        cls,
        alphabet: frozenset[str],
        ranks: Mapping[World, int | float],
    ) -> SpohnEpistemicState:
        return cls(alphabet=frozenset(alphabet), ranks=dict(ranks))

    @classmethod
    def from_belief_set(cls, belief_set: BeliefSet) -> SpohnEpistemicState:
        return cls(
            alphabet=belief_set.alphabet,
            ranks={
                world: 0 if world in belief_set.models else 1
                for world in BeliefSet.all_worlds(belief_set.alphabet)
            },
        )

    @property
    def belief_set(self) -> BeliefSet:
        min_rank = min(self.ranks.values(), default=0)
        if math.isinf(float(min_rank)):
            return BeliefSet.contradiction(self.alphabet)
        return BeliefSet(
            self.alphabet,
            frozenset(world for world, rank in self.ranks.items() if rank == min_rank),
        )


def revise(
    state: SpohnEpistemicState,
    formula: Formula,
    *,
    provenance: Provenance | None = None,
    max_alphabet_size: int = MAX_ALPHABET_SIZE,
) -> RevisionOutcome:
    """Darwiche-Pearl 1997 bullet revision over a Spohn ranking."""
    signature = state.alphabet | formula.atoms()
    _raise_if_alphabet_exceeds_budget(signature, max_alphabet_size)
    working_state = extend_state(state, signature)
    worlds = BeliefSet.all_worlds(signature)
    satisfying = tuple(world for world in worlds if formula.evaluate(world))
    if not satisfying:
        result_state = SpohnEpistemicState.from_ranks(
            signature,
            {world: math.inf for world in worlds},
        )
    else:
        min_formula_rank = min(working_state.ranks[world] for world in satisfying)
        revised_ranks: dict[World, int | float] = {}
        for world in worlds:
            current_rank = working_state.ranks[world]
            if formula.evaluate(world):
                revised_ranks[world] = current_rank - min_formula_rank
            else:
                revised_ranks[world] = current_rank + 1
        result_state = SpohnEpistemicState.from_ranks(signature, revised_ranks)
    return RevisionOutcome(
        belief_set=result_state.belief_set,
        state=result_state,
        trace=revision_trace("revise", state.belief_set, provenance=provenance),
    )


def full_meet_contract(
    state: SpohnEpistemicState,
    formula: Formula,
    *,
    provenance: Provenance | None = None,
) -> RevisionOutcome:
    """AGM contraction using the Harper identity over the finite theory."""
    if not state.belief_set.entails(formula):
        return RevisionOutcome(
            belief_set=state.belief_set,
            state=state,
            trace=revision_trace("contract", state.belief_set, provenance=provenance),
        )
    revised_by_negation = revise(state, negate(formula), provenance=provenance)
    contracted = state.belief_set.intersection_theory(revised_by_negation.belief_set)
    contracted_ranks = {
        world: min(state.ranks[world], revised_by_negation.state.ranks[world])
        for world in BeliefSet.all_worlds(state.alphabet)
    }
    return RevisionOutcome(
        belief_set=contracted,
        state=SpohnEpistemicState.from_ranks(state.alphabet, contracted_ranks),
        trace=revision_trace("contract", state.belief_set, provenance=provenance),
    )


def extend_state(state: SpohnEpistemicState, alphabet: frozenset[str]) -> SpohnEpistemicState:
    if alphabet == state.alphabet:
        return state
    extras = tuple(sorted(alphabet - state.alphabet))
    ranks: dict[World, int | float] = {}
    for world, rank in state.ranks.items():
        for extension in BeliefSet.all_worlds(frozenset(extras)):
            ranks[frozenset(set(world) | set(extension))] = rank
    return SpohnEpistemicState.from_ranks(alphabet, ranks)


def _normalize_rank(rank: int | float, min_rank: float) -> int | float:
    rank_value = float(rank)
    if math.isinf(rank_value):
        return math.inf
    normalized = max(0.0, rank_value - min_rank)
    if normalized.is_integer():
        return int(normalized)
    return normalized


def _raise_if_alphabet_exceeds_budget(
    signature: frozenset[str],
    max_alphabet_size: int,
) -> None:
    if max_alphabet_size < 0:
        raise ValueError("max_alphabet_size must be non-negative")
    if len(signature) > max_alphabet_size:
        raise EnumerationExceeded(
            partial_count=0,
            max_candidates=2 ** max_alphabet_size,
        )


def _trace_timestamp() -> datetime:
    return datetime.now(timezone.utc)


def _format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def revision_trace(
    operator: str,
    pre_image: BeliefSet,
    *,
    provenance: Provenance | None = None,
) -> RevisionTrace:
    timestamp = _trace_timestamp()
    graph_name = f"urn:propstore:belief-set:{operator}:{pre_image.fingerprint()}"
    trace_provenance = (
        provenance
        if provenance is not None
        else Provenance(
            status=ProvenanceStatus.VACUOUS,
            witnesses=(
                ProvenanceWitness(
                    asserter="propstore",
                    timestamp=_format_timestamp(timestamp),
                    source_artifact_code="propstore-belief-set",
                    method=operator,
                ),
            ),
            graph_name=graph_name,
            operations=(operator,),
        )
    )
    return RevisionTrace(
        operator=operator,
        pre_image_fingerprint=pre_image.fingerprint(),
        provenance=trace_provenance,
        timestamp=timestamp,
    )
