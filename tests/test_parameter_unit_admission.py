"""Declared parameter units are checked before numeric comparison."""

from pathlib import Path

from condition_ir import KindType
import pytest

from propstore.claim_contracts import validate_claim
from propstore.compiler.context import build_compilation_context_from_repo
from propstore.compiler.workflows import build_repository, compile_repository_checked_bundle, validate_repository
from propstore.core.lemon import LexicalEntry, LexicalForm, LexicalSense, OntologyReference
from propstore.dimensions import ExtraUnitDefinition, UnitConversion
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.forms import FormDefinition
from propstore.provenance import Provenance, ProvenanceStatus, read_provenance_note, write_provenance_note
from propstore.repository import Repository


def _repo(tmp_path: Path, form: FormDefinition | None = None) -> Repository:
    repo = Repository.init(tmp_path)
    form = form or FormDefinition(
        name="force", kind=KindType.QUANTITY, unit_symbol="N",
        dimensions={"M": 1, "L": 1, "T": -2},
    )
    repo.families.form.save(form.name, form, message="Declare form")
    repo.families.concept.save(
        "output", Concept(
            concept_id="output", canonical_name="output",
            lexical_entry=LexicalEntry(
                identifier="entry:output",
                canonical_form=LexicalForm(written_rep="output", language="en"),
                senses=(LexicalSense(reference=OntologyReference(uri="urn:output")),),
                physical_dimension_form=form.name,
            ),
        ), message="Declare concept",
    )
    return repo


def _parameter(claim_id: str, unit: str | None) -> Claim:
    return Claim(
        claim_id=claim_id, claim_type=ClaimType.PARAMETER,
        output_concept="output", value=1.0, unit=unit,
    )


@pytest.mark.parametrize(
    ("unit", "code"),
    [("N", None), ("kN", None), ("kg", "claim.unit.incompatible"),
     ("not_a_known_unit", "claim.unit.incompatible"),
     ("N / (", "claim.unit.incompatible"), ("N**", "claim.unit.incompatible"),
     (None, "claim.unit.required"), ("", "claim.unit.required")],
)
def test_parameter_units_checked_by_real_compiler(
    tmp_path: Path, unit: str | None, code: str | None,
) -> None:
    repo = _repo(tmp_path)
    claim = _parameter("parameter", unit)
    repo.families.claim.save(claim.claim_id, claim, message="Author parameter")
    context = build_compilation_context_from_repo(repo)
    report = validate_claim(claim, context=context)
    assert report.deferred_checks == ()
    assert [problem.code for problem in report.diagnostics] == ([] if code is None else [code])
    checked = compile_repository_checked_bundle(repo, commit=None)
    assert checked is not None
    entry = checked.claim_bundle.claims[0]
    assert entry.blocked is (code is not None)
    assert [problem.code for problem in entry.diagnostics] == ([] if code is None else [code])
    if code is not None:
        assert "concept 'output', form 'force'" in entry.diagnostics[0].message
        assert repr(unit) in entry.diagnostics[0].message
    assert repo.families.claim.load(claim.claim_id) == claim


@pytest.mark.parametrize("unit", ["kg", "N / (", "N**"])
def test_incompatible_rival_quarantines_without_build_crash(tmp_path: Path, unit: str) -> None:
    repo = _repo(tmp_path)
    claims = (_parameter("valid", "N"), _parameter("invalid", unit))
    for claim in claims:
        commit = repo.families.claim.save(claim.claim_id, claim, message="Author rival")
    git = repo.require_git()
    provenance = Provenance(status=ProvenanceStatus.STATED, graph_name="urn:unit-test")
    write_provenance_note(git.raw_repo, commit, provenance)
    before_refs = git.raw_repo.refs.as_dict()

    built = build_repository(repo)
    validation = validate_repository(repo)

    assert built.claim_count == validation.claim_count == 2
    assert built.blocked_claim_count == 1
    assert built.conflicts == ()
    assert not validation.ok
    assert any(problem.code == "claim.unit.incompatible" for problem in validation.errors)
    assert [repo.families.claim.load(claim.claim_id) for claim in claims] == list(claims)
    assert read_provenance_note(git.raw_repo, commit) == provenance
    assert git.raw_repo.refs.as_dict() == before_refs


