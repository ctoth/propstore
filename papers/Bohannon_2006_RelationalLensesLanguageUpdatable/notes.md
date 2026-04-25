---
title: "Relational Lenses: A Language for Updatable Views"
authors: "Aaron Bohannon, Benjamin C. Pierce, Jeffrey A. Vaughan"
year: 2006
venue: "PODS 2006 (ACM SIGACT-SIGMOD-SIGART Symposium on Principles of Database Systems)"
doi_url: "https://doi.org/10.1145/1142351.1142399"
affiliation: "University of Pennsylvania"
pages: "343-352"
produced_by:
  agent: "claude-opus-4-7-1m"
  skill: "paper-reader"
  status: "stated"
  timestamp: "2026-04-25T08:41:53Z"
---
# Relational Lenses: A Language for Updatable Views

## One-Sentence Summary
Defines a small combinator language of *relational lenses* (select, project, join) where each combinator denotes a paired `get` (view) and `put` (update-translation) function with a static functional-dependency type system, satisfying *well-behaved* lens laws (GetPut, PutGet) — and additionally the strong *very well-behaved* law (PutPut) — so that tree updates over the view can be propagated back to the source while preserving functional-dependency integrity *(p.343-344)*.

## Problem Addressed
The classical *view-update problem* in relational databases asks: given a view defined by a query Q over a source database, when an updated view is supplied, how should the source be modified so that the update is reflected by Q? Most prior approaches treat the view as fixed and determine which class of updates can be unambiguously translated to source updates (Bancilhon-Spyratos "view complement", Cosmadakis-Papadimitriou key/projection methods, Dayal-Bernstein "view update"). The authors instead build a *language* in which the source-to-view transformation and the update propagation are designed *together* as a syntactic combinator, and statically guaranteed to satisfy well-behavedness *(p.343-344, §1)*.

## Key Contributions
- A bidirectional combinator language for relational data: select (σ), project (π), join (⋈), each given as a *lens* (get + put) operating on (relation, functional-dependency-set) pairs *(p.343, §1; p.348, §5)*.
- A type discipline: each combinator is statically typed by a "predicate on relation states" plus a functional-dependency set; well-typedness implies the well-behaved lens laws *(p.347-348, §3, §5)*.
- Accommodation of full nondegenerate relational structure including multi-attribute join, arbitrary functional dependencies (including non-key dependencies), and strict total/partial distinctions *(p.343)*.
- Use of *tree forms* — finite tree representations of relations consistent with a functional-dependency set — as a uniform substrate so that lenses on trees from prior work (Foster-Greenwald-Moore-Pierce-Schmitt) can be lifted to relations through canonical encodings *(p.346-347, §2.2-§4.2)*.
- Concrete put rules for σ, π, ⋈ that are derived to be the *unique* maximally-cooperative source updates respecting the declared functional dependencies, with side-conditions that determine totality/partiality *(p.348-352, §5.1-§5.4)*.

## Study Design (empirical papers)
*Not applicable — pure theory paper. No experimental evaluation or implementation benchmarks reported.*

## Methodology
- Define lenses abstractly as a `get`/`put` pair satisfying lens laws over source-state and view-state predicates *(p.347, §3)*.
- Augment relations with explicit *functional-dependency sets* so that types track integrity constraints *(p.345-347, §2.1, §3)*.
- Build a "tree form" interpretation: a relation R consistent with an FD set F can be encoded as a finite tree whose paths trace through key-dependency hierarchy; tree-set lenses then specialize to relational ones *(p.346-347, §2.2, §4.2)*.
- Define each relational primitive's `get` directly from standard relational algebra; *derive* the matching `put` so the lens laws hold under the FD typing assumption.
- For each primitive, prove (sketch) the well-behaved laws plus stronger PutPut where it holds; identify side-conditions and totality scope.

## Lens Laws (Round-Trip / Information-Preservation Criteria)

A lens `l: S ⇌ V` between sets `S` (sources) and `V` (views) consists of two functions:

