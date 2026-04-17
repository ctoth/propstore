from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeAlias


World: TypeAlias = frozenset[str]


class Formula(Protocol):
    def evaluate(self, world: World) -> bool: ...

    def atoms(self) -> frozenset[str]: ...


@dataclass(frozen=True, slots=True)
class Top:
    def evaluate(self, world: World) -> bool:
        return True

    def atoms(self) -> frozenset[str]:
        return frozenset()


@dataclass(frozen=True, slots=True)
class Bottom:
    def evaluate(self, world: World) -> bool:
        return False

    def atoms(self) -> frozenset[str]:
        return frozenset()


@dataclass(frozen=True, slots=True)
class Atom:
    name: str

    def evaluate(self, world: World) -> bool:
        return self.name in world

    def atoms(self) -> frozenset[str]:
        return frozenset((self.name,))

    def or_(self, other: Formula) -> Formula:
        return disjunction(self, other)

    def and_(self, other: Formula) -> Formula:
        return conjunction(self, other)


@dataclass(frozen=True, slots=True)
class Not:
    formula: Formula

    def evaluate(self, world: World) -> bool:
        return not self.formula.evaluate(world)

    def atoms(self) -> frozenset[str]:
        return self.formula.atoms()


@dataclass(frozen=True, slots=True)
class And:
    formulas: tuple[Formula, ...]

    def evaluate(self, world: World) -> bool:
        return all(formula.evaluate(world) for formula in self.formulas)

    def atoms(self) -> frozenset[str]:
        return frozenset(atom for formula in self.formulas for atom in formula.atoms())


@dataclass(frozen=True, slots=True)
class Or:
    formulas: tuple[Formula, ...]

    def evaluate(self, world: World) -> bool:
        return any(formula.evaluate(world) for formula in self.formulas)

    def atoms(self) -> frozenset[str]:
        return frozenset(atom for formula in self.formulas for atom in formula.atoms())


TOP = Top()
BOTTOM = Bottom()


def negate(formula: Formula) -> Formula:
    if isinstance(formula, Top):
        return BOTTOM
    if isinstance(formula, Bottom):
        return TOP
    if isinstance(formula, Not):
        return formula.formula
    return Not(formula)


def conjunction(*formulas: Formula) -> Formula:
    flattened: list[Formula] = []
    for formula in formulas:
        if isinstance(formula, Bottom):
            return BOTTOM
        if isinstance(formula, Top):
            continue
        if isinstance(formula, And):
            flattened.extend(formula.formulas)
            continue
        flattened.append(formula)
    if not flattened:
        return TOP
    if len(flattened) == 1:
        return flattened[0]
    return And(tuple(flattened))


def disjunction(*formulas: Formula) -> Formula:
    flattened: list[Formula] = []
    for formula in formulas:
        if isinstance(formula, Top):
            return TOP
        if isinstance(formula, Bottom):
            continue
        if isinstance(formula, Or):
            flattened.extend(formula.formulas)
            continue
        flattened.append(formula)
    if not flattened:
        return BOTTOM
    if len(flattened) == 1:
        return flattened[0]
    return Or(tuple(flattened))


def equivalent(left: Formula, right: Formula, *, alphabet: frozenset[str] | None = None) -> bool:
    from propstore.belief_set.core import BeliefSet

    signature = frozenset(alphabet or (left.atoms() | right.atoms()))
    return BeliefSet.from_formula(signature, left).models == BeliefSet.from_formula(signature, right).models
