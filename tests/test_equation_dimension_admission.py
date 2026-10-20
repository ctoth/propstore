"""Dimensional obligations at the real claim CHECKED boundary."""

from pathlib import Path

from condition_ir import KindType
import pytest

from propstore.compiler.workflows import build_repository, compile_repository_checked_bundle, validate_repository
from propstore.core.lemon import LexicalEntry, LexicalForm, LexicalSense, OntologyReference
from propstore.families.claims import Claim, ClaimType, ClaimVariable
from propstore.families.concepts import Concept
from propstore.families.forms import FormDefinition
from propstore.repository import Repository
from propstore.provenance import Provenance, ProvenanceStatus, read_provenance_note, write_provenance_note


def _physics_repo(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path)
    for name, dimensions in (
        ("force", {"M": 1, "L": 1, "T": -2}),
        ("mass", {"M": 1}),
        ("time", {"T": 1}),
        ("acceleration", {"L": 1, "T": -2}),
        ("ratio", {}),
    ):
        repo.families.form.save(
            name, FormDefinition(name=name, kind=KindType.QUANTITY, dimensions=dimensions, is_dimensionless=not dimensions),
            message="Declare dimensions",
        )
        repo.families.concept.save(
            name,
            Concept(
                concept_id=name, canonical_name=name,
                lexical_entry=LexicalEntry(
                    identifier=f"entry:{name}",
                    canonical_form=LexicalForm(written_rep=name, language="en"),
                    senses=(LexicalSense(reference=OntologyReference(uri=f"urn:{name}")),),
                    physical_dimension_form=name,
                ),
            ),
            message="Declare concept",
        )
    return repo


def _equation(claim_id: str, expression: str, output: str | None = "force") -> Claim:
    return Claim(
        claim_id=claim_id, claim_type=ClaimType.EQUATION,
        expression=expression, output_concept=output,
        variables=(
            ClaimVariable(concept="force", symbol="F", role="dependent"),
            ClaimVariable(concept="mass", symbol="m", role="independent"),
            ClaimVariable(concept="time", symbol="t", role="independent"),
            ClaimVariable(concept="acceleration", symbol="a", role="independent"),
            ClaimVariable(concept="ratio", symbol="r", role="dependent"),
        ),
    )


def test_dimensionally_inconsistent_equation_is_quarantined(tmp_path: Path) -> None:
    repo = _physics_repo(tmp_path)
    claim = Claim(
        claim_id="wrong-force", claim_type=ClaimType.EQUATION,
        expression="F = m * t", output_concept="force",
        variables=(
            ClaimVariable(concept="force", symbol="F", role="dependent"),
            ClaimVariable(concept="mass", symbol="m", role="independent"),
            ClaimVariable(concept="time", symbol="t", role="independent"),
        ),
    )
    repo.families.claim.save(claim.claim_id, claim, message="Author equation")

    checked = compile_repository_checked_bundle(repo, commit=None)

    assert checked is not None
    assert [entry.claim.claim_id for entry in checked.claim_bundle.blocked_claims] == [
        "wrong-force"
    ]
    diagnostic = checked.claim_bundle.blocked_claims[0].diagnostics[0]
    assert diagnostic.code == "claim.dimension.mismatch"
    assert "concept 'mass', form 'mass'" in diagnostic.message
    assert "role 'independent'" in diagnostic.message
    assert repo.families.claim.load(claim.claim_id) == claim


