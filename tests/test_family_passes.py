"""Per-family semantic pipelines over the flat charters.

Each family's AUTHORED -> CHECKED pipeline is exercised directly. The Z1 split is
visible at the pass level: form / concept / context validation failures produce
NO checked output (the runner short-circuits, so the workflow aborts), while the
claim pipeline ALWAYS produces a bundle (invalid claims are blocked, quarantined).
"""

from __future__ import annotations

from condition_ir import (
    ConditionBinary,
    ConditionReference,
    KindType,
    check_cel_expression,
    check_condition_ir,
)

from propstore.compiler.context import build_compilation_context
from propstore.compiler.ir import ClaimCheckedBundle
from propstore.families.claims import Claim, ClaimType
from propstore.families.claims_passes import ClaimFiles, LoadedClaim, run_claim_pipeline
from propstore.families.concepts import Concept
from propstore.families.concepts_passes import (
    ConceptCheckedRegistry,
    ConceptPipelineContext,
    LoadedConcept,
    run_concept_pipeline,
)
from propstore.families.contexts import Context, LiftingRule
from propstore.families.contexts_passes import (
    ContextCheckedGraph,
    LoadedContext,
    LoadedLiftingRule,
    run_context_pipeline,
)
from propstore.core.lemon import (
    LexicalEntry,
    LexicalForm,
    LexicalSense,
    OntologyReference,
)
from propstore.families.forms import FormDefinition
from propstore.families.forms_passes import (
    FormCheckedRegistry,
    LoadedForm,
    run_form_pipeline,
)


# --- forms ----------------------------------------------------------------- #


def test_form_pipeline_builds_registry() -> None:
    forms = [
        LoadedForm(
            form=FormDefinition(
                name="mass", kind=KindType.QUANTITY, dimensions={"mass": 1}
            )
        )
    ]
    result = run_form_pipeline(forms)
    assert isinstance(result.output, FormCheckedRegistry)
    assert "mass" in result.output.registry


def test_form_pipeline_duplicate_name_short_circuits() -> None:
    forms = [
        LoadedForm(
            form=FormDefinition(
                name="m", kind=KindType.QUANTITY, dimensions={"mass": 1}
            )
        ),
        LoadedForm(
            form=FormDefinition(
                name="m", kind=KindType.QUANTITY, dimensions={"mass": 1}
            )
        ),
    ]
    result = run_form_pipeline(forms)
    assert result.output is None
    assert any(d.code == "form.id.duplicate" for d in result.errors)


def test_form_pipeline_invalid_dimensions_short_circuits() -> None:
    forms = [
        LoadedForm(
            form=FormDefinition(
                name="bad",
                kind=KindType.QUANTITY,
                is_dimensionless=True,
                dimensions={"mass": 1},
            )
        )
    ]
    result = run_form_pipeline(forms)
    assert result.output is None
    assert result.errors


# --- concepts -------------------------------------------------------------- #


def test_concept_pipeline_keeps_missing_form_out_of_condition_registry() -> None:
    concepts = [LoadedConcept(concept=Concept(concept_id="c1", canonical_name="C1"))]
    result = run_concept_pipeline(concepts)
    assert isinstance(result.output, ConceptCheckedRegistry)
    assert "c1" in result.output.by_id
    assert result.output.condition_registry == {}


def test_concept_pipeline_preserves_identity_symbol_and_lexical_form() -> None:
    concept = Concept(
        concept_id="ps:concept:frequency",
        canonical_name="frequency",
        lexical_entry=LexicalEntry(
            identifier="entry:frequency",
            canonical_form=LexicalForm(
                written_rep="Fundamental frequency", language="en"
            ),
            senses=(
                LexicalSense(reference=OntologyReference(uri="ps:concept:frequency")),
            ),
            physical_dimension_form="frequency",
        ),
    )
    result = run_concept_pipeline(
        [LoadedConcept(concept=concept)],
        context=ConceptPipelineContext(
            form_registry={
                "frequency": FormDefinition(name="frequency", kind=KindType.QUANTITY)
            }
        ),
    )

    assert isinstance(result.output, ConceptCheckedRegistry)
    checked = result.output.by_id["ps:concept:frequency"]
    assert checked.concept_id == "ps:concept:frequency"
    assert checked.canonical_name == "frequency"
    assert checked.lexical_entry is not None
    assert checked.lexical_entry.canonical_form.written_rep == "Fundamental frequency"
    info = result.output.condition_registry["frequency"]
    assert info.id == "ps:concept:frequency"

    assert not check_cel_expression("frequency > 10", result.output.condition_registry)
    lowered = check_condition_ir("frequency > 10", result.output.condition_registry).ir
    assert isinstance(lowered, ConditionBinary)
    assert isinstance(lowered.left, ConditionReference)
    assert lowered.left.concept_id == "ps:concept:frequency"
    assert check_cel_expression(
        "ps:concept:frequency > 10", result.output.condition_registry
    )


