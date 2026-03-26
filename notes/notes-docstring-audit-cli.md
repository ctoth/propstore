# Docstring Audit: propstore/cli/

Audited 2026-03-24. Every finding cites file and line number.

---

## 1. cli/__init__.py

### Finding 1 — OMISSION (module docstring)
- **File:** `propstore/cli/__init__.py`, line 3
- **Docstring:** `"Single entry point. Subcommand groups registered from sibling modules."`
- **Actual behavior:** The module registers both subcommand *groups* (`concept`, `context`, `claim`, `form`, `world`, `worldline`) and standalone *commands* (`validate`, `build`, `query`, `export_aliases`, `import_papers`, `init`). See lines 39-50 where `cli.add_command(...)` adds both types.
- **Severity:** OMISSION — "subcommand groups" implies only groups are registered, but over half of the registered commands are standalone commands, not groups.

### Finding 2 — OMISSION (cli function docstring)
- **File:** `propstore/cli/__init__.py`, line 26
- **Docstring:** `"Propositional Knowledge Store CLI."`
- **Actual behavior:** The function does more than serve as a CLI entry point. It performs conditional repository lookup: if the invoked subcommand is `init`, it stores the start directory and skips Repository resolution (lines 29-32); otherwise it calls `Repository.find()` and raises `ClickException` on failure (lines 33-36). This conditional path-finding behavior is not mentioned.
- **Severity:** OMISSION — the docstring is not wrong, but it hides the `init`-bypass logic that affects how every subcommand receives context.

---

## 2. cli/claim.py

### Finding 3 — OMISSION (module docstring)
- **File:** `propstore/cli/claim.py`, line 1
- **Docstring:** `"pks claim -- subcommands for claim validation and conflict detection."`
- **Actual behavior:** The file defines six subcommands: `validate`, `validate-file`, `conflicts`, `compare`, `embed`, `similar`, and `relate` (lines 18-397). Of these, only `validate`, `validate-file`, and `conflicts` are about validation/conflict detection. The remaining four (`compare`, `embed`, `similar`, `relate`) handle AST equivalence comparison, embedding generation, similarity search, and LLM-based epistemic relationship classification.
- **Severity:** OMISSION — the module docstring names only two of the four functional categories the file provides.

### Finding 4 — HALF-TRUTH (claim group docstring)
- **File:** `propstore/cli/claim.py`, line 15
- **Docstring:** `"Manage and validate claims."`
- **Actual behavior:** The group provides validation (`validate`, `validate-file`), conflict detection (`conflicts`), AST comparison (`compare`), embedding (`embed`), similarity search (`similar`), and relationship classification (`relate`). "Manage" is vague enough to cover anything, but the emphasis on "validate" undersells the embedding/similarity/relationship machinery that constitutes over half the file.
- **Severity:** HALF-TRUTH

### Finding 5 — HALF-TRUTH (compare docstring)
- **File:** `propstore/cli/claim.py`, line 160
- **Docstring:** `"Compare two algorithm claims for equivalence."`
- **Actual behavior:** The command uses `ast_compare` (line 224) which returns a result with `tier`, `equivalent`, `similarity`, and `details` fields (lines 227-231). The comparison is not a simple boolean equivalence check — it produces a tiered similarity score. The word "equivalence" overpromises; the actual output is a graded comparison.
- **Severity:** HALF-TRUTH — calling it "equivalence" comparison when it actually produces similarity tiers.

---

## 3. cli/compiler_cmds.py

### Finding 6 — OMISSION (module docstring)
- **File:** `propstore/cli/compiler_cmds.py`, line 1
- **Docstring:** `"pks validate / build / query / export-aliases -- top-level compiler commands."`
- **Actual behavior:** The file also defines `import-papers` (line 285), and the entire `world` command group with subcommands: `status`, `query`, `bind`, `explain`, `algorithms`, `derive`, `resolve`, `extensions`, `hypothetical`, `chain`, `export-graph`, `sensitivity`, `check-consistency` (lines 356-1079). That is 13+ additional commands not mentioned in the module docstring.
- **Severity:** OMISSION — the module docstring lists 4 commands but the file defines 18+. The `world` group alone is a major feature surface.

### Finding 7 — HALF-TRUTH (validate docstring)
- **File:** `propstore/cli/compiler_cmds.py`, line 19
- **Docstring:** `"Validate all concepts and claims. Runs CEL type-checking."`
- **Actual behavior:** The function also validates form schema files (lines 39-43 via `validate_form_files`). Form validation is not mentioned. Additionally, the claim "Runs CEL type-checking" cannot be verified from this file — it depends on what `validate_concepts` does internally. The docstring asserts a specific mechanism (CEL type-checking) that may or may not fire depending on concept content.
- **Severity:** HALF-TRUTH — omits form validation; CEL claim is unverifiable from this file alone.

