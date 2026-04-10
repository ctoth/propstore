"""Typed document models for canonical claim YAML files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from propstore.document_schema import (
    DocumentStruct,
    convert_document_value,
)
from propstore.knowledge_path import KnowledgePath
from propstore.loaded import LoadedDocument, LoadedEntry


def _source_label(filename: str, source_path: KnowledgePath | None) -> str:
    if source_path is None:
        return filename
    rendered = source_path.as_posix()
    return rendered if rendered else filename


class ClaimLogicalIdDocument(DocumentStruct):
    namespace: str
    value: str
    confidence: float | int | None = None
    pass_number: int | None = None

    @property
    def formatted(self) -> str:
        return f"{self.namespace}:{self.value}"

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "namespace": self.namespace,
            "value": self.value,
        }
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        if self.pass_number is not None:
            payload["pass_number"] = self.pass_number
        return payload


class ClaimSourceDocument(DocumentStruct):
    paper: str
    extraction_date: str | None = None
    extraction_model: str | None = None
    extraction_prompt_hash: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"paper": self.paper}
        if self.extraction_date is not None:
            payload["extraction_date"] = self.extraction_date
        if self.extraction_model is not None:
            payload["extraction_model"] = self.extraction_model
        if self.extraction_prompt_hash is not None:
            payload["extraction_prompt_hash"] = self.extraction_prompt_hash
        return payload


class ProvenanceDocument(DocumentStruct):
    page: int
    paper: str | None = None
    figure: str | None = None
    quote_fragment: str | None = None
    section: str | None = None
    table: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"page": self.page}
        if self.paper is not None:
            payload["paper"] = self.paper
        if self.figure is not None:
            payload["figure"] = self.figure
        if self.quote_fragment is not None:
            payload["quote_fragment"] = self.quote_fragment
        if self.section is not None:
            payload["section"] = self.section
        if self.table is not None:
            payload["table"] = self.table
        return payload


class FitStatisticsDocument(DocumentStruct):
    r: float | int | None = None
    r_sd: float | int | None = None
    slope: float | int | None = None
    slope_sd: float | int | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.r is not None:
            payload["r"] = self.r
        if self.r_sd is not None:
            payload["r_sd"] = self.r_sd
        if self.slope is not None:
            payload["slope"] = self.slope
        if self.slope_sd is not None:
            payload["slope_sd"] = self.slope_sd
        return payload


class VariableBindingDocument(DocumentStruct):
    concept: str
    symbol: str | None = None
    role: str | None = None
    name: str | None = None

    @property
    def binding_name(self) -> str | None:
        if self.name is not None:
            return self.name
        return self.symbol

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"concept": self.concept}
        if self.symbol is not None:
            payload["symbol"] = self.symbol
        if self.role is not None:
            payload["role"] = self.role
        if self.name is not None:
            payload["name"] = self.name
        return payload


class ParameterBindingDocument(DocumentStruct):
    name: str
    concept: str
    note: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "concept": self.concept,
        }
        if self.note is not None:
            payload["note"] = self.note
        return payload


class ResolutionDocument(DocumentStruct):
    method: str
    embedding_distance: float | int | None = None
    embedding_model: str | None = None
    model: str | None = None
    pass_number: int | None = None
    confidence: float | int | None = None
    opinion_belief: float | int | None = None
    opinion_disbelief: float | int | None = None
    opinion_uncertainty: float | int | None = None
    opinion_base_rate: float | int | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"method": self.method}
        if self.embedding_distance is not None:
            payload["embedding_distance"] = self.embedding_distance
        if self.embedding_model is not None:
            payload["embedding_model"] = self.embedding_model
        if self.model is not None:
            payload["model"] = self.model
        if self.pass_number is not None:
            payload["pass_number"] = self.pass_number
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        if self.opinion_belief is not None:
            payload["opinion_belief"] = self.opinion_belief
        if self.opinion_disbelief is not None:
            payload["opinion_disbelief"] = self.opinion_disbelief
        if self.opinion_uncertainty is not None:
            payload["opinion_uncertainty"] = self.opinion_uncertainty
        if self.opinion_base_rate is not None:
            payload["opinion_base_rate"] = self.opinion_base_rate
        return payload


class StanceDocument(DocumentStruct):
    type: str
    target: str
    conditions_differ: str | None = None
    note: str | None = None
    resolution: ResolutionDocument | None = None
    strength: str | None = None
    target_justification_id: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": self.type,
            "target": self.target,
        }
        if self.conditions_differ is not None:
            payload["conditions_differ"] = self.conditions_differ
        if self.note is not None:
            payload["note"] = self.note
        if self.resolution is not None:
            payload["resolution"] = self.resolution.to_payload()
        if self.strength is not None:
            payload["strength"] = self.strength
        if self.target_justification_id is not None:
            payload["target_justification_id"] = self.target_justification_id
        return payload


class ClaimDocument(DocumentStruct):
    artifact_id: str | None = None
    artifact_code: str | None = None
    logical_ids: tuple[ClaimLogicalIdDocument, ...] = ()
    version_id: str | None = None
    type: str | None = None
    provenance: ProvenanceDocument | None = None
    id: str | None = None
    body: str | None = None
    concept: str | None = None
    concepts: tuple[str, ...] = ()
    conditions: tuple[str, ...] = ()
    confidence: float | int | None = None
    context: str | None = None
    equations: tuple[str, ...] = ()
    expression: str | None = None
    fit: FitStatisticsDocument | None = None
    listener_population: str | None = None
    lower_bound: float | int | None = None
    measure: str | None = None
    methodology: str | None = None
    name: str | None = None
    notes: str | None = None
    parameters: tuple[ParameterBindingDocument, ...] = ()
    sample_size: int | None = None
    stage: str | None = None
    stances: tuple[StanceDocument, ...] = ()
    statement: str | None = None
    sympy: str | None = None
    target_concept: str | None = None
    uncertainty: float | int | None = None
    uncertainty_type: str | None = None
    unit: str | None = None
    upper_bound: float | int | None = None
    value: float | int | None = None
    variables: tuple[VariableBindingDocument, ...] | dict[str, str] = ()

    @property
    def primary_logical_id(self) -> str | None:
        if not self.logical_ids:
            return None
        return self.logical_ids[0].formatted

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.artifact_id is not None:
            payload["artifact_id"] = self.artifact_id
        if self.artifact_code is not None:
            payload["artifact_code"] = self.artifact_code
        if self.logical_ids:
            payload["logical_ids"] = [logical_id.to_payload() for logical_id in self.logical_ids]
        if self.version_id is not None:
            payload["version_id"] = self.version_id
        if self.type is not None:
            payload["type"] = self.type
        if self.provenance is not None:
            payload["provenance"] = self.provenance.to_payload()
        if self.id is not None:
            payload["id"] = self.id
        if self.body is not None:
            payload["body"] = self.body
        if self.concept is not None:
            payload["concept"] = self.concept
        if self.concepts:
            payload["concepts"] = list(self.concepts)
        if self.conditions:
            payload["conditions"] = list(self.conditions)
        if self.confidence is not None:
            payload["confidence"] = self.confidence
        if self.context is not None:
            payload["context"] = self.context
        if self.equations:
            payload["equations"] = list(self.equations)
        if self.expression is not None:
            payload["expression"] = self.expression
        if self.fit is not None:
            payload["fit"] = self.fit.to_payload()
        if self.listener_population is not None:
            payload["listener_population"] = self.listener_population
        if self.lower_bound is not None:
            payload["lower_bound"] = self.lower_bound
        if self.measure is not None:
            payload["measure"] = self.measure
        if self.methodology is not None:
            payload["methodology"] = self.methodology
        if self.name is not None:
            payload["name"] = self.name
        if self.notes is not None:
            payload["notes"] = self.notes
        if self.parameters:
            payload["parameters"] = [
                parameter.to_payload()
                for parameter in self.parameters
            ]
        if self.sample_size is not None:
            payload["sample_size"] = self.sample_size
        if self.stage is not None:
            payload["stage"] = self.stage
        if self.stances:
            payload["stances"] = [stance.to_payload() for stance in self.stances]
        if self.statement is not None:
            payload["statement"] = self.statement
        if self.sympy is not None:
            payload["sympy"] = self.sympy
        if self.target_concept is not None:
            payload["target_concept"] = self.target_concept
        if self.uncertainty is not None:
            payload["uncertainty"] = self.uncertainty
        if self.uncertainty_type is not None:
            payload["uncertainty_type"] = self.uncertainty_type
        if self.unit is not None:
            payload["unit"] = self.unit
        if self.upper_bound is not None:
            payload["upper_bound"] = self.upper_bound
        if self.value is not None:
            payload["value"] = self.value
        if self.variables:
            if isinstance(self.variables, dict):
                payload["variables"] = dict(self.variables)
            else:
                payload["variables"] = [variable.to_payload() for variable in self.variables]
        return payload


class ClaimsFileDocument(DocumentStruct):
    source: ClaimSourceDocument
    claims: tuple[ClaimDocument, ...]
    stage: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source": self.source.to_payload(),
            "claims": [claim.to_payload() for claim in self.claims],
        }
        if self.stage is not None:
            payload["stage"] = self.stage
        return payload


class LoadedClaimFile(LoadedDocument[ClaimsFileDocument]):
    """Typed claim-file envelope."""

    @classmethod
    def from_payload(
        cls,
        *,
        filename: str,
        source_path: KnowledgePath | Path | None,
        data: dict[str, Any],
        knowledge_root: KnowledgePath | Path | None = None,
    ) -> LoadedClaimFile:
        label = filename if source_path is None else str(source_path)
        document = convert_document_value(
            data,
            ClaimsFileDocument,
            source=label,
        )
        return cls(
            filename=filename,
            source_path=source_path,
            knowledge_root=knowledge_root,
            document=document,
        )

    @classmethod
    def from_loaded_document(
        cls,
        document: LoadedDocument[ClaimsFileDocument],
    ) -> LoadedClaimFile:
        return cls(
            filename=document.filename,
            source_path=document.source_path,
            knowledge_root=document.knowledge_root,
            document=document.document,
        )

    @classmethod
    def from_loaded_entry(cls, entry: LoadedEntry) -> LoadedClaimFile:
        document = convert_document_value(
            entry.data,
            ClaimsFileDocument,
            source=_source_label(entry.filename, entry.source_path),
        )
        return cls(
            filename=entry.filename,
            source_path=entry.source_path,
            knowledge_root=entry.knowledge_root,
            document=document,
        )

    @property
    def claims(self) -> tuple[ClaimDocument, ...]:
        return self.document.claims

    @property
    def source_paper(self) -> str:
        return self.document.source.paper

    @property
    def stage(self) -> str | None:
        return self.document.stage

    @property
    def data(self) -> dict[str, Any]:
        return self.document.to_payload()

    @data.setter
    def data(self, value: dict[str, Any]) -> None:
        self.document = convert_document_value(
            value,
            ClaimsFileDocument,
            source=_source_label(self.filename, self.source_path),
        )

    def to_loaded_entry(self) -> LoadedEntry:
        return LoadedEntry(
            filename=self.filename,
            source_path=self.source_path,
            knowledge_root=self.knowledge_root,
            data=self.document.to_payload(),
        )


ClaimFileInput = LoadedClaimFile | LoadedEntry


def coerce_loaded_claim_file(claim_file: ClaimFileInput) -> LoadedClaimFile:
    if isinstance(claim_file, LoadedClaimFile):
        return claim_file
    return LoadedClaimFile.from_loaded_entry(claim_file)


def coerce_loaded_claim_files(
    claim_files: list[ClaimFileInput],
) -> list[LoadedClaimFile]:
    return [coerce_loaded_claim_file(claim_file) for claim_file in claim_files]
