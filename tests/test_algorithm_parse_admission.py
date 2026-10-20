"""Algorithm parse/free-name obligations reach real claim admission (#26)."""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.claim_contracts import validate_claim
from propstore.compiler.workflows import (
    build_repository,
    compile_repository_checked_bundle,
    validate_repository,
)
from propstore.families.claims import Claim, ClaimType, ClaimVariable
from propstore.families.concepts import Concept
from propstore.repository import Repository


def _algorithm(claim_id: str, body: str) -> Claim:
    return Claim(
        claim_id=claim_id,
        claim_type=ClaimType.ALGORITHM,
        output_concept="output",
        body=body,
    )


@pytest.mark.parametrize("body", ["def", "answer = 42"])
def test_invalid_algorithm_reports_its_parse_failure(body: str) -> None:
    report = validate_claim(_algorithm("invalid", body))

    assert any(
        problem.field == "body" and "parse error" in problem.message
        for problem in report.diagnostics
    )
    assert "AlgorithmParseCheck" not in report.deferred_checks


@pytest.mark.parametrize(
    "body",
    [
        "def compute(x):\n    doubled = x * 2\n    return doubled\n",
        "async def compute(x):\n    return x\n",
        "def compute(xs):\n    return sum(x * x for x in xs)\n",
    ],
)
def test_valid_algorithm_keeps_its_existing_admission(body: str) -> None:
    report = validate_claim(_algorithm("valid", body))

    assert report.diagnostics == ()
    assert "AlgorithmParseCheck" not in report.deferred_checks
    assert "AlgorithmUnboundNamesCheck" not in report.deferred_checks


def test_undeclared_free_names_report_exact_sorted_evidence() -> None:
    claim = _algorithm(
        "unbound", "def compute(x):\n    return x + zeta + alpha + zeta\n"
    )
    report = validate_claim(claim)

    assert [(problem.field, problem.message) for problem in report.diagnostics] == [
        ("body", "algorithm body has unbound names: alpha, zeta")
    ]
    assert report.deferred_checks == ()


@pytest.mark.parametrize(
    "binding",
    [
        ClaimVariable(concept="output", symbol="offset"),
        ClaimVariable(concept="output", name="offset"),
        ClaimVariable(concept="output", name="offset", symbol="other"),
    ],
)
def test_declared_external_binding_remains_admitted(binding: ClaimVariable) -> None:
    claim = Claim(
        claim_id="bound",
        claim_type=ClaimType.ALGORITHM,
        output_concept="output",
        body="def compute(x):\n    return x + offset\n",
        variables=(binding,),
    )

    report = validate_claim(claim)

    assert report.diagnostics == ()
    assert report.deferred_checks == ()


def test_comprehension_binding_does_not_leak_into_enclosing_scope() -> None:
    report = validate_claim(
        _algorithm(
            "leaked",
            "def compute(xs):\n    squares = [x * x for x in xs]\n    return x\n",
        )
    )

    assert [(problem.field, problem.message) for problem in report.diagnostics] == [
        ("body", "algorithm body has unbound names: x")
    ]


@pytest.mark.parametrize(
    "body",
    [
        "def compute(xs):\n    total = sum(x * x for x in xs)\n    return total\n",
        "def compute(x):\n    def inner(y):\n        return x + y\n    return inner(x)\n",
        "async def compute(x):\n    return x\n",
        "def compute(x):\n    import math\n    return math.sqrt(x)\n",
        "def compute(x):\n    from math import sqrt as root\n    return root(x)\n",
        "import math\ndef compute(x):\n    return math.sqrt(x)\n",
        "def compute(x):\n    return math.sqrt(x)\nimport math\n",
        "def compute(x):\n    def inner():\n        return offset\n"
        "    offset = x\n    return inner()\n",
        "def compute(x):\n    try:\n        return int(x)\n"
        "    except ValueError as exc:\n        return str(exc)\n",
        "def compute(x):\n    return divmod(x, 2), slice(x), object(), "
        "issubclass(int, object), OSError()\n",
        "def helper(x):\n    return x\nclass Container:\n    pass\n"
        "def compute(x):\n    local = lambda y: y\n"
        "    return helper(local(x)), Container()\n",
    ],
)
def test_local_bindings_and_builtins_need_no_concept_declaration(
    body: str,
    tmp_path: Path,
) -> None:
    report = validate_claim(_algorithm("local", body))

    assert report.diagnostics == ()
    assert report.deferred_checks == ()

    repo = Repository.init(tmp_path)
    repo.families.concept.save(
        "output",
        Concept(concept_id="output", canonical_name="output"),
        message="Declare output concept",
    )
    claim = _algorithm("local", body)
    repo.families.claim.save("local", claim, message="Author algorithm")
    checked = compile_repository_checked_bundle(repo, commit=None)
    assert checked is not None
    assert checked.claim_bundle.blocked_claims == ()
    assert [entry.claim.claim_id for entry in checked.claim_bundle.checked_claims] == [
        "local"
    ]
    assert repo.families.claim.load("local") == claim


