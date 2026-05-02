from __future__ import annotations

import ast
from pathlib import Path

import pytest
import yaml

from tests.conftest import TEST_CONTEXT_ID
from propstore.core.conditions.registry import KindType
from propstore.families.forms.stages import FormDefinition
from tests.family_helpers import load_claim_files
from tests.test_validate_claims import (
    make_claim_file_data,
    make_compilation_context,
    make_equation_claim,
    validate_claims,
    write_claim_file,
)
from tests.test_validator import (
    load_concepts,
    make_quantity_concept,
    validate_concepts,
    write_concept,
)


def _concept_artifact(local_id: str) -> str:
    from propstore.families.identity.concepts import derive_concept_artifact_id

    return derive_concept_artifact_id("propstore", local_id)


def _production_python_files() -> list[Path]:
    return list(Path("propstore").rglob("*.py"))


def test_production_no_longer_imports_dims_of_expr_from_bridgman() -> None:
    offenders: list[str] = []
    for path in _production_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "bridgman":
                imported = {alias.name for alias in node.names}
                if "dims_of_expr" in imported:
                    offenders.append(str(path))

    assert offenders == []


def test_production_has_no_verify_equation_call_sites() -> None:
    offenders: list[str] = []
    for path in _production_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "bridgman":
                if any(alias.name == "verify_equation" for alias in node.names):
                    offenders.append(f"{path}:import")
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "verify_equation":
                    offenders.append(f"{path}:call")
                if isinstance(func, ast.Attribute) and func.attr == "verify_equation":
                    offenders.append(f"{path}:call")

    assert offenders == []


def test_claim_dimensional_error_records_error(tmp_path) -> None:
    claims_dir = tmp_path / "claims"
    claims_dir.mkdir()
    registry = {
        _concept_artifact("concept1"): {
            "artifact_id": _concept_artifact("concept1"),
            "canonical_name": "angle",
            "form": "duration_ratio",
            "status": "accepted",
            "definition": "Angle-like dimensionless value.",
            "_form_definition": FormDefinition(
                name="duration_ratio",
                kind=KindType.QUANTITY,
                dimensions=None,
                is_dimensionless=True,
            ),
        },
        _concept_artifact("concept2"): {
            "artifact_id": _concept_artifact("concept2"),
            "canonical_name": "length",
            "form": "distance",
            "status": "accepted",
            "definition": "Length.",
            "_form_definition": FormDefinition(
                name="distance",
                kind=KindType.QUANTITY,
                dimensions={"L": 1},
                is_dimensionless=False,
            ),
        },
    }
    claim = make_equation_claim(
        "claim1",
        "theta = sin(length)",
        sympy="Eq(theta, sin(length))",
        variables=[
            {"symbol": "theta", "concept": "concept1"},
            {"symbol": "length", "concept": "concept2"},
        ],
        context={"id": TEST_CONTEXT_ID},
    )
    write_claim_file(claims_dir, "test_claims.yaml", make_claim_file_data([claim]))

    result = validate_claims(
        load_claim_files(claims_dir),
        make_compilation_context(registry),
    )

    rendered_errors = [error.render() for error in result.errors]
    assert any("dimensional" in error.lower() and "sin" in error for error in rendered_errors)


def test_concept_dimensional_error_records_error(tmp_path) -> None:
    concept_dir = tmp_path / "knowledge" / "concepts"
    forms_dir = tmp_path / "knowledge" / "forms"
    concept_dir.mkdir(parents=True)
    forms_dir.mkdir()
    (concept_dir / ".counters").mkdir()
    (concept_dir / ".counters" / "speech.next").write_text("10", encoding="utf-8")

    (forms_dir / "distance.yaml").write_text(
        yaml.dump(
            {
                "name": "distance",
                "kind": "quantity",
                "dimensionless": False,
                "dimensions": {"L": 1},
            },
            default_flow_style=False,
        ),
        encoding="utf-8",
    )
    (forms_dir / "duration_ratio.yaml").write_text(
        yaml.dump(
            {
                "name": "duration_ratio",
                "kind": "quantity",
                "dimensionless": True,
                "dimensions": {},
            },
            default_flow_style=False,
        ),
        encoding="utf-8",
    )

    c1 = make_quantity_concept("concept1", "length", form="distance")
    c2 = make_quantity_concept("concept2", "scale", form="duration_ratio")
    c3 = make_quantity_concept(
        "concept3",
        "angle",
        form="duration_ratio",
        parameterization_relationships=[
            {
                "formula": "angle = sin(length) * scale",
                "sympy": "Eq(angle, sin(length) * scale)",
                "inputs": ["concept1", "concept2"],
                "exactness": "exact",
                "source": "Test_2026",
                "bidirectional": True,
            }
        ],
    )
    write_concept(concept_dir, "length.yaml", c1)
    write_concept(concept_dir, "scale.yaml", c2)
    write_concept(concept_dir, "angle.yaml", c3)

    result = validate_concepts(load_concepts(concept_dir), forms_dir=forms_dir)

    assert any("dimensional" in error.lower() and "sin" in error for error in result.errors)
