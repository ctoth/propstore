"""SQLite sidecar builder for the propstore concept registry.

Reads validated concept files and builds a SQLite database with:
- concept table
- alias table
- relationship table
- parameterization table
- FTS5 index over names, aliases, definitions, conditions
- normalized claim/relation/conflict tables (when claim files provided)
- claim FTS5 index (when claim files provided)
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

import yaml

from propstore.parameterization_groups import build_groups
from propstore.form_utils import (
    FormDefinition,
    kind_value_from_form_name,
    load_all_forms_path,
    normalize_to_si,
    verify_form_algebra_dimensions,
)
from propstore.knowledge_path import KnowledgePath
from propstore.stances import VALID_STANCE_TYPES
from propstore.loaded import LoadedEntry
from propstore.validate import load_concepts
from propstore.validate_claims import load_claim_files
from propstore.identity import format_logical_id, primary_logical_id
from ast_equiv import canonical_dump

if TYPE_CHECKING:
    from propstore.validate_contexts import ContextHierarchy

_SEMANTIC_INPUT_VERSION = "semantic-input-v1"

_ConvertibleToFloat = float | int | str


@dataclass(frozen=True)
class _TypedClaimFields:
    concept_id: str | None = None
    statement: str | None = None
    expression: str | None = None
    name: str | None = None
    target_concept: str | None = None
    measure: str | None = None
    listener_population: str | None = None
    methodology: str | None = None
    value: float | None = None
    lower_bound: _ConvertibleToFloat | None = None
    upper_bound: _ConvertibleToFloat | None = None
    uncertainty: _ConvertibleToFloat | None = None
    uncertainty_type: str | None = None
    sample_size: int | None = None
    unit: str | None = None

    def __getitem__(self, key: str) -> object | None:
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)


def _optional_string(value: object) -> str | None:
    if isinstance(value, str):
        return value
    return None


def _optional_float_input(value: object) -> _ConvertibleToFloat | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float | str):
        return value
    return None


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None




def _content_hash(knowledge_root: KnowledgePath) -> str:
    """Hash all semantic inputs that define the compiled sidecar.

    Reads all knowledge subdirs through the knowledge tree path.
    Schema files (package code) are hashed separately from the filesystem.
    """
    h = hashlib.sha256()
    h.update(_SEMANTIC_INPUT_VERSION.encode())
    for subdir in ("concepts", "claims", "contexts", "forms", "justifications", "stances"):
        subtree = knowledge_root / subdir
        if not subtree.exists():
            continue
        for entry in subtree.iterdir():
            if not entry.is_file() or entry.suffix != ".yaml":
                continue
            h.update(entry.stem.encode())
            h.update(entry.read_bytes())

    schema_dir = Path(__file__).parent.parent / "schema" / "generated"
    if schema_dir.exists():
        for schema_path in sorted(schema_dir.glob("*.json")):
            h.update(str(schema_path.name).encode())
            h.update(schema_path.read_bytes())
    return h.hexdigest()


def _concept_content_hash(data: dict) -> str:
    """Compute a deterministic content hash for a concept.

    Identity fields: canonical_name, domain, definition.
    """
    version_id = data.get("version_id")
    if isinstance(version_id, str) and version_id:
        return version_id.removeprefix("sha256:")[:16]
    h = hashlib.sha256()
    h.update((data.get("canonical_name", "")).encode())
    h.update((data.get("domain", "")).encode())
    h.update((data.get("definition", "")).encode())
    return h.hexdigest()[:16]


def _concept_artifact_id(concept: dict) -> str | None:
    artifact_id = concept.get("artifact_id")
    if isinstance(artifact_id, str) and artifact_id:
        return artifact_id
    return None


def _concept_primary_logical_id(concept: dict) -> str | None:
    return primary_logical_id(concept)


def _concept_version_id(concept: dict) -> str | None:
    version_id = concept.get("version_id")
    if isinstance(version_id, str) and version_id:
        return version_id
    return None


def _claim_version_id(claim: dict) -> str | None:
    """Return the claim version ID from canonical claim storage data."""
    version_id = claim.get("version_id")
    if isinstance(version_id, str) and version_id:
        return version_id
    return None


def _populate_stances_from_files(
    conn: sqlite3.Connection,
    stances_root: KnowledgePath,
) -> int:
    """Read stance YAML files and insert into normalized relation storage."""
    if not stances_root.exists():
        return 0
    stance_entries = [
        (entry.stem, yaml.safe_load(entry.read_bytes()) or {})
        for entry in stances_root.iterdir()
        if entry.is_file() and entry.suffix == ".yaml"
    ]

    if not stance_entries:
        return 0

    count = 0

    # Build set of valid claim IDs for validation
    valid_claims = {r[0] for r in conn.execute("SELECT id FROM claim_core").fetchall()}

    for fname, data in stance_entries:

        source_claim = data.get("source_claim", "")
        if source_claim not in valid_claims:
            raise sqlite3.IntegrityError(
                f"stance file {fname} references nonexistent source claim '{source_claim}'"
            )

        stances = data.get("stances", [])
        if not isinstance(stances, list):
            raise ValueError(f"stance file {fname} has non-list 'stances'")

        for index, s in enumerate(stances, start=1):
            if not isinstance(s, dict):
                raise ValueError(f"stance file {fname} stance #{index} must be a mapping")
            target = s.get("target", "")
            stype = s.get("type", "")
            if target not in valid_claims:
                raise sqlite3.IntegrityError(
                    f"stance file {fname} references nonexistent target claim '{target}'"
                )
            if stype not in VALID_STANCE_TYPES:
                raise ValueError(
                    f"stance file {fname} uses unrecognized stance type '{stype}'"
                )

            # Extract resolution provenance if present
            res = _coerce_stance_resolution(
                s.get("resolution"),
                f"stance file {fname} stance #{index}",
            )
            cond_differ = _normalize_conditions_differ(s.get("conditions_differ"))

            _insert_claim_stance_row(
                conn,
                (
                    source_claim,
                    target,
                    stype,
                    s.get("target_justification_id"),
                    s.get("strength"),
                    cond_differ,
                    s.get("note"),
                    res.get("method"),
                    res.get("model"),
                    res.get("embedding_model"),
                    res.get("embedding_distance"),
                    res.get("pass_number"),
                    res.get("confidence"),
                    res.get("opinion_belief"),
                    res.get("opinion_disbelief"),
                    res.get("opinion_uncertainty"),
                    res.get("opinion_base_rate"),
                ),
            )
            count += 1

    return count


def _populate_authored_justifications_from_files(
    conn: sqlite3.Connection,
    justifications_root: KnowledgePath,
) -> int:
    """Read authored justification YAML files and insert them into the sidecar."""
    if not justifications_root.exists():
        return 0

    justification_entries = [
        (entry.stem, yaml.safe_load(entry.read_bytes()) or {})
        for entry in justifications_root.iterdir()
        if entry.is_file() and entry.suffix == ".yaml"
    ]
    if not justification_entries:
        return 0

    valid_claims = {row[0] for row in conn.execute("SELECT id FROM claim_core").fetchall()}
    count = 0
    for fname, data in justification_entries:
        justifications = data.get("justifications", [])
        if not isinstance(justifications, list):
            raise ValueError(f"justification file {fname} has non-list 'justifications'")

        for index, justification in enumerate(justifications, start=1):
            if not isinstance(justification, dict):
                raise ValueError(f"justification file {fname} entry #{index} must be a mapping")
            justification_id = justification.get("id")
            conclusion = justification.get("conclusion")
            premises = justification.get("premises") or []
            if not isinstance(justification_id, str) or not justification_id:
                raise ValueError(f"justification file {fname} entry #{index} missing id")
            if not isinstance(conclusion, str) or conclusion not in valid_claims:
                raise sqlite3.IntegrityError(
                    f"justification file {fname} entry #{index} references nonexistent conclusion '{conclusion}'"
                )
            if not isinstance(premises, list):
                raise ValueError(f"justification file {fname} entry #{index} premises must be a list")
            if any(not isinstance(premise, str) or premise not in valid_claims for premise in premises):
                raise sqlite3.IntegrityError(
                    f"justification file {fname} entry #{index} references nonexistent premise"
                )

            provenance = justification.get("provenance")
            attack_target = justification.get("attack_target")
            provenance_payload: dict[str, object] = {}
            if isinstance(provenance, dict):
                provenance_payload.update(provenance)
            if isinstance(attack_target, dict):
                provenance_payload["attack_target"] = attack_target

            conn.execute(
                "INSERT OR IGNORE INTO justification "
                "(id, justification_kind, conclusion_claim_id, premise_claim_ids, "
                "source_relation_type, source_claim_id, provenance_json, rule_strength) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    justification_id,
                    str(justification.get("rule_kind") or "reported_claim"),
                    conclusion,
                    json.dumps(premises),
                    None,
                    None,
                    json.dumps(provenance_payload) if provenance_payload else None,
                    str(justification.get("rule_strength") or "defeasible"),
                ),
            )
            count += 1
    return count



def build_sidecar(
    knowledge_root: KnowledgePath,
    sidecar_path: Path,
    force: bool = False,
    *,
    commit_hash: str | None = None,
) -> bool:
    """Build the SQLite sidecar from a knowledge tree.

    All semantic inputs are read through *knowledge_root*. When *commit_hash* is provided
    (git-backed repo), it is used as the rebuild key instead of computing
    a content hash from the knowledge tree.

    Returns True if the sidecar was rebuilt, False if skipped.
    """
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if rebuild is needed
    if commit_hash is not None:
        content_hash = commit_hash
    else:
        content_hash = _content_hash(knowledge_root)
    hash_path = sidecar_path.with_suffix(".hash")

    if not force and sidecar_path.exists() and hash_path.exists():
        existing_hash = hash_path.read_text().strip()
        if existing_hash == content_hash:
            return False

    # Load all data through the knowledge tree
    form_registry = load_all_forms_path(knowledge_root / "forms")
    concepts = load_concepts(knowledge_root / "concepts")
    claim_files = (
        load_claim_files(knowledge_root / "claims")
        if (knowledge_root / "claims").exists()
        else None
    )
    from propstore.validate_contexts import load_contexts, ContextHierarchy
    context_files = (
        load_contexts(knowledge_root / "contexts")
        if (knowledge_root / "contexts").exists()
        else None
    )

    # Build concept registry for claim processing
    concept_registry: dict[str, dict] = {}
    for c in concepts:
        cid = _concept_artifact_id(c.data)
        if cid:
            enriched = dict(c.data)
            form_name = enriched.get("form")
            if isinstance(form_name, str):
                fd = form_registry.get(form_name)
                if fd is not None:
                    enriched["_form_definition"] = fd
                    if fd.allowed_units:
                        enriched["_allowed_units"] = sorted(fd.allowed_units)
            concept_registry[cid] = enriched
            # Also register by canonical_name and aliases
            cname = enriched.get("canonical_name")
            if cname:
                concept_registry[cname] = enriched
            for logical_id in enriched.get("logical_ids", []) or []:
                if not isinstance(logical_id, dict):
                    continue
                formatted = format_logical_id(logical_id)
                if formatted:
                    concept_registry[formatted] = enriched
            for alias in enriched.get("aliases", []) or []:
                aname = alias.get("name")
                if aname:
                    concept_registry[aname] = enriched

    # Snapshot embeddings before rebuild
    _embedding_snapshot = None
    if sidecar_path.exists():
        _snap_conn = None
        try:
            from propstore.embed import extract_embeddings, _load_vec_extension
            _snap_conn = sqlite3.connect(sidecar_path)
            _snap_conn.row_factory = sqlite3.Row
            _load_vec_extension(_snap_conn)
            _embedding_snapshot = extract_embeddings(_snap_conn)
            if _embedding_snapshot is not None:
                import sys
                _cv = sum(len(v) for v in _embedding_snapshot.claim_vectors.values())
                _ccv = sum(len(v) for v in _embedding_snapshot.concept_vectors.values())
                print(f"  Embedding snapshot: {len(_embedding_snapshot.models)} model(s), {_cv} claim vecs, {_ccv} concept vecs", file=sys.stderr)
        except ImportError:
            pass  # sqlite-vec not installed
        except Exception as exc:
            logging.warning("Embedding snapshot failed: %s", exc)
        finally:
            if _snap_conn is not None:
                _snap_conn.close()

    # Build fresh
    if sidecar_path.exists():
        sidecar_path.unlink()

    conn = sqlite3.connect(sidecar_path)
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")

        _create_tables(conn)
        _create_context_tables(conn)
        _populate_forms(conn, form_registry)
        _populate_concepts(conn, concepts, form_registry)
        _populate_aliases(conn, concepts)
        _populate_relationships(conn, concepts, concept_registry)
        _populate_parameterizations(conn, concepts, concept_registry)
        _populate_parameterization_groups(conn, concepts)
        _populate_form_algebra(conn, concepts, form_registry)
        _build_fts_index(conn, concepts)

        if context_files:
            _populate_contexts(conn, context_files)

        if claim_files is not None:
            _create_claim_tables(conn)
            _populate_claims(conn, claim_files, concept_registry, form_registry=form_registry)

            context_hierarchy = ContextHierarchy(list(context_files)) if context_files else None
            _populate_conflicts(
                conn,
                claim_files,
                concept_registry,
                context_hierarchy=context_hierarchy,
            )
            _build_claim_fts_index(conn, claim_files)

        # Restore embeddings after rebuild
        if _embedding_snapshot is not None:
            try:
                from propstore.embed import restore_embeddings, _load_vec_extension
                conn.row_factory = sqlite3.Row
                _load_vec_extension(conn)
                restore_embeddings(conn, _embedding_snapshot)
                conn.row_factory = None
            except (ImportError, Exception) as exc:
                import sys
                print(f"Warning: embedding restore failed: {exc}", file=sys.stderr)
                conn.row_factory = None

        # Populate stances from stance files
        if claim_files is not None:
            _populate_stances_from_files(conn, knowledge_root / "stances")
            _populate_authored_justifications_from_files(conn, knowledge_root / "justifications")
            _populate_justifications(conn)

        conn.commit()
    except BaseException:
        conn.close()
        if sidecar_path.exists():
            sidecar_path.unlink()
        raise
    conn.close()

    # Write content hash
    hash_path.write_text(content_hash)

    return True


def _create_tables(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE concept (
            id TEXT PRIMARY KEY,
            primary_logical_id TEXT NOT NULL,
            logical_ids_json TEXT NOT NULL,
            version_id TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            seq INTEGER NOT NULL,
            canonical_name TEXT NOT NULL,
            status TEXT NOT NULL,
            domain TEXT,
            definition TEXT NOT NULL,
            kind_type TEXT NOT NULL,
            form TEXT NOT NULL,
            form_parameters TEXT,
            range_min REAL,
            range_max REAL,
            is_dimensionless INTEGER NOT NULL DEFAULT 0,
            unit_symbol TEXT,
            created_date TEXT,
            last_modified TEXT
        );

        CREATE TABLE alias (
            concept_id TEXT NOT NULL,
            alias_name TEXT NOT NULL,
            source TEXT NOT NULL,
            FOREIGN KEY (concept_id) REFERENCES concept(id)
        );

        CREATE TABLE relationship (
            source_id TEXT NOT NULL,
            type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            conditions_cel TEXT,
            note TEXT,
            FOREIGN KEY (source_id) REFERENCES concept(id),
            FOREIGN KEY (target_id) REFERENCES concept(id)
        );

        CREATE TABLE parameterization (
            output_concept_id TEXT NOT NULL,
            concept_ids TEXT NOT NULL,
            formula TEXT NOT NULL,
            sympy TEXT,
            exactness TEXT NOT NULL,
            conditions_cel TEXT,
            FOREIGN KEY (output_concept_id) REFERENCES concept(id)
        );

        CREATE TABLE parameterization_group (
            concept_id TEXT NOT NULL,
            group_id INTEGER NOT NULL,
            FOREIGN KEY (concept_id) REFERENCES concept(id)
        );

        CREATE TABLE relation_edge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_kind TEXT NOT NULL,
            source_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            target_kind TEXT NOT NULL,
            target_id TEXT NOT NULL,
            target_justification_id TEXT,
            conditions_cel TEXT,
            strength TEXT,
            conditions_differ TEXT,
            note TEXT,
            resolution_method TEXT,
            resolution_model TEXT,
            embedding_model TEXT,
            embedding_distance REAL,
            pass_number INTEGER,
            confidence REAL,
            opinion_belief REAL,
            opinion_disbelief REAL,
            opinion_uncertainty REAL,
            opinion_base_rate REAL DEFAULT 0.5,
            CHECK(opinion_belief IS NULL OR (opinion_belief >= 0 AND opinion_belief <= 1)),
            CHECK(opinion_disbelief IS NULL OR (opinion_disbelief >= 0 AND opinion_disbelief <= 1)),
            CHECK(opinion_uncertainty IS NULL OR (opinion_uncertainty >= 0 AND opinion_uncertainty <= 1)),
            CHECK(opinion_base_rate IS NULL OR (opinion_base_rate > 0 AND opinion_base_rate < 1)),
            CHECK(opinion_belief IS NULL OR ABS(opinion_belief + opinion_disbelief + opinion_uncertainty - 1.0) <= 1e-6)
        );

        CREATE TABLE form (
            name TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            unit_symbol TEXT,
            is_dimensionless INTEGER NOT NULL DEFAULT 0,
            dimensions TEXT
        );

        CREATE TABLE form_algebra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            output_form TEXT NOT NULL,
            input_forms TEXT NOT NULL,
            operation TEXT NOT NULL,
            source_concept_id TEXT,
            source_formula TEXT,
            dim_verified INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (output_form) REFERENCES form(name)
        );

        CREATE INDEX idx_alias_name ON alias(alias_name);
        CREATE INDEX idx_alias_concept ON alias(concept_id);
        CREATE INDEX idx_concept_primary_logical_id ON concept(primary_logical_id);
        CREATE INDEX idx_rel_source ON relationship(source_id);
        CREATE INDEX idx_rel_target ON relationship(target_id);
        CREATE INDEX idx_relation_edge_source ON relation_edge(source_kind, source_id);
        CREATE INDEX idx_relation_edge_target ON relation_edge(target_kind, target_id);
        CREATE INDEX idx_relation_edge_type ON relation_edge(relation_type);
        CREATE INDEX idx_param_group ON parameterization_group(group_id);
        CREATE INDEX idx_form_algebra_output ON form_algebra(output_form);
    """)


