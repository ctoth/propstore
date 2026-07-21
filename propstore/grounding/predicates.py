"""The predicate registry and the ``derived_from`` fact-mining DSL.

The :class:`PredicateRegistry` indexes authored :class:`~propstore.families.predicates.Predicate`
charters by id and validates ground atoms against their declared arity and
argument types. :func:`parse_derived_from` parses a predicate's optional
fact-mining spec into a typed :class:`DerivedFromSpec` consumed by
:mod:`propstore.grounding.facts`.

Substrate boundary: argument types are matched against condition-ir's own
:class:`condition_ir.KindType` directly — there is no propstore mirror of that
enum. A declared ``arg_type`` string and a ``KindType`` member normalize to the
same lower-case token so authored vocab and typed kinds compare cleanly.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from condition_ir import KindType

from propstore.families.predicates import Predicate


class PredicateNotRegisteredError(KeyError):
    """Raised when a predicate id has no registered declaration."""


class PredicateArityMismatchError(ValueError):
    """Raised when an atom's argument count disagrees with the declared arity."""


class PredicateArgKindError(ValueError):
    """Raised when an atom's argument types disagree with the declaration."""


class DuplicatePredicateError(ValueError):
    """Raised when the same predicate id is declared more than once."""


class DerivedFromParseError(ValueError):
    """Raised when a ``derived_from`` spec is empty or malformed."""


DerivedFromKind = Literal[
    "concept_relation",
    "claim_attribute",
    "claim_condition",
    "claim_role",
    "claim_context",
    "claim_provenance",
]

PredicateArgumentType = str | KindType


@dataclass(frozen=True)
class DerivedFromSpec:
    """A parsed predicate fact-mining spec.

    Exactly the field for ``kind`` is populated; the rest stay ``None``.
    ``concept_relation`` carries ``relation`` + ``target`` (the target may itself
    contain ``:``); ``claim_attribute`` / ``claim_condition`` / ``claim_role`` /
    ``claim_provenance`` each carry their single segment; ``claim_context`` carries
    no payload.
    """

    kind: DerivedFromKind
    relation: str | None = None
    target: str | None = None
    attribute: str | None = None
    condition: str | None = None
    role: str | None = None
    provenance_field: str | None = None


@dataclass(frozen=True)
class PredicateAtom:
    """A candidate ground atom checked against a registered declaration."""

    predicate_id: str
    arguments: tuple[object, ...] = ()
    argument_types: tuple[PredicateArgumentType, ...] = ()


def parse_derived_from(spec: str) -> DerivedFromSpec:
    """Parse a ``derived_from`` spec string into a typed :class:`DerivedFromSpec`.

    Raises :class:`DerivedFromParseError` on an empty spec, a spec missing its
    ``':'`` separator, a missing/empty segment, or an unknown prefix.
    """

    if spec == "":
        raise DerivedFromParseError("derived_from spec must be a non-empty string")
    if spec == "claim.context":
        return DerivedFromSpec(kind="claim_context")
    if ":" not in spec:
        raise DerivedFromParseError(
            f"derived_from spec missing ':' separator: {spec!r}"
        )
    prefix, _, remainder = spec.partition(":")
    if prefix == "concept.relation":
        if ":" not in remainder:
            raise DerivedFromParseError(
                f"concept.relation spec missing target: {spec!r}"
            )
        relation, _, target = remainder.partition(":")
        if relation == "":
            raise DerivedFromParseError(
                f"concept.relation spec has empty relation: {spec!r}"
            )
        if target == "":
            raise DerivedFromParseError(
                f"concept.relation spec has empty target: {spec!r}"
            )
        return DerivedFromSpec(
            kind="concept_relation", relation=relation, target=target
        )
    if prefix == "claim.attribute":
        return DerivedFromSpec(
            kind="claim_attribute",
            attribute=_single_segment(spec, remainder, "attribute"),
        )
    if prefix == "claim.condition":
        return DerivedFromSpec(
            kind="claim_condition",
            condition=_single_segment(spec, remainder, "condition"),
        )
    if prefix == "claim.role":
        return DerivedFromSpec(
            kind="claim_role", role=_single_segment(spec, remainder, "role")
        )
    if prefix == "claim.provenance":
        return DerivedFromSpec(
            kind="claim_provenance",
            provenance_field=_single_segment(spec, remainder, "provenance"),
        )
    raise DerivedFromParseError(f"unknown derived_from prefix {prefix!r}: {spec!r}")


