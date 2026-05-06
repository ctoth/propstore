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

import hashlib
import os
import sqlite3
import tempfile
import threading
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from quire.hashing import canonical_json_bytes
from propstore.claims import ClaimFileEntry
from propstore.compiler.context import (
    build_compilation_context_from_loaded,
)
from propstore.families.registry import PROPSTORE_FAMILY_REGISTRY
from propstore.families.claims.passes import register_claim_pipeline, run_claim_pipeline
from propstore.families.claims.stages import ClaimAuthoredFiles, ClaimCheckedBundle
from propstore.families.contexts.passes import register_context_pipeline
from propstore.families.contexts.stages import (
    LoadedContext,
    parse_context_record_document,
)
from propstore.families.concepts.passes import register_concept_pipeline
from propstore.families.concepts.stages import LoadedConcept, parse_concept_record_document
from propstore.families.forms.passes import register_form_pipeline, run_form_pipeline
from propstore.families.forms.stages import FormCheckedRegistry, LoadedForm
from propstore.grounding.loading import build_grounded_bundle
from propstore.sidecar.claims import (
    populate_authored_justifications,
    populate_claim_fts_rows,
    populate_claims,
    populate_conflicts,
    populate_raw_id_quarantine_records,
    populate_stances,
)
from propstore.sidecar.passes import compile_sidecar_build_plan
from propstore.sidecar.stages import ContextSidecarRows, RepositoryCheckedBundle
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
from propstore.sidecar.rules import create_grounded_fact_table, populate_grounded_facts
from propstore.sidecar.sources import populate_sources
from propstore.compiler.context import build_authored_concept_registry
from propstore.semantic_passes.registry import PipelineRegistry
from propstore.semantic_passes.types import PassDiagnostic
import propstore.sidecar.schema as sidecar_schema
from propstore.sidecar.stages import QuarantineDiagnostic
from propstore.sidecar.sqlite import connect_sidecar

if TYPE_CHECKING:
    from propstore.compiler.context import CompilationContext
    from propstore.repository import Repository

_SIDECAR_PUBLISH_LOCKS_LOCK = threading.Lock()
_SIDECAR_PUBLISH_LOCKS: dict[Path, threading.Lock] = {}
_SIDECAR_CACHE_DEPENDENCIES = (
    "argumentation",
    "ast-equiv",
    "bridgman",
    "gunray",
    "quire",
)


@dataclass(frozen=True)
class EmbeddingSnapshotReport:
    model_count: int
    claim_vector_count: int
    concept_vector_count: int


def _sidecar_cache_key_inputs(source_revision: str) -> dict[str, object]:
    return {
        "source_revision": source_revision,
        "sidecar_schema_version": sidecar_schema.SCHEMA_VERSION,
        "passes": _semantic_pass_versions(),
        "generated_schema_version": _generated_schema_version(),
        "family_contract_versions": _family_contract_versions(),
        "dependency_pins": _dependency_pins(),
        "build_time_config": {
            "PROPSTORE_SIDECAR_CACHE_BUST": os.environ.get(
                "PROPSTORE_SIDECAR_CACHE_BUST",
                "",
            ),
        },
    }


def _sidecar_content_hash(source_revision: str) -> str:
    return hashlib.sha256(
        canonical_json_bytes(_sidecar_cache_key_inputs(source_revision))
    ).hexdigest()


def _family_contract_versions() -> dict[str, str]:
    versions = {
        "propstore_registry": str(PROPSTORE_FAMILY_REGISTRY.contract_version),
    }
    for family in PROPSTORE_FAMILY_REGISTRY.families:
        versions[family.name] = str(family.contract_version)
        artifact_family = getattr(family, "artifact_family", None)
        artifact_name = getattr(artifact_family, "name", None)
        artifact_version = getattr(artifact_family, "contract_version", None)
        if isinstance(artifact_name, str) and artifact_version is not None:
            versions[artifact_name] = str(artifact_version)
    return dict(sorted(versions.items()))


def _semantic_pass_versions() -> tuple[dict[str, str], ...]:
    registry = PipelineRegistry()
    register_claim_pipeline(registry)
    register_concept_pipeline(registry)
    register_context_pipeline(registry)
    register_form_pipeline(registry)
    pass_inputs: list[dict[str, str]] = []
    for pass_class in registry.registered_passes():
        version = getattr(pass_class, "version", None)
        if not isinstance(version, str) or not version:
            raise RuntimeError(
                f"semantic pass {pass_class.name!r} must declare a non-empty version"
            )
        pass_inputs.append(
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
            pass_inputs,
            key=lambda item: (
                item["family"],
                item["name"],
                item["input_stage"],
                item["output_stage"],
            ),
        )
    )


