# Principled Path — Self-Audit of the Workstream Hedges

Date: 2026-04-16
Status: proposed correction to `workstreams/`
Companion to: `SYNTHESIS.md`

## Operating constraints (confirmed 2026-04-16)

Before auditing the hedges: the project's actual constraints, which collapse several of the "costs" I wrote below.

- **No external users.** Q is the sole user. No deployment cadence, no release SLA, no downstream consumers.
- **No funding / publication / deployment pressure.** Build-the-right-thing mandate. The only scope discipline is *what's beautiful and correct*.
- **On-disk format is uncommitted.** Breaking schema changes are free; old knowledge repositories are not a compatibility target.
- **Agent pools:** Claude Max + Codex Pro. Agent time is effectively unbounded at plan-level cost; iteration cost is low.

These constraints mean: **every argument of the form "the hedged path preserves compatibility / reduces user friction / defers a license question" dies.** There is nothing to preserve. There is no user to be friendly to but Q, and Q is already saying go fast. The principled path is not just preferred — with these constraints, the hedged path has no defense.

## What this is

Q asked: is there anywhere in these workstreams where I recommended the easy path where we should instead take the beautiful / correct path?

Answer: yes. Several places. Below is an honest enumeration.

Framing first: "principled" in this project means (a) non-commitment discipline at storage, (b) honest ignorance over fabricated confidence, (c) render filters, build does not, (d) heuristic output is proposals, not mutations. I'll add a fifth that falls out of this review: (e) **docs never lead code** — every citation is a claim, every claim is property-tested or retracted.

For each hedge I catch in my own work, I state what I wrote, what the principled version is, why the hedge is wrong, and what the principled version costs beyond the hedged version. Then I reshape the workstream set accordingly.

## Hedges I wrote, by workstream

### WS-A-P1 — Provenance

**Hedge 1.1: Migration default `status="legacy"` for undocumented pre-migration data.**

What I wrote: "mark all pre-migration trust as `status='legacy'`" as one of two options for handling existing on-disk documents without provenance.

Principled version: **refuse to load undocumented trust**. New authored data must use explicit provenance for every probability-bearing document. Pre-workstream payloads fail at the document boundary; there is no reauthoring CLI, migration path, quarantine branch, fallback reader, or old-repo bridge.

Why the hedge is wrong: `"legacy"` is a lie. It says "this value has provenance of kind legacy" when the actual truth is "this value has no known provenance." The review's central complaint is exactly this class of default-masquerading-as-answer. Encoding it into the migration path bakes the bug into every repo that ever existed.

Cost of the principled path: pre-workstream `knowledge/` repos do not load under the new schema. That is acceptable because old knowledge repositories are not a compatibility target.

**Hedge 1.2: "Opaque witness-id references into a per-repo provenance table" as the serialization.**

What I wrote: "probably use opaque witness-id references into a per-repo provenance table; the table itself is named-graph-shaped."

Principled version: **named graphs inline, every claim self-describing**. Carroll 2005's argument for named graphs is precisely that a claim's provenance should travel with the claim — not be stored in a side table where consumers may or may not look it up. The storage cost is higher; the epistemic value of self-containment is what Carroll is selling.

Why the hedge is wrong: a side-table design repeats the same failure mode as `SourceTrustDocument`'s missing `status` field — the provenance rides elsewhere from the value, and consumers drift into reading the value without the provenance. Self-containment is the invariant that makes provenance tractable at scale.

Cost of the principled path: storage bloat. Mitigation: the on-disk format can deduplicate identical provenance witnesses via content-addressed references, but the *logical* claim carries the full named graph; the optimization is at the storage layer, not the semantic layer.

### WS-A-P2 — Lemon

**Hedge 2.1: Jaccard fallback preserved "as explicit last resort".**

What I wrote: "`source/alignment.py` Jaccard fallback still exists but sits behind an explicit lemon-first pipeline."

Principled version: **remove Jaccard**. Lexical match via lemon `Form` identity + `LexicalEntry` identity + `OntologyReference` equality, in that order. If all three miss, the system says "no match found" and proposes candidates (ranked by string similarity, yes, but as *proposals on a proposal branch*, not as a silent decision).

Why the hedge is wrong: token-Jaccard as a fallback is precisely a fabricated-confidence site. The system has no structural knowledge that two strings with 70% token overlap refer to the same concept; it just returns an answer because having an answer is more convenient than not. This is the same antipattern as `_DEFAULT_BASE_RATES` wearing semantic clothes. Per principle (b) honest ignorance, the system should admit it doesn't know, not guess.

