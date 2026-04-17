# Axis 2 — Layer Discipline

## Summary

Layer discipline does not hold. The declared six-layer, one-way dependency graph is
violated in several structural ways — most notably, layer 1 (`propstore/source/`)
runtime-imports `propstore.cli.repository.Repository` (layer 6 CLI), layer 1
(`propstore/repo/`) depends on layer-4 `propstore.dung` for merge classification,
and `propstore.core.analyzers` (layer 2) imports layer-4 (`dung`, `preference`,
`probabilistic_relations`) and layer-5 (`world.types`) types at module top. The
strict-typed island also has a phantom entry: `pyproject.toml` declares
`propstore/aspic_bridge.py` (singular) strict, but that file does not exist — the
actual code lives in the `propstore/aspic_bridge/` package and is *not* strict-typed.
Two of the eight strict-listed modules fail under strict pyright (`aspic.py` has 3
errors, `core/graph_types.py` has 1). No heuristic-layer module writes to source
branches, and neither `repo/` nor `source/` writes to the sidecar out-of-band.

## Layer dependency graph

Observed inter-layer imports (cluster → clusters it reaches into, with at least one
call-site reference). "Upward" means "toward the top of the declared stack." All
`from propstore.X import …` forms are counted; `if TYPE_CHECKING` lines are noted
parenthetically.

Layer 1 — Storage (`repo/`, `source/`, `artifacts/`, `claims.py`, `stances.py`,
`provenance.py`, `proposals.py`):

- `repo/` → `artifacts/` (layer 1, lateral) — e.g. `repo/git_backend.py:23-24`,
  `repo/merge_commit.py:10-11`.
- `repo/` → `identity.py` (layer 1 utility) — `repo/merge_claims.py:9`.
- `repo/` → `knowledge_path.py` (layer 1 utility) — `repo/structured_merge.py:14`.
- `repo/` → `core/` (layer 2) — `repo/structured_merge.py:10-11` imports
  `core.id_types`, `core.row_types`. **Upward.**
- `repo/` → `dung.py` (layer 4) — `repo/merge_framework.py:9`,
  `repo/paf_merge.py:6`, `repo/paf_queries.py:4`, `repo/structured_merge.py:13`.
  **Upward (layer 1 → layer 4).**
- `repo/` → `z3_conditions.py` (layer 2) — `repo/merge_classifier.py:18`.
  **Upward.**
- `repo/` → `structured_projection.py` (layer 4-ish, `aspic` helpers) —
  `repo/structured_merge.py:18`. **Upward.**
- `repo/` → `claims.py` (layer 1 top-level) — `repo/merge_classifier.py:19`. Lateral.
- `repo/` → `cli.repository` under `TYPE_CHECKING` only — `repo/repo_import.py:18`,
  `repo/snapshot.py:12`.
- `source/` → `artifacts/` (layer 1, lateral) — pervasive.
- `source/` → `repo.merge_framework`, `repo.paf_queries` (layer 1, lateral) —
  `source/alignment.py:18-19`.
- `source/` → `cli.repository` at runtime (not under `TYPE_CHECKING`) —
  `source/alignment.py:16`, `source/claims.py:11`, `source/common.py:20`,
  `source/concepts.py:6`, `source/finalize.py:15`, `source/promote.py:27`,
  `source/registry.py:7`, `source/relations.py:12`. **Upward (layer 1 → layer 6).**
- `source/` → `core/` (layer 2) — `source/claims.py:9`, `source/common.py:21`.
  **Upward (minor).**
- `source/` → `source_calibration.py` (layer 3) — `source/finalize.py:17`.
  **Upward (layer 1 → layer 3).**
- `source/` → `parameterization_groups.py` (layer 2 utility) —
  `source/registry.py:8`. **Upward.**
- `source/` → `stances.py` (layer 1 top-level) — lateral.
- `artifacts/` → `core/labels.py` (layer 2) — `artifacts/codes.py:12`. **Upward.**
- `artifacts/` → `world.*` (layer 5, lazy at call sites) —
  `artifacts/codes.py:241,364,365`. **Upward (layer 1 → layer 5).**
