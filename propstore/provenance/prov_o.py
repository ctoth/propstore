"""One-way PROV-O JSON-LD export for typed provenance records.

Moreau and Missier 2013 define PROV-O's core classes around entities,
activities, and agents. Propstore keeps its internal mutation model typed and
projects to these PROV-O nodes only at export boundaries.
"""

from __future__ import annotations

from typing import Any

from propstore.provenance.records import (
    ExternalInferenceProvenanceRecord,
    ExternalStatementAttitude,
    ExternalStatementProvenanceRecord,
    ImportRunProvenanceRecord,
    LicenseProvenanceRecord,
    ProjectionFrameProvenanceRecord,
    SourceVersionProvenanceRecord,
)

_CONTEXT = {
    "ps": "https://prop.store/ns#",
    "prov": "http://www.w3.org/ns/prov#",
    "swp": "http://www.w3.org/2004/03/trix/swp-2/",
}


def to_prov_o(record: object) -> dict[str, Any]:
    if isinstance(record, SourceVersionProvenanceRecord):
        return _document(_source_version_nodes(record))
    if isinstance(record, LicenseProvenanceRecord):
        return _document(_license_nodes(record))
    if isinstance(record, ImportRunProvenanceRecord):
        return _document(_import_run_nodes(record))
    if isinstance(record, ProjectionFrameProvenanceRecord):
        return _document(_projection_frame_nodes(record))
    if isinstance(record, ExternalStatementProvenanceRecord):
        return _document(_external_statement_nodes(record))
    if isinstance(record, ExternalInferenceProvenanceRecord):
        return _document(_external_inference_nodes(record))
    raise TypeError(f"unsupported PROV-O record type: {type(record).__name__}")


def provenance_to_prov_o(provenance: object) -> dict[str, Any]:
    payload = provenance.to_payload()  # type: ignore[attr-defined]
    graph_name = payload.get("graph_name") or "urn:propstore:provenance:anonymous"
    node: dict[str, Any] = {
        "@id": graph_name,
        "@type": "prov:Entity",
        "ps:status": payload.get("status"),
    }
    if payload.get("derived_from"):
        node["prov:wasDerivedFrom"] = [{"@id": value} for value in payload["derived_from"]]
    if payload.get("operations"):
        node["ps:operation"] = list(payload["operations"])
    return _document([node])


def _document(graph: list[dict[str, Any]]) -> dict[str, Any]:
    return {"@context": dict(_CONTEXT), "@graph": graph}


def _source_version_nodes(record: SourceVersionProvenanceRecord) -> list[dict[str, Any]]:
    node: dict[str, Any] = {
        "@id": record.source_id,
        "@type": "prov:Entity",
        "ps:versionId": record.version_id,
        "ps:contentHash": record.content_hash,
    }
    if record.retrieval_uri is not None:
        node["prov:hadPrimarySource"] = {"@id": record.retrieval_uri}
    if record.retrieved_at is not None:
        node["prov:generatedAtTime"] = record.retrieved_at
    return [node]


def _license_nodes(record: LicenseProvenanceRecord) -> list[dict[str, Any]]:
    node: dict[str, Any] = {
        "@id": record.license_id,
        "@type": "prov:Entity",
        "ps:label": record.label,
    }
    if record.uri is not None:
        node["prov:hadPrimarySource"] = {"@id": record.uri}
    return [node]


def _import_run_nodes(record: ImportRunProvenanceRecord) -> list[dict[str, Any]]:
    return [
        {
            "@id": record.run_id,
            "@type": "prov:Activity",
            "prov:startedAtTime": record.imported_at,
            "prov:used": [
                {"@id": record.source.source_id},
                {"@id": record.license.license_id},
            ],
            "prov:wasAssociatedWith": {"@id": record.importer_id},
        },
        {
            "@id": record.importer_id,
            "@type": "prov:Agent",
        },
        *_source_version_nodes(record.source),
        *_license_nodes(record.license),
    ]


def _projection_frame_nodes(record: ProjectionFrameProvenanceRecord) -> list[dict[str, Any]]:
    return [
        {
            "@id": record.frame_id,
            "@type": "prov:Activity",
            "ps:backend": record.backend,
            "prov:startedAtTime": record.projected_at,
            "prov:wasDerivedFrom": [
                {"@id": assertion_id}
                for assertion_id in record.source_assertion_ids
            ],
        }
    ]


def _external_statement_nodes(record: ExternalStatementProvenanceRecord) -> list[dict[str, Any]]:
    node: dict[str, Any] = {
        "@id": record.statement_id,
        "@type": "prov:Entity",
        "ps:locator": record.locator,
    }
    if record.attitude is ExternalStatementAttitude.QUOTED:
        node["prov:wasQuotedFrom"] = {"@id": record.source.source_id}
    else:
        node["prov:wasAttributedTo"] = {
            "@id": record.authority_id or record.source.source_id
        }
    return [node, *_source_version_nodes(record.source)]


def _external_inference_nodes(record: ExternalInferenceProvenanceRecord) -> list[dict[str, Any]]:
    return [
        {
            "@id": record.inference_id,
            "@type": "prov:Activity",
            "ps:engine": record.engine,
            "prov:startedAtTime": record.inferred_at,
            "prov:used": [
                {"@id": premise}
                for premise in record.premise_statement_ids
            ],
            "prov:generated": {"@id": record.conclusion_statement_id},
        }
    ]
