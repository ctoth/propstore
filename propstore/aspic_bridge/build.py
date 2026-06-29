"""Shared bridge compilation pipeline and CSAF assembly.

:func:`compile_bridge_context` lowers claims/justifications/stances (plus a
grounded bundle and any lifting decisions) into the ASPIC+ engine inputs:
literals, contrariness, knowledge base, preference config, and a
transposition-closed :class:`ArgumentationSystem`. :func:`build_bridge_csaf` then
runs the kernel — ``build_arguments`` → ``compute_attacks`` → ``compute_defeats``
— and projects the structured framework down to a Dung AF over argument ids,
returning the package's ``CSAF`` directly (CLAUDE.md substrate boundary).

Preference-sensitive directional stances (supersede/undermine) are filtered after
attack and defeat computation so a strictly-weaker attacker does not defeat its
stronger target.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from argumentation.core.dung import ArgumentationFramework
from argumentation.structured.aspic.aspic import (
    CSAF,
    Argument,
    ArgumentationSystem,
    Attack,
    ContrarinessFn,
    GroundAtom,
    KnowledgeBase,
    Literal,
    PreferenceConfig,
    PremiseArg,
    Rule,
    build_arguments,
    compute_attacks,
    compute_defeats,
    conc,
    transposition_closure,
)
from argumentation.structured.aspic.datalog_grounding import GroundRuleOrigin

from propstore.aspic_bridge.grounding import ground_facts_to_axioms, project_grounded_rules
from propstore.aspic_bridge.lifting_projection import LiftingProjection, project_lifting_decisions
from propstore.aspic_bridge.translate import (
    StanceInput,
    build_preference_config,
    claims_to_kb,
    claims_to_literals,
    justifications_to_rules,
    preference_sensitive_stance_pairs,
    stances_to_contrariness,
)
from propstore.context_lifting import LiftingDecision
from propstore.core.active_claims import ActiveClaim, ActiveClaimInput, coerce_active_claims
from propstore.core.justifications import CanonicalJustification
from propstore.core.literal_keys import LiteralKey
from propstore.grounding.bundle import GroundedRulesBundle


@dataclass(frozen=True)
class BridgeCompilation:
    """Shared pre-engine bridge state used by CSAF building and queries."""

    normalized_claims: tuple[ActiveClaim, ...]
    literals: dict[LiteralKey, Literal]
    contrariness: ContrarinessFn
    kb: KnowledgeBase
    pref: PreferenceConfig
    system: ArgumentationSystem
    lifting_projection: LiftingProjection
    grounded_rule_origins: Mapping[Rule, GroundRuleOrigin]


def _build_language(
    literals: dict[LiteralKey, Literal],
    strict_rules: frozenset[Rule],
    defeasible_rules: frozenset[Rule],
    kb: KnowledgeBase,
) -> frozenset[Literal]:
    language: set[Literal] = set()
    for literal in literals.values():
        language.add(literal)
        language.add(literal.contrary)
    for literal in kb.axioms | kb.premises:
        language.add(literal)
        language.add(literal.contrary)
    for rule in defeasible_rules:
        if rule.name is None:
            continue
        name_lit = Literal(atom=GroundAtom(rule.name), negated=False)
        language.add(name_lit)
        language.add(name_lit.contrary)
    for rule in strict_rules | defeasible_rules:
        language.add(rule.consequent)
        language.add(rule.consequent.contrary)
        for antecedent in rule.antecedents:
            language.add(antecedent)
            language.add(antecedent.contrary)
    return frozenset(language)


def compile_bridge_context(
    active_claims: Sequence[ActiveClaimInput],
    justifications: list[CanonicalJustification],
    stances: Sequence[StanceInput],
    *,
    bundle: GroundedRulesBundle,
    lifting_decisions: Sequence[LiftingDecision] = (),
    comparison: str = "elitist",
    link: str = "last",
) -> BridgeCompilation:
    """Compile claim-graph inputs into the shared ASPIC+ engine inputs."""

    normalized_claims = coerce_active_claims(active_claims)
    literals = claims_to_literals(normalized_claims)
    lifting_projection = project_lifting_decisions(literals, lifting_decisions)
    literals = lifting_projection.literals

    strict_rules, defeasible_rules = justifications_to_rules(justifications, literals)
    strict_rules |= lifting_projection.strict_rules
    defeasible_rules |= lifting_projection.defeasible_rules

    grounded_projection = project_grounded_rules(bundle, literals)
    literals = grounded_projection.literals
    strict_rules |= grounded_projection.strict_rules
    defeasible_rules |= grounded_projection.defeasible_rules

    contrariness = stances_to_contrariness(
        stances, literals, defeasible_rules, rule_origins=grounded_projection.origins
    )
    kb = claims_to_kb(normalized_claims, justifications, literals)
    kb = ground_facts_to_axioms(bundle, literals, kb)

    language = _build_language(literals, strict_rules, defeasible_rules, kb)
    closed_strict, language = transposition_closure(strict_rules, language, contrariness)

    pref = build_preference_config(
        normalized_claims,
        literals,
        defeasible_rules,
        rule_order=grounded_projection.rule_order,
        comparison=comparison,
        link=link,
    )

    system = ArgumentationSystem(
        language=language,
        contrariness=contrariness,
        strict_rules=closed_strict,
        defeasible_rules=defeasible_rules,
    )

    return BridgeCompilation(
        normalized_claims=normalized_claims,
        literals=literals,
        contrariness=contrariness,
        kb=kb,
        pref=pref,
        system=system,
        lifting_projection=lifting_projection,
        grounded_rule_origins=grounded_projection.origins,
    )


def _targeted_literal_for_directional_filter(attack: Attack) -> Literal | None:
    if attack.kind == "undermining":
        if not isinstance(attack.target_sub, PremiseArg):
            return None
        return attack.target_sub.premise
    if attack.kind == "rebutting":
        return conc(attack.target_sub)
    return None


def filter_preference_sensitive_stance_attacks(
    attacks: frozenset[Attack],
    directed_pairs: frozenset[tuple[Literal, Literal]],
) -> frozenset[Attack]:
    """Drop a directional attack whose stronger target supersedes the attacker."""

    if not directed_pairs:
        return attacks
    filtered: set[Attack] = set()
    for attack in attacks:
        target_literal = _targeted_literal_for_directional_filter(attack)
        if target_literal is None:
            filtered.add(attack)
            continue
        attacker_literal = conc(attack.attacker)
        if (
            (target_literal, attacker_literal) in directed_pairs
            and (attacker_literal, target_literal) not in directed_pairs
        ):
            continue
        filtered.add(attack)
    return frozenset(filtered)


def filter_preference_sensitive_stance_defeats(
    defeat_attacks: frozenset[Attack],
    *,
    arguments: frozenset[Argument],
    system: ArgumentationSystem,
    kb: KnowledgeBase,
    pref: PreferenceConfig,
    directed_pairs: frozenset[tuple[Literal, Literal]],
) -> frozenset[Attack]:
    """Re-check directional defeats under the authored superiority pair."""

    if not directed_pairs:
        return defeat_attacks
    filtered: set[Attack] = set()
    for attack in defeat_attacks:
        target_literal = _targeted_literal_for_directional_filter(attack)
        if target_literal is None:
            filtered.add(attack)
            continue
        attacker_literal = conc(attack.attacker)
        if (attacker_literal, target_literal) not in directed_pairs:
            filtered.add(attack)
            continue
        preference_sensitive_system = replace(
            system,
            contrariness=ContrarinessFn(
                contradictories=system.contrariness.contradictories
                | frozenset({(attacker_literal, target_literal)}),
                contraries=frozenset(
                    pair
                    for pair in system.contrariness.contraries
                    if pair != (attacker_literal, target_literal)
                ),
            ),
        )
        if compute_defeats(frozenset({attack}), arguments, preference_sensitive_system, kb, pref):
            filtered.add(attack)
    return frozenset(filtered)


def build_bridge_csaf(
    active_claims: Sequence[ActiveClaimInput],
    justifications: list[CanonicalJustification],
    stances: Sequence[StanceInput],
    *,
    bundle: GroundedRulesBundle,
    lifting_decisions: Sequence[LiftingDecision] = (),
    comparison: str = "elitist",
    link: str = "last",
) -> CSAF:
    """Build a complete CSAF from claim-graph inputs and a grounded bundle."""

    compiled = compile_bridge_context(
        active_claims,
        justifications,
        stances,
        bundle=bundle,
        lifting_decisions=lifting_decisions,
        comparison=comparison,
        link=link,
    )

    arguments = build_arguments(compiled.system, compiled.kb)
    attacks = compute_attacks(arguments, compiled.system)
    directed_pairs = preference_sensitive_stance_pairs(stances, compiled.literals)
    attacks = filter_preference_sensitive_stance_attacks(attacks, directed_pairs)
    defeat_attacks = compute_defeats(attacks, arguments, compiled.system, compiled.kb, compiled.pref)
    defeat_attacks = filter_preference_sensitive_stance_defeats(
        defeat_attacks,
        arguments=arguments,
        system=compiled.system,
        kb=compiled.kb,
        pref=compiled.pref,
        directed_pairs=directed_pairs,
    )
    defeat_pairs = frozenset((attack.attacker, attack.target) for attack in defeat_attacks)

    arg_to_id: dict[Argument, str] = {}
    id_to_arg: dict[str, Argument] = {}
    for index, argument in enumerate(sorted(arguments, key=repr)):
        arg_id = f"arg_{index}"
        arg_to_id[argument] = arg_id
        id_to_arg[arg_id] = argument

    def require_argument_id(argument: Argument, edge_kind: str) -> str:
        try:
            return arg_to_id[argument]
        except KeyError as exc:
            raise AssertionError(
                f"{edge_kind} references argument outside bridge argument domain: {argument!r}"
            ) from exc

    framework = ArgumentationFramework(
        arguments=frozenset(arg_to_id.values()),
        defeats=frozenset(
            (require_argument_id(attacker, "defeat"), require_argument_id(target, "defeat"))
            for attacker, target in defeat_pairs
        ),
        attacks=frozenset(
            (require_argument_id(attack.attacker, "attack"), require_argument_id(attack.target, "attack"))
            for attack in attacks
        ),
    )

    return CSAF(
        system=compiled.system,
        kb=compiled.kb,
        pref=compiled.pref,
        arguments=arguments,
        attacks=attacks,
        defeats=defeat_pairs,
        framework=framework,
        arg_to_id=arg_to_id,
        id_to_arg=id_to_arg,
    )


__all__ = [
    "BridgeCompilation",
    "build_bridge_csaf",
    "compile_bridge_context",
    "filter_preference_sensitive_stance_attacks",
    "filter_preference_sensitive_stance_defeats",
]
