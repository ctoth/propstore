from __future__ import annotations

import pytest

from argumentation.aspic import GroundAtom, Literal
from argumentation.aspic import conc
from propstore.aspic_bridge import (
    build_bridge_csaf,
    csaf_to_projection,
    claims_to_literals,
    grounded_rules_to_rules,
    justifications_to_rules,
    query_claim,
    stances_to_contrariness,
)
from propstore.aspic_bridge.grounding import (
    _canonical_substitution_key,
    _literal_for_atom,
)
from propstore.core.justifications import CanonicalJustification
from propstore.core.literal_keys import LiteralKey, claim_key
from propstore.grounding.bundle import GroundedRulesBundle


def _make_claim(claim_id: str) -> dict[str, object]:
    return {
        "id": claim_id,
        "concept_id": f"concept_{claim_id}",
        "statement": f"Claim {claim_id}",
        "premise_kind": "ordinary",
    }


def _make_justification(
    justification_id: str,
    conclusion_claim_id: str,
    premise_claim_ids: tuple[str, ...] = (),
    *,
    rule_kind: str = "supports",
    rule_strength: str = "defeasible",
) -> CanonicalJustification:
    return CanonicalJustification(
        justification_id=justification_id,
        conclusion_claim_id=conclusion_claim_id,
        premise_claim_ids=premise_claim_ids,
        rule_kind=rule_kind,
        rule_strength=rule_strength,
    )


def _make_var(name: str):
    from propstore.families.documents.rules import TermDocument

    return TermDocument(kind="var", name=name, value=None)


def _make_atom(predicate: str, terms=(), *, negated: bool = False):
    from propstore.families.documents.rules import AtomDocument

    return AtomDocument(predicate=predicate, terms=tuple(terms), negated=negated)


def _make_rule_document(
    rule_id: str,
    head,
    body=(),
):
    from propstore.families.documents.rules import BodyLiteralDocument, RuleDocument

    return RuleDocument(
        id=rule_id,
        kind="defeasible",
        head=head,
        body=tuple(
            BodyLiteralDocument(kind="positive", atom=atom)
            for atom in body
        ),
    )


def _make_rule_file(rules):
    from quire.documents import LoadedDocument
    from propstore.families.documents.rules import RuleSourceDocument, RulesFileDocument
    from propstore.rule_files import LoadedRuleFile

    loaded = LoadedDocument(
        filename="generated.yaml",
        source_path=None,
        knowledge_root=None,
        document=RulesFileDocument(
            source=RuleSourceDocument(paper="review_v2"),
            rules=tuple(rules),
        ),
    )
    return LoadedRuleFile.from_loaded_document(loaded)


def _make_grounded_bundle(rules=(), *, yes=None):
    from types import MappingProxyType

    def _freeze(section):
        if section is None:
            return MappingProxyType({})
        return MappingProxyType(
            {
                predicate: frozenset(rows)
                for predicate, rows in section.items()
            }
        )

    source_facts = tuple(
        GroundAtom(predicate, tuple(row))
        for predicate, rows in (yes or {}).items()
        for row in rows
    )

    return GroundedRulesBundle(
        source_rules=(
            ()
            if not rules
            else (_make_rule_file(rules),)
        ),
        source_facts=source_facts,
        sections=MappingProxyType(
            {
                "yes": _freeze(yes),
                "no": MappingProxyType({}),
                "undecided": MappingProxyType({}),
                "unknown": MappingProxyType({}),
            }
        ),
    )


def test_literal_for_atom_does_not_alias_opposite_polarities() -> None:
    literals: dict[LiteralKey, Literal] = {}

    positive = _literal_for_atom(GroundAtom("p", (1,)), False, literals)  # type: ignore[arg-type]
    negative = _literal_for_atom(GroundAtom("p", (1,)), True, literals)  # type: ignore[arg-type]

    assert positive is not negative
    assert positive.negated is False
    assert negative.negated is True


def test_ground_literals_do_not_collide_with_claim_id_namespace() -> None:
    literals = claims_to_literals([_make_claim("bird(tweety)")])

    claim_literal = literals[claim_key("bird(tweety)")]
    ground_literal = _literal_for_atom(
        GroundAtom("bird", ("tweety",)),
        False,
        literals,
    )

    assert claim_literal is not ground_literal
    assert claim_literal.atom.arguments == ()
    assert ground_literal.atom.arguments == ("tweety",)


