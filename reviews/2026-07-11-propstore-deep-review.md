# Propstore and tests deep review — 2026-07-11

## Scope and verification

Scope was limited to `propstore/` and `tests/`. Top-level application code,
scripts, documents, generated paper assets, and sibling repositories were not
reviewed as product surfaces. Project scripts were used only to run the named
test gate.

Current checkout facts:

- Branch: `master`.
- Pre-existing untracked paths: `pyghidra_mcp_projects/` and
  `tests/test_micropub_clark_charter.py`. Neither was changed. The latter was
  excluded from the tracked-system verdict because it is not in Git.
- `uv run pyright propstore`: 0 errors, 0 warnings.
- Logged full-suite baseline: 1,692 passed, 6 skipped, and 9 failures, all nine
  from the pre-existing untracked `tests/test_micropub_clark_charter.py`.
- Logged tracked-suite coverage run (explicitly ignoring that untracked file):
  1,690 passed, 6 skipped, 1 Hypothesis deadline failure; 88% aggregate line
  coverage (26,408 statements, 3,111 missed). The deadline failure is finding
  T1 below, not a product assertion failure.

The findings below distinguish demonstrated incorrect behavior, explicitly
skipped capability gaps, architecture/duplication debt, and test defects.

## Confirmed product defects

### F1 — High: canonical policy decoding changes user-supplied policy values

The canonical policy types do not enforce their own input invariants, and their
mapping decoders use Python truthiness/coercion in ways that change meaning.

Evidence:

- `RenderPolicy.from_dict` uses `bool(value)` for lifecycle flags
  (`propstore/world/types.py:989-991`). Therefore decoded strings such as
  `"false"`, `"0"`, and `"off"` all become `True`.
- The same bug exists in persisted policy profiles:
  `RevisionPolicy.allow_reintroduction` (`propstore/policies.py:69`),
  `MergePolicy.require_witnesses` (`propstore/policies.py:109`), and
  `SourceTrustProfile.require_digest` (`propstore/policies.py:198`).
- `MergePolicy.from_dict` iterates `branch_filter`
  (`propstore/policies.py:106-108`). A scalar string such as `"main"` becomes
  `("m", "a", "i", "n")`. `RenderPolicy.from_dict` has the same family of
  problem at `propstore/world/types.py:971-975`, and
  `SourceTrustProfile.from_dict` does it for `accepted_authorities` at
  `propstore/policies.py:191-193`.
- `RenderPolicy.__post_init__` normalizes enums and collections but does not
  validate documented numeric domains (`propstore/world/types.py:858-899`). It
  accepts non-finite or out-of-range `pessimism_index`, non-positive Monte Carlo
  epsilon, invalid confidence, negative treewidth cutoffs, and non-positive
  future limits.
- The worldline PrAF/ATMS consumer then rewrites valid falsy values with `or`:
  `future_limit=policy.future_limit or 8`
  (`propstore/worldline/argumentation.py:248`) and
  `policy.praf_mc_epsilon or 0.01`
  (`propstore/worldline/argumentation.py:268`). A supplied zero does not survive
  to the downstream owner.
- The web adapter performs stricter numeric/boolean validation
  (`propstore/web/requests.py:25-98`), but persisted worldlines and direct owner
  calls go through the permissive canonical decoders. The same policy has
  different meaning depending on entry point.

Impact: visibility can be enabled when explicitly disabled, branch filters can
select character-named branches, source-trust requirements can flip, and
reasoning-budget/tolerance settings can be silently replaced. These affect
epistemic results, not presentation alone.

Direction: make `RenderPolicy` and the policy-profile value objects enforce the
domain invariants they own. Boundary adapters may parse strings, but they must
not be the only place correctness is enforced. Reject scalar strings where a
sequence is required and reject ambiguous string-to-boolean coercion.

### F2 — High: PrAF claim calibration silently discards authored evidence

`p_arg_from_claim` says that missing required calibration returns
`NoCalibration`, but it silently falls back to the source prior when a claim
probability exists without an effective sample size.

Evidence:

- The function reads `claim_probability` (or `confidence`) and
  `effective_sample_size` (or `sample_size`) at
  `propstore/praf/engine.py:261-270`.