$$
\text{get}_l : S \to V
$$

$$
\text{put}_l : V \times S \to S
$$

The first projects a source to its view; the second takes an updated view together with the original source and produces a new source *(p.347, §3)*.

### Well-behaved laws
A lens is **well-behaved** iff for all `s ∈ S` and `v ∈ V`:

$$
\text{put}_l(\text{get}_l(s),\, s) = s \quad\text{(GetPut)}
$$
*If you read the view and then put it back unchanged on top of the same source, the source must be unchanged. Forbids the lens from gratuitously losing source information when no view edit happened.* *(p.347)*

$$
\text{get}_l(\text{put}_l(v,\, s)) = v \quad\text{(PutGet)}
$$
*Whatever view you write must be exactly the view you read back. Forbids the lens from silently rejecting or distorting the view-update.* *(p.347)*

### Very well-behaved law
A lens is **very well-behaved** iff additionally:

$$
\text{put}_l(v',\, \text{put}_l(v,\, s)) = \text{put}_l(v',\, s) \quad\text{(PutPut)}
$$
*Successive puts are equivalent to the last put. The intermediate source state used when computing a chain of view-updates does not leak into the final source.* *(p.347)*

These three together form the canonical Foster-Greenwald-Moore-Pierce-Schmitt (FGMPS) lens-law family. Bohannon-Pierce-Vaughan adopt them verbatim from the tree-lens setting and apply them to relations *(p.347, §3)*.

### Total vs partial lenses
A lens is **total** when `get` and `put` are total functions on their declared types; **partial** when `put` may be undefined on some `(v, s)` pairs that violate side-conditions (e.g., a view update that would necessitate unrepresentable updates to fields the lens has hidden) *(p.347, §3)*.

### Why these laws matter for migration / non-commitment
- **GetPut** says identity-preserving roundtrips do not erode storage. A migration that "reads then writes" cannot lose data.
- **PutGet** says updates take effect deterministically — no silent dropping or duplication. A view update is a *commitment* about what the view should be.
- **PutPut** lets two staged migrations compose without remembering scratch source-state. Crucial when migrations are pipelined.

## Background (§2)

### 2.1 Relations
Schema `U` is a finite set of attribute names. Each attribute `A ∈ U` has a domain `dom(A)`. A *tuple* over `U` is a function `t: U → ⋃_A dom(A)` with `t(A) ∈ dom(A)`. A *relation* over `U` is a finite set of such tuples *(p.344)*.

For attribute set `X ⊆ U` and tuple `t`, the *projection* `t[X]` is `t`'s restriction to `X`. For a relation `R` over `U` and `X ⊆ U`, define:

$$
\pi_X(R) = \{ t[X] \mid t \in R \}
$$

$$
\sigma_P(R) = \{ t \in R \mid P(t) \}
$$

For a binary predicate `P` on tuples *(p.344)*.

**Natural join** of `R` (over `U`) and `S` (over `V`):

$$
R \bowtie S = \{ t \mid t \text{ over } U \cup V,\, t[U] \in R,\, t[V] \in S \}
$$
*(p.344)*

### 2.2 Functional dependencies and tree sets
A functional dependency `X → Y` (with `X, Y ⊆ U`) holds on `R` iff for all `t, t' ∈ R`, `t[X] = t'[X] ⇒ t[Y] = t'[Y]`. Write `R ⊨ F` when `R` satisfies every FD in set `F` *(p.345-346)*.

A *tree form* of FD set `F` is a strict partial order on attribute sets representing how `F` factors as a hierarchy of key/non-key relationships. Equivalently, an FD set `F` is in tree form when its closure under standard FD inference axioms admits a tree-shaped Bachman/dependency diagram. The authors note this is the standard "BCNF-like" decomposition where every non-trivial FD's left-hand side is a *superkey* of the relevant component. Tree-form FDs are central — the lens combinators are typed *only* on tree-form FD sets, and they explicitly preserve that tree-form structure *(p.346-347)*.

