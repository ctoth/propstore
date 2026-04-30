from __future__ import annotations

import msgspec.yaml
import pytest
from hypothesis import given
from hypothesis import strategies as st


def test_proposal_predicates_family_is_registered(tmp_path) -> None:
    from propstore.families.registry import (
        PROPOSAL_PREDICATES_FAMILY,
        PredicateProposalRef,
    )
    from propstore.repository import Repository

    repo = Repository.init(tmp_path / "knowledge")
    ref = PredicateProposalRef("Ioannidis_2005_WhyMostPublishedResearch")

    assert repo.families.proposal_predicates.family is PROPOSAL_PREDICATES_FAMILY
    assert repo.families.proposal_predicates.address(ref).require_path() == (
        "predicates/Ioannidis_2005_WhyMostPublishedResearch/declarations.yaml"
    )


def test_predicate_proposal_document_is_typed() -> None:
    from propstore.families.documents.predicates import (
        PredicateDeclaration,
        PredicateExtractionProvenance,
        PredicateProposalDocument,
    )

    declaration = PredicateDeclaration(
        name="sample_size",
        arity=2,
        arg_types=("paper_id", "int"),
        description="Paper-level sample size.",
    )

    document = PredicateProposalDocument(
        source_paper="Ioannidis_2005_WhyMostPublishedResearch",
        proposed_declarations=(declaration,),
        extraction_provenance=PredicateExtractionProvenance(
            operations=("predicate_extraction",),
            agent="codex",
            model="test-model",
            prompt_sha="abc123",
            notes_sha="def456",
            status="CALIBRATED",
        ),
        extraction_date="2026-04-29",
    )

    assert document.source_paper == "Ioannidis_2005_WhyMostPublishedResearch"
    assert document.proposed_declarations[0].arg_types == ("paper_id", "int")


@pytest.mark.parametrize(
    "arg_type",
    ["paper_id", "int", "float", "str", "bool", "enum:hot|warm|cold"],
)
def test_predicate_arg_type_closed_set_accepts_known_tags(arg_type: str) -> None:
    from propstore.families.documents.predicates import PredicateDeclaration

    declaration = PredicateDeclaration(
        name="typed_predicate",
        arity=1,
        arg_types=(arg_type,),
        description="test",
    )

    assert declaration.arg_types == (arg_type,)


def test_predicate_arg_type_closed_set_rejects_unknown_tag() -> None:
    from propstore.families.documents.predicates import PredicateDeclaration

    with pytest.raises(ValueError, match="unsupported predicate arg type"):
        PredicateDeclaration(
            name="bad_predicate",
            arity=1,
            arg_types=("callable",),
            description="test",
        )


@pytest.mark.property
@given(
    name=st.from_regex(r"[a-z_][a-z0-9_]{0,20}", fullmatch=True),
    arg_types=st.lists(
        st.sampled_from(("paper_id", "int", "float", "str", "bool", "enum:hot|warm|cold")),
        min_size=0,
        max_size=4,
    ),
    source_paper=st.from_regex(r"[A-Za-z][A-Za-z0-9_]{0,40}", fullmatch=True),
)
def test_generated_predicate_declaration_roundtrip_preserves_identity_and_provenance(
    name: str,
    arg_types: list[str],
    source_paper: str,
) -> None:
    from propstore.families.documents.predicates import (
        PredicateDeclaration,
        PredicateExtractionProvenance,
        PredicateProposalDocument,
    )

    proposal = PredicateProposalDocument(
        source_paper=source_paper,
        proposed_declarations=(
            PredicateDeclaration(
                name=name,
                arity=len(arg_types),
                arg_types=tuple(arg_types),
                description="generated declaration",
            ),
        ),
        extraction_provenance=PredicateExtractionProvenance(
            operations=("predicate_extraction",),
            agent="property-test",
            model="generated",
            prompt_sha="prompt-sha",
            notes_sha="notes-sha",
            status="CALIBRATED",
        ),
        extraction_date="2026-04-29",
    )

    decoded = msgspec.yaml.decode(
        msgspec.yaml.encode(proposal),
        type=PredicateProposalDocument,
        strict=True,
    )

    declaration = decoded.proposed_declarations[0]
    assert decoded.source_paper == source_paper
    assert decoded.extraction_provenance.notes_sha == "notes-sha"
    assert declaration.name == name
    assert declaration.arity == len(arg_types)
    assert declaration.arg_types == tuple(arg_types)
