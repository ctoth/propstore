"""Declared parameter units are checked before numeric comparison."""

from pathlib import Path

from condition_ir import KindType
import pytest

from propstore.claim_contracts import validate_claim
from propstore.compiler.context import build_compilation_context_from_repo
from propstore.compiler.workflows import build_repository, compile_repository_checked_bundle, validate_repository
from propstore.core.lemon import LexicalEntry, LexicalForm, LexicalSense, OntologyReference
from propstore.dimensions import ExtraUnitDefinition, UnitConversion
from propstore.families.claims import Claim, ClaimType, ClaimVariable, Exactness
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
    assert [problem.code for problem in report.diagnostics] == ["claim.unit.form.invalid"]
    assert "evidence unavailable" in report.diagnostics[0].message


@pytest.mark.parametrize("unit", ["unknown_canonical", "kg"])
def test_dimensionless_canonical_unit_must_have_proven_dimensionless_evidence(tmp_path: Path, unit: str) -> None:
    repo = _repo(tmp_path, FormDefinition(name="ratio", kind=KindType.QUANTITY, is_dimensionless=True, unit_symbol=unit))
    report = validate_claim(_parameter("wrong", unit), context=build_compilation_context_from_repo(repo))
    assert [problem.code for problem in report.diagnostics] == ["claim.unit.form.invalid"]


@pytest.mark.parametrize("dimension", ["Theta", "\u0398", "\u03b8"])
def test_temperature_signature_aliases_remain_supported(tmp_path: Path, dimension: str) -> None:
    repo = _repo(tmp_path, FormDefinition(name="temperature", kind=KindType.QUANTITY, unit_symbol="K", dimensions={dimension: 1}))
    report = validate_claim(_parameter("temperature", "degC"), context=build_compilation_context_from_repo(repo))
    assert not report.diagnostics


