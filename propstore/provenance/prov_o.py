"""One-way PROV-O JSON-LD export for typed provenance.

Moreau and Missier 2013 define PROV-O's core classes around entities,
activities, and agents. Propstore keeps its internal model typed and projects to
these PROV-O nodes only at export boundaries; nothing reads PROV-O back.

The stored carrier is :class:`~propstore.provenance.Provenance`, so
:func:`provenance_to_prov_o` is the export that matters: the named graph becomes
a ``prov:Entity`` and each of its witnesses becomes the ``prov:Activity`` that
generated it, associated with the ``prov:Agent`` that asserted it.
:class:`~propstore.provenance.records.ProjectionFrameProvenanceRecord` is
exported too because the argumentation projection boundary holds it as a typed
field rather than as provenance on a git note.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from propstore.provenance._jsonld import JSONLD_CONTEXT as _CONTEXT
from propstore.provenance._jsonld import URI_SCHEME_PREFIXES as _URI_PREFIXES
from propstore.provenance.records import ProjectionFrameProvenanceRecord

if TYPE_CHECKING:
    from propstore.provenance import Provenance, ProvenanceWitness


def to_prov_o(record: ProjectionFrameProvenanceRecord) -> dict[str, Any]:
    """Export one projection frame as a PROV-O activity document."""

    return _document(_projection_frame_nodes(record))


def provenance_to_prov_o(provenance: Provenance) -> dict[str, Any]:
    """Export a stored provenance named graph as a PROV-O document.

    Each witness is projected as the activity that generated the entity. A
    witness's ``asserter`` and ``source_artifact_code`` are free-form (an agent
    urn, but also bare names like ``propstore``, branch names, and filesystem
    paths), and a JSON-LD ``@id`` must be an IRI — so the asserter is linked as a
    ``prov:Agent`` node only when it is one, and carried as a literal otherwise.
    Nothing here fabricates an identifier for a value that does not have one.
    """

    graph_name = provenance.graph_name or "urn:propstore:provenance:anonymous"
    entity: dict[str, Any] = {
        "@id": graph_name,
        "@type": "prov:Entity",
        "ps:status": provenance.status.value,
    }
    if provenance.derived_from:
        entity["prov:wasDerivedFrom"] = [
            {"@id": value} for value in provenance.derived_from
        ]
    if provenance.operations:
        entity["ps:operation"] = list(provenance.operations)

    nodes: list[dict[str, Any]] = [entity]
    generated_by: list[dict[str, str]] = []
    for index, witness in enumerate(provenance.witnesses):
        activity_id = f"{graph_name}#witness-{index}"
        generated_by.append({"@id": activity_id})
        nodes.extend(_witness_nodes(witness, activity_id=activity_id))
    if generated_by:
        entity["prov:wasGeneratedBy"] = generated_by
    return _document(nodes)


def _witness_nodes(
    witness: ProvenanceWitness,
    *,
    activity_id: str,
) -> list[dict[str, Any]]:
    activity: dict[str, Any] = {
        "@id": activity_id,
        "@type": "prov:Activity",
        "prov:startedAtTime": witness.timestamp,
        "ps:method": witness.method,
        "ps:sourceArtifactCode": witness.source_artifact_code,
    }
    if witness.source_version_id is not None:
        activity["ps:versionId"] = witness.source_version_id
    if witness.source_content_hash is not None:
        activity["ps:contentHash"] = witness.source_content_hash
    if not witness.asserter.startswith(_URI_PREFIXES):
        activity["ps:asserter"] = witness.asserter
        return [activity]
    activity["prov:wasAssociatedWith"] = {"@id": witness.asserter}
    return [activity, {"@id": witness.asserter, "@type": "prov:Agent"}]


def _document(graph: list[dict[str, Any]]) -> dict[str, Any]:
    return {"@context": dict(_CONTEXT), "@graph": graph}


def _projection_frame_nodes(
    record: ProjectionFrameProvenanceRecord,
) -> list[dict[str, Any]]:
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
