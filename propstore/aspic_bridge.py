"""ASPIC+ translation layer from propstore data to the formal engine.

Implements translation rules T1-T7 from proposals/aspic-bridge-spec.md:
    T1: claims_to_literals — claims -> Literal map
    T2: justifications_to_rules — justifications -> (strict_rules, defeasible_rules)
    T3: stances_to_contrariness — stances -> ContrarinessFn
    T4: claims_to_kb — claims -> KnowledgeBase
    T5: build_preference_config — claims -> PreferenceConfig
    T6: build_bridge_csaf — full bridge -> CSAF
    T7: csaf_to_projection — CSAF -> StructuredProjection

References:
    Modgil & Prakken 2018: Defs 1-22, the complete ASPIC+ framework.
    proposals/aspic-bridge-spec.md: translation rules and rationale.

This module owns propstore-to-ASPIC translation. Projection-level callers
should normally enter through `propstore.structured_projection`.
"""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from typing import Any

from propstore.aspic import (
    Literal,
    ContrarinessFn,
    Rule,
    KnowledgeBase,
    ArgumentationSystem,
    PreferenceConfig,
    CSAF,
    PremiseArg,
    StrictArg,
    DefeasibleArg,
    Attack,
    build_arguments,
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

Argument = PremiseArg | StrictArg | DefeasibleArg
_ATTACK_TYPES = ATTACK_TYPES
_SUPPORT_TYPES = SUPPORT_TYPES


def _claim_attr(claim: ActiveClaim, key: str) -> Any:
    return getattr(claim, key, claim.attributes.get(key))


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


def claims_to_literals(active_claims: list[ActiveClaimInput]) -> dict[str, Literal]:
    """Map each claim to a positive Literal.

    T1 (proposals/aspic-bridge-spec.md): Each claim becomes
    Literal(atom=claim_id, negated=False). The atom is the claim ID,
    not the concept ID — two claims about the same concept are
    different literals.

    Modgil & Prakken 2018, Def 1 (p.8): L is a logical language.

    Args:
        active_claims: List of claim dicts with at least an "id" key.

    Returns:
        Dict mapping claim_id -> Literal.
    """
    normalized_claims = coerce_active_claims(active_claims)
    return {
        str(claim.claim_id): Literal(atom=str(claim.claim_id), negated=False)
        for claim in normalized_claims
    }


# ── T2: justifications -> rules ──────────────────────────────────


def justifications_to_rules(
    justifications: list[CanonicalJustification],
    literals: dict[str, Literal],
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
            continue
        # Skip if any premise or conclusion not in literals
        if j.conclusion_claim_id not in literals:
            continue
        if any(pid not in literals for pid in j.premise_claim_ids):
            continue

        antecedents = tuple(literals[pid] for pid in j.premise_claim_ids)
        consequent = literals[j.conclusion_claim_id]
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


# ── T3: stances -> contrariness ──────────────────────────────────


def stances_to_contrariness(
    stances: Sequence[StanceRowInput],
    literals: dict[str, Literal],
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
    contradictory_pairs: set[tuple[Literal, Literal]] = set()
    contrary_pairs: set[tuple[Literal, Literal]] = set()

    for stance_input in stances:
        stance = coerce_stance_row(stance_input)
        src_id = stance.claim_id
        tgt_id = stance.target_claim_id
        stype = stance.stance_type

        if src_id not in literals or tgt_id not in literals:
            continue

        src = literals[src_id]
        tgt = literals[tgt_id]

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
                matching_rules = [
                    rule
                    for rule in matching_rules
                    if rule.name == target_justification_id
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
                rule_lit = Literal(atom=rule.name, negated=False)
                if src != rule_lit:
                    contrary_pairs.add((src, rule_lit))

    return ContrarinessFn(
        contradictories=frozenset(contradictory_pairs),
        contraries=frozenset(contrary_pairs),
    )


# ── T4: claims -> knowledge base ─────────────────────────────────


def claims_to_kb(
    active_claims: list[ActiveClaimInput],
    justifications: list[CanonicalJustification],
    literals: dict[str, Literal],
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
        if cid not in literals:
            continue
        claim = claim_by_id.get(cid)
        if claim is None:
            continue
        lit = literals[cid]
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
    active_claims: list[ActiveClaimInput],
    literals: dict[str, Literal],
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

    claim_ids = list(literals.keys())
    for i, cid_a in enumerate(claim_ids):
        for cid_b in claim_ids[i + 1:]:
            vec_a = metadata_strength_vector(claim_by_id[cid_a])
            vec_b = metadata_strength_vector(claim_by_id[cid_b])
            lit_a = literals[cid_a]
            lit_b = literals[cid_b]

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
    literals: dict[str, Literal],
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
            name_lit = Literal(atom=rule.name, negated=False)
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
    active_claims: list[ActiveClaimInput],
    justifications: list[CanonicalJustification],
    stances: Sequence[StanceRowInput],
    *,
    comparison: str = "elitist",
    link: str = "last",
) -> CSAF:
    """Build a complete CSAF from a claim graph.

    T6 (proposals/aspic-bridge-spec.md): orchestrates T1-T5, then calls
    aspic.py's build_arguments/compute_attacks/compute_defeats.

    Modgil & Prakken 2018, Def 12 (p.13): a c-SAF is well-defined iff
    it is axiom consistent, well-formed, and closed under transposition.

    Args:
        active_claims: List of claim dicts.
        justifications: List of CanonicalJustification objects.
        stances: List of stance dicts.

    Returns:
        A complete CSAF with arguments, attacks, defeats, and Dung AF.
    """
    # T1: claims -> literals
    normalized_claims = coerce_active_claims(active_claims)
    lits = claims_to_literals(normalized_claims)

    # T2: justifications -> rules
    strict_rules, defeasible_rules = justifications_to_rules(justifications, lits)

    # T3: stances -> contrariness
    contrariness = stances_to_contrariness(stances, lits, defeasible_rules)

    # T4: claims -> KB
    kb = claims_to_kb(normalized_claims, justifications, lits)

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


# ── T7: CSAF -> StructuredProjection ─────────────────────────────


def csaf_to_projection(
    csaf: CSAF,
    active_claims: list[ActiveClaimInput],
    *,
    support_metadata: SupportMetadata | None = None,
) -> StructuredProjection:
    """Map a CSAF to a StructuredProjection for backward compatibility.

    T7 (proposals/aspic-bridge-spec.md): maps ASPIC+ Argument objects
    back to StructuredArgument instances. Transposition-generated
    arguments (negated literals with no corresponding claim) are
    excluded from the projection.

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
        # Skip transposition artifacts — negated literals or atoms not in claims
        if conclusion.negated or conclusion.atom not in claim_id_set:
            continue

        arg_id = csaf.arg_to_id[arg]
        cid = conclusion.atom
        claim = claim_by_id[cid]

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
            p.atom for p in prem(arg) if p.atom in claim_id_set
        )

        # Sub-argument IDs (excluding self)
        subargument_ids = tuple(
            csaf.arg_to_id[s]
            for s in sub(arg)
            if s != arg and s in csaf.arg_to_id
        )

        # Strength: scalar average of claim_strength vector
        vec = claim_strength(claim)
        strength = statistics.mean(vec) if vec else 0.0

        # Justification ID
        if isinstance(arg, PremiseArg):
            just_id = f"reported:{cid}"
        elif tr is not None and tr.name is not None:
            just_id = tr.name
        else:
            just_id = f"reported:{cid}"

        # Dependency claim IDs (all premise atoms)
        dependency_claim_ids = tuple(p.atom for p in prem(arg))

        # Apply support_metadata if provided, else compute defaults from claim
        if cid in metadata:
            label, support_quality = metadata[cid]
        else:
            label, support_quality = _default_support_metadata(claim)

        sa = StructuredArgument(
            arg_id=arg_id,
            claim_id=cid,
            conclusion_concept_id=(
                None if claim.concept_id is None else str(claim.concept_id)
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
    active_claims: list[ActiveClaimInput],
    *,
    support_metadata: SupportMetadata | None = None,
    comparison: str = "elitist",
    link: str = "last",
    active_graph: ActiveWorldGraph | None = None,
) -> StructuredProjection:
    """Build a StructuredProjection via the ASPIC+ bridge (T1-T7).

    Drop-in replacement for structured_argument.build_structured_projection.
    Same signature, same return type. Routes through the formal ASPIC+
    engine instead of the legacy structured_argument path.

    Args:
        store: ArtifactStore providing stances_between().
        active_claims: List of active claim dicts.
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

    # T6: build the full CSAF via the bridge
    csaf = build_bridge_csaf(
        normalized_claims,
        justifications,
        stance_rows,
        comparison=comparison,
        link=link,
    )

    # T7: project back to StructuredProjection
    return csaf_to_projection(csaf, normalized_claims, support_metadata=support_metadata)