### Finding 8 — HALF-TRUTH (build docstring)
- **File:** `propstore/cli/compiler_cmds.py`, line 88
- **Docstring:** `"Validate everything, build sidecar, run conflict detection."`
- **Actual behavior:** The build process validates forms (lines 108-116), concepts (118-128), contexts (130-146), and claims (148-165), then builds the sidecar (167-175). After that, it opens a WorldModel to read summary stats including conflict count (lines 182-218). It does NOT "run conflict detection" as a separate step — it reads conflict data that was presumably computed during `build_sidecar`. The docstring also omits context validation as a step.
- **Severity:** HALF-TRUTH — "run conflict detection" implies an active step, but the code just reads stats from the sidecar. Context validation is omitted.

### Finding 9 — OMISSION (_parse_bindings docstring)
- **File:** `propstore/cli/compiler_cmds.py`, lines 545-548
- **Docstring:** `"Parse CLI args into (bindings, concept_id). Arguments with '=' are bindings, the last argument without '=' is concept_id."`
- **Actual behavior:** If multiple non-binding arguments are provided, only the last one is used as `concept_id` (line 551: `non_binding[-1] if non_binding else None`). All preceding non-binding arguments are silently discarded. The docstring says "the last argument" which is technically correct, but it omits the fact that extra non-binding args are silently dropped.
- **Severity:** OMISSION — silent data loss for extra positional arguments.

### Finding 10 — HALF-TRUTH (world_extensions docstring)
- **File:** `propstore/cli/compiler_cmds.py`, line 673
- **Docstring:** `"Show argumentation extensions -- all claims that survive scrutiny."`
- **Actual behavior:** The description "all claims that survive scrutiny" only fits grounded semantics where the result is a single set of justified claims (lines 771-797). For preferred/stable semantics, the result is a collection of alternative extensions (lines 798-806), and claims in one extension may not survive in another. The docstring describes only the grounded case.
- **Severity:** HALF-TRUTH — misleading for non-grounded semantics, which the command explicitly supports via the `--semantics` option.

### Finding 11 — HALF-TRUTH (world_hypothetical docstring)
- **File:** `propstore/cli/compiler_cmds.py`, line 819
- **Docstring:** `"Show what changes if claims are removed/added."`
- **Actual behavior:** The command constructs a `HypotheticalWorld` and calls `diff()` (lines 848-849), then displays per-concept status transitions (lines 854-855). The docstring is technically correct but omits that the diff operates at the concept-value-result level, not at the claim level. Users might expect to see which claims changed, but they actually see concept status transitions.
- **Severity:** HALF-TRUTH

---

## 4. cli/concept.py

### Finding 12 — HALF-TRUTH (_rename_cel_identifier docstring)
- **File:** `propstore/cli/concept.py`, line 39
- **Docstring:** `"Rename a CEL identifier without touching quoted string literals."`
- **Actual behavior:** The function correctly skips single- and double-quoted strings (lines 45-51) and replaces identifier tokens matching `old_name` with `new_name` (lines 58-65). However, it does not handle escaped quotes within strings robustly: the check `expression[i - 1] != "\\"` at line 47 only checks one level of escape, and `i == 0` before that check means it does handle the edge case of a quote at position 0. The docstring's claim is mostly correct, but the escape handling is fragile for nested/double-escaped strings.
- **Severity:** HALF-TRUTH — works for simple cases but the escape handling is not fully robust, which is not acknowledged.

---

## 5. cli/context.py

No significant docstring issues found. The module docstring (line 1) accurately describes the file. The `add` docstring (line 34) and `list_contexts` docstring (line 74) match their implementations.

---

## 6. cli/form.py

### Finding 13 — HALF-TRUTH (form validate docstring)
- **File:** `propstore/cli/form.py`, lines 192-196
- **Docstring:** `"Validate form definitions (one or all). Checks that every form YAML has a valid name field and that forms referenced by concepts actually exist."`
- **Actual behavior:** The function also validates that the `name` field matches the filename (line 224-225: `if form_name != path.stem`), and it validates that the file is a valid YAML mapping (line 217-218). The docstring mentions "valid name field" which partially covers this, but omits the filename-match check, which is a distinct validation rule.
- **Severity:** HALF-TRUTH — omits the filename-must-match-name-field check.

---

## 7. cli/helpers.py

### Finding 14 — HALF-TRUTH (module docstring)
- **File:** `propstore/cli/helpers.py`, line 1
- **Docstring:** `"Shared helpers for CLI subcommands."`
- **Actual behavior:** The file provides file locking (`_lock_file`, `_unlock_file`), counter management (`read_counter`, `write_counter`, `CounterLock`, `atomic_next_counter`, `next_id`), YAML I/O (`load_concept_file`, `write_yaml_file`, `write_concept_file`), concept lookup (`find_concept`, `load_all_concepts_by_id`), and exit codes. The docstring is technically correct but so generic it says nothing.
- **Severity:** HALF-TRUTH — while not wrong, it provides zero information about what kind of helpers are in the file.

