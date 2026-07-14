from __future__ import annotations

from typing import Any

from propstore.provenance import (
    Provenance,
    ProvenanceStatus,
    ProvenanceWitness,
)
from propstore.provenance.prov_o import provenance_to_prov_o, to_prov_o
from propstore.provenance.records import ProjectionFrameProvenanceRecord


def _graph(document: dict[str, Any]) -> list[dict[str, Any]]:
    assert document["@context"]["prov"] == "http://www.w3.org/ns/prov#"
    graph = document["@graph"]
    assert isinstance(graph, list)
    return graph


def _types(graph: list[dict[str, Any]]) -> set[str]:
    result: set[str] = set()
    for node in graph:
        value = node.get("@type")
        if isinstance(value, str):
            result.add(value)
        elif isinstance(value, list):
            result.update(str(item) for item in value)
    return result


def _node(graph: list[dict[str, Any]], node_type: str) -> dict[str, Any]:
    matches = [node for node in graph if node.get("@type") == node_type]
    assert len(matches) == 1, f"expected exactly one {node_type} node"
    return matches[0]


def test_projection_frame_exports_derivation_activity() -> None:
    graph = _graph(
        to_prov_o(
            ProjectionFrameProvenanceRecord(
                frame_id="urn:frame:1",
                backend="aspic",
                projected_at="2026-04-30T00:00:00Z",
                source_assertion_ids=("urn:assertion:1", "urn:assertion:2"),
            )
        )
    )

    assert "prov:Activity" in _types(graph)
    assert any("prov:wasDerivedFrom" in node for node in graph)


def test_provenance_exports_entity_with_status_and_lineage() -> None:
    graph = _graph(
        provenance_to_prov_o(
            Provenance(
                status=ProvenanceStatus.STATED,
                graph_name="urn:propstore:repository-import:abc",
                derived_from=("def456",),
                operations=("repository-import",),
            )
        )
    )

    entity = _node(graph, "prov:Entity")
    assert entity["@id"] == "urn:propstore:repository-import:abc"
    assert entity["ps:status"] == "stated"
    assert entity["prov:wasDerivedFrom"] == [{"@id": "def456"}]
    assert entity["ps:operation"] == ["repository-import"]


def test_provenance_witnesses_export_as_activity_agent_and_source_pin() -> None:
    """A witness is the activity that generated the entity (was silently dropped).

    Before 2026-07-14 ``provenance_to_prov_o`` emitted only the entity, so the
    PROV-O export of a stored provenance had no agent, no activity, and no source
    — the three things PROV-O exists to record.
    """

    graph = _graph(
        provenance_to_prov_o(
            Provenance(
                status=ProvenanceStatus.STATED,
                graph_name="urn:propstore:repository-import:abc",
                witnesses=(
                    ProvenanceWitness(
                        asserter="urn:propstore:agent:repository-import",
                        timestamp="2026-07-14T00:00:00Z",
                        source_artifact_code="/repos/upstream/knowledge",
                        method="repository-import",
                        source_version_id="def456",
                        source_content_hash="git:def456",
                    ),
                ),
            )
        )
    )

    assert {"prov:Entity", "prov:Activity", "prov:Agent"}.issubset(_types(graph))

    activity = _node(graph, "prov:Activity")
    assert activity["prov:startedAtTime"] == "2026-07-14T00:00:00Z"
    assert activity["ps:method"] == "repository-import"
    assert activity["ps:sourceArtifactCode"] == "/repos/upstream/knowledge"
    assert activity["ps:versionId"] == "def456"
    assert activity["ps:contentHash"] == "git:def456"
    assert activity["prov:wasAssociatedWith"] == {
        "@id": "urn:propstore:agent:repository-import"
    }

    agent = _node(graph, "prov:Agent")
    assert agent["@id"] == "urn:propstore:agent:repository-import"

    entity = _node(graph, "prov:Entity")
    assert entity["prov:wasGeneratedBy"] == [{"@id": activity["@id"]}]


def test_non_uri_asserter_stays_a_literal_instead_of_a_fabricated_id() -> None:
    """``asserter`` is free-form (``propstore`` in ``app/project_init.py``).

    A JSON-LD ``@id`` must be an IRI, so a bare name is carried as a literal
    rather than minted into an identifier it never had.
    """

    graph = _graph(
        provenance_to_prov_o(
            Provenance(
                status=ProvenanceStatus.STATED,
                graph_name="urn:propstore:seed:1",
                witnesses=(
                    ProvenanceWitness(
                        asserter="propstore",
                        timestamp="2026-04-17T00:00:00Z",
                        source_artifact_code="ps:resource:phase3-seed",
                        method="packaged-resource",
                    ),
                ),
            )
        )
    )

    assert "prov:Agent" not in _types(graph)
    activity = _node(graph, "prov:Activity")
    assert activity["ps:asserter"] == "propstore"
    assert "prov:wasAssociatedWith" not in activity
    assert "ps:versionId" not in activity
    assert "ps:contentHash" not in activity
