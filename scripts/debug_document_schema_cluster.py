from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

import yaml

from propstore.cli.repository import Repository
from propstore.core.concepts import (
    ConceptDocument,
    normalize_loaded_concepts,
)
from propstore.document_schema import load_document
from propstore.identity import compute_concept_version_id
from propstore.sidecar.build import build_sidecar
from tests.conftest import normalize_claims_payload, normalize_concept_payloads


def debug_context_fixture() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        knowledge = root / "knowledge"
        concepts = knowledge / "concepts"
        forms = knowledge / "forms"
        counters = concepts / ".counters"
        counters.mkdir(parents=True)
        forms.mkdir(parents=True)
        (counters / "global.next").write_text("2\n", encoding="utf-8")
        (forms / "structural.yaml").write_text(
            yaml.dump({"name": "structural", "dimensionless": True}, default_flow_style=False),
            encoding="utf-8",
        )

        concept_payload = normalize_concept_payloads(
            [
                {
                    "id": "concept1",
                    "canonical_name": "test_concept",
                    "status": "accepted",
                    "definition": "A test concept",
                    "domain": "test",
                    "form": "structural",
                    "created_date": "2026-03-22",
                }
            ],
            default_domain="test",
        )[0]
        concept_path = concepts / "test_concept.yaml"
        concept_path.write_text(yaml.dump(concept_payload, default_flow_style=False), encoding="utf-8")

        loaded = load_document(concept_path, ConceptDocument, knowledge_root=knowledge)
        normalized = normalize_loaded_concepts([loaded])[0]
        loaded_payload = normalized.record.to_payload()

        print("== context fixture concept ==")
        print("file payload")
        print(json.dumps(concept_payload, indent=2, sort_keys=True))
        print("loaded payload")
        print(json.dumps(loaded_payload, indent=2, sort_keys=True))
        print("file version", concept_payload["version_id"])
        print("loaded version", loaded_payload["version_id"])
        print("recomputed file version", compute_concept_version_id(concept_payload))
        print("recomputed loaded version", compute_concept_version_id(loaded_payload))


def debug_physics_parameterizations() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        knowledge = root / "knowledge"
        concepts_dir = knowledge / "concepts"
        forms_dir = knowledge / "forms"
        claims_dir = knowledge / "claims"
        counters = concepts_dir / ".counters"
        counters.mkdir(parents=True)
        forms_dir.mkdir(parents=True)
        claims_dir.mkdir(parents=True)
        (counters / "physics.next").write_text("10", encoding="utf-8")

        for form_name in ("acceleration", "force", "mass", "category"):
            data = {"name": form_name, "dimensionless": False, "kind": "quantity"}
            if form_name == "category":
                data["kind"] = "category"
            (forms_dir / f"{form_name}.yaml").write_text(
                yaml.dump(data, default_flow_style=False),
                encoding="utf-8",
            )

        def write_concept(name: str, data: dict) -> None:
            (concepts_dir / f"{name}.yaml").write_text(
                yaml.dump(data, default_flow_style=False),
                encoding="utf-8",
            )

        write_concept(
            "mass",
            {
                "id": "concept1",
                "canonical_name": "mass",
                "status": "accepted",
                "definition": "Mass.",
                "form": "mass",
            },
        )
        write_concept(
            "acceleration",
            {
                "id": "concept2",
                "canonical_name": "acceleration",
                "status": "accepted",
                "definition": "Acceleration.",
                "form": "acceleration",
            },
        )
        write_concept(
            "force",
            {
                "id": "concept3",
                "canonical_name": "force",
                "status": "accepted",
                "definition": "Force.",
                "form": "force",
                "parameterization_relationships": [
                    {
                        "formula": "F = m * a",
                        "inputs": ["concept1", "concept2"],
                        "sympy": "Eq(concept3, concept1 * concept2)",
                        "exactness": "exact",
                        "source": "Newton",
                        "bidirectional": True,
                    }
                ],
            },
        )
        write_concept(
            "location",
            {
                "id": "concept6",
                "canonical_name": "location",
                "status": "accepted",
                "definition": "Location.",
                "form": "category",
                "form_parameters": {"values": ["earth", "moon"], "extensible": False},
            },
        )

        (claims_dir / "physics_claims.yaml").write_text(
            yaml.dump(
                normalize_claims_payload(
                    {
                        "source": {"paper": "test"},
                        "claims": [
                            {
                                "id": "g_earth",
                                "type": "parameter",
                                "concept": "concept2",
                                "value": 9.807,
                                "unit": "m/s^2",
                                "conditions": ["location == 'earth'"],
                                "provenance": {"paper": "test", "page": 1},
                            },
                            {
                                "id": "mass_5kg",
                                "type": "parameter",
                                "concept": "concept1",
                                "value": 5.0,
                                "unit": "kg",
                                "provenance": {"paper": "test", "page": 1},
                            },
                        ],
                    }
                ),
                default_flow_style=False,
            ),
            encoding="utf-8",
        )

        repo = Repository(knowledge)
        repo.sidecar_path.parent.mkdir(parents=True, exist_ok=True)
        build_sidecar(knowledge, repo.sidecar_path)

        conn = sqlite3.connect(repo.sidecar_path)
        conn.row_factory = sqlite3.Row
        concepts = [dict(row) for row in conn.execute("SELECT id, canonical_name, logical_ids_json FROM concept ORDER BY id")]
        params = [dict(row) for row in conn.execute("SELECT * FROM parameterization ORDER BY output_concept_id")]
        conn.close()
        print("== physics concepts ==")
        print(json.dumps(concepts, indent=2, sort_keys=True))
        print("== physics parameterizations ==")
        print(json.dumps(params, indent=2, sort_keys=True))


if __name__ == "__main__":
    debug_context_fixture()
    debug_physics_parameterizations()
