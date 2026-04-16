# Report — WS-A Event Semantics Position Statement Doc

Source prompt: `prompts/ws-a-event-semantics-doc.md`.

## Result

- **Doc created:** `docs/event-semantics.md`
- **Commit hash:** `f25817d`
- **Commit message:** `docs(events): adopt descriptivist event semantics — Hobbs/Quine/Putnam grounding, Davidsonian rejection`
- **Word count:** 1199 (within the prompt's 600–1200 target).

## Structure

All 8 required sections present in the specified order, with the specified headings:

1. Position — verbatim two-paragraph spine from the prompt; commitments unchanged.
2. Why this matters — federation, non-commitment, composition.
3. Philosophical lineage — Hobbs 1985, Quine 1968, late-period Putnam.
4. What we are explicitly NOT doing — all 8 required bullets preserved.
5. Practical commitments — all 8 required bullets preserved.
6. Pushback acknowledged — description-quality and UI paragraphs.
7. References — citation-as-claim compliant.
8. Cross-references within propstore.

## Citation-as-claim compliance

Every paper named resolves to either a `papers/<dir>/` location or a `to fetch` tag against `semantic-substrate-papers.md`:

- **Resolved to `papers/`:** Pustejovsky 1991, Dowty 1991, Fillmore 1982 — confirmed present in `papers/` listing.
- **`to fetch` against `semantic-substrate-papers.md`:** Hobbs 1985, Quine 1968, Putnam late-period, Davidson 1967, Davidson 1969, Davidson 1985, Parsons 1990 — confirmed absent from `papers/` listing and cross-checked against the P3 sections of `semantic-substrate-papers.md` which flag them as may-fetch / read-for-rejection.
- **Allen 1983** — cited as the interval-relation vocabulary already consumed inside the existing `Z3ConditionSolver` temporal machinery. Not in `papers/` as its own directory; cited in the doc as "already consumed inside existing temporal machinery." Flag for Q: if a standalone Allen-1983 paper directory is desired, it should be added to the retrieval list. Did not add it myself since the prompt restricts me to creating `docs/event-semantics.md` and did not authorize corpus changes.

## Decisions and latitude taken

- **Intro preamble.** Added a one-line framing before section 1 naming WS-A/WS-C grounding so a fresh reader sees where the doc fits before hitting the verbatim spine. Kept it minimal.
- **Tone.** Followed the prompt's "clear, technical, neither defensive nor sycophantic." No hedges, no meta-commentary.
- **Length trim pattern.** Initial draft was 1535 words; trimmed in four passes to 1199 without touching: the verbatim spine (section 1), any required bullet (sections 4, 5), any required paragraph topic (sections 2, 3, 6), or any paper citation. Trims were prose-density only.
- **"Putnam late-late retraction" framing.** The prompt authorized acknowledging Putnam's retreat from internal realism. Kept the acknowledgement in section 3 but shortened it.
- **Cross-reference to `disciplines.md`.** Not required by the prompt's cross-reference section, but added to section 8 because section 7's citation-as-claim statement depends on it.
- **Did not touch `CLAUDE.md`, `semantic-substrate-papers.md`, the workstream docs, or any code.** Per the prompt's "don't update them yourself; just flag" instruction, every outside-doc change suggestion lives in the "Cross-references to flag" section below.

## Cross-references to flag (not updated here)

These files reference event-semantics topics and should be updated to point at `docs/event-semantics.md`:

- **`CLAUDE.md`** — the "Literature Grounding" section should add a line referencing `docs/event-semantics.md` as the canonical position on event semantics. The "Concept/semantic layer" paragraph currently talks frame-semantic rhetoric; once WS-A lands the implementation, the paragraph needs the honest rewrite per WS-A P3 exit criteria, and this doc is the anchor for that rewrite.
- **`reviews/2026-04-16-code-review/workstreams/ws-a-semantic-substrate.md`** — already references `docs/event-semantics.md` in multiple places (phase 3 scope, red-flags, vision); references resolve correctly once this doc exists. No updates needed.
- **`reviews/2026-04-16-code-review/workstreams/ws-c-defeasibility.md`** — already references `docs/event-semantics.md` in the "Composition with WS-A's descriptivist event semantics" section; reference resolves correctly. No updates needed.
- **`semantic-substrate-papers.md`** — P3 section already references `docs/event-semantics.md`. No updates needed.
- **`docs/worldlines.md`** (exists; not read during this task) — likely worth a cross-reference from there to `docs/event-semantics.md` since section 5 commits to worldlines as description-trajectories. Flag for a separate pass that has permission to read and edit `docs/worldlines.md`.
- **Future `docs/qualia-and-proto-roles.md` and `docs/contexts-and-micropubs.md`** (WS-A phase 3 and phase 4 exit criteria) — both will need to open-coordinate with this doc. Not yet written.

## Commit for the report

Per prompt:

```
git add -f reports/ws-a-event-semantics-doc.md
git commit -m "report(ws-a): event-semantics position-statement doc landed"
```

Commit hash for the report itself will be recorded at the end of the task in the transcript.
