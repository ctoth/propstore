"""Explicit checked-form evidence for repository scalar-parameter fixtures."""

from condition_ir import KindType

from propstore.core.lemon import LexicalEntry, LexicalForm, LexicalSense, OntologyReference
from propstore.families.concepts import Concept
from propstore.families.forms import FormDefinition
from propstore.repository import Repository


def save_dimensionless_concept(repo: Repository, concept_id: str, name: str) -> None:
    repo.families.form.save(
        "ratio", FormDefinition(name="ratio", kind=KindType.QUANTITY, is_dimensionless=True),
        message="Declare dimensionless quantity",
    )
    repo.families.concept.save(
        concept_id, Concept(
            concept_id=concept_id, canonical_name=name,
            lexical_entry=LexicalEntry(
                identifier=f"entry:{concept_id}",
                canonical_form=LexicalForm(written_rep=name, language="en"),
                senses=(LexicalSense(reference=OntologyReference(uri=f"urn:{concept_id}")),),
                physical_dimension_form="ratio",
            ),
        ), message="Declare scalar concept",
    )