- `artifacts/` → `repo.branch` (layer 1, lateral) — `artifacts/store.py:18`.
- `artifacts/` → `identity.py`, `knowledge_path.py`, `loaded.py`, `uri.py`,
  `stances.py` (layer 1 utilities / top-level). Lateral.
- `artifacts/` → `cel_types.py` (layer 2) — `artifacts/documents/concepts.py:7`,
  `claims.py:8`, `sources.py:16`, `worldlines.py:8`. **Upward.**
- `claims.py` (layer 1 top-level) → `artifacts.*` (layer 1). Lateral, OK.
- `proposals.py` (layer 1 top-level) → `artifacts.*` (layer 1). Lateral, OK.
- `stances.py` (layer 1 top-level) — no propstore imports.

Layer 2 — Semantic (`core/`, `context_*`, `form_utils.py`, `cel_*`,
`z3_conditions.py`, `condition_classifier.py`, `unit_dimensions.py`,
`validate_concepts.py`, `validate_contexts.py`, `compiler/`):

- `core/` → `cel_*` (layer 2, lateral) — pervasive.
- `core/` → `artifacts.*` (layer 1, downward). OK.
- `core/` → `aspic.py` (layer 4) — `core/literal_keys.py:17`. **Upward (and file is
  strict-typed).**
- `core/` → `bipolar.py`, `conflict_detector.*`, `dung.py`, `preference.py`,
  `probabilistic_relations.py` (layer 4) — `core/analyzers.py:8-41`. **Upward.**
- `core/` → `world.types` (layer 5) — `core/analyzers.py:61`,
  `core/environment.py:33` (TYPE_CHECKING). **Upward (analyzers.py is runtime).**
- `core/` → `conflict_detector.models` (layer 4) — `core/row_types.py:10`.
  **Upward.**
- `core/` → `opinion.py` (layer 4) — `core/claim_values.py:10`. **Upward.**
- `core/` → `stances.py` (layer 1) — `core/row_types.py:25`. Downward, OK.
- `compiler/` → `core/` (layer 2, lateral). OK.
- `compiler/` → `artifacts/` (layer 1, downward). OK.
- `compiler/` → `claims.py` (layer 1, downward). OK.
- `compiler/` → `cli.repository` under TYPE_CHECKING (`compiler/context.py:28`).
- `conflict_detector/` → `cel_*`, `condition_classifier` (layer 2, lateral).
- `conflict_detector/` → `claims.py`, `equation_comparison.py`,
  `value_comparison.py` (layer 1 / layer 2 utilities). Downward / lateral.
- `validate_concepts.py`, `validate_contexts.py` — layer 1/2 downward. OK.

Layer 3 — Heuristic (`embed.py`, `classify.py`, `relate.py`,
`relation_analysis.py`, `calibrate.py`, `source_calibration.py`, `sensitivity.py`):

- `embed.py` — no propstore imports. OK.
- `classify.py` → `calibrate.py`, `stances.py`. Lateral/downward. OK.
- `relate.py` → `classify.py`. Lateral. OK.
- `calibrate.py` → `opinion.py` (layer 4). **Upward (layer 3 → layer 4).**
- `sensitivity.py` → `core.id_types`, `core.row_types`, `propagation.py` (layer 2).
  Downward. OK.
- `relation_analysis.py` → `core.relation_types`, `core.row_types` (layer 2),
  `world.types` (layer 5). **Upward (layer 3 → layer 5).**
- `source_calibration.py` → `cli.repository` (layer 6) at top,
  `propstore.world` (layer 5) inside function,
  `source.common` (layer 1), `artifacts.documents.sources`. **Upward to 5 and 6.**

Layer 4 — Argumentation (`dung.py`, `dung_z3.py`, `aspic.py`, `aspic_bridge/`,
`bipolar.py`, `preference.py`, `praf/`, `claim_graph.py`,
`probabilistic_relations.py`, `opinion.py`, `revision/`, `conflict_detector/`):