def test_concept_pipeline_projects_explicit_closed_category() -> None:
    concept = Concept(
        concept_id="ps:concept:severity",
        canonical_name="severity",
        category_values=("low", "medium", "high"),
        category_extensible=False,
        lexical_entry=LexicalEntry(
            identifier="entry:severity",
            canonical_form=LexicalForm(written_rep="Severity", language="en"),
            senses=(
                LexicalSense(reference=OntologyReference(uri="ps:concept:severity")),
            ),
            physical_dimension_form="category",
        ),
    )
    result = run_concept_pipeline(
        [LoadedConcept(concept=concept)],
        context=ConceptPipelineContext(
            form_registry={
                "category": FormDefinition(name="category", kind=KindType.CATEGORY)
            }
        ),
    )

    assert isinstance(result.output, ConceptCheckedRegistry)
    info = result.output.condition_registry["severity"]
    assert info.kind is KindType.CATEGORY
    assert info.category_values == ["low", "medium", "high"]
    assert info.category_extensible is False


def test_concept_pipeline_rejects_category_metadata_on_quantity() -> None:
    concept = Concept(
        concept_id="ps:concept:frequency",
        canonical_name="frequency",
        category_values=("low", "high"),
        lexical_entry=LexicalEntry(
            identifier="entry:frequency",
            canonical_form=LexicalForm(written_rep="Frequency", language="en"),
            senses=(
                LexicalSense(reference=OntologyReference(uri="ps:concept:frequency")),
            ),
            physical_dimension_form="frequency",
        ),
    )
    result = run_concept_pipeline(
        [LoadedConcept(concept=concept)],
        context=ConceptPipelineContext(
            form_registry={
                "frequency": FormDefinition(name="frequency", kind=KindType.QUANTITY)
            }
        ),
    )

    assert result.output is None
    assert any(
        diagnostic.code == "concept.category_metadata.invalid_kind"
        for diagnostic in result.errors
    )


def test_concept_pipeline_duplicate_id_short_circuits() -> None:
    concepts = [
        LoadedConcept(concept=Concept(concept_id="c1", canonical_name="A")),
        LoadedConcept(concept=Concept(concept_id="c1", canonical_name="B")),
    ]
    result = run_concept_pipeline(concepts)
    assert result.output is None
    assert any(d.code == "concept.id.duplicate" for d in result.errors)


def test_concept_pipeline_invalid_canonical_name_short_circuits() -> None:
    result = run_concept_pipeline(
        [
            LoadedConcept(
                concept=Concept(
                    concept_id="ps:concept:draft_concept",
                    canonical_name="Draft Concept",
                )
            )
        ]
    )

    assert result.output is None
    assert any(d.code == "concept.canonical_name.invalid" for d in result.errors)


def test_concept_pipeline_duplicate_canonical_name_short_circuits() -> None:
    result = run_concept_pipeline(
        [
            LoadedConcept(concept=Concept(concept_id="c1", canonical_name="shared")),
            LoadedConcept(concept=Concept(concept_id="c2", canonical_name="shared")),
        ]
    )

    assert result.output is None
    assert any(d.code == "concept.canonical_name.duplicate" for d in result.errors)


def test_concept_pipeline_dangling_form_is_warning_not_abort() -> None:
    concept = Concept(
        concept_id="width",
        canonical_name="width",
        lexical_entry=LexicalEntry(
            identifier="e:width",
            canonical_form=LexicalForm(written_rep="width", language="en"),
            senses=(LexicalSense(reference=OntologyReference(uri="u:width")),),
            physical_dimension_form="missing_form",
        ),
    )
    result = run_concept_pipeline(
        [LoadedConcept(concept=concept)],
        context=ConceptPipelineContext(form_registry={}),
    )
    assert isinstance(result.output, ConceptCheckedRegistry)
    assert any(
        d.code == "concept.form.dangling" and d.is_warning for d in result.warnings
    )
    assert "width" not in result.output.condition_registry


# --- contexts -------------------------------------------------------------- #


def test_context_pipeline_builds_graph() -> None:
    contexts = [LoadedContext(context=Context(context_id="ctx1", name="C1"))]
    result = run_context_pipeline(contexts)
    assert isinstance(result.output, ContextCheckedGraph)
    assert result.output.context_ids == frozenset({"ctx1"})


def test_context_pipeline_duplicate_id_short_circuits() -> None:
    contexts = [
        LoadedContext(context=Context(context_id="ctx1", name="A")),
        LoadedContext(context=Context(context_id="ctx1", name="B")),
    ]
    result = run_context_pipeline(contexts)
    assert result.output is None
    assert any(d.code == "context.id.duplicate" for d in result.errors)


def test_context_pipeline_missing_lifting_target_short_circuits() -> None:
    contexts = [LoadedContext(context=Context(context_id="ctx1", name="C1"))]
    rules = [
        LoadedLiftingRule(
            rule=LiftingRule(
                rule_id="r1", source_context="ctx1", target_context="ghost"
            )
        )
    ]
    result = run_context_pipeline(contexts, lifting_rules=rules)
    assert result.output is None
    assert any(d.code == "context.lifting.target_missing" for d in result.errors)


