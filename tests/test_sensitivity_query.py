"""Owner-layer ``query_sensitivity`` report tier (Phase 10-0b).

``query_sensitivity`` is the render-owner entry point the ``pks world
sensitivity`` adapter calls. It binds a repo-backed :class:`WorldQuery` under the
request bindings and runs the finite-difference :func:`analyze_sensitivity`
(no SymPy boundary in propstore). A concept with no parameterization yields an
honest ``result=None`` rather than a fabricated sensitivity.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.repository import Repository
from propstore.sensitivity import (
    SensitivityReport,
    SensitivityRequest,
    query_sensitivity,
)
from propstore.world import WorldQuery


def _repo(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "kn")
    for concept_id in ("A", "B", "C"):
        repo.families.concept.save(
            concept_id,
            Concept(concept_id=concept_id, canonical_name=concept_id),
            message="m",
        )
    repo.families.context.save(
        "ctx1", Context(context_id="ctx1", name="ctx"), message="m"
    )
    repo.families.claim.save(
        "a",
        Claim(
            claim_id="a",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="A",
            value=2.0,
        ),
        message="m",
    )
    repo.families.claim.save(
        "b",
        Claim(
            claim_id="b",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="B",
            value=3.0,
        ),
        message="m",
    )
    repo.families.claim.save(
        "eq",
        Claim(
            claim_id="eq",
            context_id="ctx1",
            claim_type=ClaimType.EQUATION,
            output_concept="C",
            concepts=("A", "B"),
            expression="A + B",
            sympy="A + B",
        ),
        message="m",
    )
    return repo


def test_query_sensitivity_reports_ranked_elasticities(tmp_path: Path) -> None:
    with WorldQuery(_repo(tmp_path)) as world:
        report = query_sensitivity(
            world, SensitivityRequest(concept_id="C", bindings={})
        )

    assert isinstance(report, SensitivityReport)
    assert report.concept_id == "C"
    assert report.result is not None
    assert report.result.output_value == pytest.approx(5.0)
    by_input = {str(entry.input_concept_id): entry for entry in report.result.entries}
    assert by_input["A"].partial_derivative_value == pytest.approx(1.0)
    assert by_input["B"].partial_derivative_value == pytest.approx(1.0)
    # elasticity = (df/dx)*(x/f): A=1*2/5=0.4, B=1*3/5=0.6 → B dominates, ranked first.
    assert by_input["A"].elasticity == pytest.approx(0.4)
    assert by_input["B"].elasticity == pytest.approx(0.6)
    assert [str(entry.input_concept_id) for entry in report.result.entries] == [
        "B",
        "A",
    ]


def test_query_sensitivity_no_parameterization_is_honest_none(tmp_path: Path) -> None:
    with WorldQuery(_repo(tmp_path)) as world:
        report = query_sensitivity(
            world, SensitivityRequest(concept_id="A", bindings={})
        )

    # A has a value but no parameterization — honest ignorance, not a fabricated result.
    assert report.concept_id == "A"
    assert report.result is None


def test_query_sensitivity_report_is_json_ready(tmp_path: Path) -> None:
    with WorldQuery(_repo(tmp_path)) as world:
        report = query_sensitivity(
            world, SensitivityRequest(concept_id="C", bindings={})
        )

    payload = report.to_json()
    assert payload["concept_id"] == "C"
    assert payload["result"] is not None
