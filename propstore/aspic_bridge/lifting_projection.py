"""Project typed context-lifting decisions into ASPIC+ rules.

A ``LIFTED`` decision licenses carrying a proposition from its source context to
a target context: a ``BRIDGE`` lift is a strict rule, other modes are defeasible.
``BLOCKED`` / ``UNKNOWN`` decisions contribute no rule but are still recorded, so
a blocked lift remains visible (CLAUDE.md non-commitment) rather than vanishing.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from argumentation.structured.aspic.aspic import GroundAtom, Literal, Rule

from propstore.context_lifting import LiftingDecision, LiftingDecisionStatus, LiftingMode
from propstore.core.id_types import to_claim_id, to_context_id
from propstore.core.literal_keys import IstLiteralKey, LiteralKey


@dataclass(frozen=True)
class LiftingProjectionRecord:
    """One lifting decision as projected into the bridge."""

    source_context_id: str
    target_context_id: str
    proposition_id: str
    rule_id: str
    status: LiftingDecisionStatus
    mode: LiftingMode
    source_literal: Literal
    target_literal: Literal


@dataclass(frozen=True)
class LiftingProjection:
    """The literals and rules contributed by a set of lifting decisions."""

    literals: dict[LiteralKey, Literal]
    strict_rules: frozenset[Rule]
    defeasible_rules: frozenset[Rule]
    records: tuple[LiftingProjectionRecord, ...]


def _literal_for_key(key: IstLiteralKey) -> Literal:
    return Literal(
        atom=GroundAtom("ist", (str(key.context_id), str(key.proposition_id))),
        negated=False,
    )


def project_lifting_decisions(
    literals: Mapping[LiteralKey, Literal],
    decisions: Sequence[LiftingDecision],
) -> LiftingProjection:
    """Project context-lifting decisions into ASPIC+ literals and rules."""

    projected_literals = dict(literals)
    strict_rules: set[Rule] = set()
    defeasible_rules: set[Rule] = set()
    records: list[LiftingProjectionRecord] = []

    for decision in decisions:
        source_key = IstLiteralKey(
            to_context_id(decision.source_context),
            to_claim_id(decision.proposition_id),
        )
        target_key = IstLiteralKey(
            to_context_id(decision.target_context),
            to_claim_id(decision.proposition_id),
        )
        source_literal = projected_literals.setdefault(source_key, _literal_for_key(source_key))
        target_literal = projected_literals.setdefault(target_key, _literal_for_key(target_key))
        records.append(
            LiftingProjectionRecord(
                source_context_id=str(decision.source_context),
                target_context_id=str(decision.target_context),
                proposition_id=decision.proposition_id,
                rule_id=decision.rule_id,
                status=decision.status,
                mode=decision.mode,
                source_literal=source_literal,
                target_literal=target_literal,
            )
        )
        if decision.status is not LiftingDecisionStatus.LIFTED:
            continue
        rule = Rule(
            antecedents=(source_literal,),
            consequent=target_literal,
            kind="strict" if decision.mode is LiftingMode.BRIDGE else "defeasible",
            name=decision.rule_id,
        )
        if rule.kind == "strict":
            strict_rules.add(rule)
        else:
            defeasible_rules.add(rule)

    return LiftingProjection(
        literals=projected_literals,
        strict_rules=frozenset(strict_rules),
        defeasible_rules=frozenset(defeasible_rules),
        records=tuple(records),
    )


__all__ = ["LiftingProjection", "LiftingProjectionRecord", "project_lifting_decisions"]
