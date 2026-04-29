from __future__ import annotations

from argumentation.aspic import (
    ContrarinessFn,
    GroundAtom,
    Literal,
    Rule,
    contraries_of,
    transposition_closure,
)


def test_workstream_f_upstream_aspic_public_api_is_behavioral_not_sha_based() -> None:
    """WS-F sentinel: Modgil 2014 Def. 4.3 / Theorem 1, pp. 19-20."""

    p = Literal(atom=GroundAtom("p"), negated=False)
    q = Literal(atom=GroundAtom("q"), negated=False)
    not_p = p.contrary
    not_q = q.contrary
    contrariness = ContrarinessFn(frozenset({(p, q), (not_q, not_p)}))
    strict_rule = Rule(antecedents=(p,), consequent=not_q, kind="strict")

    closed_rules, post_closure_language = transposition_closure(
        frozenset({strict_rule}),
        frozenset({p, q, not_p, not_q}),
        contrariness,
    )

    assert contraries_of(p, contrariness, post_closure_language) == frozenset({q})
    assert strict_rule in closed_rules
    assert Rule(antecedents=(not_p,), consequent=q, kind="strict") in closed_rules
    assert {p, q, not_p, not_q}.issubset(post_closure_language)