# --- claims (always a bundle; quarantine, never abort) --------------------- #


def test_claim_pipeline_valid_claim_not_blocked() -> None:
    concept_result = run_concept_pipeline([])
    assert isinstance(concept_result.output, ConceptCheckedRegistry)
    context = build_compilation_context(concept_result.output, context_ids={"ctx1"})
    claim = Claim(
        claim_id="c1",
        context_id="ctx1",
        claim_type=ClaimType.OBSERVATION,
        statement="something observed",
        concepts=("x",),
    )
    bundle = run_claim_pipeline(
        ClaimFiles.from_sequence([LoadedClaim(claim=claim)], context)
    ).output
    assert isinstance(bundle, ClaimCheckedBundle)
    assert len(bundle.checked_claims) == 1
    assert not bundle.blocked_claims


def test_claim_pipeline_invalid_claim_is_blocked_not_aborted() -> None:
    concept_result = run_concept_pipeline([])
    assert isinstance(concept_result.output, ConceptCheckedRegistry)
    context = build_compilation_context(concept_result.output, context_ids={"ctx1"})
    # PARAMETER requires output_concept; this one omits it -> blocked, retained.
    claim = Claim(claim_id="c2", context_id="ctx1", claim_type=ClaimType.PARAMETER)
    result = run_claim_pipeline(
        ClaimFiles.from_sequence([LoadedClaim(claim=claim)], context)
    )
    bundle = result.output
    assert isinstance(bundle, ClaimCheckedBundle)
    assert len(bundle.blocked_claims) == 1
    assert bundle.blocked_claims[0].claim.claim_id == "c2"


def test_claim_pipeline_blocks_value_outside_closed_category() -> None:
    form = FormDefinition(name="category", kind=KindType.CATEGORY)
    concept = Concept(
        concept_id="ps:concept:severity",
        canonical_name="severity",
        category_values=("low", "high"),
        category_extensible=False,
        lexical_entry=LexicalEntry(
            identifier="entry:severity",
            canonical_form=LexicalForm(written_rep="Severity", language="en"),
            senses=(
                LexicalSense(reference=OntologyReference(uri="ps:concept:severity")),
            ),
            physical_dimension_form="category",
        ),
    )
    concept_result = run_concept_pipeline(
        [LoadedConcept(concept=concept)],
        context=ConceptPipelineContext(form_registry={"category": form}),
    )
    assert isinstance(concept_result.output, ConceptCheckedRegistry)
    context = build_compilation_context(
        concept_result.output,
        form_registry={"category": form},
    )
    claim = Claim(
        claim_id="unknown-severity",
        claim_type=ClaimType.PARAMETER,
        output_concept="ps:concept:severity",
        value="critical",
    )

    result = run_claim_pipeline(
        ClaimFiles.from_sequence([LoadedClaim(claim=claim)], context)
    )
    bundle = result.output
    assert isinstance(bundle, ClaimCheckedBundle)
    assert bundle.blocked_claims
    assert any(
        diagnostic.code == "claim.contract"
        and "closed category vocabulary" in diagnostic.message
        for diagnostic in bundle.blocked_claims[0].diagnostics
    )


def test_claim_pipeline_dangling_context_is_blocked() -> None:
    # A claim whose context is not among the known contexts is quarantined
    # (blocked) at the pass level. (Through the canonical store the FK is also
    # enforced on write; the pass is a defensive net for out-of-band content.)
    concept_result = run_concept_pipeline([])
    assert isinstance(concept_result.output, ConceptCheckedRegistry)
    context = build_compilation_context(concept_result.output, context_ids={"ctx1"})
    claim = Claim(
        claim_id="c4",
        context_id="ghost",
        claim_type=ClaimType.OBSERVATION,
        statement="x",
    )
    bundle = run_claim_pipeline(
        ClaimFiles.from_sequence([LoadedClaim(claim=claim)], context)
    ).output
    assert isinstance(bundle, ClaimCheckedBundle)
    assert bundle.blocked_claims
    assert any(
        d.code == "claim.context.dangling" for d in bundle.blocked_claims[0].diagnostics
    )


def test_claim_pipeline_normalizes_conditions_ir() -> None:
    concept_result = run_concept_pipeline([])
    assert isinstance(concept_result.output, ConceptCheckedRegistry)
    context = build_compilation_context(concept_result.output, context_ids={"ctx1"})
    claim = Claim(
        claim_id="c3",
        context_id="ctx1",
        claim_type=ClaimType.OBSERVATION,
        statement="x",
    )
    bundle = run_claim_pipeline(
        ClaimFiles.from_sequence([LoadedClaim(claim=claim)], context)
    ).output
    assert isinstance(bundle, ClaimCheckedBundle)
    assert bundle.claims[0].claim.conditions_ir is not None