- It constructs claim evidence only when both are present
  (`propstore/praf/engine.py:286-290`). In every other case it assigns
  `omega_claim = omega_prior` and labels the result `STATED`
  (`propstore/praf/engine.py:291-292`).
- Consequently `{source_prior_base_rate: ..., claim_probability: 0.8}` produces
  the prior opinion rather than a `NoCalibration(missing_evidence_count, ...)`.
  The caller cannot tell that authored claim evidence was ignored.
- Relation calibration already handles the equivalent case correctly:
  `p_relation_from_stance` returns `missing_evidence_count` when confidence is
  present without a sample size (`propstore/praf/engine.py:343-349`).
- Existing tests cover “prior only,” “complete claim evidence,” and “probability
  without prior,” but not “prior plus probability without evidence count”
  (`tests/test_praf_engine.py:71-117`).

Impact: probabilistic argument acceptance can be computed from a source prior
while appearing to have consumed the claim record. This violates the system's
stated honest-ignorance rule and can materially change rankings.

Direction: distinguish “no claim evidence supplied” from “partial claim
evidence supplied.” The latter must return a typed missing-calibration result;
do not fall back to the prior.

### F3 — Medium: worldline deserialization silently corrupts or drops malformed data

The worldline persistence boundary is inconsistent: some malformed values
raise, some are iterated as character sequences, and some are silently omitted.

Evidence:

- `WorldlineDefinition.from_dict` verifies only that `targets` is truthy, then
  calls `list(targets)` (`propstore/worldline/definition.py:153-179`). A stored
  scalar target `"mass"` becomes four targets: `m`, `a`, `s`, `s`.
- `WorldlineResult.from_dict` constructs steps with a filtering comprehension
  (`propstore/worldline/query.py:192-196`). Any non-mapping step is silently
  discarded rather than invalidating the materialized result.
- `WorldlineRevisionQuery.from_dict` iterates `merge_parent_commits`
  (`propstore/worldline/query.py:120-121`); a scalar commit string is split into
  characters.
- `RevisionConflictSelection.from_mapping` blindly iterates each target value
  (`propstore/worldline/revision_types.py:130-136`), so a scalar atom id becomes
  a tuple of characters.
- `_coerce_variable_refs` returns an empty tuple for invalid non-mapping,
  non-sequence values (`propstore/worldline/result_types.py:166-179`), losing the
  malformed field without an error.

Impact: corrupted or hand-authored YAML can produce a valid-looking but
different query/result. Silent step loss is especially damaging because it
changes explanation/provenance while leaving the materialized result readable.

Direction: fail hard at the worldline document boundary. Collection fields must
accept only the documented list/mapping shapes, and every element must validate;
never filter invalid persisted elements out of semantic records.

### F4 — Medium: transient chain-query exception text contaminates content identity

The worldline hash claims equivalent transient failures hash identically, but
the chain-resolution path embeds arbitrary exception text in the hashed result.

Evidence:

- `_resolve_chain_target` catches every exception and creates
  `reason = f"chain query failed: {exc}"` in both the trace and target value
  (`propstore/worldline/resolution.py:368-388`).
- `compute_worldline_content_hash` hashes target-value dictionaries and every
  trace step (`propstore/worldline/hashing.py:35-46`). Both include `reason`.
- The hashing contract says transient failures use typed markers rather than
  exception text (`propstore/worldline/hashing.py:26-31`), and argumentation,
  revision, and sensitivity captures do use typed `WorldlineCaptureError`
  values (`propstore/worldline/runner.py:119-147`, `241-245`).

Impact: equivalent failures can generate different content hashes across
library versions, operating systems, paths, or exception wording. Exception
messages can also be persisted and rendered, leaking internal details.

Direction: represent chain failure with the same typed error vocabulary used by
the other capture paths. Log the exception separately; do not put its text in
content-addressed semantic output.

## Explicitly deferred product capability gaps

### G1 — High: PrAF argument-enumeration budget exhaustion is not surfaced

