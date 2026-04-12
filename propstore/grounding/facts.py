"""Phase-1 fact extractor for the propstore -> Datalog grounding pipeline.

The fact extractor walks the propstore concept graph and materialises
the Datalog fact base consumed by later grounding stages. It is the
sole bridge between propstore source-of-truth concept relationships
and the ground-atom set that the gunray translator and the sidecar
populate stage will read.

Theoretical sources:
    Diller, M., Borg, A., & Bex, F. (2025). Grounding Rule-Based
    Argumentation Using Datalog.
    - Section 3 (Definition 7, p.3): a Datalog program's fact base is a
      finite set of ground atoms ``p(c_1,...,c_n)`` whose terms are
      constants drawn from the domain. The extractor produces exactly
      this set from the propstore concept graph.
    - Section 3 (Definition 9): ground substitutions are a function of
      the program and its fact base. The extractor must therefore be a
      pure, total, deterministic function of its inputs so the
      substitution set downstream is stable across runs.
    - Section 4: every emitted ground atom must reference a declared
      predicate and respect its declared arity. The extractor cannot
      invent predicate symbols and cannot emit atoms whose arity
      disagrees with the registry. Section 4 also fixes the three
      sanctioned ``derived_from`` source kinds; Phase 1 only
      materialises the ``concept_relation`` form, leaving
      ``claim_attribute`` and ``claim_condition`` for later phases.

    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic Programming:
    An Argumentative Approach. TPLP 4(1-2), 95-138.
    - Section 3 (p.3-4): the unary ``bird/1`` predicate is the
      canonical defeasible-reasoning toy example; the ground literal
      ``bird(tweety)`` is produced from a fact-base entry asserting
      that the constant ``tweety`` participates in the ``Bird``
      classification. The Phase-1 extractor reproduces exactly this
      derivation: a concept whose ``canonical_name`` is ``tweety`` with
      an outgoing ``is_a`` edge to ``Bird`` produces ``bird(tweety)``.
    - Section 3.1: the ground instances of a program are obtained by
      replacing each variable in a rule head/body with a constant
      drawn from the Herbrand base. Here the Herbrand base for a
      ``concept.relation:<rel>:<target>`` derivation is the set of
      concept canonical names that have a matching outgoing edge.
    - Section 3.2: predicate signatures are a flat function from
      predicate id to arity; rule heads and bodies have term-tuple
      lengths matching the declared arity for grounding to be
      well-defined. Phase 1 only materialises unary atoms because the
      ``concept.relation`` derivation form fixes a single source-side
      argument.
"""

from __future__ import annotations

from collections.abc import Sequence

from propstore.aspic import GroundAtom
from propstore.core.concepts import LoadedConcept
from propstore.grounding.predicates import (
    PredicateRegistry,
    parse_derived_from,
)


def extract_facts(
    concepts: Sequence[LoadedConcept],
    registry: PredicateRegistry,
) -> tuple[GroundAtom, ...]:
    """Materialise the Datalog fact base from the propstore concept graph.

    For every predicate in ``registry`` whose ``derived_from`` DSL
    parses as ``concept.relation:<relation>:<target>``, walk every
    ``LoadedConcept`` in ``concepts``. For each outgoing
    ``ConceptRelationship`` whose ``relationship_type`` matches
    ``relation`` and whose ``target`` matches ``target``, emit one
    ground atom of the form ``predicate(canonical_name)`` where
    ``canonical_name`` is the source concept's
    ``ConceptRecord.canonical_name`` (Garcia & Simari 2004 §3: the
    user-facing token like ``tweety`` in ``bird(tweety)``).

    Phase 1 supports ONLY the ``concept_relation`` source kind. The
    other two sanctioned forms (``claim.attribute:<attribute>`` and
    ``claim.condition:<condition>``) parse successfully via
    ``parse_derived_from`` but contribute no facts here -- Diller, Borg,
    Bex 2025 §4 lists them as legitimate source kinds, but
    materialising them belongs to a later chunk. Predicates with
    ``derived_from is None`` likewise contribute nothing because they
    have no bridge from propstore data.

    The result is a deterministic, duplicate-free tuple. Diller et al.
    2025 §3 (Definition 7) treats the fact base as a *set*, so the
    extractor deduplicates internally before sorting; Garcia & Simari
    2004 §3.1 makes the same point about ground instances. Sorting on
    the natural ``(predicate, arguments)`` key gives a stable order
    independent of dict iteration order or graph-walk order, which
    Diller et al. 2025 §3 Definition 9 requires for the substitution
    set to be a deterministic function of the program and the fact
    base.

    Note: ``ConceptRelationship.relationship_type`` is the parsed
    dataclass field name (the underlying YAML uses ``type``, but
    ``parse_concept_record`` renames it). The extractor reads
    ``rel.relationship_type`` and compares against ``spec.relation``.

    Args:
        concepts: Sequence of ``LoadedConcept`` envelopes as produced
            by ``propstore.core.concepts.load_concepts`` and consumed
            by the sidecar build pipeline.
        registry: ``PredicateRegistry`` providing predicate
            declarations and their ``derived_from`` DSL strings.

    Returns:
        A deterministic tuple of ``GroundAtom``, sorted on
        ``(predicate, arguments)``, with no duplicates.
    """

    # Collect into a set to enforce the Diller 2025 §3 Definition 7
    # requirement that the fact base is a set, not a multiset. The
    # same (concept, predicate) pair never produces more than one
    # atom, regardless of how the loops below are nested.
    collected: set[GroundAtom] = set()

    for predicate in registry.all_predicates():
        derived_from = predicate.derived_from
        if derived_from is None:
            # No bridge from propstore data: this predicate contributes
            # nothing to the fact base. Diller 2025 §3-§4: derived_from
            # is the only sanctioned source.
            continue

        spec = parse_derived_from(derived_from)
        if spec.kind != "concept_relation":
            # Phase 1 only materialises the concept_relation source
            # kind. claim_attribute and claim_condition parse cleanly
            # but their materialisation belongs to a later chunk; the
            # extractor must not raise on them (Diller 2025 §4 lists
            # all three as legitimate kinds).
            continue

        spec_relation = spec.relation
        spec_target = spec.target
        # parse_derived_from guarantees both are non-empty strings for
        # the concept_relation kind, but pyright sees them as
        # ``str | None``. Narrow defensively.
        if spec_relation is None or spec_target is None:
            continue

        for concept in concepts:
            record = concept.record
            for relationship in record.relationships:
                if relationship.relationship_type != spec_relation:
                    continue
                if str(relationship.target) != spec_target:
                    continue
                # Garcia & Simari 2004 §3: the ground term is the
                # source concept's canonical name (e.g. ``tweety``),
                # not the artifact id or any logical id. Phase 1
                # emits unary atoms because the concept_relation
                # derivation fixes a single source-side argument.
                collected.add(
                    GroundAtom(
                        predicate=predicate.id,
                        arguments=(record.canonical_name,),
                    )
                )

    # Sort on (predicate, arguments) for a deterministic order
    # independent of dict / set iteration order. Diller et al. 2025
    # §3 Definition 9 requires the ground substitution set to be a
    # deterministic function of its inputs; downstream consumers
    # (the gunray translator, the sidecar populate stage) rely on
    # this stability for reproducible builds.
    return tuple(
        sorted(collected, key=lambda atom: (atom.predicate, atom.arguments))
    )
