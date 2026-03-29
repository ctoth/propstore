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
from propstore.form_utils import kind_value_from_form_name, load_all_forms, load_form, normalize_to_si, FormDefinition
from propstore.stances import VALID_STANCE_TYPES
from propstore.validate import LoadedConcept
from propstore.validate_claims import LoadedClaimFile
from ast_equiv import canonical_dump

from propstore.tree_reader import TreeReader

if TYPE_CHECKING:
    from propstore.cli.repository import Repository
    from propstore.validate_contexts import ContextHierarchy, LoadedContext

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


def _content_hash(
    concepts: list[LoadedConcept],
    claim_files: Sequence[LoadedClaimFile] | None = None,
    *,
    repo: Repository | None = None,
    context_files: Sequence[LoadedContext] | None = None,
) -> str:
    """Hash all semantic inputs that define the compiled sidecar."""
    h = hashlib.sha256()
    h.update(_SEMANTIC_INPUT_VERSION.encode())
    for c in sorted(concepts, key=lambda x: x.filename):
        h.update(c.filename.encode())
        h.update(json.dumps(c.data, sort_keys=True, default=str).encode())
    if claim_files:
        for cf in sorted(claim_files, key=lambda x: x.filename):
            h.update(cf.filename.encode())
            h.update(json.dumps(cf.data, sort_keys=True, default=str).encode())
    if context_files:
        for ctx in sorted(context_files, key=lambda x: x.filename):
            h.update(ctx.filename.encode())
            filepath = ctx.filepath
            if filepath is not None and Path(filepath).exists():
                h.update(Path(filepath).read_bytes())
            else:
                h.update(json.dumps(ctx.data, sort_keys=True, default=str).encode())

    forms_dirs: set[Path] = set()
    if repo is not None:
        forms_dirs.add(repo.forms_dir)
    else:
        for concept in concepts:
            if concept.filepath is not None:
                forms_dirs.add(concept.filepath.parent.parent / "forms")
    for forms_dir in sorted(forms_dirs):
        if not forms_dir.exists():
            continue
        for form_path in sorted(forms_dir.glob("*.yaml")):
            h.update(str(form_path.name).encode())
            h.update(form_path.read_bytes())

    if repo is not None and claim_files is not None:
        stances_dir = repo.stances_dir
        if stances_dir.exists():
            for stance_path in sorted(stances_dir.glob("*.yaml")):
                h.update(str(stance_path.name).encode())
                h.update(stance_path.read_bytes())

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
    h = hashlib.sha256()
    h.update((data.get("canonical_name", "")).encode())
    h.update((data.get("domain", "")).encode())
    h.update((data.get("definition", "")).encode())
    return h.hexdigest()[:16]


def _claim_content_hash(claim: dict, source_paper: str) -> str:
    """Compute a deterministic content hash for a claim.

    Identity fields: type, concept/target_concept, value, conditions (sorted),
    source paper, expression (for equations), statement (for observations).
    """
    h = hashlib.sha256()
    h.update((claim.get("type", "")).encode())
    concept_ref = claim.get("concept") or claim.get("target_concept") or ""
    h.update(str(concept_ref).encode())

    # Value — normalize to string
    value = claim.get("value")
    if value is not None:
        h.update(str(value).encode())
    for bound_field in ("lower_bound", "upper_bound"):
        bv = claim.get(bound_field)
        if bv is not None:
            h.update(f"{bound_field}:{bv}".encode())

    # Conditions — sorted for determinism
    conditions = claim.get("conditions") or []
    for c in sorted(conditions):
        h.update(c.encode())

    # Type-specific identity fields
    h.update((claim.get("expression", "")).encode())
    h.update((claim.get("statement", "")).encode())
    h.update((claim.get("name", "")).encode())
    h.update((claim.get("measure", "")).encode())
    h.update(source_paper.encode())

    return h.hexdigest()[:16]


def _populate_stances_from_files(
    conn: sqlite3.Connection,
    stances_dir: Path,
    *,
    reader: TreeReader | None = None,
) -> int:
    """Read stance YAML files and insert into normalized relation storage.

    When *reader* is provided, reads stance files from the TreeReader
    (git or filesystem abstraction). Otherwise falls back to filesystem glob.
    """
    # Load stance entries from reader or filesystem
    if reader is not None:
        stance_entries = [
            (stem, yaml.safe_load(raw) or {})
            for stem, raw in reader.list_yaml("stances")
        ]
    elif stances_dir and stances_dir.exists():
        stance_entries = []
        for f in sorted(stances_dir.glob("*.yaml")):
            with open(f, encoding="utf-8") as fh:
                stance_entries.append((f.stem, yaml.safe_load(fh) or {}))
    else:
        return 0

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