Cost of the principled path: reconciliation workflows change — every near-match goes through explicit proposal review instead of auto-aligning. More friction; more truth.

**Hedge 2.2: "Backward-compatibility shims live for one release cycle."**

What I wrote: "Backward-compatibility shims live for one release cycle per Z-3."

Principled version: **single hard migration, no parallel support**. Old-schema documents fail to load on the new version; the migration CLI is the supported path. Per Q's memory `feedback_no_fallbacks`: "Never build fallback/compat shims — rip out old interface, let it break, fix callers in one pass."

Why the hedge is wrong: I wrote it as if propstore has external users whose repos might outlive a release cycle. The project is one month old. Even if it did have such users, parallel support is the decade-long bug generator — it is exactly how the unfixed `if opinion:` shortcircuit bug lived in `classify.py` until commit 34d0074. Backward compat preserves the bug surface at the cost of the fix surface.

Cost of the principled path: existing repos must migrate before using the new version. This is the correct cost.

**Hedge 2.3: `form_utils.py` "renamed or partitioned".**

What I wrote: hedging `or`.

Principled version: **split**. `form_utils.py` does two unrelated things (physical-dimension algebra via pint, and what is accidentally shaped like lemon Form). They deserve separate files — `propstore/dimensions.py` for the physics, `propstore/core/lemon/forms.py` for the lemon Form. Renaming the combined file preserves the confusion; splitting removes it.

Cost: one more file. No semantic cost.

### WS-A-P3 — Frames + Qualia

**Hedge 3.1: Binary proto-role presence "as a simplification."**

What I wrote: "Committing to binary proto-role presence is a simplification; graded requires a provenance-bearing numerical property."

Principled version: **graded proto-roles with provenance.** Dowty's paper argues proto-role entailments are graded; committing to binary bit-flags loses the paper's argument. A-P1 provenance gives us the numerical-with-provenance carrier for free — we already need it for opinions; using it for proto-role entailment bundles costs no additional type machinery.

Cost: slightly richer proto-role type; slightly more complex CLI for editing. Both trivial at this project's cadence.

**Hedge 3.2: FrameNet import "as a separate data ingestion task if decided."**

What I wrote: punting the FrameNet-inventory decision.

Principled version: **commit to FrameNet import**. The Berkeley FrameNet inventory is the shared-vocabulary commons for frame semantics. A system calling itself a semantic OS without a standard frame inventory is reinventing vocabulary per repo, which defeats the point. Import it; expose extensibility for per-repo additions.

Cost: an external data dependency (~150MB) and a licensing check (FrameNet is CC BY 3.0 via LDC or direct Berkeley release; terms need confirmation). The licensing is the real question; if acceptable, import. If not, document the gap in `docs/gaps.md` with a plan for alternative seed inventories.

**Hedge 3.3: `list[OntologyReference]` qualia structure as a false option.**

What I wrote: "either commit to `list[OntologyReference]` or a richer structure."

Principled version: **richer structure — nested qualia typed by Pustejovsky's event structure**. The flat list is what the code would be if propstore were a description-logic-style ontology; the richer structure is what Pustejovsky's generative lexicon actually needs. A-P3 should deliver the latter.

Cost: more typing. Directly buys the generative-lexicon behavior the workstream exists to enable.

### WS-A-P4 — Contexts + Micropubs

**Hedge 4.1: "Retain visibility inheritance as a default lifting rule."**

What I wrote: one of two options — "retire entirely, or retain as a default lifting rule that users can override."

Principled version: **retire entirely**. Visibility-inheritance contexts are a different semantics from `ist(c, p)`; keeping them alive under a new name means the old wrong semantics ship in the new version. Users who want ancestor visibility can declare explicit lifting rules that encode that behavior per-repo.

Cost: a documentation burden — users relying on the implicit inheritance need to learn to declare it. The migration tool that rewrites existing contexts can emit the declarative lifting rules automatically during migration.

**Hedge 4.2: Nested `ist` "leave a hook and defer."**

What I wrote: "Probably leave a hook and defer — don't commit to nested reasoning in this workstream."

Principled version: **commit to nested at the type level now**. `ist(c1, ist(c2, p))` should parse, store, and round-trip from day one, even if operational reasoning over nested contexts lands later. Type shape is cheap at design time; changing it later is expensive and breaks every consumer.

Cost: the type hierarchy has to handle the recursive case (trivially — `Context` contains `ist` statements that can themselves reference contexts). No runtime cost.

**Hedge 4.3: Micropub-ATMS identity as two options, easier one highlighted.**