### Finding 15 — HALF-TRUTH (find_concept docstring)
- **File:** `propstore/cli/helpers.py`, line 177
- **Docstring:** `"Find a concept file by ID or canonical_name. Returns filepath or None."`
- **Actual behavior:** The "canonical_name" lookup is actually a *filename* lookup (line 182: `cdir / f"{id_or_name}.yaml"`). It matches against the filename, not the `canonical_name` field inside the YAML. If a file was renamed without updating `canonical_name`, or vice versa, this function would find the wrong concept or fail to find it. The docstring claims to search by `canonical_name` but the code searches by filename.
- **Severity:** HALF-TRUTH — relies on the convention that filename == canonical_name, but doesn't actually read the YAML to verify. The ID search path (lines 187-192) does correctly search inside YAML files.

### Finding 16 — STALE (read_counter docstring)
- **File:** `propstore/cli/helpers.py`, line 71
- **Docstring:** `"Read the global concept counter from the given counters directory."`
- **Actual behavior:** The function also has a migration fallback: if `global.next` doesn't exist, it scans existing concept files to find the highest ID and returns max+1 (line 76: `return _scan_max_concept_id(counters.parent) + 1`). The docstring says "read the global concept counter" but the function may *compute* the counter by scanning the filesystem when no counter file exists.
- **Severity:** OMISSION — the migration/scan-fallback behavior is undocumented.

### Finding 17 — HALF-TRUTH (next_id docstring)
- **File:** `propstore/cli/helpers.py`, lines 141-143
- **Docstring:** `"Return (concept_id, next_counter) and increment the counter file."`
- **Actual behavior:** The return value is `(cid, n)` where `n` is the *current* counter value (before increment), and `cid` is `f"concept{n}"`. The counter file is written with `n+1` by `atomic_next_counter` -> `CounterLock.commit()` (line 118: `write_counter(self._counters, self.value + 1)`). The docstring says "next_counter" for the second element, but the returned value `n` is actually the *current* counter (the one used for this ID), not the next one.
- **Severity:** HALF-TRUTH — "next_counter" in the return description is misleading; the second element is the counter value used for the returned ID, not the incremented value written to disk.

---

## 8. cli/init.py

### Finding 18 — OMISSION (init docstring)
- **File:** `propstore/cli/init.py`, lines 40-45
- **Docstring:** `"Creates the standard directory structure (concepts/, claims/, sidecar/) needed for pks to operate."`
- **Actual behavior:** `Repository.init()` at `propstore/cli/repository.py` lines 99-110 creates seven directories: `concepts/.counters`, `claims`, `contexts`, `forms`, `sidecar`, `stances`, `worldlines`. Additionally, `_seed_forms()` populates `forms/` with YAML files (lines 23-33). The docstring only mentions 3 of 7 directories and does not mention form seeding.
- **Severity:** OMISSION — hides the creation of contexts/, forms/, stances/, worldlines/, .counters/, and the form seeding behavior. The printed output at lines 61-67 is actually more accurate than the docstring.

### Finding 19 — HALF-TRUTH (_seed_forms docstring)
- **File:** `propstore/cli/init.py`, line 24
- **Docstring:** `"Populate forms/ for a freshly initialized project."`
- **Actual behavior:** The function has two code paths: (1) copy form YAML files from the package's own `forms/` directory if it exists (lines 25-29), or (2) generate minimal stub YAML files from a hardcoded list of form names (lines 31-33). Path (2) produces stubs with `kind:` and `dimensionless: false` fields, which may not match the actual form schema. The docstring hides the fallback behavior.
- **Severity:** HALF-TRUTH — "populate" doesn't distinguish between copying real definitions vs generating stubs.

---

## 9. cli/repository.py

### Finding 20 — HALF-TRUTH (Repository class docstring)
- **File:** `propstore/cli/repository.py`, lines 13-16
- **Docstring:** `"A propstore knowledge repository rooted at a ``knowledge/`` directory."`
- **Actual behavior:** The constructor (`__init__` at line 19) accepts any `Path` as root — it does not require the directory to be named `knowledge/`. The `init` classmethod (line 97) also creates a repository at any path. Only the `find` classmethod (line 74) specifically searches for a directory named `knowledge/`. A `Repository` can be rooted at any directory that contains `concepts/`.
- **Severity:** HALF-TRUTH — the class is not inherently tied to a `knowledge/` directory name; only the `find()` discovery mechanism prefers that name.

