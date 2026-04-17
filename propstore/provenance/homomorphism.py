"""Homomorphic evaluation for provenance polynomials."""

from __future__ import annotations

from typing import Protocol, TypeVar

from propstore.provenance.polynomial import ProvenancePolynomial
from propstore.provenance.variables import SourceVariableId


K = TypeVar("K")


class Homomorphism(Protocol[K]):
    @property
    def zero(self) -> K: ...

    @property
    def one(self) -> K: ...

    def add(self, left: K, right: K) -> K: ...

    def mul(self, left: K, right: K) -> K: ...

    def variable(self, variable: SourceVariableId) -> K: ...


def evaluate(poly: ProvenancePolynomial, hom: Homomorphism[K]) -> K:
    total = hom.zero
    for term in poly.terms:
        value = hom.one
        for power in term.powers:
            base = hom.variable(power.variable)
            factor = hom.one
            for _ in range(power.exponent):
                factor = hom.mul(factor, base)
            value = hom.mul(value, factor)
        for _ in range(term.coefficient):
            total = hom.add(total, value)
    return total
