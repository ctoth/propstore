"""Concept family projection, row, and derived-query declaration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

import json
from quire.charters import FamilyModel

from propstore.core.conditions import (
    check_condition_ir,
    checked_condition_set,
    checked_condition_set_to_json,
)
from propstore.core.conditions.registry import ConceptInfo, with_standard_synthetic_bindings
from propstore.core.id_types import ConceptId, to_concept_id
from propstore.families.forms.stages import (
    Form,
    FormAlgebra,
    FormDefinition,
    compile_form_algebra,
    compile_form_models,
    kind_value_from_form_name,
)
from propstore.parameterization_groups import build_groups

if TYPE_CHECKING:
    from propstore.families.concepts.stages import ConceptRecord, LoadedConcept


@dataclass(frozen=True)
class ConceptWriteModels:
    form_rows: tuple[Form, ...]
    concept_rows: tuple["Concept", ...]
    alias_rows: tuple["ConceptAlias", ...]
    relationship_rows: tuple["ConceptRelationship", ...]
    relation_edge_rows: tuple[object, ...]
    parameterization_rows: tuple["Parameterization", ...]
    parameterization_group_rows: tuple["ParameterizationGroup", ...]
    form_algebra_rows: tuple[FormAlgebra, ...]


def compile_concept_sidecar_rows(
    concepts: list["LoadedConcept"],
    form_registry: dict[str, FormDefinition],
    cel_registry: dict[str, ConceptInfo],
) -> ConceptWriteModels:
    from propstore.families.relations.declaration import ConceptRelation

    form_rows = compile_form_models(form_registry)
    concept_rows: list[Concept] = []
    alias_rows: list[ConceptAlias] = []
    relationship_rows: list[ConceptRelationship] = []
    relation_edge_rows: list[object] = []
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
                ConceptRelation(
                    source_kind="concept",
                    source_id=concept_id,
                    relation_type=str(relationship.relationship_type),
                    target_kind="concept",
                    target_id=target_id,
                    conditions_cel=conditions_json,
                    note=relationship.note,
                )
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
        return to_concept_id(cast(str, getattr(self, "id")))

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