def _populate_form_algebra(
    conn: sqlite3.Connection,
    concepts: list[LoadedEntry],
    form_registry: dict[str, FormDefinition],
) -> None:
    """Derive form algebra from concept parameterizations and populate the table.

    For each concept parameterization, extracts the form-level relationship
    (e.g. force = mass * acceleration) by substituting concept IDs with form
    names in the sympy expression. Deduplicates and validates with bridgman.
    """
    if not form_registry:
        return

    # Build concept artifact_id → form_name lookup
    id_to_form: dict[str, str] = {}
    for c in concepts:
        cid = _concept_artifact_id(c.data)
        form_name = c.data.get("form")
        if cid and form_name:
            id_to_form[cid] = form_name

    # Track seen entries for deduplication
    seen: set[tuple] = set()

    for c in concepts:
        cid = _concept_artifact_id(c.data)
        if not cid:
            continue
        output_form = id_to_form.get(cid)
        if not output_form:
            continue

        for param in c.data.get("parameterization_relationships", []) or []:
            inputs = param.get("inputs", []) or []
            if not inputs:
                continue

            # Resolve input forms
            input_forms = []
            all_resolved = True
            for inp_id in inputs:
                inp_form = id_to_form.get(inp_id)
                if not inp_form:
                    all_resolved = False
                    break
                input_forms.append(inp_form)
            if not all_resolved:
                continue

            # Build form-level operation from sympy
            sympy_str = param.get("sympy")
            operation = ""
            if sympy_str:
                try:
                    import sympy as sp
                    parsed = sp.sympify(sympy_str)
                    # Substitute concept IDs with form names
                    subs = {}
                    for inp_id in inputs:
                        subs[sp.Symbol(inp_id)] = sp.Symbol(id_to_form[inp_id])
                    subs[sp.Symbol(cid)] = sp.Symbol(output_form)
                    form_expr = parsed.subs(subs)
                    operation = str(form_expr)
                except Exception:
                    operation = sympy_str
            if not operation:
                operation = param.get("formula", "")

            # Validate dimensions with bridgman (only when sympy expression exists)
            dim_verified = 1
            if sympy_str and operation:
                output_fd = form_registry.get(output_form)
                input_fd_list = [form_registry.get(f) for f in input_forms]
                if output_fd is not None and all(f is not None for f in input_fd_list):
                    if not verify_form_algebra_dimensions(
                        output_fd, input_fd_list, operation  # type: ignore[arg-type]
                    ):
                        dim_verified = 0
                else:
                    dim_verified = 0

            # Dedup key: (output_form, sorted input forms, canonical operation)
            try:
                canon_op = canonical_dump(operation, {})
            except Exception:
                canon_op = operation
            dedup_key = (output_form, tuple(sorted(input_forms)), canon_op)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            conn.execute(
                "INSERT INTO form_algebra "
                "(output_form, input_forms, operation, source_concept_id, "
                "source_formula, dim_verified) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (output_form, json.dumps(input_forms), operation, cid,
                 param.get("formula", ""), dim_verified),
            )


