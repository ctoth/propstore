"""Predicate declaration charters and generated document types."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Literal

import msgspec
from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import CharterField, FamilyCharter, FamilyModel
from quire.families import FamilyDefinition
from quire.lifecycle import ConflictPolicy, FamilyState, FamilyTransition
from quire.versions import VersionId


PredicateArgType = Literal["paper_id", "int", "float", "str", "bool"] | str
_BASE_ARG_TYPES = frozenset({"paper_id", "int", "float", "str", "bool"})
_ENUM_TYPE_RE = re.compile(r"^enum:[A-Za-z0-9_-]+(\|[A-Za-z0-9_-]+)+$")

PREDICATE_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")


def validate_predicate_arg_type(arg_type: str) -> None:
    if arg_type in _BASE_ARG_TYPES:
        return
    if _ENUM_TYPE_RE.match(arg_type):
        return
    raise ValueError(f"unsupported predicate arg type: {arg_type!r}")


def _validate_predicate_arity_and_arg_types(doc: msgspec.Struct) -> None:
    predicate_name = getattr(doc, "id", getattr(doc, "name", "<unknown>"))
    arity = getattr(doc, "arity")
    arg_types = tuple(getattr(doc, "arg_types"))
    if arity < 0:
        raise ValueError("predicate arity must be >= 0")
    if arg_types and len(arg_types) != arity:
        raise ValueError(
            f"predicate {predicate_name!r}: arg_types length {len(arg_types)} "
            f"does not match arity {arity}"
        )
    if hasattr(doc, "name"):
        for arg_type in arg_types:
            validate_predicate_arg_type(str(arg_type))


class PredicateDeclarationModel(FamilyModel):
    pass


class PredicateProposalDeclarationModel(FamilyModel):
    pass


PREDICATE_DECLARATION_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="predicate_declaration",
        name="predicate_declaration",
        contract_version=PREDICATE_FAMILY_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-predicate_declaration",
            contract_version=PREDICATE_FAMILY_CONTRACT_VERSION,
            doc_type=PredicateDeclarationModel,
            placement=FlatYamlPlacement(".derived/predicate_declaration", str),
        ),
        identity_field="id",
    ),
    model=PredicateDeclarationModel,
    fields=(
        CharterField("id", str, primary_key=True, nullable=False),
        CharterField("arity", int, nullable=False),
        CharterField(
            "arg_types",
            tuple[str, ...],
            parse_boundary="json",
            nullable=False,
            default=(),
            default_sql="'[]'",
        ),
        CharterField("derived_from", str, nullable=True),
        CharterField("description", str, nullable=True),
        CharterField("authoring_group", str, nullable=True),
        CharterField("promoted_from_sha", str, nullable=True),
    ),
    semantic_metadata={"semantic": "propstore.world"},
    validators=(_validate_predicate_arity_and_arg_types,),
)


PREDICATE_PROPOSAL_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="predicate_proposal",
        name="predicate_proposal",
        contract_version=PREDICATE_FAMILY_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-predicate_proposal",
            contract_version=PREDICATE_FAMILY_CONTRACT_VERSION,
            doc_type=PredicateProposalDeclarationModel,
            placement=FlatYamlPlacement(".derived/predicate_proposal", str),
        ),
        identity_field="name",
    ),
    model=PredicateProposalDeclarationModel,
    fields=(
        CharterField("name", str, primary_key=True, nullable=False),
        CharterField("arity", int, nullable=False),
        CharterField("description", str, nullable=False),
        CharterField(
            "arg_types",
            tuple[PredicateArgType, ...],
            parse_boundary="json",
            nullable=False,
            default=(),
            default_sql="'[]'",
        ),
    ),
    semantic_metadata={"semantic": "propstore.world"},
    validators=(_validate_predicate_arity_and_arg_types,),
    states=(
        FamilyState("proposed", document_label="proposal"),
        FamilyState("canonical", document_label="canonical", terminal=True),
    ),
    transitions=(
        FamilyTransition(
            "promote_proposal",
            source="proposed",
            target="canonical",
            materializer="predicate_proposal_to_canonical",
            conflict_policy=ConflictPolicy.REPLACE,
        ),
    ),
)


class PredicateExtractionProvenance(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    """Prompt and source provenance for proposed predicate declarations."""

    operations: tuple[str, ...]
    agent: str
    model: str
    prompt_sha: str
    notes_sha: str
    status: str


if TYPE_CHECKING:

    class PredicateDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
        id: str
        arity: int
        arg_types: tuple[str, ...] = ()
        derived_from: str | None = None
        description: str | None = None
        authoring_group: str | None = None
        promoted_from_sha: str | None = None

    class PredicateDeclaration(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
        name: str
        arity: int
        description: str
        arg_types: tuple[PredicateArgType, ...] = ()

else:
    PredicateDocument: Any = PREDICATE_DECLARATION_CHARTER.generated_document()
    PredicateDocument.__name__ = "PredicateDocument"
    PredicateDocument.__qualname__ = "PredicateDocument"
    PredicateDocument.__module__ = __name__

    PredicateDeclaration: Any = PREDICATE_PROPOSAL_CHARTER.generated_document()
    PredicateDeclaration.__name__ = "PredicateDeclaration"
    PredicateDeclaration.__qualname__ = "PredicateDeclaration"
    PredicateDeclaration.__module__ = __name__


class PredicateProposalDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    """Proposal-branch payload for a paper's predicate vocabulary."""

    source_paper: str
    proposed_declarations: tuple[PredicateDeclaration, ...]
    extraction_provenance: PredicateExtractionProvenance
    extraction_date: str
    promoted_from_sha: str | None = None


PREDICATE_CHARTERS: tuple[FamilyCharter, ...] = (
    PREDICATE_DECLARATION_CHARTER,
    PREDICATE_PROPOSAL_CHARTER,
)