def test_query_claim_accepts_ground_atom_goal_without_string_recovery() -> None:
    bundle = _make_grounded_bundle(
        rules=(
            _make_rule_document(
                "r1",
                _make_atom("flies", (_make_var("X"),)),
                (_make_atom("bird", (_make_var("X"),)),),
            ),
        ),
        yes={"bird": {("tweety",)}},
    )

    result = query_claim(
        GroundAtom("flies", ("tweety",)),
        active_claims=[],
        justifications=[],
        stances=[],
        bundle=bundle,
    )

    assert result.goal == _literal_for_atom(
        GroundAtom("flies", ("tweety",)),
        False,
        {},
    )
    assert result.arguments_for


def test_query_claim_treats_strongly_negated_fact_as_argument_against_ground_goal() -> None:
    bundle = _make_grounded_bundle(
        rules=(
            _make_rule_document(
                "r1",
                _make_atom("fly", (_make_var("X"),)),
                (_make_atom("bird", (_make_var("X"),)),),
            ),
        ),
        yes={
            "bird": {("tweety",)},
            "~fly": {("tweety",)},
        },
    )

    result = query_claim(
        GroundAtom("fly", ("tweety",)),
        active_claims=[],
        justifications=[],
        stances=[],
        bundle=bundle,
    )

    assert result.arguments_for
    against_conclusions = {conc(arg) for arg in result.arguments_against}
    assert Literal(atom=GroundAtom("fly", ("tweety",)), negated=True) in against_conclusions


def test_query_claim_matches_strongly_negated_body_atoms_from_bundle_sections() -> None:
    bundle = _make_grounded_bundle(
        rules=(
            _make_rule_document(
                "r1",
                _make_atom("blocked", (_make_var("X"),)),
                (_make_atom("fly", (_make_var("X"),), negated=True),),
            ),
        ),
        yes={
            "~fly": {("tweety",)},
        },
    )

    result = query_claim(
        GroundAtom("blocked", ("tweety",)),
        active_claims=[],
        justifications=[],
        stances=[],
        bundle=bundle,
    )

    conclusions_for = {conc(arg) for arg in result.arguments_for}
    assert Literal(atom=GroundAtom("blocked", ("tweety",)), negated=False) in conclusions_for


def test_canonical_substitution_key_distinguishes_delimiter_collisions() -> None:
    left = _canonical_substitution_key({"X": "a,Y=b", "Y": "c"})
    right = _canonical_substitution_key({"X": "a", "Y": "b,Y=c"})

    assert left != right


def test_query_claim_does_not_misclassify_supporting_subarguments_as_against() -> None:
    claims = [_make_claim("p"), _make_claim("q")]
    justifications = [
        _make_justification("reported:p", "p", rule_kind="reported_claim"),
        _make_justification("reported:q", "q", rule_kind="reported_claim"),
        _make_justification("supports:p->q", "q", ("p",)),
    ]

    result = query_claim(
        "q",
        active_claims=claims,
        justifications=justifications,
        stances=[],
        bundle=GroundedRulesBundle.empty(),
    )

    assert result.arguments_for
    assert result.arguments_against == frozenset()


def test_query_claim_arguments_against_excludes_counter_attackers() -> None:
    claims = [_make_claim("p"), _make_claim("q"), _make_claim("r")]
    justifications = [
        _make_justification("reported:p", "p", rule_kind="reported_claim"),
        _make_justification("reported:q", "q", rule_kind="reported_claim"),
        _make_justification("reported:r", "r", rule_kind="reported_claim"),
    ]
    stances = [
        {"claim_id": "q", "target_claim_id": "p", "stance_type": "rebuts"},
        {"claim_id": "r", "target_claim_id": "q", "stance_type": "rebuts"},
    ]

    result = query_claim(
        "p",
        active_claims=claims,
        justifications=justifications,
        stances=stances,
        bundle=GroundedRulesBundle.empty(),
    )

    against_conclusions = {conc(arg) for arg in result.arguments_against}
    assert against_conclusions == {claims_to_literals(claims)[claim_key("q")]}