@pytest.mark.parametrize(
    ("expression", "output", "code"),
    [
        ("F = m * a", "force", None),
        ("F = m * a", None, None),
        ("m * a", "force", None),
        ("m * a", None, "claim.dimension.concept.missing"),
        ("F = F", "force", None),
        ("Eq(F, F)", "force", None),
        ("F / m = a", "force", None),
        ("F = m + a", "force", "claim.dimension.algebra.invalid"),
        ("m = m + t - t", "mass", "claim.dimension.algebra.invalid"),
        ("m.attribute = m", "mass", "claim.dimension.expression.invalid"),
        ("__claim_output__(m)", "force", "claim.dimension.algebra.invalid"),
        ("r = sin(t)", "ratio", "claim.dimension.algebra.invalid"),
        ("r = sin(r)", "ratio", None),
        ("F = m * unknown", "force", "claim.dimension.binding.unavailable"),
        ("r = 2 ^ m", "ratio", "claim.dimension.algebra.invalid"),
        ("r = 2 ^ unknown", "ratio", "claim.dimension.binding.unavailable"),
        ("F = 0", "force", None),
        ("F = F + 0", "force", None),
        ("m = (m^2)^(1/2)", "mass", None),
        ("m = m^(2/2)", "mass", None),
        ("m = sqrt(m^2)", "mass", None),
        ("F = F or (m + t)", "force", "claim.contract"),
        ("F = F or unknown", "force", "claim.contract"),
        ("m = m if r else t", "mass", "claim.contract"),
        ("m = Piecewise((m, True), (m+t, False))", "mass", "claim.contract"),
        ("F = (F, m+t)[0]", "force", "claim.contract"),
        ("F = [F, unknown][0]", "force", "claim.contract"),
        ("m = (m+t).args[0]", "mass", "claim.contract"),
        ("F = (lambda x: 0)(m+t)", "force", "claim.contract"),
        ("F = (lambda x: 0)(unknown)", "force", "claim.contract"),
        ("F = Max(*[F for x in (m+t,)])", "force", "claim.contract"),
        ("F = Max(*{F: m+t})", "force", "claim.contract"),
        ("F = Max(*[F for x in (unknown,)])", "force", "claim.contract"),
        ("F = Max(*(F for x in (unknown,)))", "force", "claim.contract"),
        ("F = Max(*(F for x in (m+t,)))", "force", "claim.contract"),
    ],
)
def test_authored_equation_operations_are_checked(
    tmp_path: Path, expression: str, output: str | None, code: str | None,
) -> None:
    repo = _physics_repo(tmp_path)
    claim = _equation("formula", expression, output)
    repo.families.claim.save(claim.claim_id, claim, message="Author equation")
    checked = compile_repository_checked_bundle(repo, commit=None)
    assert checked is not None
    entry = checked.claim_bundle.claims[0]
    assert entry.blocked is (code is not None)
    assert [problem.code for problem in entry.diagnostics] == ([] if code is None else [code])
    if code == "claim.contract":
        assert "unsupported authored syntax" in entry.diagnostics[0].message
    assert repo.families.claim.load(claim.claim_id) == claim


@pytest.mark.parametrize(
    ("form", "code"),
    [
        (None, "claim.dimension.form.missing"),
        (FormDefinition(name="opaque", kind=KindType.QUANTITY), "claim.dimension.signature.missing"),
        (FormDefinition(name="opaque", kind=KindType.TIMEPOINT, dimensions={"T": 1}), "claim.dimension.kind.invalid"),
    ],
)
def test_unavailable_input_evidence_is_distinct_from_mismatch(
    tmp_path: Path, form: FormDefinition | None, code: str,
) -> None:
    repo = _physics_repo(tmp_path)
    if form is not None:
        repo.families.form.save(form.name, form, message="Declare incomplete input")
    repo.families.concept.save(
        "opaque",
        Concept(
            concept_id="opaque", canonical_name="opaque",
            lexical_entry=LexicalEntry(
                identifier="entry:opaque",
                canonical_form=LexicalForm(written_rep="opaque", language="en"),
                senses=(LexicalSense(reference=OntologyReference(uri="urn:opaque")),),
                physical_dimension_form="opaque" if form is not None else None,
            ),
        ), message="Declare input concept",
    )
    claim = Claim(
        claim_id="unavailable", claim_type=ClaimType.EQUATION,
        expression="F = x", output_concept="force",
        variables=(ClaimVariable(concept="force", symbol="F"), ClaimVariable(concept="opaque", symbol="x")),
    )
    repo.families.claim.save(claim.claim_id, claim, message="Author equation")
    checked = compile_repository_checked_bundle(repo, commit=None)
    assert checked is not None
    diagnostic = checked.claim_bundle.blocked_claims[0].diagnostics[0]
    assert diagnostic.code == code
    assert "evidence unavailable" in diagnostic.message
    assert f"concept 'opaque', form {('opaque' if form is not None else None)!r}" in diagnostic.message