### Functions on FDs and tree forms (§4)
Two key meta-operations on FD sets used in put-rule derivations:

- **Outputs** `outputs(F, X)`: the set of attributes determined by `X` via `F`'s closure.
- **Tree-form refinement and revision rules**: the put functions are defined by case analysis over how a view-update changes the *attribute hierarchy* implied by the FDs. Figure on p.349 (rules `T-NEW`, `T-WEAKEN`, etc.) gives the inductive transformation. *(p.347-348, §4)*.

## Composite Lens Example (Figure 1, §2 walkthrough)

Source database has two relations: `Tracks` (Track, Date, Rating, Album, Quantity) and `Albums` (Album, Quantity). The composite lens applies sequentially *(p.345)*:

1. **Join Tracks and Albums on Album → Tracks1.** Get adds `Quantity` from Albums; Put on update propagates back into both source relations subject to the join's FD discipline.
2. **Drop Date determined by `(Track, unknown)` from Tracks1 → Tracks2.** Get is a projection that hides Date; Put restores Date from the original source on tuples that remain, and uses a default policy on newly-introduced tuples.
3. **Select Tracks2 where Quantity > 2 → Tracks3.** Get filters; Put writes back records that match the predicate, leaving non-matching source tuples alone (with detailed handling for newly-inserted view tuples that would not satisfy `Quantity > 2`).

Concrete update example: in the view, "Lullaby's Rating becomes 4," "Lullaby's Album becomes Disintegration," and "Trust" is deleted. The lens propagates each change back through the three stages, preserving the FDs in the source *(p.345, Fig. 1)*.

## Lens Primitives (§5) — `get` and `put` definitions

Throughout, lenses are typed by a *source-side relation predicate* `P_S` (which encodes both schema and FD set) and a *view-side predicate* `P_V`.

### 5.1 Selection lens (§5.1)
**Get:**

$$
\text{get}_{\sigma_P}(R) = \sigma_P(R)
$$
*The view contains exactly those tuples of the source satisfying P.* *(p.348)*

**Put:** Given updated view `V'` and original source `R`:

