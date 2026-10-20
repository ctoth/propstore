"""Repository-derived formulas retain the applicability of their equation."""

import json
from dataclasses import replace
from pathlib import Path

import pytest
from argumentation.core.dung import grounded_extension
from condition_ir import (
    ConceptInfo,
    KindType,
    check_condition_ir,
    checked_condition_set,
    checked_condition_set_to_json,
)

from propstore.conflict_detector.models import ConflictClass
from propstore.aspic_bridge.projection import build_aspic_projection
from propstore.core.environment import Environment
from propstore.core.graph_types import CompiledWorldGraph
from propstore.core.id_types import to_claim_id
from propstore.core.labels import environment_context_ids
from propstore.core.lemon import (
    LexicalEntry,
    LexicalForm,
    LexicalSense,
    OntologyReference,
)
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context, LiftingRule
from propstore.families.forms import FormDefinition
from propstore.families.justifications import Justification
from propstore.repository import Repository
from propstore.sensitivity import analyze_sensitivity
from propstore.world import OverlayWorld, RenderPolicy, WorldQuery
from propstore.world.types import ReasoningBackend, ValueStatus


def _repo(
    tmp_path: Path,
    *,
    lift: str = "absent",
    rival: bool = False,
    conditions: tuple[str, ...] = (),
) -> Repository:
    repo = Repository.init(tmp_path / "knowledge")
    repo.families.form.save(
        "quantity",
        FormDefinition(name="quantity", kind=KindType.QUANTITY),
        message="form",
    )
    for concept_id in ("x", "y"):
        repo.families.concept.save(
            concept_id,
            Concept(
                concept_id=concept_id,
                canonical_name=concept_id,
                lexical_entry=LexicalEntry(
                    identifier=f"entry:{concept_id}",
                    canonical_form=LexicalForm(written_rep=concept_id, language="en"),
                    senses=(LexicalSense(reference=OntologyReference(uri=concept_id)),),
                    physical_dimension_form="quantity",
                ),
            ),
            message="concept",
        )
    for context_id in ("a", "b"):
        repo.families.context.save(
            context_id,
            Context(context_id=context_id, name=context_id),
            message="context",
        )
    repo.families.claim.save(
        "a_input",
        Claim(
            claim_id="a_input",
            claim_type=ClaimType.PARAMETER,
            output_concept="x",
            value=3,
        ),
        message="input",
    )
    registry = {"x": ConceptInfo(id="x", canonical_name="x", kind=KindType.QUANTITY)}
    conditions_ir = (
        json.dumps(
            checked_condition_set_to_json(
                checked_condition_set(
                    check_condition_ir(source, registry) for source in conditions
                )
            )
        )
        if conditions
        else None
    )
    for context_id, multiplier in (("a", 2), ("b", 3)) if rival else (("a", 2),):
        claim_id = f"equation_{context_id}"
        repo.families.claim.save(
            claim_id,
            Claim(
                claim_id=claim_id,
                claim_type=ClaimType.EQUATION,
                context_id=context_id,
                output_concept="y",
                concepts=("x",),
                expression=f"{multiplier} * x",
                sympy=f"Eq(y, {multiplier} * x)",
                conditions=conditions,
                conditions_ir=conditions_ir,
            ),
            message="equation",
        )
    if lift != "absent":
        repo.families.lifting_rule.save(
            "lift",
            LiftingRule(
                rule_id="lift",
                source_context="a",
                target_context="b",
                conditions=("true",) if lift == "gated" else (),
            ),
            message="lift",
        )
    return repo


@pytest.mark.parametrize(
    "backend", [ReasoningBackend.CLAIM_GRAPH, ReasoningBackend.ATMS]
)
@pytest.mark.parametrize(
    ("context_id", "lift", "expected"),
    [
        ("a", "absent", 6),
        ("b", "absent", None),
        ("b", "unconditional", 6),
        ("b", "gated", None),
    ],
)
def test_derivation_and_sensitivity_follow_equation_activation(
    tmp_path: Path,
    backend: ReasoningBackend,
    context_id: str,
    lift: str,
    expected: int | None,
) -> None:
    with WorldQuery(_repo(tmp_path, lift=lift)) as world:
        bound = world.bind(
            Environment(context_id=context_id),
            policy=RenderPolicy(reasoning_backend=backend),
        )
        (edge,) = world.all_parameterizations()
        assert edge.equation_claim_id == "equation_a"
        equation = world.get_claim("equation_a")
        assert equation is not None
        assert bound.is_param_compatible(edge) == bound.is_active(equation)
        result = bound.derived_value("y")
        sensitivity = analyze_sensitivity(world, "y", bound)
        if expected is None:
            assert result.status is ValueStatus.NO_RELATIONSHIP
            assert sensitivity is None
            assert bound.atms_engine().derived_label("y", 6) is None
        else:
            assert result.status is ValueStatus.DERIVED
            assert result.value == expected
            assert result.equation_claim_id == "equation_a"
            assert result.label is not None
            assert all(
                "a" in environment_context_ids(env) for env in result.label.environments
            )
            assert sensitivity is not None
            engine = bound.atms_engine()
            assert engine.derived_label("y", 6) == engine.claim_label("equation_a")
        # Binding never changes the stored inventory, including inactive edges.
        assert len(world.all_parameterizations()) == 1