`tests/test_praf_argument_enumeration_budget.py:6-15` is entirely skipped until
Propstore consumes the gunray enumeration budget and surfaces
`ResultStatus.BUDGET_EXCEEDED`. The skipped test's contract is “no silent
truncation of partial argument enumeration.” Until this is implemented, callers
cannot reliably distinguish a complete argument set from a budget-truncated
one.

### G2 — Medium: categorical providers cannot be authored end to end

`tests/test_atms_categorical_provider_visibility.py:8-30` is skipped because the
claim charter remains float-only. The ATMS engine has an explicit
`PARAMETERIZATION_INPUT_TYPE_INCOMPATIBLE` outcome, but no canonical authoring
path can drive that outcome for categorical or boolean providers. This leaves a
tested engine branch unreachable from actual authored data.

These are not newly inferred defects; the tracked tests explicitly record them
as missing capability.

## Architecture and duplication findings

### A1 — Medium: `propstore.cli` still owns grounding query/workflow semantics

The documented CLI boundary permits request construction, owner calls, and
rendering, and explicitly forbids grounding query semantics. Current
`propstore/cli/grounding_cmds.py` loads and grounds the repository in each
command, computes section counts, searches marking sections, enumerates
arguments, and implements atom/row matching locally
(`grounding_cmds.py:41-163`). The helpers `_section_atoms`, `_atom_in_section`,
and `_row_matches_terms` are reusable grounding/query behavior, not Click or
rendering behavior.

Impact: CLI behavior cannot be reused consistently by web/app callers, and
grounding semantics can drift between adapters.

Direction: the existing grounding owner should return typed status/show/query/
argument reports. The CLI should only form the request and render the report.
This is an ownership move, not a request for a new adapter or compatibility
surface.

### A2 — High: Propstore reimplements Quire-owned document decoding

The package defines 21 `_is_mapping` functions, 10 `_optional_mapping`
functions, 3 `_required_mapping` functions, and 12 `_is_sequence` functions:
46 generic shape helpers across 22 production files. Those same files contain
18 hand-written `from_dict` methods and 27 hand-written `from_mapping` methods.
They are spread through core semantic types, worldlines, support revision,
observatory, and reporting. The divergence is observable in F3: one codec
rejects a malformed collection, one returns an empty collection, one splits a
string, and one filters invalid elements.

This is not merely cosmetic duplication. Quire already owns strict typed
document conversion and decoding through `DocumentStruct`,
`decode_document_bytes`, `convert_document_value`, `DocumentCodec`, family
codecs, and batch codecs (`../quire/quire/documents/schema.py`,
`../quire/quire/documents/codecs.py`, and
`../quire/quire/documents/batch.py`). Propstore nevertheless repeatedly accepts
`Mapping[str, Any]` deep inside core code, despite the project rule that decoded
dicts stop at IO boundaries. Examples include worldline result/revision types,
support-revision state/history/snapshot types, and graph types. The repeated
local narrowings make each semantic owner its own slightly different decoder.

Exact convergence target:

- Delete all 46 generic Propstore shape helpers. The search gate for their
  definitions must reach zero.
- Delete hand-written mapping reconstruction for Quire-backed documents and
  nested persisted semantic state. Quire must decode the complete typed
  document graph.
- Replace the `dict[str, Any]` fields on `WorldlineDefinition` (`inputs`,
  `policy`, `revision`, `results`, and `journal`) with typed document fields;
  no deserialize-after-deserialize step survives.
- Pass typed Propstore domain objects beyond the Quire boundary. Runtime owners
  validate semantic invariants, not generic mapping shapes.
- If Quire cannot express a generic nested-document feature required here, add
  that generic capability to Quire first. Do not preserve it as a Propstore
  family special case or a family-supplied custom decoder with the old shape.
- HTTP query parameters, LLM responses, and other non-Quire external inputs
  remain their adapter's parsing responsibility, but must decode directly into
  typed request/domain objects. They do not justify local Quire-like helper
  families.

This is a deletion-first ownership repair, not a consolidation into a new
Propstore codec module. Inventory and per-symbol disposition come before the
first deletion; then each bounded slice deletes its local codec surface first,
classifies the broken dependency edges, moves any genuinely generic missing
capability to Quire, rewrites callers to typed owners, commits the reduction,
and repeats to the zero-hit search gate.