- `dung.py`, `opinion.py`, `aspic.py`, `bipolar.py` — no propstore imports. OK.
- `dung_z3.py` → `dung.py` (layer 4, lateral). OK.
- `claim_graph.py` → `core.analyzers`, `dung.py`, `world.types` (layer 5).
  **Upward (layer 4 → layer 5).**
- `aspic_bridge/` → `aspic.py`, `core.*`, `grounding.bundle` (layer 5), `dung.py`,
  `preference.py`, `structured_projection.py`, `world.types` (layer 5) —
  e.g. `aspic_bridge/projection.py:17`, `aspic_bridge/build.py:28`.
  **Upward (layer 4 → layer 5) for `world.types` and `grounding.bundle`.**
- `praf/` → `dung.py`, `opinion.py`, `probabilistic_relations.py`, `core.*`
  (downward) — plus `praf/projection.py:11` imports `world.types` (layer 5).
  **Upward.**
- `preference.py` → `core.active_claims`, `opinion.py`, `stances.py`. Downward/lateral.
- `probabilistic_relations.py` → `opinion.py`, `stances.py`. Lateral.
- `revision/` → `core.*`, `cel_types`. Downward. OK.
- `conflict_detector/` — listed in layer 4 by the task, but its imports
  (cel_types, condition_classifier, claims, equation_comparison, value_comparison)
  are all layer 1/2. It behaves as a layer-2/3 utility that layer-4 reaches into.
  See Open questions.

Layer 5 — Render (`world/`, `worldline/`, `grounding/`, `sidecar/`, `fragility*`):

- `world/` → `cel_*`, `core.*`, `form_utils.py`, `knowledge_path.py`,
  `conflict_detector`, `propagation.py`, `z3_conditions.py`. All downward / layer-2.
  OK.
- `world/model.py` → `sidecar.schema` (layer 5, lateral). OK, read-only constants.
- `worldline/` → `core.*`, `revision.*`, `world.*`, `artifacts.*`. Mostly downward
  or lateral within layer 5.
- `grounding/` → `aspic.py` (layer 4), `core.concepts`, `artifacts.documents.*`,
  `rule_files.py`, `predicate_files.py`, `knowledge_path.py`. **Upward to layer 4
  (`aspic`) in bundle.py:45, facts.py:54, grounder.py:55, translator.py:66.**
- `sidecar/` → `compiler/` (layer 2), `artifacts/` (layer 1), `core.concepts`,
  `claims.py`, `form_utils.py`, `identity.py`, `stances.py`,
  `parameterization_groups.py`, `propagation.py`, `aspic.py` (layer 4) in
  `sidecar/rules.py:66`, `grounding.bundle` (layer 5). **Upward to layer 4
  (`aspic`).**
- `fragility*.py` → `cel_types`, `world.types`, `grounding.bundle`,
  `aspic`, `aspic_bridge.*`, `core.row_types`. Lateral within layer 5 and
  **upward to layer 4 (`aspic` and `aspic_bridge`) in
  `fragility.py:9-12`.**

Layer 6 — CLI (`propstore/cli/`):

- Imports widely from all layers — expected for an entry point.
- One notable path: `cli/__init__.py:297` and `cli/compiler_cmds.py:214` both
  invoke `sidecar.build.build_sidecar`. No non-CLI module writes to the sidecar
  at runtime.

## Findings

### Finding 1 — Phantom strict-typed target `aspic_bridge.py`
- Severity: **crit** (the strict contract is silently unenforced)
- Evidence: `pyproject.toml:55` lists `"propstore/aspic_bridge.py"` under
  `[tool.pyright] strict = [...]`, but `ls propstore/aspic_bridge.py` returns
  "No such file or directory". The actual module is the package
  `propstore/aspic_bridge/` (`__init__.py`, `build.py`, `extract.py`,
  `grounding.py`, `projection.py`, `query.py`, `translate.py`).