$$
\text{put}_{\sigma_P}(V', R) = (R \setminus \sigma_P(R)) \cup V'
$$

i.e. replace the satisfying-`P` portion of `R` with the new `V'`. **Side-conditions:**
- Every tuple in `V'` must satisfy `P`.
- Inserting a tuple `t ∈ V'` that does *not* match any source tuple must not violate the source's functional dependencies (concretely, must not duplicate keys with conflicting values).

When these side-conditions hold, the selection lens is well-behaved and *very* well-behaved (total on this domain, partial otherwise). *(p.348, §5.1)*

### 5.2 — (Authors' numbering: §5.1 Selection, §5.2 ...; the exact section labels in this version of the paper run Selection → Projection → Join.)*

### Projection lens (§5.3 in paper, "drop" syntax)
**Syntax** (informal): `drop A determined by (X, default-fn)` removes attribute `A` from the schema, where `X → A` is an FD in the source's FD set and `default-fn` provides values for `A` when new view tuples are inserted *(p.345, p.350)*.

**Get:**

$$
\text{get}_{\text{drop}}(R) = \pi_{U \setminus \{A\}}(R)
$$

*Project away the dropped attribute.*

**Put:** Given updated view `V'` (a relation over `U \ {A}`) and original source `R`:

For each tuple `v ∈ V'`:
1. If there is `t ∈ R` with `t[X] = v[X]`, take `A`-value from `t` (i.e., `A`-value for `v[X]` is preserved from the source).
2. Otherwise (new key `v[X]` not present in source), take `A`-value from `default-fn(v)`.

Then restrict to FD-consistent tuples:

$$
\text{put}_{\text{drop}}(V', R) = \{ \langle v, a \rangle \mid v \in V',\, a = \text{lookup}(v[X], R) \text{ or } \text{default}(v) \}
$$

The side-condition is that the rebuilt source must satisfy `F`; the projection lens is well-behaved when `X → A` is in `F`'s closure and the default function returns FD-consistent values. *(p.350-351, §5.3)*

### Join lens (§5.4)
Given source pair `(R₁, R₂)` over schemas `U₁, U₂` (where `U₁ ∩ U₂ ≠ ∅`):

**Get:**

$$
\text{get}_{\bowtie}(R_1, R_2) = R_1 \bowtie R_2
$$
*(p.351)*

**Put:** This is the combinator with the most delicate side-conditions. Given updated view `V'` over `U₁ ∪ U₂`:

$$
\text{put}_{\bowtie}(V', (R_1, R_2)) = (\pi_{U_1}(V'), \pi_{U_2}(V'))
$$
adjusted so that records of `R₁` (resp `R₂`) whose `U₁ ∩ U₂` keys have disappeared from the view are *retained* (left-join semantics) or *removed* (inner-join semantics) according to the lens variant used.

**Side-conditions:** `(U₁ ∩ U₂) → U₁` *or* `(U₁ ∩ U₂) → U₂` must be implied by the FDs (i.e., the join column functionally determines at least one side). This is the *predicate condition* under which join admits a well-behaved put. The paper distinguishes inner-join, left-outer-join, and right-outer-join lens variants; each has different side-conditions on which orphan tuples may be legally hidden in the source *(p.351-352, §5.4)*.

## Equations

### Selection get/put

$$
\text{get}_{\sigma_P}(R) = \{ t \in R \mid P(t) \}
$$

$$
\text{put}_{\sigma_P}(V', R) = (R \setminus \sigma_P(R)) \cup V'
$$
Where: `R` is the source relation, `V'` is the updated view, `P` is the selection predicate. Defined when every `t ∈ V'` satisfies `P` and the union preserves `R`'s FDs. *(p.348)*

### Projection (drop) get/put

$$
\text{get}_{\text{drop}_A}(R) = \pi_{U \setminus \{A\}}(R)
$$

$$
\text{put}_{\text{drop}_A}(V', R)(v) = \begin{cases} \langle v, R(v[X])[A] \rangle & \text{if } v[X] \in \pi_X(R) \\ \langle v, \text{default}(v) \rangle & \text{otherwise} \end{cases}
$$
Where: `A` is the dropped attribute, `X → A` is an FD in the source's FD set, `default` is a user-supplied function from `U \ {A}` tuples to `dom(A)` values. *(p.350)*

### Join get

$$
\text{get}_{\bowtie}(R_1, R_2) = \{ t \mid t \text{ defined on } U_1 \cup U_2,\, t[U_1] \in R_1,\, t[U_2] \in R_2 \}
$$
Where: `R₁, R₂` are the two source relations over `U₁, U₂`. *(p.344, p.351)*

### Lens laws

$$
\text{put}_l(\text{get}_l(s), s) = s
$$

$$
\text{get}_l(\text{put}_l(v, s)) = v
$$

$$
\text{put}_l(v', \text{put}_l(v, s)) = \text{put}_l(v', s)
$$
Where: `s ∈ S` (source domain), `v, v' ∈ V` (view domain). The first two define *well-behaved*; all three define *very well-behaved*. *(p.347)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Source schema | U | set of attributes | — | finite | p.344 | Universe of attribute names |
| Source FD set | F | set of FDs | — | tree-form FDs | p.346 | Must be in tree form for typing |
| Default-value function | default | function | user-supplied | — | p.350 | Used by projection lens for new view rows |
| Selection predicate | P | tuple-Boolean | — | decidable | p.348 | Used to type σ-lens; both V' and R\σP(R) must be P-disjoint |
| Join key set | U₁ ∩ U₂ | attribute set | — | nonempty | p.351 | Must functionally determine at least one side under F |

## Effect Sizes / Key Quantitative Results
*Not applicable — no empirical results reported.*

## Methods & Implementation Details
- Source representation: relations augmented with explicit functional-dependency sets `(R, F)`. The FD set is part of the typing predicate, not metadata to be inferred. *(p.345-346)*
- Tree-form FDs: the typing system requires FDs to admit a tree decomposition; this gives a canonical "scaffold" against which views and updates align. *(p.346-347)*
- Tree-form revision rules: fixed inductive system (§4) that updates the FD-tree as a view-update propagates; the put rules call this system to compute the new source-side FD set when needed. *(p.347-348, §4)*
- Each combinator's `put` is the *unique* well-behaved put given the matching `get` and the FD typing — uniqueness is a consequence of the combination of GetPut and the FD constraints. *(p.348, §5)*
- Composition: `put` on a pipeline `l₁ ; l₂` is computed by passing the updated outermost view through `l₂.put`, then through `l₁.put`, threading the original source state through both stages. The composite of well-behaved lenses is well-behaved by construction. *(p.345 walkthrough; standard FGMPS result.)*
- Partial lenses: the paper explicitly accepts partial puts when side-conditions cannot be satisfied; the *type* of a lens limits where it is total. *(p.347)*

## Algorithms / Protocols

### Composite lens evaluation (Figure 1, p.345)

**Inputs:** Source `(Tracks, Albums)`; Composite lens `l = σ_{Q>2}(drop_{Date}(Tracks ⋈ Albums))`.

**get pipeline:**
1. `T₁ = Tracks ⋈ Albums on Album` (join lens).
2. `T₂ = π_{¬Date}(T₁)` (projection/drop lens).
3. `T₃ = σ_{Quantity>2}(T₂)` (selection lens).
4. Return `T₃` as the user-visible view.

**put pipeline (given updated view `T₃'`):**
1. `T₂' = put_{σ_{Q>2}}(T₃', T₂)` — re-attach hidden non-matching rows.
2. `T₁' = put_{drop_{Date}}(T₂', T₁)` — restore Date from original or default function.
3. `(Tracks', Albums') = put_{⋈}(T₁', (Tracks, Albums))` — split back into the two source relations, preserving FDs.
4. Verify that the new source still satisfies the source FD set; if not, the composite put is undefined. *(p.345-346)*

## Figures of Interest
- **Fig. 1 (p.345):** "A Composite Lens." Shows original `Tracks` and `Albums` tables; intermediate views `Tracks1`, `Tracks2`, `Tracks3`; an explicit view-update ("Lullaby's Rating becomes 4," "Lullaby's Album becomes Disintegration," "Trust deleted"); and the resulting updated source. The figure traces the put-pipeline visually and is the primary intuition-builder for the paper.

## Results Summary
- σ, π (drop), and ⋈ are each given concrete put-rules that satisfy GetPut, PutGet, and (for σ and drop) PutPut under explicit FD-side-conditions *(§5)*.
- The lens laws *force uniqueness* of the put-rule given the get and the FD typing; this is the "design rationale" sense in which the paper's puts are not arbitrary but determined.
- Composite lenses built from these primitives inherit well-behavedness, giving a small but non-trivial fragment of relational-algebra view-update with formal correctness *(p.345-346)*.

## Limitations
- The language is not relationally complete — only σ, π (single-attribute drop variant), and ⋈ are covered. Set operations (∪, ∩, \), aggregation, and multi-attribute projections beyond the dropping form are not supported in this paper *(p.352, §6)*.
- FDs must be in tree form. Arbitrary FD sets (where the implication graph is not tree-shaped) fall outside the typing system *(p.346)*.
- Side-conditions for join (functional determination of at least one side by the join key) restrict applicability; non-key joins are excluded *(p.351-352)*.
- Several primitives are partial: when side-conditions fail, `put` is undefined and the composite update is rejected. The paper does not provide a mechanism for "best-effort" partial propagation *(p.347)*.
- No implementation reported; the work is formal-semantic only *(p.352, §6)*.

## Arguments Against Prior Work
- **Bancilhon-Spyratos "view complement"** approach: the authors note that view-complement-based methods can determine *whether* a class of view updates is uniquely translatable, but they do not give the database designer a *language* in which to construct an updatable view-and-update-policy together. *(p.352, §7)*
- **Cosmadakis-Papadimitriou** projection-key methods: these are restricted to projections; do not cover the joint design of multi-stage view-update propagation. *(p.352, §7)*
- **Dayal-Bernstein "view update"**: relies on system-chosen update translations that may surprise the user. The lens-language alternative makes the update policy *explicit syntax* in the view definition. *(p.343, §1; p.352, §7)*
- **Gottlob-Paolini-Zicari** (relational lenses extending Bancilhon-Spyratos): they establish formal equivalences but do not connect to a syntactic combinator language. *(p.352, §7)*
- **Foster et al. (FGMPS) tree lenses** (predecessor work by some of the same authors): handles trees, not relations; this paper extends the FGMPS lens-law framework into the relational setting with FD typing. *(p.347, p.352)*

## Design Rationale
- **Why FDs in the type, not the data?** Because GetPut/PutGet uniqueness only holds modulo the integrity constraints; without explicit FDs, multiple incompatible put-rules satisfy the laws. Lifting FDs into the type makes the put-rule deterministic and statically checkable. *(p.346, §2.2)*
- **Why tree-form FDs only?** Tree form gives a canonical decomposition aligning view structure with source-side hierarchy; this is what makes the tree-set / relation correspondence work and lets the prior FGMPS tree-lens machinery be reused. *(p.346-347, §4.2)*
- **Why partial lenses, not "best-effort" puts?** A best-effort put cannot satisfy PutGet without lying about what the update was. Partiality preserves the lens-law guarantee that successful puts are exactly faithful. *(p.347, §3)*
- **Why a combinator language rather than an arbitrary higher-order put-language?** Combinators give compositional reasoning: a composite lens's well-behavedness follows from each primitive's well-behavedness, with no further global proof obligation. The price is restricted expressiveness. *(p.343, §1; p.345)*

## Testable Properties
- For every well-typed relational lens `l` over (P_S, P_V) and every `s` with `P_S(s)`: `put_l(get_l(s), s) = s` (GetPut). *(p.347)*
- For every well-typed relational lens `l` and every `(v, s)` with `P_S(s)`, `P_V(v)`, and `(v, s)` in `put`'s domain: `get_l(put_l(v, s)) = v` (PutGet). *(p.347)*
- For very-well-behaved lenses: `put_l(v', put_l(v, s)) = put_l(v', s)` (PutPut). *(p.347)*
- Selection lens: total iff every tuple of `V'` satisfies `P` and `(R \ σ_P(R)) ∪ V'` satisfies the source FD set. *(p.348)*
- Projection (drop A determined by X) lens: well-defined iff `X → A` is implied by the source FD set and the default function returns FD-consistent values. *(p.350)*
- Join lens: well-defined iff `U₁ ∩ U₂` functionally determines at least one of `U₁, U₂` under the source FD set. *(p.351)*
- Composite lens well-behavedness: compositional — composite is well-behaved iff each component is. *(implicit, FGMPS-standard)*
- After a put, the resulting source must satisfy the source FD set; otherwise put is undefined. *(p.348-352)*

## Relevance to Project

**Direct relevance to propstore's migration framework and non-commitment principle.**

- propstore's design checklist forbids storage gates and storage mutation by heuristic. Lens laws give a formal account of when a *migration* (a mapping between two storage representations) preserves information: GetPut ensures a roundtrip through the new representation back to the old does not lose data; PutGet ensures the new representation faithfully reflects authored updates.
- The non-commitment principle says "do not collapse disagreement in storage unless the user explicitly requests a migration." Bohannon-Pierce-Vaughan provide the *test* a migration must pass before propstore should accept it as collapsing-but-faithful: well-behavedness against an explicit FD-typed source/view pair. If a proposed migration cannot be expressed as a well-behaved lens, it loses information and must be refused.
- Tree-form FDs map naturally onto propstore's tree-shaped concept inventories (lemon-style entry/form/sense hierarchies, Pustejovsky qualia trees, Dowty proto-role bundles). The lens-typing discipline is therefore directly applicable to propstore's structured semantic core.
- The paper's compositional combinator pattern matches propstore's render-time policy stack: render layers can be designed as well-behaved lenses over the underlying corpus, so that "views of belief" are formally faithful to source claims.
- The σ/π/⋈ primitives are the minimal kernel; later lens work (Greenwald, Hofmann-Pierce-Wagner, Hu-Mu-Takeichi, etc.) extends this. Bohannon 2006 is the citable foundation for any propstore-internal claim that "this transformation preserves information."

## Open Questions
- [ ] What does propstore's analogue of an FD set look like for the ATMS-bundled claim graph? (Likely: the lemma "every claim has a single context" etc.)
- [ ] Can the lens framework be extended to handle propstore's *probabilistic* annotations (subjective-logic opinions) without giving up well-behavedness? (Likely requires a stochastic-lens generalization — see Foster et al. on "matching lenses" and probabilistic bidirectional transformations.)
- [ ] How does this interact with the AGM revision layer? AGM gives belief-set revision; lenses give data-shape preservation. They sit at different abstraction levels but might compose.
- [ ] propstore's content-addressed sidecar is rebuilt only when source changes; lens get/put gives a discipline for *explaining* what changes the rebuild should propagate. Worth investigating.

## Related Work Worth Reading
- Foster, Greenwald, Moore, Pierce, Schmitt: tree lenses (cited as the predecessor with the well-behaved law family — TOPLAS 2007 / POPL 2005). Foundational for the lens-law machinery.
- Bancilhon, Spyratos: "Update semantics of relational views" (1981) — the view-complement approach this paper supersedes.
- Cosmadakis, Papadimitriou: updatability of relational views.
- Dayal, Bernstein: view-update problem framing.
- Gottlob, Paolini, Zicari: prior "relational lenses" terminology.
- Hofmann, Pierce, Wagner: subsequent "edit lenses" — finer notion of update beyond state-based puts.
- Hu, Mu, Takeichi: bidirectional XML transformation, related compositional approach.
- Greenwald: dissertation expanding on lens combinators.

## Collection Cross-References

### Already in Collection
- (none — none of the cited references appear in the current collection)

### New Leads (Not Yet in Collection)
- Foster, Greenwald, Moore, Pierce, Schmitt (2005) — "Combinators for Bi-Directional Tree Transformations: A Linguistic Approach to the View Update Problem" (POPL) — the predecessor "tree lens" paper that establishes the well-behaved/very-well-behaved lens laws this paper inherits and lifts to relations. **Highest priority** for the migration-framework batch — without it, the lens-law citation chain is incomplete.
- Bancilhon, Spyratos (1981) — "Update semantics of relational views" (TODS) — the view-complement formulation Bohannon-Pierce-Vaughan position themselves against. Background reading for why the lens framework chose syntactic combinators.
- Dayal, Bernstein (1982) — "On the correct translation of update operations on relational views" (TODS) — paired with Bancilhon-Spyratos as the prior-art landscape.
- Hegner (2004) — "An order-based theory of updates for closed database views" (AMAI) — closer in structure to lenses than the complement-based methods; useful comparison.
- Keller (1985) — "Algorithms for translating view updates to database updates for views involving selections, projections, and joins" (PODS) — algorithmic predecessor for the same σ/π/⋈ primitives. Direct comparison point on update determinacy.
- Lechtenbörger (2003) — "The impact of the constant complement approach towards view updating" (PODS) — most recent (pre-2006) prior on view-update semantics.

### Supersedes or Recontextualizes
- (none — this paper extends FGMPS tree lenses into the relational setting but does not supersede any current collection paper; it does establish the formal account that propstore's migration discipline cites for information-preservation criteria, recontextualizing Roddick's "lossless schema integration" criterion as a concrete lens-law obligation)

### Cited By (in Collection)
- [A Component-Based Framework For Ontology Evolution](../Klein_2003_ComponentBasedFrameworkOntologyEvolution/notes.md) — cites this paper conceptually (not citationally — Klein-Noy 2003 predates this 2006 paper) for the *bidirectional, well-typed, composable transformations between database states* design point. Klein/Noy's basic change operations are similarly typed and reversible (modify ops carry old+new for reversal). Different formalism, same engineering discipline: typed reversible transformations as the canonical migration primitive. Lenses give an algebraic story Klein/Noy lack.
- [A Nanopass Infrastructure for Compiler Education](../Sarkar_2004_Nanopass/notes.md) — cites this paper conceptually for the same-design-point observation that Sarkar's typed compiler-pass DSL and Bohannon's typed view-update DSL occupy the same niche: small typed combinator languages with statically-checked semantic laws. Lens laws are the bidirectional analogue of Sarkar's pass-grammar conformance.

### Conceptual Links (not citation-based)
- [A Nanopass Infrastructure for Compiler Education](../Sarkar_2004_Nanopass/notes.md) — STRONG: Sarkar, Waddell, Dybvig define a small typed combinator DSL (`define-language`, `define-pass`, language-inheritance via `extends`+/`-`, plus a pass expander) for compiler IR transformations, with statically-checked grammar conformance between every pair of intermediate languages. Relational lenses occupy the same design point — small typed combinator DSLs with statically-checked semantic laws — for the updatable-views problem. Lens laws (GetPut, PutGet, PutPut) are the bidirectional analogue of nanopass's per-pass typed input/output grammar plus reference-implementation equivalence check. A propstore migration framework that wants bidirectional (rollback-capable) schema migrations would naturally combine lens combinators for the get/put discipline with the nanopass pass-expander pattern for trivial structural recursion.
- [A Component-Based Framework For Ontology Evolution](../Klein_2003_ComponentBasedFrameworkOntologyEvolution/notes.md) — STRONG: Klein/Noy frame ontology evolution as typed atomic change operations with old-state/new-state reversal data; lenses frame view-update as paired get/put with explicit FD typing. Different domains (ontologies vs relational databases), same architectural commitment: typed bidirectional transformations are the *only* trustworthy migration primitive. Klein/Noy lack the algebraic well-behaved/very-well-behaved law structure; lenses lack Klein/Noy's component-targeted change-operation typology. A propstore migration framework needs both.
- [A Survey of Schema Versioning Issues for Database Systems](../Roddick_1995_SurveySchemaVersioningIssues/notes.md) — STRONG: Roddick formalizes "lossless schema integration" via Miller-Ioannidis-Ramakrishnan (1993) information capacity; lens laws give the operational test for that lossless-ness. GetPut and PutGet *are* the formal information-preservation criterion Roddick's vocabulary points at without specifying. A migration that satisfies the lens laws is a lossless schema-evolution step in Roddick's sense; a migration that does not is at most a partial schema-versioning step.
- [Preserving mapping consistency under schema changes](../Velegrakis_2004_PreservingMappingConsistencyUnder/notes.md) — STRONG: Velegrakis, Miller, Popa give the *forward* consistency criterion for inter-schema mappings under schema evolution (`A_s ∈ LA(S') ∧ A_t ∈ LA(T')`, where `LA(X)` is the set of maximal logical associations of `X` after chasing with key/FK constraints). Relational lenses give the *round-trip* information-preservation laws (GetPut/PutGet) for the same setting. Both papers depend on functional-dependency / key-constraint sets being explicit and propagated through the transformation, and both decompose complex transformations into a small typed operator set whose well-typedness statically discharges the global property. ToMAS goes further by handling cross-mapping consistency (one schema change affects many dependent mappings), while lenses go further by giving the bidirectional law structure. A propstore migration framework needs both: lenses for the round-trip law on each individual projection, ToMAS-style operator decomposition for the cross-projection consistency when the source schema changes.
