"""Sidecar build orchestration.

Schema-v3 gate refactor (``reviews/2026-04-16-code-review/workstreams/
ws-z-render-gates.md`` axis-1 finding 3.1): the former
``_raise_on_raw_id_claim_inputs`` build-time abort has been replaced with
``_collect_raw_id_diagnostics``, which produces typed quarantine records.
The build proceeds; the offending claim lands as a stub row in
``claim_core`` with ``build_status='blocked'`` and a ``build_diagnostics``
row carries the reason. Render-policy filtering (phase 4) decides
whether to show these rows. This implements the discipline declared in
``reviews/2026-04-16-code-review/workstreams/disciplines.md`` rule 5:
"Filter at render, not at build".
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from propstore.claims import claim_file_claims, claim_file_filename, claim_file_source_paper
from propstore.compiler.context import (
    build_compilation_context_from_loaded,
)
from propstore.compiler.passes import compile_claim_files
from propstore.context_types import LoadedContext, parse_context_record_document
from propstore.core.concepts import LoadedConcept, parse_concept_record_document
from propstore.form_utils import parse_form
from propstore.sidecar.claims import (
    build_claim_fts_index,
    populate_authored_justifications,
    populate_claims,
    populate_conflicts,
    populate_raw_id_quarantine_records,
    populate_stances,
)
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
    from propstore.compiler.ir import ClaimCompilationBundle
    from propstore.repository import Repository

@dataclass(frozen=True)
class RawIdQuarantineRecord:
    """Typed quarantine record for a claim whose raw 'id' never canonicalized.

    Produced by :func:`_collect_raw_id_diagnostics` as a replacement for the
    former all-or-nothing ``_raise_on_raw_id_claim_inputs`` gate (axis-1
    finding 3.1). Each record carries enough metadata to synthesize a stub
    ``claim_core`` row with ``build_status='blocked'`` and an attached
    ``build_diagnostics`` row (``diagnostic_kind='raw_id_input'``,
    ``blocking=1``). The synthetic id construction is recorded in
    ``detail_json`` on the diagnostic row for traceability per the
    honest-ignorance discipline.
    """

    filename: str
    source_paper: str
    raw_id: str
    seq: int
    synthetic_id: str
    message: str

    @property
    def detail_json(self) -> str:
        """JSON provenance describing how ``synthetic_id`` was derived.

        The synthetic id is ``sha256(filename|raw_id|seq)`` truncated to 32
        hex chars and prefixed with ``quarantine:raw_id:``. Keeping the
        basis fields visible avoids hiding that the id is not canonical
        (CLAUDE.md honest-ignorance discipline).
        """

        return json.dumps(
            {
                "synthetic_id_basis": {
                    "scheme": "sha256(filename|raw_id|seq)",
                    "filename": self.filename,
                    "raw_id": self.raw_id,
                    "seq": self.seq,
                    "prefix": "quarantine:raw_id:",
                },
            },
            sort_keys=True,
        )


def _synthesize_quarantine_id(filename: str, raw_id: str, seq: int) -> str:
    """Deterministic synthetic id for a raw-id-broken claim."""

    import hashlib

    digest = hashlib.sha256(f"{filename}|{raw_id}|{seq}".encode()).hexdigest()
    return f"quarantine:raw_id:{digest[:32]}"


def _collect_raw_id_diagnostics(
    claim_bundle: ClaimCompilationBundle,
) -> list[RawIdQuarantineRecord]:
    """Return quarantine records for claims with a raw ``id`` but no canonical identity.

    Walks ``claim_bundle.normalized_claim_files`` rather than relying on
    the diagnostic message alone: the diagnostic records filename + text,
    but the per-claim metadata (raw id, source paper, sequence number) is
    on the claim objects themselves. Matching the two gives us the typed
    record the populator needs to emit a ``build_status='blocked'`` stub
    row plus a ``build_diagnostics`` row.

    Per axis-1 finding 3.1: this function replaces the prior
    ``_raise_on_raw_id_claim_inputs`` abort. It never raises.
    """

    raw_id_filenames = {
        diagnostic.filename
        for diagnostic in claim_bundle.diagnostics
        if diagnostic.is_error and "raw 'id' input" in diagnostic.message
    }
    if not raw_id_filenames:
        return []

    records: list[RawIdQuarantineRecord] = []
    seq = 0
    for claim_file in claim_bundle.normalized_claim_files:
        filename = claim_file_filename(claim_file)
        if filename not in raw_id_filenames:
            # Still advance seq to stay stable across files? No — seq is
            # within-file. Restart per-file so synthetic ids are local.
            continue
        source_paper = claim_file_source_paper(claim_file) or filename
        for file_seq, claim in enumerate(claim_file_claims(claim_file), start=1):
            raw_id = claim.id
            artifact_id = claim.artifact_id
            if (
                isinstance(raw_id, str)
                and raw_id
                and not (isinstance(artifact_id, str) and artifact_id)
            ):
                seq += 1
                synthetic_id = _synthesize_quarantine_id(filename, raw_id, file_seq)
                records.append(
                    RawIdQuarantineRecord(
                        filename=filename,
                        source_paper=str(source_paper),
                        raw_id=raw_id,
                        seq=seq,
                        synthetic_id=synthetic_id,
                        message=(
                            "claim uses raw 'id' input "
                            "without canonical identity fields"
                        ),
                    )
                )
    return records


def build_sidecar(
    repo: "Repository",
    sidecar_path: Path,
    force: bool = False,
    *,
    commit_hash: str | None = None,
    compilation_context: CompilationContext | None = None,
    claim_bundle: ClaimCompilationBundle | None = None,
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

    from propstore.context_types import loaded_contexts_to_lifting_system

    form_registry = {
        document.name: parse_form(document.name, document)
        for form_ref in repo.families.forms.iter(commit=commit_hash)
        for document in (
            repo.families.forms.require(form_ref, commit=commit_hash),
        )
    }
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
    if claim_bundle is None and claim_files:
        claim_bundle = compile_claim_files(
            list(claim_files),
            compilation_context,
            context_ids=context_ids if context_ids else None,
        )
    raw_id_quarantine_records: list[RawIdQuarantineRecord] = (
        _collect_raw_id_diagnostics(claim_bundle) if claim_bundle is not None else []
    )
    normalized_claim_files = (
        list(claim_bundle.normalized_claim_files)
        if claim_bundle is not None
        else (claim_files if claim_files else None)
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
        populate_forms(conn, form_registry)
        populate_concepts(conn, concepts, form_registry)
        populate_aliases(conn, concepts)
        populate_relationships(conn, concepts)
        populate_parameterizations(conn, concepts)
        populate_parameterization_groups(conn, concepts)
        populate_form_algebra(conn, concepts, form_registry)
        build_concept_fts_index(conn, concepts)
        create_claim_tables(conn)
        create_micropublication_tables(conn)

        if context_files:
            populate_contexts(conn, context_files)

        if normalized_claim_files is not None:
            populate_claims(
                conn,
                normalized_claim_files,
                concept_registry,
                form_registry=form_registry,
                semantic_bundle=claim_bundle,
            )

            if raw_id_quarantine_records:
                populate_raw_id_quarantine_records(conn, raw_id_quarantine_records)

            lifting_system = (
                loaded_contexts_to_lifting_system(list(context_files))
                if context_files
                else None
            )
            populate_conflicts(
                conn,
                normalized_claim_files,
                concept_registry,
                dict(compilation_context.cel_registry),
                lifting_system=lifting_system,
            )
            build_claim_fts_index(conn, normalized_claim_files)

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