def _populate_forms(
    conn: sqlite3.Connection,
    form_registry: dict[str, FormDefinition],
) -> None:
    """Populate the form table from a pre-loaded form registry."""
    for fd in form_registry.values():
        dims_json = json.dumps(fd.dimensions) if fd.dimensions is not None else None
        conn.execute(
            "INSERT INTO form (name, kind, unit_symbol, is_dimensionless, dimensions) "
            "VALUES (?, ?, ?, ?, ?)",
            (fd.name, fd.kind.value if hasattr(fd.kind, 'value') else str(fd.kind),
             fd.unit_symbol, 1 if fd.is_dimensionless else 0, dims_json),
        )


def _populate_concepts(
    conn: sqlite3.Connection,
    concepts: list[LoadedEntry],
    form_registry: dict[str, FormDefinition],
):
    for seq, c in enumerate(concepts, 1):
        d = c.data
        created = d.get("created_date")
        if created and not isinstance(created, str):
            created = str(created)
        modified = d.get("last_modified")
        if modified and not isinstance(modified, str):
            modified = str(modified)

        # Extract range bounds
        range_val = d.get("range")
        range_min = None
        range_max = None
        if isinstance(range_val, list) and len(range_val) >= 2:
            range_min = float(range_val[0])
            range_max = float(range_val[1])

        # Serialize form_parameters as JSON
        form_params = d.get("form_parameters")
        form_params_json = json.dumps(form_params) if form_params else None

        content_hash = _concept_content_hash(d)

        # Look up form definition from registry
        form_name = d.get("form")
        form_def = form_registry.get(form_name) if isinstance(form_name, str) else None
        is_dimensionless = 1 if (form_def is not None and form_def.is_dimensionless) else 0
        unit_symbol = form_def.unit_symbol if form_def is not None else None

        conn.execute(
            "INSERT INTO concept (id, primary_logical_id, logical_ids_json, version_id, content_hash, seq, canonical_name, status, domain, definition, "
            "kind_type, form, form_parameters, range_min, range_max, "
            "is_dimensionless, unit_symbol, "
            "created_date, last_modified) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (_concept_artifact_id(d), _concept_primary_logical_id(d),
             json.dumps(d.get("logical_ids") or []), _concept_version_id(d),
             content_hash, seq, d.get("canonical_name"), d.get("status"),
             d.get("domain"), d.get("definition"),
             form_def.kind.value if form_def is not None else kind_value_from_form_name(d.get("form")),
             d.get("form", ""), form_params_json, range_min, range_max,
             is_dimensionless, unit_symbol,
             created, modified),
        )


