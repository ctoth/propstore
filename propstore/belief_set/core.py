from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from itertools import combinations

from propstore.belief_set.language import Formula, World


@dataclass(frozen=True, slots=True)
class BeliefSet:
    """Finite propositional theory represented extensionally by its models."""

    alphabet: frozenset[str]
    models: frozenset[World]

    def __post_init__(self) -> None:
        normalized_alphabet = frozenset(str(atom) for atom in self.alphabet)
        valid_worlds = self.all_worlds(normalized_alphabet)
        normalized_models = frozenset(frozenset(world) for world in self.models)
        if not normalized_models <= valid_worlds:
            raise ValueError("BeliefSet models must be worlds over the declared alphabet")
        object.__setattr__(self, "alphabet", normalized_alphabet)
        object.__setattr__(self, "models", normalized_models)

    @property
    def is_consistent(self) -> bool:
        return bool(self.models)

    @classmethod
    def all_worlds(cls, alphabet: frozenset[str]) -> frozenset[World]:
        ordered = tuple(sorted(alphabet))
        worlds: set[World] = set()
        for size in range(len(ordered) + 1):
            for true_atoms in combinations(ordered, size):
                worlds.add(frozenset(true_atoms))
        return frozenset(worlds)

    @classmethod
    def tautology(cls, alphabet: frozenset[str]) -> BeliefSet:
        return cls(alphabet=frozenset(alphabet), models=cls.all_worlds(frozenset(alphabet)))

    @classmethod
    def contradiction(cls, alphabet: frozenset[str]) -> BeliefSet:
        return cls(alphabet=frozenset(alphabet), models=frozenset())

    @classmethod
    def from_formula(cls, alphabet: frozenset[str], formula: Formula) -> BeliefSet:
        signature = frozenset(alphabet) | formula.atoms()
        return cls(
            alphabet=signature,
            models=frozenset(
                world for world in cls.all_worlds(signature) if formula.evaluate(world)
            ),
        )

    def cn(self) -> BeliefSet:
        return self

    def equivalent(self, other: BeliefSet) -> bool:
        left, right = align_belief_sets(self, other)
        return left.models == right.models

    def entails(self, formula: Formula) -> bool:
        signature = self.alphabet | formula.atoms()
        aligned = self.with_alphabet(signature)
        return all(formula.evaluate(world) for world in aligned.models)

    def with_alphabet(self, alphabet: frozenset[str]) -> BeliefSet:
        signature = self.alphabet | alphabet
        if signature == self.alphabet:
            return self
        extras = tuple(sorted(signature - self.alphabet))
        expanded_models: set[World] = set()
        for model in self.models:
            for extension in self.all_worlds(frozenset(extras)):
                expanded_models.add(frozenset(set(model) | set(extension)))
        return BeliefSet(signature, frozenset(expanded_models))

    def intersection_theory(self, other: BeliefSet) -> BeliefSet:
        """Return the theory intersection, represented by union of model sets."""
        left, right = align_belief_sets(self, other)
        return BeliefSet(left.alphabet, left.models | right.models)

    def conjunction_with_formula(self, formula: Formula) -> BeliefSet:
        signature = self.alphabet | formula.atoms()
        aligned = self.with_alphabet(signature)
        return BeliefSet(
            signature,
            frozenset(world for world in aligned.models if formula.evaluate(world)),
        )

    def fingerprint(self) -> str:
        payload = {
            "alphabet": sorted(self.alphabet),
            "models": [sorted(world) for world in sorted(self.models, key=lambda item: tuple(sorted(item)))],
        }
        body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha1(body.encode("utf-8")).hexdigest()


def align_belief_sets(left: BeliefSet, right: BeliefSet) -> tuple[BeliefSet, BeliefSet]:
    signature = left.alphabet | right.alphabet
    return left.with_alphabet(signature), right.with_alphabet(signature)


def theory_subset(left: BeliefSet, right: BeliefSet) -> bool:
    """Whether every formula entailed by ``left`` is also entailed by ``right``."""
    aligned_left, aligned_right = align_belief_sets(left, right)
    return aligned_right.models.issubset(aligned_left.models)


def expand(belief_set: BeliefSet, formula: Formula) -> BeliefSet:
    return belief_set.conjunction_with_formula(formula)
