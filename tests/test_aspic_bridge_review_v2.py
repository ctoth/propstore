from __future__ import annotations

import pytest

from propstore.aspic import GroundAtom
from propstore.aspic_bridge import (
    _canonical_substitution_key,
    _literal_for_atom,
    _parse_ground_atom_key,
    build_bridge_csaf,
    claims_to_literals,
    grounded_rules_to_rules,
    justifications_to_rules,
    query_claim,
    stances_to_contrariness,
)
from propstore.core.justifications import CanonicalJustification
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
    from propstore.rule_documents import TermDocument

    return TermDocument(kind="var", name=name, value=None)


def _make_atom(predicate: str, terms=()):
    from propstore.rule_documents import AtomDocument

    return AtomDocument(predicate=predicate, terms=tuple(terms), negated=False)


def _make_rule_document(
    rule_id: str,
    head,
    body=(),
):
    from propstore.rule_documents import RuleDocument

    return RuleDocument(
        id=rule_id,
        kind="defeasible",
        head=head,
        body=tuple(body),
        negative_body=(),
    )


def _make_rule_file(rules):
    from propstore.loaded import LoadedDocument
    from propstore.rule_documents import (
        LoadedRuleFile,
        RuleSourceDocument,
        RulesFileDocument,
    )

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


def _make_grounded_bundle(rules=(), *, definitely=None, defeasibly=None):
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

    return GroundedRulesBundle(
        source_rules=(
            ()
            if not rules
            else (_make_rule_file(rules),)
        ),
        source_facts=(),
        sections=MappingProxyType(
            {
                "definitely": _freeze(definitely),
                "defeasibly": _freeze(defeasibly),
                "not_defeasibly": MappingProxyType({}),
                "undecided": MappingProxyType({}),
            }
        ),
    )


def test_literal_for_atom_does_not_alias_opposite_polarities() -> None:
    literals: dict[str, object] = {}

    positive = _literal_for_atom(GroundAtom("p", (1,)), False, literals)  # type: ignore[arg-type]
    negative = _literal_for_atom(GroundAtom("p", (1,)), True, literals)  # type: ignore[arg-type]

    assert positive is not negative
    assert positive.negated is False
    assert negative.negated is True


def test_ground_literals_do_not_collide_with_claim_id_namespace() -> None:
    literals = claims_to_literals([_make_claim("bird(tweety)")])

    claim_literal = literals["bird(tweety)"]
    ground_literal = _literal_for_atom(
        GroundAtom("bird", ("tweety",)),
        False,
        literals,
    )

    assert claim_literal is not ground_literal
    assert claim_literal.atom.arguments == ()
    assert ground_literal.atom.arguments == ("tweety",)


def test_parse_ground_atom_key_round_trips_quoted_strings_and_numeric_scalars() -> None:
    parsed = _parse_ground_atom_key('p("a,b", 1, true, "1")')

    assert parsed == GroundAtom("p", ("a,b", 1, True, "1"))


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
    literals = {
        "attacker": _literal_for_atom(GroundAtom("attacker", ()), False, {}),
    }
    literals["target"] = _literal_for_atom(
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
        definitely={"bird": {("tweety",)}},
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
    assert cfn.is_contrary(literals["attacker"], grounded_rule_lit)


def test_query_claim_raises_keyerror_for_unknown_goal() -> None:
    with pytest.raises(KeyError, match="missing_goal"):
        query_claim(
            "missing_goal",
            active_claims=[_make_claim("known")],
            justifications=[],
            stances=[],
            bundle=GroundedRulesBundle.empty(),
        )