def _populate_aliases(conn: sqlite3.Connection, concepts: list[LoadedEntry]):
    for c in concepts:
        d = c.data
        cid = _concept_artifact_id(d)
        for alias in d.get("aliases", []) or []:
            conn.execute(
                "INSERT INTO alias (concept_id, alias_name, source) VALUES (?, ?, ?)",
                (cid, alias.get("name"), alias.get("source")),
            )


def _populate_relationships(
    conn: sqlite3.Connection,
    concepts: list[LoadedEntry],
    concept_registry: dict[str, dict],
):
    for c in concepts:
        d = c.data
        source_id = _concept_artifact_id(d)
        for rel in d.get("relationships", []) or []:
            conditions = rel.get("conditions", []) or []
            conditions_json = json.dumps(conditions) if conditions else None
            target_id = _resolve_concept_reference(rel.get("target"), concept_registry)
            conn.execute(
                "INSERT INTO relationship (source_id, type, target_id, conditions_cel, note) VALUES (?, ?, ?, ?, ?)",
                (source_id, rel.get("type"), target_id,
                 conditions_json, rel.get("note")),
            )
            conn.execute(
                "INSERT INTO relation_edge (source_kind, source_id, relation_type, target_kind, target_id, conditions_cel, note) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("concept", source_id, rel.get("type"), "concept", target_id, conditions_json, rel.get("note")),
            )


def _populate_parameterizations(
    conn: sqlite3.Connection,
    concepts: list[LoadedEntry],
    concept_registry: dict[str, dict],
):
    for c in concepts:
        d = c.data
        for param in d.get("parameterization_relationships", []) or []:
            raw_inputs = param.get("inputs", [])
            inputs = [
                _resolve_concept_reference(input_id, concept_registry)
                if isinstance(input_id, str)
                else input_id
                for input_id in raw_inputs
            ]
            conditions = param.get("conditions", []) or []
            conn.execute(
                "INSERT INTO parameterization (output_concept_id, concept_ids, formula, sympy, exactness, conditions_cel) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (_concept_artifact_id(d), json.dumps(inputs), param.get("formula"), param.get("sympy"),
                 param.get("exactness"),
                 json.dumps(conditions) if conditions else None),
            )


def _insert_claim_row(conn: sqlite3.Connection, row: dict[str, object]) -> None:
    conn.execute(
        "INSERT INTO claim_core (id, primary_logical_id, logical_ids_json, version_id, seq, type, concept_id, target_concept, source_paper, provenance_page, provenance_json, context_id, branch) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            row["id"],
            row["primary_logical_id"],
            row["logical_ids_json"],
            row["version_id"],
            row["seq"],
            row["type"],
            row["concept_id"],
            row["target_concept"],
            row["source_paper"],
            row["provenance_page"],
            row["provenance_json"],
            row["context_id"],
            row.get("branch"),
        ),
    )
    conn.execute(
        "INSERT INTO claim_numeric_payload (claim_id, value, lower_bound, upper_bound, uncertainty, uncertainty_type, sample_size, unit, value_si, lower_bound_si, upper_bound_si) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            row["id"],
            row["value"],
            row["lower_bound"],
            row["upper_bound"],
            row["uncertainty"],
            row["uncertainty_type"],
            row["sample_size"],
            row["unit"],
            row["value_si"],
            row["lower_bound_si"],
            row["upper_bound_si"],
        ),
    )
    conn.execute(
        "INSERT INTO claim_text_payload (claim_id, conditions_cel, statement, expression, sympy_generated, sympy_error, name, measure, listener_population, methodology, notes, description, auto_summary) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            row["id"],
            row["conditions_cel"],
            row["statement"],
            row["expression"],
            row["sympy_generated"],
            row["sympy_error"],
            row["name"],
            row["measure"],
            row["listener_population"],
            row["methodology"],
            row["notes"],
            row["description"],
            row["auto_summary"],
        ),
    )
    conn.execute(
        "INSERT INTO claim_algorithm_payload (claim_id, body, canonical_ast, variables_json, stage) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            row["id"],
            row["body"],
            row["canonical_ast"],
            row["variables_json"],
            row["stage"],
        ),
    )