def _single_segment(spec: str, remainder: str, label: str) -> str:
    """Validate and return a single (colon-free, non-empty) payload segment."""

    if remainder == "":
        raise DerivedFromParseError(f"claim.{label} spec has empty {label}: {spec!r}")
    if ":" in remainder:
        raise DerivedFromParseError(
            f"claim.{label} spec has extra ':' in {label}: {spec!r}"
        )
    return remainder


class PredicateRegistry:
    """An id-indexed registry of declared predicates with atom validation."""

    def __init__(self, predicates: tuple[Predicate, ...]) -> None:
        self._predicates = predicates
        self._by_id: dict[str, Predicate] = {p.predicate_id: p for p in predicates}

    @classmethod
    def from_documents(cls, predicates: Iterable[Predicate]) -> PredicateRegistry:
        """Build a registry, rejecting a duplicated predicate id."""

        collected: list[Predicate] = []
        seen: set[str] = set()
        for predicate in predicates:
            if predicate.predicate_id in seen:
                raise DuplicatePredicateError(
                    f"duplicate predicate id {predicate.predicate_id!r} declared in multiple predicate artifacts"
                )
            seen.add(predicate.predicate_id)
            collected.append(predicate)
        return cls(tuple(collected))

    def lookup(self, predicate_id: str) -> Predicate:
        """Return the declaration for ``predicate_id`` or raise."""

        try:
            return self._by_id[predicate_id]
        except KeyError:
            raise PredicateNotRegisteredError(
                f"predicate {predicate_id!r} is not registered"
            ) from None

    def all_predicates(self) -> tuple[Predicate, ...]:
        """Every registered predicate, in declaration order."""

        return self._predicates

    def validate_atom(self, atom: PredicateAtom) -> None:
        """Validate ``atom`` against its declaration's arity and argument types."""

        declaration = self.lookup(atom.predicate_id)
        arity = len(atom.arguments)
        if declaration.arity != arity:
            raise PredicateArityMismatchError(
                f"predicate {atom.predicate_id!r} declared with arity {declaration.arity}, atom uses arity {arity}"
            )
        if len(declaration.arg_types) != declaration.arity:
            raise PredicateArityMismatchError(
                f"predicate {atom.predicate_id!r} declares {len(declaration.arg_types)} argument type(s) but arity {declaration.arity}"
            )
        if len(atom.argument_types) != arity:
            raise PredicateArgKindError(
                f"predicate {atom.predicate_id!r} atom has arity {arity}, but carries {len(atom.argument_types)} argument type(s)"
            )
        for index, (expected, observed) in enumerate(
            zip(declaration.arg_types, atom.argument_types, strict=True), start=1
        ):
            if _normalize_argument_type(expected) != _normalize_argument_type(observed):
                raise PredicateArgKindError(
                    f"predicate {atom.predicate_id!r} argument {index} declared as "
                    f"{_format_argument_type(expected)!r}, atom uses {_format_argument_type(observed)!r}"
                )


def _normalize_argument_type(value: PredicateArgumentType) -> str:
    """Lower a declared type string or a ``KindType`` to one comparison token."""

    if isinstance(value, KindType):
        return value.value
    return value.strip().lower()


def _format_argument_type(value: PredicateArgumentType) -> str:
    """Human-readable rendering of an argument type for error messages."""

    if isinstance(value, KindType):
        return value.value
    return value
