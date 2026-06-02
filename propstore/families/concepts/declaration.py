"""Concept family projection, row, and derived-query declaration."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Any, cast

import json
import msgspec
from quire.charter_class import CharterDoc, charter, charter_field
from quire.charters import (
    CharterFtsIndex,
    CharterIndex,
    CharterVectorCache,
    FamilyCharter,
    FamilyModel,
)
from quire.documents import DocumentBatchSpec
from quire.references import ForeignKeySpec, ReferenceKey
from quire.versions import VersionId

from propstore.cel_types import CelExpr, to_cel_exprs
from propstore.core.exactness_types import Exactness
from propstore.core.id_types import ConceptId
from propstore.core.lemon.description_kinds import DescriptionKind
from propstore.core.lemon.proto_roles import ProtoRoleBundle
from propstore.core.lemon.qualia import QualiaStructure
from propstore.families.conditions.declaration import CheckedConditionSetDocument
from propstore.families.forms.stages import (
    Form,
    FormAlgebra,
)
from propstore.families.concepts.types import ConceptRelationshipType, ConceptStatus
from propstore.provenance import Provenance

if TYPE_CHECKING:
    pass


AUTHORED_CONCEPT_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")
_CONCEPT_WORLD_CONTRACT_VERSION = VersionId("2026.05.20", allow_placeholder=False)
SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION = VersionId("2026.05.21")


# ---------------------------------------------------------------------------
# Embedded Pop-B charter documents (leaf-first lemon chain)
# ---------------------------------------------------------------------------


class OntologyReferenceDocument(CharterDoc, kw_only=True):
    uri: str
    label: str | None = None


class LexicalFormDocument(CharterDoc, kw_only=True):
    written_rep: str
    language: str
    phonetic_rep: str | None = None


class LexicalSenseDocument(CharterDoc, kw_only=True):
    reference: OntologyReferenceDocument
    usage: str | None = None
    provenance: Provenance | None = None
    qualia: QualiaStructure | None = None
    description_kind: DescriptionKind | None = None
    role_bundles: dict[str, ProtoRoleBundle] | None = None


class LexicalEntryDocument(CharterDoc, kw_only=True):
    identifier: str
    canonical_form: LexicalFormDocument
    senses: tuple[LexicalSenseDocument, ...]
    physical_dimension_form: str
    other_forms: tuple[LexicalFormDocument, ...] = ()


class ConceptLogicalIdDocument(CharterDoc, kw_only=True):
    namespace: str
    value: str


class ConceptAliasDocument(CharterDoc, kw_only=True):
    name: str
    source: str | None = None
    note: str | None = None


class ConceptRelationshipDocument(CharterDoc, kw_only=True):
    type: ConceptRelationshipType
    target: str
    source: str | None = None
    conditions: tuple[str, ...] = ()
    note: str | None = None


class ConceptFormParametersDocument(CharterDoc, kw_only=True):
    construction: str | None = None
    extensible: bool | None = None
    note: str | None = None
    reference: str | None = None
    values: tuple[str, ...] | None = None


class ParameterizationRelationshipDocument(CharterDoc, kw_only=True):
    inputs: tuple[str, ...]
    formula: str | None = None
    exactness: Exactness | None = None
    source: str | None = None
    bidirectional: bool | None = None
    sympy: str | None = None
    conditions: tuple[str, ...] = ()
    note: str | None = None
    canonical_claim: str | None = None
    fit_statistics: str | None = None


class ConceptIdScan(msgspec.Struct, kw_only=True, forbid_unknown_fields=False):
    id: str | None = None
    artifact_id: str | None = None
    logical_ids: tuple[ConceptLogicalIdDocument, ...] = ()


# ---------------------------------------------------------------------------
# Row behaviour mixins (generated SQLAlchemy models inherit these)
# ---------------------------------------------------------------------------


class ConceptBehavior(FamilyModel):
    @property
    def concept_id(self) -> ConceptId:
        return ConceptId(cast(str, getattr(self, "id")))

    @property
    def logical_ids(self) -> tuple[Mapping[str, object], ...]:
        if not self.logical_ids_json:
            return ()
        loaded = json.loads(self.logical_ids_json)
        if not isinstance(loaded, list):
            raise ValueError("concept logical_ids_json must decode to a list")
        entries: list[Mapping[str, object]] = []
        for entry in loaded:
            if not isinstance(entry, Mapping):
                raise ValueError("concept logical_ids_json entries must be mappings")
            entries.append(entry)
        return tuple(entries)

    def parsed_logical_ids(self) -> list[dict[str, Any]]:
        logical_ids_json = cast(str | None, getattr(self, "logical_ids_json", None))
        if not logical_ids_json:
            return []
        try:
            loaded = json.loads(logical_ids_json)
        except json.JSONDecodeError:
            return []
        return loaded if isinstance(loaded, list) else []

    def attribute_mapping(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for key in (
            "version_id",
            "content_hash",
            "seq",
            "range_min",
            "range_max",
            "is_dimensionless",
            "unit_symbol",
            "created_date",
            "last_modified",
        ):
            value = getattr(self, key, None)
            if value is not None:
                data[key] = value
        return data

    def attribute_value(self, key: str) -> Any:
        value = getattr(self, key, None)
        if value is not None:
            return value
        return None


class ConceptRelationshipBehavior(FamilyModel):
    @property
    def relationship_type(self) -> str:
        return cast(str, getattr(self, "type"))


class ParameterizationBehavior(FamilyModel):
    @property
    def input_concept_ids(self) -> tuple[str, ...]:
        if not self.concept_ids:
            return ()
        inputs = json.loads(self.concept_ids)
        if not isinstance(inputs, list):
            return ()
        return tuple(str(item) for item in inputs if isinstance(item, str) and item)

    @property
    def condition_expressions(self) -> tuple[CelExpr, ...]:
        if not self.conditions_cel:
            return ()
        conditions = json.loads(self.conditions_cel)
        if not isinstance(conditions, list):
            return ()
        return to_cel_exprs(
            condition
            for condition in conditions
            if isinstance(condition, str) and condition
        )


if TYPE_CHECKING:
    # ``@charter(model_name=...)`` generates these SQLAlchemy-mappable models at
    # runtime and binds them into this module's namespace; the static stubs keep
    # ``from ...concepts.declaration import Concept`` (etc.) type-checking against
    # the models (including their behaviour mixins where present).
    class AuthoredConcept(FamilyModel): ...

    class Concept(ConceptBehavior): ...

    class ConceptAlias(FamilyModel): ...

    class ConceptRelationship(ConceptRelationshipBehavior): ...

    class Parameterization(ParameterizationBehavior): ...

    class ParameterizationGroup(FamilyModel): ...


# ---------------------------------------------------------------------------
# AUTHORED_CONCEPT — the lemon-shaped authored document
# ---------------------------------------------------------------------------


def _validate_lexical_entry_has_sense(document: msgspec.Struct) -> None:
    lexical_entry = getattr(document, "lexical_entry")
    if not lexical_entry.senses:
        raise ValueError("lexical_entry requires at least one sense")


@charter(
    key="authored_concept",
    name="authored_concept",
    contract_version=AUTHORED_CONCEPT_FAMILY_CONTRACT_VERSION,
    placement=".derived/authored_concept",
    identity_field="id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-authored_concept",
    model_name="AuthoredConcept",
    reference_keys=(
        ReferenceKey.field("artifact_id"),
        ReferenceKey.field("logical_ids[].value"),
        ReferenceKey.format("{namespace}:{value}", from_field="logical_ids[]"),
        ReferenceKey.field("aliases[].name"),
    ),
    validators=(_validate_lexical_entry_has_sense,),
)
class ConceptDocument(CharterDoc, kw_only=True):
    status: Annotated[ConceptStatus, charter_field(nullable=False, order=0)]
    ontology_reference: Annotated[
        OntologyReferenceDocument,
        charter_field(json=True, nullable=False, order=1),
    ]
    lexical_entry: Annotated[
        LexicalEntryDocument,
        charter_field(
            json=True,
            nullable=False,
            order=2,
            foreign_key=ForeignKeySpec(
                name="concept_form",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="concepts",
                source_field="lexical_entry.physical_dimension_form",
                target_family="forms",
            ),
        ),
    ]
    artifact_id: Annotated[
        str | None,
        charter_field(
            column_name="id",
            primary_key=True,
            nullable=True,
            order=3,
            versioned=False,
        ),
    ] = None
    logical_ids: Annotated[
        tuple[ConceptLogicalIdDocument, ...],
        charter_field(json=True, nullable=False, default_sql="'[]'"),
    ] = ()
    version_id: Annotated[str | None, charter_field(versioned=False)] = None
    aliases: Annotated[
        tuple[ConceptAliasDocument, ...],
        charter_field(json=True, nullable=False, default_sql="'[]'"),
    ] = ()
    created_date: str | None = None
    definition_source: str | None = None
    domain: str | None = None
    form_parameters: Annotated[
        ConceptFormParametersDocument | None,
        charter_field(json=True, nullable=True),
    ] = None
    last_modified: str | None = None
    notes: str | None = None
    parameterization_relationships: Annotated[
        tuple[ParameterizationRelationshipDocument, ...],
        charter_field(
            json=True,
            nullable=False,
            default_sql="'[]'",
            foreign_keys=(
                ForeignKeySpec(
                    name="concept_parameterization_input",
                    contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                    source_family="concepts",
                    source_field="parameterization_relationships[].inputs[]",
                    target_family="concepts",
                    many=True,
                    required=False,
                ),
                ForeignKeySpec(
                    name="concept_parameterization_canonical_claim",
                    contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                    source_family="concepts",
                    source_field="parameterization_relationships[].canonical_claim",
                    target_family="claims",
                    required=False,
                ),
            ),
        ),
    ] = ()
    range: Annotated[
        tuple[float, float] | None,
        charter_field(json=True, nullable=True),
    ] = None
    relationships: Annotated[
        tuple[ConceptRelationshipDocument, ...],
        charter_field(
            json=True,
            nullable=False,
            default_sql="'[]'",
            foreign_key=ForeignKeySpec(
                name="concept_relationship_target",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="concepts",
                source_field="relationships[].target",
                target_family="concepts",
                many=True,
                required=False,
            ),
        ),
    ] = ()
    replaced_by: Annotated[
        str | None,
        charter_field(
            nullable=True,
            foreign_key=ForeignKeySpec(
                name="concept_replaced_by",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="concepts",
                source_field="replaced_by",
                target_family="concepts",
                required=False,
            ),
        ),
    ] = None


AUTHORED_CONCEPT_CHARTER: FamilyCharter = ConceptDocument.__charter__


# ---------------------------------------------------------------------------
# Source-branch concept documents
# ---------------------------------------------------------------------------


@charter(
    key="source-concept-alias",
    name="source-concept-alias",
    contract_version=AUTHORED_CONCEPT_FAMILY_CONTRACT_VERSION,
    placement=".source/concept-aliases",
    identity_field="name",
    semantic="propstore.source",
    artifact_family_name="propstore-source-concept-alias",
    model_name="SourceConceptAlias",
)
class SourceConceptAliasDocument(CharterDoc, kw_only=True):
    name: str
    source: str | None = None
    note: str | None = None


SOURCE_CONCEPT_ALIAS_CHARTER: FamilyCharter = SourceConceptAliasDocument.__charter__


@charter(
    key="source-concept-registry-match",
    name="source-concept-registry-match",
    contract_version=AUTHORED_CONCEPT_FAMILY_CONTRACT_VERSION,
    placement=".source/concept-registry-matches",
    identity_field="artifact_id",
    semantic="propstore.source",
    artifact_family_name="propstore-source-concept-registry-match",
    model_name="SourceConceptRegistryMatch",
)
class SourceConceptRegistryMatchDocument(CharterDoc, kw_only=True):
    artifact_id: str
    canonical_name: str | None = None


SOURCE_CONCEPT_REGISTRY_MATCH_CHARTER: FamilyCharter = (
    SourceConceptRegistryMatchDocument.__charter__
)


@charter(
    key="source-concept-form-parameters",
    name="source-concept-form-parameters",
    contract_version=AUTHORED_CONCEPT_FAMILY_CONTRACT_VERSION,
    placement=".source/concept-form-parameters",
    identity_field="construction",
    semantic="propstore.source",
    artifact_family_name="propstore-source-concept-form-parameters",
    model_name="SourceConceptFormParameters",
)
class SourceConceptFormParametersDocument(CharterDoc, kw_only=True):
    construction: str | None = None
    extensible: bool | None = None
    note: str | None = None
    reference: str | None = None
    values: tuple[str, ...] | None = None


SOURCE_CONCEPT_FORM_PARAMETERS_CHARTER: FamilyCharter = (
    SourceConceptFormParametersDocument.__charter__
)


@charter(
    key="source-parameterization-relationship",
    name="source-parameterization-relationship",
    contract_version=AUTHORED_CONCEPT_FAMILY_CONTRACT_VERSION,
    placement=".source/parameterization-relationships",
    identity_field="inputs",
    semantic="propstore.source",
    artifact_family_name="propstore-source-parameterization-relationship",
    model_name="SourceParameterizationRelationship",
)
class SourceParameterizationRelationshipDocument(CharterDoc, kw_only=True):
    inputs: tuple[str, ...]
    formula: str | None = None
    sympy: str | None = None
    exactness: Annotated[Exactness | None, charter_field(enum_type=Exactness)] = None
    source: str | None = None
    bidirectional: bool | None = None
    conditions: Annotated[tuple[CelExpr, ...], charter_field(nullable=True)] = ()
    note: str | None = None
    canonical_claim: str | None = None
    fit_statistics: str | None = None


SOURCE_PARAMETERIZATION_RELATIONSHIP_CHARTER: FamilyCharter = (
    SourceParameterizationRelationshipDocument.__charter__
)


@charter(
    key="source-concept-entry-document",
    name="source-concept-entry",
    contract_version=AUTHORED_CONCEPT_FAMILY_CONTRACT_VERSION,
    placement=".source/concepts",
    identity_field="local_name",
    semantic="propstore.source",
    artifact_family_name="propstore-source-concept-entry-document",
    model_name="SourceConceptEntry",
)
class SourceConceptEntryDocument(CharterDoc, kw_only=True):
    local_name: str | None = None
    proposed_name: str | None = None
    definition: str | None = None
    form: str | None = None
    aliases: Annotated[
        tuple[SourceConceptAliasDocument, ...], charter_field(nullable=True)
    ] = ()
    form_parameters: SourceConceptFormParametersDocument | None = None
    parameterization_relationships: Annotated[
        tuple[SourceParameterizationRelationshipDocument, ...],
        charter_field(nullable=True),
    ] = ()
    status: str | None = None
    registry_match: SourceConceptRegistryMatchDocument | None = None
    artifact_code: str | None = None


SOURCE_CONCEPT_ENTRY_DOCUMENT_CHARTER: FamilyCharter = (
    SourceConceptEntryDocument.__charter__
)

SOURCE_CONCEPT_BATCH_SPEC = DocumentBatchSpec(
    batch_name="source-concepts",
    item_type=SourceConceptEntryDocument,
    items_field="concepts",
)
object.__setattr__(
    AUTHORED_CONCEPT_CHARTER,
    "batch_specs",
    (SOURCE_CONCEPT_BATCH_SPEC,),
)


# ---------------------------------------------------------------------------
# World row families (document == row)
# ---------------------------------------------------------------------------


class ConceptSearchQuerySyntaxError(ValueError):
    pass


_CONCEPT_FTS_SOURCE_QUERY = """
    SELECT
        c.id AS concept_id,
        c.canonical_name AS canonical_name,
        COALESCE((SELECT group_concat(a.alias_name, ' ') FROM alias a WHERE a.concept_id = c.id), '') AS aliases,
        c.definition AS definition,
        COALESCE((SELECT group_concat(value, ' ') FROM (
            SELECT rel_condition.value AS value FROM relationship r, json_each(r.conditions_cel) AS rel_condition WHERE r.source_id = c.id AND r.conditions_cel IS NOT NULL
            UNION ALL
            SELECT param_condition.value AS value FROM parameterization p, json_each(p.conditions_cel) AS param_condition WHERE p.output_concept_id = c.id AND p.conditions_cel IS NOT NULL
        )), '') AS conditions
    FROM concept c
    ORDER BY c.seq