def test_build_counts_quarantined_claims_once_with_multiple_diagnostics(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    claim = Claim(claim_id="invalid", claim_type=ClaimType.PARAMETER, output_concept="output", value="not_numeric", unit="kg")
    repo.families.claim.save(claim.claim_id, claim, message="Author invalid claim")
    built = build_repository(repo)
    assert len(built.errors) == 2
    assert built.claim_count == built.blocked_claim_count == 1


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


def test_omitted_unit_is_one_when_canonical_unit_is_percent(tmp_path: Path) -> None:
    from propstore.dimensions import from_si, normalize_to_si

    form = FormDefinition(name="ratio", kind=KindType.QUANTITY, is_dimensionless=True, unit_symbol="percent")
    repo = _repo(tmp_path, form)
    claims = (
        _parameter("implicit_one", None),
        Claim(claim_id="percent", claim_type=ClaimType.PARAMETER, output_concept="output", value=100, unit="percent"),
    )
    for claim in claims:
        repo.families.claim.save(claim.claim_id, claim, message="Author equivalent ratio")
    assert validate_repository(repo).ok
    built = build_repository(repo)
    assert built.blocked_claim_count == 0
    assert built.conflicts == ()
    assert normalize_to_si(1.0, None, form) == 100.0
    assert from_si(100.0, None, form) == 1.0
    assert [repo.families.claim.load(claim.claim_id) for claim in claims] == list(claims)


@pytest.mark.parametrize("conversion", [
    UnitConversion(unit="unusable_force", type="logarithmic", divisor=0),
    UnitConversion(unit="unusable_force", type="logarithmic", base=1),
    UnitConversion(unit="unusable_force", type="multiplicative", multiplier=0),
])
def test_unusable_conversion_evidence_quarantines_before_comparison(tmp_path: Path, conversion: UnitConversion) -> None:
    repo = _repo(tmp_path, FormDefinition(
        name="force", kind=KindType.QUANTITY, unit_symbol="N", dimensions={"M": 1, "L": 1, "T": -2},
        conversions={"unusable_force": conversion},
    ))
    claims = (_parameter("valid", "N"), _parameter("unusable", "unusable_force"))
    for claim in claims:
        repo.families.claim.save(claim.claim_id, claim, message="Author rival")
    built = build_repository(repo)
    validation = validate_repository(repo)
    assert built.blocked_claim_count == 1
    assert built.conflicts == ()
    assert not validation.ok
    assert any(problem.code == "claim.unit.form.invalid" for problem in validation.errors)
    assert [repo.families.claim.load(claim.claim_id) for claim in claims] == list(claims)


def test_compound_units_can_use_declared_extra_units(tmp_path: Path) -> None:
    repo = _repo(tmp_path, FormDefinition(
        name="pressure", kind=KindType.QUANTITY, unit_symbol="Pa", dimensions={"M": 1, "L": -1, "T": -2},
        extra_units=(ExtraUnitDefinition(symbol="unit_admission_compound_newton", dimensions={"M": 1, "L": 1, "T": -2}),),
    ))
    for claim in (_parameter("canonical", "Pa"), _parameter("compound", "unit_admission_compound_newton / m**2")):
        repo.families.claim.save(claim.claim_id, claim, message="Author equivalent pressure")
    assert validate_repository(repo).ok
    built = build_repository(repo)
    assert built.blocked_claim_count == 0
    assert built.conflicts == ()


def test_parameterization_uses_omitted_dimensionless_default(tmp_path: Path) -> None:
    repo = _repo(tmp_path, FormDefinition(name="ratio", kind=KindType.QUANTITY, is_dimensionless=True, unit_symbol="percent"))
    repo.families.concept.save("input", Concept(
        concept_id="input", canonical_name="input",
        lexical_entry=LexicalEntry(
            identifier="entry:input",
            canonical_form=LexicalForm(written_rep="input", language="en"),
            senses=(LexicalSense(reference=OntologyReference(uri="urn:input")),),
            physical_dimension_form="ratio",
        ),
    ), message="Declare input")
    for claim in (
        Claim(claim_id="input", claim_type=ClaimType.PARAMETER, output_concept="input", value=1, unit=None),
        Claim(claim_id="output", claim_type=ClaimType.PARAMETER, output_concept="output", value=100, unit="percent"),
        Claim(claim_id="identity", claim_type=ClaimType.EQUATION, output_concept="output", concepts=("input",),
              expression="out = inp", sympy="input", exactness=Exactness.EXACT,
              variables=(ClaimVariable(concept="output", symbol="out"), ClaimVariable(concept="input", symbol="inp"))),
    ):
        repo.families.claim.save(claim.claim_id, claim, message="Author identity")
    assert validate_repository(repo).ok
    built = build_repository(repo)
    assert built.blocked_claim_count == 0
    assert built.conflicts == ()


def test_logarithmic_value_overflow_is_quarantined_before_comparison(tmp_path: Path) -> None:
    repo = _repo(tmp_path, FormDefinition(
        name="force", kind=KindType.QUANTITY, unit_symbol="N", dimensions={"M": 1, "L": 1, "T": -2},
        conversions={"log_force": UnitConversion(unit="log_force", type="logarithmic")},
    ))
    for claim in (
        _parameter("valid", "N"),
        Claim(claim_id="overflow", claim_type=ClaimType.PARAMETER, output_concept="output", value=10000, unit="log_force"),
    ):
        repo.families.claim.save(claim.claim_id, claim, message="Author force")
    built = build_repository(repo)
    assert built.blocked_claim_count == 1
    assert built.conflicts == ()
    assert any(problem.code == "claim.unit.conversion.invalid" for problem in built.errors)


def test_linear_conversion_cannot_relabel_known_mass_as_force(tmp_path: Path) -> None:
    repo = _repo(tmp_path, FormDefinition(
        name="force", kind=KindType.QUANTITY, unit_symbol="N", dimensions={"M": 1, "L": 1, "T": -2},
        conversions={"kg": UnitConversion(unit="kg", type="multiplicative")},
    ))
    repo.families.claim.save("mass", _parameter("mass", "kg"), message="Author force")
    assert not validate_repository(repo).ok
    assert build_repository(repo).blocked_claim_count == 1
