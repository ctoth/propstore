from __future__ import annotations

from dataclasses import dataclass

from propstore.belief_set.core import BeliefSet, expand
from propstore.belief_set.language import Formula, World, negate
from propstore.provenance import Provenance, ProvenanceStatus, ProvenanceWitness


@dataclass(frozen=True, slots=True)
class RevisionTrace:
    operator: str
    pre_image_fingerprint: str
    provenance: Provenance


@dataclass(frozen=True, slots=True)
class RevisionOutcome:
    belief_set: BeliefSet
    state: SpohnEpistemicState
    trace: RevisionTrace


@dataclass(frozen=True, slots=True)
class SpohnEpistemicState:
    """Finite ordinal conditional function over propositional worlds."""

    alphabet: frozenset[str]
    ranks: dict[World, int]

    def __post_init__(self) -> None:
        signature = frozenset(self.alphabet)
        worlds = BeliefSet.all_worlds(signature)
        if set(self.ranks) != set(worlds):
            raise ValueError("SpohnEpistemicState ranks must cover every world in the alphabet")
        min_rank = min(self.ranks.values(), default=0)
        object.__setattr__(
            self,
            "ranks",
            {frozenset(world): max(0, int(rank) - min_rank) for world, rank in self.ranks.items()},
        )
        object.__setattr__(self, "alphabet", signature)

    @classmethod
    def from_ranks(
        cls,
        alphabet: frozenset[str],
        ranks: dict[World, int],
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
        return BeliefSet(
            self.alphabet,
            frozenset(world for world, rank in self.ranks.items() if rank == min_rank),
        )


def revise(state: SpohnEpistemicState, formula: Formula) -> RevisionOutcome:
    """Darwiche-Pearl 1997 bullet revision over a Spohn ranking."""
    signature = state.alphabet | formula.atoms()
    working_state = _extend_state(state, signature)
    worlds = BeliefSet.all_worlds(signature)
    satisfying = tuple(world for world in worlds if formula.evaluate(world))
    if not satisfying:
        result_state = working_state
    else:
        min_formula_rank = min(working_state.ranks[world] for world in satisfying)
        revised_ranks: dict[World, int] = {}
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
        trace=_trace("revise", state.belief_set),
    )


def full_meet_contract(state: SpohnEpistemicState, formula: Formula) -> RevisionOutcome:
    """AGM contraction using the Harper identity over the finite theory."""
    if not state.belief_set.entails(formula):
        return RevisionOutcome(
            belief_set=state.belief_set,
            state=state,
            trace=_trace("contract", state.belief_set),
        )
    revised_by_negation = revise(state, negate(formula))
    contracted = state.belief_set.intersection_theory(revised_by_negation.belief_set)
    return RevisionOutcome(
        belief_set=contracted,
        state=SpohnEpistemicState.from_belief_set(contracted),
        trace=_trace("contract", state.belief_set),
    )


def _extend_state(state: SpohnEpistemicState, alphabet: frozenset[str]) -> SpohnEpistemicState:
    if alphabet == state.alphabet:
        return state
    extras = tuple(sorted(alphabet - state.alphabet))
    ranks: dict[World, int] = {}
    for world, rank in state.ranks.items():
        for extension in BeliefSet.all_worlds(frozenset(extras)):
            ranks[frozenset(set(world) | set(extension))] = rank
    return SpohnEpistemicState.from_ranks(alphabet, ranks)


def _trace(operator: str, pre_image: BeliefSet) -> RevisionTrace:
    graph_name = f"urn:propstore:belief-set:{operator}:{pre_image.fingerprint()}"
    provenance = Provenance(
        status=ProvenanceStatus.STATED,
        witnesses=(
            ProvenanceWitness(
                asserter="propstore",
                timestamp="1970-01-01T00:00:00Z",
                source_artifact_code="ws-b-belief-set-layer",
                method=operator,
            ),
        ),
        graph_name=graph_name,
        operations=(operator,),
    )
    return RevisionTrace(
        operator=operator,
        pre_image_fingerprint=pre_image.fingerprint(),
        provenance=provenance,
    )