def test_checked_dimensionless_default_needs_no_explicit_signature(tmp_path: Path) -> None:
    repo = _physics_repo(tmp_path)
    repo.families.form.save(
        "ratio", FormDefinition(name="ratio", kind=KindType.QUANTITY, is_dimensionless=True),
        message="Use declared dimensionless form",
    )
    repo.families.claim.save("ratio", _equation("ratio", "r = sin(r)", "ratio"), message="Author equation")
    checked = compile_repository_checked_bundle(repo, commit=None)
    assert checked is not None
    assert checked.claim_bundle.blocked_claims == ()


def test_unchecked_forms_cannot_fabricate_a_dimensional_verdict() -> None:
    from propstore.compiler.context import build_compilation_context
    from propstore.families.concepts_passes import ConceptCheckedRegistry, run_concept_pipeline

    result = run_concept_pipeline([])
    assert isinstance(result.output, ConceptCheckedRegistry)
    with pytest.raises(TypeError, match="FormCheckedRegistry"):
        build_compilation_context(result.output, form_registry={})


def test_full_equation_must_match_the_concept_it_computes(tmp_path: Path) -> None:
    repo = _physics_repo(tmp_path)
    claim = Claim(
        claim_id="wrong-output", claim_type=ClaimType.EQUATION,
        expression="m = m", output_concept="force", concepts=("force", "mass"),
        variables=(ClaimVariable(concept="mass", symbol="m", role="dependent"),),
    )
    repo.families.claim.save(claim.claim_id, claim, message="Author parameterization")
    checked = compile_repository_checked_bundle(repo, commit=None)
    assert checked is not None
    assert [problem.code for problem in checked.claim_bundle.claims[0].diagnostics] == [
        "claim.dimension.output.binding.unavailable"
    ]


def test_context_repository_loader_rejects_invalid_forms(tmp_path: Path) -> None:
    from propstore.compiler.context import build_compilation_context_from_repo

    repo = _physics_repo(tmp_path)
    repo.families.form.save(
        "bad", FormDefinition(name="bad", kind=KindType.QUANTITY, is_dimensionless=True, dimensions={"M": 1}),
        message="Retain invalid form",
    )
    with pytest.raises(ValueError, match="form validation failed"):
        build_compilation_context_from_repo(repo)


def test_validate_build_preserve_rival_claims_and_provenance(tmp_path: Path) -> None:
    repo = _physics_repo(tmp_path)
    invalid = _equation("invalid", "F = m * t")
    valid = _equation("valid", "F = m * a")
    for claim in (invalid, valid):
        authored_commit = repo.families.claim.save(claim.claim_id, claim, message="Author equation")
    provenance = Provenance(status=ProvenanceStatus.STATED, graph_name="urn:test:equations")
    git = repo.require_git()
    write_provenance_note(git.raw_repo, authored_commit, provenance)
    before_refs = git.raw_repo.refs.as_dict()

    validation = validate_repository(repo)
    built = build_repository(repo)

    assert validation.claim_count == built.claim_count == 2
    assert not validation.ok
    assert built.blocked_claim_count == 1
    assert any(problem.code == "claim.dimension.mismatch" for problem in validation.errors)
    assert repo.families.claim.load("invalid") == invalid
    assert repo.families.claim.load("valid") == valid
    assert read_provenance_note(git.raw_repo, authored_commit) == provenance
    assert git.raw_repo.refs.as_dict() == before_refs
