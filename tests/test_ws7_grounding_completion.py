"""WS7 grounding-completion contract tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from argumentation.aspic import GroundAtom
from quire.documents import LoadedDocument


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
    from propstore.families.documents.predicates import PredicatesFileDocument
    from propstore.grounding.predicates import PredicateRegistry
    from propstore.predicate_files import LoadedPredicateFile

    loaded = LoadedDocument(
        filename="generated.yaml",
        source_path=None,
        knowledge_root=None,
        document=PredicatesFileDocument(predicates=tuple(predicates)),
    )
    return PredicateRegistry.from_files(
        (LoadedPredicateFile.from_loaded_document(loaded),)
    )


def _claim_file_from_payload(payload: dict):
    from propstore.claims import loaded_claim_file_from_payload

    return loaded_claim_file_from_payload(
        filename="claims.yaml",
        source_path=None,
        knowledge_root=None,
        data=payload,
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
                "definitely": MappingProxyType(
                    {"strict_fact": frozenset({("claim-tweety",)})}
                ),
                "defeasibly": MappingProxyType(
                    {"flies": frozenset({("tweety",)})}
                ),
                "not_defeasibly": MappingProxyType(
                    {"grounded_out": frozenset({("claim-flight",)})}
                ),
                "undecided": MappingProxyType(
                    {"contested": frozenset({("claim-flight",)})}
                ),
            }
        ),
    )


def test_ws7_extract_facts_materializes_claim_structural_sources() -> None:
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

    atoms = extract_facts(
        GroundingFactInputs(claim_files=(_ws7_claim_file(),)),
        registry,
    )

    assert set(atoms) == {
        GroundAtom("claim_sample_size", ("claim-tweety", 11)),
        GroundAtom("claim_condition", ("claim-tweety", "habitat == 'wetland'")),
        GroundAtom("claim_context", ("claim-tweety", "ctx-field")),
        GroundAtom("claim_context", ("claim-flight", "ctx-field")),
        GroundAtom("claim_page", ("claim-tweety", 25)),
        GroundAtom("claim_page", ("claim-flight", 8)),
        GroundAtom("claim_output_concept", ("claim-tweety", "concept:bird")),
        GroundAtom("claim_about_concept", ("claim-flight", "concept:bird")),
        GroundAtom("claim_about_concept", ("claim-flight", "concept:flight")),
    }


def test_ws7_sidecar_runtime_bundle_preserves_four_statuses() -> None:
    from propstore.sidecar.rules import (
        create_grounded_fact_table,
        populate_grounded_facts,
        read_grounded_bundle,
    )

    conn = sqlite3.connect(":memory:")
    create_grounded_fact_table(conn)
    bundle = _bundle_with_four_statuses()

    populate_grounded_facts(conn, bundle)
    restored = read_grounded_bundle(conn)

    assert restored.sections == bundle.sections


def test_ws7_world_model_reads_grounding_bundle_from_sidecar(
    tmp_path: Path,
) -> None:
    from propstore.sidecar.rules import (
        create_grounded_fact_table,
        populate_grounded_facts,
    )
    from propstore.sidecar.schema import (
        create_claim_tables,
        create_context_tables,
        create_tables,
        write_schema_metadata,
    )
    from propstore.world.model import WorldModel

    sidecar_path = tmp_path / "propstore.sqlite"
    conn = sqlite3.connect(sidecar_path)
    write_schema_metadata(conn)
    create_tables(conn)
    conn.execute(
        """
        CREATE VIRTUAL TABLE concept_fts USING fts5(
            concept_id UNINDEXED,
            canonical_name,
            aliases,
            definition,
            conditions
        )
        """
    )
    create_context_tables(conn)
    create_claim_tables(conn)
    create_grounded_fact_table(conn)
    populate_grounded_facts(conn, _bundle_with_four_statuses())
    conn.commit()
    conn.close()

    with WorldModel(sidecar_path=sidecar_path) as world:
        bundle = world.grounding_bundle()

    assert bundle.sections["defeasibly"]["flies"] == frozenset({("tweety",)})
    assert bundle.sections["not_defeasibly"]["grounded_out"] == frozenset(
        {("claim-flight",)}
    )
    assert bundle.sections["undecided"]["contested"] == frozenset(
        {("claim-flight",)}
    )
