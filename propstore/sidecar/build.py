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
    populate_authored_justifications,
    populate_claim_fts_rows,
    populate_claims,
    populate_conflicts,
    populate_raw_id_quarantine_records,
    populate_stances,
)
from propstore.sidecar.passes import compile_sidecar_build_plan
from propstore.sidecar.stages import RepositoryCheckedBundle
from propstore.sidecar.concepts import populate_concept_sidecar_rows
from propstore.sidecar.schema import (
    create_build_diagnostics_table,
    create_claim_tables,
    create_micropublication_tables,
    create_context_tables,
    create_tables,
    populate_contexts,
    write_schema_metadata,
)
from propstore.sidecar.micropublications import populate_micropublications
from propstore.sidecar.quarantine import QuarantinableWriter
from propstore.sidecar.sources import populate_sources
from propstore.compiler.context import build_authored_concept_registry
from propstore.semantic_passes.types import PassDiagnostic

if TYPE_CHECKING:
    from propstore.compiler.context import CompilationContext
    from propstore.repository import Repository


def _record_build_exception(conn: sqlite3.Connection, exc: Exception) -> None:
    """Persist a build-exception diagnostic instead of deleting the sidecar.

    Rule 5 from the render-gates workstream keeps build failures inspectable at
    render time; the partial sidecar is evidence, not trash to unlink.
    """
    create_build_diagnostics_table(conn)
    conn.execute(
        """
        INSERT INTO build_diagnostics (
            claim_id, source_kind, source_ref, diagnostic_kind,
            severity, blocking, message, file, detail_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            None,
            "sidecar_build",
            None,
            "build_exception",
            "error",
            1,
            str(exc),
            None,
            None,
        ),
    )
    conn.commit()


def _record_form_diagnostics(
    conn: sqlite3.Connection,
    diagnostics: tuple[PassDiagnostic, ...],
) -> None:
    if not diagnostics:
        return
    writer = QuarantinableWriter(conn)
    for diagnostic in diagnostics:
        if not diagnostic.is_error:
            continue
        writer.quarantine(
            artifact_id=diagnostic.filename or diagnostic.artifact_id or "unknown",
            kind="form",
            diagnostic_kind="form_validation",
            message=diagnostic.render(),
            file=diagnostic.filename,
        )


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

    form_result = run_form_pipeline(
        [
            LoadedForm(
                filename=form_ref.name,
                document=repo.families.forms.require(form_ref, commit=commit_hash),
            )
            for form_ref in repo.families.forms.iter(commit=commit_hash)
        ]
    )
    if not isinstance(form_result.output, FormCheckedRegistry):
        errors = ", ".join(error.render() for error in form_result.errors)
        raise ValueError(f"form validation failed: {errors}")
    form_registry = form_result.output.registry
    form_diagnostics = form_result.diagnostics
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
    sidecar_plan = compile_sidecar_build_plan(
        repository_checked_bundle,
        source_entries=(
            (
                ref.name,
                repo.families.sources.require(ref, commit=commit_hash),
            )
            for ref in repo.families.sources.iter(commit=commit_hash)
        ),
        stance_entries=(
            (
                ref.source_claim,
                repo.families.stances.require(ref, commit=commit_hash),
            )
            for ref in repo.families.stances.iter(commit=commit_hash)
        ),
        justification_entries=(
            (
                ref.name,
                repo.families.justifications.require(ref, commit=commit_hash),
            )
            for ref in repo.families.justifications.iter(commit=commit_hash)
        ),
        micropub_files=(
            (
                ref.name,
                repo.families.micropubs.require(ref, commit=commit_hash),
            )
            for ref in repo.families.micropubs.iter(commit=commit_hash)
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
            sidecar_plan.source_rows,
        )
        populate_concept_sidecar_rows(
            conn,
            sidecar_plan.concept_rows,
        )
        create_claim_tables(conn)
        _record_form_diagnostics(conn, form_diagnostics)
        create_micropublication_tables(conn)

        if sidecar_plan.context_rows.context_rows:
            populate_contexts(conn, sidecar_plan.context_rows)

        if sidecar_plan.claim_rows is not None:
            populate_claims(conn, sidecar_plan.claim_rows)

            if sidecar_plan.raw_id_quarantine_rows.claim_rows:
                populate_raw_id_quarantine_records(
                    conn,
                    sidecar_plan.raw_id_quarantine_rows,
                )

            populate_conflicts(conn, sidecar_plan.conflict_rows)
            populate_claim_fts_rows(conn, sidecar_plan.claim_fts_rows)

        populate_micropublications(conn, sidecar_plan.micropublication_rows)

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

        if sidecar_plan.claim_rows is not None:
            populate_stances(conn, sidecar_plan.stance_rows)
            populate_authored_justifications(
                conn,
                sidecar_plan.justification_rows,
            )

        conn.commit()
    except Exception as exc:
        try:
            _record_build_exception(conn, exc)
        except Exception as diagnostic_error:
            exc.add_note(f"failed to record build diagnostic: {diagnostic_error}")
        conn.close()
        raise
    conn.close()

    hash_path.write_text(content_hash)
    return True
