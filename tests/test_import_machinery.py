from __future__ import annotations

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from propstore.importing.machinery import (
    AuthoredAssertionSurface,
    EquivalenceWitnessStore,
    ExternalInferenceSurface,
    ImportAuthoredFormLens,
    ImportCompiler,
    SurfaceRoleBinding,
)


def _surface() -> AuthoredAssertionSurface:
    return AuthoredAssertionSurface(
        source_id="https://example.test/sources/table-1",
        source_label="Example Table",
        source_version_id="v1",
        source_content_hash="sha256:source",
        retrieval_uri="https://example.test/sources/table-1.csv",
        license_id="https://example.test/licenses/cc-by-4.0",
        license_label="CC BY 4.0",
        license_uri="https://creativecommons.org/licenses/by/4.0/",
        import_run_id="urn:propstore:import-run:table-1",
        importer_id="urn:propstore:importer:fixture",
        imported_at="2026-04-26T01:00:00Z",
        external_statement_id="urn:example:statement:row-7",
        external_statement_locator="row=7",
        external_inference=ExternalInferenceSurface(
            inference_id="urn:example:inference:row-7",
            engine="fixture-rule",
            inferred_at="2026-04-26T01:00:01Z",
            premise_statement_ids=("urn:example:statement:row-5",),
        ),
        mapping_policy_id="urn:propstore:mapping-policy:non-nl-fixture",
        mapping_policy_label="non-NL fixture mapping",
        relation_id="ps:concept:relation:measured-value",
        role_bindings=(
            SurfaceRoleBinding(role="subject", value="ps:concept:temperature"),
            SurfaceRoleBinding(role="value", value="293.15"),
            SurfaceRoleBinding(role="unit", value="K"),
        ),
        context_id="ps:context:lab-a",
        microtheory_id="cyc:Microtheory:LabA",
        lifting_rule_id="urn:propstore:lifting-rule:lab-a",
        condition_id="ps:condition:unconditional",
        condition_registry_fingerprint="registry:unconditional",
    )


def test_import_compiler_builds_situated_assertion_with_external_contract() -> None:
    form = ImportAuthoredFormLens().get(_surface())

    compiled = ImportCompiler().compile(form)

    assert str(compiled.assertion.assertion_id).startswith("ps:assertion:")
    assert str(compiled.assertion.relation.concept_id) == "ps:concept:relation:measured-value"
    assert compiled.assertion.role_bindings.identity_payload() == (
        ("subject", "ps:concept:temperature"),
        ("unit", "K"),
        ("value", "293.15"),
    )
    assert str(compiled.assertion.context.id) == "ps:context:lab-a"
    assert str(compiled.assertion.condition.id) == "ps:condition:unconditional"
    assert str(compiled.assertion.provenance_ref.graph_name).startswith(
        "urn:propstore:import-provenance:"
    )

    metadata = compiled.import_metadata
    assert metadata.source.source_id == "https://example.test/sources/table-1"
    assert metadata.source.version_id == "v1"
    assert metadata.source.content_hash == "sha256:source"
    assert metadata.import_run.run_id == "urn:propstore:import-run:table-1"
    assert metadata.external_statement.statement_id == "urn:example:statement:row-7"
    assert metadata.external_inference is not None
    assert metadata.external_inference.inference_id == "urn:example:inference:row-7"
    assert metadata.mapping_policy.policy_id == "urn:propstore:mapping-policy:non-nl-fixture"
    assert metadata.context_mapping.microtheory_id == "cyc:Microtheory:LabA"


def test_equivalence_witness_store_composes_without_identity_collapse() -> None:
    store = EquivalenceWitnessStore()
    left = store.record_witness(
        "urn:example:candidate:a",
        "urn:example:candidate:b",
        mapping_policy_id="urn:propstore:mapping-policy:test",
        evidence_statement_ids=("urn:example:statement:1",),
    )
    right = store.record_witness(
        "urn:example:candidate:b",
        "urn:example:candidate:c",
        mapping_policy_id="urn:propstore:mapping-policy:test",
        evidence_statement_ids=("urn:example:statement:2",),
    )

    composed = store.compose(left.witness_id, right.witness_id)

    assert composed is not None
    assert composed.candidate_ids == (
        "urn:example:candidate:a",
        "urn:example:candidate:c",
    )
    assert composed.status == "derived_unresolved"
    assert composed.source_witness_ids == (left.witness_id, right.witness_id)
    assert store.identity_for("urn:example:candidate:a") == "urn:example:candidate:a"
    assert store.identity_for("urn:example:candidate:b") == "urn:example:candidate:b"
    assert store.identity_for("urn:example:candidate:c") == "urn:example:candidate:c"


_token = st.from_regex(r"[a-z][a-z0-9_]{0,8}", fullmatch=True)
_uri_token = st.from_regex(r"[a-z][a-z0-9]{0,8}", fullmatch=True)


@settings(deadline=None)
@given(
    relation=_token,
    context=_token,
    microtheory=_token,
    role=_token,
    value=_token,
)
def test_surface_authored_form_lens_laws(
    relation: str,
    context: str,
    microtheory: str,
    role: str,
    value: str,
) -> None:
    lens = ImportAuthoredFormLens()
    surface = _surface().with_mapping(
        relation_id=f"ps:concept:relation:{relation}",
        context_id=f"ps:context:{context}",
        microtheory_id=f"cyc:Microtheory:{microtheory}",
        role_bindings=(SurfaceRoleBinding(role=role, value=value),),
    )

    form = lens.get(surface)

    assert lens.put(form, surface) == surface
    assert lens.get(lens.put(form, _surface())) == form


@settings(deadline=None)
@given(first=_uri_token, middle=_uri_token, last=_uri_token)
def test_equivalence_witness_composition_keeps_candidates_distinct(
    first: str,
    middle: str,
    last: str,
) -> None:
    store = EquivalenceWitnessStore()
    a = f"urn:example:candidate:{first}"
    b = f"urn:example:candidate:{middle}"
    c = f"urn:example:candidate:{last}"
    assume(len({a, b, c}) == 3)
    witness_ab = store.record_witness(
        a,
        b,
        mapping_policy_id="urn:propstore:mapping-policy:test",
        evidence_statement_ids=("urn:example:statement:1",),
    )
    witness_bc = store.record_witness(
        b,
        c,
        mapping_policy_id="urn:propstore:mapping-policy:test",
        evidence_statement_ids=("urn:example:statement:2",),
    )

    composed = store.compose(witness_ab.witness_id, witness_bc.witness_id)

    assert composed is not None
    assert set(composed.candidate_ids) == {a, c}
    assert store.identity_for(a) == a
    assert store.identity_for(b) == b
    assert store.identity_for(c) == c