def _normalize_conditions_differ(value: object) -> object:
    """Normalize stance ``conditions_differ`` for SQLite storage."""
    if isinstance(value, list):
        return json.dumps(value)
    return value


def _coerce_stance_resolution(
    resolution: object,
    owner: str,
) -> dict[str, object]:
    """Return a stance resolution mapping or raise a clean error."""
    if resolution is None:
        return {}
    if not isinstance(resolution, dict):
        raise ValueError(f"{owner} resolution must be a mapping")
    return resolution


def _insert_claim_stance_row(conn: sqlite3.Connection, stance_row: tuple) -> None:
    supported_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(relation_edge)").fetchall()
    }
    row_values = {
        "source_kind": "claim",
        "source_id": stance_row[0],
        "relation_type": stance_row[2],
        "target_kind": "claim",
        "target_id": stance_row[1],
        "target_justification_id": stance_row[3],
        "strength": stance_row[4],
        "conditions_differ": _normalize_conditions_differ(stance_row[5]),
        "note": stance_row[6],
        "resolution_method": stance_row[7],
        "resolution_model": stance_row[8],
        "embedding_model": stance_row[9],
        "embedding_distance": stance_row[10],
        "pass_number": stance_row[11],
        "confidence": stance_row[12],
        "opinion_belief": stance_row[13],
        "opinion_disbelief": stance_row[14],
        "opinion_uncertainty": stance_row[15],
        "opinion_base_rate": stance_row[16],
    }
    columns = [name for name in row_values if name in supported_columns]
    placeholders = ", ".join("?" for _ in columns)
    conn.execute(
        f"INSERT INTO relation_edge ({', '.join(columns)}) VALUES ({placeholders})",
        tuple(row_values[name] for name in columns),
    )


def _populate_parameterization_groups(conn: sqlite3.Connection, concepts: list[LoadedEntry]):
    """Build connected-component groups and write to parameterization_group table."""
    concept_dicts = [c.data for c in concepts]
    groups = build_groups(concept_dicts)
    for group_id, group_members in enumerate(sorted(groups, key=lambda g: min(g))):
        for concept_id in sorted(group_members):
            conn.execute(
                "INSERT INTO parameterization_group (concept_id, group_id) VALUES (?, ?)",
                (concept_id, group_id),
            )


def _create_context_tables(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS context (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            inherits TEXT,
            FOREIGN KEY (inherits) REFERENCES context(id)
        );

        CREATE TABLE IF NOT EXISTS context_assumption (
            context_id TEXT NOT NULL,
            assumption_cel TEXT NOT NULL,
            seq INTEGER NOT NULL,
            FOREIGN KEY (context_id) REFERENCES context(id)
        );

        CREATE TABLE IF NOT EXISTS context_exclusion (
            context_a TEXT NOT NULL,
            context_b TEXT NOT NULL,
            FOREIGN KEY (context_a) REFERENCES context(id),
            FOREIGN KEY (context_b) REFERENCES context(id)
        );

        CREATE INDEX IF NOT EXISTS idx_ctx_assumption ON context_assumption(context_id);
        CREATE INDEX IF NOT EXISTS idx_ctx_exclusion_a ON context_exclusion(context_a);
        CREATE INDEX IF NOT EXISTS idx_ctx_exclusion_b ON context_exclusion(context_b);
    """)


def _populate_contexts(
    conn: sqlite3.Connection,
    contexts: Sequence[LoadedEntry],
) -> None:
    """Populate context, context_assumption, and context_exclusion tables."""

    # First pass: insert all contexts and their assumptions
    exclusion_pairs: list[tuple[str, str]] = []
    for ctx in contexts:
        d = ctx.data
        cid = d.get("id")
        if not cid:
            continue

        conn.execute(
            "INSERT INTO context (id, name, description, inherits) VALUES (?, ?, ?, ?)",
            (cid, d.get("name", ""), d.get("description"), d.get("inherits")),
        )

        for seq, assumption in enumerate(d.get("assumptions") or [], 1):
            conn.execute(
                "INSERT INTO context_assumption (context_id, assumption_cel, seq) VALUES (?, ?, ?)",
                (cid, assumption, seq),
            )

        for exc in d.get("excludes") or []:
            exclusion_pairs.append((cid, exc))

    # Second pass: insert exclusions after all contexts exist
    for ctx_a, ctx_b in exclusion_pairs:
        conn.execute(
            "INSERT INTO context_exclusion (context_a, context_b) VALUES (?, ?)",
            (ctx_a, ctx_b),
        )


def _build_fts_index(conn: sqlite3.Connection, concepts: list[LoadedEntry]):
    """Build FTS5 index over concept names, aliases, definitions, and condition strings."""
    conn.execute("""
        CREATE VIRTUAL TABLE concept_fts USING fts5(
            concept_id UNINDEXED,
            canonical_name,
            aliases,
            definition,
            conditions
        )
    """)

    for c in concepts:
        d = c.data
        cid = _concept_artifact_id(d) or ""
        name = d.get("canonical_name", "")
        definition = d.get("definition", "")

        # Collect all alias names
        alias_names = [a.get("name", "") for a in d.get("aliases", []) or []]
        aliases_text = " ".join(alias_names)

        # Collect all condition strings
        conditions_parts = []
        for rel in d.get("relationships", []) or []:
            for cond in rel.get("conditions", []) or []:
                conditions_parts.append(cond)
        for param in d.get("parameterization_relationships", []) or []:
            for cond in param.get("conditions", []) or []:
                conditions_parts.append(cond)
        conditions_text = " ".join(conditions_parts)

        conn.execute(
            "INSERT INTO concept_fts (concept_id, canonical_name, aliases, definition, conditions) "
            "VALUES (?, ?, ?, ?, ?)",
            (cid, name, aliases_text, definition, conditions_text),
        )


def _create_claim_tables(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE claim_core (
            id TEXT PRIMARY KEY,
            primary_logical_id TEXT NOT NULL,
            logical_ids_json TEXT NOT NULL,
            version_id TEXT NOT NULL,
            seq INTEGER NOT NULL,
            type TEXT NOT NULL,
            concept_id TEXT,
            target_concept TEXT,
            source_paper TEXT NOT NULL,
            provenance_page INTEGER NOT NULL,
            provenance_json TEXT,
            context_id TEXT,
            premise_kind TEXT NOT NULL DEFAULT 'ordinary',
            branch TEXT,
            FOREIGN KEY (context_id) REFERENCES context(id)
        );

        CREATE TABLE claim_numeric_payload (
            claim_id TEXT PRIMARY KEY,
            value REAL,
            lower_bound REAL,
            upper_bound REAL,
            uncertainty REAL,
            uncertainty_type TEXT,
            sample_size INTEGER,
            unit TEXT,
            value_si REAL,
            lower_bound_si REAL,
            upper_bound_si REAL,
            FOREIGN KEY (claim_id) REFERENCES claim_core(id)
        );

        CREATE TABLE claim_text_payload (
            claim_id TEXT PRIMARY KEY,
            conditions_cel TEXT,
            statement TEXT,
            expression TEXT,
            sympy_generated TEXT,
            sympy_error TEXT,
            name TEXT,
            measure TEXT,
            listener_population TEXT,
            methodology TEXT,
            notes TEXT,
            description TEXT,
            auto_summary TEXT,
            FOREIGN KEY (claim_id) REFERENCES claim_core(id)
        );

        CREATE TABLE claim_algorithm_payload (
            claim_id TEXT PRIMARY KEY,
            body TEXT,
            canonical_ast TEXT,
            variables_json TEXT,
            stage TEXT,
            FOREIGN KEY (claim_id) REFERENCES claim_core(id)
        );

        CREATE TABLE conflict_witness (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id TEXT NOT NULL,
            claim_a_id TEXT NOT NULL,
            claim_b_id TEXT NOT NULL,
            warning_class TEXT NOT NULL,
            conditions_a TEXT,
            conditions_b TEXT,
            value_a TEXT,
            value_b TEXT,
            derivation_chain TEXT
        );

        CREATE TABLE justification (
            id TEXT PRIMARY KEY,
            justification_kind TEXT NOT NULL,
            conclusion_claim_id TEXT NOT NULL,
            premise_claim_ids TEXT NOT NULL,
            source_relation_type TEXT,
            source_claim_id TEXT,
            provenance_json TEXT,
            rule_strength TEXT NOT NULL DEFAULT 'defeasible'
        );

        CREATE TABLE IF NOT EXISTS calibration_counts (
            pass_number INTEGER NOT NULL,
            category TEXT NOT NULL,
            correct_count INTEGER NOT NULL,
            total_count INTEGER NOT NULL,
            PRIMARY KEY (pass_number, category)
        );

        CREATE VIRTUAL TABLE claim_fts USING fts5(
            claim_id UNINDEXED,
            statement,
            conditions,
            expression
        );

        CREATE INDEX idx_claim_core_concept ON claim_core(concept_id);
        CREATE INDEX idx_claim_core_target ON claim_core(target_concept);
        CREATE INDEX idx_claim_core_type ON claim_core(type);
        CREATE INDEX idx_claim_core_primary_logical_id ON claim_core(primary_logical_id);
        CREATE INDEX idx_claim_algorithm_stage ON claim_algorithm_payload(stage);
        CREATE INDEX idx_conflict_witness_concept ON conflict_witness(concept_id);
    """)


