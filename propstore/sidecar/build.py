"""Sidecar build orchestration.

Schema-v3 gate refactor (``reviews/2026-04-16-code-review/workstreams/
ws-z-render-gates.md`` axis-1 finding 3.1): the former
``_raise_on_raw_id_claim_inputs`` build-time abort has been replaced with
the claim family pipeline, which produces typed quarantine records.
The build proceeds; the offending claim lands as a stub row in
``claim_core`` with ``build_status='blocked'`` and a ``build_diagnostics``
row carries the reason. Render-policy filtering (phase 4) decides
whether to show these rows. This implements the discipline declared in
``reviews/2026-04-16-code-review/workstreams/disciplines.md`` rule 5:
"Filter at render, not at build".
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from propstore.compiler.context import (
    build_compilation_context_from_loaded,
)
from propstore.families.claims.passes import run_claim_pipeline
from propstore.families.claims.stages import ClaimAuthoredFiles, ClaimCheckedBundle
from propstore.families.contexts.stages import (
    LoadedContext,
    parse_context_record_document,
)
from propstore.families.concepts.stages import LoadedConcept, parse_concept_record_document
from propstore.families.forms.passes import run_form_pipeline
from propstore.families.forms.stages import FormCheckedRegistry, LoadedForm
from propstore.sidecar.claims import (
    build_claim_fts_index,
    populate_authored_justifications,
    populate_claims,
    populate_conflicts,
    populate_raw_id_quarantine_records,
    populate_stances,
)
from propstore.sidecar.passes import compile_claim_sidecar_rows
from propstore.sidecar.stages import RepositoryCheckedBundle
from propstore.sidecar.concepts import (
    build_concept_fts_index,
    populate_aliases,
    populate_concepts,
    populate_form_algebra,
    populate_forms,
    populate_parameterization_groups,
    populate_parameterizations,
    populate_relationships,
)
from propstore.sidecar.schema import (
    create_claim_tables,
    create_micropublication_tables,
    create_context_tables,
    create_tables,
    populate_contexts,
    write_schema_metadata,
)
from propstore.sidecar.micropublications import populate_micropublications
from propstore.sidecar.sources import populate_sources
from propstore.compiler.context import build_authored_concept_registry

if TYPE_CHECKING:
    from propstore.compiler.context import CompilationContext
    from propstore.repository import Repository

def build_sidecar(
    repo: "Repository",
    sidecar_path: Path,
    force: bool = False,
    *,
    commit_hash: str | None = None,
    compilation_context: CompilationContext | None = None,
    claim_checked_bundle: ClaimCheckedBundle | None = None,
) -> bool:
    """Build the SQLite sidecar from repository artifact families."""
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    tree = repo.tree(commit=commit_hash)

    if commit_hash is not None:
        content_hash = commit_hash
    else:
        content_hash = repo.snapshot.head_sha()
        if content_hash is None:
            raise ValueError("build_sidecar requires a committed git repository or an explicit commit_hash")
    hash_path = sidecar_path.with_suffix(".hash")

    if not force and sidecar_path.exists() and hash_path.exists():
        existing_hash = hash_path.read_text().strip()
        if existing_hash == content_hash:
            return False

    from propstore.families.contexts.stages import loaded_contexts_to_lifting_system

    form_result = run_form_pipeline(
        [
            LoadedForm(
                filename=form_ref.name,
                document=repo.families.forms.require(form_ref, commit=commit_hash),
            )
            for form_ref in repo.families.forms.iter(commit=commit_hash)
        ]
    )
    if not form_result.ok or not isinstance(form_result.output, FormCheckedRegistry):
        errors = ", ".join(error.render() for error in form_result.errors)
        raise ValueError(f"form validation failed: {errors}")
    form_registry = form_result.output.registry
    concepts = [
        LoadedConcept(
            filename=ref.name,
            source_path=tree / handle.address.require_path(),
            knowledge_root=tree,
            record=parse_concept_record_document(handle.document),
            document=handle.document,
        )
        for ref in repo.families.concepts.iter(commit=commit_hash)
        for handle in (
            repo.families.concepts.require_handle(ref, commit=commit_hash),
        )
    ]
    claim_files = [
        repo.families.claims.require_handle(ref, commit=commit_hash)
        for ref in repo.families.claims.iter(commit=commit_hash)
    ]
    context_files = [
        LoadedContext(
            filename=ref.name,
            source_path=tree / handle.address.require_path(),
            knowledge_root=tree,
            record=parse_context_record_document(handle.document),
        )
        for ref in repo.families.contexts.iter(commit=commit_hash)
        for handle in (
            repo.families.contexts.require_handle(ref, commit=commit_hash),
        )
    ]
    context_ids = {
        str(c.record.context_id)
        for c in (context_files or [])
        if c.record.context_id is not None
    }

    if compilation_context is None:
        compilation_context = build_compilation_context_from_loaded(
            concepts,
            form_registry=form_registry,
            claim_files=list(claim_files) if claim_files else None,
            context_ids=context_ids,
        )
    concept_registry = build_authored_concept_registry(
        concepts,
        form_registry=form_registry,
        require_form_definition=False,
    )
    claim_bundle = (
        None
        if claim_checked_bundle is None
        else claim_checked_bundle.bundle
    )
    raw_id_quarantine_records = (
        ()
        if claim_checked_bundle is None
        else claim_checked_bundle.raw_id_quarantine_records
    )
    if claim_bundle is None and claim_files:
        claim_pipeline_result = run_claim_pipeline(
            ClaimAuthoredFiles.from_sequence(
                list(claim_files),
                compilation_context,
                context_ids=context_ids if context_ids else None,
            )
        )
        if not isinstance(claim_pipeline_result.output, ClaimCheckedBundle):
            errors = ", ".join(error.render() for error in claim_pipeline_result.errors)
            raise ValueError(f"claim validation failed: {errors}")
        claim_checked_bundle = claim_pipeline_result.output
        claim_bundle = claim_checked_bundle.bundle
        raw_id_quarantine_records = claim_checked_bundle.raw_id_quarantine_records
    normalized_claim_files = (
        list(claim_bundle.normalized_claim_files)
        if claim_bundle is not None
        else (claim_files if claim_files else None)
    )
    repository_checked_bundle = RepositoryCheckedBundle(
        concepts=concepts,
        form_registry=form_registry,
        context_files=tuple(context_files),
        context_ids=frozenset(context_ids),
        compilation_context=compilation_context,
        concept_registry=concept_registry,
        claim_checked_bundle=claim_checked_bundle,
        normalized_claim_files=(
            None
            if normalized_claim_files is None
            else tuple(normalized_claim_files)
        ),
    )

    embedding_snapshot = None
    if sidecar_path.exists():
        snapshot_conn = None
        try:
            from propstore.embed import _load_vec_extension, extract_embeddings

            snapshot_conn = sqlite3.connect(sidecar_path)
            snapshot_conn.row_factory = sqlite3.Row
            _load_vec_extension(snapshot_conn)
            embedding_snapshot = extract_embeddings(snapshot_conn)
            if embedding_snapshot is not None:
                import sys

                claim_count = sum(
                    len(vectors) for vectors in embedding_snapshot.claim_vectors.values()
                )
                concept_count = sum(
                    len(vectors) for vectors in embedding_snapshot.concept_vectors.values()
                )
                print(
                    "  Embedding snapshot: "
                    f"{len(embedding_snapshot.models)} model(s), "
                    f"{claim_count} claim vecs, {concept_count} concept vecs",
                    file=sys.stderr,
                )
        except ImportError:
            pass
        finally:
            if snapshot_conn is not None:
                snapshot_conn.close()

    if sidecar_path.exists():
        sidecar_path.unlink()

    conn = sqlite3.connect(sidecar_path)
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")

        write_schema_metadata(conn)
        create_tables(conn)
        create_context_tables(conn)
        populate_sources(
            conn,
            (
                (
                    ref.name,
                    repo.families.sources.require(ref, commit=commit_hash),
                )
                for ref in repo.families.sources.iter(commit=commit_hash)
            ),
        )
        populate_forms(conn, repository_checked_bundle.form_registry)
        populate_concepts(
            conn,
            repository_checked_bundle.concepts,
            repository_checked_bundle.form_registry,
        )
        populate_aliases(conn, repository_checked_bundle.concepts)
        populate_relationships(conn, repository_checked_bundle.concepts)
        populate_parameterizations(conn, repository_checked_bundle.concepts)
        populate_parameterization_groups(conn, repository_checked_bundle.concepts)
        populate_form_algebra(
            conn,
            repository_checked_bundle.concepts,
            repository_checked_bundle.form_registry,
        )
        build_concept_fts_index(conn, repository_checked_bundle.concepts)
        create_claim_tables(conn)
        create_micropublication_tables(conn)

        if repository_checked_bundle.context_files:
            populate_contexts(conn, repository_checked_bundle.context_files)

        if repository_checked_bundle.normalized_claim_files is not None:
            checked_claims = repository_checked_bundle.claim_checked_bundle
            if checked_claims is None:
                raise ValueError("checked claim bundle is required to populate claims")
            populate_claims(
                conn,
                compile_claim_sidecar_rows(
                    checked_claims.bundle,
                    repository_checked_bundle.concept_registry,
                    form_registry=repository_checked_bundle.form_registry,
                ),
            )

            if raw_id_quarantine_records:
                populate_raw_id_quarantine_records(conn, raw_id_quarantine_records)

            lifting_system = (
                loaded_contexts_to_lifting_system(
                    list(repository_checked_bundle.context_files)
                )
                if repository_checked_bundle.context_files
                else None
            )
            populate_conflicts(
                conn,
                list(repository_checked_bundle.normalized_claim_files),
                repository_checked_bundle.concept_registry,
                dict(repository_checked_bundle.compilation_context.cel_registry),
                lifting_system=lifting_system,
            )
            build_claim_fts_index(
                conn,
                repository_checked_bundle.normalized_claim_files,
            )

        populate_micropublications(
            conn,
            (
                (
                    ref.name,
                    repo.families.micropubs.require(ref, commit=commit_hash),
                )
                for ref in repo.families.micropubs.iter(commit=commit_hash)
            ),
        )

        if embedding_snapshot is not None:
            try:
                from propstore.embed import _load_vec_extension, restore_embeddings

                conn.row_factory = sqlite3.Row
                _load_vec_extension(conn)
                restore_embeddings(conn, embedding_snapshot)
                conn.row_factory = None
            except (ImportError, Exception) as exc:
                import sys

                print(f"Warning: embedding restore failed: {exc}", file=sys.stderr)
                conn.row_factory = None

        if normalized_claim_files is not None:
            populate_stances(
                conn,
                (
                    (
                        ref.source_claim,
                        repo.families.stances.require(ref, commit=commit_hash),
                    )
                    for ref in repo.families.stances.iter(commit=commit_hash)
                ),
            )
            populate_authored_justifications(
                conn,
                (
                    (
                        ref.name,
                        repo.families.justifications.require(ref, commit=commit_hash),
                    )
                    for ref in repo.families.justifications.iter(commit=commit_hash)
                ),
            )

        conn.commit()
    except BaseException:
        conn.close()
        if sidecar_path.exists():
            sidecar_path.unlink()
        raise
    conn.close()

    hash_path.write_text(content_hash)
    return True