def _generated_schema_version(schema_dir: Path | None = None) -> str:
    if schema_dir is None:
        schema_dir = Path(__file__).resolve().parents[2] / "schema" / "generated"
    digest = hashlib.sha256()
    if not schema_dir.exists():
        return ""
    for path in sorted(item for item in schema_dir.rglob("*") if item.is_file()):
        digest.update(path.relative_to(schema_dir).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _dependency_pins(lock_path: Path | None = None) -> dict[str, str]:
    if lock_path is None:
        lock_path = Path(__file__).resolve().parents[2] / "uv.lock"
    if not lock_path.exists():
        return {}
    lock = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    pins: dict[str, str] = {}
    for package in lock.get("package", ()):
        if not isinstance(package, dict):
            continue
        name = package.get("name")
        if name not in _SIDECAR_CACHE_DEPENDENCIES:
            continue
        version = str(package.get("version") or "")
        source = package.get("source")
        pins[str(name)] = f"{version}|{source!r}"
    return dict(sorted(pins.items()))


def _sqlite_sidecar_artifact_paths(sidecar_path: Path) -> tuple[Path, Path, Path]:
    return (
        sidecar_path,
        sidecar_path.with_name(f"{sidecar_path.name}-wal"),
        sidecar_path.with_name(f"{sidecar_path.name}-shm"),
    )


def _cleanup_sidecar_artifacts(sidecar_path: Path) -> None:
    for path in _sqlite_sidecar_artifact_paths(sidecar_path):
        path.unlink(missing_ok=True)


def _new_temp_sidecar_path(sidecar_path: Path) -> Path:
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{sidecar_path.name}.",
        suffix=".tmp",
        dir=sidecar_path.parent,
    )
    os.close(fd)
    temp_path = Path(temp_name)
    temp_path.unlink()
    return temp_path


def _publish_lock_for_sidecar(sidecar_path: Path) -> threading.Lock:
    key = sidecar_path.resolve()
    with _SIDECAR_PUBLISH_LOCKS_LOCK:
        lock = _SIDECAR_PUBLISH_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _SIDECAR_PUBLISH_LOCKS[key] = lock
        return lock


def _checkpoint_and_close(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.close()


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


def _record_embedding_restore_diagnostic(
    conn: sqlite3.Connection,
    exc: Exception,
) -> None:
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
            "embedding",
            "restore",
            "embedding_restore",
            "warning",
            0,
            f"embedding restore failed: {exc}",
            None,
            None,
        ),
    )


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


def _record_claim_diagnostics(
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
            artifact_id=diagnostic.artifact_id or diagnostic.filename or "unknown",
            kind="claim",
            diagnostic_kind="claim_validation",
            message=diagnostic.render(),
            file=diagnostic.filename,
        )


def _record_concept_diagnostics(
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
            artifact_id=diagnostic.artifact_id or diagnostic.filename or "unknown",
            kind="concept",
            diagnostic_kind="concept_validation",
            message=diagnostic.render(),
            file=diagnostic.filename,
        )


def _record_context_diagnostics(
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
            artifact_id=diagnostic.artifact_id or diagnostic.filename or "unknown",
            kind="context",
            diagnostic_kind="context_validation",
            message=diagnostic.render(),
            file=diagnostic.filename,
        )


