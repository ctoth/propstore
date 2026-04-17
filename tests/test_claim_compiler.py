"""Characterization tests for the claim compiler middle-end."""

from __future__ import annotations

import yaml

from propstore.compiler.context import (
    build_compilation_context_from_paths,
    compilation_context_from_concept_registry,
)
from propstore.compiler.passes import compile_claim_files
from propstore.claims import load_claim_files
from propstore.sidecar.claim_utils import prepare_claim_insert_row
from tests.conftest import (
    make_concept_registry,
    make_parameter_claim,
    normalize_claims_payload,
    normalize_concept_payloads,
)


def test_build_compilation_context_from_paths_keeps_canonical_records_and_lookup_indices(
    tmp_path,
):
    knowledge = tmp_path / "knowledge"
    concepts_dir = knowledge / "concepts"
    forms_dir = knowledge / "forms"
    concepts_dir.mkdir(parents=True)
    forms_dir.mkdir()

    (forms_dir / "frequency.yaml").write_text(yaml.dump({
        "name": "frequency",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "Hz",
    }))

    concepts = normalize_concept_payloads([{
        "id": "concept1",
        "canonical_name": "fundamental_frequency",
        "aliases": [{"name": "F0", "source": "paper"}],
        "status": "accepted",
        "definition": "F0",
        "domain": "speech",
        "form": "frequency",
    }], default_domain="speech")
    (concepts_dir / "fundamental_frequency.yaml").write_text(
        yaml.dump(concepts[0], default_flow_style=False)
    )

    context = build_compilation_context_from_paths(concepts_dir, forms_dir)
    artifact_id = concepts[0]["artifact_id"]
    logical_id = f"{concepts[0]['logical_ids'][0]['namespace']}:{concepts[0]['logical_ids'][0]['value']}"

    assert artifact_id in context.concepts_by_id
    assert context.concepts_by_id[artifact_id].canonical_name == "fundamental_frequency"
    assert context.concept_lookup["F0"] == (artifact_id,)
    assert context.concept_lookup["fundamental_frequency"] == (artifact_id,)
    assert context.concept_lookup[logical_id] == (artifact_id,)
    assert not hasattr(context, "legacy_concept_registry")


def test_compile_claim_files_preserves_binding_provenance_for_concepts_and_stances(
    tmp_path,
):
    knowledge = tmp_path / "knowledge"
    claims_dir = knowledge / "claims"
    concepts_dir = knowledge / "concepts"
    forms_dir = knowledge / "forms"
    claims_dir.mkdir(parents=True)
    concepts_dir.mkdir()
    forms_dir.mkdir()

    (forms_dir / "frequency.yaml").write_text(yaml.dump({
        "name": "frequency",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "Hz",
    }))
    (forms_dir / "pressure.yaml").write_text(yaml.dump({
        "name": "pressure",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "Pa",
    }))

    concepts = normalize_concept_payloads([
        {
            "id": "concept1",
            "canonical_name": "fundamental_frequency",
            "aliases": [{"name": "F0", "source": "paper"}],
            "status": "accepted",
            "definition": "F0",
            "domain": "speech",
            "form": "frequency",
        },
        {
            "id": "concept2",
            "canonical_name": "subglottal_pressure",
            "aliases": [{"name": "Ps", "source": "paper"}],
            "status": "accepted",
            "definition": "Ps",
            "domain": "speech",
            "form": "pressure",
        },
    ], default_domain="speech")
    for index, concept in enumerate(concepts, start=1):
        (concepts_dir / f"concept{index}.yaml").write_text(
            yaml.dump(concept, default_flow_style=False)
        )

    claim1 = make_parameter_claim(
        "claim1",
        "concept1",
        200.0,
        "Hz",
        paper="paper",
        stances=[{"type": "supports", "target": "paper:claim2"}],
    )
    claim1["concept"] = "F0"
    claim2 = make_parameter_claim("claim2", "concept2", 100.0, "Pa", paper="paper")
    payload = normalize_claims_payload({
        "source": {"paper": "paper"},
        "claims": [claim1, claim2],
    })
    (claims_dir / "paper.yaml").write_text(yaml.dump(payload, default_flow_style=False))

    files = load_claim_files(claims_dir)
    context = build_compilation_context_from_paths(
        concepts_dir,
        forms_dir,
        claim_files=files,
    )
    bundle = compile_claim_files(files, context)

    assert bundle.ok
    semantic_claim = bundle.semantic_files[0].claims[0]
    target_claim_id = bundle.semantic_files[0].claims[1].artifact_id

    assert semantic_claim.concept_ref is not None
    assert semantic_claim.concept_ref.matched_by == "alias"
    assert semantic_claim.concept_ref.resolved_id == semantic_claim.resolved_claim["concept"]
    assert semantic_claim.stances[0].target_ref.matched_by == "logical_id"
    assert semantic_claim.stances[0].target_ref.resolved_id == target_claim_id


def test_prepare_claim_insert_row_matches_for_raw_and_semantic_claims(tmp_path):
    claims_dir = tmp_path / "claims"
    claims_dir.mkdir()

    claim = make_parameter_claim("claim1", "concept1", 200.0, "Hz", paper="paper")
    claim["concept"] = "F0"
    payload = normalize_claims_payload({
        "source": {"paper": "paper"},
        "claims": [claim],
    })
    (claims_dir / "paper.yaml").write_text(yaml.dump(payload, default_flow_style=False))

    files = load_claim_files(claims_dir)
    registry = make_concept_registry()
    context = compilation_context_from_concept_registry(registry, claim_files=files)
    bundle = compile_claim_files(files, context)

    raw_row = prepare_claim_insert_row(
        payload["claims"][0],
        "paper",
        claim_seq=1,
        concept_registry=registry,
    )
    semantic_row = prepare_claim_insert_row(
        bundle.semantic_files[0].claims[0],
        None,
        claim_seq=1,
        concept_registry=registry,
    )

    assert semantic_row == raw_row


def test_compile_claim_files_rejects_raw_id_only_claims(tmp_path):
    knowledge = tmp_path / "knowledge"
    claims_dir = knowledge / "claims"
    concepts_dir = knowledge / "concepts"
    forms_dir = knowledge / "forms"
    claims_dir.mkdir(parents=True)
    concepts_dir.mkdir()
    forms_dir.mkdir()

    (forms_dir / "frequency.yaml").write_text(yaml.dump({
        "name": "frequency",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "Hz",
    }))

    concepts = normalize_concept_payloads([{
        "id": "concept1",
        "canonical_name": "fundamental_frequency",
        "status": "accepted",
        "definition": "F0",
        "domain": "speech",
        "form": "frequency",
    }], default_domain="speech")
    (concepts_dir / "fundamental_frequency.yaml").write_text(
        yaml.dump(concepts[0], default_flow_style=False)
    )

    payload = {
        "source": {"paper": "paper"},
        "claims": [
            {
                "id": "claim1",
                "type": "parameter",
                "concept": concepts[0]["artifact_id"],
                "value": 200.0,
                "unit": "Hz",
                "context": {"id": "ctx_test"},
                "provenance": {"paper": "paper", "page": 1},
            }
        ],
    }
    (claims_dir / "paper.yaml").write_text(yaml.dump(payload, default_flow_style=False))

    files = load_claim_files(claims_dir)
    context = build_compilation_context_from_paths(
        concepts_dir,
        forms_dir,
        claim_files=files,
    )
    bundle = compile_claim_files(files, context)

    assert not bundle.ok
    messages = [diagnostic.message for diagnostic in bundle.diagnostics if diagnostic.is_error]
    assert any("raw 'id' input" in message for message in messages)