def test_rival_equations_keep_individual_origins_and_scopes(tmp_path: Path) -> None:
    with WorldQuery(_repo(tmp_path, rival=True)) as world:
        edges = world.all_parameterizations()
        assert {edge.equation_claim_id for edge in edges} == {
            "equation_a",
            "equation_b",
        }
        for context_id, expected in (("a", 6), ("b", 9)):
            bound = world.bind(Environment(context_id=context_id))
            result = bound.derived_value("y")
            assert result.status is ValueStatus.DERIVED
            assert result.value == expected
            assert result.equation_claim_id == f"equation_{context_id}"
            assert bound.atms_engine().derived_label("y", expected) is not None


def test_referenced_equation_must_exist_and_mixed_edges_sort(tmp_path: Path) -> None:
    with WorldQuery(_repo(tmp_path)) as world:
        (edge,) = world.all_parameterizations()
        bound = world.bind(Environment(context_id="a"))
        assert not bound.is_param_compatible(
            replace(edge, equation_claim_id=to_claim_id("missing"))
        )
        bare = replace(edge, equation_claim_id=None)
        graph = CompiledWorldGraph(parameterizations=(edge, bare))
        assert len(graph.parameterizations) == 2
        assert edge != bare


@pytest.mark.parametrize(
    "backend", [ReasoningBackend.CLAIM_GRAPH, ReasoningBackend.ATMS]
)
def test_equation_conditions_are_required_for_applicability_and_support(
    tmp_path: Path, backend: ReasoningBackend
) -> None:
    with WorldQuery(_repo(tmp_path, conditions=("x == 3",))) as world:
        policy = RenderPolicy(reasoning_backend=backend)
        bound = world.bind(
            Environment(context_id="a", bindings={"x": 3}), policy=policy
        )
        result = bound.derived_value("y")
        assert result.status is ValueStatus.DERIVED
        assert result.value == 6
        equation_label = bound.atms_engine().claim_label("equation_a")
        assert equation_label is not None
        assert result.label == equation_label
        assert bound.atms_engine().derived_label("y", 6) == equation_label
        assert all(env.variables for env in equation_label.environments)
        rejected = world.bind(
            Environment(context_id="a", bindings={"x": 4}), policy=policy
        )
        assert rejected.derived_value("y").status is ValueStatus.NO_RELATIONSHIP
        assert rejected.atms_engine().derived_label("y", 6) is None


@pytest.mark.parametrize(
    "backend", [ReasoningBackend.CLAIM_GRAPH, ReasoningBackend.ATMS]
)
def test_equation_and_canonical_justification_share_withdrawn_support(
    tmp_path: Path, backend: ReasoningBackend
) -> None:
    repo = _repo(tmp_path)
    repo.families.claim.save(
        "application",
        Claim(
            claim_id="application",
            claim_type=ClaimType.OBSERVATION,
            context_id="a",
            concepts=("y",),
            statement="The equation and input support this application.",
        ),
        message="application",
    )
    licence = Justification(
        justification_id="application-support",
        conclusion="application",
        premises=("equation_a", "a_input"),
        rule_kind="methodological_inference",
        rule_strength="defeasible",
    )
    repo.families.justification.save(
        licence.justification_id, licence, message="application support"
    )
    with WorldQuery(repo) as world:
        graph = world.compiled_graph()
        assert graph.justifications == (licence,)
        assert graph.parameterizations[0].equation_claim_id == "equation_a"
        bound = world.bind(
            Environment(context_id="a"),
            policy=RenderPolicy(reasoning_backend=backend),
        )
        withdrawn = OverlayWorld(bound, remove=("equation_a",))
        for view, supported in ((bound, True), (withdrawn, False)):
            assert view.store.all_justifications() == [licence]
            projection = build_aspic_projection(
                view.store, view.active_claims(), bundle=world.grounding_bundle()
            )
            accepted = grounded_extension(projection.framework)
            arguments = set(projection.claim_to_argument_ids.get("application", ()))
            assert bool(arguments & accepted) is supported
            result = view.derived_value("y")
            assert result.status is (
                ValueStatus.DERIVED if supported else ValueStatus.NO_RELATIONSHIP
            )
        assert bound.derived_value("y").value == 6
        assert world.get_claim("equation_a") is not None


def test_context_separation_and_equation_support_coexist(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    repo.families.concept.save(
        "contextual",
        Concept(concept_id="contextual", canonical_name="contextual"),
        message="contextual parameter",
    )
    for context_id, value in (("a", 1), ("b", 2)):
        claim_id = f"context_{context_id}"
        repo.families.claim.save(
            claim_id,
            Claim(
                claim_id=claim_id,
                claim_type=ClaimType.PARAMETER,
                context_id=context_id,
                output_concept="contextual",
                value=value,
            ),
            message="context-separated value",
        )
    with WorldQuery(repo) as world:
        assert any(
            conflict.warning_class is ConflictClass.CONTEXT_PHI_NODE
            for conflict in world.conflicts()
        )
        bound = world.bind(policy=RenderPolicy(reasoning_backend=ReasoningBackend.ATMS))
        engine = bound.atms_engine()
        assert {"context_a", "context_b"} <= engine.supported_claim_ids()
        assert not engine.nogoods.environments
        result = bound.derived_value("y")
        assert result.status is ValueStatus.DERIVED and result.value == 6
        assert result.equation_claim_id == "equation_a"
        assert result.label is not None
        assert result.label == engine.claim_label("equation_a")
        assert all(
            "a" in environment_context_ids(env) for env in result.label.environments
        )