def test_convertible_rivals_remain_admitted_and_compare_in_si(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    for claim in (
        Claim(claim_id="newtons", claim_type=ClaimType.PARAMETER, output_concept="output", value=1000, unit="N"),
        _parameter("kilonewtons", "kN"),
    ):
        repo.families.claim.save(claim.claim_id, claim, message="Author equivalent force")
    assert validate_repository(repo).ok
    built = build_repository(repo)
    assert built.blocked_claim_count == 0
    assert built.conflicts == ()


def test_missing_checked_unit_evidence_is_not_success(tmp_path: Path) -> None:
    claim = _parameter("parameter", "N")
    raw_form = FormDefinition(name="raw", kind=KindType.QUANTITY, unit_symbol="N")
    report = validate_claim(claim, form=raw_form)
    assert [problem.code for problem in report.diagnostics] == ["claim.unit.context.missing"]
    repo = Repository.init(tmp_path)
    repo.families.concept.save("output", Concept(concept_id="output", canonical_name="output"), message="Declare unresolved concept")
    repo.families.claim.save(claim.claim_id, claim, message="Author unresolved parameter")
    checked = compile_repository_checked_bundle(repo, commit=None)
    assert checked is not None
    assert [problem.code for problem in checked.claim_bundle.claims[0].diagnostics] == ["claim.unit.form.missing"]


def test_missing_canonical_unit_is_unavailable_evidence(tmp_path: Path) -> None:
    repo = _repo(tmp_path, FormDefinition(name="force", kind=KindType.QUANTITY, dimensions={"M": 1, "L": 1, "T": -2}))
    claim = _parameter("parameter", "N")
    report = validate_claim(claim, context=build_compilation_context_from_repo(repo))
    assert [problem.code for problem in report.diagnostics] == ["claim.unit.form.unit.missing"]


@pytest.mark.parametrize("unit", [None, "1"])
def test_declared_dimensionless_default_preserves_authored_unit(tmp_path: Path, unit: str | None) -> None:
    repo = _repo(tmp_path, FormDefinition(name="ratio", kind=KindType.QUANTITY, is_dimensionless=True))
    claim = _parameter("ratio", unit)
    repo.families.claim.save(claim.claim_id, claim, message="Author ratio")
    assert validate_repository(repo).ok
    assert build_repository(repo).blocked_claim_count == 0
    assert repo.families.claim.load(claim.claim_id) == claim


def test_declared_custom_conversion_stays_supported(tmp_path: Path) -> None:
    repo = _repo(tmp_path, FormDefinition(
        name="force", kind=KindType.QUANTITY, unit_symbol="N", dimensions={"M": 1, "L": 1, "T": -2},
        conversions={"trial_force": UnitConversion(unit="trial_force", type="multiplicative", multiplier=2.0)},
    ))
    claim = _parameter("custom", "trial_force")
    repo.families.claim.save(claim.claim_id, claim, message="Author custom unit")
    assert validate_repository(repo).ok
    assert build_repository(repo).blocked_claim_count == 0


def test_declared_extra_unit_stays_supported(tmp_path: Path) -> None:
    repo = _repo(tmp_path, FormDefinition(
        name="force", kind=KindType.QUANTITY, unit_symbol="N", dimensions={"M": 1, "L": 1, "T": -2},
        extra_units=(ExtraUnitDefinition(symbol="unit_admission_newton", dimensions={"M": 1, "L": 1, "T": -2}),),
    ))
    claim = _parameter("extra", "unit_admission_newton")
    repo.families.claim.save(claim.claim_id, claim, message="Author declared unit")
    assert validate_repository(repo).ok
    assert build_repository(repo).blocked_claim_count == 0


def test_allowed_label_does_not_prove_dimensional_compatibility(tmp_path: Path) -> None:
    repo = _repo(tmp_path, FormDefinition(
        name="force", kind=KindType.QUANTITY, unit_symbol="N", dimensions={"M": 1, "L": 1, "T": -2},
        allowed_units=("kg",),
    ))
    report = validate_claim(_parameter("wrong", "kg"), context=build_compilation_context_from_repo(repo))
    assert [problem.code for problem in report.diagnostics] == ["claim.unit.incompatible"]


def test_dimensionless_scaled_units_are_compared_in_canonical_scale(tmp_path: Path) -> None:
    repo = _repo(tmp_path, FormDefinition(name="ratio", kind=KindType.QUANTITY, is_dimensionless=True))
    for claim in (
        _parameter("ratio", None),
        Claim(claim_id="percentage", claim_type=ClaimType.PARAMETER, output_concept="output", value=100, unit="percent"),
    ):
        repo.families.claim.save(claim.claim_id, claim, message="Author equivalent ratio")
    built = build_repository(repo)
    assert built.blocked_claim_count == 0
    assert built.conflicts == ()


def test_inconsistent_canonical_unit_does_not_prove_compatibility(tmp_path: Path) -> None:
    repo = _repo(tmp_path, FormDefinition(
        name="force", kind=KindType.QUANTITY, unit_symbol="kg", dimensions={"M": 1, "L": 1, "T": -2},
    ))
    report = validate_claim(_parameter("wrong", "kg"), context=build_compilation_context_from_repo(repo))
    assert [problem.code for problem in report.diagnostics] == ["claim.unit.incompatible"]


@pytest.mark.parametrize("kind", [KindType.CATEGORY, KindType.BOOLEAN, KindType.STRUCTURAL, KindType.TIMEPOINT])
def test_non_quantity_forms_do_not_require_physical_units(tmp_path: Path, kind: KindType) -> None:
    repo = _repo(tmp_path, FormDefinition(name="non_quantity", kind=kind))
    claim = Claim(
        claim_id="parameter", claim_type=ClaimType.PARAMETER, output_concept="output",
        value="category" if kind is KindType.CATEGORY else True if kind is KindType.BOOLEAN else 1,
    )
    repo.families.claim.save(claim.claim_id, claim, message="Author scalar")
    assert validate_repository(repo).ok
    assert build_repository(repo).blocked_claim_count == 0


def test_unit_owner_called_once_in_claim_admission(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from propstore import claim_contracts

    repo = _repo(tmp_path)
    repo.families.claim.save("parameter", _parameter("parameter", "kN"), message="Author parameter")
    calls = 0
    owner = claim_contracts.unit_compatible_with_form

    def count(unit: str, form: FormDefinition) -> bool:
        nonlocal calls
        calls += 1
        return owner(unit, form)

    monkeypatch.setattr(claim_contracts, "unit_compatible_with_form", count)
    checked = compile_repository_checked_bundle(repo, commit=None)
    assert checked is not None
    assert not checked.claim_bundle.blocked_claims
    assert calls == 1
