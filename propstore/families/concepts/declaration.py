"""Concept family projection, row, and derived-query declaration."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

import json
import msgspec
from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import (
    CharterField,
    CharterFtsIndex,
    CharterIndex,
    CharterVectorCache,
    FamilyCharter,
    FamilyModel,
)
from quire.documents import DocumentBatchSpec
from quire.families import FamilyDefinition
from quire.references import ForeignKeySpec, ReferenceKey
from quire.versions import VersionId

from propstore.core.conditions import (
    check_condition_ir,
    checked_condition_set,
    checked_condition_set_to_json,
)
from propstore.core.conditions.registry import ConceptInfo, with_standard_synthetic_bindings
from propstore.core.exactness_types import Exactness
from propstore.core.id_types import ConceptId
from propstore.core.lemon.description_kinds import DescriptionKind
from propstore.core.lemon.proto_roles import ProtoRoleBundle
from propstore.core.lemon.qualia import QualiaStructure
from propstore.families.forms.stages import (
    Form,
    FormAlgebra,
    FormDefinition,
    compile_form_algebra,
    compile_form_models,
    kind_value_from_form_name,
)
from propstore.families.concepts.types import ConceptRelationshipType, ConceptStatus
from propstore.provenance import Provenance

if TYPE_CHECKING:
    from propstore.families.concepts.stages import ConceptRecord, LoadedConcept


AUTHORED_CONCEPT_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")
_CONCEPT_WORLD_CONTRACT_VERSION = VersionId("2026.05.20", allow_placeholder=False)
SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION = VersionId("2026.05.21")


class ConceptLogicalIdDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    namespace: str
    value: str


class ConceptAliasDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    name: str
    source: str | None = None
    note: str | None = None


class ConceptRelationshipDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    type: ConceptRelationshipType
    target: str
    source: str | None = None
    conditions: tuple[str, ...] = ()
    note: str | None = None


class ConceptFormParametersDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    construction: str | None = None
    extensible: bool | None = None
    note: str | None = None
    reference: str | None = None
    values: tuple[str, ...] | None = None


class ParameterizationRelationshipDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
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


class OntologyReferenceDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    uri: str
    label: str | None = None


class LexicalFormDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    written_rep: str
    language: str
    phonetic_rep: str | None = None


class LexicalSenseDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    reference: OntologyReferenceDocument
    usage: str | None = None
    provenance: Provenance | None = None
    qualia: QualiaStructure | None = None
    description_kind: DescriptionKind | None = None
    role_bundles: dict[str, ProtoRoleBundle] | None = None


class LexicalEntryDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    identifier: str
    canonical_form: LexicalFormDocument
    senses: tuple[LexicalSenseDocument, ...]
    physical_dimension_form: str
    other_forms: tuple[LexicalFormDocument, ...] = ()


class ConceptIdScanDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=False):
    id: str | None = None
    artifact_id: str | None = None
    logical_ids: tuple[ConceptLogicalIdDocument, ...] = ()


class AuthoredConcept(FamilyModel):
    pass


def _validate_lexical_entry_has_sense(document: msgspec.Struct) -> None:
    lexical_entry = getattr(document, "lexical_entry")
    if not lexical_entry.senses:
        raise ValueError("lexical_entry requires at least one sense")


AUTHORED_CONCEPT_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="authored_concept",
        name="authored_concept",
        contract_version=AUTHORED_CONCEPT_FAMILY_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-authored_concept",
            contract_version=AUTHORED_CONCEPT_FAMILY_CONTRACT_VERSION,
            doc_type=AuthoredConcept,
            placement=FlatYamlPlacement(".derived/authored_concept", str),
        ),
        identity_field="id",
        reference_keys=(
            ReferenceKey.field("artifact_id"),
            ReferenceKey.field("logical_ids[].value"),
            ReferenceKey.format("{namespace}:{value}", from_field="logical_ids[]"),
            ReferenceKey.field("aliases[].name"),
        ),
    ),
    model=AuthoredConcept,
    fields=(
        CharterField(
            "id",
            str | None,
            primary_key=True,
            nullable=True,
            document_name="artifact_id",
            document_order=3,
        ),
        CharterField("status", ConceptStatus, nullable=False, document_order=0),
        CharterField(
            "ontology_reference",
            OntologyReferenceDocument,
            parse_boundary="json",
            nullable=False,
            document_order=1,
        ),
        CharterField(
            "lexical_entry",
            LexicalEntryDocument,
            parse_boundary="json",
            nullable=False,
            document_order=2,
            foreign_key=ForeignKeySpec(
                name="concept_form",
                contract_version=SEMANTIC_FOREIGN_KEY_CONTRACT_VERSION,
                source_family="concepts",
                source_field="lexical_entry.physical_dimension_form",
                target_family="forms",
            ),
        ),
        CharterField(
            "logical_ids",
            tuple[ConceptLogicalIdDocument, ...],
            parse_boundary="json",
            nullable=False,
            default=(),
            default_sql="'[]'",
        ),
        CharterField("version_id", str, nullable=True),
        CharterField(
            "aliases",
            tuple[ConceptAliasDocument, ...],
            parse_boundary="json",
            nullable=False,
            default=(),
            default_sql="'[]'",
        ),
        CharterField("created_date", str, nullable=True),
        CharterField("definition_source", str, nullable=True),
        CharterField("domain", str, nullable=True),
        CharterField(
            "form_parameters",
            ConceptFormParametersDocument,
            parse_boundary="json",
            nullable=True,
        ),
        CharterField("last_modified", str, nullable=True),
        CharterField("notes", str, nullable=True),
        CharterField(
            "parameterization_relationships",
            tuple[ParameterizationRelationshipDocument, ...],
            parse_boundary="json",
            nullable=False,
            default=(),
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
        CharterField(
            "range",
            tuple[float, float],
            parse_boundary="json",
            nullable=True,
        ),
        CharterField(
            "relationships",
            tuple[ConceptRelationshipDocument, ...],
            parse_boundary="json",
            nullable=False,
            default=(),
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
        CharterField(
            "replaced_by",
            str,
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
    ),
    semantic_metadata={"semantic": "propstore.world"},
    validators=(_validate_lexical_entry_has_sense,),
)


if TYPE_CHECKING:

    class ConceptDocument(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
        status: ConceptStatus
        ontology_reference: OntologyReferenceDocument
        lexical_entry: LexicalEntryDocument
        artifact_id: str | None = None
        logical_ids: tuple[ConceptLogicalIdDocument, ...] = ()
        version_id: str | None = None
        aliases: tuple[ConceptAliasDocument, ...] = ()
        created_date: str | None = None
        definition_source: str | None = None
        domain: str | None = None
        form_parameters: ConceptFormParametersDocument | None = None
        last_modified: str | None = None
        notes: str | None = None
        parameterization_relationships: tuple[ParameterizationRelationshipDocument, ...] = ()
        range: tuple[float, float] | None = None
        relationships: tuple[ConceptRelationshipDocument, ...] = ()
        replaced_by: str | None = None

else:
    ConceptDocument: Any = AUTHORED_CONCEPT_CHARTER.generated_document()
    ConceptDocument.__name__ = "ConceptDocument"
    ConceptDocument.__qualname__ = "ConceptDocument"
    ConceptDocument.__module__ = __name__


from propstore.families.documents.sources import SourceConceptEntryDocument

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


def compile_concept_sidecar_rows(
    concepts: list["LoadedConcept"],
    form_registry: dict[str, FormDefinition],
    cel_registry: dict[str, ConceptInfo],
) -> ConceptWriteModels:
    form_rows = compile_form_models(form_registry)
    concept_rows: list[Concept] = []
    alias_rows: list[ConceptAlias] = []
    relationship_rows: list[ConceptRelationship] = []
    relation_edge_rows: list[Mapping[str, object]] = []
    parameterization_rows: list[Parameterization] = []
    parameterization_group_rows: list[ParameterizationGroup] = []
    condition_registry = with_standard_synthetic_bindings(cel_registry)

    for seq, concept in enumerate(concepts, 1):
        record = concept.record
        content_hash = record.version_id.removeprefix("sha256:")[:16]
        form_definition = form_registry.get(record.form)
        is_dimensionless = (
            1
            if form_definition is not None and form_definition.is_dimensionless
            else 0
        )
        unit_symbol = form_definition.unit_symbol if form_definition is not None else None
        form_parameters_json = (
            json.dumps(record.form_parameters)
            if record.form_parameters
            else None
        )
        range_min = None if record.range is None else record.range[0]
        range_max = None if record.range is None else record.range[1]
        concept_id = str(record.artifact_id)

        concept_rows.append(
            Concept(
                id=concept_id,
                primary_logical_id=record.primary_logical_id or "",
                logical_ids_json=json.dumps(
                    [logical_id.to_payload() for logical_id in record.logical_ids]
                ),
                version_id=record.version_id,
                content_hash=content_hash,
                seq=seq,
                canonical_name=record.canonical_name,
                status=record.status.value,
                domain=record.domain,
                definition=record.definition,
                kind_type=form_definition.kind.value
                if form_definition is not None
                else kind_value_from_form_name(record.form),
                form=record.form,
                form_parameters=form_parameters_json,
                range_min=range_min,
                range_max=range_max,
                is_dimensionless=is_dimensionless,
                unit_symbol=unit_symbol,
                created_date=record.created_date,
                last_modified=record.last_modified,
            )
        )

        for alias in record.aliases:
            alias_rows.append(
                ConceptAlias(
                    concept_id=concept_id,
                    alias_name=alias.name,
                    source=alias.source,
                )
            )

        for relationship in record.relationships:
            conditions_json = (
                json.dumps(list(relationship.conditions))
                if relationship.conditions
                else None
            )
            target_id = str(relationship.target)
            relationship_rows.append(
                ConceptRelationship(
                    source_id=concept_id,
                    type=relationship.relationship_type,
                    target_id=target_id,
                    conditions_cel=conditions_json,
                    note=relationship.note,
                )
            )
            relation_edge_rows.append(
                {
                    "source_kind": "concept",
                    "source_id": concept_id,
                    "relation_type": str(relationship.relationship_type),
                    "target_kind": "concept",
                    "target_id": target_id,
                    "conditions_cel": conditions_json,
                    "note": relationship.note,
                }
            )

        for parameterization in record.parameterizations:
            if parameterization.formula is None:
                raise ValueError(f"Parameterization for {concept_id} is missing formula")
            if parameterization.exactness is None:
                raise ValueError(f"Parameterization for {concept_id} is missing exactness")
            inputs = [str(input_id) for input_id in parameterization.inputs]
            conditions_json = (
                json.dumps(list(parameterization.conditions))
                if parameterization.conditions
                else None
            )
            conditions_ir = (
                json.dumps(
                    checked_condition_set_to_json(
                        checked_condition_set(
                            check_condition_ir(condition, condition_registry)
                            for condition in parameterization.conditions
                        )
                    ),
                    sort_keys=True,
                )
                if parameterization.conditions
                else None
            )
            parameterization_rows.append(
                Parameterization(
                    output_concept_id=concept_id,
                    concept_ids=json.dumps(inputs),
                    formula=parameterization.formula,
                    sympy=parameterization.sympy,
                    exactness=str(parameterization.exactness),
                    conditions_cel=conditions_json,
                    conditions_ir=conditions_ir,
                )
            )

    from propstore.parameterization_groups import build_groups

    groups = build_groups(concepts)
    for group_id, group_members in enumerate(sorted(groups, key=lambda group: min(group))):
        for concept_id in sorted(group_members):
            parameterization_group_rows.append(
                ParameterizationGroup(
                    concept_id=concept_id,
                    group_id=group_id,
                )
            )

    return ConceptWriteModels(
        form_rows=form_rows,
        concept_rows=tuple(concept_rows),
        alias_rows=tuple(alias_rows),
        relationship_rows=tuple(relationship_rows),
        relation_edge_rows=tuple(relation_edge_rows),
        parameterization_rows=tuple(parameterization_rows),
        parameterization_group_rows=tuple(parameterization_group_rows),
        form_algebra_rows=compile_form_algebra(concepts, form_registry),
    )


class Concept(FamilyModel):
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

    def conflict_detector_payload(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "canonical_name": self.canonical_name,
            "status": self.status,
            "form": self.form,
            "kind_type": self.kind_type,
        }
        if self.range_min is not None:
            data["range_min"] = self.range_min
        if self.range_max is not None:
            data["range_max"] = self.range_max
        if self.form_parameters:
            try:
                form_parameters = json.loads(self.form_parameters)
            except json.JSONDecodeError:
                form_parameters = {}
            if isinstance(form_parameters, dict):
                data["form_parameters"] = form_parameters
        return data


class ConceptAlias(FamilyModel):
    pass


class ConceptRelationship(FamilyModel):
    @property
    def relationship_type(self) -> str:
        return cast(str, getattr(self, "type"))


class Parameterization(FamilyModel):
    @property
    def input_concept_ids(self) -> tuple[str, ...]:
        payload = self.conflict_detector_payload()
        inputs = payload.get("inputs", ())
        if not isinstance(inputs, list):
            return ()
        return tuple(str(item) for item in inputs)

    def conflict_detector_payload(self) -> dict[str, Any]:
        return {
            "inputs": json.loads(self.concept_ids) if self.concept_ids else [],
            "sympy": self.sympy,
            "exactness": self.exactness,
            "conditions": (
                json.loads(self.conditions_cel)
                if self.conditions_cel
                else []
            ),
        }


class ParameterizationGroup(FamilyModel):
    pass


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


CONCEPT_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="concept",
        name="concept",
        contract_version=_CONCEPT_WORLD_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-concept",
            contract_version=_CONCEPT_WORLD_CONTRACT_VERSION,
            doc_type=Concept,
            placement=FlatYamlPlacement(".derived/concept", str),
        ),
        identity_field="id",
        reference_keys=(
            ReferenceKey.field("primary_logical_id"),
            ReferenceKey.field("logical_ids[].value"),
            ReferenceKey.format("{namespace}:{value}", from_field="logical_ids[]"),
            ReferenceKey.field("canonical_name"),
        ),
    ),
    model=Concept,
    fields=(
        CharterField("id", str, primary_key=True, nullable=False),
        CharterField("primary_logical_id", str, nullable=False, default_sql="''"),
        CharterField("logical_ids_json", str, nullable=False, default_sql="'[]'"),
        CharterField("version_id", str, nullable=False, default_sql="''"),
        CharterField("content_hash", str, nullable=False),
        CharterField("seq", int, nullable=False),
        CharterField("canonical_name", str, nullable=False, graph_node_label=True),
        CharterField("status", str, nullable=False, graph_metadata=True),
        CharterField("domain", str, graph_metadata=True),
        CharterField("definition", str, nullable=False),
        CharterField("kind_type", str, nullable=False),
        CharterField("form", str, nullable=False, graph_metadata=True),
        CharterField("form_parameters", str),
        CharterField("range_min", float),
        CharterField("range_max", float),
        CharterField("is_dimensionless", int, nullable=False, default_sql="0"),
        CharterField("unit_symbol", str),
        CharterField("created_date", str),
        CharterField("last_modified", str),
    ),
    indexes=(CharterIndex("idx_concept_primary_logical_id", ("primary_logical_id",)),),
    fts_indexes=(
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
    semantic_metadata={"semantic": "propstore.world"},
)

ALIAS_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="alias",
        name="alias",
        contract_version=_CONCEPT_WORLD_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-alias",
            contract_version=_CONCEPT_WORLD_CONTRACT_VERSION,
            doc_type=ConceptAlias,
            placement=FlatYamlPlacement(".derived/alias", str),
        ),
        identity_field="concept_id",
        reference_keys=(ReferenceKey.field("alias_name"),),
    ),
    model=ConceptAlias,
    fields=(
        CharterField("concept_id", str, nullable=False),
        CharterField("alias_name", str, nullable=False),
        CharterField("source", str, nullable=False),
    ),
    indexes=(
        CharterIndex("idx_alias_name", ("alias_name",)),
        CharterIndex("idx_alias_concept", ("concept_id",)),
    ),
    semantic_metadata={"semantic": "propstore.world"},
)

PARAMETERIZATION_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="parameterization",
        name="parameterization",
        contract_version=_CONCEPT_WORLD_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-parameterization",
            contract_version=_CONCEPT_WORLD_CONTRACT_VERSION,
            doc_type=Parameterization,
            placement=FlatYamlPlacement(".derived/parameterization", str),
        ),
        identity_field="output_concept_id",
    ),
    model=Parameterization,
    fields=(
        CharterField("output_concept_id", str, nullable=False),
        CharterField("concept_ids", str, nullable=False),
        CharterField("formula", str, nullable=False),
        CharterField("sympy", str),
        CharterField("exactness", str, nullable=False),
        CharterField("conditions_cel", str),
        CharterField("conditions_ir", str),
    ),
    semantic_metadata={"semantic": "propstore.world"},
)

PARAMETERIZATION_GROUP_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="parameterization_group",
        name="parameterization_group",
        contract_version=_CONCEPT_WORLD_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-parameterization_group",
            contract_version=_CONCEPT_WORLD_CONTRACT_VERSION,
            doc_type=ParameterizationGroup,
            placement=FlatYamlPlacement(".derived/parameterization_group", str),
        ),
        identity_field="concept_id",
    ),
    model=ParameterizationGroup,
    fields=(
        CharterField("concept_id", str, nullable=False),
        CharterField("group_id", int, nullable=False),
    ),
    indexes=(CharterIndex("idx_param_group", ("group_id",)),),
    semantic_metadata={"semantic": "propstore.world"},
)

RELATIONSHIP_CHARTER: FamilyCharter = FamilyCharter(
    family=FamilyDefinition(
        key="relationship",
        name="relationship",
        contract_version=_CONCEPT_WORLD_CONTRACT_VERSION,
        artifact_family=ArtifactFamily(
            name="propstore-world-relationship",
            contract_version=_CONCEPT_WORLD_CONTRACT_VERSION,
            doc_type=ConceptRelationship,
            placement=FlatYamlPlacement(".derived/relationship", str),
        ),
        identity_field="source_id",
    ),
    model=ConceptRelationship,
    fields=(
        CharterField("source_id", str, nullable=False),
        CharterField("type", str, nullable=False),
        CharterField("target_id", str, nullable=False),
        CharterField("conditions_cel", str),
        CharterField("note", str),
    ),
    indexes=(
        CharterIndex("idx_rel_source", ("source_id",)),
        CharterIndex("idx_rel_target", ("target_id",)),
    ),
    semantic_metadata={"semantic": "propstore.world"},
)


CONCEPT_CHARTERS: tuple[FamilyCharter, ...] = (
    CONCEPT_CHARTER,
    ALIAS_CHARTER,
    PARAMETERIZATION_CHARTER,
    PARAMETERIZATION_GROUP_CHARTER,
    RELATIONSHIP_CHARTER,
)
