"""Materialize the content-addressed world sidecar from a repository.

This is the build spine (PLAN.md §6, scout-p9-map §B3). It computes the sidecar's
**content hash** — the cache key over everything a sidecar's contents depend on —
and hands a build callback to quire's :class:`~quire.derived_store.DerivedStoreManager`,
which *owns* rebuild-on-change: when a sidecar already exists for a content hash it
returns ``built=False`` without calling the callback. propstore never reimplements
that caching; it only supplies the hash and the builder.

The builder, :func:`_build_sidecar_file`, realises the charter-projection thesis:
every authored family is written straight from its charter
(``session.add_family(name, {charter fields})``) under **advisory foreign keys**
(``enforce_foreign_keys=False``), so a dangling reference inserts as a quarantined
row rather than aborting the build (Z1, gaps.md / PLAN.md §12.1). The only
non-charter compute it writes is the conflict / diagnostic plan
(:mod:`propstore.derived_build_plan`) and the raw ``grounded_fact`` table
(:mod:`propstore.grounding.sidecar`).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from quire.artifacts import UnscannablePlacementError
from quire.derived_runtime import connect_sqlite_store, write_derived_store_schema_metadata
from quire.derived_store import (
    DerivedStoreHandle,
    checkpoint_and_close_sqlite,
    derived_store_content_hash,
    read_dependency_pins,
)
from quire.sqlalchemy_schema import SqlAlchemySchema
from quire.sqlalchemy_store import create_sqlalchemy_store, writable_session

from propstore.build_diagnostics import build_exception_diagnostic
from propstore.derived_build_plan import (
    RepositoryCheckedBundle,
    SidecarBuildPlan,
    compile_sidecar_build_plan,
)
from propstore.derived_schema import (
    WORLD_SIDECAR_SCHEMA_VERSION,
    build_world_sidecar_schema,
)
from propstore.families.claims import Claim
from propstore.families.concepts import Concept
from propstore.families.predicates import Predicate
from propstore.families.registry import PROPSTORE_FAMILY_REGISTRY, registered_charters
from propstore.families.rules import DefeasibleRule, RuleSuperiority
from propstore.grounding.facts import ConceptRelations
from propstore.grounding.loading import GroundingRepo, build_grounded_bundle
from propstore.grounding.sidecar import create_grounded_fact_table, populate_grounded_facts
from propstore.semantic_passes.registry import PipelineRegistry

if TYPE_CHECKING:
    from propstore.repository import Repository

_WORLD_PROJECTION_ID = "propstore.world"
_WORLD_META_KEY = "sidecar"

# The substrate package pins whose versions a built sidecar's contents depend on.
# (Translated from the reference's ``_SIDECAR_CACHE_DEPENDENCIES``.)
_SIDECAR_CACHE_DEPENDENCIES = (
    "argumentation",
    "ast-equiv",
    "bridgman",
    "gunray",
    "quire",
)

# Families projected from their charters directly. The build computes these rather
# than reading authored documents, so they are skipped by the generic projection.
_COMPUTED_FAMILIES = frozenset(
    {"claim", "lifting_materialization", "conflict", "build_diagnostic"}
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _family_contract_versions() -> dict[str, str]:
    versions = {"propstore_registry": str(PROPSTORE_FAMILY_REGISTRY.contract_version)}
    for family in PROPSTORE_FAMILY_REGISTRY.families:
        versions[family.name] = str(family.contract_version)
    return dict(sorted(versions.items()))


def _semantic_pass_versions() -> tuple[dict[str, str], ...]:
    from propstore.families.claims_passes import register_claim_pipeline
    from propstore.families.concepts_passes import register_concept_pipeline
    from propstore.families.contexts_passes import register_context_pipeline
    from propstore.families.forms_passes import register_form_pipeline

    registry = PipelineRegistry()
    register_form_pipeline(registry)
    register_concept_pipeline(registry)
    register_context_pipeline(registry)
    register_claim_pipeline(registry)

    entries: list[dict[str, str]] = []
    for pass_class in registry.registered_passes():
        version = pass_class.version
        if not isinstance(version, str) or not version:
            raise RuntimeError(
                f"semantic pass {pass_class.__name__} declares no non-empty version"
            )
        entries.append(
            {
                "family": pass_class.family.value,
                "name": pass_class.name,
                "input_stage": pass_class.input_stage.value,
                "output_stage": pass_class.output_stage.value,
                "version": version,
            }
        )
    return tuple(
        sorted(
            entries,
            key=lambda entry: (
                entry["family"],
                entry["name"],
                entry["input_stage"],
                entry["output_stage"],
            ),
        )
    )


def _source_branch_tips(repo: Repository) -> tuple[tuple[str, str], ...]:
    tips = [
        (branch.name, branch.tip_sha)
        for branch in repo.snapshot.iter_branches()
        if branch.kind == "source"
    ]
    return tuple(sorted(tips))


def world_sidecar_hash_inputs(
    source_revision: str,
    *,
    source_branch_tips: tuple[tuple[str, str], ...] = (),
    schema_hash: str,
) -> dict[str, object]:
    """The full set of inputs the world-sidecar content hash is computed over.

    Returned as a dict for inspectability (tests assert which inputs invalidate the
    cache). ``schema_hash`` is the charter-derived schema's ``catalog_hash`` — the
    rewrite's replacement for the reference's ``digest_directory(schema/generated)``
    (PLAN.md §6 deletes the generated-schema directory).
    """

    return {
        "source_revision": source_revision,
        "source_branch_tips": [list(tip) for tip in source_branch_tips],
        "sidecar_schema_version": WORLD_SIDECAR_SCHEMA_VERSION,
        "schema_hash": schema_hash,
        "passes": list(_semantic_pass_versions()),
        "family_contract_versions": _family_contract_versions(),
        "build_time_config": {
            "PROPSTORE_SIDECAR_CACHE_BUST": os.environ.get(
                "PROPSTORE_SIDECAR_CACHE_BUST", ""
            ),
        },
        "dependency_pins": read_dependency_pins(
            _repo_root() / "uv.lock", _SIDECAR_CACHE_DEPENDENCIES
        ),
    }


def world_sidecar_hash(
    source_revision: str,
    *,
    source_branch_tips: tuple[tuple[str, str], ...] = (),
    schema_hash: str,
) -> str:
    """The content hash (cache key) for a world sidecar at ``source_revision``."""

    inputs = world_sidecar_hash_inputs(
        source_revision,
        source_branch_tips=source_branch_tips,
        schema_hash=schema_hash,
    )
    return derived_store_content_hash(
        projection_version=str(WORLD_SIDECAR_SCHEMA_VERSION),
        schema_hash=schema_hash,
        dependencies=read_dependency_pins(
            _repo_root() / "uv.lock", _SIDECAR_CACHE_DEPENDENCIES
        ),
        extra_inputs={
            "source_revision": inputs["source_revision"],
            "source_branch_tips": inputs["source_branch_tips"],
            "passes": inputs["passes"],
            "family_contract_versions": inputs["family_contract_versions"],
            "build_time_config": inputs["build_time_config"],
        },
    )


def materialize_world_sidecar(
    repo: Repository,
    *,
    force: bool = False,
    checked: RepositoryCheckedBundle | None = None,
    plan: SidecarBuildPlan | None = None,
    commit: str | None = None,
) -> tuple[DerivedStoreHandle, bool]:
    """Build (or reuse) the content-addressed world sidecar; return (handle, built).

    quire's :meth:`DerivedStoreManager.materialize_with_report` owns rebuild-on-
    change: it returns ``built=False`` without invoking the builder when a sidecar
    for this content hash already exists (and ``force`` is false). ``checked`` /
    ``plan`` let a caller that already ran the compiler (``build_repository``) thread
    its work through; absent, :func:`_build_sidecar_file` recompiles.
    """

    with repo.mutation_guard():
        resolved_commit = str(
            commit if commit is not None else repo.require_git().head_sha()
        )
        schema = build_world_sidecar_schema()
        content_hash = world_sidecar_hash(
            resolved_commit,
            source_branch_tips=_source_branch_tips(repo),
            schema_hash=schema.catalog_hash,
        )

        def _build(target: Path) -> None:
            _build_sidecar_file(
                target,
                repo,
                schema=schema,
                commit=resolved_commit,
                checked=checked,
                plan=plan,
            )

        materialization = repo.derived_stores.materialize_with_report(
            projection_id=_WORLD_PROJECTION_ID,
            source_commit=resolved_commit,
            content_hash=content_hash,
            build=_build,
            force=force,
        )
    return materialization.handle, materialization.built


def _project_documents(
    session: object,
    schema: SqlAlchemySchema,
    family_name: str,
    documents: tuple[object, ...],
) -> None:
    """Project documents of one family from their charter fields into the sidecar.

    The values dict is exactly the charter's columns read off the document — the
    per-family ``compile_*_sidecar_rows`` / ``populate_*`` projection mass of the
    reference tree, gone.
    """

    field_names = [field.name for field in schema.schema_object(family_name).fields]
    add_family = getattr(session, "add_family")
    for document in documents:
        values = {
            name: getattr(document, name)
            for name in field_names
            if hasattr(document, name)
        }
        add_family(family_name, values)


def _project_authored_families(
    session: object, schema: SqlAlchemySchema, repo: Repository, commit: str | None
) -> None:
    """Generic charter projection of every master-resident authored family.

    Families with a non-master placement (source / proposal branches) yield no
    documents at the master commit and contribute nothing; the computed families
    (claims, conflicts, diagnostics, lifting materializations) are projected
    separately and skipped here.
    """

    for charter in registered_charters():
        name = charter.family.name
        if name in _COMPUTED_FAMILIES:
            continue
        # Source families use a fixed-file placement that cannot be scanned by
        # commit — they live on dedicated source branches and are not part of the
        # world master projection (their sidecar mirror is 9-3). Skipping them is a
        # capability classification, not error suppression.
        try:
            documents = tuple(
                handle.document
                for handle in repo.families.by_name(name).iter_handles(commit=commit)
            )
        except UnscannablePlacementError:
            continue
        _project_documents(session, schema, name, documents)


def _load_grounding_repo(repo: Repository, commit: str | None) -> GroundingRepo:
    def _documents(family_name: str) -> tuple[object, ...]:
        return tuple(
            handle.document
            for handle in repo.families.by_name(family_name).iter_handles(commit=commit)
        )

    predicates = tuple(d for d in _documents("predicate") if isinstance(d, Predicate))
    rules = tuple(d for d in _documents("defeasible_rule") if isinstance(d, DefeasibleRule))
    superiority = tuple(
        d for d in _documents("rule_superiority") if isinstance(d, RuleSuperiority)
    )
    claims = tuple(d for d in _documents("claim") if isinstance(d, Claim))
    concepts = tuple(
        ConceptRelations(concept_id=d.concept_id, canonical_name=d.canonical_name)
        for d in _documents("concept")
        if isinstance(d, Concept)
    )
    return GroundingRepo(
        predicates=predicates,
        rules=rules,
        rule_superiority=superiority,
        concepts=concepts,
        claims=claims,
    )


def _blocked_source_diagnostics(repo: Repository) -> tuple[object, ...]:
    """The blocked-promotion mirror rows for every source branch (Phase 9-3).

    A source branch's blocked claims stay on that branch (quarantine, not drop);
    this projects their reasons into the world sidecar as ``promotion_blocked``
    :class:`~propstore.families.diagnostics.BuildDiagnostic` rows so a source-status
    reader can surface them. Imported lazily to keep the build spine free of a
    source-subsystem import at module load.
    """

    from propstore.source.promote import (
        compile_all_source_promotion_blocked_projection_rows,
    )

    return compile_all_source_promotion_blocked_projection_rows(repo).diagnostics


def _record_build_exception(
    path: Path, schema: SqlAlchemySchema, exc: BaseException
) -> None:
    """Best-effort: record a ``build_exception`` diagnostic before re-raising.

    A failed build still leaves a queryable trace. If even the recording fails (the
    table may not exist yet), the reason is attached to the original exception
    rather than swallowed.
    """

    try:
        with writable_session(path, schema, enforce_foreign_keys=False) as session:
            diagnostic = build_exception_diagnostic(exc, diagnostic_id="diag:exception")
            _project_documents(session, schema, "build_diagnostic", (diagnostic,))
            session.commit()
    except Exception as record_error:  # noqa: BLE001 - reported, not swallowed
        exc.add_note(f"failed to record build diagnostic: {record_error}")


def _build_sidecar_file(
    path: Path,
    repo: Repository,
    *,
    schema: SqlAlchemySchema,
    commit: str | None,
    checked: RepositoryCheckedBundle | None = None,
    plan: SidecarBuildPlan | None = None,
) -> None:
    """Build one world-sidecar sqlite file at ``path`` from ``repo``.

    Runs the shared compiler (when ``checked`` was not threaded in), then writes
    every authored family from its charter plus the conflict / diagnostic plan,
    then the raw grounded-fact table. All population happens under advisory foreign
    keys so a dangling reference quarantines rather than aborting (Z1).
    """

    if checked is None:
        from propstore.compiler.workflows import compile_repository_checked_bundle

        checked = compile_repository_checked_bundle(repo, commit=commit)
        plan = (
            compile_sidecar_build_plan(repo, checked, commit=commit)
            if checked is not None
            else None
        )

    try:
        create_sqlalchemy_store(path, schema)
        with writable_session(path, schema, enforce_foreign_keys=False) as session:
            _project_authored_families(session, schema, repo, commit)
            if checked is not None:
                _project_documents(session, schema, "claim", checked.claims)
            if plan is not None:
                _project_documents(session, schema, "conflict", plan.conflicts)
                _project_documents(session, schema, "build_diagnostic", plan.diagnostics)
            _project_documents(
                session, schema, "build_diagnostic", _blocked_source_diagnostics(repo)
            )
            session.commit()

        conn = connect_sqlite_store(path)
        try:
            write_derived_store_schema_metadata(
                conn,
                schema_version=WORLD_SIDECAR_SCHEMA_VERSION,
                key=_WORLD_META_KEY,
            )
            create_grounded_fact_table(conn)
            populate_grounded_facts(
                conn, build_grounded_bundle(_load_grounding_repo(repo, commit))
            )
            conn.commit()
        finally:
            checkpoint_and_close_sqlite(conn)
    except Exception as exc:
        _record_build_exception(path, schema, exc)
        raise