def build_sidecar(
    concepts: list[LoadedConcept],
    sidecar_path: Path,
    force: bool = False,
    claim_files: Sequence[LoadedClaimFile] | None = None,
    concept_registry: dict | None = None,
    *,
    repo: Repository | None = None,
    context_files: Sequence[LoadedContext] | None = None,
    commit_hash: str | None = None,
    reader: TreeReader | None = None,
) -> bool:
    """Build the SQLite sidecar from concept data.

    When claim_files is provided, also creates normalized claim/relation/conflict
    tables plus claim_fts. concept_registry is required for conflict detection
    when claim_files is provided.

    When *commit_hash* is provided (git-backed repo), it is used as the
    rebuild key instead of computing ``_content_hash()``.

    When *reader* is provided, stance files are loaded via the TreeReader
    instead of filesystem glob.

    Returns True if the sidecar was rebuilt, False if skipped.
    """
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if rebuild is needed
    if commit_hash is not None:
        content_hash = commit_hash
    else:
        content_hash = _content_hash(
            concepts,
            claim_files,
            repo=repo,
            context_files=context_files,
        )
    hash_path = sidecar_path.with_suffix(".hash")

    if not force and sidecar_path.exists() and hash_path.exists():
        existing_hash = hash_path.read_text().strip()
        if existing_hash == content_hash:
            return False

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
            # Intentionally broad: embedding snapshot is optional graceful degradation.
            # Any failure here (sqlite-vec issues, corrupt DB, etc.) should not block
            # the sidecar rebuild — embeddings will simply be re-generated.
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
        _populate_forms(conn, repo=repo, concepts=concepts)
        _populate_concepts(conn, concepts, repo=repo)
        _populate_aliases(conn, concepts)
        _populate_relationships(conn, concepts)
        _populate_parameterizations(conn, concepts)
        _populate_parameterization_groups(conn, concepts)
        _populate_form_algebra(conn, concepts, repo=repo)
        _build_fts_index(conn, concepts)

        if context_files:
            _populate_contexts(conn, context_files)

        if claim_files is not None:
            _create_claim_tables(conn)
            if concept_registry is None:
                concept_registry = {c.data["id"]: c.data for c in concepts if c.data.get("id")}
            # Resolve forms directory for SI normalization
            _forms_dir: Path | None = None
            if repo is not None:
                _forms_dir = repo.forms_dir
            elif concepts and concepts[0].filepath is not None:
                _forms_dir = concepts[0].filepath.parent.parent / "forms"
            _form_registry: dict[str, FormDefinition] = {}
            if _forms_dir is not None and _forms_dir.exists():
                _form_registry = load_all_forms(_forms_dir)
            _populate_claims(conn, claim_files, concept_registry, form_registry=_form_registry)
            from propstore.validate_contexts import ContextHierarchy

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
                _restore_report = restore_embeddings(conn, _embedding_snapshot)
                conn.row_factory = None
            except (ImportError, Exception) as exc:
                import sys
                print(f"Warning: embedding restore failed: {exc}", file=sys.stderr)
                conn.row_factory = None

        # Populate stances from stance files (in addition to inline stances from claims)
        if repo is not None and claim_files is not None:
            _populate_stances_from_files(conn, repo.stances_dir, reader=reader)

        if claim_files is not None:
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
    concepts: list[LoadedConcept],
    *,
    repo: Repository | None = None,
) -> None:
    """Derive form algebra from concept parameterizations and populate the table.

    For each concept parameterization, extracts the form-level relationship
    (e.g. force = mass * acceleration) by substituting concept IDs with form
    names in the sympy expression. Deduplicates and validates with bridgman.
    """
    # Build concept_id → (form_name, concept data) lookup
    id_to_form: dict[str, str] = {}
    for c in concepts:
        cid = c.data.get("id")
        form_name = c.data.get("form")
        if cid and form_name:
            id_to_form[cid] = form_name

    # Determine forms directory for dimension lookup
    forms_dir: Path | None = None
    if repo is not None:
        forms_dir = repo.forms_dir
    elif concepts and concepts[0].filepath is not None:
        forms_dir = concepts[0].filepath.parent.parent / "forms"
    if forms_dir is None or not forms_dir.exists():
        return

    # Track seen entries for deduplication
    seen: set[tuple] = set()

    for c in concepts:
        cid = c.data.get("id")
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

            # Validate dimensions with bridgman
            dim_verified = 1
            try:
                output_fd = load_form(forms_dir, output_form)
                if output_fd is None or output_fd.dimensions is None:
                    dim_verified = 0
                else:
                    input_fds = [load_form(forms_dir, f) for f in input_forms]
                    if any(fd is None or fd.dimensions is None for fd in input_fds):
                        dim_verified = 0
                    else:
                        # Build dim_map and verify
                        dim_map: dict[str, dict[str, int]] = {}
                        dim_map[output_form] = dict(output_fd.dimensions)
                        for inp_form, inp_fd in zip(input_forms, input_fds):
                            dim_map[inp_form] = dict(inp_fd.dimensions)  # type: ignore[arg-type]

                        if sympy_str and operation:
                            import sympy as sp
                            from bridgman import verify_expr
                            form_parsed = sp.sympify(operation)
                            if not isinstance(form_parsed, sp.Eq):
                                dim_verified = 0  # Not an equation — skip verification
                            elif not verify_expr(form_parsed, dim_map):
                                dim_verified = 0  # Dimensionally invalid
            except (KeyError, ValueError):
                dim_verified = 0
            except ImportError:
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
    *,
    repo: Repository | None = None,
    concepts: list[LoadedConcept] | None = None,
) -> None:
    """Populate the form table from form YAML files."""
    # Determine forms directory
    forms_dir: Path | None = None
    if repo is not None:
        forms_dir = repo.forms_dir
    elif concepts and concepts[0].filepath is not None:
        forms_dir = concepts[0].filepath.parent.parent / "forms"
    if forms_dir is None or not forms_dir.exists():
        return

    registry = load_all_forms(forms_dir)
    for fd in registry.values():
        dims_json = json.dumps(fd.dimensions) if fd.dimensions is not None else None
        conn.execute(
            "INSERT INTO form (name, kind, unit_symbol, is_dimensionless, dimensions) "
            "VALUES (?, ?, ?, ?, ?)",
            (fd.name, fd.kind.value if hasattr(fd.kind, 'value') else str(fd.kind),
             fd.unit_symbol, 1 if fd.is_dimensionless else 0, dims_json),
        )


