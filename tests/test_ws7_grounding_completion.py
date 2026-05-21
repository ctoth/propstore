"""WS7 grounding-completion contract tests."""

from __future__ import annotations

from pathlib import Path

from argumentation.aspic import GroundAtom
from quire.sqlalchemy_store import create_sqlalchemy_store, readonly_session, writable_session
from tests.family_helpers import world_query_from_sqlite_path


def _build_predicate_document(
    predicate_id: str,
    arity: int,
    arg_types: tuple[str, ...],
    derived_from: str | None,
):
    from propstore.families.documents.predicates import PredicateDocument

    return PredicateDocument(
        id=predicate_id,
        arity=arity,
        arg_types=arg_types,
        derived_from=derived_from,
        description=None,
    )


def _build_registry(predicates):
    from propstore.grounding.predicates import PredicateRegistry

    return PredicateRegistry.from_documents(tuple(predicates))


def _claim_file_from_payload(payload: dict):
    from propstore.claims import loaded_claim_file_from_payload
    from tests.conftest import normalize_claims_payload

    normalized = normalize_claims_payload(payload)
    source = normalized.get("source", {})
    return tuple(
        loaded_claim_file_from_payload(
            filename=f"claims.yaml#{index}",
            source_path=None,
            knowledge_root=None,
            data={"source": source, "claims": [claim]},
        )
        for index, claim in enumerate(normalized.get("claims", []), start=1)
    )


def _ws7_claim_file():
    return _claim_file_from_payload(
        {
            "source": {"paper": "Garcia_2004_DefeasibleLogicProgramming"},
            "claims": [
                {
                    "id": "claim-tweety",
                    "type": "parameter",
                    "output_concept": "concept:bird",
                    "value": 42,
                    "sample_size": 11,
                    "conditions": ["habitat == 'wetland'"],
                    "context": {"id": "ctx-field"},
                    "provenance": {
                        "paper": "Garcia_2004_DefeasibleLogicProgramming",
                        "page": 25,
                    },
                },
                {
                    "id": "claim-flight",
                    "type": "observation",
                    "concepts": ["concept:bird", "concept:flight"],
                    "statement": "Tweety usually flies.",
                    "context": {"id": "ctx-field"},
                    "provenance": {
                        "paper": "Diller_2025_GroundingRuleBasedArgumentationDatalog",
                        "page": 8,
                    },
                },
            ],
        }
    )


def _bundle_with_four_statuses():
    from types import MappingProxyType

    from propstore.grounding.bundle import GroundedRulesBundle

    return GroundedRulesBundle(
        source_rules=(),
        source_facts=(),
        sections=MappingProxyType(
            {
                "yes": MappingProxyType(
                    {"strict_fact": frozenset({("claim-tweety",)})}
                ),
                "no": MappingProxyType(
                    {"grounded_out": frozenset({("claim-flight",)})}
                ),
                "undecided": MappingProxyType(
                    {"contested": frozenset({("claim-flight",)})}
                ),
                "unknown": MappingProxyType(
                    {"flies": frozenset({("tweety",)})}
                ),
            }
        ),
    )


def _runtime_grounded_bundle():
    from propstore.grounding.grounder import ground
    from propstore.grounding.predicates import PredicateRegistry

    return ground(
        (),
        (GroundAtom("bird", ("tweety",)),),
        PredicateRegistry(()),
        return_arguments=True,
    )