What I wrote: "If each micropub is an ATMS node, ATMS gets much bigger. If micropubs aggregate ATMS nodes, the mapping is less clean."

Principled version: **each micropub IS an ATMS node**. Clean semantics, even though labels grow. Clark's micropublications are the composition rule; ATMS nodes are the justification-bearing unit; making them the same object collapses two abstractions that otherwise drift.

Cost: ATMS label sets grow; property tests take longer. Acceptable.

**Hedge 4.4: Blocking vs parallel support migration.**

What I wrote: "Decision: blocking migration (can't use new version until migrated) vs. parallel support (old claims work with default-context shim). Blocking is cleaner but harder on users."

Principled version: **blocking**. Same reasoning as 2.2.

**Hedge 4.5: Lifting-rule expressiveness "commit to a decidable subset."**

What I wrote: hand-wave about deciding later.

Principled version: **commit to Bozzato CKR's justifiable-exceptions shape**. It's decidable, expressive enough for propstore's use cases, and the paper is already in the corpus for Track C. Use it; prepares for Track C by double-dipping the same paper across both.

### Cross-cutting

**Hedge X.1: Z-3 as a separate workstream.**

What I wrote: a distinct "citation + doc cleanup" bucket.

Principled version: **Z-3 dissolves into discipline**. Two concrete commitments replace the bucket:

1. **One-time sweep during any touch of a cited module.** Whoever edits a file with an unbacked citation (for any reason) is responsible for either retracting the citation in the same commit, or introducing the property test that backs it. CI lint fails commits that weaken the citation-coverage ratio.
2. **Standing `docs/gaps.md`** replaces CLAUDE.md's "Known Limitations." Every gap has a finding reference or a workstream reference. New gaps are only added when observed; existing gaps are only removed when a test proves closure.

A separate Z-3 workstream concedes that the project might not enforce this discipline across other work. Not concedeing it is the principled move.

**Hedge X.2: Four discrete Track A workstreams with defined handoffs.**

What I wrote: A-P1, A-P2, A-P3, A-P4 as separate workstreams.

Principled version: **one integrated semantic-substrate workstream with internal phases**. The dependencies are too tight. Provenance feeds into lemon senses. Lemon senses hold frame/qualia slots. Frame/qualia content gets `ist`-qualified. Artificial handoffs between workstreams add integration overhead without adding clarity.

Restructure: `workstreams/ws-a-semantic-substrate.md` covers the whole thing, with **P1→P2→P3→P4 as phases within it** and a single integrated papers list, type system, and migration pass. The four original workstream documents survive as *phase details* referenced from the master.

Cost: harder to parallelize across agent swarms (some phase work can still happen in parallel — papers reading for P3 can start while P1 types are still under design). The integration coherence is worth the serialization.

**Hedge X.3: The meta-discipline I didn't state.**

I wrote fifteen structural findings and four workstreams and did not install the one discipline that would have prevented the findings from existing in the first place.

Principled version: **every citation is a property test**. Every claim in docstrings of the form "per Paper 2018 Def N" generates (or references) a test named after the claim. Tests that would require machinery not yet built (AGM K*1-K*8 on a non-AGM revision module) are *pending* — they exist, they xfail with a link to the workstream that will make them pass. This surfaces gaps instead of hiding them behind prose.

Cost: every existing citation either gets a test, or gets a pending test with a xfail link, or gets struck. One-time sweep. Thereafter CI enforces.

## Restructured workstream set

Putting the corrections together, the principled set is:

### Primary workstreams

- **WS-A** (one workstream, four internal phases) — semantic substrate retrofit. Principled-version commitments baked in: named-graph-inline provenance, Jaccard removed, single hard migration, `form_utils.py` split, graded proto-roles, FrameNet imported, rich qualia type, visibility inheritance retired, nested `ist` typed from day one, micropub IS ATMS node, Bozzato-style lifting rules.
- **WS-B** — belief-set layer (real AGM) with K*1-K*8 + C1-C4 + EE1-EE5 as property tests. Revision module either wraps the new layer or is retired.
- **WS-C** — defeasibility remediation. Populates priorities; commits to a defeasibility semantics (Bozzato-style from WS-A is a candidate; ABA is an alternative; decision in the workstream prompt).
- **WS-Z-types** — honest-ignorance types (`Provenance`, `CategoryPrior`, `SolverResult`, `Opinion | NoCalibration`, `ConflictClass.UNKNOWN`). Depends on WS-A phase 1 (provenance). Closes patterns A + B from SYNTHESIS.md.
- **WS-Z-gates** — build-to-render gate removal. Closes pattern C. No paper dependency.

