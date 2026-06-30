"""The canonical compilation context (PLAN-mandated coverage).

CompilationContext bundles the symbol tables the semantic passes resolve
against. These tests pin its builders for the flat tree: from already-loaded
concepts, from a repository, and the small index helpers.
"""

from __future__ import annotations

from pathlib import Path

from propstore.compiler.context import (
    build_authored_concept_registry,
    build_compilation_context_from_loaded,
    build_compilation_context_from_repo,
    build_compiler_claim_index,
)
from propstore.families.claims import Claim
from propstore.families.concepts import Concept
from propstore.families.concepts_passes import LoadedConcept
from propstore.families.forms import FormDefinition
from propstore.repository import Repository
from condition_ir import KindType


def test_claim_index_keyed_by_claim_id() -> None:
    claims = [Claim(claim_id="a"), Claim(claim_id="b")]
    index = build_compiler_claim_index(claims)
    assert set(index) == {"a", "b"}
    assert index["a"].claim_id == "a"


def test_authored_concept_registry_keyed_by_concept_id() -> None:
    concepts = [Concept(concept_id="c1", canonical_name="C1")]
    registry = build_authored_concept_registry(concepts)
    assert set(registry) == {"c1"}


def test_context_from_loaded_populates_tables() -> None:
    concepts = [LoadedConcept(concept=Concept(concept_id="freq", canonical_name="frequency"))]
    forms = {"mass": FormDefinition(name="mass", kind=KindType.QUANTITY, dimensions={"mass": 1})}
    claims = [Claim(claim_id="c1")]
    context = build_compilation_context_from_loaded(
        concepts, form_registry=forms, claims=claims, context_ids={"ctx1"}
    )
    assert "freq" in context.concepts_by_id
    assert "freq" in context.cel_registry
    assert "c1" in context.claim_index
    assert context.context_ids == frozenset({"ctx1"})
    assert "mass" in context.form_registry


def test_context_from_repo_reads_concepts_and_forms(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path)
    repo.families.concept.save(
        "freq", Concept(concept_id="freq", canonical_name="frequency"), message="m"
    )
    repo.families.form.save(
        "mass",
        FormDefinition(name="mass", kind=KindType.QUANTITY, dimensions={"mass": 1}),
        message="m",
    )
    context = build_compilation_context_from_repo(repo)
    assert "freq" in context.concepts_by_id
    assert "mass" in context.form_registry
    assert "freq" in context.cel_registry


def test_context_from_repo_none_is_empty() -> None:
    context = build_compilation_context_from_repo(None)
    assert context.concepts_by_id == {}
    assert context.claim_index == {}
