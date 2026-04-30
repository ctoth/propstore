from __future__ import annotations

from propstore.provenance.records import (
    ExternalInferenceProvenanceRecord,
    ExternalStatementAttitude,
    ExternalStatementProvenanceRecord,
    ImportRunProvenanceRecord,
    LicenseProvenanceRecord,
    ProjectionFrameProvenanceRecord,
    SourceVersionProvenanceRecord,
)


def _source() -> SourceVersionProvenanceRecord:
    return SourceVersionProvenanceRecord(
        source_id="urn:source:paper",
        version_id="v1",
        content_hash="sha256:abc",
        retrieved_at="2026-04-30T00:00:00Z",
        retrieval_uri="https://example.test/paper.pdf",
    )


def _license() -> LicenseProvenanceRecord:
    return LicenseProvenanceRecord(
        license_id="urn:license:cc-by",
        label="CC BY",
        uri="https://creativecommons.org/licenses/by/4.0/",
    )


def _graph(document: dict) -> list[dict]:
    assert document["@context"]["prov"] == "http://www.w3.org/ns/prov#"
    graph = document["@graph"]
    assert isinstance(graph, list)
    return graph


def _types(graph: list[dict]) -> set[str]:
    result: set[str] = set()
    for node in graph:
        value = node.get("@type")
        if isinstance(value, str):
            result.add(value)
        elif isinstance(value, list):
            result.update(str(item) for item in value)
    return result


def test_source_version_exports_prov_entity() -> None:
    from propstore.provenance.prov_o import to_prov_o

    graph = _graph(to_prov_o(_source()))

    assert "prov:Entity" in _types(graph)
    assert any("prov:hadPrimarySource" in node for node in graph)


def test_import_run_exports_activity_usage_and_agent() -> None:
    from propstore.provenance.prov_o import to_prov_o

    record = ImportRunProvenanceRecord(
        run_id="urn:run:1",
        importer_id="urn:agent:propstore",
        imported_at="2026-04-30T00:00:00Z",
        source=_source(),
        license=_license(),
    )
    graph = _graph(to_prov_o(record))

    assert {"prov:Activity", "prov:Agent"}.issubset(_types(graph))
    assert any("prov:used" in node for node in graph)
    assert any("prov:wasAssociatedWith" in node for node in graph)


def test_projection_frame_exports_derivation_activity() -> None:
    from propstore.provenance.prov_o import to_prov_o

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


def test_external_statement_exports_quote_or_attribution() -> None:
    from propstore.provenance.prov_o import to_prov_o

    quoted = _graph(
        to_prov_o(
            ExternalStatementProvenanceRecord(
                statement_id="urn:statement:1",
                source=_source(),
                locator="p. 7",
                attitude=ExternalStatementAttitude.QUOTED,
            )
        )
    )
    asserted = _graph(
        to_prov_o(
            ExternalStatementProvenanceRecord(
                statement_id="urn:statement:2",
                source=_source(),
                locator="p. 8",
                attitude=ExternalStatementAttitude.ASSERTED,
                authority_id="urn:agent:author",
            )
        )
    )

    assert any("prov:wasQuotedFrom" in node for node in quoted)
    assert any("prov:wasAttributedTo" in node for node in asserted)


def test_external_inference_exports_activity_premises_and_conclusion() -> None:
    from propstore.provenance.prov_o import to_prov_o

    graph = _graph(
        to_prov_o(
            ExternalInferenceProvenanceRecord(
                inference_id="urn:inference:1",
                engine="paper",
                inferred_at="2026-04-30T00:00:00Z",
                premise_statement_ids=("urn:statement:1", "urn:statement:2"),
                conclusion_statement_id="urn:statement:3",
            )
        )
    )

    assert "prov:Activity" in _types(graph)
    assert any("prov:used" in node for node in graph)
    assert any("prov:generated" in node for node in graph)