def test_ws7_extract_facts_materializes_claim_structural_sources() -> None:
    from propstore.claims import claim_file_claims
    from propstore.grounding.facts import GroundingFactInputs, extract_facts

    registry = _build_registry(
        [
            _build_predicate_document(
                "claim_sample_size",
                2,
                ("Claim", "Scalar"),
                "claim.attribute:sample_size",
            ),
            _build_predicate_document(
                "claim_condition",
                2,
                ("Claim", "Scalar"),
                "claim.condition:habitat == 'wetland'",
            ),
            _build_predicate_document(
                "claim_context",
                2,
                ("Claim", "Context"),
                "claim.context",
            ),
            _build_predicate_document(
                "claim_page",
                2,
                ("Claim", "Scalar"),
                "claim.provenance:page",
            ),
            _build_predicate_document(
                "claim_output_concept",
                2,
                ("Claim", "Concept"),
                "claim.role:output",
            ),
            _build_predicate_document(
                "claim_about_concept",
                2,
                ("Claim", "Concept"),
                "claim.role:about",
            ),
        ]
    )

    claim_files = _ws7_claim_file()
    claim_ids = {
        claim.primary_logical_id: claim.artifact_id
        for claim_file in claim_files
        for claim in claim_file_claims(claim_file)
    }
    tweety_claim_id = claim_ids["Garcia_2004_DefeasibleLogicProgramming:claim-tweety"]
    flight_claim_id = claim_ids["Garcia_2004_DefeasibleLogicProgramming:claim-flight"]

    atoms = extract_facts(
        GroundingFactInputs(claim_files=claim_files),
        registry,
    )

    assert set(atoms) == {
        GroundAtom("claim_sample_size", (tweety_claim_id, 11)),
        GroundAtom("claim_condition", (tweety_claim_id, "habitat == 'wetland'")),
        GroundAtom("claim_context", (tweety_claim_id, "ctx-field")),
        GroundAtom("claim_context", (flight_claim_id, "ctx-field")),
        GroundAtom("claim_page", (tweety_claim_id, 25)),
        GroundAtom("claim_page", (flight_claim_id, 8)),
        GroundAtom("claim_output_concept", (tweety_claim_id, "concept:bird")),
        GroundAtom("claim_about_concept", (flight_claim_id, "concept:bird")),
        GroundAtom("claim_about_concept", (flight_claim_id, "concept:flight")),
    }


def test_ws7_sidecar_runtime_bundle_preserves_four_statuses(tmp_path: Path) -> None:
    from propstore.families.rules.declaration import (
        load_grounded_sections,
        persist_grounded_bundle,
    )
    from propstore.families.world_charters import world_sqlalchemy_schema

    sidecar_path = tmp_path / "ws7-grounding.sqlite"
    create_sqlalchemy_store(sidecar_path, world_sqlalchemy_schema())
    bundle = _bundle_with_four_statuses()

    with writable_session(sidecar_path, world_sqlalchemy_schema()) as derived:
        persist_grounded_bundle(derived, bundle)
        derived.session.commit()
    with readonly_session(sidecar_path, world_sqlalchemy_schema()) as derived:
        restored = load_grounded_sections(derived)

    assert restored == bundle.sections


def test_ws7_world_model_reads_grounding_bundle_from_sidecar(
    tmp_path: Path,
) -> None:
    from propstore.families.rules.declaration import (
        persist_grounded_bundle,
    )
    from propstore.families.world_charters import (
        PROPSTORE_WORLD_META_KEY,
        PROPSTORE_WORLD_SCHEMA_VERSION,
        WorldMeta,
        world_sqlalchemy_schema,
    )

    sidecar_path = tmp_path / "propstore.sqlite"
    create_sqlalchemy_store(sidecar_path, world_sqlalchemy_schema())
    with writable_session(sidecar_path, world_sqlalchemy_schema()) as derived:
        derived.add(
            WorldMeta(
                key=PROPSTORE_WORLD_META_KEY,
                schema_version=PROPSTORE_WORLD_SCHEMA_VERSION,
            )
        )
        persist_grounded_bundle(derived, _runtime_grounded_bundle())
        derived.session.commit()

    with world_query_from_sqlite_path(sidecar_path) as world:
        bundle = world.grounding_bundle()

    assert bundle.sections["yes"]["bird"] == frozenset({("tweety",)})
    assert bundle.grounding_inspection is not None
