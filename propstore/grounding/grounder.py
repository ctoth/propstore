"""Phase-1 grounder — the thin wrapper that runs gunray and bundles output.

Chunk 1.5b (green) of the Phase-1 grounder workstream. ``ground`` is
the single public entry point: it translates propstore rule/fact
documents into a ``gunray.schema.DefeasibleTheory`` via
``propstore.grounding.translator.translate_to_theory``, runs
``gunray.adapter.GunrayEvaluator`` over the theory, and packages the
resulting sections into a frozen ``GroundedRulesBundle``.

Theoretical anchors:

    Diller, M., Borg, A., & Bex, F. (2025). Grounding Rule-Based
    Argumentation Using Datalog.
    - Section 3 (Definition 9): the ground substitution set is a
      deterministic function of the program and its fact base. The
      grounder delegates the actual substitution enumeration to
      gunray; propstore owns the envelope.
    - Section 3 (Definition 7, p.3): the fact base is a finite set of
      ground atoms — trivially in the ground model. The ``definitely``
      section therefore echoes the input facts when there are no
      strict rules to derive additional atoms.
    - Section 4: a ground model is the closure of the fact base under
      the rules; every ground atom has a well-defined status. Gunray's
      evaluator returns that model via ``DefeasibleModel.sections``.

    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic
    Programming: An Argumentative Approach.
    - Section 3 (p.3-4): the canonical DeLP example is
      ``bird(tweety) ∈ Facts`` with the defeasible rule
      ``flies(X) -< bird(X)``. The Phase-1 grounder reproduces this
      textbook derivation end-to-end.
    - Section 4 (p.25): the four-valued answer system
      ``{YES, NO, UNDECIDED, UNKNOWN}`` maps onto gunray's four
      section names
      (``definitely`` / ``defeasibly`` / ``not_defeasibly`` /
      ``undecided``). Gunray's evaluator drops empty sections from its
      raw output (see ``gunray.defeasible`` — the result is built via
      ``{name: facts_map for name, facts_map in sections.items() if
      facts_map}``); the grounder **re-normalises** the dict so every
      bundle exposes all four section keys, even when some are empty.
      That normalisation is the non-commitment anchor for this
      pipeline: the storage layer never silently collapses a verdict.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import cast

import gunray
from gunray.adapter import GunrayEvaluator
from gunray.schema import DefeasibleModel, DefeasibleSections, Policy

from propstore.aspic import GroundAtom, Scalar
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.grounding.predicates import PredicateRegistry
from propstore.grounding.translator import translate_to_theory
from propstore.rule_files import LoadedRuleFile

# Garcia & Simari 2004 §4 (p.25): the four-valued answer system
# ``{YES, NO, UNDECIDED, UNKNOWN}`` maps onto gunray's four named
# sections. This tuple fixes both the required key set and their
# iteration order, so the normalisation pass below is deterministic
# (Diller, Borg, Bex 2025 §3 Definition 9: the grounder output must
# be a pure function of the program and its fact base).
_FOUR_SECTIONS: tuple[str, ...] = (
    "definitely",
    "defeasibly",
    "not_defeasibly",
    "undecided",
)


def ground(
    rule_files: Sequence[LoadedRuleFile],
    facts: tuple[GroundAtom, ...],
    registry: PredicateRegistry,
    *,
    policy: Policy = Policy.BLOCKING,
    return_arguments: bool = False,
) -> GroundedRulesBundle:
    """Ground a propstore rule/fact bundle via gunray.

    Diller, Borg, Bex 2025 §3: the grounded model is a pair
    ``(program, fact_base) -> model``; this function is the
    propstore-side envelope that performs exactly that evaluation. The
    implementation is intentionally thin — all of the substitution
    enumeration lives in gunray. The grounder's own responsibilities
    are:

    1. Hand the rule files, facts and registry to
       ``translate_to_theory`` to build a
       ``gunray.schema.DefeasibleTheory`` (the translator stringifies
       atoms, groups facts by predicate id, and refuses Phase-2+
       constructs). Diller, Borg, Bex 2025 §3 Definition 7.
    2. Invoke ``GunrayEvaluator().evaluate`` with the requested
       ``Policy`` to obtain a ``DefeasibleModel``. Garcia & Simari 2004
       §4 (p.25): the four-valued answer system is computed here.
    3. Re-normalise the model's sections into an immutable
       four-section view. Gunray's evaluator drops empty sections from
       its output — the grounder restores them so every bundle exposes
       all four section keys, even when some are empty. Garcia &
       Simari 2004 §4 (p.25) non-commitment anchor: storage never
       silently collapses a verdict, so the render layer always sees
       the full shape.
    4. Package the normalised sections together with the original
       ``rule_files`` and ``facts`` into a frozen
       ``GroundedRulesBundle`` (Diller, Borg, Bex 2025 §3: the program
       and the ground model travel together through the pipeline).

    Args:
        rule_files: Sequence of ``LoadedRuleFile`` envelopes. Each
            carries an ordered tuple of ``RuleDocument`` values; rule
            order is preserved across the YAML round-trip because
            authored order can carry preference information downstream.
            May be empty — Diller, Borg, Bex 2025 §3: the empty program
            is a valid Datalog input.
        facts: Tuple of ``GroundAtom`` values as produced by
            ``propstore.grounding.facts.extract_facts``. Diller, Borg,
            Bex 2025 §3 Definition 7: ground atoms ``p(c_1,...,c_n)``
            drawn from the propstore concept graph.
        registry: ``PredicateRegistry`` providing predicate
            declarations. Threaded through to the translator for
            Phase-2+ validation hooks (Diller, Borg, Bex 2025 §4 arity
            discipline at the grounder boundary); Phase 1 does not
            itself validate against it.
        policy: Ambiguity-resolution policy threaded through to
            ``GunrayEvaluator.evaluate``. Garcia & Simari 2004 §4
            (p.25) discusses ambiguity regimes for the four-valued
            answer system. Defaults to ``Policy.BLOCKING`` to match
            gunray's own default; post-Block-2 (see gunray
            ``notes/policy_propagating_fate.md``) only ``BLOCKING`` is
            supported on the dialectical-tree path — argument
            preference is resolved via ``GeneralizedSpecificity``
            (Simari & Loui 1992 Lemma 2.4) regardless of the policy
            value. The keyword is still threaded through so callers
            can opt into closure-style policies (rational, lexicographic,
            relevant) once propstore surfaces them.
        return_arguments: When ``True``, populate
            ``bundle.arguments`` with the full ordered tuple of
            ``gunray.Argument`` objects produced by
            ``gunray.build_arguments(theory)``. Defaults to ``False``
            for backwards compatibility — existing callers pay no
            argument-enumeration cost. Block 3 of the gunray
            refactor exposes this typed view alongside the legacy
            section projection; callers that operate on arguments
            (dialectical renderer, claim graph) opt in via this
            keyword. Garcia & Simari 2004 §3 Def 3.6 (argument as
            minimal consistent defeasible derivation) and Diller,
            Borg, Bex 2025 §4 (arguments as the atomic unit of the
            dialectical-tree procedure).

    Returns:
        A ``GroundedRulesBundle`` whose ``sections`` mapping always
        has all four gunray section keys
        (``definitely`` / ``defeasibly`` / ``not_defeasibly`` /
        ``undecided``), whose ``source_rules`` is ``tuple(rule_files)``,
        and whose ``source_facts`` is ``facts``. When
        ``return_arguments=True``, ``arguments`` carries the
        deterministically-sorted tuple of ``gunray.Argument``
        objects; otherwise it is the empty tuple.
    """

    # Step 1: translate propstore documents into the gunray schema.
    # Diller, Borg, Bex 2025 §3 Definition 7 shape.
    theory = translate_to_theory(rule_files, facts, registry)

    # Step 2: run gunray. Garcia & Simari 2004 §4 (p.25) computes the
    # four-valued answer system here; the ``policy`` keyword selects
    # the ambiguity-resolution regime. ``GunrayEvaluator.evaluate`` is
    # typed as returning ``object`` because it dispatches over both
    # ``Program`` and ``DefeasibleTheory`` — but we pass a
    # ``DefeasibleTheory`` so the concrete return is a
    # ``DefeasibleModel``.
    evaluator = GunrayEvaluator()
    raw_model = cast(DefeasibleModel, evaluator.evaluate(theory, policy))

    # Step 3: re-normalise sections. Garcia & Simari 2004 §4 (p.25)
    # non-commitment anchor: every bundle must expose all four section
    # keys even when gunray dropped some for being empty. Diller, Borg,
    # Bex 2025 §3 Definition 9: the output must be a deterministic
    # function of the inputs, so we build the dict in the fixed
    # ``_FOUR_SECTIONS`` order.
    normalized_sections = _normalise_sections(raw_model.sections)

    # Step 3b (opt-in): enumerate the argument view. Garcia & Simari
    # 2004 §3 Def 3.6 / Simari & Loui 1992 Def 2.2 — an argument is a
    # minimal consistent defeasible derivation. ``gunray.build_arguments``
    # returns an unordered ``frozenset[Argument]``; we sort it by a
    # deterministic key (rule id tuple, conclusion predicate,
    # conclusion argument tuple) so repeated invocations with the same
    # inputs yield byte-identical bundles — the Diller, Borg, Bex 2025
    # §3 Definition 9 determinism contract at the argument-tuple
    # granularity.
    sorted_arguments: tuple[gunray.Argument, ...] = ()
    if return_arguments:
        argument_set = gunray.build_arguments(theory)
        sorted_arguments = tuple(
            sorted(
                argument_set,
                key=_argument_sort_key,
            )
        )

    # Step 4: package into the immutable bundle. Diller, Borg, Bex
    # 2025 §3: the rule base and fact base travel with the model so
    # downstream consumers retain full provenance.
    return GroundedRulesBundle(
        source_rules=tuple(rule_files),
        source_facts=facts,
        sections=normalized_sections,
        arguments=sorted_arguments,
    )


def _argument_sort_key(
    argument: "gunray.Argument",
) -> tuple[tuple[str, ...], str, tuple[str, ...]]:
    """Deterministic sort key for ``gunray.Argument`` objects.

    The key is a tuple of primitives so ``sorted`` is stable across
    Python implementations and across gunray versions: the rule-id
    tuple (sorted so set iteration order is irrelevant), the
    conclusion predicate string, and the conclusion argument tuple
    (rendered to strings because gunray's ``GroundAtom.arguments``
    stores arbitrary scalar types).

    Diller, Borg, Bex 2025 §3 Definition 9: the grounder must be a
    deterministic function of its inputs. ``build_arguments`` returns
    an unordered frozenset; this key projects it onto a total order
    so the returned tuple is byte-identical for byte-identical
    inputs.
    """

    rule_ids = tuple(sorted(rule.rule_id for rule in argument.rules))
    conclusion = argument.conclusion
    conclusion_args = tuple(str(arg) for arg in conclusion.arguments)
    return rule_ids, conclusion.predicate, conclusion_args


def _normalise_sections(
    raw_sections: DefeasibleSections,
) -> Mapping[str, Mapping[str, frozenset[tuple[Scalar, ...]]]]:
    """Convert gunray's ``DefeasibleSections`` into an immutable view.

    Three invariants enforced here, pinned by
    ``tests/test_grounding_grounder.py``:

    1. **All four section keys are always present.** Gunray drops
       empty sections in its raw output (``gunray.defeasible`` builds
       the result via ``{name: facts_map for ... if facts_map}``); we
       restore any missing keys with empty inner maps. Garcia & Simari
       2004 §4 (p.25) four-valued answer system is exhaustive.
    2. **Inner sets are frozen.** Gunray emits mutable
       ``set[tuple[Scalar, ...]]`` per predicate; propstore owns its
       own immutable view, so we convert each one to ``frozenset``.
       Diller, Borg, Bex 2025 §3: the ground model is a pure function
       of the program, so freezing is safe.
    3. **Outer and inner mappings reject assignment.** Wrapped via
       ``types.MappingProxyType`` so attempts to do
       ``bundle.sections["definitely"] = {}`` raise ``TypeError``.

    The iteration order over ``_FOUR_SECTIONS`` is fixed so two calls
    with the same input produce structurally identical dicts
    (determinism property — Diller, Borg, Bex 2025 §3 Definition 9).

    Args:
        raw_sections: The ``sections`` field of a
            ``gunray.schema.DefeasibleModel``.

    Returns:
        An immutable mapping with all four gunray section keys present
        and every inner set converted to a ``frozenset``.
    """

    normalized: dict[str, Mapping[str, frozenset[tuple[Scalar, ...]]]] = {}
    for name in _FOUR_SECTIONS:
        inner_raw = raw_sections.get(name, {})
        inner_frozen: dict[str, frozenset[tuple[Scalar, ...]]] = {}
        for predicate_id, rows in inner_raw.items():
            # Each row is a ``tuple[Scalar, ...]`` — freeze the set.
            # Garcia & Simari 2004 §3.1: ground instances are the
            # substituted argument tuples.
            inner_frozen[predicate_id] = frozenset(rows)
        # Wrap the inner dict so ``bundle.sections["definitely"]
        # ["bird"] = ...`` also raises. Not strictly required by the
        # tests (they only probe the outer mapping) but consistent
        # with the non-commitment discipline.
        normalized[name] = MappingProxyType(inner_frozen)

    return MappingProxyType(normalized)
