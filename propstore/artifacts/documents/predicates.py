"""Typed document models for DeLP/Datalog predicate declaration files.

This module hosts the authored-file schema for typed predicate
declarations consumed by the grounding pipeline. Each predicate names a
relation symbol, fixes its arity, and tags every argument position with
a sort/concept that the grounder will use to enumerate well-typed
substitutions.

Theoretical sources:
    Diller, M., Borg, A., & Bex, F. (2025). Grounding Rule-Based
    Argumentation Using Datalog.
    - Section 3 (p.3): a Datalog predicate has the shape
      ``p(t_1,...,t_n)``; the predicate symbol carries a fixed arity
      ``n`` and a typed argument vector. The Datalog schema is the set
      of declared predicates, indexed by id.
    - Section 4: ground substitutions are well-defined only when an
      atom's term-tuple length matches the declared arity. The grounder
      validates atom shapes against this declaration set before
      enumerating Herbrand substitutions.

    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic Programming:
    An Argumentative Approach. TPLP 4(1-2), 95-138.
    - Section 3 (p.3-4): predicate symbols have a fixed arity; ground
      literals are atoms ``p(c_1,...,c_n)`` whose term-tuple length
      matches the predicate's arity. The unary ``bird/1`` predicate is
      the canonical defeasible-reasoning toy example.
    - Section 3.2: predicate signatures are a flat function from
      predicate id to arity; declared arity is what the Herbrand base
      ranges variables over.

DocumentStruct conventions mirrored from
``propstore.artifacts.documents.rules``
and ``propstore/claim_documents.py``: ``msgspec.Struct`` with
``kw_only=True, forbid_unknown_fields=True``, list-valued fields use
``tuple[T, ...] = ()``, and round-tripping through ``msgspec.yaml`` is
idempotent under strict decoding.
"""

from __future__ import annotations

from propstore.artifacts.schema import DocumentStruct


class PredicateDocument(DocumentStruct):
    """Typed predicate declaration.

    Declares a predicate name, its arity, and the concept-typed sorts of
    its argument positions. Rules reference predicates by name and the
    registry enforces arity matching at grounding time.

    Diller, Borg, Bex 2025, §3 (p.3): a Datalog predicate is
    ``p(t_1,...,t_n)`` where the ``t_i`` are terms. The arity ``n`` and
    the per-position argument types are fixed at declaration time and
    indexed by predicate id into the Datalog schema. Section 4 ties the
    declared arity to the well-formedness of ground substitutions.

    Garcia & Simari 2004, §3 (p.3-4): predicate symbols have a fixed
    arity; ground literals substitute variables with constants of
    matching sort. The 0-ary case is admitted as propositional facts
    (``raining``), and the unary ``bird/1`` predicate is the canonical
    defeasible-reasoning example.

    Attributes:
        id: Predicate name (e.g. ``"bird"``).
        arity: Number of argument positions (``>= 0``).
        arg_types: Tuple of length ``arity`` declaring each position's
            sort. The strategy invariant ``len(arg_types) == arity`` is
            enforced by the authoring layer, not by the schema itself.
        derived_from: Optional ``derived_from`` DSL string describing how
            propstore data materialises this predicate's ground atoms.
            Recognised forms live in ``propstore.grounding.predicates``.
        description: Human-readable explanation of the predicate.
    """

    id: str
    arity: int
    arg_types: tuple[str, ...] = ()
    derived_from: str | None = None
    description: str | None = None


class PredicatesFileDocument(DocumentStruct):
    """Top-level envelope for an authored predicates YAML file.

    Mirrors the ``RulesFileDocument`` envelope shape from
    ``propstore.artifacts.documents.rules``: a flat ordered tuple of
    predicate declarations. Order is preserved across YAML round-trip
    because Diller, Borg, Bex 2025 §3 builds the Datalog schema in
    declaration order — authored order is the only stable way to anchor
    authoring intent across re-encoding.

    Attributes:
        predicates: Ordered tuple of predicate declarations.
    """

    predicates: tuple[PredicateDocument, ...] = ()
