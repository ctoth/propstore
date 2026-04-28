# WS-B: Render policy & web data leak

**Status**: CLOSED bb0bf7fe
**Depends on**: WS-A (schema fidelity — render-policy filters reference `claim_core.stage`, `build_status`, `promotion_status`; until WS-A lands those columns are not validated at sidecar open and tests against the policy run on a substrate production never produces).
**Blocks**: nothing downstream — but every day it stays open is a day a hidden draft/blocked claim is one URL away from a third party.
**Owner**: TBD (Codex implementation owner + human reviewer required).

---

## Why this is urgent

Render policy is the propstore privacy boundary. If `/claim/{id}.json` returns the statement, value, and provenance of a draft or blocked claim because the route didn't consult the policy before populating the report, the boundary is fictional. Codex #8 / #9 / #10 / #11 and Claude T1.1 / T1.2 / T1.3 / T1.5 / T1.8 / T1.9 are all variants of the same architectural mistake: **render policy is consulted as metadata on the way out instead of as a gate on the way in**. The fix has the same shape everywhere — filter at the data-access boundary, not at the presentation boundary. For blocked single-claim reads the gate isn't a redaction filter, it's an outright refusal to render.

This is also asymmetric in cost-of-delay terms (per `REMEDIATION-PLAN.md` Tier 1, line 33). Math/naming bugs reveal themselves in tests; a render-policy bypass reveals itself in a leak. There is no good day-one mitigation for "we already shipped the wrong claim text to a browser."

A11y note (Q is blind, the propstore UI is screen-reader-targeted): under D-21 the blocked path renders no claim page and no redacted region. The a11y obligation is on the **error page** — it must have a useful `<title>`, a useful `<h1>` heading, a clearly-announced explanation, and a useful next action (e.g., a link back to the index, or a search box). The HTML at `propstore/web/html.py:73-117` already uses `aria-labelledby` regions for normal pages; the error template needs the same skeleton. Per `a11y:cognitive-a11y` and `a11y:accessible-content-writing`, the error message must be plain language, not require the user to infer cause from absence, and not leak the existence of the blocked claim by saying anything more specific than the chosen status code's standard meaning ("Not Found" for anonymous, "Forbidden" for identified).

## Review findings covered

This workstream closes ALL of the following. "Done means done" — every finding listed is removed from `gaps.md` and has a green test gating it.

| Finding | Source | Citation | Description | Verdict |
|---|---|---|---|---|
| **T1.1** | Claude REMEDIATION-PLAN | n/a | Render-policy enforcement on direct `/claim/{id}` URL — must hard-error. | D-21: hard error, no page rendered. |
| **T1.2** | Claude REMEDIATION-PLAN | n/a | Render-policy enforcement on neighborhood routes — filter `world.all_claim_stances()`. | Hidden claims must not appear in neighborhood graphs. |
| **T1.3** | Claude REMEDIATION-PLAN | n/a | Render-policy on concept pages — do not disclose hidden claim counts. | Hidden claims must not appear in concept aggregates. |
| **T1.5** | Claude REMEDIATION-PLAN | n/a | Read-only sidecar opens in read-only mode from start. | Unchanged from D-21. |
| **T1.8** | Claude REMEDIATION-PLAN | n/a | Web request-boundary float validation — reject NaN/inf/out-of-range. | Unchanged from D-21. |
| **T1.9** | Claude REMEDIATION-PLAN | n/a | `pks web --host 0.0.0.0` requires `--insecure` flag. | Unchanged from D-21. |
| **Codex #4** | `reviews/2026-04-26-codex/README.md` | `propstore/sidecar/query.py:21-30`, `propstore/sidecar/sqlite.py:20-22` | Read-only sidecar query opens write-capable mode and sets `journal_mode=WAL` BEFORE applying `query_only`. | Unchanged from D-21. |
| **Codex #8** | `reviews/2026-04-26-codex/README.md` | `propstore/web/routing.py:144-170`, `propstore/app/claim_views.py:168-195` | "Blocked claim returns full ClaimViewReport even when `visible_under_policy=False`": `build_claim_view` populates statement/value/provenance unconditionally; only `status.visible_under_policy` is set. | **D-21: hard error.** `ClaimViewBlockedError` raised before report is built; route maps to 403 (identified user) or 404 (anonymous). No `ClaimViewReport` is constructed for a blocked claim. |
| **Codex #9** | `reviews/2026-04-26-codex/README.md` | `propstore/app/neighborhoods.py:135-153`, `propstore/world/model.py:887-912` | Neighborhood routes leak hidden supporter/attacker IDs via unfiltered `all_claim_stances()`. | Same hard-error principle — hidden endpoints must not appear in graphs. Filter at the world layer. |
| **Codex #10** | `reviews/2026-04-26-codex/README.md` | `propstore/app/concept_views.py:242-272` | Concept pages disclose hidden claim counts (`blocked_claim_count`, `total_claim_count`) and per-type blocked distribution. | Same hard-error principle — hidden claims must not appear in aggregates. |
| **Codex #11** | `reviews/2026-04-26-codex/README.md` | `propstore/web/routing.py:376-409`, `propstore/app/concepts/display.py:40-50`, `propstore/web/routing.py:61-70` | Malformed concept FTS queries escape as 500s — `sqlite3.OperationalError` is not in `_EXPECTED_WEB_ERRORS`. | Typed error → 400. |