@pytest.mark.parametrize(
    ("invalid_body", "diagnostic_text"),
    [
        ("def", "parse error"),
        ("def compute(x):\n    return x + missing\n", "unbound names: missing"),
        (
            "def compute(x):\n    class C:\n        import math\n"
            "    return math.sqrt(x)\n",
            "unbound names: math",
        ),
        (
            "def compute(xs):\n    xs[missing] = 0\n    return xs\n",
            "unbound names: missing",
        ),
        (
            "def compute():\n    nonlocal missing\n    return missing\n",
            "binding error: Invalid binding syntax",
        ),
        pytest.param(
            "def compute(xs):\n    return sum(x for x in xs) + genexpr\n",
            "unbound names: genexpr",
            id="generator_namespace_label",
        ),
        pytest.param(
            "def compute(xs):\n    return [x for x in xs], listcomp\n",
            "unbound names: listcomp",
            id="list_comprehension_label",
        ),
        pytest.param(
            "def compute(xs):\n    return {x for x in xs}, setcomp\n",
            "unbound names: setcomp",
            id="set_comprehension_label",
        ),
        pytest.param(
            "def compute(xs):\n    return {x: x for x in xs}, dictcomp\n",
            "unbound names: dictcomp",
            id="dict_comprehension_label",
        ),
        pytest.param(
            "def compute(xs):\n    return (lambda x: x), lambda_\n",
            "unbound names: lambda_",
            id="lambda_namespace",
        ),
        pytest.param(
            "def f(x):\n    return " + "+".join(["x"] * 600) + "\n",
            "recursion",
            id="analysis_limit_600",
        ),
        pytest.param(
            "def f(x):\n    return " + "+".join(["x"] * 800) + "\n",
            "recursion",
            id="analysis_limit_800",
        ),
    ],
)
def test_repository_quarantines_invalid_algorithm_and_retains_both_claims(
    tmp_path: Path,
    invalid_body: str,
    diagnostic_text: str,
) -> None:
    repo = Repository.init(tmp_path)
    repo.families.concept.save(
        "output",
        Concept(concept_id="output", canonical_name="output"),
        message="Declare output concept",
    )
    invalid = _algorithm("invalid", invalid_body)
    valid = Claim(
        claim_id="valid",
        claim_type=ClaimType.ALGORITHM,
        output_concept="output",
        body="def compute(x):\n    return x + offset\n",
        variables=(ClaimVariable(concept="output", symbol="offset"),),
    )
    for claim in (invalid, valid):
        repo.families.claim.save(claim.claim_id, claim, message="Author algorithm")

    checked = compile_repository_checked_bundle(repo, commit=None)
    assert checked is not None
    assert [entry.claim.claim_id for entry in checked.claim_bundle.claims] == [
        "invalid",
        "valid",
    ]
    assert [
        entry.claim.claim_id for entry in checked.claim_bundle.blocked_claims
    ] == ["invalid"]
    assert [
        entry.claim.claim_id for entry in checked.claim_bundle.checked_claims
    ] == ["valid"]
    diagnostic = checked.claim_bundle.blocked_claims[0].diagnostics[0]
    assert diagnostic.code == "claim.contract"
    assert diagnostic.artifact_id == "invalid"
    assert diagnostic_text in diagnostic.message

    validation = validate_repository(repo)
    assert not validation.ok
    assert validation.claim_count == 2
    assert any(
        message.artifact_id == "invalid" and diagnostic_text in message.message
        for message in validation.errors
    )

    built = build_repository(repo)
    assert built.claim_count == 2
    assert built.blocked_claim_count == 1
    assert repo.families.claim.load("invalid") == invalid
    assert repo.families.claim.load("valid") == valid
