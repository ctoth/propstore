# Harsh zen review — rewrite plan: Phases 8, 9, 10 + GLOBAL

> NOTE: intended path was `reports/rewrite-zen-E.md`; a foreman Write hook blocked that
> directory (allows only prompts/ and notes-*.md). Full report parked here for the team lead
> to relocate.

Reviewer: adversarial design review (slice E). Read-only. No code/repo edits.
Sources: `REWRITE_PLAN.md` (plan), `decomposition/SPEC.md` (SPEC), `inventory/FEATURE_INVENTORY.md` (INV),
per-area decomp docs, `CLAUDE.md` (zen). Citations: `plan:§/line`, `INV:line`, `SPEC:line`, decomp-doc:line.

Verdict scale: PASS / PASS-WITH-CONCERNS / AT-RISK / FAIL.

---

## Phase 8 — source + proposals + provenance + micropubs

**Verdict: PASS-WITH-CONCERNS**

**Principles at risk: Z3 (coercer seam), Z1 (promote winner-pick), Z4 (storage→argumentation upward dep).**

### 8.1 — Promotion "concept resolution" is not pinned to quarantine-never-pick (Z1)
- Concern: `plan:§8/137` and `INV:374` describe promotion as "per-item blocking filter, **concept resolution**,
  immutable rebuild, atomic master commit". "Concept resolution" is unspecified. The zen-correct behavior is
  encoded only implicitly in two remediation tests (`INV:70`: "Source-promote quarantines claim on
  ambiguous/unresolved concept", T2_2r/2s). Nothing in the PLAN states the invariant **"lower unambiguous
  handles, quarantine ambiguous ones, never auto-pick a winner."** A coder rebuilding promotion blind can
  implement auto-resolution of an ambiguous concept ref = picking a winner at the one commit gate. That is
  "collapse disagreement in storage" (`CLAUDE.md` Core Design Principle).
- Fix: PLAN states the promotion invariant explicitly — ambiguous/unresolved reference → quarantine row with
  diagnostic, never heuristic auto-selection. Promote T2_2r/2s to a named Phase-8 discipline gate.

### 8.2 — provenance-semiring extraction ships an adapter escape hatch (Z3)
- Concern: the EXTRACT seam is left as a **fork**, not a decision. decomp source-doc:88-95 + `SPEC:30` describe
  `projections.py → propstore.core.id_types` and `variables.py/nogoods.py → propstore.provenance.Provenance`
  (circular), and offer resolution as generic variable-kind parameterization **OR "a thin propstore adapter
  over a generic why_provenance"** (decomp:90,102). The second is a coercer/mirror across the boundary. The
  PLAN asserts provenance-semiring is already **SHIPPED+pinned** (`plan:§4/41`, `§5/47`, rev 13380ece) yet its
  own decomposition still lists the seams as open. If it shipped with the adapter / a baked-in `Provenance`
  field, the extraction failed Z3 AND **atms (Phase 7) already consumes the broken boundary** (atms labels carry
  these polynomials — decomp:98, `SPEC:30`).
- Fix: verify the shipped package exposes `why_provenance`/`SourceVariable` parameterized by a generic
  variable-kind tag, NO `propstore` import, NO `Provenance` field in the math core. If not, re-cut before Phase 7
  is trusted. Strike the "thin adapter" option.

### 8.3 — provenance is the carrier, so Opinion must NOT carry a provenance field (Z3) — see GLOBAL #2
- Promote computes trust as opinions with typed provenance (`INV:374,385,202`); correct on Z2 (vacuous when
  uncalibrated, `INV:190,192`) but rides the propstore opinion **fork** (`plan:§5/114`). The project's own
  provenance architecture (named-graph carrier on git notes, "does not contaminate claim identity") argues
  provenance belongs in the carrier, not threaded through every Opinion op. See GLOBAL #2.

### 8.4 — promote-time trust calibration uses argumentation inside storage layer (Z4) — folded into GLOBAL Z4 thread
- `INV:202` "Source-trust calibration via argumentation (rule firings → Dung → grounded → SL opinion)" "runs at
  promote". Storage-layer promotion invoking the argumentation kernel = upward layer reference.

### 8.5 — micropublications immutable: PASS
- `INV:392-394`: content-addressed (ni-URI, payload excludes id fields, sha256 version_id); first-writer dedupe
  is idempotent on content identity (not winner-pick).

---

## Phase 9 — storage-build-compile

**Verdict: AT-RISK** (contains the plan's worst zen exposure)

**Principles at risk: Z1 (build-time filtering — quarantine vs drop), Z4 (build imports argumentation/world),
Z3 (duplicate contract emission), no-test gate machinery.**

### 9.1 — quarantine-vs-drop specified BOTH ways; invariant never stated (Z1) — WORST FINDING
- Two contradictory spellings of the same gate:
  - `INV:431` "quarantine writer (try_write/quarantine; **build-not-render discipline**)" — rows go INTO sidecar.
  - `INV:133` "Claim quarantine pipeline (**invalid never reaches sidecar**)"; `INV:69` "Build quarantines invalid
    form/concept/schema (not raises)".
- `plan:§8/145-149` never states which is law. Implementing "invalid never reaches sidecar" for **semantically
  disputed but well-formed** data violates Z1: 4-Q (a) prevents data reaching sidecar = YES, (d) filter at build
  not render = YES.
- Undrawn line: structurally malformed (unparseable CEL — reject at ingest, `INV:116`) is not a rival and may be
  refused; semantically invalid/conflicting/disputed is a rival and MUST project a queryable quarantined row.
- Fix: PLAN mandates verbatim — "every structurally-parseable artifact projects a row (active|quarantined-with-
  diagnostic); nothing semantic is dropped; active/blocked is a RENDER predicate, not a missing row." Add a
  class-B discipline gate (CI day 0) asserting a semantically-invalid claim still yields a queryable quarantined
  row reachable via `--show-quarantined`. The import-linter gates do NOT guard this today.

### 9.2 — build pipeline imports argumentation + world (Z4 inversion + latent Z1)
- `INV:416`: build substrate = "quire derived_store; **argumentation; world**", computes "conflict/phi summary"
  at build. Storage (1) importing argumentation (4) + world (5) inverts the one-way dependency (`CLAUDE.md`
  Architectural Layers). Computing a phi/conflict summary at build is render-time work pulled to build time.
- Fix: build records detected conflicts as provenance-tagged rows only; phi/coreference adjudication + any
  resolution stays render-side. Storage must not import the argumentation kernel.

### 9.3 — contract manifest risks re-emitting charter-owned bodies (Z3)
- `plan:§8/148` "contract manifest/versioning" unscoped. decomp storage-doc:34 + `INV:425`: doc/family/FK
  contract bodies DUPLICATE quire charters and must be DROPPED; only pass/stage/identity entries are propstore.
- Fix: PLAN states contract manifest emits ONLY semantic_pass/semantic_stage/identity; charter-owned bodies are
  consumed from quire, never re-emitted.

### 9.4 — semantic-pass framework: gate machinery rebuilt blind (no-test) — see GLOBAL #3
- `INV:423` "**NO dedicated test**"; `plan:§8/145` "WRITE framework test". The AUTHORED→CHECKED gate is exactly
  where build-time filtering lives, rebuilt with a self-authored test and no reference pin for quarantine-not-drop.

### 9.5 — charter-derived registry: PASS (genuinely zen-positive)
- decomp KEY FINDING + `INV:427-429`: quire charter classes drive doc/codec/schema/projection/FK/lifecycle from
  ONE source; DTO/coercer mass VANISHES. Strongest Z3 win. Identity algorithms stay propstore as functions fed
  INTO charter metadata — no mirror.

### 9.6 — CLI build owns nothing: PASS
- `INV:416,460` (C2) + decomp render-doc:39; arch gates `test_app_layer_no_cli_payloads`/`test_no_cli_flags_in_owner_errors`.

---

## Phase 10 — render + cli + web + heuristic-embeddings

**Verdict: PASS-WITH-CONCERNS**

**Principles at risk: Z1 (sequencing on Phase-9 quarantine-row), Z3 (doxa fork — global), Z4 (heuristic split across phases).**

### 10.1 — `--show-quarantined` depends on an un-validated Phase-9 assumption (Z1 + sequencing)
- `INV:447,499` R1 carries `--show-quarantined`; `INV:448` claim view STATE includes blocked/quarantined. Correct
  end state, but it is load-bearing proof Phase 9 took the "quarantine-row" branch (9.1). If Phase 9 ships "never
  reaches sidecar", `--show-quarantined` has nothing to show and non-commitment breaks 3 phases earlier.
- Fix: make 9.1's "quarantine projects a queryable row" a HARD Phase-9 exit gate, tested by a Phase-10 render
  test (`--show-quarantined` surfaces a known semantically-invalid claim).

### 10.2 — calibration split is clean: PASS (Z3)
- `INV:485-487` + decomp render-doc:55-66: pure metrics (stdlib, ZERO propstore deps) → EXTRACT `calibration`;
  CorpusCalibrator/categorical→opinion stay propstore over doxa. `plan:§8/157` scoped correctly. File MUST be
  split (not imported with propstore types) — keep decomp's warning in the brief.

### 10.3 — LLM stance classify: PASS (Z2 + Z5)
- `INV:479-480` H1/H2: failure/missing-confidence/strength/base-rate → ABSTAIN + vacuous Opinion + provenance op.
  `INV:205` stance authoring emits PROPOSAL files (never source mutation). Contingent only on the opinion type (#2).

### 10.4 — heuristic-embeddings is layer-3 work bundled into the final presentation phase (Z4, minor)
- Embeddings split across Phase 2 (`plan:§8/92`) and Phase 10, co-located with render(5)+cli/web(6). Keep the
  embeddings adapter importable without render/cli/web; verify via `test_heuristic_package_layout` (`INV:489`).

### 10.5 — CLI full tree presentation-only: PASS (Z6)
- decomp render-doc:39-40 + `INV:459-460` C1/C2.

---

## GLOBAL — top 3 zen risks, ranked

### GLOBAL #1 — The build pipeline can re-introduce the build-time gate the rewrite exists to delete (Z1) — Phase 9
- Inventory specifies build quarantine BOTH ways (`INV:133` vs `INV:431`); PLAN (`plan:§8/145-149`) never states
  which is law nor separates structural-reject from semantic-quarantine. Compounded by `INV:416` (build imports
  argumentation/world, computes conflict/phi at build = Z4 inversion + render work at build) and `INV:423` (gate
  machinery rebuilt with no reference test). Riskiest phase: non-commitment lives or dies here.
- Fix: (1) mandate "structurally-parseable → always a queryable row (active|quarantined-with-provenance)";
  (2) class-B discipline gate enforcing it, CI day 0; (3) build records conflicts as data only — no argumentation
  import, no phi adjudication at build.

### GLOBAL #2 — The doxa/opinion FORK is rebuilt instead of consumed (Z3 + Z7) — Phases 5, 8, 10
- `propstore/opinion.py` = 768-line provenance-threaded FORK of doxa (decomp render-doc:80-89; 13 importers,
  `SPEC:13`). Plan's resolution (`SPEC:13-14`, `plan:§5/114`) leaves a "thin opinion **shim** adding provenance"
  option open = mirror type (`propstore.Opinion` ≠ `doxa.Opinion`) with a provenance field on every op = coercion
  per op = Z3 fail + literal Z7 shim, on the type carrying EVERY probability value (Z2). Contradicts the project's
  own architecture: provenance is a separate named-graph carrier that "does not contaminate identity"
  (`CLAUDE.md` Honest-ignorance) — so threading it through Opinion is doubly wrong.
- Fix: consume `doxa.Opinion` as the ONE type; carry provenance in the named-graph carrier keyed by value
  identity, not as an Opinion field. Keep enforce_coh/metadata_strength as functions OVER doxa opinions. If a
  per-value tag is truly needed in the algebra, parameterize doxa upstream with generic metadata. Strike "shim".

### GLOBAL #3 — Non-commitment-core capabilities rebuilt with no reference gate (cross-cutting) — Phases 7, 9, 10
- `plan:§7/68-70` + `§11/179` rebuild ~13 no-test capabilities "write tests first." Dangerous subset touches the
  non-commitment core: **semantic-pass framework** (`INV:423`), **CompilationContext** (`INV:419`),
  **recency/sample_size resolution** (`INV:225`), **world check-consistency** (`INV:234`). For gate machinery a
  self-authored test can encode the WRONG invariant (drop) and pass — no reference test pins quarantine-not-drop.
  The advertised safety net (class-B import-linter gates, `plan:§7/62`) checks boundaries, NOT data-flow
  non-commitment. Also the "DROP = DTO-shape" rule (`plan:§2/25`) risks discarding a roundtrip/projection test
  that secretly guards non-commitment (blocked-row projection `INV:375`; sidecar projection contract `INV:430`
  are among the only guards rivals reach the sidecar, yet projection tests are marked DROP/VANISH `INV:90,430`).
- Fix: before rebuilding any non-commitment-core capability, PORT (not author) a reference behavioral test pinning
  the data-flow invariant; add the GLOBAL #1 discipline gate; re-audit every DROP test whose name contains
  roundtrip/projection/blocked/quarantine before discarding it.

### Worst finding
**Phase 9 / GLOBAL #1 — quarantine-vs-drop ambiguity in the build pipeline.** Inventory carries both invariants
(`INV:133` vs `INV:431`); PLAN (`plan:§8/144-151`) never states which is law nor separates structural-reject from
semantic-quarantine; the deciding gate machinery is rebuilt with no reference test (`INV:423`). Single place the
rewrite can silently re-grow the forbidden build-time gate.

### Other global notes (not top-3)
- **Cutover safe + reversible (PASS):** `plan:§9/161-165` tags old master `archive/broken-master-<sha>`, preserves
  feature-peak (3702 green). All in git; no irreversible step.
- **Plan cites a non-existent input:** `plan:§3/36` references `decomposition/DESIGN-projection-registry.md` which
  does not exist in the scratchpad; the projection-registry design is load-bearing for Phase 9 and unreviewable.
- **`schema/` (LinkML) marked for blind deletion** (`plan:§6/56`, `§11/174`) "confirm before deleting" — confirm
  against charter coverage first; if it encodes invariants charters don't, deletion loses them.
