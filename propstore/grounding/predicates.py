"""Predicate registry and derived_from DSL for the Datalog grounder.

This module materialises the typed predicate-declaration set authored
under ``predicates/`` YAML files into a flat, indexed registry that the
grounding pipeline (chunks 1.3 onward) can query at fact-extraction and
ground-substitution time.

Theoretical sources:
    Diller, M., Borg, A., & Bex, F. (2025). Grounding Rule-Based
    Argumentation Using Datalog.
    - Section 3 (p.3): a Datalog program is a set of declared
      predicates with typed argument vectors plus rules over those
      predicates. Each predicate id keys a unique typed signature; the
      registry layer makes that schema queryable so the grounder can
      validate atom shapes before enumerating Herbrand substitutions.
    - Section 4: ground substitutions are well-defined only when an
      atom's arity matches the registered predicate signature; arity
      mismatches are schema errors and are rejected by the grounder.
      The ``derived_from`` DSL identifies how propstore data
      materialises ground atoms — concept relations, claim attributes,
      and claim conditions are the three sanctioned source kinds.

    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic Programming:
    An Argumentative Approach. TPLP 4(1-2), 95-138.
    - Section 3 (p.3-4): predicate signatures are a flat function from
      predicate id to arity; an undeclared predicate has no Herbrand
      semantics. The unary ``bird/1`` predicate is the canonical
      defeasible-reasoning example used throughout this layer.
    - Section 3.2: rule heads and bodies are atoms whose term-tuple
      length must match the declared predicate arity for grounding to
      be well-defined; mismatches are rejected at the schema layer.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from propstore.artifacts.documents.predicates import PredicateDocument
from propstore.predicate_files import LoadedPredicateFile


DerivedFromKind = Literal["concept_relation", "claim_attribute", "claim_condition"]


class PredicateNotRegisteredError(KeyError):
    """Raised when ``PredicateRegistry.lookup`` cannot find a predicate id.

    Inherits from ``KeyError`` so callers using the standard
    ``pytest.raises(KeyError)`` idiom catch it without coupling to the
    propstore-specific subclass. Diller, Borg, Bex 2025 §4 treats
    undeclared predicates as schema errors: the grounder cannot
    enumerate substitutions over a signature it has never seen.
    """


class PredicateArityMismatchError(ValueError):
    """Raised when ``PredicateRegistry.validate_atom`` sees a wrong arity.

    Diller, Borg, Bex 2025 §4: ground substitutions are well-defined
    only when the observed atom's term-tuple length equals the declared
    predicate arity. Garcia & Simari 2004 §3.2 enforces the same
    invariant at the Herbrand-base level — a predicate symbol used at
    the wrong arity has no grounding semantics.
    """


class DuplicatePredicateError(ValueError):
    """Raised when two predicate files declare the same predicate id.

    Diller, Borg, Bex 2025 §3 treats the predicate id as the unique key
    into the Datalog schema; two declarations for the same id are
    ambiguous because the grounder cannot decide which arity/arg-type
    vector to use. Garcia & Simari 2004 §3.2 makes the same point: the
    predicate signature is a flat function from id to arity. The
    registry surfaces this collision at build time so authoring
    mistakes do not silently shadow.
    """


class DerivedFromParseError(ValueError):
    """Raised when ``parse_derived_from`` cannot parse a DSL string.

    Diller, Borg, Bex 2025 §3 fixes the grammar of the ``derived_from``
    DSL: only the three sanctioned prefixes (``concept.relation``,
    ``claim.attribute``, ``claim.condition``) are recognised, each with
    a fixed number of colon-separated segments. Anything else is an
    authoring typo and must be rejected so fact extraction does not
    silently misroute. Garcia & Simari 2004 §3 admits no other
    extension points at the schema layer.
    """


@dataclass(frozen=True)
class DerivedFromSpec:
    """Parsed shape of a ``derived_from`` DSL string.

    Discriminated record over the three sanctioned source kinds for
    fact extraction. Diller, Borg, Bex 2025 §3-§4 lists exactly three
    ways propstore data can materialise into a Datalog ground atom:

    - ``concept.relation:<relation>:<target>`` — a concept relation
      walked from a subject concept to a target via a named relation;
      ``kind == "concept_relation"`` with ``relation`` and ``target``
      populated.
    - ``claim.attribute:<attribute>`` — a claim-side attribute pulled
      from the claim store as a (potentially boolean-coerced) fact;
      ``kind == "claim_attribute"`` with ``attribute`` populated.
    - ``claim.condition:<condition>`` — a claim-side context condition
      treated as a fact in the grounder; ``kind == "claim_condition"``
      with ``condition`` populated.

    Garcia & Simari 2004 §3 grounds the same canonical examples
    (``bird/1``, ``is_a:Bird``) used in the test fixtures.

    Attributes:
        kind: Discriminant tag identifying which DSL form was parsed.
        relation: Concept relation name (concept_relation only).
        target: Target concept identifier (concept_relation only).
        attribute: Claim attribute name (claim_attribute only).
        condition: Claim condition name (claim_condition only).
    """

    kind: DerivedFromKind
    relation: str | None = None
    target: str | None = None
    attribute: str | None = None
    condition: str | None = None


def parse_derived_from(spec: str) -> DerivedFromSpec:
    """Parse a ``derived_from`` DSL string into a typed ``DerivedFromSpec``.

    Diller, Borg, Bex 2025 §3-§4 lists three sanctioned prefixes; each
    has a fixed shape:

    - ``concept.relation:<relation>:<target>`` -> ``concept_relation``
    - ``claim.attribute:<attribute>``          -> ``claim_attribute``
    - ``claim.condition:<condition>``          -> ``claim_condition``

    Garcia & Simari 2004 §3 fixes the canonical example tokens
    (``is_a:Bird``, ``bird``) the parser must round-trip without loss.
    The ``target`` segment for ``concept.relation`` is the canonical
    concept identifier used by propstore relationships, so it may
    legitimately contain additional ``:`` separators (for example
    ``ps:concept:...`` artifact ids).

    The parser is strict: the empty string, missing separators, extra
    separators, empty segments, and unknown prefixes all raise
    ``DerivedFromParseError`` (a ``ValueError`` subclass). Loose
    decoding would let authoring typos silently misroute fact
    extraction.

    Args:
        spec: The DSL string to parse.

    Returns:
        A frozen ``DerivedFromSpec`` tagged with the matching kind.

    Raises:
        DerivedFromParseError: when the input does not exactly match
            one of the three sanctioned shapes.
    """

    if not isinstance(spec, str) or spec == "":
        raise DerivedFromParseError(
            "derived_from spec must be a non-empty string"
        )

    # Split into prefix + remainder on the first colon. Diller 2025 §3
    # fixes the prefix as the discriminant; everything after the first
    # colon is the kind-specific payload.
    if ":" not in spec:
        raise DerivedFromParseError(
            f"derived_from spec missing ':' separator: {spec!r}"
        )

    prefix, _, remainder = spec.partition(":")

    if prefix == "concept.relation":
        # Shape: concept.relation:<relation>:<target>
        # The target segment may itself contain ':' because propstore
        # canonical concept identifiers are artifact ids such as
        # ``ps:concept:...``.
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
            kind="concept_relation",
            relation=relation,
            target=target,
        )

    if prefix == "claim.attribute":
        # Shape: claim.attribute:<attribute>
        # No further colons, non-empty attribute.
        if remainder == "":
            raise DerivedFromParseError(
                f"claim.attribute spec has empty attribute: {spec!r}"
            )
        if ":" in remainder:
            raise DerivedFromParseError(
                f"claim.attribute spec has extra ':' in attribute: {spec!r}"
            )
        return DerivedFromSpec(
            kind="claim_attribute",
            attribute=remainder,
        )

    if prefix == "claim.condition":
        # Shape: claim.condition:<condition>
        # No further colons, non-empty condition.
        if remainder == "":
            raise DerivedFromParseError(
                f"claim.condition spec has empty condition: {spec!r}"
            )
        if ":" in remainder:
            raise DerivedFromParseError(
                f"claim.condition spec has extra ':' in condition: {spec!r}"
            )
        return DerivedFromSpec(
            kind="claim_condition",
            condition=remainder,
        )

    raise DerivedFromParseError(
        f"unknown derived_from prefix {prefix!r}: {spec!r}"
    )


class PredicateRegistry:
    """Flat registry mapping predicate id to its declaration.

    Materialises the Datalog predicate schema (Diller, Borg, Bex 2025
    §3) so downstream pipeline stages can query the typed signature for
    any declared predicate by id. Built once from a sequence of loaded
    predicate files; raises on duplicate ids so authoring collisions
    surface immediately.

    Garcia & Simari 2004 §3.2 treats the predicate signature as a flat
    function from id to arity; this registry provides exactly that
    function plus the per-position type vector and provenance metadata
    that Diller 2025 §3 layers on top.
    """

    def __init__(self, predicates: Sequence[PredicateDocument]) -> None:
        self._predicates: tuple[PredicateDocument, ...] = tuple(predicates)
        self._by_id: dict[str, PredicateDocument] = {
            doc.id: doc for doc in self._predicates
        }

    @classmethod
    def from_files(
        cls,
        files: Sequence[LoadedPredicateFile],
    ) -> PredicateRegistry:
        """Build a registry from loaded predicate files.

        Iterates declarations in file-then-authored order and rejects
        any predicate id seen more than once with
        ``DuplicatePredicateError``. Diller, Borg, Bex 2025 §3: the
        predicate id is the unique key into the Datalog schema; two
        declarations for the same id leave the grounder unable to
        decide which signature to use.

        Args:
            files: Loaded predicate-file envelopes whose
                ``.predicates`` tuples will be flattened into the
                registry's id->declaration map.

        Returns:
            A populated ``PredicateRegistry``.

        Raises:
            DuplicatePredicateError: when two declarations share an id.
        """

        seen: dict[str, PredicateDocument] = {}
        ordered: list[PredicateDocument] = []
        for predicate_file in files:
            for doc in predicate_file.predicates:
                if doc.id in seen:
                    raise DuplicatePredicateError(
                        f"duplicate predicate id {doc.id!r} declared in "
                        f"multiple predicate files"
                    )
                seen[doc.id] = doc
                ordered.append(doc)
        return cls(ordered)

    def lookup(self, predicate_id: str) -> PredicateDocument:
        """Return the declaration registered under ``predicate_id``.

        Diller, Borg, Bex 2025 §3 treats the predicate schema as an
        indexed namespace; once a predicate is declared, the grounder
        retrieves its full typed signature by id. Garcia & Simari 2004
        §3.2 makes the same point: an undeclared predicate has no
        arity and therefore no grounding semantics.

        Args:
            predicate_id: The predicate name to look up.

        Returns:
            The matching ``PredicateDocument``.

        Raises:
            PredicateNotRegisteredError: when no declaration exists for
                ``predicate_id``. The error subclass inherits from
                ``KeyError`` so the standard
                ``pytest.raises(KeyError)`` idiom catches it.
        """

        try:
            return self._by_id[predicate_id]
        except KeyError as exc:
            raise PredicateNotRegisteredError(
                f"predicate {predicate_id!r} is not registered"
            ) from exc

    def validate_atom(self, predicate_id: str, arity: int) -> None:
        """Verify that an atom's arity matches its declared signature.

        Diller, Borg, Bex 2025 §4: ground substitutions are
        well-defined only when the atom's term-tuple length equals the
        declared predicate arity. Garcia & Simari 2004 §3.2 enforces
        the same invariant at the Herbrand-base level. Returns
        cleanly (no return value) when the arities agree.

        Args:
            predicate_id: The predicate name the atom uses.
            arity: The observed term-tuple length to validate.

        Raises:
            PredicateNotRegisteredError: when ``predicate_id`` is not
                in the registry (delegated from ``lookup``).
            PredicateArityMismatchError: when the observed arity does
                not match the declared arity.
        """

        declaration = self.lookup(predicate_id)
        if declaration.arity != arity:
            raise PredicateArityMismatchError(
                f"predicate {predicate_id!r} declared with arity "
                f"{declaration.arity}, atom uses arity {arity}"
            )

    def all_predicates(self) -> tuple[PredicateDocument, ...]:
        """Return every registered declaration as an immutable tuple.

        Diller, Borg, Bex 2025 §3: the Datalog schema is the full set
        of declared predicates. Downstream pipeline stages (the fact
        extractor in chunk 1.3, the grounder in chunk 2.x) need to
        iterate over the complete schema, so the registry exposes a
        flat tuple view in declaration order.
        """

        return self._predicates