The "open question for Q on blocked-claim behavior" from the previous draft is **resolved by D-21 — hard error, no page rendered**. There is no redacted-page rendering in WS-B's scope.

## Code references (verified by direct read)

### Direct claim leak (Codex #8 / T1.1) — D-21 hard-error path

- `propstore/web/routing.py:144-170` — both `/claim/{id}.json` and `/claim/{id}` route through `_claim_report` -> `build_claim_view`. No policy short-circuit at the route layer.
- `propstore/web/routing.py:193-212` — `_claim_report` builds the request, calls `build_claim_view`, returns the report unconditionally. Only catches `_EXPECTED_WEB_ERRORS`; does not consult `report.status.visible_under_policy`.
- `propstore/app/claim_views.py:168-195` — `build_claim_view`:
  - line 176: computes `visible_ids` from `world.claims_with_policy(None, policy)`.
  - line 177: derives `status` (a flag).
  - lines 179-195: returns a `ClaimViewReport` with `statement`, `value`, `uncertainty`, `condition`, `provenance` populated UNCONDITIONALLY. The flag is not consulted.
- `propstore/web/html.py:79-104` — `render_claim_page` reads `report.heading`, `report.statement`, `report.value.sentence`, `report.provenance.paper`, `report.provenance.page`, `report.provenance.source_id` directly into HTML. JSON path at `routing.py:147-149` calls `to_json_compatible(report)` which serializes the same fields.

**Therefore**: a `GET /claim/<blocked-id>.json` returns the full claim payload today; the render-policy "blocked" status is a label on a fully-disclosed object. **D-21 fix**: refuse to construct the report at all. Raise `ClaimViewBlockedError` from `build_claim_view` before populating any field; the route maps the exception to a 403 or 404 response with no claim-derived payload.

### Neighborhood leak (Codex #9 / T1.2)

- `propstore/app/neighborhoods.py:135-140` — `stances = [stance for stance in world.all_claim_stances() if str(stance.claim_id) == focus_id or str(stance.target_claim_id) == focus_id]`. **No filter on policy visibility of either endpoint.**
- `propstore/app/neighborhoods.py:141-153` — `supporters` and `attackers` are tuples of `stance.claim_id` derived from the unfiltered list. These IDs are claim IDs of potentially-hidden claims.
- `propstore/app/neighborhoods.py:200-214` — `SemanticMove(kind="supporters", target_ids=supporters)` and `SemanticMove(kind="attackers", target_ids=attackers)` ship the IDs out.
- `propstore/app/neighborhoods.py:265-288` — `_nodes` resolves each ID to a `display_id` and emits a `SemanticNode`. Hidden claims are now full nodes in the response.
- `propstore/app/neighborhoods.py:291-316` — `_edges` ships every stance as a `SemanticEdge` with source/target claim IDs.
- `propstore/world/model.py:887-912` — `all_claim_stances()` is an unconditional SELECT over `relation_edge` filtered only by `source_kind='claim' AND target_kind='claim'`. There is no render-policy join. The policy-aware variant required to fix this does not exist yet.

The hard-error principle from D-21 applies: **don't show what shouldn't be shown**. In neighborhoods that means hidden claims simply do not appear (they are not endpoints, not nodes, not edges, not in counts). The neighborhood request itself is a normal 200 response — it just does not surface anything the policy bars.

### Concept leak (Codex #10 / T1.3)