def _populate_claims(
    conn: sqlite3.Connection,
    claim_files: Sequence[LoadedEntry],
    concept_registry: dict | None = None,
    *,
    form_registry: dict[str, FormDefinition] | None = None,
):
    claim_seq = 0
    deferred_stances: list[tuple] = []
    valid_claim_ids = _collect_valid_claim_ids(claim_files)
    for cf in claim_files:
        source_paper = cf.data.get("source", {}).get("paper", cf.filename)
        for claim in cf.data.get("claims", []):
            claim_seq += 1
            row = _prepare_claim_insert_row(
                claim,
                source_paper,
                claim_seq=claim_seq,
                concept_registry=concept_registry,
                form_registry=form_registry,
            )
            _insert_claim_row(conn, row)
            deferred_stances.extend(_extract_deferred_stance_rows(claim, valid_claim_ids))

    # Insert stances after all claims are in, so target_claim_id FKs resolve
    for stance_row in deferred_stances:
        _insert_claim_stance_row(conn, stance_row)


def _collect_valid_claim_ids(claim_files: Sequence[LoadedEntry]) -> set[str]:
    valid_claim_ids: set[str] = set()
    for cf in claim_files:
        claims = cf.data.get("claims", [])
        if not isinstance(claims, list):
            continue
        for claim in claims:
            if not isinstance(claim, dict):
                continue
            claim_id = claim.get("artifact_id")
            if isinstance(claim_id, str) and claim_id:
                valid_claim_ids.add(claim_id)
    return valid_claim_ids


def _prepare_claim_insert_row(
    claim: dict,
    source_paper: str,
    *,
    claim_seq: int,
    concept_registry: dict | None = None,
    form_registry: dict[str, FormDefinition] | None = None,
) -> dict[str, object]:
    from propstore.description_generator import generate_description

    normalized_claim = _canonicalize_claim_for_storage(
        claim,
        concept_registry or {},
    )
    ctype = normalized_claim.get("type")
    prov = normalized_claim.get("provenance", {})
    conditions = normalized_claim.get("conditions")
    typed_fields = _extract_typed_claim_fields(normalized_claim)
    expression = typed_fields.expression
    sympy_generated, sympy_error = _resolve_equation_sympy(
        ctype,
        str(expression) if expression is not None else None,
        normalized_claim,
    )
    body, canonical_ast, variables_json, stage = _resolve_algorithm_storage(
        normalized_claim
    )

    # ── SI normalization ──────────────────────────────────────────────
    value_si = typed_fields.value
    lower_bound_si = typed_fields.lower_bound
    upper_bound_si = typed_fields.upper_bound
    unit = typed_fields.unit

    form_def: FormDefinition | None = None
    if form_registry and concept_registry:
        concept_id = typed_fields.concept_id
        concept_data = concept_registry.get(concept_id) if concept_id else None
        if isinstance(concept_data, dict):
            form_name = concept_data.get("form")
            if isinstance(form_name, str):
                form_def = form_registry.get(form_name)

    if form_def is not None:
        try:
            if value_si is not None:
                value_si = normalize_to_si(float(value_si), unit, form_def)
            if lower_bound_si is not None:
                lower_bound_si = normalize_to_si(float(lower_bound_si), unit, form_def)
            if upper_bound_si is not None:
                upper_bound_si = normalize_to_si(float(upper_bound_si), unit, form_def)
        except (ValueError, TypeError):
            # Unknown unit or non-numeric value — keep raw values
            value_si = typed_fields.value
            lower_bound_si = typed_fields.lower_bound
            upper_bound_si = typed_fields.upper_bound

    return {
        "id": normalized_claim.get("artifact_id"),
        "primary_logical_id": primary_logical_id(normalized_claim),
        "logical_ids_json": json.dumps(normalized_claim.get("logical_ids") or []),
        "version_id": _claim_version_id(normalized_claim),
        "seq": claim_seq,
        "type": ctype,
        "concept_id": typed_fields.concept_id,
        "value": typed_fields.value,
        "lower_bound": typed_fields.lower_bound,
        "upper_bound": typed_fields.upper_bound,
        "uncertainty": typed_fields.uncertainty,
        "uncertainty_type": typed_fields.uncertainty_type,
        "sample_size": typed_fields.sample_size,
        "unit": typed_fields.unit,
        "value_si": value_si,
        "lower_bound_si": lower_bound_si,
        "upper_bound_si": upper_bound_si,
        "conditions_cel": json.dumps(conditions) if conditions else None,
        "statement": typed_fields.statement,
        "expression": typed_fields.expression,
        "sympy_generated": sympy_generated,
        "sympy_error": sympy_error,
        "name": typed_fields.name,
        "target_concept": typed_fields.target_concept,
        "measure": typed_fields.measure,
        "listener_population": typed_fields.listener_population,
        "methodology": typed_fields.methodology,
        "notes": normalized_claim.get("notes"),
        "description": normalized_claim.get("description"),
        "auto_summary": generate_description(normalized_claim, concept_registry or {}),
        "body": body,
        "canonical_ast": canonical_ast,
        "variables_json": variables_json,
        "stage": stage,
        "source_paper": prov.get("paper", source_paper),
        "provenance_page": prov.get("page", 0),
        "provenance_json": json.dumps(prov),
        "context_id": normalized_claim.get("context"),
        "branch": claim.get("branch"),
    }


