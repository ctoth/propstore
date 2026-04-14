"""Shared bridge compilation pipeline and CSAF assembly."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence

from propstore.aspic import (
    Argument,
    ArgumentationSystem,
    CSAF,
    ContrarinessFn,
    GroundAtom,
    KnowledgeBase,
    Literal,
    PreferenceConfig,
    Rule,
    build_arguments,
    compute_attacks,
    compute_defeats,
    transposition_closure,
)
from propstore.core.active_claims import ActiveClaim, ActiveClaimInput, coerce_active_claims
from propstore.core.justifications import CanonicalJustification
from propstore.core.literal_keys import LiteralKey
from propstore.core.row_types import StanceRowInput
from propstore.dung import ArgumentationFramework
from propstore.grounding.bundle import GroundedRulesBundle

from .grounding import _ground_facts_to_axioms, grounded_rules_to_rules
from .translate import (
    build_preference_config,
    claims_to_kb,
    claims_to_literals,
    justifications_to_rules,
    stances_to_contrariness,
)


@dataclass(frozen=True)
class BridgeCompilation:
    """Shared pre-engine bridge state used by CSAF building and queries."""

    normalized_claims: tuple[ActiveClaim, ...]
    literals: dict[LiteralKey, Literal]
    contrariness: ContrarinessFn
    kb: KnowledgeBase
    pref: PreferenceConfig
    system: ArgumentationSystem


def _build_language(
    literals: dict[LiteralKey, Literal],
    strict_rules: frozenset[Rule],
    defeasible_rules: frozenset[Rule],
    kb: KnowledgeBase,
) -> frozenset[Literal]:
    """Build the full ASPIC+ language from claims, rules, KB, and rule names."""

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
    stances: Sequence[StanceRowInput],
    *,
    bundle: GroundedRulesBundle,
    comparison: str = "elitist",
    link: str = "last",
) -> BridgeCompilation:
    """Compile claim-graph inputs into the shared ASPIC+ engine inputs."""

    normalized_claims = tuple(coerce_active_claims(active_claims))
    literals = claims_to_literals(normalized_claims)

    strict_rules, defeasible_rules = justifications_to_rules(justifications, literals)
    grounded_strict, grounded_defeasible, literals = grounded_rules_to_rules(bundle, literals)
    strict_rules |= grounded_strict
    defeasible_rules |= grounded_defeasible

    contrariness = stances_to_contrariness(stances, literals, defeasible_rules)
    kb = claims_to_kb(normalized_claims, justifications, literals)
    kb = _ground_facts_to_axioms(bundle, literals, kb)

    language = _build_language(literals, strict_rules, defeasible_rules, kb)
    closed_strict = transposition_closure(strict_rules, language, contrariness)
    language = _build_language(literals, closed_strict, defeasible_rules, kb)

    pref = build_preference_config(
        normalized_claims,
        literals,
        defeasible_rules,
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
    )


def build_bridge_csaf(
    active_claims: Sequence[ActiveClaimInput],
    justifications: list[CanonicalJustification],
    stances: Sequence[StanceRowInput],
    *,
    bundle: GroundedRulesBundle,
    comparison: str = "elitist",
    link: str = "last",
) -> CSAF:
    """Build a complete CSAF from claim-graph inputs and a grounded bundle."""

    compiled = compile_bridge_context(
        active_claims,
        justifications,
        stances,
        bundle=bundle,
        comparison=comparison,
        link=link,
    )

    arguments = build_arguments(compiled.system, compiled.kb)
    attacks = compute_attacks(arguments, compiled.system)
    defeat_attacks = compute_defeats(
        attacks,
        arguments,
        compiled.system,
        compiled.kb,
        compiled.pref,
    )
    defeat_pairs = frozenset((attack.attacker, attack.target) for attack in defeat_attacks)

    sorted_args = sorted(arguments, key=repr)
    arg_to_id: dict[Argument, str] = {}
    id_to_arg: dict[str, Argument] = {}
    for index, argument in enumerate(sorted_args):
        arg_id = f"arg_{index}"
        arg_to_id[argument] = arg_id
        id_to_arg[arg_id] = argument

    framework = ArgumentationFramework(
        arguments=frozenset(arg_to_id.values()),
        defeats=frozenset(
            (arg_to_id[attacker], arg_to_id[target])
            for attacker, target in defeat_pairs
            if attacker in arg_to_id and target in arg_to_id
        ),
        attacks=frozenset(
            (arg_to_id[attack.attacker], arg_to_id[attack.target])
            for attack in attacks
            if attack.attacker in arg_to_id and attack.target in arg_to_id
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
    "build_bridge_csaf",
]