- `propstore/app/concept_views.py:162-163` — `visible_claims` and `all_claims` are computed independently; the difference IS the disclosure surface.
- `propstore/app/concept_views.py:242-272` — `_concept_status` returns `ConceptViewStatus(visible_claim_count=..., blocked_claim_count=total - visible, total_claim_count=...)`. These three integers are the exact thing Codex #10 says must not appear without an explicit include flag.
- `propstore/app/concept_views.py:275-309` — `_claim_groups` builds a per-claim-type `(visible_count, blocked_count)` distribution and a sentence "X visible Y claims and Z blocked claims refer to this concept." The blocked count is in the prose, in the JSON, and in the structure.

Same hard-error principle: hidden claims must not contribute to counts, prose, or per-type distributions under default policy. The concept page is a normal 200 — but it acts as if blocked claims do not exist.

### FTS escape (Codex #11)

- `propstore/web/routing.py:376-409` — `_concepts_report` calls `search_concepts` inside a `try ... except _EXPECTED_WEB_ERRORS`.
- `propstore/web/routing.py:61-70` — `_EXPECTED_WEB_ERRORS` does NOT include `sqlite3.OperationalError`, `sqlite3.DatabaseError`, or any FTS-grammar error.
- `propstore/app/concepts/display.py:40-50` — `search_concepts` passes `request.query` straight to `concept_fts MATCH ?`. SQLite raises `OperationalError: fts5: syntax error near ...` for malformed input; this propagates past `_concepts_report` and reaches the framework as a 500.

**Therefore**: `GET /concepts.json?q=%22unterminated` returns 500 with raw `sqlite3.OperationalError` text in the framework's default error rendering.

### Read-only sidecar mutates (Codex #4 / T1.5)

- `propstore/sidecar/query.py:21-30` — `query_sidecar` calls `connect_sidecar(sidecar)` (line 26) **before** `conn.execute("PRAGMA query_only=ON")` (line 28).
- `propstore/sidecar/sqlite.py:9-23` — `connect_sidecar` opens read/write (`sqlite3.connect(path)`) and `configure_sidecar_connection` runs `PRAGMA journal_mode = WAL` at line 22. WAL is a state change recorded in the file header; on a previously-non-WAL DB this writes. It also creates `.db-wal` and `.db-shm` siblings.

**Therefore**: a code path advertised as "read-only sidecar query" mutates the file and creates sidecar files. On a read-only filesystem, the connection setup throws before `query_only` is ever applied, so the failure mode is not "fail clean" but "fail because we tried to write."

### Float boundary (T1.8)

- `propstore/web/requests.py:58-69` — `_float_param` does `float(value)` and returns. `float("nan")`, `float("inf")`, `float("-inf")` all succeed silently. There is no `math.isfinite` check, no range check on `pessimism_index` (must be in [0,1]), `praf_epsilon` (must be > 0), or `praf_confidence` (must be in (0,1)).

**Therefore**: `?pessimism_index=NaN` reaches `AppRenderPolicyRequest` and propagates into render-policy construction. Whether it crashes or silently misbehaves is downstream from the boundary; the fix lives at the boundary.

### `pks web` host check (T1.9)

- `tests/test_cli_web.py:33-54` — current behaviour: `--host 0.0.0.0` succeeds with no warning, no `--insecure` flag, no auth posture. The test asserts the message `"Open http://127.0.0.1:8765"` is printed regardless of host.

**Therefore**: `pks web --host 0.0.0.0` exposes the propstore knowledge browser to the LAN with no auth and no acknowledgement.

## First failing tests (write these first; they MUST fail before any production change)

1. **`tests/test_render_policy_direct_claim.py`** (new) — D-21 hard-error contract
   - Build a sidecar with a visible claim `V` and a blocked claim `B` carrying a unique marker text.
   - **Anonymous request, `GET /claim/B.json`**: assert response status is **404** and the response body contains no marker text, no `claim_id` echo of `B`, no `statement`, no `value`, no `provenance` field. Assert the body matches the standard `_ERROR_RESPONSES` shape.
   - **Anonymous request, `GET /claim/B`** (HTML): assert status is **404**. Assert the rendered HTML contains a useful `<title>` (e.g., "Not Found · propstore"), a useful `<h1>` heading, and a useful next-action link (e.g., back to the claim index). Assert the unique marker text from `B` does NOT appear anywhere in the body. Assert no element with class/id implying a redacted-claim region is present (we are not rendering a redacted page; we are rendering an error page).
   - **Identified-user request, `GET /claim/B.json`** (when the identity layer lands; for now skip-marked with rationale): assert status is **403** and that the body still contains no marker text.
   - **A11y assertions on the error page only** (per D-21 — NOT on redacted claim content):
     - `<title>` is non-empty and informative.
     - There is exactly one `<h1>`.
     - There is at least one in-page link to a known navigable destination (index, search).
     - The `<main>` landmark is present and `aria-labelledby` (or equivalent) ties to the heading.
     - The page passes `axe-core` (or equivalent) with zero serious violations.
   - **Visible claim still works**: `GET /claim/V.json` returns 200 with the populated report. (Sanity test that the gate is targeted, not a global block.)
   - **Must fail today**: `build_claim_view` populates the report unconditionally; the route returns 200 with the marker text.

