from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

import yaml

from propstore.cli.repository import Repository
from propstore.sidecar.build import build_sidecar
from tests.conftest import normalize_claims_payload


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
        concepts = [
            dict(row)
            for row in conn.execute(
                "SELECT id, canonical_name, logical_ids_json FROM concept ORDER BY id"
            )
        ]
        params = [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM parameterization ORDER BY output_concept_id"
            )
        ]
        conn.close()
        print("== physics concepts ==")
        print(json.dumps(concepts, indent=2, sort_keys=True))
        print("== physics parameterizations ==")
        print(json.dumps(params, indent=2, sort_keys=True))


if __name__ == "__main__":
    debug_context_fixture()
    debug_physics_parameterizations()
