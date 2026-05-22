"""Claim-side compilation helpers for the sidecar.

Raw-id quarantine path (``reviews/2026-04-16-code-review/workstreams/
ws-z-render-gates.md`` axis-1 finding 3.1): claims whose raw ``id`` never
canonicalized are still given a ``claim_core`` row with a synthetic id
and ``build_status='blocked'``, plus a ``build_diagnostics`` row
describing why. This implements discipline rule 5 (filter at render, not
at build) — no data is refused; the render layer decides what to show.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from quire.charters import FamilyModel
from quire.references import FamilyReferenceIndex
from propstore.claims import (
    claim_file_filename,
    claim_file_stage,
)
from propstore.cel_types import CelExpr, to_cel_exprs
from propstore.compiler.ir import ClaimCompilationBundle
from propstore.core.algorithm_stage import AlgorithmStage
from propstore.families.claims.types import ClaimType
from propstore.core.conditions import (
    CheckedConditionSet,
    checked_condition_set_from_json,
    checked_condition_set_to_json,
)
from propstore.core.justifications import Justification
from propstore.core.relations import ClaimConceptLinkRole
from propstore.dimensions import DimensionalForm, normalize_to_si
from propstore.description_generator import generate_description
from propstore.families.claims.references import (
    ClaimReferenceRecord,
    build_claim_file_reference_index,
)
from propstore.families.claims.documents import claim_type_contract_for
from propstore.families.claims.stages import (
    ClaimAlgorithmVariable,
    claim_algorithm_canonical_ast,
    claim_algorithm_variable_payload,
    PromotionBlockedClaimFact,
    RawIdQuarantineRecord,
    parse_claim_algorithm_variables,
)
from propstore.families.claims.sympy_generation import derive_equation_sympy
from propstore.families.diagnostics.declaration import (
    QuarantineDiagnostic,
    compile_promotion_blocked_diagnostics,
)
from propstore.families.documents.justifications import JustificationDocument

if TYPE_CHECKING:
    from propstore.core.graph_types import ProvenanceRecord
    from propstore.core.justifications import CanonicalJustification
    from propstore.families.sources.declaration import Source


def _require_claim_type(value: object) -> ClaimType:
    if not isinstance(value, str):
        raise KeyError('claim_type')
    return ClaimType(value)


class Claim(FamilyModel):
    def concept_ids_for_role(self, role: ClaimConceptLinkRole) -> tuple[str, ...]:
        return tuple(
            str(link.concept_id)
            for link in self.concept_links
            if link.role is role
        )

    @property
    def logical_ids(self) -> tuple[Mapping[str, object], ...]:
        if not self.logical_ids_json:
            return ()
        loaded = json.loads(self.logical_ids_json)
        if not isinstance(loaded, list):
            raise ValueError("claim logical_ids_json must decode to a list")
        entries: list[Mapping[str, object]] = []
        for entry in loaded:
            if not isinstance(entry, Mapping):
                raise ValueError("claim logical_ids_json entries must be mappings")
            entries.append(entry)
        return tuple(entries)

    @property
    def output_concept_id(self) -> str | None:
        concept_ids = self.concept_ids_for_role(ClaimConceptLinkRole.OUTPUT)
        return concept_ids[0] if concept_ids else None

    @property
    def value_concept_id(self) -> str | None:
        return self.output_concept_id or self.target_concept

    @property
    def about_concept_ids(self) -> tuple[str, ...]:
        return self.concept_ids_for_role(ClaimConceptLinkRole.ABOUT)

    @property
    def input_concept_ids(self) -> tuple[str, ...]:
        return self.concept_ids_for_role(ClaimConceptLinkRole.INPUT)

    @property
    def target_concept_ids(self) -> tuple[str, ...]:
        return self.concept_ids_for_role(ClaimConceptLinkRole.TARGET)

    @property
    def checked_conditions(self) -> CheckedConditionSet | None:
        text_payload = self.text_payload
        if text_payload is None or not text_payload.conditions_ir:
            return None
        loaded = json.loads(text_payload.conditions_ir)
        if not isinstance(loaded, Mapping):
            raise ValueError("claim conditions_ir must decode to a mapping")
        return checked_condition_set_from_json(loaded)

    @property
    def conditions(self) -> tuple[CelExpr, ...]:
        checked_conditions = self.checked_conditions
        if checked_conditions is not None:
            return to_cel_exprs(checked_conditions.sources)
        text_payload = self.text_payload
        if text_payload is None or not text_payload.conditions_cel:
            return ()
        loaded = json.loads(text_payload.conditions_cel)
        if not isinstance(loaded, list):
            raise ValueError("claim conditions_cel must decode to a list")
        return to_cel_exprs(str(item) for item in loaded)

    @property
    def variables(self) -> tuple[ClaimAlgorithmVariable, ...]:
        algorithm_payload = self.algorithm_payload
        if algorithm_payload is None:
            return ()
        return parse_claim_algorithm_variables(algorithm_payload.variables_json)

    def variable_bindings(self) -> dict[str, str]:
        bindings: dict[str, str] = {}
        for variable in self.variables:
            if variable.concept_id is None:
                continue
            name = variable.name or variable.symbol
            if name:
                bindings[name] = str(variable.concept_id)
        return bindings

    def variable_concept_ids(self) -> tuple[str, ...]:
        return tuple(
            str(variable.concept_id)
            for variable in self.variables
            if variable.concept_id is not None
        )

    def variable_payload(self) -> list[dict[str, Any]] | None:
        if not self.variables:
            return None
        return [claim_algorithm_variable_payload(variable) for variable in self.variables]

    def to_source_claim_payload(self) -> dict[str, Any]:
        numeric_payload = self.numeric_payload
        text_payload = self.text_payload
        algorithm_payload = self.algorithm_payload
        source: dict[str, Any] = {
            "id": self.id,
            "type": self.type.value,
            "target_concept": self.target_concept,
            "context": {"id": self.context_id},
            "source_paper": self.source_paper,
            "provenance": json.loads(self.provenance_json)
            if self.provenance_json
            else None,
        }
        if self.type is ClaimType.PARAMETER and self.output_concept_id is not None:
            source["output_concept"] = self.output_concept_id
        if (
            self.type is ClaimType.MEASUREMENT
            and self.output_concept_id is not None
            and self.target_concept is None
        ):
            source["target_concept"] = self.output_concept_id
        if self.type is ClaimType.ALGORITHM and self.output_concept_id is not None:
            source["output_concept"] = self.output_concept_id
        if numeric_payload is not None:
            source.update(
                value=numeric_payload.value,
                lower_bound=numeric_payload.lower_bound,
                upper_bound=numeric_payload.upper_bound,
                uncertainty=numeric_payload.uncertainty,
                uncertainty_type=numeric_payload.uncertainty_type,
                sample_size=numeric_payload.sample_size,
                unit=numeric_payload.unit,
            )
        if text_payload is not None:
            source.update(
                conditions=json.loads(text_payload.conditions_cel)
                if text_payload.conditions_cel
                else [],
                statement=text_payload.statement,
                expression=text_payload.expression,
                sympy=text_payload.sympy_generated,
                name=text_payload.name,
                measure=text_payload.measure,
                listener_population=text_payload.listener_population,
                methodology=text_payload.methodology,
                notes=text_payload.notes,
            )
        if algorithm_payload is not None:
            source.update(
                body=algorithm_payload.body,
                stage=algorithm_payload.algorithm_stage,
            )
            variable_payload = self.variable_payload()
            if variable_payload is not None:
                source["variables"] = variable_payload
        return {key: value for key, value in source.items() if value is not None}


class ClaimConceptLink(FamilyModel):
    pass


class ClaimNumericPayload(FamilyModel):
    pass


class ClaimTextPayload(FamilyModel):
    pass


class ClaimAlgorithmPayload(FamilyModel):
    pass


class ClaimSourceAssertion(FamilyModel):
    pass


@dataclass(frozen=True)
class ClaimWriteModels:
    claims: tuple[Claim, ...]
    numeric_payloads: tuple[ClaimNumericPayload, ...]
    text_payloads: tuple[ClaimTextPayload, ...]
    algorithm_payloads: tuple[ClaimAlgorithmPayload, ...]
    source_assertions: tuple[ClaimSourceAssertion, ...]
    concept_links: tuple[ClaimConceptLink, ...]
    quarantine_diagnostics: tuple[QuarantineDiagnostic, ...]


@dataclass(frozen=True)
class RawIdQuarantineModels:
    claims: tuple[Claim, ...]
    diagnostics: tuple[BuildDiagnostic, ...]


@dataclass(frozen=True)
class PromotionBlockedModels:
    claims: tuple[Claim, ...]
    diagnostics: tuple[BuildDiagnostic, ...]


from propstore.families.world_charters import BuildDiagnostic, world_record


def _numeric_si_value(
    value: object,
    *,
    unit: object,
    form_definition: DimensionalForm | None,
) -> float | int | None:
    if value is None:
        return None
    if not isinstance(value, int | float) or isinstance(value, bool):
        return None
    if form_definition is None:
        return value
    if form_definition.unit_symbol is None:
        return value
    return normalize_to_si(
        float(value),
        None if unit is None else str(unit),
        form_definition,
    )


def _claim_form_definition(
    claim_doc: object,
    concept_registry: Mapping[str, Mapping[str, Any]],
    form_registry: Mapping[str, DimensionalForm] | None,
) -> DimensionalForm | None:
    if form_registry is None:
        return None
    concept_id = (
        getattr(claim_doc, "output_concept", None)
        or getattr(claim_doc, "target_concept", None)
    )
    if concept_id is None:
        return None
    concept_payload = concept_registry.get(str(concept_id))
    if not isinstance(concept_payload, Mapping):
        return None
    form_name = concept_payload.get("form")
    if not isinstance(form_name, str) or not form_name:
        return None
    return form_registry.get(form_name)


def compile_claim_models(
    claim_bundle: ClaimCompilationBundle,
    concept_registry: Mapping[str, Mapping[str, Any]],
    *,
    form_registry: Mapping[str, DimensionalForm] | None = None,
    source_slugs: Collection[str] = (),
) -> ClaimWriteModels:
    claim_seq = 0
    claim_models: list[Claim] = []
    numeric_payloads: list[ClaimNumericPayload] = []
    text_payloads: list[ClaimTextPayload] = []
    algorithm_payloads: list[ClaimAlgorithmPayload] = []
    source_assertions: list[ClaimSourceAssertion] = []
    claim_links: list[ClaimConceptLink] = []
    quarantine_diagnostics: list[QuarantineDiagnostic] = []
    seen_claim_versions: dict[str, str] = {}
    emitted_version_conflicts: set[tuple[str, str, str]] = set()
    seen_claim_link_keys: set[tuple[str, ClaimConceptLinkRole, int, str]] = set()
    claim_index = build_claim_file_reference_index(
        claim_bundle.normalized_claim_files
    )
    file_stage_by_filename: dict[str, str | None] = {
        claim_file_filename(claim_file): claim_file_stage(claim_file)
        for claim_file in claim_bundle.normalized_claim_files
    }

    for semantic_file in claim_bundle.semantic_files:
        file_stage = file_stage_by_filename.get(
            claim_file_filename(semantic_file.normalized_entry)
        )
        for semantic_claim in semantic_file.claims:
            claim_seq += 1
            claim_doc = semantic_claim.resolved_claim
            provenance = claim_doc.provenance
            provenance_payload = None if provenance is None else provenance.to_payload()
            conditions_ir = (
                json.dumps(
                    checked_condition_set_to_json(semantic_claim.checked_conditions),
                    sort_keys=True,
                )
                if semantic_claim.checked_conditions is not None
                else None
            )
            logical_ids_payload = [
                logical_id.to_payload()
                for logical_id in claim_doc.logical_ids
            ]
            source_slug = (
                semantic_claim.source_paper
                if semantic_claim.source_paper in source_slugs
                else None
            )
            claim_values: dict[str, object] = {
                "id": semantic_claim.artifact_id or claim_doc.artifact_id,
                "primary_logical_id": claim_doc.primary_logical_id or "",
                "logical_ids_json": json.dumps(logical_ids_payload),
                "version_id": claim_doc.version_id or "",
                "seq": claim_seq,
                "type": claim_doc.type,
                "target_concept": claim_doc.target_concept,
                "source_slug": source_slug,
                "source_paper": (
                    semantic_claim.source_paper
                    if provenance is None or provenance.paper is None
                    else provenance.paper
                ),
                "provenance_page": 0 if provenance is None else provenance.page,
                "provenance_json": (
                    None
                    if provenance_payload is None
                    else json.dumps(provenance_payload, sort_keys=True)
                ),
                "context_id": claim_doc.context.id,
                "premise_kind": "ordinary",
                "branch": None,
                "build_status": "ingested",
                "stage": file_stage,
                "promotion_status": None,
            }
            if file_stage is not None:
                claim_values["stage"] = file_stage
            claim_id = claim_values.get("id")
            if not isinstance(claim_id, str) or not claim_id:
                raise TypeError("compiled claim id must be a non-empty string")
            version_id = claim_values.get("version_id")
            if not isinstance(version_id, str):
                raise TypeError("compiled claim version_id must be a string")
            if claim_id in seen_claim_versions:
                existing_version = seen_claim_versions[claim_id]
                if existing_version == version_id:
                    continue
                conflict_key = (claim_id, existing_version, version_id)
                if conflict_key not in emitted_version_conflicts:
                    quarantine_diagnostics.append(
                        QuarantineDiagnostic(
                            artifact_id=claim_id,
                            kind="claim",
                            diagnostic_kind="claim_version_conflict",
                            message=(
                                f"Claim logical id {claim_id!r} appears with "
                                "multiple version_id values"
                            ),
                            file=semantic_claim.filename,
                        )
                    )
                    emitted_version_conflicts.add(conflict_key)
                continue
            form_definition = _claim_form_definition(
                claim_doc,
                concept_registry,
                form_registry,
            )
            numeric_values = {
                "claim_id": claim_id,
                "value": claim_doc.value,
                "lower_bound": claim_doc.lower_bound,
                "upper_bound": claim_doc.upper_bound,
                "uncertainty": claim_doc.uncertainty,
                "uncertainty_type": claim_doc.uncertainty_type,
                "sample_size": claim_doc.sample_size,
                "confidence": claim_doc.confidence,
                "unit": claim_doc.unit,
                "value_si": _numeric_si_value(
                    claim_doc.value,
                    unit=claim_doc.unit,
                    form_definition=form_definition,
                ),
                "lower_bound_si": _numeric_si_value(
                    claim_doc.lower_bound,
                    unit=claim_doc.unit,
                    form_definition=form_definition,
                ),
                "upper_bound_si": _numeric_si_value(
                    claim_doc.upper_bound,
                    unit=claim_doc.unit,
                    form_definition=form_definition,
                ),
            }
            sympy_derivation = (
                derive_equation_sympy(
                    authored_sympy=claim_doc.sympy,
                    expression=claim_doc.expression,
                )
                if claim_doc.type is ClaimType.EQUATION
                else None
            )
            text_values = {
                "claim_id": claim_id,
                "conditions_cel": (
                    json.dumps(list(claim_doc.conditions))
                    if claim_doc.conditions
                    else None
                ),
                "conditions_ir": conditions_ir,
                "statement": claim_doc.statement,
                "expression": claim_doc.expression,
                "sympy_generated": (
                    claim_doc.sympy
                    if sympy_derivation is None
                    else sympy_derivation.generated
                ),
                "sympy_error": (
                    None
                    if sympy_derivation is None
                    else sympy_derivation.error
                ),
                "name": claim_doc.name,
                "measure": claim_doc.measure,
                "listener_population": claim_doc.listener_population,
                "methodology": claim_doc.methodology,
                "notes": claim_doc.notes,
                "description": None,
                "auto_summary": generate_description(claim_doc, concept_registry),
            }
            algorithm_values = {
                "claim_id": claim_id,
                "body": claim_doc.body,
                "canonical_ast": claim_algorithm_canonical_ast(
                    claim_doc.body,
                    claim_doc.variables,
                ),
                "variables_json": (
                    json.dumps([
                        variable.to_payload()
                        for variable in claim_doc.variables
                    ])
                    if claim_doc.variables
                    else None
                ),
                "algorithm_stage": claim_doc.stage,
            }
            claim_model = world_record("claim_core", claim_values)
            numeric_payload = world_record("claim_numeric_payload", numeric_values)
            text_payload = world_record("claim_text_payload", text_values)
            algorithm_payload = world_record("claim_algorithm_payload", algorithm_values)
            source_assertion = ClaimSourceAssertion(
                claim_id=claim_id,
                source_assertion_id=f"ps:assertion:{claim_id}",
                ordinal=0,
            )
            claim_model.numeric_payload = numeric_payload
            claim_model.text_payload = text_payload
            claim_model.algorithm_payload = algorithm_payload
            claim_model.concept_links = []
            claim_model.source_assertions = [source_assertion]
            numeric_payload.claim = claim_model
            text_payload.claim = claim_model
            algorithm_payload.claim = claim_model
            source_assertion.claim = claim_model
            claim_models.append(claim_model)
            numeric_payloads.append(numeric_payload)
            text_payloads.append(text_payload)
            algorithm_payloads.append(algorithm_payload)
            source_assertions.append(source_assertion)
            seen_claim_versions[claim_id] = version_id
            claim_type_contract = claim_type_contract_for(claim_doc.type)
            if claim_type_contract is not None:
                for declaration in claim_type_contract.concept_links:
                    if declaration.source == "scalar":
                        if declaration.field == "output_concept":
                            linked_concepts = (
                                ((claim_doc.output_concept, None),)
                                if claim_doc.output_concept is not None
                                else ()
                            )
                        elif declaration.field == "target_concept":
                            linked_concepts = (
                                ((claim_doc.target_concept, None),)
                                if claim_doc.target_concept is not None
                                else ()
                            )
                        else:
                            raise ValueError(
                                "unsupported scalar claim concept-link field: "
                                f"{declaration.field}"
                            )
                    elif declaration.source == "list":
                        if declaration.field != "concepts":
                            raise ValueError(
                                "unsupported list claim concept-link field: "
                                f"{declaration.field}"
                            )
                        linked_concepts = tuple(
                            (concept_id, None)
                            for concept_id in claim_doc.concepts
                        )
                    elif declaration.source == "bindings":
                        if declaration.field == "variables":
                            linked_concepts = tuple(
                                (variable.concept, variable.binding_name)
                                for variable in claim_doc.variables
                            )
                        elif declaration.field == "parameters":
                            linked_concepts = tuple(
                                (parameter.concept, parameter.name)
                                for parameter in claim_doc.parameters
                            )
                        else:
                            raise ValueError(
                                "unsupported binding claim concept-link field: "
                                f"{declaration.field}"
                            )
                    else:
                        raise ValueError(
                            "unsupported claim concept-link source: "
                            f"{declaration.source}"
                        )
                    for ordinal, (concept_id, binding_name) in enumerate(linked_concepts):
                        link_key = (claim_id, declaration.role, ordinal, concept_id)
                        if link_key in seen_claim_link_keys:
                            continue
                        seen_claim_link_keys.add(link_key)
                        link = ClaimConceptLink(
                            claim_id=claim_id,
                            concept_id=concept_id,
                            role=declaration.role,
                            ordinal=ordinal,
                            binding_name=binding_name,
                        )
                        link.claim = claim_model
                        claim_model.concept_links.append(link)
                        claim_links.append(link)
    return ClaimWriteModels(
        claims=tuple(claim_models),
        numeric_payloads=tuple(numeric_payloads),
        text_payloads=tuple(text_payloads),
        algorithm_payloads=tuple(algorithm_payloads),
        source_assertions=tuple(source_assertions),
        concept_links=tuple(claim_links),
        quarantine_diagnostics=tuple(quarantine_diagnostics),
    )


def compile_authored_justification_models(
    justification_entries: Iterable[tuple[str, JustificationDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[Justification, ...]:
    models, diagnostics = compile_authored_justification_models_with_diagnostics(
        justification_entries,
        claim_index,
    )
    if diagnostics:
        raise sqlite3.IntegrityError(diagnostics[0].message)
    return models


def compile_authored_justification_models_with_diagnostics(
    justification_entries: Iterable[tuple[str, JustificationDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[tuple[Justification, ...], tuple[QuarantineDiagnostic, ...]]:
    valid_claims = set(claim_index.ids())
    models: list[Justification] = []
    diagnostics: list[QuarantineDiagnostic] = []

    for filename, justification in justification_entries:
        justification_payload = justification.to_payload()
        justification_id = justification.id
        conclusion = claim_index.resolve_id(justification.conclusion)
        if not isinstance(justification_id, str) or not justification_id:
            raise ValueError(
                f"justification artifact {filename} missing id"
            )
        if not isinstance(conclusion, str) or conclusion not in valid_claims:
            message = (
                f"justification artifact {filename} references "
                f"nonexistent conclusion '{conclusion}'"
            )
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=conclusion or justification.conclusion or filename,
                    kind="justification",
                    diagnostic_kind="justification_validation",
                    message=message,
                    file=filename,
                )
            )
            continue
        resolved_premises: list[str] = []
        missing_premise_ref: str | None = None
        for premise in justification.premises:
            resolved_premise = claim_index.resolve_id(premise)
            if (
                not isinstance(resolved_premise, str)
                or resolved_premise not in valid_claims
            ):
                if isinstance(resolved_premise, str) and resolved_premise:
                    missing_premise_ref = resolved_premise
                elif isinstance(premise, str) and premise:
                    missing_premise_ref = premise
                else:
                    missing_premise_ref = filename
                break
            resolved_premises.append(resolved_premise)
        if missing_premise_ref is not None:
            message = (
                f"justification artifact {filename} references "
                f"nonexistent premise '{missing_premise_ref}'"
            )
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=missing_premise_ref,
                    kind="justification",
                    diagnostic_kind="justification_validation",
                    message=message,
                    file=filename,
                )
            )
            continue

        provenance = justification_payload.get("provenance")
        attack_target = justification_payload.get("attack_target")
        provenance_payload: dict[str, object] = {}
        if isinstance(provenance, dict):
            provenance_payload.update(provenance)
        if isinstance(attack_target, dict):
            provenance_payload["attack_target"] = attack_target

        models.append(
            Justification(
                id=justification_id,
                justification_kind=str(justification.rule_kind or "reported_claim"),
                conclusion_claim_id=conclusion,
                premise_claim_ids=json.dumps(resolved_premises),
                source_relation_type=None,
                source_claim_id=None,
                provenance_json=json.dumps(provenance_payload)
                if provenance_payload
                else None,
                rule_strength=str(justification.rule_strength or "defeasible"),
            )
        )
    return tuple(models), tuple(diagnostics)


def compile_raw_id_quarantine_models(
    records: Sequence[RawIdQuarantineRecord],
) -> RawIdQuarantineModels:
    diagnostics: list[BuildDiagnostic] = []

    for record in records:
        diagnostics.append(
            BuildDiagnostic(
                claim_id=record.synthetic_id,
                source_kind="claim",
                source_ref=record.raw_id,
                diagnostic_kind="raw_id_input",
                severity="error",
                blocking=1,
                message=record.message,
                file=record.filename,
                detail_json=record.detail_json,
            )
        )

    return RawIdQuarantineModels(
        claims=(),
        diagnostics=tuple(diagnostics),
    )


def compile_promotion_blocked_models(
    facts: Sequence[PromotionBlockedClaimFact],
) -> PromotionBlockedModels:
    claims = tuple(
        Claim(
            id=fact.artifact_id,
            type=fact.claim_type,
            source_paper=fact.source_paper,
            provenance_page=0,
            primary_logical_id=fact.raw_id,
            logical_ids_json="[]",
            version_id="",
            seq=seq,
            branch=fact.source_branch,
            build_status="blocked",
            stage="source.promotion",
            promotion_status="blocked",
        )
        for seq, fact in enumerate(facts)
    )
    return PromotionBlockedModels(
        claims=claims,
        diagnostics=compile_promotion_blocked_diagnostics(facts),
    )