def _populate_concepts(
    conn: sqlite3.Connection,
    concepts: list[LoadedConcept],
    *,
    repo: Repository | None = None,
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

        # Load form definition for is_dimensionless and unit_symbol
        if repo is not None:
            forms_dir = repo.forms_dir
        elif c.filepath is not None:
            forms_dir = c.filepath.parent.parent / "forms"
        else:
            forms_dir = None
        form_def = load_form(forms_dir, d.get("form")) if forms_dir is not None else None
        is_dimensionless = 1 if (form_def is not None and form_def.is_dimensionless) else 0
        unit_symbol = form_def.unit_symbol if form_def is not None else None

        conn.execute(
            "INSERT INTO concept (id, content_hash, seq, canonical_name, status, domain, definition, "
            "kind_type, form, form_parameters, range_min, range_max, "
            "is_dimensionless, unit_symbol, "
            "created_date, last_modified) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (d.get("id"), content_hash, seq, d.get("canonical_name"), d.get("status"),
             d.get("domain"), d.get("definition"),
             form_def.kind.value if form_def is not None else kind_value_from_form_name(d.get("form")),
             d.get("form", ""), form_params_json, range_min, range_max,
             is_dimensionless, unit_symbol,
             created, modified),
        )


def _populate_aliases(conn: sqlite3.Connection, concepts: list[LoadedConcept]):
    for c in concepts:
        d = c.data
        cid = d.get("id")
        for alias in d.get("aliases", []) or []:
            conn.execute(
                "INSERT INTO alias (concept_id, alias_name, source) VALUES (?, ?, ?)",
                (cid, alias.get("name"), alias.get("source")),
            )


