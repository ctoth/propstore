# propstore Narrative Review: Gaps and Opportunities

Date: 2026-03-22
Source: metanovel architecture analysis (paper Section 5) + propstore code review

## Context

The metanovel project aims to build a novel-length fiction generator grounded in
the computational narrative literature. Its paper (Section 5) describes a four-layer
architecture where the state layer needs: time-aware fact tracking, causal event
graphs, conflict tracking, character knowledge scoping, and consistency checking.

propstore already provides most of the infrastructure for this. But the analysis
revealed three gaps that are **domain-general improvements**, not narrative-specific
hacks. Each would strengthen propstore for scientific knowledge too.

## Resolution Update: Worldline Journals

The temporal-query part of this review is resolved by the worldline-journal bridge
implemented on 2026-05-04. The implemented path is not claim-level
`valid_from` / `valid_until`; it is durable worldline trajectories:
`pks worldline build-journal` captures a `TransitionJournal`, and
`pks worldline at-step NAME STEP` projects the accepted claim view at a journal
step. The backing APIs are `capture_journal(...)` and
`WorldQuery.at_journal_step(...)`.

This means the narrative-engine query formerly described as `world.at(chapter_N)`
is now `worldline at-step <canon-track> <chapter-step>` for claim-membership
views. Causal edges and subgraph pattern queries remain separate workstreams.
Heavy historical stance/conflict reconstruction is not part of the completed
bridge and should be triggered only by a concrete inter-step stance requirement.

---

## Gap 1: Directional Causal Edges

### What propstore has now

Parameterization relationships: algebraic formulas linking concepts.
`f0 = 1/T0` — bidirectional, symmetric, derived through SymPy.

Stances between claims: rebuts, undercuts, supports, supersedes.
These express epistemic relations (agreement/disagreement), not causal ones.

Concept relationships: component_of, etc. Structural, not causal.

### What's missing