### A3 — Low: CLI presentation scaffolding is copied across claim, concept, and world

`propstore/cli/claim/__init__.py` and
`propstore/cli/concept/__init__.py` are near copies. They duplicate
`format_option`, `lifecycle_options`, `lifecycle_policy`, `open_world`, and
`emit_report_json` (roughly lines 46-118 in both files). The world CLI repeats
the format/lifecycle policy and JSON-emission pieces at
`propstore/cli/world/__init__.py:115-177`.

Impact: user-facing option help and error mapping can drift. A direct comparison
already shows family-specific wording embedded in otherwise identical option
declarations.

Direction: remove repeated CLI declarations by giving their existing owner a
single direct surface. Do not add per-family wrappers around a new helper.

### A4 — Medium: claim identity crosses its owner boundary as mutable dict payloads

`propstore/families/identity/claims.py` exposes identity operations over
`dict[str, object]` (`canonicalize_claim_for_version`,
`compute_claim_version_id`, and `normalize_canonical_claim_payload`, lines
59-103). `source/claims.py` and `artifact_codes.py` serialize typed claim
documents to mutable dicts to call those operations. During canonicalization,
non-string condition entries are silently filtered from the version payload
(`families/identity/claims.py:70-74`), creating another potential silent-loss
boundary.

Impact: claim identity depends on an untyped payload convention repeated by
multiple callers. A future charter field can be omitted, normalized
differently, or silently removed without a type error.

Direction: identity should consume the typed claim/document owner directly and
derive canonical bytes from its charter. Do not preserve the dict API behind a
renamed wrapper.

## Test-system defects and blind spots

### T1 — Medium: a property test is instrumentation-sensitive

`test_p_cap_1_capture_journal_is_deterministic` disables the Hypothesis deadline
at `tests/test_capture_journal.py:100`, but the adjacent, similarly expensive
`test_p_cap_2_capture_replay_matches_direct_dispatch` does not
(`tests/test_capture_journal.py:117-130`). Under coverage, Hypothesis produced a
five-atom example taking 408 ms and failed the default 200 ms deadline. The
assertions did not fail.

Impact: coverage or slower CI workers produce a false red gate, and Hypothesis
may save a timing-only “failing” example.

### T2 — Medium: SQLite connections leak from `tests/test_opinion_schema.py`

The file opens raw connections at lines 90, 114, 140, and 173 and never closes
them. Tracemalloc confirmed those exact allocations; the property test repeats
the leak for up to 25 examples. The coverage run emitted repeated
`ResourceWarning: unclosed database` messages.

Impact: Windows file locks, warning noise, nondeterministic collection timing,
and interference with unrelated tests. These are test-owned leaks, not a
production connection-owner defect.

### T3 — Medium: high-risk worldline code is materially below the aggregate coverage

Aggregate coverage is 88%, but several boundary/orchestration modules that
carry the defects above are much lower:

- `propstore/worldline/argumentation.py`: 53%.
- `propstore/worldline/resolution.py`: 57%.
- `propstore/worldline/query.py`: 76%.
- `propstore/worldline/result_types.py`: 76%.
- `propstore/worldline/runner.py`: 77%.

The existing tests heavily cover valid round trips but do not systematically
generate malformed persisted shapes. Boundary-focused property tests should
assert either exact round-trip preservation or a loud validation error; silent
normalization/drop behavior should never be an allowed third outcome.

## Recommended order

1. Fix F2 first because it can silently change epistemic conclusions while
   reporting a valid calibrated object.
2. Fix F1 as one canonical-policy invariant slice, then add cross-entry-point
   tests proving web, CLI/app requests, persisted worldlines, and direct typed
   construction agree.
3. Fix F3 one worldline document family at a time, rejecting malformed data at
   the boundary rather than adding fallback coercers.
4. Fix F4 and G1 so incomplete/failing reasoning has stable, typed status.
5. Repair T1/T2, then use the stable coverage gate to close T3.
6. Address A1/A4 with deletion-first owner moves. A2/A3 should be reduced as a
   consequence of moving decoding and behavior to their true owners, not by
   introducing generic helper layers.

No production or test fixes are included in this review.
