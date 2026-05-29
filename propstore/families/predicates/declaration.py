"""Predicate declaration charters and generated document types."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Annotated, Literal

import msgspec
from quire.charter_class import CharterDoc, charter, charter_field
from quire.charters import FamilyCharter, FamilyModel
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


def _validate_predicate_proposal_artifact(doc: msgspec.Struct) -> None:
    for declaration in getattr(doc, "proposed_declarations"):
        _validate_predicate_arity_and_arg_types(declaration)


if TYPE_CHECKING:
    # ``@charter`` generates these SQLAlchemy-mappable models at runtime (via
    # ``model_name=``) and binds them into this module's namespace; the static
    # stubs let this module and external importers type-check model construction
    # and attribute access while the runtime classes replace them.
    class PredicateDeclarationModel(FamilyModel): ...

    class PredicateProposalArtifactModel(FamilyModel): ...


class PredicateDeclaration(CharterDoc, kw_only=True):
    name: str
    arity: int
    description: str
    arg_types: tuple[PredicateArgType, ...] = ()

    def __post_init__(self) -> None:
        _validate_predicate_arity_and_arg_types(self)


class PredicateExtractionProvenance(CharterDoc, kw_only=True):
    """Prompt and source provenance for proposed predicate declarations."""

    operations: tuple[str, ...]
    agent: str
    model: str
    prompt_sha: str
    notes_sha: str
    status: str


@charter(
    key="predicate_declaration",
    name="predicate_declaration",
    contract_version=PREDICATE_FAMILY_CONTRACT_VERSION,
    placement=".derived/predicate_declaration",
    identity_field="id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-predicate_declaration",
    model_name="PredicateDeclarationModel",
    validators=(_validate_predicate_arity_and_arg_types,),
)
class PredicateDocument(CharterDoc, kw_only=True):
    id: Annotated[str, charter_field(primary_key=True)]
    arity: int
    arg_types: Annotated[
        tuple[str, ...], charter_field(json=True, default_sql="'[]'")
    ] = ()
    derived_from: str | None = None
    description: str | None = None
    authoring_group: str | None = None
    promoted_from_sha: str | None = None


@charter(
    key="predicate_proposal",
    name="predicate_proposal",
    contract_version=PREDICATE_FAMILY_CONTRACT_VERSION,
    placement=".derived/predicate_proposal",
    identity_field="source_paper",
    semantic="propstore.world",
    artifact_family_name="propstore-world-predicate_proposal",
    model_name="PredicateProposalArtifactModel",
    validators=(_validate_predicate_proposal_artifact,),
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
class PredicateProposalArtifact(CharterDoc, kw_only=True):
    source_paper: Annotated[str, charter_field(primary_key=True)]
    proposed_declarations: Annotated[
        tuple[PredicateDeclaration, ...], charter_field(json=True)
    ]
    extraction_provenance: Annotated[
        PredicateExtractionProvenance, charter_field(json=True)
    ]
    extraction_date: str
    promoted_from_sha: str | None = None


PREDICATE_DECLARATION_CHARTER: FamilyCharter = PredicateDocument.__charter__
PREDICATE_PROPOSAL_CHARTER: FamilyCharter = PredicateProposalArtifact.__charter__

PREDICATE_CHARTERS: tuple[FamilyCharter, ...] = (
    PREDICATE_DECLARATION_CHARTER,
    PREDICATE_PROPOSAL_CHARTER,
)