2. **`tests/test_render_policy_neighborhood.py`** (new)
   - Same fixture plus a stance `B supports V`.
   - `GET /claim/V/neighborhood.json` default policy: assert response is 200; assert `B`'s claim_id is absent from `moves[*].target_ids`, `nodes[*].node_id`, `edges[*].source_id`, `edges[*].target_id`, and `table_rows[*]`. Assert prose count says `0 supporters`, not `1 supporter`.
   - `GET /claim/B/neighborhood.json` (focus claim is itself blocked): assert response is **404** with no body content derived from `B`. (The hard-error principle: a focus claim that the policy bars cannot anchor a neighborhood, because the response would necessarily disclose `B`'s identity.)
   - **Must fail today**: `world.all_claim_stances()` is unfiltered; `supporters`/`attackers` carry the IDs out at `neighborhoods.py:200-214`.

3. **`tests/test_render_policy_concept.py`** (new)
   - Concept C with claims `V` (visible) and `B` (blocked), both referencing C.
   - `GET /concept/C.json` default policy: assert response is 200; assert `status.total_claim_count == 1`, `status.blocked_claim_count == 0` (or omit those fields entirely — pin the design choice). Assert the per-group `blocked_count == 0`. Assert no string in the JSON or HTML mentions blocked counts.
   - **Must fail today**: `_concept_status` always returns `total = visible + blocked` and per-type `blocked_count` is always populated.

4. **`tests/test_concept_fts_malformed_query.py`** (new)
   - Build a sidecar with `concept_fts` populated.
   - `GET /concepts.json?q=%22unterminated` (or other FTS5 grammar violations).
   - Assert: response is 400 with a stable JSON body matching `_ERROR_RESPONSES` shape, NOT 500 and NOT raw `sqlite3.OperationalError` text.
   - Property test variant via Hypothesis: any string drawn from a "malformed FTS" strategy returns 400, not 500. (Per memory: prefer Hypothesis property tests over example tests.)
   - **Must fail today**: `_EXPECTED_WEB_ERRORS` doesn't include sqlite errors.

5. **`tests/test_sidecar_query_read_only.py`** (new)
   - Copy a sidecar to a temp dir; record its byte size, mtime, and assert no `-wal`/`-shm` siblings.
   - Call `query_sidecar(repo, "SELECT 1")`.
   - Assert: byte size unchanged, mtime unchanged, no `-wal`/`-shm` siblings created.
   - Second variant: chmod the temp dir read-only on POSIX (skip on Windows). Assert `query_sidecar` succeeds (it should — it's read-only) instead of failing with a write-access error.
   - **Must fail today**: `connect_sidecar` runs `PRAGMA journal_mode = WAL` before `query_only`.

6. **`tests/test_web_request_float_boundary.py`** (new)
   - Hypothesis property: for every `float_param_name` in {`pessimism_index`, `praf_epsilon`, `praf_confidence`}, `_float_param` rejects `nan`, `inf`, `-inf` with `WebQueryParseError`.
   - Hypothesis property: for `pessimism_index`, values outside [0, 1] raise `WebQueryParseError`. Likewise `praf_epsilon > 0` and `praf_confidence` in `(0, 1)`.
   - **Must fail today**: `float(value)` accepts `"nan"`, `"inf"`, `"1e9"`.

7. **`tests/test_pks_web_insecure_flag.py`** (new)
   - `pks web --host 0.0.0.0` without `--insecure`: assert `exit_code != 0` and stderr contains a security warning naming the public-bind risk.
   - `pks web --host 0.0.0.0 --insecure`: assert `exit_code == 0` and stderr STILL contains a clearly-labelled banner ("WARNING: serving propstore with no auth on 0.0.0.0").
   - `pks web --host 127.0.0.1`: works without `--insecure` (default behaviour preserved).
   - **Must fail today**: current test at `tests/test_cli_web.py:33-54` accepts `--host 0.0.0.0` silently.

8. **`tests/test_workstream_b_done.py`** (new — gating sentinel)
   - `xfail` until WS-B closes; flips to `pass` on the final commit. Mirror of WS-A's gating-sentinel mechanism.

## Production change sequence

Each step lands as its own commit with a message of the form `WS-B step N — <slug>`.

### Step 1 — Delete any redacted-rendering helpers (D-21 cleanup precondition)

Before adding the hard-error path, remove any code that exists or was sketched to render a "redacted but otherwise structured" claim page. Concretely, audit and delete:

- Any helper in `propstore/web/html.py` that generates a "redacted under render policy" region with `aria-labelledby` plumbing for blocked claims (search for `redacted`, `render_policy`, `visible_under_policy` in HTML templates and helpers).
- Any branch in `propstore/app/claim_views.py` that constructs a `ClaimViewReport` with statement/value/provenance set to redaction sentinels.
- Any test fixture or assertion that expects a redacted claim page response (HTML body containing redaction markers, JSON with explicit `redaction:"render_policy"` fields).

Per `feedback_no_fallbacks.md` and `feedback_update_callers.md`: do not leave the redacted-render helpers behind a flag or as dead code. They are deleted in this step. If a caller exists, update it to expect the hard-error path.

Acceptance: Grep for `redacted`/`redaction` in `propstore/web/` and `propstore/app/claim_views.py` returns no production matches. Any tests that asserted redacted-page structure either fail (they will be replaced in Step 2) or are deleted as part of this commit.

### Step 2 — Hard-error path for blocked claim reads (D-21)

`propstore/app/claim_views.py:168-195`: short-circuit before populating the report. If `str(claim.claim_id) not in visible_ids` and the policy doesn't include the relevant `include_*` flag, raise a new `ClaimViewBlockedError(claim_id)` (parallel to `ClaimViewUnknownClaimError`). The exception carries no claim-derived data beyond an opaque identifier the route uses for logging — it does NOT carry `statement`, `value`, or `provenance`.

`propstore/web/routing.py`:
- Add `ClaimViewBlockedError` to `_EXPECTED_WEB_ERRORS`.
- Add a mapping in `_ERROR_RESPONSES` keyed by `ClaimViewBlockedError`. The mapping selects the status code based on request identity:
  - Anonymous request → **404** with the standard "Not Found" body.
  - Identified user → **403** with the standard "Forbidden" body. (When the identity layer is not yet in place, default to **404** so the privacy-preserving option is the default.)
- The error response uses the standard error template (next step) — not a redacted-claim template.

`propstore/web/html.py`: add or reuse a generic error-page template that renders:
- Useful `<title>` (e.g., `"404 · propstore"` or `"403 · propstore"`).
- Single `<h1>` with a plain-language heading ("Not Found", "Forbidden").
- A short, honest message in plain language. The 404 message MUST NOT confirm or deny the existence of any specific claim — it is the standard "Not Found" message. The 403 message names the policy state in generic terms.
- A useful next-action: a link back to the claim index, plus a search affordance.
- `<main>` landmark with `aria-labelledby` tying to the heading; `lang="en"` on `<html>`; skip-link if the existing layout uses one.

Per `a11y:cognitive-a11y` and `a11y:accessible-content-writing`: the message is plain language, the next action is concrete, the user does not have to infer cause from absence.

`render_claim_page` and `to_json_compatible` paths are unchanged for visible claims. They are never reached for blocked claims because the exception fires before report construction.

Acceptance: `tests/test_render_policy_direct_claim.py` turns green — the response codes match D-21, the marker text is absent everywhere, and the error page passes its a11y assertions.

### Step 3 — Filter neighborhood relations at the world layer

Add `propstore/world/model.py:claims_stances_with_policy(focus_claim_id, policy) -> list[StanceRow]`. SQL joins `relation_edge` against the same visibility predicate `_visibility_predicates` already implements (per WS-A `model.py:722-736`). Both endpoints must be visible.

Migrate `propstore/app/neighborhoods.py:137` from `world.all_claim_stances()` to the new policy-aware method. Per memory `feedback_update_callers.md` and `feedback_no_fallbacks.md`: do not keep `all_claim_stances()` as a "raw" alternative for the unfiltered case. The raw method has no app-layer caller after this change; if it remains it is a footgun for the next refactor.

Additionally, when the **focus** claim itself is blocked under the active policy, the neighborhood route raises `ClaimViewBlockedError` (same hard-error principle as Step 2) and returns 404/403. The neighborhood for a blocked focus would necessarily disclose `B`'s ID by virtue of being addressable.

Acceptance: `tests/test_render_policy_neighborhood.py` turns green.

### Step 4 — Concept reports become policy-relative

`propstore/app/concept_views.py:242-272`: change `ConceptViewStatus` so the default-policy report has `total_claim_count == visible_claim_count` and omits `blocked_claim_count` (or sets it to `None` with serialization eliding `None`). Only when `policy.include_blocked` (or equivalent administrative flag) is true does the field surface.

`_claim_groups` at `:275-309`: under default policy, `blocked_count == 0` and the prose says "X visible <type> claims refer to this concept" — never mentioning blocked counts. Under the administrative flag, the existing behaviour is preserved.

Acceptance: `tests/test_render_policy_concept.py` turns green.

### Step 5 — Typed FTS error

`propstore/app/concepts/display.py`: wrap the `concept_fts MATCH` execution in a try block; catch `sqlite3.OperationalError` whose message indicates an FTS5 grammar problem; raise `ConceptSearchSyntaxError(query, message)` (new exception type). Add to `_EXPECTED_WEB_ERRORS` and to `_ERROR_RESPONSES` -> `("Invalid Search Query", 400)`.

Do not over-broaden — catch only FTS grammar errors, not arbitrary sqlite errors. A bare `except sqlite3.OperationalError` swallows database corruption signals and is the same anti-pattern as the `build_repository` swallow-and-succeed bug Claude N flagged.

Acceptance: `tests/test_concept_fts_malformed_query.py` turns green.

### Step 6 — Split read-only and read-write sidecar paths

`propstore/sidecar/sqlite.py`: introduce `connect_sidecar_readonly(path)` that opens via SQLite URI mode `file:{path}?mode=ro` and runs `PRAGMA query_only=ON` immediately, never executing `journal_mode = WAL`. Keep `connect_sidecar` (read-write) for build/publish paths.

`propstore/sidecar/query.py:21-30`: switch to `connect_sidecar_readonly`. Remove the now-redundant `query_only` from `query_sidecar` (the helper sets it).

Audit other read-only call sites — every place that wraps `connect_sidecar` with `query_only` is suspect. Move them to the read-only helper. Per `feedback_no_fallbacks.md`: do not leave `connect_sidecar` as the read-only path with a flag; the helpers are distinct.

Acceptance: `tests/test_sidecar_query_read_only.py` turns green; no caller in `propstore/` uses `connect_sidecar` for a query-only workload.

### Step 7 — Float boundary validation

`propstore/web/requests.py:58-69`: extend `_float_param` to take optional `lo`, `hi` bounds (open or closed), check `math.isfinite`, raise `WebQueryParseError` with a per-parameter message. Update each call site at `:22-25` to pass the spec'd bounds. The numeric domain of each parameter is documented in `propstore/app/rendering.py` (or `core/policy.py`) — read it; do not invent bounds.

Acceptance: `tests/test_web_request_float_boundary.py` turns green.

### Step 8 — `pks web --insecure` gate

`propstore/cli/web.py`: add `--insecure` boolean flag. If host is not in `{"127.0.0.1", "::1", "localhost"}` and `--insecure` is not set, print a security warning and exit non-zero. If `--insecure` is set, print a clearly-labelled banner before starting the server.

Update `tests/test_cli_web.py:33-54` to assert the new contract (or write the new test in `tests/test_pks_web_insecure_flag.py` and delete the bare-host-passes assertion at `:50`).

Acceptance: `tests/test_pks_web_insecure_flag.py` turns green.

### Step 9 — Close gaps and gate

- Update `docs/gaps.md`: remove the render-policy / sidecar-readonly / FTS-grammar / float-boundary / public-bind entries; add `# WS-B closed <sha>` line in the Closed Gaps section.
- Flip `tests/test_workstream_b_done.py` from `xfail` to `pass`.
- Update this file's STATUS line to `CLOSED <sha>`.

## Acceptance gates

Before declaring WS-B done, ALL must hold:

- [ ] `uv run pyright propstore` — passes with 0 errors.
- [ ] `uv run lint-imports` — passes (no new contract violations introduced; the world-layer policy-aware method respects the existing app-cannot-bypass-world layering).
- [ ] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-B tests/test_render_policy_direct_claim.py tests/test_render_policy_neighborhood.py tests/test_render_policy_concept.py tests/test_concept_fts_malformed_query.py tests/test_sidecar_query_read_only.py tests/test_web_request_float_boundary.py tests/test_pks_web_insecure_flag.py tests/test_workstream_b_done.py` — all green.
- [ ] Full suite `powershell -File scripts/run_logged_pytest.ps1` — no NEW failures vs the post-WS-A baseline.
- [ ] `propstore/world/model.py:all_claim_stances` has no app-layer caller (audit by Grep).
- [ ] `propstore/sidecar/query.py` calls `connect_sidecar_readonly` and never `connect_sidecar`.
- [ ] `_EXPECTED_WEB_ERRORS` includes `ClaimViewBlockedError` and `ConceptSearchSyntaxError`.
- [ ] Grep for `redacted`/`redaction` in `propstore/web/` and `propstore/app/claim_views.py` returns no production matches related to render policy.
- [ ] `docs/gaps.md` has no open rows for the findings listed above.
- [ ] `reviews/2026-04-26-claude/workstreams/WS-B-render-policy.md` STATUS line is `CLOSED <sha>`.

## Done means done

This workstream is done when **every finding in the table at the top is closed**, not when "most" are closed. Specifically:

- T1.1, T1.2, T1.3, T1.5, T1.8, T1.9, Codex #4, Codex #8, Codex #9, Codex #10, Codex #11 — all eleven have a corresponding green test in CI.
- The error-page template is screen-reader friendly: useful title, useful heading, useful message, useful next-action, verified by `tests/test_render_policy_direct_claim.py`'s a11y assertions.
- No redacted-claim rendering helpers exist in the codebase.
- `gaps.md` is updated.
- The workstream's gating sentinel test (`tests/test_workstream_b_done.py`) has flipped from xfail to pass.

If any one of those is not true, WS-B stays OPEN. No "we'll get to the FTS grammar later." Either it's in scope and closed, or it's explicitly removed from this WS in this file (and moved to a successor WS) before declaring done.

## Cross-stream notes

- WS-B depends on WS-A. Render-policy filters reference `claim_core.stage`, `build_status`, `promotion_status`. Until WS-A's `_REQUIRED_SCHEMA` validates those at sidecar-open time, the policy-aware tests can pass against a fixture that doesn't exercise them.
- WS-B does NOT depend on WS-C (sidecar atomicity) or WS-D (math naming). It can run in parallel with the math-correctness workstreams once WS-A merges.
- WS-B's Step 6 (read-only sidecar split) is adjacent to WS-C (sidecar atomicity / promote ordering). If both touch `propstore/sidecar/sqlite.py`, sequence: WS-B Step 6 first (introduces the helper), WS-C uses it.
- The `ClaimViewBlockedError` -> 404/403 selection (anonymous vs identified) should be documented in `docs/render-policy.md` (create if missing) so future routes inherit the convention. Anonymous defaults to 404 per D-21's privacy-preserving default.

## What this WS does NOT do

- Does NOT render redacted claim pages. D-21 forbids it; redacted-rendering helpers are deleted in Step 1.
- Does NOT introduce new include-flag semantics. The existing `include_drafts`, `include_blocked`, `show_quarantined` (per `propstore/web/requests.py:27-29`) are honoured; this WS just makes the default path actually enforce them.
- Does NOT add authentication. The 403 vs 404 selection is keyed off whatever identity signal the request carries; until that signal exists, the default is 404. `--insecure` is a guardrail, not auth; auth is a separate workstream if/when it lands.
- Does NOT change the render-policy semantics themselves (visible/blocked rules). That's `propstore/world/model.py:_visibility_predicates` and out of scope.
- Does NOT add CSP, security headers, or general web hardening — those are separable, lower-priority items.
- Does NOT touch the architecture / import-linter contracts — that's WS-N.

## Papers / specs referenced

None. WS-B is software-engineering hygiene around a privacy boundary. No paper implements "do not leak hidden claims through your JSON endpoints" — it's a property of the system, gated by tests, not corroborated against a citation.
