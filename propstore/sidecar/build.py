"""Sidecar build orchestration."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from propstore.compiler.context import (
    build_compilation_context_from_loaded,
    concept_registry_for_context,
    normalize_loaded_concepts,
)
from propstore.compiler.passes import compile_claim_files
from propstore.form_utils import FormDefinition, load_all_forms_path
from propstore.knowledge_path import KnowledgePath
from propstore.sidecar.claims import (
    build_claim_fts_index,
    populate_authored_justifications_from_files,
    populate_claims,
    populate_conflicts,
    populate_stances_from_files,
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
    create_context_tables,
    create_tables,
    populate_contexts,
    write_schema_metadata,
)
from propstore.sidecar.sources import populate_sources
from propstore.validate import load_concepts
from propstore.validate_claims import build_authored_concept_registry, load_claim_files

if TYPE_CHECKING:
    from propstore.compiler.context import CompilationContext
    from propstore.compiler.ir import ClaimCompilationBundle

_SEMANTIC_INPUT_VERSION = "semantic-input-v1"


def _content_hash(knowledge_root: KnowledgePath) -> str:
    import hashlib

    h = hashlib.sha256()
    h.update(_SEMANTIC_INPUT_VERSION.encode())
    for subdir in ("concepts", "claims", "contexts", "forms", "justifications", "sources", "stances"):
        subtree = knowledge_root / subdir
        if not subtree.exists():
            continue
        for entry in subtree.iterdir():
            if not entry.is_file() or entry.suffix != ".yaml":
                continue
            h.update(entry.stem.encode())
            h.update(entry.read_bytes())

    schema_dir = Path(__file__).parent.parent.parent / "schema" / "generated"
    if schema_dir.exists():
        for schema_path in sorted(schema_dir.glob("*.json")):
            h.update(str(schema_path.name).encode())
            h.update(schema_path.read_bytes())
    return h.hexdigest()


def _raise_on_raw_id_claim_inputs(claim_bundle: ClaimCompilationBundle) -> None:
    raw_id_errors = [
        diagnostic.message
        for diagnostic in claim_bundle.diagnostics
        if diagnostic.is_error and "raw 'id' input" in diagnostic.message
    ]
    if raw_id_errors:
        raise ValueError("\n".join(raw_id_errors))


def build_sidecar(
    knowledge_root: KnowledgePath,
    sidecar_path: Path,
    force: bool = False,
    *,
    commit_hash: str | None = None,
    compilation_context: CompilationContext | None = None,
    claim_bundle: ClaimCompilationBundle | None = None,
) -> bool:
    """Build the SQLite sidecar from a knowledge tree."""
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)

    if commit_hash is not None:
        content_hash = commit_hash
    else:
        content_hash = _content_hash(knowledge_root)
    hash_path = sidecar_path.with_suffix(".hash")

    if not force and sidecar_path.exists() and hash_path.exists():
        existing_hash = hash_path.read_text().strip()
        if existing_hash == content_hash:
            return False

    form_registry = load_all_forms_path(knowledge_root / "forms")
    concepts = normalize_loaded_concepts(load_concepts(knowledge_root / "concepts"))
    claim_files = (
        load_claim_files(knowledge_root / "claims")
        if (knowledge_root / "claims").exists()
        else None
    )
    from propstore.validate_contexts import ContextHierarchy, load_contexts

    context_files = (
        load_contexts(knowledge_root / "contexts")
        if (knowledge_root / "contexts").exists()
        else None
    )
    context_ids = {
        c.data["id"]
        for c in (context_files or [])
        if isinstance(c.data, dict) and c.data.get("id")
    }

    if compilation_context is None:
        compilation_context = build_compilation_context_from_loaded(
            concepts,
            forms_dir=knowledge_root / "forms",
            claim_files=list(claim_files) if claim_files is not None else None,
            context_ids=context_ids,
        )
    concept_registry = build_authored_concept_registry(
        concepts,
        knowledge_root / "forms",
        require_form_definition=False,
    )
    if claim_bundle is None and claim_files is not None:
        claim_bundle = compile_claim_files(
            list(claim_files),
            compilation_context,
            context_ids=context_ids if context_ids else None,
        )
    if claim_bundle is not None:
        _raise_on_raw_id_claim_inputs(claim_bundle)
    normalized_claim_files = (
        list(claim_bundle.normalized_claim_files)
        if claim_bundle is not None
        else claim_files
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
        except Exception as exc:
            logging.warning("Embedding snapshot failed: %s", exc)
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
        populate_sources(conn, knowledge_root)
        populate_forms(conn, form_registry)
        populate_concepts(conn, concepts, form_registry)
        populate_aliases(conn, concepts)
        populate_relationships(conn, concepts, concept_registry)
        populate_parameterizations(conn, concepts, concept_registry)
        populate_parameterization_groups(conn, concepts)
        populate_form_algebra(conn, concepts, form_registry)
        build_concept_fts_index(conn, concepts)
        create_claim_tables(conn)

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

            context_hierarchy = ContextHierarchy(list(context_files)) if context_files else None
            populate_conflicts(
                conn,
                normalized_claim_files,
                concept_registry,
                context_hierarchy=context_hierarchy,
            )
            build_claim_fts_index(conn, normalized_claim_files)

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
            populate_stances_from_files(conn, knowledge_root / "stances")
            populate_authored_justifications_from_files(conn, knowledge_root / "justifications")

        conn.commit()
    except BaseException:
        conn.close()
        if sidecar_path.exists():
            sidecar_path.unlink()
        raise
    conn.close()

    hash_path.write_text(content_hash)
    return True
