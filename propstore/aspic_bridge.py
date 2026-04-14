"""ASPIC+ translation layer from propstore data to the formal engine.

Implements translation rules T1-T7 from proposals/aspic-bridge-spec.md:
    T1: claims_to_literals — claims -> Literal map
    T2: justifications_to_rules — justifications -> (strict_rules, defeasible_rules)
    T2.5: grounded_rules_to_rules — GroundedRulesBundle -> (strict, defeasible, lits)
    T3: stances_to_contrariness — stances -> ContrarinessFn
    T4: claims_to_kb — claims -> KnowledgeBase
    T5: build_preference_config — claims -> PreferenceConfig
    T6: build_bridge_csaf — full bridge -> CSAF
    T7: csaf_to_projection — CSAF -> StructuredProjection

References:
    Modgil & Prakken 2018: Defs 1-22, the complete ASPIC+ framework.
    Garcia & Simari 2004: DeLP syntax, Herbrand grounding (§3).
    Diller, Borg, Bex 2025: Datalog fact base + ground instances (§3-§4).
    proposals/aspic-bridge-spec.md: translation rules and rationale.

This module owns propstore-to-ASPIC translation. Projection-level callers
should normally enter through `propstore.structured_projection`.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from collections.abc import Iterator, Sequence
from typing import Any

from gunray.disagreement import complement as gunray_complement
from gunray.types import GroundAtom as GunrayGroundAtom

from propstore.aspic import Scalar
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.artifacts.documents.rules import AtomDocument

from propstore.aspic import (
    GroundAtom,
    Literal,
    ContrarinessFn,
    Rule,
    KnowledgeBase,
    ArgumentationSystem,
    PreferenceConfig,
    CSAF,
    PremiseArg,
    Argument,
    Attack,
    build_arguments,
    build_arguments_for,
    compute_attacks,
    compute_defeats,
    conc,
    prem,
    sub,
    top_rule,
    transposition_closure,
)
from propstore.core.active_claims import ActiveClaim, ActiveClaimInput, coerce_active_claims
from propstore.core.graph_types import ActiveWorldGraph
from propstore.core.justifications import (
    CanonicalJustification,
    claim_justifications_from_active_graph,
)
from propstore.core.literal_keys import (
    ClaimLiteralKey,
    LiteralKey,
    claim_key,
    ground_key,
)
from propstore.core.relation_types import ATTACK_TYPES, SUPPORT_TYPES
from propstore.core.row_types import StanceRow, StanceRowInput, coerce_stance_row
from propstore.dung import ArgumentationFramework
from propstore.preference import metadata_strength_vector, claim_strength
from propstore.structured_projection import (
    StructuredArgument,
    StructuredProjection,
)
from propstore.core.labels import Label, SupportQuality
from propstore.core.environment import StanceStore
from propstore.world.types import SupportMetadata

_ATTACK_TYPES = ATTACK_TYPES
_SUPPORT_TYPES = SUPPORT_TYPES


def _claim_attr(claim: ActiveClaim, key: str) -> Any:
    return getattr(claim, key, claim.attributes.get(key))


def _coerce_bridge_stance_row(row: StanceRowInput) -> StanceRow:
    """Coerce a bridge stance row, accepting bridge-local `contradicts`.

    The authored stance vocabulary intentionally rejects ``contradicts`` and
    uses ``rebuts`` as the canonical attack label. The ASPIC bridge spec and
    tests still admit ``contradicts`` as a rebuttal synonym, so normalize it at
    the bridge boundary instead of widening the shared authored enum surface.
    """
    if isinstance(row, StanceRow):
        return row
    row_map = dict(row)
    if row_map.get("stance_type") == "contradicts":
        row_map["stance_type"] = "rebuts"
    return coerce_stance_row(row_map)


def _default_support_metadata(claim: ActiveClaim) -> tuple[Label | None, SupportQuality]:
    """Compute default (label, support_quality) for a claim.

    Moved from structured_projection.py during Phase 5 cleanup.
    """
    has_context = claim.context_id is not None
    has_conditions = bool(claim.conditions)
    if has_context and has_conditions:
        return None, SupportQuality.MIXED
    if has_context:
        return None, SupportQuality.CONTEXT_VISIBLE_ONLY
    if has_conditions:
        return None, SupportQuality.SEMANTIC_COMPATIBLE
    return Label.empty(), SupportQuality.EXACT


# ── T1: claims -> literals ────────────────────────────────────────


def claims_to_literals(active_claims: Sequence[ActiveClaimInput]) -> dict[LiteralKey, Literal]:
    """Map each claim to a positive Literal.

    T1 (proposals/aspic-bridge-spec.md): Each claim becomes
    Literal(atom=claim_id, negated=False). The atom is the claim ID,
    not the concept ID — two claims about the same concept are
    different literals.

    Modgil & Prakken 2018, Def 1 (p.8): L is a logical language.

    Args:
        active_claims: List of claim dicts with at least an "id" key.

    Returns:
        Dict mapping ``ClaimLiteralKey`` -> Literal.
    """
    normalized_claims = coerce_active_claims(active_claims)
    return {
        claim_key(str(claim.claim_id)): Literal(
            atom=GroundAtom(str(claim.claim_id)),
            negated=False,
        )
        for claim in normalized_claims
    }


# ── T2: justifications -> rules ──────────────────────────────────


def justifications_to_rules(
    justifications: list[CanonicalJustification],
    literals: dict[LiteralKey, Literal],
) -> tuple[frozenset[Rule], frozenset[Rule]]:
    """Translate justifications to ASPIC+ strict and defeasible rules.

    T2 (proposals/aspic-bridge-spec.md):
    - reported_claim justifications are premises, not rules — skipped.
    - rule_strength="strict" -> Rule(kind="strict", name=None)
    - rule_strength="defeasible" -> Rule(kind="defeasible", name=justification_id)

    Modgil & Prakken 2018, Def 2 (p.8): strict rules have no name;
    Def 8c (p.11): undercutting targets n(r) for defeasible rules only.

    Args:
        justifications: List of CanonicalJustification objects.
        literals: Claim-ID-to-Literal mapping from T1.

    Returns:
        (strict_rules, defeasible_rules) as frozensets of Rule.
    """
    strict: list[Rule] = []
    defeasible: list[Rule] = []

    for j in justifications:
        if j.rule_kind == "reported_claim":
            continue
        if not j.premise_claim_ids:
            raise ValueError(
                f"empty-premise justification {j.justification_id!r} must be rejected or represented explicitly"
            )
        # Skip if any premise or conclusion not in literals
        conclusion_key = claim_key(j.conclusion_claim_id)
        premise_keys = tuple(claim_key(pid) for pid in j.premise_claim_ids)
        if conclusion_key not in literals:
            continue
        if any(pid not in literals for pid in premise_keys):
            continue

        antecedents = tuple(literals[pid] for pid in premise_keys)
        consequent = literals[conclusion_key]
        strength = j.rule_strength

        if strength == "strict":
            strict.append(Rule(
                antecedents=antecedents,
                consequent=consequent,
                kind="strict",
                name=None,
            ))
        else:
            defeasible.append(Rule(
                antecedents=antecedents,
                consequent=consequent,
                kind="defeasible",
                name=j.justification_id,
            ))

    return frozenset(strict), frozenset(defeasible)


# ── T2.5: grounded rules -> rules ────────────────────────────────

_GroundFactKey = tuple[str, bool]


def _decode_grounded_predicate(predicate_id: str) -> _GroundFactKey:
    """Decode a gunray section predicate key into ``(positive_predicate, negated)``.

    Gunray serializes strong negation via a ``~`` prefix on the
    predicate token; see ``gunray.disagreement.complement`` which
    owns that encoding. The ASPIC bridge models polarity as a typed
    bool on the ``Literal`` object instead, so section rows and
    grounded axioms must be projected from gunray's predicate-string
    convention onto propstore's typed convention before they
    participate in grounding or KB injection.

    This helper routes the projection through a ``GroundAtom`` ->
    ``complement`` round-trip so the ``~``-handling lives inside
    gunray's own typed surface rather than as a raw string hack in
    propstore. The round-trip is:

    1. Build a gunray ``GroundAtom`` from the section key (arity
       zero is fine — we only care about the predicate token).
    2. Apply ``gunray.disagreement.complement`` to toggle the
       polarity; the result's predicate is the positive form when
       the input was negative and vice versa.
    3. Detect polarity by comparing string lengths: a shorter
       complement means the original carried the ``~`` prefix.

    Garcia & Simari 2004 §3 (strong negation as a primitive relation
    on literals) and Diller, Borg, Bex 2025 §3 Def 7 (ground atoms
    keyed by predicate id) are the anchors.
    """

    probe = GunrayGroundAtom(predicate=predicate_id, arguments=())
    toggled = gunray_complement(probe)
    negated = len(toggled.predicate) < len(probe.predicate)
    positive = toggled.predicate if negated else probe.predicate
    return positive, negated


def _try_match(
    atom: AtomDocument,
    fact_args: tuple[Scalar, ...],
    sigma: dict[str, Scalar],
) -> dict[str, Scalar] | None:
    """Try to unify ``atom``'s terms against ``fact_args`` under ``sigma``.

    Garcia & Simari 2004 §3 (p.4): the Herbrand grounding step binds a
    schema atom to a ground atom by simultaneously matching every term
    position. Variables extend the substitution (with a consistency
    check if already bound); constants must equal the corresponding
    fact argument.

    Returns an extended substitution when the match succeeds, or
    ``None`` when it fails.
    """

    if len(atom.terms) != len(fact_args):
        return None
    extended = dict(sigma)
    for term, fact_arg in zip(atom.terms, fact_args):
        if term.kind == "var":
            name = term.name
            if name is None:
                return None
            if name in extended:
                if extended[name] != fact_arg:
                    return None
            else:
                extended[name] = fact_arg
        elif term.kind == "const":
            if term.value != fact_arg:
                return None
        else:
            return None
    return extended


def _enumerate_substitutions(
    body_atoms: tuple[AtomDocument, ...],
    facts: dict[_GroundFactKey, set[tuple[Scalar, ...]]],
) -> Iterator[dict[str, Scalar]]:
    """Yield every consistent substitution σ grounding all body atoms.

    Classic Datalog body-join (Diller, Borg, Bex 2025 §3 Def 7, p.3;
    Garcia & Simari 2004 §3.1, p.4). Starts from the empty substitution
    and, for each body atom in schema order, extends every partial
    substitution with every fact that matches under it. Empty body
    yields the single empty substitution — the nullary / propositional
    base case.
    """

    partial_subs: list[dict[str, Scalar]] = [{}]
    for atom in body_atoms:
        next_subs: list[dict[str, Scalar]] = []
        for sigma in partial_subs:
            for fact_args in facts.get((atom.predicate, atom.negated), set()):
                extended = _try_match(atom, fact_args, sigma)
                if extended is not None:
                    next_subs.append(extended)
        partial_subs = next_subs
        if not partial_subs:
            break
    return iter(partial_subs)


def _apply_substitution(
    atom: AtomDocument,
    sigma: dict[str, Scalar],
) -> GroundAtom:
    """Apply substitution σ to a schema atom to produce a ground atom.

    Garcia & Simari 2004 §3 (p.4): Herbrand grounding is pure term
    substitution — the predicate symbol is unchanged, variables in σ
    are replaced by their bound constants, and constants are carried
    through verbatim. Variables not in σ would indicate an unsafe rule
    (§3.3, p.8); the authoring CLI rejects those, so in a well-formed
    bundle every term resolves to a scalar.
    """

    args: list[Scalar] = []
    for term in atom.terms:
        if term.kind == "var":
            name = term.name
            if name is None or name not in sigma:
                raise ValueError(
                    f"Unsafe rule: variable {name!r} in atom "
                    f"{atom.predicate!r} not bound by substitution"
                )
            args.append(sigma[name])
        elif term.kind == "const":
            if term.value is None:
                raise ValueError(
                    f"Constant term in atom {atom.predicate!r} has no value"
                )
            args.append(term.value)
        else:
            raise ValueError(
                f"Unknown term kind {term.kind!r} in atom {atom.predicate!r}"
            )
    return GroundAtom(predicate=atom.predicate, arguments=tuple(args))


def _typed_scalar_key(value: Scalar) -> dict[str, Scalar | str]:
    if isinstance(value, bool):
        return {"type": "bool", "value": value}
    if isinstance(value, int):
        return {"type": "int", "value": value}
    if isinstance(value, float):
        return {"type": "float", "value": value}
    return {"type": "str", "value": value}


def _literal_for_atom(
    ground_atom: GroundAtom,
    negated: bool,
    literals: dict[LiteralKey, Literal],
) -> Literal:
    """Fetch or create the canonical Literal for a GroundAtom.

    Grounded literals use a typed internal key that includes predicate,
    typed arguments, and polarity. This keeps the grounded-literal
    namespace disjoint from T1 claim ids and prevents positive/negative
    occurrences of the same atom from aliasing.
    """

    key = ground_key(ground_atom, negated)
    if key in literals:
        return literals[key]
    lit = Literal(atom=ground_atom, negated=negated)
    literals[key] = lit
    return lit


def _canonical_substitution_key(sigma: dict[str, Scalar]) -> str:
    """Render σ as a stable structured string with variable names sorted.

    Modgil & Prakken 2018 Def 2 (p.8) requires a unique name n(r) per
    defeasible rule to drive undercutting (Def 8c, p.11). Every
    distinct substitution must therefore map to a distinct key. Use a
    JSON object over typed scalar encodings so delimiter characters in
    string constants cannot create collisions.
    """
    return json.dumps(
        {
            name: _typed_scalar_key(sigma[name])
            for name in sorted(sigma)
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def grounded_rules_to_rules(
    bundle: GroundedRulesBundle,
    literals: dict[LiteralKey, Literal],
) -> tuple[frozenset[Rule], frozenset[Rule], dict[LiteralKey, Literal]]:
    """T2.5: Enumerate ground rule instances and translate to ASPIC+ Rules.

    Walks every ``RuleDocument`` in ``bundle.source_rules``, joins the
    bundle's positive fact sections (``definitely`` and ``defeasibly``)
    into a single Datalog-style fact base, enumerates all consistent
    variable substitutions per rule via the natural body join, and
    emits one ASPIC+ ``Rule`` per substitution.

    Phase 1 scope:
    - Only ``kind == "defeasible"`` rules with empty ``negative_body``
      are translated; strict, defeater, and NAF-bearing rules raise
      ``NotImplementedError``. The non-commitment discipline requires a
      loud refusal rather than a silent partial translation.
    - The strict return frozenset is always empty in Phase 1.
    - The input ``literals`` dict is extended in place and returned as
      the third tuple element.

    Canonical ``Rule.name`` form: ``f"{rule_doc.id}#{sigma_key}"`` where
    ``sigma_key`` is a stable JSON encoding of the substitution with
    variable names sorted alphabetically. Empty substitutions
    (nullary rules) become ``f"{rule_doc.id}#"``. Distinct substitutions
    therefore map to distinct names, satisfying the n(r) uniqueness
    requirement that undercutting relies on.

    [cite Modgil & Prakken 2018 Def 2 p.8, Def 5 pp.9-10, Def 8c p.11;
     Garcia & Simari 2004 §3 pp.3-4 (Herbrand grounding), §6.1 pp.29-31
     (default negation deferral);
     Diller, Borg, Bex 2025 §3 Def 7 p.3, §4 (ground instances as a
     deterministic function of program + fact base)]

    Args:
        bundle: Immutable grounding-pipeline output with source rules
            and four-valued sections.
        literals: Existing typed literal dict — typically the T1 output keyed
            by ``ClaimLiteralKey``. Extended in
            place with entries for every ground atom that appears as an
            antecedent or consequent of an emitted rule.

    Returns:
        ``(strict_rules, defeasible_rules, extended_literals)`` where
        ``strict_rules`` is always empty in Phase 1 and
        ``extended_literals is literals`` (same dict, mutated).

    Raises:
        NotImplementedError: If any rule in the bundle has
            ``kind == "strict"``, ``kind == "defeater"``, or a
            non-empty ``negative_body``.
    """

    # Build the positive fact base: union of definitely and defeasibly
    # sections. Diller, Borg, Bex 2025 §3 Def 7 (p.3) treats the fact
    # base as a flat finite set of ground atoms; the per-section split
    # is gunray's four-valued answer record, not a rule-level concern.
    facts: dict[_GroundFactKey, set[tuple[Scalar, ...]]] = {}
    for section_name in ("definitely", "defeasibly"):
        section = bundle.sections.get(section_name, {})
        for predicate_id, rows in section.items():
            bucket = facts.setdefault(_decode_grounded_predicate(predicate_id), set())
            for row in rows:
                bucket.add(row)

    defeasible_rules: list[Rule] = []

    for rule_file in bundle.source_rules:
        for rule_doc in rule_file.document.rules:
            if rule_doc.kind == "strict":
                raise NotImplementedError(
                    "Strict rules deferred to Phase 4"
                )
            if rule_doc.kind == "defeater":
                raise NotImplementedError(
                    "Defeater rules deferred to Phase 4"
                )
            if rule_doc.negative_body:
                raise NotImplementedError(
                    "Negative body (NAF) deferred to Phase 4"
                )

            # rule_doc.kind == "defeasible" with empty negative_body.
            for sigma in _enumerate_substitutions(rule_doc.body, facts):
                antecedent_literals: list[Literal] = []
                for body_atom in rule_doc.body:
                    ground = _apply_substitution(body_atom, sigma)
                    antecedent_literals.append(
                        _literal_for_atom(ground, body_atom.negated, literals)
                    )

                head_ground = _apply_substitution(rule_doc.head, sigma)
                consequent = _literal_for_atom(
                    head_ground, rule_doc.head.negated, literals
                )

                sub_key = _canonical_substitution_key(sigma)
                rule_name = f"{rule_doc.id}#{sub_key}"

                defeasible_rules.append(
                    Rule(
                        antecedents=tuple(antecedent_literals),
                        consequent=consequent,
                        kind="defeasible",
                        name=rule_name,
                    )
                )

    return frozenset(), frozenset(defeasible_rules), literals


def _ground_facts_to_axioms(
    bundle: GroundedRulesBundle,
    literals: dict[LiteralKey, Literal],
    kb: KnowledgeBase,
) -> KnowledgeBase:
    """Inject bundle ``definitely`` facts into the ASPIC+ knowledge base.

    T2.5 (facts half): a Datalog fact base supplies the ground atoms
    that argument construction bottoms out on. Modgil & Prakken 2018
    Def 4 (p.9) places axioms in ``K_n`` (unattackable) and ordinary
    premises in ``K_p``. Garcia & Simari 2004 §3 (p.3-4): the DeLP
    canonical example treats the fact ``bird(tweety)`` as an
    unquestioned premise, which is the ``K_n`` mapping. Diller, Borg,
    Bex 2025 §3 Def 7 (p.3) similarly treats the Datalog fact base as
    the given set from which the ground model derives.

    The ``defeasibly`` section is *not* injected here — those rows are
    derived conclusions, and their supporting argument is the
    DefeasibleArg built from the grounded rule. Injecting them as K_p
    premises would create duplicate premise-level arguments that the
    tests correctly reject (``len(arguments_for) == 1`` for
    ``flies(tweety)`` in the canonical tweety scenario).

    Every injected literal is also registered in ``literals`` so that
    downstream language-building, contrariness lookup, and preference
    filtering see a consistent keyed view.

    Args:
        bundle: Immutable grounder output.
        literals: The T1/T2.5-extended literal map. Mutated in place
            with one new entry per ground fact whose key is not
            already present.
        kb: The T4 knowledge base, built from authored claims. The
            returned KB is a *new* KnowledgeBase whose axioms are the
            union of ``kb.axioms`` and the ground-fact axioms.

    Returns:
        A ``KnowledgeBase`` with ground-fact axioms added to K_n.
    """

    axioms: set[Literal] = set(kb.axioms)
    definitely = bundle.sections.get("definitely", {})
    for predicate_id, rows in definitely.items():
        predicate, negated = _decode_grounded_predicate(predicate_id)
        for row in rows:
            ground = GroundAtom(predicate=predicate, arguments=tuple(row))
            lit = _literal_for_atom(ground, negated, literals)
            axioms.add(lit)

    return KnowledgeBase(axioms=frozenset(axioms), premises=kb.premises)


# ── T3: stances -> contrariness ──────────────────────────────────


def stances_to_contrariness(
    stances: Sequence[StanceRowInput],
    literals: dict[LiteralKey, Literal],
    defeasible_rules: frozenset[Rule],
) -> ContrarinessFn:
    """Build a ContrarinessFn from attack stances.

    T3 (proposals/aspic-bridge-spec.md):
    - rebuts/contradicts -> contradictories (symmetric)
    - supersedes/undermines -> contraries (asymmetric)
    - undercuts -> contrary of Literal(rule_name) for targeted rules

    Modgil & Prakken 2018, Def 2 (p.8): contradictories are symmetric,
    contraries are directional.

    Args:
        stances: List of stance dicts with claim_id, target_claim_id, stance_type.
        literals: Claim-ID-to-Literal mapping from T1.
        defeasible_rules: Defeasible rules from T2.

    Returns:
        ContrarinessFn with contradictory and contrary pairs.
    """
    # Prakken 2010, Def. 5.1 (p. 141; local page image
    # ``papers/Prakken_2010_AbstractFrameworkArgumentationStructured/pngs/page-012.png``)
    # defines transposition over the system's ``-`` operator. The bridge must
    # therefore publish the base contradictory pairs for every claim / ground
    # literal, not only attack stances layered on top of them.
    contradictory_pairs: set[tuple[Literal, Literal]] = {
        (lit, lit.contrary) for lit in literals.values()
    }
    for rule in defeasible_rules:
        if rule.name is None:
            continue
        rule_lit = Literal(atom=GroundAtom(rule.name), negated=False)
        contradictory_pairs.add((rule_lit, rule_lit.contrary))
    contrary_pairs: set[tuple[Literal, Literal]] = set()

    for stance_input in stances:
        stance = _coerce_bridge_stance_row(stance_input)
        src_id = stance.claim_id
        tgt_id = stance.target_claim_id
        stype = stance.stance_type

        src_key = claim_key(src_id)
        tgt_key = claim_key(tgt_id)
        if src_key not in literals or tgt_key not in literals:
            continue

        src = literals[src_key]
        tgt = literals[tgt_key]

        # No self-contrariness (Def 2, p.8)
        if src == tgt:
            continue

        if stype in ("rebuts", "contradicts"):
            # Symmetric contradictories — add both directions
            contradictory_pairs.add((src, tgt))
            contradictory_pairs.add((tgt, src))
        elif stype in ("supersedes", "undermines"):
            # Asymmetric contraries — src is contrary of tgt
            contrary_pairs.add((src, tgt))
        elif stype == "undercuts":
            target_justification_id = stance.target_justification_id
            matching_rules = [
                rule
                for rule in defeasible_rules
                if rule.consequent == tgt and rule.name is not None
            ]
            if target_justification_id is not None:
                exact_matches = [
                    rule
                    for rule in matching_rules
                    if rule.name == target_justification_id
                ]
                if exact_matches:
                    matching_rules = exact_matches
                else:
                    matching_rules = [
                        rule
                        for rule in matching_rules
                        if rule.name is not None
                        and rule.name.partition("#")[0] == target_justification_id
                    ]
                if not matching_rules:
                    raise ValueError(
                        "undercut target_justification_id "
                        f"{target_justification_id!r} did not match a defeasible "
                        f"justification for target claim {tgt_id!r}"
                    )
            elif len(matching_rules) > 1:
                raise ValueError(
                    "undercut against target claim "
                    f"{tgt_id!r} is ambiguous across multiple defeasible "
                    "justifications; provide target_justification_id"
                )

            for rule in matching_rules:
                assert rule.name is not None
                rule_lit = Literal(atom=GroundAtom(rule.name), negated=False)
                if src != rule_lit:
                    contrary_pairs.add((src, rule_lit))

    return ContrarinessFn(
        contradictories=frozenset(contradictory_pairs),
        contraries=frozenset(contrary_pairs),
    )


# ── T4: claims -> knowledge base ─────────────────────────────────


def claims_to_kb(
    active_claims: Sequence[ActiveClaimInput],
    justifications: list[CanonicalJustification],
    literals: dict[LiteralKey, Literal],
) -> KnowledgeBase:
    """Build an ASPIC+ knowledge base from claims and justifications.

    T4 (proposals/aspic-bridge-spec.md):
    - Claims with reported_claim justification are premises.
    - premise_kind="necessary" -> K_n (axioms, unattackable)
    - premise_kind="ordinary" -> K_p (ordinary premises, attackable)

    Modgil & Prakken 2018, Def 4 (p.9): K = K_n ∪ K_p, K_n ∩ K_p = ∅.

    Args:
        active_claims: List of claim dicts.
        justifications: List of CanonicalJustification objects.
        literals: Claim-ID-to-Literal mapping from T1.

    Returns:
        KnowledgeBase with axioms (K_n) and premises (K_p).
    """
    # Find which claims have a reported_claim justification
    reported_claim_ids = {
        j.conclusion_claim_id
        for j in justifications
        if j.rule_kind == "reported_claim"
    }

    normalized_claims = coerce_active_claims(active_claims)
    claim_by_id = {str(claim.claim_id): claim for claim in normalized_claims}
    kn: set[Literal] = set()
    kp: set[Literal] = set()

    for cid in reported_claim_ids:
        literal_key = claim_key(cid)
        if literal_key not in literals:
            continue
        claim = claim_by_id.get(cid)
        if claim is None:
            continue
        lit = literals[literal_key]
        if _claim_attr(claim, "premise_kind") == "necessary":
            kn.add(lit)
        else:
            kp.add(lit)

    return KnowledgeBase(axioms=frozenset(kn), premises=frozenset(kp))


# ── T5: preferences ──────────────────────────────────────────────


def _component_wise_dominates(a: list[float], b: list[float]) -> bool:
    """True if a is strictly dominated by b (a weaker than b).

    b dominates a iff every component of b >= corresponding component of a,
    AND at least one component is strictly greater. This is standard
    Pareto domination — a strict partial order (irreflexive, transitive).
    """
    if len(a) != len(b):
        return False
    return all(ai <= bi for ai, bi in zip(a, b)) and any(ai < bi for ai, bi in zip(a, b))


def _transitive_closure(pairs: set[tuple[Literal, Literal]]) -> frozenset[tuple[Literal, Literal]]:
    """Compute transitive closure of a binary relation over Literals."""
    closure = set(pairs)
    changed = True
    while changed:
        changed = False
        new_pairs: set[tuple[Literal, Literal]] = set()
        for a, b in closure:
            for c, d in closure:
                if b == c and (a, d) not in closure:
                    new_pairs.add((a, d))
        if new_pairs:
            closure |= new_pairs
            changed = True
    return frozenset(closure)


def build_preference_config(
    active_claims: Sequence[ActiveClaimInput],
    literals: dict[LiteralKey, Literal],
    defeasible_rules: frozenset[Rule],
    *,
    comparison: str = "elitist",
    link: str = "last",
) -> PreferenceConfig:
    """Build preference orderings from claim metadata.

    T5 (proposals/aspic-bridge-spec.md):
    - Premise ordering: component-wise domination of metadata_strength_vector.
    - Rule ordering: empty (no rule ordering — rules are incomparable).

    Modgil & Prakken 2018, Def 22 (p.22): orderings must be strict
    partial orders (irreflexive, transitive).

    Args:
        active_claims: List of claim dicts with metadata.
        literals: Claim-ID-to-Literal mapping from T1.
        defeasible_rules: Defeasible rules from T2 (unused for now).

    Returns:
        PreferenceConfig with premise_order and empty rule_order.
    """
    normalized_claims = coerce_active_claims(active_claims)
    claim_by_id = {str(claim.claim_id): claim for claim in normalized_claims}
    premise_order: set[tuple[Literal, Literal]] = set()

    # Filter the literal map down to entries that actually correspond
    # to active claims. After T2.5 (grounded_rules_to_rules) the same
    # ``literals`` dict also carries ground-atom keys like
    # ``"bird(tweety)"`` that have no matching claim metadata; those
    # literals cannot participate in a premise ordering (Modgil &
    # Prakken 2018 Def 22 p.22 uses the claim strength vector, which
    # only exists for authored claims). Ground atoms without metadata
    # are treated as incomparable — the zero element of the strict
    # partial order (honest ignorance, per project CLAUDE.md).
    claim_ids = [
        key.claim_id
        for key in literals.keys()
        if isinstance(key, ClaimLiteralKey) and key.claim_id in claim_by_id
    ]
    for i, cid_a in enumerate(claim_ids):
        for cid_b in claim_ids[i + 1:]:
            vec_a = metadata_strength_vector(claim_by_id[cid_a])
            vec_b = metadata_strength_vector(claim_by_id[cid_b])
            lit_a = literals[claim_key(cid_a)]
            lit_b = literals[claim_key(cid_b)]

            if _component_wise_dominates(vec_a, vec_b):
                # a is weaker than b
                premise_order.add((lit_a, lit_b))
            elif _component_wise_dominates(vec_b, vec_a):
                # b is weaker than a
                premise_order.add((lit_b, lit_a))

    premise_order_closed = _transitive_closure(premise_order)

    return PreferenceConfig(
        rule_order=frozenset(),
        premise_order=premise_order_closed,
        comparison=comparison,
        link=link,
    )


# ── T6: build_bridge_csaf ────────────────────────────────────────


def _build_language(
    literals: dict[LiteralKey, Literal],
    strict_rules: frozenset[Rule],
    defeasible_rules: frozenset[Rule],
    kb: KnowledgeBase,
) -> frozenset[Literal]:
    """Build the full language L from all components.

    L must include: all claim literals, their contraries, all rule-name
    literals (for defeasible rules), their contraries, and all literals
    from rules (including transposition-generated).

    Modgil & Prakken 2018, Def 1 (p.8): L is closed under contrariness.
    """
    lang: set[Literal] = set()

    # Claim literals and their contraries
    for lit in literals.values():
        lang.add(lit)
        lang.add(lit.contrary)

    # KB literals and contraries
    for lit in kb.axioms | kb.premises:
        lang.add(lit)
        lang.add(lit.contrary)

    # Rule-name literals for defeasible rules and their contraries
    for rule in defeasible_rules:
        if rule.name is not None:
            name_lit = Literal(atom=GroundAtom(rule.name), negated=False)
            lang.add(name_lit)
            lang.add(name_lit.contrary)

    # All literals from rule antecedents/consequents and their contraries
    for rule in strict_rules | defeasible_rules:
        lang.add(rule.consequent)
        lang.add(rule.consequent.contrary)
        for ante in rule.antecedents:
            lang.add(ante)
            lang.add(ante.contrary)

    return frozenset(lang)


def build_bridge_csaf(
    active_claims: Sequence[ActiveClaimInput],
    justifications: list[CanonicalJustification],
    stances: Sequence[StanceRowInput],
    *,
    bundle: GroundedRulesBundle,
    comparison: str = "elitist",
    link: str = "last",
) -> CSAF:
    """Build a complete CSAF from a claim graph plus a grounded-rules bundle.

    T6 (proposals/aspic-bridge-spec.md): orchestrates T1, T2, T2.5,
    T3-T5, then calls aspic.py's
    build_arguments/compute_attacks/compute_defeats.

    Modgil & Prakken 2018, Def 12 (p.13): a c-SAF is well-defined iff
    it is axiom consistent, well-formed, and closed under transposition.
    Diller, Borg, Bex 2025 §3 Def 9: the grounded ASPIC+ rule set is a
    deterministic function of program plus fact base; threading the
    bundle explicitly through the bridge is what makes the resulting
    CSAF reproducible from the same inputs. Garcia & Simari 2004 §3.1
    (p.4): the ground instance expansion is a pure function of the
    Herbrand base — we consume it here via ``grounded_rules_to_rules``.

    Args:
        active_claims: List of claim dicts.
        justifications: List of CanonicalJustification objects.
        stances: List of stance dicts.
        bundle: Immutable grounder output. Required — pass
            ``GroundedRulesBundle.empty()`` at call sites that do not
            exercise grounding. No ``Optional`` fallback: every caller
            must state explicitly whether it is grounding or not.

    Returns:
        A complete CSAF with arguments, attacks, defeats, and Dung AF.
    """
    # T1: claims -> literals
    normalized_claims = coerce_active_claims(active_claims)
    lits = claims_to_literals(normalized_claims)

    # T2: justifications -> rules
    strict_rules, defeasible_rules = justifications_to_rules(justifications, lits)

    # T2.5: ground-atom rules from the bundle. Diller, Borg, Bex 2025
    # §3 Def 9 determinism: the ground instance set is a function of
    # (program, fact base) — we must consume the bundle here (not
    # re-ground) so the same inputs yield the same R_d. The call
    # extends ``lits`` in place with one entry per antecedent/consequent
    # ground atom, so downstream T3/T4/T5 see every literal the
    # ground rules reference. Modgil & Prakken 2018 Def 2 (p.8): R_s
    # and R_d are union sets — merging the grounded output into the
    # T2 output is the natural identity on the rule monoid.
    ground_strict, ground_defeasible, lits = grounded_rules_to_rules(bundle, lits)
    strict_rules = strict_rules | ground_strict
    defeasible_rules = defeasible_rules | ground_defeasible

    # T3: stances -> contrariness
    contrariness = stances_to_contrariness(stances, lits, defeasible_rules)

    # T4: claims -> KB
    kb = claims_to_kb(normalized_claims, justifications, lits)

    # T4.5: bundle ``definitely`` facts become K_n axioms so argument
    # construction can bottom out on the ground Herbrand base. Modgil &
    # Prakken 2018 Def 4 (p.9); Garcia & Simari 2004 §3; Diller, Borg,
    # Bex 2025 §3 Def 7.
    kb = _ground_facts_to_axioms(bundle, lits, kb)

    # Build the language (before transposition, to bootstrap)
    language = _build_language(lits, strict_rules, defeasible_rules, kb)

    # Transposition closure on strict rules (Def 12, p.13)
    closed_strict = transposition_closure(strict_rules, language, contrariness)

    # Rebuild language with transposition-generated literals
    language = _build_language(lits, closed_strict, defeasible_rules, kb)

    # T5: preferences
    pref = build_preference_config(
        normalized_claims,
        lits,
        defeasible_rules,
        comparison=comparison,
        link=link,
    )

    # Build ArgumentationSystem
    system = ArgumentationSystem(
        language=language,
        contrariness=contrariness,
        strict_rules=closed_strict,
        defeasible_rules=defeasible_rules,
    )

    # Build arguments, attacks, defeats
    arguments = build_arguments(system, kb)
    attacks = compute_attacks(arguments, system)
    defeat_attacks = compute_defeats(attacks, arguments, system, kb, pref)

    # Extract defeat pairs
    defeat_pairs = frozenset((atk.attacker, atk.target) for atk in defeat_attacks)

    # Build arg_to_id / id_to_arg (deterministic ordering)
    sorted_args = sorted(arguments, key=lambda a: repr(a))
    arg_to_id: dict[Argument, str] = {}
    id_to_arg: dict[str, Argument] = {}
    for i, arg in enumerate(sorted_args):
        aid = f"arg_{i}"
        arg_to_id[arg] = aid
        id_to_arg[aid] = arg

    # Build Dung AF with string IDs (defeats only — pure Dung AF for grounded semantics)
    af_arguments = frozenset(arg_to_id.values())
    af_defeats = frozenset(
        (arg_to_id[a], arg_to_id[t])
        for a, t in defeat_pairs
        if a in arg_to_id and t in arg_to_id
    )

    framework = ArgumentationFramework(
        arguments=af_arguments,
        defeats=af_defeats,
        attacks=frozenset(
            (arg_to_id[atk.attacker], arg_to_id[atk.target])
            for atk in attacks
            if atk.attacker in arg_to_id and atk.target in arg_to_id
        ),
    )

    return CSAF(
        system=system,
        kb=kb,
        pref=pref,
        arguments=arguments,
        attacks=attacks,
        defeats=defeat_pairs,
        framework=framework,
        arg_to_id=arg_to_id,
        id_to_arg=id_to_arg,
    )


# ── Goal-directed query ────────────────────────────────────────────


@dataclass(frozen=True)
class ClaimQueryResult:
    """Result of a goal-directed query for a specific claim.

    Combines backward-chaining argument construction with attack/defeat
    computation to answer "what is the argumentation status of this claim?"

    Attributes:
        claim_id: The queried goal reference. Strings mean authored claim ids;
            grounded queries should use ``GroundAtom`` or ``LiteralKey``.
        goal: The Literal corresponding to the claim.
        arguments_for: Arguments whose conclusion is the goal literal.
        arguments_against: Arguments whose conclusion is contrary to the goal.
        attacks: All attacks among the relevant arguments.
        defeats: Defeat pairs after preference filtering.
    """

    claim_id: str | GroundAtom | LiteralKey
    goal: Literal
    arguments_for: frozenset[Argument]
    arguments_against: frozenset[Argument]
    attacks: frozenset[Attack]
    defeats: frozenset[tuple[Argument, Argument]]


def _query_goal_key(goal_ref: str | GroundAtom | LiteralKey) -> LiteralKey:
    """Convert a query boundary input to the internal typed key surface.

    Strings are authored claim ids only. Grounded goals must cross the boundary
    as ``GroundAtom`` values (or prebuilt ``LiteralKey`` objects), so the core
    bridge never has to guess whether a string is a claim id or an encoded atom.
    """

    if isinstance(goal_ref, str):
        return claim_key(goal_ref)
    if isinstance(goal_ref, GroundAtom):
        return ground_key(goal_ref, False)
    return goal_ref


def _goal_contraries(
    literal: Literal,
    contrariness: ContrarinessFn,
    language: frozenset[Literal],
) -> frozenset[Literal]:
    """Return every language literal that conflicts with ``literal``.

    The query path needs the same notion of "arguments against the goal" as the
    argument builder: any argument whose conclusion is contradictory to the goal
    or is a directional contrary of it.
    """

    return frozenset(
        other
        for other in language
        if contrariness.is_contradictory(other, literal)
        or contrariness.is_contrary(other, literal)
    )


def query_claim(
    claim_id: str | GroundAtom | LiteralKey,
    active_claims: Sequence[ActiveClaimInput],
    justifications: list[CanonicalJustification],
    stances: Sequence[StanceRowInput],
    *,
    bundle: GroundedRulesBundle,
    comparison: str = "elitist",
    link: str = "last",
    max_depth: int = 10,
) -> ClaimQueryResult:
    """Goal-directed query for a specific claim's argumentation status.

    Instead of building the full CSAF (all arguments for all claims),
    this constructs only the arguments relevant to the queried claim
    using backward chaining, then computes attacks and defeats on
    that focused subset.

    Uses the same T1-T5 translation pipeline as build_bridge_csaf(),
    but replaces the exhaustive build_arguments() call with the
    goal-directed build_arguments_for().

    Ordering rule (pinned by Chunk 1.8a handoff): the bundle merge
    into ``lits`` happens **before** the goal-key existence check.
    This is what lets grounded goals like
    ``GroundAtom("flies", ("tweety",))`` resolve against the typed
    ground-literal keys that T2.5 introduces. Modgil & Prakken 2018
    Def 5 (pp.9-10): backward chaining needs every literal the rule
    set references in the language; T2.5 is where those literals
    enter. Diller, Borg, Bex 2025 §3 Def 9: the ground-atom key set
    is a deterministic function of (program, fact base), so running
    the extension before the existence check is safe and reproducible.

    Args:
        claim_id: The goal to query. Strings mean authored claim ids.
            Grounded goals must be passed as ``GroundAtom`` (or as an
            already-built ``LiteralKey``). Unknown goals raise
            ``KeyError`` rather than synthesising an empty answer.
        active_claims: List of claim dicts (same as build_bridge_csaf).
        justifications: List of CanonicalJustification objects.
        stances: List of stance dicts.
        bundle: Immutable grounder output. Required — pass
            ``GroundedRulesBundle.empty()`` at call sites that do not
            exercise grounding.
        comparison: Preference comparison mode ("elitist" or "democratic").
        link: Preference link principle ("last" or "weakest").
        max_depth: Maximum backward chaining depth. Default 10.

    Returns:
        ClaimQueryResult with arguments for/against, attacks, and defeats.

    Raises:
        KeyError: If ``claim_id`` is not found in the extended literal
            map (claim literals + bundle ground atoms).
    """
    # T1: claims -> literals.
    normalized_claims = coerce_active_claims(active_claims)
    lits = claims_to_literals(normalized_claims)

    # T2: justifications -> rules.
    strict_rules, defeasible_rules = justifications_to_rules(justifications, lits)

    # T2.5: ground-atom rules from the bundle. MUST run before the
    # membership check below — otherwise any query whose goal is a
    # grounded atom raises KeyError even though the bundle contains a
    # rule that would resolve it.
    # Modgil & Prakken 2018 Def 1 (p.8): L must contain every literal
    # appearing in a rule; ``grounded_rules_to_rules`` extends
    # ``lits`` with exactly those entries. Garcia & Simari 2004 §3:
    # DeLP queries resolve against the ground Herbrand base, which
    # is precisely what the bundle materialises.
    ground_strict, ground_defeasible, lits = grounded_rules_to_rules(bundle, lits)
    strict_rules = strict_rules | ground_strict
    defeasible_rules = defeasible_rules | ground_defeasible

    goal_key = _query_goal_key(claim_id)
    if goal_key not in lits:
        raise KeyError(claim_id)
    goal = lits[goal_key]

    contrariness = stances_to_contrariness(stances, lits, defeasible_rules)
    kb = claims_to_kb(normalized_claims, justifications, lits)
    # T4.5: bundle ``definitely`` facts become K_n axioms (see
    # build_bridge_csaf for the citation chain).
    kb = _ground_facts_to_axioms(bundle, lits, kb)
    language = _build_language(lits, strict_rules, defeasible_rules, kb)
    closed_strict = transposition_closure(strict_rules, language, contrariness)
    language = _build_language(lits, closed_strict, defeasible_rules, kb)

    pref = build_preference_config(
        normalized_claims, lits, defeasible_rules,
        comparison=comparison, link=link,
    )

    system = ArgumentationSystem(
        language=language,
        contrariness=contrariness,
        strict_rules=closed_strict,
        defeasible_rules=defeasible_rules,
    )

    # Goal-directed argument construction
    arguments = build_arguments_for(
        system, kb, goal,
        include_attackers=True,
        max_depth=max_depth,
    )

    # Compute attacks and defeats on the focused subset
    attacks = compute_attacks(arguments, system)
    defeat_attacks = compute_defeats(attacks, arguments, system, kb, pref)
    defeat_pairs = frozenset((atk.attacker, atk.target) for atk in defeat_attacks)

    # Partition into for/against
    args_for = frozenset(a for a in arguments if conc(a) == goal)
    against_literals = _goal_contraries(goal, system.contrariness, system.language)
    args_against = frozenset(
        a for a in arguments if conc(a) in against_literals
    )

    return ClaimQueryResult(
        claim_id=claim_id,
        goal=goal,
        arguments_for=args_for,
        arguments_against=args_against,
        attacks=attacks,
        defeats=defeat_pairs,
    )


# ── T7: CSAF -> StructuredProjection ─────────────────────────────


def _projection_conclusion_key(literal: Literal) -> str:
    """Return a stable string identity for a projected conclusion literal."""

    return json.dumps(
        {
            "predicate": literal.atom.predicate,
            "arguments": [_typed_scalar_key(value) for value in literal.atom.arguments],
            "negated": literal.negated,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def csaf_to_projection(
    csaf: CSAF,
    active_claims: Sequence[ActiveClaimInput],
    *,
    support_metadata: SupportMetadata | None = None,
) -> StructuredProjection:
    """Map a CSAF to a StructuredProjection for backward compatibility.

    T7 (proposals/aspic-bridge-spec.md): maps ASPIC+ Argument objects
    back to StructuredArgument instances over the full argument set.
    Claim-backed arguments keep their claim linkage; grounded-only
    arguments project with ``claim_id=None`` and a canonical
    ``conclusion_key``.

    Args:
        csaf: A complete CSAF from T6.
        active_claims: List of claim dicts.
        support_metadata: Optional mapping from claim_id to (Label, SupportQuality).
            When provided, overrides the default label=None / SupportQuality.EXACT
            on projected arguments.

    Returns:
        StructuredProjection with arguments, framework, and mappings.
    """
    metadata = support_metadata or {}
    normalized_claims = coerce_active_claims(active_claims)
    claim_id_set = {str(claim.claim_id) for claim in normalized_claims}
    claim_by_id = {str(claim.claim_id): claim for claim in normalized_claims}

    projected_args: list[StructuredArgument] = []
    projected_arg_ids: set[str] = set()
    claim_to_args: dict[str, list[str]] = {}
    arg_to_claim: dict[str, str] = {}

    for arg in csaf.arguments:
        conclusion = conc(arg)

        arg_id = csaf.arg_to_id[arg]
        cid = conclusion.atom.predicate if conclusion.atom.predicate in claim_id_set and not conclusion.negated else None
        claim = None if cid is None else claim_by_id[cid]

        # Determine top_rule_kind
        tr = top_rule(arg)
        if isinstance(arg, PremiseArg):
            top_kind = "reported_claim"
        elif tr is not None:
            top_kind = tr.kind
        else:
            top_kind = "reported_claim"

        # Determine attackable_kind
        attackable = "base_claim" if isinstance(arg, PremiseArg) else "inference_rule"

        # Premise claim IDs (atoms from prem(arg) that are real claims)
        premise_claim_ids = tuple(
            p.atom.predicate for p in prem(arg) if p.atom.predicate in claim_id_set
        )

        # Sub-argument IDs (excluding self)
        subargument_ids = tuple(
            csaf.arg_to_id[s]
            for s in sub(arg)
            if s != arg and s in csaf.arg_to_id
        )

        # Strength: claim-backed arguments use claim strength; grounded-only
        # arguments do not have claim metadata yet.
        if claim is None:
            strength = 0.0
        else:
            vec = claim_strength(claim)
            strength = statistics.mean(vec) if vec else 0.0

        # Justification ID
        if isinstance(arg, PremiseArg):
            just_id = (
                f"reported:{cid}" if cid is not None
                else f"premise:{_projection_conclusion_key(conclusion)}"
            )
        elif tr is not None and tr.name is not None:
            just_id = tr.name
        else:
            just_id = (
                f"reported:{cid}" if cid is not None
                else f"premise:{_projection_conclusion_key(conclusion)}"
            )

        # Dependency claim IDs track only authored claims.
        dependency_claim_ids = tuple(
            p.atom.predicate for p in prem(arg) if p.atom.predicate in claim_id_set
        )

        # Apply support_metadata if provided, else compute defaults from claim.
        if cid is not None and cid in metadata:
            label, support_quality = metadata[cid]
        elif claim is not None:
            label, support_quality = _default_support_metadata(claim)
        else:
            label, support_quality = None, SupportQuality.EXACT

        sa = StructuredArgument(
            arg_id=arg_id,
            conclusion_key=_projection_conclusion_key(conclusion),
            claim_id=cid,
            conclusion_concept_id=(
                None if claim is None or claim.concept_id is None else str(claim.concept_id)
            ),
            premise_claim_ids=premise_claim_ids,
            label=label,
            strength=strength,
            top_rule_kind=top_kind,
            attackable_kind=attackable,
            subargument_ids=subargument_ids,
            support_quality=support_quality,
            justification_id=just_id,
            dependency_claim_ids=dependency_claim_ids,
        )
        projected_args.append(sa)
        projected_arg_ids.add(arg_id)
        if cid is not None:
            claim_to_args.setdefault(cid, []).append(arg_id)
            arg_to_claim[arg_id] = cid

    # Filter framework to only projected arguments
    proj_defeats = frozenset(
        (a, t) for a, t in csaf.framework.defeats
        if a in projected_arg_ids and t in projected_arg_ids
    )
    # Build attacks from CSAF Attack objects (attacks >= defeats per M&P 2018 Def 14)
    proj_attacks = frozenset(
        (csaf.arg_to_id[atk.attacker], csaf.arg_to_id[atk.target])
        for atk in csaf.attacks
        if atk.attacker in csaf.arg_to_id and atk.target in csaf.arg_to_id
        and csaf.arg_to_id[atk.attacker] in projected_arg_ids
        and csaf.arg_to_id[atk.target] in projected_arg_ids
    )

    proj_framework = ArgumentationFramework(
        arguments=frozenset(projected_arg_ids),
        defeats=proj_defeats,
        attacks=proj_attacks,
    )

    claim_to_argument_ids = {
        cid: tuple(aids) for cid, aids in claim_to_args.items()
    }

    return StructuredProjection(
        arguments=tuple(sorted(projected_args, key=lambda a: a.arg_id)),
        framework=proj_framework,
        claim_to_argument_ids=claim_to_argument_ids,
        argument_to_claim_id=arg_to_claim,
    )


# ── Entry point: drop-in replacement for build_structured_projection ─


def _extract_stance_rows(
    store: StanceStore,
    active_by_id: dict[str, ActiveClaim],
    *,
    active_graph: ActiveWorldGraph | None,
) -> list[StanceRow]:
    """Extract stance rows from active_graph or store.

    Mirrors structured_argument._stance_rows — same logic, same output shape.
    """
    if active_graph is not None:
        active_ids = set(active_graph.active_claim_ids)
        rows: list[StanceRow] = []
        for relation in active_graph.compiled.relations:
            if relation.source_id not in active_ids or relation.target_id not in active_ids:
                continue
            if relation.relation_type not in _ATTACK_TYPES and relation.relation_type not in _SUPPORT_TYPES:
                continue
            rows.append(
                StanceRow.from_mapping(
                    {
                        "claim_id": relation.source_id,
                        "target_claim_id": relation.target_id,
                        "stance_type": relation.relation_type,
                        **dict(relation.attributes),
                    }
                )
            )
        return rows
    return [
        coerce_stance_row(row)
        for row in store.stances_between(set(active_by_id))
    ]


def _extract_justifications(
    active_by_id: dict[str, ActiveClaim],
    stance_rows: list[StanceRow],
    *,
    active_graph: ActiveWorldGraph | None,
) -> list[CanonicalJustification]:
    """Extract canonical justifications from active_graph or stance rows.

    Mirrors structured_argument._canonical_justifications — same logic,
    same output shape.
    """
    if active_graph is not None:
        return list(claim_justifications_from_active_graph(active_graph))

    justifications: list[CanonicalJustification] = [
        CanonicalJustification(
            justification_id=f"reported:{claim_id}",
            conclusion_claim_id=claim_id,
            rule_kind="reported_claim",
        )
        for claim_id in sorted(active_by_id)
    ]
    for row in stance_rows:
        if row.stance_type not in {"supports", "explains"}:
            continue
        justifications.append(
            CanonicalJustification(
                justification_id=(
                    f"{row.stance_type}:{row.claim_id}->{row.target_claim_id}"
                ),
                conclusion_claim_id=row.target_claim_id,
                premise_claim_ids=(row.claim_id,),
                rule_kind=row.stance_type,
                attributes=tuple(row.attributes.items()),
            )
        )
    return sorted(justifications)


def build_aspic_projection(
    store: StanceStore,
    active_claims: Sequence[ActiveClaimInput],
    *,
    bundle: GroundedRulesBundle,
    support_metadata: SupportMetadata | None = None,
    comparison: str = "elitist",
    link: str = "last",
    active_graph: ActiveWorldGraph | None = None,
) -> StructuredProjection:
    """Build a StructuredProjection via the ASPIC+ bridge (T1-T7).

    Drop-in replacement for structured_argument.build_structured_projection.
    Same signature, same return type. Routes through the formal ASPIC+
    engine instead of the legacy structured_argument path.

    Diller, Borg, Bex 2025 §3 Def 9: the ground rule set is part of
    the program identity. The projection entry point therefore
    requires an explicit bundle so the render layer and storage see
    the same rule set the engine argued over. Phase-1 call sites that
    do not exercise grounding should pass
    ``GroundedRulesBundle.empty()``.

    Args:
        store: ArtifactStore providing stances_between().
        active_claims: List of active claim dicts.
        bundle: Immutable grounder output. Required. Threaded into
            ``build_bridge_csaf``. Pass ``GroundedRulesBundle.empty()``
            at call sites that do not exercise grounding.
        support_metadata: Optional mapping from claim_id to (Label, SupportQuality).
        comparison: Preference comparison strategy (default "elitist").
        link: Preference link strategy (default "last").
        active_graph: Optional ActiveWorldGraph for graph-based extraction.

    Returns:
        StructuredProjection with arguments, framework, and mappings.
    """
    normalized_claims = coerce_active_claims(active_claims)
    active_by_id = {
        str(claim.claim_id): claim
        for claim in normalized_claims
    }

    # Extract stances and justifications (same logic as structured_projection.py)
    stance_rows = _extract_stance_rows(store, active_by_id, active_graph=active_graph)
    justifications = _extract_justifications(
        active_by_id, stance_rows, active_graph=active_graph,
    )

    # T6: build the full CSAF via the bridge. Thread the bundle
    # through so T2.5 runs inside ``build_bridge_csaf`` exactly once.
    csaf = build_bridge_csaf(
        normalized_claims,
        justifications,
        stance_rows,
        bundle=bundle,
        comparison=comparison,
        link=link,
    )

    # T7: project back to StructuredProjection
    return csaf_to_projection(csaf, normalized_claims, support_metadata=support_metadata)
