"""Propstore semantic foreign-key declarations and indexes."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Mapping, cast

from quire.references import (
    CrossFamilyReferenceIndex,
    ForeignKeySpec,
    ReferenceIndex,
    ReferenceResolution,
    build_reference_lookup,
)
from quire.versions import VersionId

from propstore.claims import (
    LoadedClaimsFile,
    claim_file_claims,
    claim_file_source_paper,
)
from propstore.core.concepts import ConceptRecord
from propstore.form_utils import FormDefinition
from propstore.identity import normalize_identity_namespace, normalize_logical_value

if TYPE_CHECKING:
    from propstore.compiler.context import CompilationContext


PROPSTORE_FOREIGN_KEY_CONTRACT_VERSION = VersionId("2026.04.20")

SEMANTIC_FOREIGN_KEYS: tuple[ForeignKeySpec, ...] = (
    ForeignKeySpec(
        name="claim_concept",
        contract_version=PROPSTORE_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="claim",
        source_field="concept",
        target_family="concept",
    ),
    ForeignKeySpec(
        name="claim_concepts",
        contract_version=PROPSTORE_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="claim",
        source_field="concepts",
        target_family="concept",
        many=True,
    ),
    ForeignKeySpec(
        name="claim_variable_concept",
        contract_version=PROPSTORE_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="claim",
        source_field="variables[].concept",
        target_family="concept",
    ),
    ForeignKeySpec(
        name="claim_parameter_concept",
        contract_version=PROPSTORE_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="claim",
        source_field="parameters[].concept",
        target_family="concept",
    ),
    ForeignKeySpec(
        name="claim_measurement_target_concept",
        contract_version=PROPSTORE_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="claim",
        source_field="target_concept",
        target_family="concept",
    ),
    ForeignKeySpec(
        name="claim_stance_target",
        contract_version=PROPSTORE_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="claim",
        source_field="stances[].target",
        target_family="claim",
    ),
    ForeignKeySpec(
        name="concept_parameterization_input",
        contract_version=PROPSTORE_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="concept",
        source_field="parameterization_relationships[].inputs[]",
        target_family="concept",
        many=True,
    ),
    ForeignKeySpec(
        name="concept_parameterization_canonical_claim",
        contract_version=PROPSTORE_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="concept",
        source_field="parameterization_relationships[].canonical_claim",
        target_family="claim",
        required=False,
    ),
    ForeignKeySpec(
        name="concept_replaced_by",
        contract_version=PROPSTORE_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="concept",
        source_field="replaced_by",
        target_family="concept",
        required=False,
    ),
    ForeignKeySpec(
        name="concept_relationship_target",
        contract_version=PROPSTORE_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="concept",
        source_field="relationships[].target",
        target_family="concept",
        many=True,
    ),
    ForeignKeySpec(
        name="concept_form",
        contract_version=PROPSTORE_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="concept",
        source_field="form",
        target_family="form",
    ),
    ForeignKeySpec(
        name="claim_context",
        contract_version=PROPSTORE_FOREIGN_KEY_CONTRACT_VERSION,
        source_family="claim",
        source_field="context",
        target_family="context",
    ),
)


def iter_semantic_foreign_keys() -> tuple[ForeignKeySpec, ...]:
    return SEMANTIC_FOREIGN_KEYS


def build_claim_reference_lookup(
    claim_files: list[LoadedClaimsFile],
) -> Mapping[str, tuple[str, ...]]:
    lookup = build_reference_lookup(
        (
            (claim_file, claim)
            for claim_file in claim_files
            for claim in claim_file_claims(claim_file)
        ),
        target_id=_claim_target_id,
        keys=_claim_reference_keys,
    )
    return MappingProxyType(dict(lookup))


def _claim_target_id(item: tuple[LoadedClaimsFile, Any]) -> str | None:
    artifact_id = item[1].artifact_id
    return artifact_id if isinstance(artifact_id, str) and artifact_id else None


def _claim_reference_keys(item: tuple[LoadedClaimsFile, Any]) -> tuple[str | None, ...]:
    claim_file, claim = item
    source_paper = claim_file_source_paper(claim_file) or claim_file.filename
    keys: list[str | None] = []
    raw_id = getattr(claim, "id", None)
    if isinstance(raw_id, str) and raw_id:
        keys.append(raw_id)
        keys.append(
            f"{normalize_identity_namespace(str(source_paper))}:"
            f"{normalize_logical_value(raw_id)}"
        )
    for logical_id in getattr(claim, "logical_ids", ()):
        keys.append(logical_id.formatted)
        keys.append(logical_id.value)
    return tuple(keys)


def foreign_keys_from_context(context: CompilationContext) -> CrossFamilyReferenceIndex:
    concept_index = ReferenceIndex(
        family="concept",
        records_by_id=MappingProxyType(dict(context.concepts_by_id)),
        lookup=context.concept_lookup,
    )
    claim_index = ReferenceIndex(
        family="claim",
        records_by_id=MappingProxyType({}),
        lookup=context.claim_lookup,
    )
    form_index = ReferenceIndex(
        family="form",
        records_by_id=MappingProxyType(dict(context.form_registry)),
        lookup=MappingProxyType({
            name: (name,)
            for name in context.form_registry
        }),
    )
    context_index = ReferenceIndex(
        family="context",
        records_by_id=MappingProxyType({
            context_id: context_id
            for context_id in context.context_ids
        }),
        lookup=MappingProxyType({
            context_id: (context_id,)
            for context_id in context.context_ids
        }),
    )
    return CrossFamilyReferenceIndex(
        families=MappingProxyType({
            "concept": cast(ReferenceIndex[object], concept_index),
            "claim": cast(ReferenceIndex[object], claim_index),
            "form": cast(ReferenceIndex[object], form_index),
            "context": cast(ReferenceIndex[object], context_index),
        })
    )


def resolve_concept_id(concept_ref: object, context: CompilationContext) -> str | None:
    return foreign_keys_from_context(context).resolve_id("concept", concept_ref)


def concept_exists(concept_ref: object, context: CompilationContext) -> bool:
    return foreign_keys_from_context(context).exists("concept", concept_ref)


def claim_exists(claim_ref: object, context: CompilationContext) -> bool:
    return foreign_keys_from_context(context).exists("claim", claim_ref)


def concept_form_definition(
    concept_ref: object,
    context: CompilationContext,
) -> FormDefinition | None:
    concept_id = resolve_concept_id(concept_ref, context)
    if concept_id is None:
        return None
    record = context.concepts_by_id.get(concept_id)
    if record is None:
        return None
    form_definition = context.form_registry.get(record.form)
    return form_definition if isinstance(form_definition, FormDefinition) else None


def _concept_match_kind(
    raw_text: str,
    resolved_id: str,
    record: object,
) -> tuple[str | None, str | None]:
    if raw_text == resolved_id:
        return "artifact_id", raw_text
    if not isinstance(record, ConceptRecord):
        return None, None
    if record.canonical_name == raw_text:
        return "canonical_name", raw_text
    for logical_id in record.logical_ids:
        if logical_id.formatted == raw_text:
            return "logical_id", raw_text
        if logical_id.value == raw_text:
            return "logical_value", raw_text
    for alias in record.aliases:
        if alias.name == raw_text:
            return "alias", raw_text
    return None, None


def resolve_concept_reference(
    concept_ref: object,
    context: CompilationContext,
) -> ReferenceResolution | None:
    return foreign_keys_from_context(context).family("concept").resolve(
        concept_ref,
        match_kind=_concept_match_kind,
    )


def resolve_claim_reference(
    claim_ref: object,
    context: CompilationContext,
    normalized_claim_files: list[LoadedClaimsFile],
) -> ReferenceResolution | None:
    return foreign_keys_from_context(context).family("claim").resolve(
        claim_ref,
        match_kind=lambda raw_text, resolved_id, record: _claim_match_kind(
            raw_text,
            resolved_id,
            normalized_claim_files,
        ),
    )


def _claim_match_kind(
    raw_text: str,
    resolved_id: str,
    normalized_claim_files: list[LoadedClaimsFile],
) -> tuple[str | None, str | None]:
    if raw_text == resolved_id:
        return "artifact_id", raw_text
    for claim_file in normalized_claim_files:
        for claim in claim_file_claims(claim_file):
            if claim.artifact_id != resolved_id:
                continue
            for logical_id in claim.logical_ids:
                if logical_id.formatted == raw_text:
                    return "logical_id", raw_text
                if logical_id.value == raw_text:
                    return "logical_value", raw_text
            break
    return None, None