def _populate_relationships(conn: sqlite3.Connection, concepts: list[LoadedConcept]):
    for c in concepts:
        d = c.data
        source_id = d.get("id")
        for rel in d.get("relationships", []) or []:
            conditions = rel.get("conditions", []) or []
            conditions_json = json.dumps(conditions) if conditions else None
            conn.execute(
                "INSERT INTO relationship (source_id, type, target_id, conditions_cel, note) VALUES (?, ?, ?, ?, ?)",
                (source_id, rel.get("type"), rel.get("target"),
                 conditions_json, rel.get("note")),
            )
            conn.execute(
                "INSERT INTO relation_edge (source_kind, source_id, relation_type, target_kind, target_id, conditions_cel, note) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("concept", source_id, rel.get("type"), "concept", rel.get("target"), conditions_json, rel.get("note")),
            )


def _populate_parameterizations(conn: sqlite3.Connection, concepts: list[LoadedConcept]):
    for c in concepts:
        d = c.data
        for param in d.get("parameterization_relationships", []) or []:
            inputs = param.get("inputs", [])
            conditions = param.get("conditions", []) or []
            conn.execute(
                "INSERT INTO parameterization (output_concept_id, concept_ids, formula, sympy, exactness, conditions_cel) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (d["id"], json.dumps(inputs), param.get("formula"), param.get("sympy"),
                 param.get("exactness"),
                 json.dumps(conditions) if conditions else None),
            )


def _insert_claim_row(conn: sqlite3.Connection, row: dict[str, object]) -> None:
    conn.execute(
        "INSERT INTO claim_core (id, content_hash, seq, type, concept_id, target_concept, source_paper, provenance_page, provenance_json, context_id, branch) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            row["id"],
            row["content_hash"],
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


def _populate_parameterization_groups(conn: sqlite3.Connection, concepts: list[LoadedConcept]):
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
    contexts: Sequence[LoadedContext],
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


def _build_fts_index(conn: sqlite3.Connection, concepts: list[LoadedConcept]):
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
        cid = d.get("id", "")
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
            content_hash TEXT NOT NULL,
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
        CREATE INDEX idx_claim_algorithm_stage ON claim_algorithm_payload(stage);
        CREATE INDEX idx_conflict_witness_concept ON conflict_witness(concept_id);
    """)


def _populate_claims(
    conn: sqlite3.Connection,
    claim_files: Sequence[LoadedClaimFile],
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


def _collect_valid_claim_ids(claim_files: Sequence[LoadedClaimFile]) -> set[str]:
    valid_claim_ids: set[str] = set()
    for cf in claim_files:
        claims = cf.data.get("claims", [])
        if not isinstance(claims, list):
            continue
        for claim in claims:
            if not isinstance(claim, dict):
                continue
            claim_id = claim.get("id")
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
        "id": normalized_claim.get("id"),
        "content_hash": _claim_content_hash(normalized_claim, source_paper),
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


def _resolve_concept_reference(
    concept_ref: str | None,
    concept_registry: dict,
) -> str | None:
    """Resolve an ID/canonical name/alias to the canonical concept ID."""
    if not concept_ref:
        return concept_ref

    direct = concept_registry.get(concept_ref)
    if isinstance(direct, dict):
        resolved = direct.get("id")
        if resolved:
            return resolved

    seen_ids: set[str] = set()
    for concept in concept_registry.values():
        if not isinstance(concept, dict):
            continue
        concept_id = concept.get("id")
        if not concept_id or concept_id in seen_ids:
            continue
        seen_ids.add(concept_id)
        if concept.get("canonical_name") == concept_ref:
            return concept_id
        for alias in concept.get("aliases", []) or []:
            if isinstance(alias, dict) and alias.get("name") == concept_ref:
                return concept_id

    return concept_ref


def _canonicalize_claim_for_storage(claim: dict, concept_registry: dict) -> dict:
    """Normalize concept references so compiled artifacts consistently use IDs."""
    normalized = dict(claim)

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
    cid = claim.get("id")
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
    claim_files: Sequence[LoadedClaimFile],
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


def _build_claim_fts_index(conn: sqlite3.Connection, claim_files: Sequence[LoadedClaimFile]):
    """Build FTS5 index over claim statements, conditions, and expressions."""
    for cf in claim_files:
        for claim in cf.data.get("claims", []):
            cid = claim.get("id", "")
            statement = claim.get("statement", "") or ""
            expression = claim.get("expression", "") or ""
            conditions = claim.get("conditions", []) or []
            conditions_text = " ".join(conditions)

            conn.execute(
                "INSERT INTO claim_fts (claim_id, statement, conditions, expression) "
                "VALUES (?, ?, ?, ?)",
                (cid, statement, conditions_text, expression),
            )
