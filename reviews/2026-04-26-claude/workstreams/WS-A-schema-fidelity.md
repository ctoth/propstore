# WS-A: Schema fidelity, fixture parity, and identity boundaries — FOUNDATION

**Status**: CLOSED e75581b9
**Depends on**: nothing
**Blocks**: every other workstream — until this lands, no test result can be trusted.
**Owner**: Codex implementation owner + human reviewer required (per Codex 2.1)

---

## Why this is the foundation

If `tests/conftest.py:create_world_model_schema` produces a different shape than `propstore/sidecar/schema.py`, then every WorldModel test passes against a schema production never creates. Every fix that downstream workstreams land could be "verified" against fictional production behavior. The substrate must be true before anything else can be measured against it.

The same substrate-truthfulness rule extends inward to **identity**. A row that has the right column shape but the wrong identifier is just a different kind of lie. URI authorities supplied by source-local config that do not parse as RFC 4151 tagging entities, and aliases that reach into reserved canonical namespaces, both punch holes in the propstore identity boundary. Per D-24, WS-A owns those holes.

This is also the only workstream both reviewers (Claude cluster A/N indirectly, Codex #6/#7 directly) flagged as foundational — Codex made it ws-02, Claude treated it as Tier 0. D-24 then folded URI authority validation and privileged-namespace policy into this stream so the substrate-identity invariants land with the substrate-shape invariants.

## Review findings covered

This workstream closes ALL of the following. "Done means done" — every finding listed is gone from `gaps.md` and has a green test gating it.

### Schema-parity findings (original scope)

| Finding | Source | Citation | Description |
|---|---|---|---|
| **T0.1** | Claude REMEDIATION-PLAN | n/a | Test fixtures must match production schema. |
| **T0.2** | Claude REMEDIATION-PLAN | n/a | `_REQUIRED_SCHEMA["claim_core"]` includes runtime columns. |
| **Codex #6** | `reviews/2026-04-26-codex/README.md` (line 35) | `propstore/world/model.py:126` vs `propstore/world/model.py:481`, `:727` | `_REQUIRED_SCHEMA["claim_core"]` stops at `branch` but `WorldModel` selects/filters `build_status`, `stage`, `promotion_status`, `build_diagnostics`. |
| **Codex #7** | `reviews/2026-04-26-codex/README.md` (line 38) | `tests/conftest.py:386` vs `propstore/sidecar/schema.py:79`, `:93`, `:395`, `:485` | `create_world_model_schema` is hand-written and diverges from production schema in source/concept/parameterization shapes and lifecycle columns. |
| **gaps.md** | `docs/gaps.md` | Codex review-axis-2 candidates | The schema-completeness gap was previously LOW; promote to MED and close here. |

Adjacent findings that should be closed in the same PR (cheaper here than later):

| Finding | Citation | Why included |
|---|---|---|
| Generated schema freshness | `schema/generate.py` writes `propstore/_resources/schemas`, but the tree is absent | Tests tolerate conditional copying. While we're touching the schema substrate, gate it. |
| Property-marker discipline | `tests/` has many `@given`-decorated functions without `@pytest.mark.property` | `pytest -m property` underselects today. Same substrate-truthfulness theme. |

### Identity-boundary findings (added per D-24)

| Finding | Source | Citation | Description |
|---|---|---|---|
| **T0.3** | DECISIONS.md D-24 | `propstore/uri.py:19-22` | `tag_uri(authority, kind, specific)` interpolates `authority` into a `tag:` URI without ever validating it against the RFC 4151 tagging-entity grammar. Source-supplied authorities (read from `propstore.yaml`) silently produce malformed URIs. |
| **T0.4** | DECISIONS.md D-24 | `propstore/concept_ids.py:33-43` | `_numeric_concept_id` privileges the `propstore` namespace: it walks `document.logical_ids`, returns the first match whose `namespace == "propstore"`, and silently ignores all other namespaces — even when two namespaces both encode `concept42`. The `propstore` namespace wins by hard-coded fiat. |
| **T0.5** | DECISIONS.md D-24 | `propstore/uri.py:10`, `propstore/concept_ids.py` | Source-local input can mint canonical `ps:`/privileged identifiers (no boundary check exists today). Authoring must hard-fail when source-local writers attempt to mint into reserved canonical namespaces. |
| **T0.6** | DECISIONS.md D-24 | `propstore/concept_ids.py:31-43` (alias resolution path) | Aliases must not collide with reserved canonical namespaces. Today nothing prevents an alias from shadowing `ps:` or any future privileged prefix. |

Cohesive with WS-A's substrate-truthfulness theme: schema parity ensures rows have the right shape; identity-boundary validation ensures rows have the right name and provenance. Both are pre-requirements for downstream workstreams to make meaningful claims.

## Code references (verified by direct read)

### Production schema (truth)
- `propstore/sidecar/schema.py:390-399` — `claim_core` table includes:
  ```sql
  build_status TEXT NOT NULL DEFAULT 'ingested',
  stage TEXT,
  promotion_status TEXT,
  ```
- `propstore/sidecar/schema.py:79`, `:93`, `:485` — additional production tables Codex flagged as diverging from fixtures.

### Required-schema validator (incomplete)
- `propstore/world/model.py:126-142` — `_REQUIRED_SCHEMA["claim_core"]` set ends at `"branch"`. **Missing**: `build_status`, `stage`, `promotion_status`, `build_diagnostics`.

### Runtime consumers (proof of gap)
- `propstore/world/model.py:475-488` — SELECT in `_load_claims_query` projects `core.build_status`, `core.stage`, `core.promotion_status` directly.
- `propstore/world/model.py:722-736` — `_visibility_predicates` filter on `core.stage`, `core.build_status`, `core.promotion_status` for render policy.

### Test fixture (lying)
- `tests/conftest.py:386` — `create_world_model_schema(conn)` hand-writes DDL that does not include the lifecycle columns at all. Tests using this fixture cannot exercise the render-policy filter at `model.py:727-735` because the columns it filters on don't exist.

### URI authority (unsanitized; D-24)
- `propstore/uri.py:10` — `DEFAULT_URI_AUTHORITY = "local@propstore,2026"` (well-formed by construction; the constant is fine).
- `propstore/uri.py:19-22` — `tag_uri(authority, kind, specific)` interpolates `authority` directly: `f"tag:{authority}:{normalized_kind}/{normalized_specific}"`. `kind` and `specific` are normalized via `normalize_uri_token`; `authority` is **not** normalized and **not** validated against RFC 4151 §2.1 grammar (`tagging-entity = authorityName "," date`). Any caller — including readers of `propstore.yaml` — can pass arbitrary bytes through.
- `propstore/uri.py:25-36` — `source_tag_uri`, `concept_tag_uri`, `claim_tag_uri` all flow through `tag_uri` and inherit the lack of authority validation.

### Privileged namespace (hard-coded; D-24)
- `propstore/concept_ids.py:31-43` — `_numeric_concept_id`:
  ```python
  for logical_id in document.logical_ids:
      if logical_id.namespace != "propstore":
          continue
      match = _CONCEPT_ID_RE.match(logical_id.value)
      if match:
          return int(match.group(1))
  ```
  The `if logical_id.namespace != "propstore": continue` clause silently filters out every non-`propstore` namespace. If the document carries `("propstore", "concept42")` and `("upstream", "concept42")`, only the propstore one is read; the conflict is invisible. If the document carries only `("upstream", "concept42")` plus a propstore alias whose target encodes a different number, the propstore side wins by namespace fiat with no warning.
- `propstore/concept_ids.py:39-43` — `artifact_id` fallback applies the same `_CONCEPT_ID_RE` regex but with no namespace gate at all — a different inconsistency on the same code path.

## First failing tests (write these first; they MUST fail before any production change)

1. **`tests/test_required_schema_completeness.py`** (new)
   - Builds a sidecar via `propstore.sidecar.schema` production builders.
   - For each (table, column) in a parametrized list of runtime-required surfaces (built from `WorldModel`'s SELECT and WHERE references), drops the column and asserts `WorldModel.from_path(...)` rejects the sidecar at open/validation time.
   - **Must fail**: dropping `claim_core.build_status` should be rejected; today it is not in `_REQUIRED_SCHEMA` so the validator passes and the query later crashes.

2. **`tests/test_fixture_schema_parity.py`** (new)
   - Builds DB-A via production `propstore.sidecar.schema` builders.
   - Builds DB-B via `tests/conftest.py:create_world_model_schema`.
   - Compares `PRAGMA table_info(<table>)` for every table `WorldModel` queries: column name, type, notnull, default, pk.
   - Compares `PRAGMA index_list` and `PRAGMA foreign_key_list`.
   - Asserts equality.
   - **Must fail today**: `claim_core.build_status` exists in production with `NOT NULL DEFAULT 'ingested'`, missing entirely from fixture.

3. **`tests/test_generated_schema_freshness.py`** (new)
   - Runs `schema/generate.py` into a tempdir.
   - Byte-compares against the committed `propstore/_resources/schemas/` tree.
   - If `propstore/_resources/schemas/` is missing entirely, asserts that emptiness is intentional (an explicit `EMPTY_BY_DESIGN` marker file) — otherwise fail.
   - **Must fail today**: tree is absent, no marker file.

4. **`tests/test_property_marker_discipline.py`** (new)
   - AST-walks `tests/`; finds every function decorated with `@given` (any module path).
   - Asserts each is also decorated with `@pytest.mark.property`.
   - **Must fail today**: per Codex, many `@given` tests are unmarked.

5. **`tests/test_uri_authority_validation.py`** (new — D-24)
   - Loads a config object where `propstore.yaml` declares a malformed authority — examples to parametrize: empty string, `"no_comma_no_date"`, `"local@propstore"` (missing date), `"local@,2026"` (missing authorityName), `"local@propstore,not-a-date"`, `"contains spaces,2026"`, `"contains:colon,2026"`, `"contains/slash,2026"`, a 1024-byte garbage blob.
   - Asserts the loader raises a typed `MalformedTaggingAuthority` (or equivalent) at config load — **not** later when a `tag_uri` is constructed. The boundary is the IO layer.
   - Adds positive cases: `"local@propstore,2026"`, `"q.example,2026-04-27"`, `"example.com,2000"` parse cleanly.
   - **Must fail today**: the loader does not validate authority; `tag_uri` happily produces `"tag:contains spaces,2026:source/foo"` which is not a valid `tag:` URI.

6. **`tests/test_no_privileged_namespace.py`** (new — D-24)
   - Constructs a `ConceptDocument` whose `logical_ids` contain both `("propstore", "concept42")` and `("upstream", "concept42")`.
   - Asserts `_numeric_concept_id` raises `NamespaceAmbiguity` (new exception) listing both candidate namespaces. Neither namespace wins silently.
   - Constructs a second `ConceptDocument` with `("propstore", "concept42")` and `("upstream", "concept99")`. Asserts `_numeric_concept_id` raises `NamespaceAmbiguity` because two namespaces encode different numeric IDs and no caller-supplied disambiguator was passed.
   - Adds an explicit-disambiguation API path: `_numeric_concept_id(document, namespace="upstream")` returns `99` deterministically. The caller — not the function — picks.
   - **Must fail today**: current code returns the propstore value silently; no exception class exists.

7. **`tests/test_source_cannot_mint_canonical_ids.py`** (new — D-24)
   - Drives the source-local authoring path (the writer used by the source-process pipeline) with an attempt to author `ps:concept:N` directly.
   - Asserts authoring raises `ReservedNamespaceViolation` (new exception) at the writer boundary — before any sidecar mutation.
   - Parametrize the reserved set: `ps:`, `propstore:`, plus any prefix declared in a new `RESERVED_CANONICAL_NAMESPACES` constant. Source-local input minting into any of those hard-fails.
   - Add an alias-collision case: an alias declaration whose target prefix equals a reserved namespace. Asserts `ReservedNamespaceViolation`.
   - Add a positive case: source-local authoring of an unreserved namespace (`mypaper:concept:42`) succeeds.
   - **Must fail today**: nothing checks the writer side; source input can mint `ps:` IDs, and no reserved-namespace registry exists.

8. **`tests/test_workstream_a_done.py`** (new — gating sentinel)
   - `xfail` until WS-A closes; flips to `pass` on the final commit.
   - This is the test that lets `gaps.md` know WS-A is closed (per Mechanism 2 in `REMEDIATION-PLAN.md` Part 2).

## Production change sequence

Each step lands in its own commit with a message of the form `WS-A step N — <slug>`.

### Step 1 — Expand `_REQUIRED_SCHEMA`
`propstore/world/model.py:126`: extend the `claim_core` set to include `build_status`, `stage`, `promotion_status`. If `claim_core.build_diagnostics` is the column Codex meant (or is a separate `build_diagnostics` table), expand the dict accordingly. Walk `propstore/world/model.py` for every `SELECT core.<column>` and `WHERE core.<column>` expression and reflect each into `_REQUIRED_SCHEMA`.

Acceptance: `tests/test_required_schema_completeness.py` step 1 turns green.

### Step 2 — Replace duplicate fixture schema with production builders
- Add a public function `propstore.sidecar.schema.build_minimal_world_model_schema(conn)` that calls the same DDL production uses, parameterized for fixture-minimum (no view materialization, no FTS triggers if not needed by the consumer test).
- Migrate every caller of `create_world_model_schema` in `tests/conftest.py` to call the new public function.
- Delete `create_world_model_schema` from `tests/conftest.py:386`. No alias, no shim. Per Q's "no old repos" rule.

Acceptance: `tests/test_fixture_schema_parity.py` turns green; no caller imports the deleted symbol.

### Step 3 — Generated schema freshness
- Decide: do we ship `propstore/_resources/schemas/` as part of the wheel, or generate at install? `pyproject.toml` shows hatchling — pick one.
- If shipped: `schema/generate.py` becomes a CI gate that regenerates and compares. If diff: fail.
- If generated at install: delete `propstore/_resources/schemas/` references from any code that reads it; require generation step in `pks` startup.

Acceptance: `tests/test_generated_schema_freshness.py` turns green.

### Step 4 — Property-marker discipline
- Walk `tests/` and add `@pytest.mark.property` to every `@given` function. One commit, mechanical.
- Add a `pytest_collection_modifyitems` hook in `tests/conftest.py` that warns if a `@given` test is missing the marker (defense in depth — the AST gate is the hard rule).

Acceptance: `tests/test_property_marker_discipline.py` turns green; `pytest -m property` selects every `@given` function.

### Step 5 — URI authority validation (D-24)
- New module `propstore/uri_authority.py` (or co-located with `uri.py`) implementing the RFC 4151 §2.1 tagging-entity grammar via parser combinators or a tight regex. Public API: `parse_tagging_authority(value: str) -> TaggingAuthority` raising `MalformedTaggingAuthority` on parse failure.
- `propstore/uri.py:19-22`: `tag_uri` calls `parse_tagging_authority(authority)` first; on failure it raises (no silent normalize). The `kind`/`specific` normalization stays.
- Wire validation at the IO boundary: every config-loading site that reads `authority` from `propstore.yaml` (or any source-local YAML) calls `parse_tagging_authority` immediately on load and rejects the config with `MalformedTaggingAuthority` before any downstream machinery runs. Hard-fail, not warn.
- `DEFAULT_URI_AUTHORITY` at `uri.py:10` becomes `parse_tagging_authority("local@propstore,2026")` resolved once at import time so the constant is a `TaggingAuthority` value, not a free-form string.

Acceptance: `tests/test_uri_authority_validation.py` turns green; every config loader rejects malformed authority at load; `DEFAULT_URI_AUTHORITY` is a typed value.

### Step 6 — Remove privileged-namespace logic from concept ID resolution (D-24)
- `propstore/concept_ids.py:31-43`: rewrite `_numeric_concept_id`. New contract:
  - Iterate every entry in `document.logical_ids` (and `artifact_id` if present) whose value matches `_CONCEPT_ID_RE`.
  - Collect `(namespace, numeric_id)` pairs.
  - If two distinct namespaces are present in the collected set, raise `NamespaceAmbiguity(candidates=...)` with the full candidate list. No silent winner.
  - If a `namespace=` keyword argument is supplied by the caller, restrict the collected set to that namespace before applying the ambiguity check; the caller picks.
  - If exactly one candidate remains, return its numeric id.
  - If zero candidates remain, return `None` (unchanged).
- New exception class `propstore.concept_ids.NamespaceAmbiguity` in the same module. Imported and re-exported from `propstore/__init__.py` if it's part of the public API used by callers.
- Remove the `if logical_id.namespace != "propstore": continue` clause. There is no privileged namespace.
- Update every caller of `_numeric_concept_id` to handle `NamespaceAmbiguity` — most callers will pass the resolved namespace explicitly. No try/except shrug. No fallback to "propstore wins."

Acceptance: `tests/test_no_privileged_namespace.py` turns green; grep for `"propstore"` string-equality in `concept_ids.py` returns zero hits; every caller has been updated.

### Step 7 — Reserved-namespace registry and source-write boundary (D-24)
- New module `propstore/canonical_namespaces.py` (or co-located with `concept_ids.py`) declaring `RESERVED_CANONICAL_NAMESPACES: frozenset[str]`. Initial members: `{"ps", "propstore"}`. Single source of truth; both the writer and the alias machinery import from here.
- New exception `ReservedNamespaceViolation` raised by:
  - The source-local authoring writer when input attempts to mint a logical_id whose namespace is in `RESERVED_CANONICAL_NAMESPACES`. Hard-fail before any sidecar mutation.
  - The alias resolver when an alias declaration's target prefix is in `RESERVED_CANONICAL_NAMESPACES`. Hard-fail at alias registration time, not at lookup.
- Authoring path that currently allows source input to mint `ps:concept:N` — locate via grep for namespace-acceptance and tighten to call the registry check.
- Alias registration path — same treatment.
- Document the policy in the canonical-namespaces module docstring: "Source-local input cannot mint into reserved canonical namespaces. Aliases cannot collide with reserved canonical namespaces. Both rules enforced at the IO boundary."

Acceptance: `tests/test_source_cannot_mint_canonical_ids.py` turns green; both reserved-namespace gates raise `ReservedNamespaceViolation` at the boundary, never silently.

### Step 8 — Close gaps and gate
- Update `docs/gaps.md`: remove the "missing column" / "schema fixture drift" entries; add the four identity-boundary entries (T0.3–T0.6) under the same closure SHA; add a `# WS-A closed <sha>` line in the "Closed gaps" section.
- Flip `tests/test_workstream_a_done.py` from `xfail` to `pass`.
- Update `reviews/2026-04-26-claude/workstreams/WS-A-schema-fidelity.md` STATUS line to `CLOSED <sha>`.

Acceptance: `tests/test_workstream_a_done.py` passes; gaps.md has new closed entries for both schema-parity and identity-boundary findings.

## Acceptance gates

Before declaring WS-A done, ALL must hold:

- [ ] `uv run pyright propstore` — passes with 0 errors.
- [ ] `uv run lint-imports` — passes (currently 4 contracts; this WS doesn't change that).
- [ ] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-A tests/test_required_schema_completeness.py tests/test_fixture_schema_parity.py tests/test_generated_schema_freshness.py tests/test_property_marker_discipline.py tests/test_uri_authority_validation.py tests/test_no_privileged_namespace.py tests/test_source_cannot_mint_canonical_ids.py tests/test_workstream_a_done.py` — all green.
- [ ] Full suite `powershell -File scripts/run_logged_pytest.ps1` — no NEW failures vs `logs/test-runs/pytest-20260426-154852.log` baseline (Codex's recorded baseline).
- [ ] `tests/conftest.py` no longer defines `create_world_model_schema`.
- [ ] `propstore/concept_ids.py` no longer contains `if logical_id.namespace != "propstore"` (or any string-literal privilege check).
- [ ] `propstore/uri.py:tag_uri` calls `parse_tagging_authority` before interpolation; `DEFAULT_URI_AUTHORITY` is a typed `TaggingAuthority`.
- [ ] `propstore/canonical_namespaces.py` exists and is the single source of truth for reserved namespaces; both the writer and the alias resolver import from it.
- [ ] Every config loader that reads `authority` from source-local YAML calls `parse_tagging_authority` at load (grep audit).
- [ ] `docs/gaps.md` has no open rows for the findings listed above (T0.1, T0.2, Codex #6, Codex #7, T0.3, T0.4, T0.5, T0.6, plus the two adjacent items).
- [ ] `reviews/2026-04-26-claude/workstreams/WS-A-schema-fidelity.md` STATUS line is `CLOSED <sha>`.

## Done means done

This workstream is done when **every finding in both tables at the top is closed**, not when "most" are closed. Specifically:

- T0.1, T0.2, Codex #6, Codex #7 — all four schema-parity findings have a corresponding green test in CI.
- T0.3, T0.4, T0.5, T0.6 — all four identity-boundary findings (D-24) have a corresponding green test in CI.
- Generated-schema-freshness gating exists.
- Property-marker discipline gates `pytest -m property` correctly.
- URI authority validation runs at every IO-boundary load site for source-local config; `tag_uri` cannot accept an unparsed authority.
- `_numeric_concept_id` raises `NamespaceAmbiguity` rather than silently picking; the `propstore` string-literal privilege check is gone.
- `ReservedNamespaceViolation` fires at both the source-local writer boundary and the alias-registration boundary; no source-local input or alias can reach into a reserved canonical namespace.
- `gaps.md` is updated.
- The workstream's gating sentinel test (`test_workstream_a_done.py`) has flipped from xfail to pass.

If any one of those is not true, WS-A stays OPEN. No "we'll get to namespace ambiguity later." Either it's in scope and closed, or it's explicitly removed from this WS in this file (and moved to a successor WS) before declaring done.

## Papers / specs referenced

- **RFC 4151** — *The 'tag' URI Scheme* (Kindberg & Hawke, 2005). The grammar in §2.1 (`taggingEntity = authorityName "," date`) is the authority WS-A enforces at the IO boundary.

No other paper drives WS-A. The schema-parity work is internal infrastructure; the identity-boundary work cites a single IETF RFC. Subsequent workstreams (WS-D, WS-F, WS-G, WS-H, WS-I, WS-J, WS-M, WS-P) reference more papers; WS-A's research surface is RFC 4151 and nothing else.

## Cross-stream notes

- This WS unblocks everything else. Open WS-B (render policy), WS-C (sidecar atomicity), WS-D (math naming) only after WS-A merges.
- WS-O-{arg,gun,qui,bri,ast} can run in parallel with WS-A — they are dependency-package fixes that don't require schema fidelity.
- After WS-A merges, WS-B's first test (`test_render_policy_direct_url.py`) becomes meaningfully verifiable, because the schema columns its filter relies on are now validated at sidecar open time.
- WS-M (Trusty URI / micropub identity) consumes WS-A's identity-boundary work directly: once `ps:` is reserved and source-local input cannot mint into it, WS-M's content-derived micropub IDs land into a clean canonical namespace with no source-local pollution.
- WS-N1 (rename WorldModel→WorldQuery, etc.) is unaffected by the identity-boundary work — the renames operate on Python symbols, not on URI namespaces.

## What this WS does NOT do

- Does NOT add new render-policy logic — that's WS-B.
- Does NOT change the architecture / import-linter contracts — that's WS-N (split into N1/N2 per D-26).
- Does NOT remove the broader test-suite improvements (e.g., property tests for AGM postulates) — those land in WS-G.
- Does NOT touch the contract_manifests/semantic-contracts.yaml runtime enforcement question — Claude cluster K flagged that as separate; consider it for WS-N.
- Does NOT implement Trusty URI verification — that's WS-M.
- Does NOT mint the canonical `ps:` namespace's contents (only reserves the prefix and gates writes into it). What lives at `ps:concept:N` is decided by the canonical-write path in WS-M / WS-K, not here.
- Does NOT extend the reserved-namespace registry beyond `{"ps", "propstore"}` initially. Future canonical prefixes are added in their owning workstream — WS-A only establishes the registry mechanism and the boundary check.