- Claim: The declared "strict island" around the ASPIC+ bridge is not in effect.
  Running `uv run pyright propstore/aspic_bridge` uses *basic* mode (0 errors),
  but this does not demonstrate strict-mode compliance because the strict flag
  never matches. The bridge is also one of the touchpoints most recently
  refactored (cf. `git log`: "refactor(cel): carry branded expressions through
  runtime").
- Recommendation: Either change the entry to `"propstore/aspic_bridge"` (the
  directory — pyright accepts directories under strict) or add individual files.

### Finding 2 — `propstore/source/` runtime-imports `propstore.cli.repository`
- Severity: **crit**
- Evidence: all eight top-level files in `propstore/source/` import
  `Repository` at module top, not inside a `TYPE_CHECKING` guard:
  - `source/alignment.py:16`
  - `source/claims.py:11`
  - `source/common.py:20`
  - `source/concepts.py:6`
  - `source/finalize.py:15`
  - `source/promote.py:27`
  - `source/registry.py:7`
  - `source/relations.py:12`
- Claim: Layer 1 (source-of-truth storage) takes a hard runtime dependency on
  layer 6 (CLI). By the declared one-way rule, upward imports are forbidden.
  The `Repository` class at `propstore/cli/repository.py:20` is in fact a
  filesystem-configuration primitive with no CLI-specific behavior; its location
  in `cli/` is the real defect, and every layer-1 module suffers for it.
- Recommendation: Move `Repository` to a true layer-1 module
  (e.g. `propstore/repo/repository.py` or `propstore/artifacts/repository.py`),
  and leave only the click command entry points in `propstore/cli/`. The same
  fix removes the lesser upward-import smells in `artifacts/store.py:21`,
  `artifacts/transaction.py:11`, `artifacts/codes.py:24`,
  `artifacts/families.py:52`, `artifacts/indexes.py:10`, `artifacts/types.py:11`,
  `repo/repo_import.py:18`, `repo/snapshot.py:12`, `world/model.py:38`,
  `compiler/context.py:28`, `proposals.py:18` (these are all `TYPE_CHECKING`
  guarded, so less urgent, but they point to the same structural problem).

### Finding 3 — `propstore/repo/` depends on layer-4 argumentation (`dung`)
- Severity: **high**
- Evidence:
  - `repo/merge_framework.py:9` — `from propstore.dung import ArgumentationFramework`
  - `repo/paf_merge.py:6` — same
  - `repo/paf_queries.py:4-10` — `from propstore.dung import (…)`
  - `repo/structured_merge.py:13` — same
  - `repo/merge_classifier.py:18` — `from propstore.z3_conditions import Z3TranslationError`
- Claim: Layer 1 (storage) imports layer 4 (argumentation) at module top. The
  merge framework embeds a `PartialArgumentationFramework` that depends on
  `dung.ArgumentationFramework`. Per CLAUDE.md: "Argumentation layer … Operates
  over assumption-labeled data, not hardened source facts." — i.e. argumentation
  is supposed to sit *above* storage, not be a primitive dependency of merge
  classification inside the git-backed repo layer.
- Recommendation: Either (a) acknowledge that the "storage" layer has a
  PAF-classification subsystem that is itself argumentative (and redraw the
  layer boundary to include it), or (b) invert the dependency: build the PAF
  over repo primitives in a higher layer, leaving `repo/merge_framework.py`
  containing only the data types without importing `dung`.

### Finding 4 — `core.analyzers` pulls argumentation + render into layer 2
- Severity: **high**
- Evidence: `propstore/core/analyzers.py:8-61` imports, at module top:
  - `propstore.bipolar` (layer 4)
  - `propstore.conflict_detector` (layer 4 by the task mapping)
  - `propstore.dung` (layer 4)
  - `propstore.preference` (layer 4)
  - `propstore.probabilistic_relations` (layer 4)
  - `propstore.world.types` (layer 5)
- Claim: `core/` is identified as layer 2 (type primitives, id types, active
  claim rows). `analyzers.py` turns it into a cross-layer dumping ground that
  depends on both argumentation and render. This is the single largest
  inversion in the tree. `graph_types.py:26` (strict-typed) stays below but is
  undermined by its sibling `analyzers.py`.
- Recommendation: Move `analyzers.py` to layer 4 (e.g.
  `propstore/argumentation/analyzers.py`) or at minimum to a free top-level
  module; strip the `world.types` coupling by moving the shared types (e.g.
  `SupportMetadata`) into a layer ≤ 2 location.

### Finding 5 — `claim_graph.py` (layer 4) reaches up into `world/` (layer 5)
- Severity: **high**
- Evidence: `propstore/claim_graph.py:15` — `from propstore.world.types import …`
  at module top.
- Claim: Upward import (layer 4 → layer 5). CLAUDE.md: "`world/` should be able
  to query `repo/` and `source/`, but neither `repo/` nor `source/` should
  reach into `world/`". The same principle is violated by layer 4.
- Recommendation: Move whatever `world.types` symbols are needed here into a
  layer ≤ 4 module (e.g. `propstore/core/`) or split `world/types.py` so that
  argumentation-facing contracts live in layer 4.

### Finding 6 — `source_calibration.py` (layer 3) pulls in layer 5 and layer 6
- Severity: **high**
- Evidence:
  - `source_calibration.py:5` — `from propstore.cli.repository import Repository`
  - `source_calibration.py:48` — `from propstore.world import WorldModel` (inside
    `derive_source_trust`)
  - Called from layer 1: `source/finalize.py:17` — `from
    propstore.source_calibration import derive_source_trust`
- Claim: Heuristic analysis reaches up to CLI and render. Combined with the
  call chain `source/finalize.py → source_calibration.derive_source_trust →
  WorldModel`, the "layers" become a strongly connected component: layer 1
  (`source/finalize`) calls layer 3 (`source_calibration`) which calls layer 5
  (`world.WorldModel`) which reads layer 5 (`sidecar`).
- Observation: `derive_source_trust` returns a new `SourceDocument`; the file
  does not write to source state itself. The write happens in `source/finalize`.
  So the heuristic-layer "proposals only" discipline (task item 4) is not
  violated in the sense of writing to non-proposal families — but the
  directional discipline is.
- Recommendation: Invert. Have the CLI orchestrate `WorldModel` lookups and
  pass bindings down into a pure layer-3 function, not the other way around.

### Finding 7 — `artifacts/codes.py` (layer 1) dynamically imports `WorldModel`
- Severity: **med**
- Evidence:
  - `artifacts/codes.py:241` — `from propstore.world import WorldModel` inside
    `verify_claim_tree`
  - `artifacts/codes.py:364-365` — same, plus `world.types.Environment`
- Claim: Layer 1 reaches up into layer 5 to resolve ambiguous claim references.
  Lazy imports don't remove the cycle; they only defer it to call time.
- Recommendation: Put claim-ref resolution (`wm.resolve_claim`) behind a
  narrow interface the CLI supplies at call time, or move `verify_claim_tree`
  out of `artifacts/` into a higher layer.

### Finding 8 — `core/literal_keys.py` (strict-typed) imports from layer 4 `aspic.py`
- Severity: **med**
- Evidence: `core/literal_keys.py:17` — `from propstore.aspic import GroundAtom, Scalar`.
- Claim: The strict-typed island intentionally pulls in `aspic`, which means
  `literal_keys.py` cannot actually type-check without propstore.aspic's types,
  and any change to `aspic.py` (not itself strict-clean per Finding 12) can
  leak via here. This is also an upward import (layer 2 → layer 4).
- Recommendation: Either move `GroundAtom`, `Scalar` down to a neutral layer,
  or move `literal_keys.py` up into the aspic bridge.

### Finding 9 — `grounding/` and `sidecar/rules.py` import layer-4 `aspic`
- Severity: **med**
- Evidence:
  - `grounding/bundle.py:45` — `from propstore.aspic import GroundAtom, Scalar`
  - `grounding/facts.py:54` — `from propstore.aspic import GroundAtom`
  - `grounding/grounder.py:55` — same
  - `grounding/translator.py:66` — same
  - `sidecar/rules.py:66` — `from propstore.aspic import Scalar`
- Claim: Layer 5 (render cluster, which `grounding/` belongs to per the task
  mapping) imports layer 4. This is *upward* in the declared order.
- Note: this may be the weakest declared assignment: `grounding/` builds the
  formal theory that the argumentation layer consumes, so it arguably belongs
  in layer 4 itself. Flagged here but also called out in Open questions.

### Finding 10 — `fragility*` (layer 5) imports `aspic`, `aspic_bridge`
- Severity: **med**
- Evidence:
  - `fragility.py:9` — `from propstore.aspic import conc, top_rule`
  - `fragility.py:10-12` — imports from `propstore.aspic_bridge.build`,
    `.extract`, `.grounding`
  - `fragility.py:14` — `from propstore.fragility_scoring import …`
  - `fragility.py:30,46` — `from propstore.world.types import QueryableAssumption`
- Claim: Layer 5 reaches into layer 4 for scoring support, which is the same
  class of upward coupling as Finding 9.
- Recommendation: If `grounding/` and `fragility*` are meant to consume layer 4,
  this is defensible — but the task mapping puts all four in layer 5.

### Finding 11 — `calibrate.py` (layer 3) imports `opinion.py` (layer 4)
- Severity: **low**
- Evidence: `calibrate.py:16` — `from propstore.opinion import Opinion,
  from_evidence, from_probability`.
- Claim: Layer 3 imports layer 4. CLAUDE.md lists `opinion.py` as a foundational
  primitive used across argumentation and calibration; it may belong lower than
  "layer 4 (argumentation)". Flagged in Open questions.

### Finding 12 — Two strict-typed modules currently fail pyright strict mode
- Severity: **high**
- Evidence: `uv run pyright propstore/aspic.py propstore/core/graph_types.py`
  reports 4 errors:
  - `aspic.py:189:16`, `aspic.py:217:16`, `aspic.py:245:16` — "Type 'int | None'
    is not assignable to return type 'int'".
  - `core/graph_types.py:206:24` — "Argument of type 'ClaimType | None' cannot be
    assigned to parameter 'claim_type' of type 'ClaimType'".
- Claim: The strict-typed island isn't actually green. Six of eight strict
  files pass cleanly (`core/literal_keys.py`, `core/labels.py`, `core/results.py`,
  `conflict_detector/models.py`, `dung.py`, `opinion.py` — 0 errors each); two
  fail. The `aspic_bridge.py` entry is phantom per Finding 1.
- Recommendation: Add explicit `None` handling or narrow return types at those
  four sites, or ward the strict list until they're green.

### Finding 13 — No heuristic-layer writes to source families (positive finding)
- Severity: **note** (requirement met)
- Evidence: grepped `transaction.save|\.save\(|\.write\(|with_transaction`
  across `embed.py`, `classify.py`, `relate.py`, `calibrate.py`,
  `sensitivity.py`, `source_calibration.py`, `relation_analysis.py` — all
  returned no matches. `classify.py` has no propstore writer-side imports,
  `relate.py` only reads via sqlite3, `calibrate.py` has no I/O, etc.
- Claim: Task item 4 (heuristic layer produces only proposals) is satisfied
  in the narrow sense that these files do not mutate source state directly.
  However `source_calibration.derive_source_trust` *returns a SourceDocument*
  that `source/finalize.py` then writes — so the heuristic result does end up
  in source state via the caller, not via a proposal branch. Worth confirming
  with Q whether source-trust calibration is meant to land on a proposal
  branch like `STANCE_PROPOSAL_BRANCH` (see `proposals.py:13`).

### Finding 14 — No out-of-band sidecar writes from `repo/`, `source/`, `world/` (positive finding)
- Severity: **note** (requirement met)
- Evidence: grepped `INSERT|UPDATE|build_sidecar|CREATE TABLE` across
  `world/`, `repo/`, `source/` — no matches. `build_sidecar` is invoked only
  from CLI (`cli/__init__.py:297`, `cli/compiler_cmds.py:214`). The only
  sidecar imports outside the sidecar package itself are `world/model.py:35`
  (read-only schema constants).
- Claim: Task item 3 ("CLI as the only entry point" for sidecar writes) holds.

### Finding 15 — `world/model.py` imports `sidecar/schema` constants (noted, not a violation)
- Severity: **note**
- Evidence: `world/model.py:35` — `from propstore.sidecar.schema import
  SCHEMA_VERSION, SIDECAR_META_KEY`; used at `world/model.py:254-292` for
  version checks on read.
- Claim: `world/` and `sidecar/` are both layer 5 per the task mapping, so
  lateral. The read-only intent is clear from the surrounding check. Listed
  here only to confirm it is intentional.

## Strict-typed island check

- Ran `uv run pyright <file>` on each strict module:

| File | Result |
|---|---|
| `propstore/core/literal_keys.py` | 0 errors |
| `propstore/core/labels.py` | 0 errors |
| `propstore/core/graph_types.py` | **1 error** (line 206) |
| `propstore/core/results.py` | 0 errors |
| `propstore/conflict_detector/models.py` | 0 errors |
| `propstore/dung.py` | 0 errors |
| `propstore/opinion.py` | 0 errors |
| `propstore/aspic.py` | **3 errors** (lines 189, 217, 245) |
| `propstore/aspic_bridge.py` | **file does not exist** (phantom; see Finding 1) |

- Leakage analysis:
  - `core/literal_keys.py:17` imports `GroundAtom, Scalar` from
    `propstore.aspic`. `aspic.py` is itself strict-listed but has 3
    strict-mode errors (Finding 12). So literal_keys passes only because its
    own use of those symbols doesn't trigger the return-type issue in
    `aspic.py`; a refactor that exposes a `to_int()`-like surface would leak
    the `int | None` return into literal_keys.
  - `core/labels.py` imports only from `cel_types` and `core.id_types`. Both
    are basic-mode but cel_types is a focused type module; low leakage risk.
  - `core/graph_types.py:11` imports `Environment` from `core.environment`
    (basic mode). `core/environment.py` has 30+ basic-mode pyright errors in
    the global run (part of the 1628) — strict graph_types builds on a
    wobbly foundation here. The strict error on `graph_types.py:206` is on a
    `ClaimType | None` where the construction site does not narrow.
  - `conflict_detector/models.py:9` imports `CelExpr`, `to_cel_expr`,
    `to_cel_exprs` from `propstore.cel_types` (basic mode). `cel_types.py`
    returns branded aliases; low leakage risk.
  - `dung.py`, `opinion.py`, `aspic.py` — no propstore imports, so no leakage
    from basic modules.

## Open questions

- **Is `propstore.conflict_detector` layer 2 or layer 4?** The task lists it
  under layer 4 (argumentation), but its imports are all layer 1/2 (cel_types,
  condition_classifier, claims, equation_comparison, value_comparison). It
  looks more like a semantic-layer analyzer. Classification matters for
  Finding 4: if conflict_detector is layer 2, then `core/analyzers.py` is
  *only* violating via `dung/preference/probabilistic_relations/bipolar` and
  `world.types`.
- **Is `propstore.grounding/` layer 4 or layer 5?** Task puts it in layer 5.
  But it builds `GroundAtom`/`Scalar` structures that feed the ASPIC+ bridge;
  a straight read of the code suggests it's a formal-theory builder that
  argumentation consumes (layer 4 or between). If it is layer 4, Finding 9
  becomes lateral.
- **Is `propstore.opinion.py` layer 4?** It is declared so by the task and
  listed strict. But it is import-isolated (no propstore imports) and is
  consumed by calibrate (layer 3). A case can be made that `opinion` is a
  foundational algebra that sits *below* both heuristic calibration and
  argumentation. If so, Finding 11 disappears.
- **Is `propstore/cli/repository.Repository` a CLI concern?** It is a thin
  filesystem locator with no click/terminal surface. Relocating it fixes
  Finding 2 and most of the secondary `TYPE_CHECKING` imports. Needs Q's
  intent on why it lives under `cli/`.
- **Did not run strict pyright across the whole project.** Strict mode is
  file-gated in `pyproject.toml`; the global `uv run pyright` used basic mode
  for everything else (1628 errors, out of scope for this axis).
- **Did not trace every `if TYPE_CHECKING:` block.** Grep shows 17 such
  guarded `cli.repository` imports; I verified the `source/` ones are
  unguarded but didn't individually read each `artifacts/` / `repo/` usage.