def _record_authoring_diagnostics(
    conn: sqlite3.Connection,
    diagnostics: tuple[PassDiagnostic, ...],
) -> None:
    for diagnostic in diagnostics:
        conn.execute(
            """
            INSERT INTO build_diagnostics (
                claim_id, source_kind, source_ref, diagnostic_kind,
                severity, blocking, message, file, detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                diagnostic.artifact_id,
                "authoring",
                diagnostic.artifact_id or diagnostic.filename,
                diagnostic.code,
                diagnostic.level,
                1 if diagnostic.is_error else 0,
                diagnostic.render(),
                diagnostic.filename,
                None,
            ),
        )


def _filter_invalid_context_lifting_rows(
    rows: ContextSidecarRows,
) -> ContextSidecarRows:
    context_ids = {row.values[0] for row in rows.context_rows}
    valid_lifting_rows = tuple(
        row
        for row in rows.lifting_rule_rows
        if row.values[1] in context_ids and row.values[2] in context_ids
    )
    return ContextSidecarRows(
        context_rows=rows.context_rows,
        assumption_rows=rows.assumption_rows,
        lifting_rule_rows=valid_lifting_rows,
    )


def _record_quarantine_diagnostics(
    conn: sqlite3.Connection,
    diagnostics: tuple[QuarantineDiagnostic, ...],
) -> None:
    if not diagnostics:
        return
    writer = QuarantinableWriter(conn)
    for diagnostic in diagnostics:
        writer.quarantine(
            artifact_id=diagnostic.artifact_id,
            kind=diagnostic.kind,
            diagnostic_kind=diagnostic.diagnostic_kind,
            message=diagnostic.message,
            file=diagnostic.file,
        )


def build_sidecar(
    repo: "Repository",
    sidecar_path: Path,
    force: bool = False,
    **kwargs,
) -> bool:
    with repo.mutation_guard():
        return _build_sidecar_locked(repo, sidecar_path, force, **kwargs)


def _build_sidecar_locked(
    repo: "Repository",
    sidecar_path: Path,
    force: bool = False,
    *,
    commit_hash: str | None = None,
    compilation_context: CompilationContext | None = None,
    claim_checked_bundle: ClaimCheckedBundle | None = None,
    claim_files: tuple[ClaimFileEntry, ...] | None = None,
    claim_diagnostics: tuple[PassDiagnostic, ...] = (),
    concept_files: tuple[LoadedConcept, ...] | None = None,
    concept_diagnostics: tuple[PassDiagnostic, ...] = (),
    context_files: tuple[LoadedContext, ...] | None = None,
    context_diagnostics: tuple[PassDiagnostic, ...] = (),
    authoring_diagnostics: tuple[PassDiagnostic, ...] = (),
    on_embedding_snapshot: Callable[[EmbeddingSnapshotReport], None] | None = None,
) -> bool:
    """Build the SQLite sidecar from repository artifact families."""
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    tree = repo.tree(commit=commit_hash)

    if commit_hash is not None:
        source_revision = commit_hash
    else:
        source_revision = repo.snapshot.head_sha()
        if source_revision is None:
            raise ValueError("build_sidecar requires a committed git repository or an explicit commit_hash")
    content_hash = _sidecar_content_hash(source_revision)
    hash_path = sidecar_path.with_suffix(".hash")

    if not force and sidecar_path.exists() and hash_path.exists():
        existing_hash = hash_path.read_text().strip()
        if existing_hash == content_hash:
            return False

    form_result = run_form_pipeline(
        [
            LoadedForm(
                filename=handle.ref.name,
                document=handle.document,
            )
            for handle in repo.families.forms.iter_handles(commit=commit_hash)
        ]
    )
    if not isinstance(form_result.output, FormCheckedRegistry):
        errors = ", ".join(error.render() for error in form_result.errors)
        raise ValueError(f"form validation failed: {errors}")
    form_registry = form_result.output.registry
    form_diagnostics = form_result.diagnostics
    concepts = (
        list(concept_files)
        if concept_files is not None
        else [
            LoadedConcept(
                filename=handle.ref.name,
                source_path=tree / handle.address.require_path(),
                knowledge_root=tree,
                record=parse_concept_record_document(handle.document),
                document=handle.document,
            )
            for handle in repo.families.concepts.iter_handles(commit=commit_hash)
        ]
    )
    claim_entries = (
        list(claim_files)
        if claim_files is not None
        else [
            handle
            for handle in repo.families.claims.iter_handles(commit=commit_hash)
        ]
    )
    if context_files is None:
        context_files = tuple(
            LoadedContext(
                filename=handle.ref.name,
                source_path=tree / handle.address.require_path(),
                knowledge_root=tree,
                record=parse_context_record_document(handle.document),
            )
            for handle in repo.families.contexts.iter_handles(commit=commit_hash)
        )
    context_ids = {
        str(c.record.context_id)
        for c in (context_files or [])
        if c.record.context_id is not None
    }

    if compilation_context is None:
        compilation_context = build_compilation_context_from_loaded(
            concepts,
            form_registry=form_registry,
            claim_files=list(claim_entries) if claim_entries else None,
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
    recorded_claim_diagnostics = list(claim_diagnostics)
    if claim_bundle is None and claim_entries:
        claim_pipeline_result = run_claim_pipeline(
            ClaimAuthoredFiles.from_sequence(
                list(claim_entries),
                compilation_context,
                context_ids=context_ids if context_ids else None,
            )
        )
        if not isinstance(claim_pipeline_result.output, ClaimCheckedBundle):
            recorded_claim_diagnostics.extend(claim_pipeline_result.diagnostics)
        else:
            claim_checked_bundle = claim_pipeline_result.output
            claim_bundle = claim_checked_bundle.bundle
    normalized_claim_files = (
        list(claim_bundle.normalized_claim_files)
        if claim_bundle is not None
        else None
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
                handle.ref.name,
                handle.document,
            )
            for handle in repo.families.sources.iter_handles(commit=commit_hash)
        ),
        stance_entries=(
            (
                handle.ref.source_claim,
                handle.document,
            )
            for handle in repo.families.stances.iter_handles(commit=commit_hash)
        ),
        justification_entries=(
            (
                handle.ref.name,
                handle.document,
            )
            for handle in repo.families.justifications.iter_handles(commit=commit_hash)
        ),
        micropub_files=(
            (
                handle.ref.name,
                handle.document,
            )
            for handle in repo.families.micropubs.iter_handles(commit=commit_hash)
        ),
    )

    embedding_snapshot = None
    if sidecar_path.exists():
        snapshot_conn = None
        try:
            from propstore.heuristic.embed import _load_vec_extension, extract_embeddings

            snapshot_conn = connect_sidecar(sidecar_path)
            snapshot_conn.row_factory = sqlite3.Row
            _load_vec_extension(snapshot_conn)
            embedding_snapshot = extract_embeddings(snapshot_conn)
            if embedding_snapshot is not None:
                claim_count = sum(
                    len(vectors) for vectors in embedding_snapshot.claim_vectors.values()
                )
                concept_count = sum(
                    len(vectors) for vectors in embedding_snapshot.concept_vectors.values()
                )
                if on_embedding_snapshot is not None:
                    on_embedding_snapshot(
                        EmbeddingSnapshotReport(
                            model_count=len(embedding_snapshot.models),
                            claim_vector_count=claim_count,
                            concept_vector_count=concept_count,
                        )
                    )
        except ImportError:
            pass
        finally:
            if snapshot_conn is not None:
                snapshot_conn.close()

    had_existing_sidecar = sidecar_path.exists()
    temp_sidecar_path = _new_temp_sidecar_path(sidecar_path)
    temp_hash_path = temp_sidecar_path.with_name(f"{temp_sidecar_path.name}.hash")

    conn = connect_sidecar(temp_sidecar_path)
    try:
        write_schema_metadata(conn)
        create_tables(conn)
        create_context_tables(conn)
        create_grounded_fact_table(conn)
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
        _record_concept_diagnostics(conn, concept_diagnostics)
        _record_context_diagnostics(conn, context_diagnostics)
        _record_claim_diagnostics(conn, tuple(recorded_claim_diagnostics))
        _record_authoring_diagnostics(conn, authoring_diagnostics)
        _record_quarantine_diagnostics(conn, sidecar_plan.quarantine_diagnostics)
        create_micropublication_tables(conn)

        context_rows = (
            _filter_invalid_context_lifting_rows(sidecar_plan.context_rows)
            if context_diagnostics
            else sidecar_plan.context_rows
        )
        if context_rows.context_rows:
            populate_contexts(conn, context_rows)

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

        grounded_bundle = build_grounded_bundle(
            repo,
            commit=commit_hash,
        )
        populate_grounded_facts(conn, grounded_bundle)

        if embedding_snapshot is not None:
            try:
                from propstore.heuristic.embed import _load_vec_extension, restore_embeddings

                conn.row_factory = sqlite3.Row
                _load_vec_extension(conn)
                restore_embeddings(conn, embedding_snapshot)
                conn.row_factory = None
            except ImportError as exc:
                _record_embedding_restore_diagnostic(conn, exc)
                conn.row_factory = None
            except Exception as exc:
                _record_embedding_restore_diagnostic(conn, exc)
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
            conn.commit()
        except Exception as diagnostic_error:
            exc.add_note(f"failed to record build diagnostic: {diagnostic_error}")
        try:
            _checkpoint_and_close(conn)
        except Exception as close_error:
            exc.add_note(f"failed to close failed sidecar build: {close_error}")
        if had_existing_sidecar:
            _cleanup_sidecar_artifacts(temp_sidecar_path)
        else:
            with _publish_lock_for_sidecar(sidecar_path):
                temp_sidecar_path.replace(sidecar_path)
            _cleanup_sidecar_artifacts(temp_sidecar_path)
        raise

    _checkpoint_and_close(conn)
    temp_hash_path.write_text(content_hash)
    try:
        with _publish_lock_for_sidecar(sidecar_path):
            temp_sidecar_path.replace(sidecar_path)
            temp_hash_path.replace(hash_path)
    except Exception:
        _cleanup_sidecar_artifacts(temp_sidecar_path)
        temp_hash_path.unlink(missing_ok=True)
        raise
    _cleanup_sidecar_artifacts(temp_sidecar_path)
    temp_hash_path.unlink(missing_ok=True)
    return True


def build_grounding_sidecar(
    repo: "Repository",
    sidecar_path: Path,
    *,
    commit_hash: str | None = None,
) -> None:
    """Materialize the grounding substrate into a sidecar-shaped SQLite file."""

    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    _cleanup_sidecar_artifacts(sidecar_path)
    conn = connect_sidecar(sidecar_path)
    try:
        write_schema_metadata(conn)
        create_grounded_fact_table(conn)
        grounded_bundle = build_grounded_bundle(
            repo,
            commit=commit_hash,
        )
        populate_grounded_facts(conn, grounded_bundle)
        conn.commit()
    except Exception:
        conn.close()
        _cleanup_sidecar_artifacts(sidecar_path)
        raise
    _checkpoint_and_close(conn)