### No longer workstreams (dissolved into discipline)

- ~~WS-Z-3 citation cleanup~~ — replaced by (a) the one-time citation sweep as part of the WS-Z-types + WS-Z-gates baseline, and (b) a CI lint that fails commits introducing unbacked citations in new docstrings. Plus: `CLAUDE.md` loses the "Known Limitations" section and gains a link to `docs/gaps.md`.

### Standing disciplines introduced

- **Citation-as-claim:** every `per Paper YYYY Def N` style docstring references a test by name. Unbacked citations are struck or xfail'd.
- **Docs follow code, never lead:** CLAUDE.md paragraphs are updated in the same commit that changes the code they describe. PR checks for CLAUDE.md edits when strict-typed modules change.
- **`docs/gaps.md` as the single source of truth for known limitations:** severity-tagged, workstream-linked, updated on every remediation merge.

## The costs I'm explicitly accepting

Under the operating constraints, the principled path's real costs are narrow:

1. **Existing `knowledge/` repos are abandoned as compatibility targets.** No reauthoring CLI, no old-repo migration, no agent-hours spent preserving old authored data.
2. ~~**No backward-compat shims means every version bump is breaking.**~~ **Retracted.** No external consumers. Breaking is the default stance; the question is only whether the new version is more correct than the old.
3. ~~**FrameNet as an external dependency** (licensing)~~ **Reduced.** No deployment pipeline to satisfy. If Berkeley FrameNet's license permits the use, ship it; if it doesn't, ship per-repo seeds and revisit. The licensing question stops being blocking — it becomes a footnote.
4. **One integrated Track A workstream is harder to parallelize** across agent swarms. Offset by lower integration overhead; with two agent pools (Claude Max + Codex Pro) this is nearly a non-issue.
5. **Citation-as-claim discipline** costs every citing commit an extra test or a retraction. This is the cost that pays for itself fastest — every finding in the review exists because this discipline wasn't in place.

## Decisions — most self-answer under the operating constraints

Most of the open decisions I raised had answers that depended on external constraints that don't exist. Under the confirmed constraints, they resolve.

1. ~~**Reauthor CLI scope** — permissive inference vs. strict unknown?~~ **Answer: strict-unknown.** No external users to be friendly to; inference fabricates the thing the whole workstream exists to eliminate.
2. ~~**FrameNet licensing.**~~ **Answer: ship it if the license permits; per-repo seeds otherwise; re-evaluate if/when external distribution becomes a concern.** Not a gating decision.
3. ~~**Belief-set layer — formulas or typed assignments?**~~ **Answer: formulas.** The typed-assignment approach was a pragmatic extension of existing machinery. With no pragmatic pressure, pick faithful-to-paper. A new subsystem is cheap at agent speed.

Genuinely open decisions:

4. **Defeasibility semantics choice** (gates Track C paper dispatch). ABA (Bondarenko/Toni), pure ASPIC+ with populated priorities (continuing the current family), or Bozzato-style justifiable exceptions (double-dips with Track A's lifting rules)? Each is defensible; the choice shapes the paper-reading order.
5. **`docs/gaps.md` authorship.** Manual (Q / PR author) vs. automated (axis-9-style doc-drift scan on every PR). Both work; automated is more robust but needs a CI lint to exist first. Pick one.
6. **Do we want a `worldline/` → `trace/` or similar rename?** `worldline/` is a lovely physics metaphor and the module's contents match it (an agent's trajectory through epistemic state), but it's undocumented in CLAUDE.md and the name is non-obvious for new readers/agents. Cosmetic; flagging only.

## Where to start

With constraints collapsed, the execution order is:

1. **Install the two standing disciplines first** — `docs/gaps.md` replaces Known Limitations; citation-as-claim CI lint goes up with a grandfathered baseline. This is the discipline layer that keeps everything downstream honest. Agent-evening.
2. **WS-Z-types + WS-Z-gates** (concurrent). Agent-day each. Closes the fabricated-certainty and build-time-filter pattern families.
3. **WS-A (integrated semantic substrate workstream)**. Paper reading kicks off. Several weeks of agent work.
4. **WS-B (belief-set + AGM)** starts as soon as WS-A's P1 (provenance) lands. AGM formulas carry provenance too.
5. **WS-C (defeasibility)** starts after the Track C semantic decision above is made. Can proceed alongside WS-A's later phases.

Query: proceed? Items 4, 5, 6 from the decisions list are the only real Q-calls remaining. Everything else collapses to "do the beautiful thing, there's nothing preventing it."