def _concept_reference_candidates(concept: dict) -> set[str]:
    candidates: set[str] = set()
    artifact_id = concept.get("artifact_id")
    if isinstance(artifact_id, str) and artifact_id:
        candidates.add(artifact_id)
    canonical_name = concept.get("canonical_name")
    if isinstance(canonical_name, str) and canonical_name:
        candidates.add(canonical_name)
    for logical_id in concept.get("logical_ids", []) or []:
        if not isinstance(logical_id, dict):
            continue
        formatted = format_logical_id(logical_id)
        if formatted:
            candidates.add(formatted)
        value = logical_id.get("value")
        if isinstance(value, str) and value:
            candidates.add(value)
    for alias in concept.get("aliases", []) or []:
        if not isinstance(alias, dict):
            continue
        alias_name = alias.get("name")
        if isinstance(alias_name, str) and alias_name:
            candidates.add(alias_name)
    return candidates


def _resolve_concept_reference(
    concept_ref: str | None,
    concept_registry: dict,
) -> str | None:
    """Resolve an ID/canonical name/logical handle/alias to the canonical concept ID."""
    if not concept_ref:
        return concept_ref

    direct = concept_registry.get(concept_ref)
    if isinstance(direct, dict):
        resolved = direct.get("artifact_id")
        if resolved:
            return resolved

    seen_ids: set[str] = set()
    for concept in concept_registry.values():
        if not isinstance(concept, dict):
            continue
        concept_id = concept.get("artifact_id")
        if not concept_id or concept_id in seen_ids:
            continue
        seen_ids.add(concept_id)
        if concept_ref in _concept_reference_candidates(concept):
            return concept_id

    return concept_ref


def _canonicalize_claim_for_storage(claim: dict, concept_registry: dict) -> dict:
    """Normalize concept references so compiled artifacts consistently use IDs."""
    normalized = dict(claim)
    artifact_id = normalized.get("artifact_id")
    if isinstance(artifact_id, str) and artifact_id:
        normalized["id"] = artifact_id

    normalized["concept"] = _resolve_concept_reference(
        normalized.get("concept"),
        concept_registry,
    )
    normalized["target_concept"] = _resolve_concept_reference(
        normalized.get("target_concept"),
        concept_registry,
    )

    concepts = normalized.get("concepts")
    if isinstance(concepts, list):
        normalized["concepts"] = [
            _resolve_concept_reference(concept_ref, concept_registry)
            for concept_ref in concepts
        ]

    variables = normalized.get("variables")
    if isinstance(variables, list):
        normalized["variables"] = []
        for variable in variables:
            if not isinstance(variable, dict):
                normalized["variables"].append(variable)
                continue
            updated = dict(variable)
            updated["concept"] = _resolve_concept_reference(
                updated.get("concept"),
                concept_registry,
            )
            normalized["variables"].append(updated)

    parameters = normalized.get("parameters")
    if isinstance(parameters, list):
        normalized["parameters"] = []
        for parameter in parameters:
            if not isinstance(parameter, dict):
                normalized["parameters"].append(parameter)
                continue
            updated = dict(parameter)
            updated["concept"] = _resolve_concept_reference(
                updated.get("concept"),
                concept_registry,
            )
            normalized["parameters"].append(updated)

    return normalized


def _extract_typed_claim_fields(claim: dict) -> _TypedClaimFields:
    fields = _TypedClaimFields()
    ctype = claim.get("type")
    if ctype == "parameter":
        numeric = _extract_numeric_claim_fields(claim)
        fields = _TypedClaimFields(
            concept_id=_optional_string(claim.get("concept")),
            value=numeric.value,
            lower_bound=numeric.lower_bound,
            upper_bound=numeric.upper_bound,
            uncertainty=numeric.uncertainty,
            uncertainty_type=numeric.uncertainty_type,
            sample_size=numeric.sample_size,
            unit=numeric.unit,
        )
    elif ctype == "measurement":
        numeric = _extract_numeric_claim_fields(claim)
        fields = _TypedClaimFields(
            target_concept=_optional_string(claim.get("target_concept")),
            measure=_optional_string(claim.get("measure")),
            listener_population=_optional_string(claim.get("listener_population")),
            methodology=_optional_string(claim.get("methodology")),
            value=numeric.value,
            lower_bound=numeric.lower_bound,
            upper_bound=numeric.upper_bound,
            uncertainty=numeric.uncertainty,
            uncertainty_type=numeric.uncertainty_type,
            sample_size=numeric.sample_size,
            unit=numeric.unit,
        )
    elif ctype == "observation":
        fields = _TypedClaimFields(statement=_optional_string(claim.get("statement")))
    elif ctype == "equation":
        fields = _TypedClaimFields(expression=_optional_string(claim.get("expression")))
    elif ctype == "model":
        fields = _TypedClaimFields(name=_optional_string(claim.get("name")))
    elif ctype == "algorithm":
        fields = _TypedClaimFields(concept_id=_optional_string(claim.get("concept")))
    return fields


