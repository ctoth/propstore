"""Grounded facts are projected into the world sidecar by the build (9-0-rest-B).

The raw ``grounded_fact`` table round-trip is pinned in
``test_sidecar_grounded_facts``; this pins the *build wiring*: a repo with authored
predicates, rules, and a matching claim grounds into ``grounded_fact`` rows in the
materialized world sidecar (the GUNRAY-unblock dependency).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


from propstore.compiler.workflows import build_repository
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.families.predicates import Predicate
from propstore.families.rules import Atom, BodyLiteral, DefeasibleRule, Term
from propstore.repository import Repository


def _section_atoms(path: str, section: str) -> set[tuple[str, tuple[str, ...]]]:
    conn = sqlite3.connect(path)
    try:
        rows = conn.execute(
            "SELECT predicate, arguments FROM grounded_fact WHERE section = ?",
            (section,),
        ).fetchall()
    finally:
        conn.close()
    return {(str(p), tuple(json.loads(a))) for p, a in rows}


def test_empty_repo_grounds_no_facts(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "kn")
    repo.families.concept.save(
        "c1", Concept(concept_id="c1", canonical_name="Speed"), message="m"
    )
    report = build_repository(repo)
    assert report.derived_store is not None
    conn = sqlite3.connect(report.derived_store.path)
    try:
        assert conn.execute("SELECT count(*) FROM grounded_fact").fetchone() == (0,)
    finally:
        conn.close()


def test_authored_rules_ground_facts_into_sidecar(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "kn")
    repo.families.concept.save(
        "c1", Concept(concept_id="c1", canonical_name="Speed"), message="m"
    )
    repo.families.context.save(
        "ctx1", Context(context_id="ctx1", name="ctx"), message="m"
    )
    repo.families.claim.save(
        "cl1",
        Claim(
            claim_id="cl1",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            value=1.0,
        ),
        message="m",
    )
    repo.families.predicate.save(
        "has_value",
        Predicate(
            predicate_id="has_value",
            arity=1,
            arg_types=("Claim",),
            derived_from="claim.attribute:value",
        ),
        message="m",
    )
    repo.families.predicate.save(
        "important",
        Predicate(predicate_id="important", arity=1, arg_types=("Claim",)),
        message="m",
    )
    repo.families.defeasible_rule.save(
        "r1",
        DefeasibleRule(
            rule_id="r1",
            kind="defeasible",
            head=Atom(predicate="important", terms=(Term(kind="var", name="X"),)),
            body=(
                BodyLiteral(
                    kind="positive",
                    atom=Atom(
                        predicate="has_value", terms=(Term(kind="var", name="X"),)
                    ),
                ),
            ),
        ),
        message="m",
    )

    report = build_repository(repo)
    assert report.derived_store is not None
    yes = _section_atoms(report.derived_store.path, "yes")
    assert ("has_value", ("cl1",)) in yes
    assert ("important", ("cl1",)) in yes