### Finding 21 — OMISSION (Repository.find docstring)
- **File:** `propstore/cli/repository.py`, lines 75-79
- **Docstring:** `"Walk up from *start* (default: cwd) looking for a ``knowledge/`` directory. Also recognises *start* itself as a repository root if it contains a ``concepts/`` subdirectory."`
- **Actual behavior:** The first check (line 84) tests `current / "concepts"` — if `start` itself has a `concepts/` subdirectory, it returns immediately without walking up. The walk-up at lines 87-90 iterates `[current, *current.parents]`, which means it checks `current` *again* for `current / "knowledge"` before walking up to parents. This means `current` is checked twice: once for `concepts/` directly, and once for `knowledge/concepts/`. The double-check of `current` is not mentioned.
- **Severity:** OMISSION — minor, but the walk also checks the current directory for `knowledge/` in addition to the direct `concepts/` check.

### Finding 22 — OMISSION (Repository.init docstring)
- **File:** `propstore/cli/repository.py`, line 98
- **Docstring:** `"Create the directory structure and return a Repository."`
- **Actual behavior:** The method creates seven directories including `worldlines/` (line 107), which is not part of the "standard" set mentioned in any other docstring. The docstring is correct but gives no information about what directories are created.
- **Severity:** OMISSION — could at minimum list the directories created.

---

## 10. cli/worldline_cmds.py

### Finding 23 — HALF-TRUTH (worldline group docstring)
- **File:** `propstore/cli/worldline_cmds.py`, line 52
- **Docstring:** `"Materialized query artifacts -- traced paths through the knowledge space."`
- **Actual behavior:** Not all worldlines are "materialized" — the `create` command (line 66) explicitly creates a worldline definition without materializing it. The `show` command (line 195) can display un-materialized worldlines. The docstring implies all worldlines are materialized, but the group supports a lifecycle from definition to materialization.
- **Severity:** HALF-TRUTH — conflates the concept (materialized query) with the lifecycle (definition -> materialization).

### Finding 24 — HALF-TRUTH (worldline_run docstring)
- **File:** `propstore/cli/worldline_cmds.py`, line 121
- **Docstring:** `"Run (materialize) a worldline. Creates it first if it doesn't exist."`
- **Actual behavior:** When the file doesn't exist and the command creates a new worldline, it does NOT save the definition before running — it goes straight to `run_worldline(wl, wm)` at line 173. The worldline file is only written after materialization completes (line 175: `wl.to_file(path)`), meaning the definition and results are saved together. If materialization fails, no file is created. The docstring implies creation and running are separate sequential steps, but they are atomic.
- **Severity:** HALF-TRUTH — the creation and running are not actually separate; if run fails, nothing is "created."

### Finding 25 — OMISSION (worldline_show docstring)
- **File:** `propstore/cli/worldline_cmds.py`, line 195
- **Docstring:** `"Show a worldline's results."`
- **Actual behavior:** The command shows much more than results: it displays the worldline name (line 206), bindings (207-208), overrides (209-210), context (211-212), targets (213), staleness check if `--check` flag is set (221-232), results (234-248), derivation trace (250-261), sensitivity data (263-270), argumentation/defeated claims (272-275), and dependency info (277-278). The docstring vastly understates the output.
- **Severity:** OMISSION — "show results" hides the display of inputs, staleness checks, derivation traces, sensitivity, argumentation, and dependencies.

### Finding 26 — OMISSION (worldline_refresh docstring)
- **File:** `propstore/cli/worldline_cmds.py`, line 378
- **Docstring:** `"Re-run a worldline with current knowledge."`
- **Actual behavior:** The implementation simply delegates to `worldline_run` via `ctx.invoke(worldline_run, name=name, bindings=(), overrides=(), targets=(), strategy=None, context=None)` at line 381. Because it passes empty tuples for bindings/overrides/targets and None for strategy/context, CLI overrides from the refresh command are NOT forwarded — only the persisted definition's values are used. The docstring doesn't mention that all CLI override parameters are ignored.
- **Severity:** OMISSION — users cannot pass overrides via refresh; it always uses the saved definition. But `refresh` command also does not accept those options, so this is more of a design note than a lie.

---

## Summary

| Severity | Count |
|----------|-------|
| LIE | 0 |
| HALF-TRUTH | 14 |
| STALE | 0 |
| OMISSION | 12 |

No outright lies were found. The dominant pattern is docstrings that were probably accurate when first written but were never updated as commands grew in scope. The most significant omissions are in `compiler_cmds.py` (module docstring listing 4 of 18+ commands) and `init.py` (listing 3 of 7 created directories). The most significant half-truths are in `helpers.py` (`find_concept` searching by filename not canonical_name field) and `repository.py` (class not actually tied to `knowledge/` name).