def _extract_numeric_claim_fields(claim: dict) -> _TypedClaimFields:
    raw_value = claim.get("value")
    if raw_value is None:
        value = None
    else:
        try:
            value = float(raw_value)
        except ValueError:
            import logging
            logging.getLogger(__name__).warning(
                "Cannot parse value %r as float, treating as None", raw_value
            )
            value = None
    return _TypedClaimFields(
        value=value,
        lower_bound=_optional_float_input(claim.get("lower_bound")),
        upper_bound=_optional_float_input(claim.get("upper_bound")),
        uncertainty=_optional_float_input(claim.get("uncertainty")),
        uncertainty_type=_optional_string(claim.get("uncertainty_type")),
        sample_size=_optional_int(claim.get("sample_size")),
        unit=_optional_string(claim.get("unit")),
    )


def _resolve_equation_sympy(
    claim_type: str | None,
    expression: str | None,
    claim: dict,
) -> tuple[str | None, str | None]:
    if claim_type != "equation":
        return None, None
    explicit_sympy = claim.get("sympy")
    if explicit_sympy:
        return explicit_sympy, None
    if not expression:
        return None, None
    from propstore.sympy_generator import generate_sympy_with_error

    sympy_result = generate_sympy_with_error(expression)
    return sympy_result.expression, sympy_result.error


def _resolve_algorithm_storage(
    claim: dict,
) -> tuple[str | None, str | None, str | None, str | None]:
    if claim.get("type") != "algorithm":
        return None, None, None, None
    body = claim.get("body")
    stage = claim.get("stage")
    canonical_ast = None
    if body:
        variables = claim.get("variables") or []
        bindings = (
            {v["name"]: v.get("concept", "") for v in variables if isinstance(v, dict) and v.get("name")}
            if isinstance(variables, list)
            else variables if isinstance(variables, dict)
            else {}
        )
        canonical_ast = canonical_dump(body, bindings)
    raw_vars = claim.get("variables")
    variables_json = json.dumps(raw_vars) if raw_vars else None
    return body, canonical_ast, variables_json, stage


def _extract_deferred_stance_rows(
    claim: dict,
    valid_claim_ids: set[str],
) -> list[tuple]:
    cid = claim.get("artifact_id")
    rows: list[tuple] = []
    for stance in claim.get("stances", []) or []:
        if not isinstance(stance, dict):
            continue
        target_claim_id = stance.get("target")
        stance_type = stance.get("type")
        if not target_claim_id or not stance_type:
            continue
        if stance_type not in VALID_STANCE_TYPES:
            raise ValueError(
                f"claim '{cid}' uses unrecognized stance type '{stance_type}'"
            )
        if target_claim_id not in valid_claim_ids:
            raise sqlite3.IntegrityError(
                f"claim '{cid}' references nonexistent target claim '{target_claim_id}'"
            )
        resolution = _coerce_stance_resolution(
            stance.get("resolution"),
            f"claim '{cid}' stance targeting '{target_claim_id}'",
        )
        rows.append((
            cid,
            target_claim_id,
            stance_type,
            stance.get("target_justification_id"),
            stance.get("strength"),
            _normalize_conditions_differ(stance.get("conditions_differ")),
            stance.get("note"),
            resolution.get("method"),
            resolution.get("model"),
            resolution.get("embedding_model"),
            resolution.get("embedding_distance"),
            resolution.get("pass_number"),
            resolution.get("confidence"),
            resolution.get("opinion_belief"),
            resolution.get("opinion_disbelief"),
            resolution.get("opinion_uncertainty"),
            resolution.get("opinion_base_rate"),
        ))
    return rows


def _populate_conflicts(
    conn: sqlite3.Connection,
    claim_files: Sequence[LoadedEntry],
    concept_registry: dict,
    context_hierarchy: ContextHierarchy | None = None,
):
    from propstore.conflict_detector import detect_conflicts, detect_transitive_conflicts

    records = detect_conflicts(
        claim_files,
        concept_registry,
        context_hierarchy=context_hierarchy,
    )
    transitive_records = detect_transitive_conflicts(
        claim_files,
        concept_registry,
        context_hierarchy=context_hierarchy,
    )
    records.extend(transitive_records)
    for r in records:
        conn.execute(
            "INSERT INTO conflict_witness (concept_id, claim_a_id, claim_b_id, "
            "warning_class, conditions_a, conditions_b, value_a, value_b, "
            "derivation_chain) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (r.concept_id, r.claim_a_id, r.claim_b_id,
             r.warning_class.value,
             json.dumps(r.conditions_a),
             json.dumps(r.conditions_b),
             r.value_a, r.value_b,
             r.derivation_chain),
        )


def _populate_justifications(conn: sqlite3.Connection) -> None:
    claim_rows = conn.execute(
        "SELECT id, provenance_json FROM claim_core ORDER BY id"
    ).fetchall()
    for claim_id, provenance_json in claim_rows:
        conn.execute(
            "INSERT OR IGNORE INTO justification (id, justification_kind, conclusion_claim_id, premise_claim_ids, source_relation_type, source_claim_id, provenance_json, rule_strength) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"reported:{claim_id}",
                "reported",
                claim_id,
                json.dumps([]),
                None,
                claim_id,
                provenance_json,
                "defeasible",
            ),
        )

    relation_rows = conn.execute(
        """
        SELECT source_id, relation_type, target_id, note, resolution_method, resolution_model
        FROM relation_edge
        WHERE source_kind = 'claim'
          AND target_kind = 'claim'
          AND relation_type IN ('supports', 'explains')
        ORDER BY source_id, relation_type, target_id
        """
    ).fetchall()
    for source_id, relation_type, target_id, note, resolution_method, resolution_model in relation_rows:
        provenance = {
            "source_table": "relation_edge",
            "source_id": f"{source_id}->{target_id}:{relation_type}",
        }
        if note is not None:
            provenance["note"] = note
        if resolution_method is not None:
            provenance["resolution_method"] = resolution_method
        if resolution_model is not None:
            provenance["resolution_model"] = resolution_model
        conn.execute(
            "INSERT OR IGNORE INTO justification (id, justification_kind, conclusion_claim_id, premise_claim_ids, source_relation_type, source_claim_id, provenance_json, rule_strength) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"{relation_type}:{source_id}->{target_id}",
                relation_type,
                target_id,
                json.dumps([source_id]),
                relation_type,
                source_id,
                json.dumps(provenance),
                "defeasible",
            ),
        )


def _build_claim_fts_index(conn: sqlite3.Connection, claim_files: Sequence[LoadedEntry]):
    """Build FTS5 index over claim statements, conditions, and expressions."""
    for cf in claim_files:
        for claim in cf.data.get("claims", []):
            cid = claim.get("artifact_id")
            if not isinstance(cid, str) or not cid:
                continue
            statement = claim.get("statement", "") or ""
            expression = claim.get("expression", "") or ""
            conditions = claim.get("conditions", []) or []
            conditions_text = " ".join(conditions)

            conn.execute(
                "INSERT INTO claim_fts (claim_id, statement, conditions, expression) "
                "VALUES (?, ?, ?, ?)",
                (cid, statement, conditions_text, expression),
            )
