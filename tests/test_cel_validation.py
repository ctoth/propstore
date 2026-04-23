"""Ingest-time CEL validation (propstore/cel_validation.py).

Three surfaces reject CEL expressions that reference structural concepts
before they land in the repository or reach Z3:

  1. ``pks source add-claim`` (and ``--batch``): every CEL expression in
     each claim's ``conditions[]`` is validated.
  2. ``pks context add --assumption``: every assumption expression is
     validated.
  3. ``pks build`` / ``pks validate``: a pre-pass over master's claims
     and contexts fails the build early with the offending artifact
     named — the safety net for YAML that bypassed the CLI ingest path.

Unit-level tests exercise the validator directly against a fixture
registry; integration tests drive the CLI end-to-end.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from propstore.cel_checker import ConceptInfo, KindType
from propstore.cel_validation import (
    CelExpressionLocation,
    CelIngestValidationError,
    validate_cel_expression,
)
from propstore.cli import cli
from propstore.repository import Repository
from tests.conftest import normalize_concept_payloads


# ── Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def registry() -> dict[str, ConceptInfo]:
    """Registry with one structural and one boolean concept for contrast."""
    return {
        "intention_to_treat": ConceptInfo(
            id="ps:concept:__test__:intention_to_treat",
            canonical_name="intention_to_treat",
            kind=KindType.STRUCTURAL,
        ),
        "primary_prevention": ConceptInfo(
            id="ps:concept:__test__:primary_prevention",
            canonical_name="primary_prevention",
            kind=KindType.BOOLEAN,
        ),
    }


# ── Unit-level validator tests ───────────────────────────────────────

def test_validator_rejects_structural_concept_by_bare_name(registry):
    location = CelExpressionLocation(
        artifact_label="claim 'c1' in paper 'demo'",
        field="condition",
        index=2,
    )
    with pytest.raises(CelIngestValidationError) as info:
        validate_cel_expression(
            "intention_to_treat == true",
            registry,
            location=location,
        )
    message = str(info.value)
    # Message must mention the offending concept, the artifact context,
    # the field, and the original CEL-checker diagnostic text.
    assert "intention_to_treat" in message
    assert "condition[2]" in message
    assert "claim 'c1' in paper 'demo'" in message
    assert "Structural concept" in message


def test_validator_accepts_boolean_concept(registry):
    location = CelExpressionLocation(
        artifact_label="context 'ctx_test'",
        field="assumption",
        index=0,
    )
    validate_cel_expression(
        "primary_prevention == true",
        registry,
        location=location,
    )


def test_validator_is_value_error_subclass():
    """``CelIngestValidationError`` must be a ``ValueError`` so existing
    CLI handlers (click ClickException converters) catch it cleanly."""
    assert issubclass(CelIngestValidationError, ValueError)


# ── Helpers shared by CLI integration tests ──────────────────────────

def _init_repo_with_structural_concept(tmp_path: Path) -> Repository:
    """Seed a repo with a form, one structural concept on master, and a
    context so CLI add-claim can resolve ``ctx_test``."""
    repo = Repository.init(tmp_path / "knowledge")
    # Master needs a ``structural`` form, the ``intention_to_treat``
    # concept, and a context used by later claims.
    concept_payload = normalize_concept_payloads(
        [
            {
                "id": "concept_itt",
                "canonical_name": "intention_to_treat",
                "status": "accepted",
                "definition": "Intention-to-treat marker (structural).",
                "domain": "trials",
                "form": "structural",
            }
        ],
        default_domain="trials",
    )[0]
    repo.git.commit_batch(
        adds={
            "forms/structural.yaml": yaml.safe_dump(
                {"name": "structural", "dimensionless": True},
                sort_keys=False,
            ).encode("utf-8"),
            "concepts/intention_to_treat.yaml": yaml.safe_dump(
                concept_payload,
                sort_keys=False,
            ).encode("utf-8"),
            "contexts/ctx_test.yaml": yaml.safe_dump(
                {
                    "id": "ctx_test",
                    "name": "ctx_test",
                    "description": "Test context",
                },
                sort_keys=False,
            ).encode("utf-8"),
        },
        deletes=[],
        message="Seed master with structural concept and context",
        branch="master",
    )
    return repo


def _init_source(runner: CliRunner, repo: Repository, name: str = "demo") -> None:
    result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "init", name,
            "--kind", "academic_paper",
            "--origin-type", "manual",
            "--origin-value", name,
        ],
    )
    assert result.exit_code == 0, result.output


# ── Integration: pks source add-claim ────────────────────────────────

def test_source_add_claim_rejects_structural_in_cel(tmp_path: Path) -> None:
    """Claim batches with a structural concept referenced in a CEL
    condition must be rejected at ingest — the store must refuse the
    write, not accept it and fail only later at ``pks build``."""
    repo = _init_repo_with_structural_concept(tmp_path)
    runner = CliRunner()
    _init_source(runner, repo, "demo")

    # Also register the concept on the source branch so concept-ref
    # validation (a separate check) cannot be what fails first. We want
    # to prove the CEL validator is what trips.
    concepts_file = tmp_path / "concepts_batch.yaml"
    concepts_file.write_text(
        yaml.safe_dump(
            {
                "concepts": [
                    {
                        "local_name": "intention_to_treat",
                        "definition": "ITT marker.",
                        "form": "structural",
                        "proposed_name": "intention_to_treat",
                    },
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    result_c = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "add-concepts", "demo",
            "--batch", str(concepts_file),
        ],
    )
    assert result_c.exit_code == 0, result_c.output

    claims_file = tmp_path / "claims.yaml"
    claims_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": "demo"},
                "claims": [
                    {
                        "id": "claim6",
                        "type": "observation",
                        "context": "ctx_test",
                        "statement": "An observation.",
                        "provenance": {"page": 3},
                        "conditions": [
                            "intention_to_treat == true",
                        ],
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "source", "add-claim", "demo",
            "--batch", str(claims_file),
        ],
    )

    assert result.exit_code != 0, result.output
    # The error must name the claim, the condition, and the offending
    # concept — not a generic "something failed" message.
    assert "intention_to_treat" in result.output
    assert "Structural concept" in result.output
    assert "claim6" in result.output or "claim 'claim6'" in result.output


# ── Integration: pks context add --assumption ────────────────────────

def test_context_add_rejects_structural_in_assumption(tmp_path: Path) -> None:
    """``pks context add --assumption`` must reject CEL assumptions that
    reference structural concepts."""
    repo = _init_repo_with_structural_concept(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "-C", str(repo.root),
            "context", "add",
            "--name", "ctx_broken",
            "--description", "Broken context.",
            "--assumption", "intention_to_treat == true",
        ],
    )

    assert result.exit_code != 0, result.output
    assert "intention_to_treat" in result.output
    assert "Structural concept" in result.output
    # The context file must not have been created.
    assert not (repo.root / "contexts" / "ctx_broken.yaml").exists()


# ── Integration: pks build / validate pre-pass ───────────────────────

def test_build_rejects_structural_in_cel(tmp_path: Path) -> None:
    """``pks build`` / ``pks validate`` must fail early — before Z3 —
    when master contains YAML with a structural concept in a CEL
    expression. This protects against direct YAML edits that bypass the
    CLI ingest path."""
    repo = _init_repo_with_structural_concept(tmp_path)
    runner = CliRunner()

    # Bypass the CLI ingest boundary and write a context file with an
    # illegal CEL assumption directly into master.
    repo.git.commit_batch(
        adds={
            "contexts/ctx_broken.yaml": yaml.safe_dump(
                {
                    "id": "ctx_broken",
                    "name": "ctx_broken",
                    "description": "Direct-edit context with bad CEL.",
                    "structure": {
                        "assumptions": ["intention_to_treat == true"],
                    },
                },
                sort_keys=False,
            ).encode("utf-8"),
        },
        deletes=[],
        message="Direct edit that bypassed CLI validation",
        branch="master",
    )

    result = runner.invoke(
        cli,
        ["-C", str(repo.root), "validate"],
    )

    assert result.exit_code != 0, result.output
    assert "intention_to_treat" in result.output
    assert "Structural concept" in result.output


