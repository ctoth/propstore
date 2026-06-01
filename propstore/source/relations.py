from __future__ import annotations


_ALLOWED_JUSTIFICATION_RULE_KINDS = frozenset(
    {
        "causal_explanation",
        "comparison_based_inference",
        "definition_application",
        "empirical_support",
        "explains",
        "methodological_inference",
        "reported_claim",
        "scope_limitation",
        "statistical_inference",
        "supports",
    }
)
_ALLOWED_JUSTIFICATION_RULE_STRENGTHS = frozenset(
    {
        "strict",
        "defeasible",
    }
)


def _validate_justification_rule_fields(
    *,
    rule_kind: str | None,
    rule_strength: str | None,
) -> None:
    if rule_kind not in _ALLOWED_JUSTIFICATION_RULE_KINDS:
        allowed = ", ".join(sorted(_ALLOWED_JUSTIFICATION_RULE_KINDS))
        raise ValueError(f"rule_kind must be one of: {allowed}")
    if (
        rule_strength is not None
        and rule_strength not in _ALLOWED_JUSTIFICATION_RULE_STRENGTHS
    ):
        allowed = ", ".join(sorted(_ALLOWED_JUSTIFICATION_RULE_STRENGTHS))
        raise ValueError(f"rule_strength must be one of: {allowed}")
