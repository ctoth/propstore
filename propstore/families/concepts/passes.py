"""Concept file validator for the propstore concept registry.

Loads all concepts/*.yaml files and runs structural validation via Python
code (required fields, valid types, cross-reference checks). There is no
JSON Schema validation in this module.

Reports errors (hard stop) and warnings separately.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from quire.documents import LoadedDocument

from quire.references import FamilyReferenceIndex
from propstore.families.identity.logical_ids import (
    LOGICAL_NAMESPACE_RE,
    LOGICAL_VALUE_RE,
    format_logical_id,
)
from propstore.families.concepts.types import (
    ConceptStatus,
    ConceptRelationshipType,
    VALID_CONCEPT_RELATIONSHIP_TYPES,
)
from propstore.families.forms.stages import (
    FormDefinition,
)
from propstore.families.concepts.stages import (
    ConceptAuthoredSet,
    ConceptBoundRegistry,
    ConceptCheckedRegistry,
    ConceptNormalizedSet,
    ConceptStage,
    concept_reference_keys,
)
from propstore.families.concepts.declaration import ConceptDocument
from propstore.families.claims.references import ClaimReferenceRecord
from propstore.families.registry import PropstoreFamily
from propstore.semantic_passes.registry import PipelineRegistry
from propstore.semantic_passes.runner import run_pipeline
from propstore.semantic_passes.types import PassDiagnostic, PassResult, PipelineResult

VALID_RELATIONSHIP_TYPES = VALID_CONCEPT_RELATIONSHIP_TYPES
_QUALIA_ROLE_NAMES = ("formal", "constitutive", "telic", "agentive")
_TYPE_RELATIONSHIPS = {
    ConceptRelationshipType.IS_A,
    ConceptRelationshipType.KIND_OF,
}


@dataclass
class _ConceptCheckResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _concept_reference_keys(
    concept: LoadedDocument[ConceptDocument],
) -> set[str]:
    return set(concept_reference_keys(concept.document))


def _concept_reference_index(
    concepts: list[LoadedDocument[ConceptDocument]],
) -> dict[str, LoadedDocument[ConceptDocument]]:
    index: dict[str, LoadedDocument[ConceptDocument]] = {}
    for concept in concepts:
        for key in _concept_reference_keys(concept):
            index.setdefault(key, concept)
    return index


def _concept_satisfies_type(
    concept: LoadedDocument[ConceptDocument],
    required_reference: str,
    reference_index: dict[str, LoadedDocument[ConceptDocument]],
) -> bool:
    pending = [concept]
    visited: set[str] = set()
    while pending:
        current = pending.pop(0)
        current_id = str(current.document.artifact_id)
        if current_id in visited:
            continue
        visited.add(current_id)
        if required_reference in _concept_reference_keys(current):
            return True
        for relationship in current.document.relationships:
            if relationship.type not in _TYPE_RELATIONSHIPS:
                continue
            target = str(relationship.target)
            if target == required_reference:
                return True
            target_concept = reference_index.get(target)
            if target_concept is not None:
                pending.append(target_concept)
    return False


def _validate_reference_exists(
    concept: LoadedDocument[ConceptDocument],
    *,
    field: str,
    reference_uri: str,
    reference_index: dict[str, LoadedDocument[ConceptDocument]],
    result: _ConceptCheckResult,
) -> LoadedDocument[ConceptDocument] | None:
    target = reference_index.get(reference_uri)
    if target is None:
        result.errors.append(
            f"{concept.filename}: {field} reference '{reference_uri}' not found in registry"
        )
    return target


def _validate_phase3_lemon_references(
    concept: LoadedDocument[ConceptDocument],
    *,
    reference_index: dict[str, LoadedDocument[ConceptDocument]],
    result: _ConceptCheckResult,
) -> None:
    document = concept.document
    if document is None:
        return

    for sense in document.lexical_entry.senses:
        qualia = sense.qualia
        if qualia is not None:
            for role_name in _QUALIA_ROLE_NAMES:
                for qualia_reference in getattr(qualia, role_name):
                    target = _validate_reference_exists(
                        concept,
                        field=f"qualia.{role_name}",
                        reference_uri=qualia_reference.reference.uri,
                        reference_index=reference_index,
                        result=result,
                    )
                    type_constraint = qualia_reference.type_constraint
                    if type_constraint is None:
                        continue
                    required_uri = type_constraint.reference.uri
                    required = _validate_reference_exists(
                        concept,
                        field=f"qualia.{role_name}.type_constraint",
                        reference_uri=required_uri,
                        reference_index=reference_index,
                        result=result,
                    )
                    if (
                        target is not None
                        and required is not None
                        and not _concept_satisfies_type(
                            target,
                            required_uri,
                            reference_index,
                        )
                    ):
                        result.errors.append(
                            f"{concept.filename}: qualia.{role_name} reference "
                            f"'{qualia_reference.reference.uri}' does not satisfy "
                            f"type constraint '{required_uri}'"
                        )

        description_kind = sense.description_kind
        if description_kind is None:
            continue
        _validate_reference_exists(
            concept,
            field="description_kind",
            reference_uri=description_kind.reference.uri,
            reference_index=reference_index,
            result=result,
        )
        for slot in description_kind.slots:
            _validate_reference_exists(
                concept,
                field=f"description_kind.slot.{slot.name}.type_constraint",
                reference_uri=slot.type_constraint.uri,
                reference_index=reference_index,
                result=result,
            )


def _validate_lemon_document(
    concept: LoadedDocument[ConceptDocument],
    *,
    result: _ConceptCheckResult,
) -> None:
    document = concept.document
    if document is None:
        return

    entry = document.lexical_entry
    ontology_uri = document.ontology_reference.uri
    sense_uris: set[str] = set()
    for sense in entry.senses:
        reference_uri = sense.reference.uri
        if reference_uri in sense_uris:
            result.errors.append(
                f"{concept.filename}: duplicate lexical sense reference '{reference_uri}'"
            )
        sense_uris.add(reference_uri)

    if ontology_uri not in sense_uris:
        result.errors.append(
            f"{concept.filename}: ontology_reference '{ontology_uri}' must have a matching lexical sense"
        )


def _validate_logical_ids(
    logical_ids: object,
    *,
    filename: str,
    artifact_id: str,
    seen_logical_ids: dict[str, str],
    result: _ConceptCheckResult,
) -> set[str]:
    formatted_ids: set[str] = set()
    if not isinstance(logical_ids, tuple) or not logical_ids:
        result.errors.append(
            f"{filename}: concept '{artifact_id}' must define a non-empty logical_ids tuple"
        )
        return formatted_ids

    for index, entry in enumerate(logical_ids, start=1):
        if isinstance(entry, Mapping):
            namespace = entry.get("namespace")
            value = entry.get("value")
        else:
            namespace = getattr(entry, "namespace", None)
            value = getattr(entry, "value", None)
        if not isinstance(namespace, str) or not isinstance(value, str):
            result.errors.append(
                f"{filename}: concept '{artifact_id}' logical_ids entry #{index} "
                "must define namespace and value"
            )
            continue
        if not isinstance(namespace, str) or not LOGICAL_NAMESPACE_RE.match(namespace):
            result.errors.append(
                f"{filename}: concept '{artifact_id}' logical_ids entry #{index} "
                f"uses invalid namespace {namespace!r}"
            )
            continue
        if not isinstance(value, str) or not LOGICAL_VALUE_RE.match(value):
            result.errors.append(
                f"{filename}: concept '{artifact_id}' logical_ids entry #{index} "
                f"uses invalid value {value!r}"
            )
            continue

        formatted = format_logical_id({"namespace": namespace, "value": value})
        if formatted is None:
            result.errors.append(
                f"{filename}: concept '{artifact_id}' logical_ids entry #{index} "
                "must serialize as namespace:value"
            )
            continue
        if formatted in formatted_ids:
            result.errors.append(
                f"{filename}: concept '{artifact_id}' duplicates logical ID '{formatted}'"
            )
            continue
        if formatted in seen_logical_ids:
            result.errors.append(
                f"{filename}: duplicate logical ID '{formatted}' "
                f"(also in {seen_logical_ids[formatted]})"
            )
            continue
        formatted_ids.add(formatted)
        seen_logical_ids[formatted] = filename
    return formatted_ids


def _check_concepts(
    concepts: list[LoadedDocument[ConceptDocument]],
    *,
    form_registry: Mapping[str, FormDefinition] | None = None,
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord] | None = None,
) -> _ConceptCheckResult:
    result = _ConceptCheckResult()
    id_to_concept: dict[str, LoadedDocument[ConceptDocument]] = {}
    seen_logical_ids: dict[str, str] = {}
    reference_index = _concept_reference_index(concepts)

    for concept in concepts:
        document = concept.document
        _validate_lemon_document(concept, result=result)
        _validate_phase3_lemon_references(
            concept,
            reference_index=reference_index,
            result=result,
        )

        artifact_id = document.artifact_id
        if not isinstance(artifact_id, str) or not artifact_id:
            result.errors.append(f"{concept.filename}: missing required field 'artifact_id'")
            continue
        id_to_concept[artifact_id] = concept

        canonical_name = document.lexical_entry.canonical_form.written_rep
        if not canonical_name:
            result.errors.append(
                f"{concept.filename}: missing canonical lexical written_rep"
            )
        if document.status is None:
            result.errors.append(f"{concept.filename}: missing required field 'status'")
        if not document.definition_source:
            result.errors.append(
                f"{concept.filename}: missing required field 'definition_source'"
            )

        _validate_logical_ids(
            document.logical_ids,
            filename=concept.filename,
            artifact_id=artifact_id,
            seen_logical_ids=seen_logical_ids,
            result=result,
        )

        form_name = document.lexical_entry.physical_dimension_form
        if not form_name:
            result.errors.append(f"{concept.filename}: missing required field 'form'")
        elif form_registry is not None and form_name not in form_registry:
            result.errors.append(
                f"{concept.filename}: form '{form_name}' is not registered"
            )

        if form_name == "category":
            values = None
            if document.form_parameters is not None:
                values = document.form_parameters.values
            if not values:
                result.errors.append(
                    f"{concept.filename}: category concept must have "
                    "form_parameters.values"
                )

        for relationship in document.relationships:
            if relationship.type not in VALID_RELATIONSHIP_TYPES:
                result.errors.append(
                    f"{concept.filename}: invalid relationship type "
                    f"{relationship.type!r}"
                )
            if relationship.target not in reference_index:
                result.errors.append(
                    f"{concept.filename}: relationship target "
                    f"'{relationship.target}' not found in registry"
                )

        for parameterization in document.parameterization_relationships:
            for input_ref in parameterization.inputs:
                if input_ref not in reference_index:
                    result.errors.append(
                        f"{concept.filename}: parameterization input "
                        f"'{input_ref}' not found in registry"
                    )
            if (
                parameterization.exactness == "conditional"
                and not parameterization.conditions
            ):
                result.errors.append(
                    f"{concept.filename}: parameterization with conditional exactness "
                    "must have conditions"
                )
            canonical_claim = parameterization.canonical_claim
            if canonical_claim and claim_index is not None:
                claim_id = claim_index.resolve_id(str(canonical_claim))
                if claim_id is None:
                    result.errors.append(
                        f"{concept.filename}: canonical_claim "
                        f"'{canonical_claim}' not found in claim index"
                    )
            if not parameterization.sympy:
                result.warnings.append(
                    f"{concept.filename}: parameterization relationship missing "
                    "sympy expression"
                )

    for concept in concepts:
        document = concept.document
        if document.status is not ConceptStatus.DEPRECATED:
            continue
        visited: set[str] = set()
        current_id = document.artifact_id
        while isinstance(current_id, str) and current_id:
            if current_id in visited:
                result.errors.append(
                    f"{concept.filename}: circular deprecation chain detected "
                    f"involving '{current_id}'"
                )
                break
            visited.add(current_id)
            current_concept = id_to_concept.get(current_id)
            if current_concept is None:
                break
            current_document = current_concept.document
            if current_document.status is not ConceptStatus.DEPRECATED:
                break
            current_id = current_document.replaced_by

    return result


@dataclass(frozen=True)
class ConceptPipelineContext:
    form_registry: Mapping[str, FormDefinition] | None = None
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord] | None = None


class ConceptNormalizePass:
    family = PropstoreFamily.CONCEPTS
    name = "concept.normalize"
    version = "1"
    input_stage = ConceptStage.AUTHORED
    output_stage = ConceptStage.NORMALIZED

    def run(
        self,
        value: ConceptAuthoredSet,
        context: object,
    ) -> PassResult[ConceptNormalizedSet]:
        return PassResult.ok(ConceptNormalizedSet(concepts=tuple(value.concepts)))


class ConceptIdentityPass:
    family = PropstoreFamily.CONCEPTS
    name = "concept.identity"
    version = "1"
    input_stage = ConceptStage.NORMALIZED
    output_stage = ConceptStage.BOUND

    def run(
        self,
        value: ConceptNormalizedSet,
        context: object,
    ) -> PassResult[ConceptBoundRegistry]:
        registry = {
            str(concept.document.artifact_id): concept.document
            for concept in value.concepts
            if isinstance(concept.document.artifact_id, str)
            and concept.document.artifact_id
        }
        return PassResult.ok(
            ConceptBoundRegistry(
                concepts=value.concepts,
                registry=registry,
            )
        )


class ConceptSemanticCheckPass:
    family = PropstoreFamily.CONCEPTS
    name = "concept.semantic.check"
    version = "1"
    input_stage = ConceptStage.BOUND
    output_stage = ConceptStage.CHECKED

    def run(
        self,
        value: ConceptBoundRegistry,
        context: object,
    ) -> PassResult[ConceptCheckedRegistry]:
        pipeline_context = (
            context
            if isinstance(context, ConceptPipelineContext)
            else ConceptPipelineContext()
        )
        checked = _check_concepts(
            list(value.concepts),
            form_registry=pipeline_context.form_registry,
            claim_index=pipeline_context.claim_index,
        )
        diagnostics = [
            _diagnostic("warning", "concept.warning", warning)
            for warning in checked.warnings
        ]
        diagnostics.extend(
            _diagnostic("error", "concept.error", error) for error in checked.errors
        )
        return PassResult(
            output=ConceptCheckedRegistry(
                concepts=value.concepts,
                registry=value.registry,
            ),
            diagnostics=tuple(diagnostics),
        )


def register_concept_pipeline(registry: PipelineRegistry) -> None:
    registry.register(ConceptNormalizePass, family=PropstoreFamily.CONCEPTS)
    registry.register(ConceptIdentityPass, family=PropstoreFamily.CONCEPTS)
    registry.register(ConceptSemanticCheckPass, family=PropstoreFamily.CONCEPTS)


def run_concept_pipeline(
    concepts: tuple[LoadedDocument[ConceptDocument], ...]
    | list[LoadedDocument[ConceptDocument]],
    *,
    target_stage: ConceptStage = ConceptStage.CHECKED,
    context: ConceptPipelineContext | None = None,
) -> PipelineResult[object]:
    registry = PipelineRegistry()
    register_concept_pipeline(registry)
    return run_pipeline(
        ConceptAuthoredSet(concepts=tuple(concepts)),
        family=PropstoreFamily.CONCEPTS,
        start_stage=ConceptStage.AUTHORED,
        target_stage=target_stage,
        registry=registry,
        context=context or ConceptPipelineContext(),
    )


def _diagnostic(
    level: str,
    code: str,
    message: str,
) -> PassDiagnostic:
    filename = None
    detail = message
    if ": " in message:
        filename, detail = message.split(": ", 1)
    return PassDiagnostic(
        level="warning" if level == "warning" else "error",
        code=code,
        message=detail,
        family=PropstoreFamily.CONCEPTS,
        stage=ConceptStage.CHECKED,
        filename=filename,
        pass_name="concept.semantic.check",
    )