Directional causal links between claims or events: "A causes B", "A enables B",
"A prevents B." These are not algebraic (you can't solve backwards), not epistemic
(they don't agree or disagree), and not structural (they're about temporal influence).

### Why this matters for science too

Scientific papers make causal claims constantly:
- "Increased vocal fold tension causes higher fundamental frequency"
- "Drug X prevents tumor growth"
- "Sleep deprivation enables attentional lapses"

These are not derivation relationships (no formula) and not stances (not
agreement/disagreement). They're a distinct edge type that propstore currently
can't represent.

Right now these get flattened into `observation` claims: "Breathiness increases
with incomplete glottal closure." The causal structure is buried in prose. If
`causes`/`enables`/`prevents` were first-class edges between claims, propstore
could answer: "What downstream effects does this claim have?" and "If I remove
this claim, what causal chains break?"

### Proposed addition

New relationship types on claims (not concepts):

```yaml
causal_links:
  - type: causes       # directional: this claim's truth leads to target's truth
    target: claim15
    strength: strong
    mechanism: "incomplete closure reduces harmonic energy"
  - type: prevents
    target: claim22
    strength: moderate
```

This parallels the stance system but for causal rather than epistemic relations.
The graph export already handles multiple edge types — adding `causal` edges
would slot in alongside parameterization, relationship, stance, and claim_of.

`pks world hypothetical --remove claim2` already shows what changes when a claim
is removed. With causal edges, it could also show what *downstream effects* are
lost — not just what derivations break, but what causal chains break.

---

## Gap 2: Temporal Ordering of Claims

### What propstore has now

Claims have provenance (paper, page) but no temporal index. The `supersedes`
stance implies temporal ordering (newer replaces older) but the ordering is
implicit in the paper metadata, not first-class.

Conditions can express time-like scoping (`chapter <= 7`, `phase == 'treatment'`)
but there's no built-in notion of validity intervals — a claim that is true
from time T1 to time T2 and then false.

### What's missing

First-class temporal validity on claims:

```yaml
valid_from: "chapter_3"    # or a date, or an experimental phase
valid_until: "chapter_7"   # null = still valid
superseded_by: claim42     # explicit link when validity ends
```

### Why this matters for science too

Scientific knowledge has temporal validity:
- "The recommended dosage was 500mg" (valid until 2023 trial)
- "The standard model predicted no Higgs boson" (valid until 2012)
- Longitudinal studies have time-phased findings
- Treatment protocols change; the old claim isn't wrong, it's expired

Currently propstore handles this through `supersedes` stances, but that's
claim-to-claim. There's no way to say "this claim is valid during experimental
phase 2 only" without making the phase a condition. Conditions work but they
conflate *when* a claim holds with *under what circumstances* it holds. These
are semantically different:

- `speaker_sex == 'male'` — a circumstance (the claim holds whenever this is true)
- `study_phase == 'baseline'` — a temporal scope (the claim was measured here)

If propstore distinguished temporal scope from logical conditions, queries like
"what was believed at time T?" and "what changed between T1 and T2?" would
become natural.

### Superseded proposal

The original proposal was optional `valid_from` / `valid_until` fields on
claims, plus a `world.at(time)` query that filters to claims valid at that
point. The implemented bridge uses worldline journals instead: temporal
currency is represented by the ordered `TransitionJournal` state sequence, not
by adding validity intervals to each claim document.

For conflict detection, the current bridge answers "which claims are accepted at
step k?" It does not yet re-derive historical stances/conflicts at step k. That
heavier view remains a separate trigger: implement it only if fiction-curation
or federation work needs inter-step stance projection rather than flat accepted
claim membership.

---

## Gap 3: Subgraph Pattern Queries

### What propstore has now

- `pks world query CONCEPT` — single-concept lookup
- `pks world chain CONCEPT` — traverse parameterization graph
- `pks world check-consistency` — find conflicts
- `pks world export-graph` — dump the whole graph

### What's missing

Pattern matching over the knowledge graph: "find all subgraphs where claim A
`causes` claim B, and claim C `rebuts` claim A." Or in narrative terms: "find
all competition structures" (two characters with conflicting goals where each
takes actions that threaten the other's goal).

### Why this matters for science too

Recurring structural patterns in scientific knowledge:
- **Replication structure:** Claim A (original finding) + Claim B (replication)
  where B `supports` A with different conditions
- **Controversy structure:** Claim A + Claim B where they `rebut` each other,
  plus Claims C and D that `support` one side each
- **Paradigm shift:** Chain of `supersedes` stances from old to new
- **Methodological critique:** Claim A `undercuts` Claim B (attacks the method,
  not the conclusion)

These are graph patterns that propstore could match automatically. Currently you
have to manually inspect `pks world explain` output for individual claims. A
pattern query system would surface structural features across the whole knowledge
base.

### Proposed addition

A template-based pattern query:

```bash
pks world find-pattern replication
pks world find-pattern controversy
pks world find-pattern causal-chain --min-length 3
```

Where patterns are defined as typed node/edge templates:

```yaml
name: controversy
nodes:
  - id: a
    type: claim
  - id: b
    type: claim
edges:
  - source: a
    target: b
    type: stance
    stance_type: rebuts
  - source: b
    target: a
    type: stance
    stance_type: rebuts
```

This is the most speculative of the three gaps — it may be premature to build
before the first two are in place. But it's worth flagging because it falls out
naturally once causal edges and temporal ordering exist.

---

## What stays outside propstore

Two things from the metanovel architecture that should NOT go into propstore:

1. **Mutable state.** propstore is a journal of claims — append-mostly, never
   mutated. Narrative state changes (a door is locked, then unlocked) should be
   modeled as claim sequences captured into worldline journals, not as in-place
   mutations. The narrative engine maintains a "current state" view by querying
   a worldline journal step; propstore stays immutable underneath.

2. **Character simulation.** Persistent agents with goals, fears, memory, and
   decision-making are a simulation concern. propstore can store the *knowledge*
   that agents have access to (scoped by character conditions), but the agent
   loop itself lives in the narrative engine. propstore is the world model;
   the agents are the actors.

---

## Implementation priority

1. **Causal edges** — smallest change, biggest payoff. New edge type on claims,
   integrated into graph export and hypothetical queries.
2. **Pattern queries** — largest change, most speculative. Depends on causal
   edges and the completed worldline-journal bridge for temporal projection.
3. **Heavy journal projection, conditional** — re-derive historical
   stances/conflicts at a worldline step only if downstream fiction-curation or
   federation work needs more than accepted claim membership.

Causal edges, pattern queries, and any heavy journal projection remain
domain-general. None require narrative-specific concepts in propstore's core.