"""


@charter(
    key="concept",
    name="concept",
    contract_version=_CONCEPT_WORLD_CONTRACT_VERSION,
    placement=".derived/concept",
    identity_field="id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-concept",
    model_name="Concept",
    model_mixin=ConceptBehavior,
    reference_keys=(
        ReferenceKey.field("primary_logical_id"),
        ReferenceKey.field("logical_ids[].value"),
        ReferenceKey.format("{namespace}:{value}", from_field="logical_ids[]"),
        ReferenceKey.field("canonical_name"),
    ),
    indexes=(CharterIndex("idx_concept_primary_logical_id", ("primary_logical_id",)),),
    fts=(
        CharterFtsIndex(
            "concept_fts",
            "concept_id",
            ("canonical_name", "aliases", "definition", "conditions"),
            source_query=_CONCEPT_FTS_SOURCE_QUERY,
        ),
    ),
    vector_caches=(
        CharterVectorCache(
            "concept_embeddings",
            table="concept_vec_{model_identity_hash}_{dimensions}",
            entity_id_field="id",
            source_seq_field="seq",
            source_content_hash_field="content_hash",
            status_table="concept_embedding_status",
        ),
    ),
)
class ConceptRowDocument(CharterDoc):
    id: Annotated[str, charter_field(primary_key=True, nullable=False)]
    primary_logical_id: Annotated[str, charter_field(nullable=False, default_sql="''")]
    logical_ids_json: Annotated[str, charter_field(nullable=False, default_sql="'[]'")]
    version_id: Annotated[str, charter_field(nullable=False, default_sql="''")]
    content_hash: Annotated[str, charter_field(nullable=False)]
    seq: Annotated[int, charter_field(nullable=False)]
    canonical_name: Annotated[str, charter_field(nullable=False, graph_node_label=True)]
    status: Annotated[str, charter_field(nullable=False, graph_metadata=True)]
    domain: Annotated[str, charter_field(nullable=True, graph_metadata=True)]
    definition: Annotated[str, charter_field(nullable=False)]
    kind_type: Annotated[str, charter_field(nullable=False)]
    form: Annotated[str, charter_field(nullable=False, graph_metadata=True)]
    form_parameters: Annotated[str, charter_field(nullable=True)]
    range_min: Annotated[float, charter_field(nullable=True)]
    range_max: Annotated[float, charter_field(nullable=True)]
    is_dimensionless: Annotated[int, charter_field(nullable=False, default_sql="0")]
    unit_symbol: Annotated[str, charter_field(nullable=True)]
    created_date: Annotated[str, charter_field(nullable=True)]
    last_modified: Annotated[str, charter_field(nullable=True)]


# The world ``concept`` family's generated document is named ``ConceptDocument``
# (auto-derived from the family name by the hand-written builder), which collides
# in name with the authored lemon ``ConceptDocument`` above. The contract-manifest
# document-schema map is keyed by ``module.__name__`` and ``concept`` is processed
# after ``authored_concept`` in ``world_charters()``, so this row document is the
# dedup winner whose flat fields appear under ``document_schema:ConceptDocument``.
# Restore that name on the document class (the public ``ConceptDocument`` binding
# keeps referencing the authored lemon document) so the manifest is byte-identical.
ConceptRowDocument.__name__ = "ConceptDocument"
ConceptRowDocument.__qualname__ = "ConceptDocument"

CONCEPT_CHARTER: FamilyCharter = ConceptRowDocument.__charter__


@charter(
    key="alias",
    name="alias",
    contract_version=_CONCEPT_WORLD_CONTRACT_VERSION,
    placement=".derived/alias",
    identity_field="concept_id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-alias",
    model_name="ConceptAlias",
    reference_keys=(ReferenceKey.field("alias_name"),),
    indexes=(
        CharterIndex("idx_alias_name", ("alias_name",)),
        CharterIndex("idx_alias_concept", ("concept_id",)),
    ),
)
class AliasDocument(CharterDoc):
    concept_id: Annotated[str, charter_field(nullable=False)]
    alias_name: Annotated[str, charter_field(nullable=False)]
    source: Annotated[str, charter_field(nullable=False)]


ALIAS_CHARTER: FamilyCharter = AliasDocument.__charter__


@charter(
    key="parameterization",
    name="parameterization",
    contract_version=_CONCEPT_WORLD_CONTRACT_VERSION,
    placement=".derived/parameterization",
    identity_field="output_concept_id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-parameterization",
    model_name="Parameterization",
    model_mixin=ParameterizationBehavior,
)
class ParameterizationDocument(CharterDoc):
    output_concept_id: Annotated[str, charter_field(nullable=False)]
    concept_ids: Annotated[str, charter_field(nullable=False)]
    formula: Annotated[str, charter_field(nullable=False)]
    sympy: Annotated[str, charter_field(nullable=True)]
    exactness: Annotated[str, charter_field(nullable=False)]
    conditions_cel: Annotated[str, charter_field(nullable=True)]
    conditions_ir: Annotated[
        CheckedConditionSetDocument | None, charter_field(json=True, nullable=True)
    ] = None


PARAMETERIZATION_CHARTER: FamilyCharter = ParameterizationDocument.__charter__


@charter(
    key="parameterization_group",
    name="parameterization_group",
    contract_version=_CONCEPT_WORLD_CONTRACT_VERSION,
    placement=".derived/parameterization_group",
    identity_field="concept_id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-parameterization_group",
    model_name="ParameterizationGroup",
    indexes=(CharterIndex("idx_param_group", ("group_id",)),),
)
class Parameterization_groupDocument(CharterDoc):
    concept_id: Annotated[str, charter_field(nullable=False)]
    group_id: Annotated[int, charter_field(nullable=False)]


PARAMETERIZATION_GROUP_CHARTER: FamilyCharter = (
    Parameterization_groupDocument.__charter__
)


@charter(
    key="relationship",
    name="relationship",
    contract_version=_CONCEPT_WORLD_CONTRACT_VERSION,
    placement=".derived/relationship",
    identity_field="source_id",
    semantic="propstore.world",
    artifact_family_name="propstore-world-relationship",
    model_name="ConceptRelationship",
    model_mixin=ConceptRelationshipBehavior,
    indexes=(
        CharterIndex("idx_rel_source", ("source_id",)),
        CharterIndex("idx_rel_target", ("target_id",)),
    ),
)
class RelationshipDocument(CharterDoc):
    source_id: Annotated[str, charter_field(nullable=False)]
    type: Annotated[str, charter_field(nullable=False)]
    target_id: Annotated[str, charter_field(nullable=False)]
    conditions_cel: Annotated[str, charter_field(nullable=True)]
    note: Annotated[str, charter_field(nullable=True)]


RELATIONSHIP_CHARTER: FamilyCharter = RelationshipDocument.__charter__


CONCEPT_CHARTERS: tuple[FamilyCharter, ...] = (
    CONCEPT_CHARTER,
    ALIAS_CHARTER,
    PARAMETERIZATION_CHARTER,
    PARAMETERIZATION_GROUP_CHARTER,
    RELATIONSHIP_CHARTER,
)


# ---------------------------------------------------------------------------
# Sidecar row compilation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConceptWriteModels:
    form_rows: tuple[Form, ...]
    concept_rows: tuple["Concept", ...]
    alias_rows: tuple["ConceptAlias", ...]
    relationship_rows: tuple["ConceptRelationship", ...]
    relation_edge_rows: tuple[Mapping[str, object], ...]
    parameterization_rows: tuple["Parameterization", ...]
    parameterization_group_rows: tuple["ParameterizationGroup", ...]
    form_algebra_rows: tuple[FormAlgebra, ...]