def test_build_bridge_csaf_populates_framework_attacks() -> None:
    claims = [_make_claim("a"), _make_claim("b")]
    justifications = [
        _make_justification("reported:a", "a", rule_kind="reported_claim"),
        _make_justification("reported:b", "b", rule_kind="reported_claim"),
    ]
    stances = [
        {"claim_id": "a", "target_claim_id": "b", "stance_type": "rebuts"},
    ]

    csaf = build_bridge_csaf(
        claims,
        justifications,
        stances,
        bundle=GroundedRulesBundle.empty(),
    )

    assert csaf.attacks
    assert csaf.framework.attacks is not None


def test_csaf_to_projection_keeps_grounded_arguments_and_subarguments() -> None:
    bundle = _make_grounded_bundle(
        rules=(
            _make_rule_document(
                "r1",
                _make_atom("fly", (_make_var("X"),)),
                (_make_atom("bird", (_make_var("X"),)),),
            ),
        ),
        yes={"bird": {("tweety",)}},
    )

    csaf = build_bridge_csaf(
        [],
        [],
        [],
        bundle=bundle,
    )
    projection = csaf_to_projection(csaf, [])

    assert projection.arguments
    assert projection.claim_to_argument_ids == {}
    assert projection.argument_to_claim_id == {}

    projected_ids = {argument.arg_id for argument in projection.arguments}
    assert projection.framework.arguments == frozenset(projected_ids)
    assert any(argument.claim_id is None for argument in projection.arguments)
    assert any(argument.projection.backend_atom == GroundAtom("fly", ("tweety",)) for argument in projection.arguments)
    assert any(argument.projection.backend_atom == GroundAtom("bird", ("tweety",)) for argument in projection.arguments)
    for argument in projection.arguments:
        assert set(argument.subargument_ids) <= projected_ids


def test_stances_to_contrariness_includes_classical_claim_contradictories() -> None:
    """Claim literals must keep their base contradictory partners in the bridge.

    Prakken 2010, Def. 5.1 (p. 141; local page image
    ``papers/Prakken_2010_AbstractFrameworkArgumentationStructured/pngs/page-012.png``)
    defines transposition over the argumentation system's ``-`` operator. For
    claim literals, the bridge must therefore publish the classical
    contradictory pairs explicitly instead of leaving ``ContrarinessFn`` empty
    unless an attack stance happens to mention the claim.
    """

    claims = [_make_claim("a"), _make_claim("b")]
    literals = claims_to_literals(claims)

    cfn = stances_to_contrariness([], literals, frozenset())

    for literal in literals.values():
        assert cfn.is_contradictory(literal, literal.contrary)


def test_justifications_to_rules_rejects_empty_premise_non_reported_rule() -> None:
    literals = claims_to_literals([_make_claim("q")])
    justifications = [
        _make_justification(
            "supports:empty->q",
            "q",
            (),
            rule_kind="supports",
            rule_strength="defeasible",
        )
    ]

    with pytest.raises(ValueError, match="empty-premise"):
        justifications_to_rules(justifications, literals)


def test_undercut_target_justification_id_matches_grounded_rule_base_id() -> None:
    literals: dict[LiteralKey, Literal] = {
        claim_key("attacker"): _literal_for_atom(GroundAtom("attacker", ()), False, {}),
    }
    literals[claim_key("target")] = _literal_for_atom(
        GroundAtom("flies", ("tweety",)),
        False,
        literals,
    )
    bundle = _make_grounded_bundle(
        rules=(
            _make_rule_document(
                "r1",
                _make_atom("flies", (_make_var("X"),)),
                (_make_atom("bird", (_make_var("X"),)),),
            ),
        ),
        yes={"bird": {("tweety",)}},
    )
    _strict, defeasible, literals = grounded_rules_to_rules(bundle, literals)

    cfn = stances_to_contrariness(
        [
            {
                "claim_id": "attacker",
                "target_claim_id": "target",
                "stance_type": "undercuts",
                "target_justification_id": "r1",
            }
        ],
        literals,
        defeasible,
    )

    grounded_rule = next(iter(defeasible))
    grounded_rule_lit = _literal_for_atom(
        GroundAtom(grounded_rule.name or "", ()),
        False,
        {},
    )
    assert cfn.is_contrary(literals[claim_key("attacker")], grounded_rule_lit)


def test_query_claim_raises_keyerror_for_unknown_goal() -> None:
    with pytest.raises(KeyError, match="missing_goal"):
        query_claim(
            "missing_goal",
            active_claims=[_make_claim("known")],
            justifications=[],
            stances=[],
            bundle=GroundedRulesBundle.empty(),
        )
