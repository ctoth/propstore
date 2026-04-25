---
title: "Preserving mapping consistency under schema changes"
authors: "Yannis Velegrakis, Renée J. Miller, Lucian Popa"
year: 2004
venue: "The VLDB Journal 13:274-293"
doi_url: "https://doi.org/10.1007/s00778-004-0136-2"
pages: "274-293"
affiliations: "University of Toronto; IBM Almaden Research Center"
note: "Edited by M. Carey. Received Jan 13, 2004 / Accepted Mar 26, 2004 / Published online Aug 12, 2004"
produced_by:
  agent: "claude-opus-4-7-1m"
  skill: "paper-reader"
  status: "stated"
  timestamp: "2026-04-25T08:45:19Z"
---
# Preserving mapping consistency under schema changes

## One-Sentence Summary
A framework and tool (ToMAS) that detects when schema changes leave inter-schema mappings inconsistent and incrementally rewrites those mappings to remain semantically valid under the modified schemas, preserving user-modeled mapping choices and ranking candidate rewritings by closeness to prior semantics. *(p.274)*

## Problem Addressed
Mappings between heterogeneous data sources (relational, XML, etc.) are specified as transformation queries that depend on the structure and constraints of the source/target schemas. When a schema changes structurally, semantically, or in its constraints, dependent mappings can become inconsistent — they may reference moved/renamed elements, drop key dependencies, or produce data not consistent with the modified target. Manually rewriting many mappings is infeasible because (i) there is no analytic record of which mappings are affected, (ii) candidate rewritings are not unique, and (iii) the user's prior semantic choices (which join, which optional structure) must be preserved. Existing approaches (view adaptation, view synchronization, schema integration) are local and do not handle structural changes that affect many mapping components simultaneously. *(p.274–275)*

## Key Contributions
- A novel framework for **incremental mapping adaptation** under schema evolution that handles both structural and constraint changes. *(p.275)*
- A **typed mapping language** based on nested relational structure, with mappings expressed as `foreach … exists … where …` constraints between source/target structural+logical associations. *(p.276–279)*
- A formal definition of **mapping consistency** (semantic validity) of a mapping with respect to a mapping system `⟨S, T, M⟩` via **structural** and **logical associations** (the latter induced by referential/key constraints). *(p.280)*
- An **evolution algorithm** comprising a small primitive set of schema operations (rename, copy, move, create, delete element; add/remove constraint) plus higher-level operations expressed in terms of primitives, each of which performs minimum-change rewriting per affected mapping. *(p.281–285)*
- A **ranking criterion** based on relative similarity of pre/post mapping element sets to choose among candidate rewritings, plus the **support** of a rewriting (its frequency across the affected mapping set). *(p.286–287)*
- The **ToMAS tool** (Toronto Mapping Adaptation System) with mapping analyzer, evolution engine, ranker, and pluggable schema wrappers (relational, XML), plus a graphical user interface; experiments on ProjectGrants, DBLP, TPC-H, Mondial, GeneX, and an IMDB physical-design case study. *(p.287–292)*

## Study Design
Not an empirical study in the clinical sense; this is a systems/algorithmic paper with an experimental performance evaluation.
- **Experimental subjects:** Five schemas — ProjectGrants (16 atomic, 6 corresp, 7 mappings), DBLP (88 [0 constraints], 6, 12), TPC-H (51 [10], 10, 9), Mondial (159 [15], 15, 60), GeneX (88 [9], 33, 2). *(p.288 Table 1)*
- **Procedure:** Two versions of each schema. From the initial version, a Clio-generated set of mappings is filtered to two intended-semantics mappings. A random sequence of schema changes is applied, with adaptation by ToMAS measured against a "from-scratch" Clio regenerate-and-pick alternative. *(p.288–289)*
- **Metric:** ToMAS Advantage = `1 − (mappings_generated_by_ToMAS / (mappings_generated_by_mapping_tool + correspondences))`. *(p.290)*

## Methodology
- A mapping system is a triple `⟨S, T, M⟩` with source schema `S`, target schema `T`, and a set of mappings `M` between them. Mappings are typed nested-relational queries `Q^S → Q^T` with `S` over the source and `T` over the target. *(p.276)*
- Mappings are expressed as constraints of the form `foreach X^S exists X^T where φ`, where `X^S` is a quantification over a source structural association, `X^T` over a target one, and `φ` is the mapping body equating projections via correspondences. *(p.279)*
- The **schema graph** is the basis for navigation: nodes are schema elements (with NRA types `Set | Tuple | Atomic`), edges are parent-child structural relationships and referential-integrity edges. *(p.277)*
- A **structural association** is a navigation path in the schema graph (set of variables introduced by `foreach` plus a body), and a **logical association** extends it via schema constraints (foreign keys / key dependencies) using a chase. *(p.279–280)*
- **Maximal logical associations** of a schema `S`, `LA(S)`, are the closure under all logical extensions of structural associations; the chase terminates because schemas have finite NRA constraint sets. *(p.280)*
- **Mapping consistency:** a mapping `m = ⟨A_s, A_t, ψ⟩` is **semantically valid** with respect to `⟨S, T⟩` iff `A_s ∈ LA(S)` (modulo dominance) and `A_t ∈ LA(T)`, and the body `ψ` is well-typed in the equality of correspondences. Equivalently, the mapping must be expressible over maximal logical associations of the *current* `S` and `T`. *(p.280)*
- The **evolution operators** (atomic + composite) are: `addCon`, `remCon`, `copyEl`, `moveEl`, `delEl`, `renEl`, `createEl`. Each operator detects the affected subset of mappings and rewrites them locally; an "evolution engine" composes these. *(p.281–285)*

## Key Equations / Statistical Models

### Mapping system definition
$$
\langle S, T, M \rangle \quad \text{where} \quad M \subseteq Q^S \times Q^T \times \Phi
$$
Where: `S` source schema, `T` target schema, `M` set of mappings. Each mapping is a triple `⟨A_s, A_t, ψ⟩` with `A_s` a source association, `A_t` a target association, `ψ` a body relating projections. *(p.276)*

### Mapping form
$$
\textbf{foreach}\ X^S\ \textbf{exists}\ X^T\ \textbf{where}\ \varphi
$$
Where: `X^S` quantifies a tuple of variables over a source structural/logical association, `X^T` over a target one, `φ` is a conjunction of equalities between correspondences applied to the variables. *(p.279)*

### Mapping consistency (semantic validity)
$$
m = \langle A_s, A_t, \psi \rangle \in M \text{ is valid} \iff A_s \trianglelefteq A^*_s \in LA(S) \land A_t \trianglelefteq A^*_t \in LA(T) \land \text{type-correct}(\psi)
$$
Where: `LA(X)` is the set of maximal logical associations of schema `X`; `⊴` denotes dominance (extension by schema constraints); type-correctness checks each correspondence pair has compatible NRA types. *(p.280)*

### Relative similarity for ranking
$$
S(m_1, m_2) = \frac{|\,\text{elements}(m_1) \cap \text{elements}(m_2)\,|}{p_1 \cdot |\text{elements}(m_1)| + p_2 \cdot |\text{elements}(m_2)|}
$$
Where: `m_1, m_2` are two mappings; `p_1, p_2` are user-tunable weights with `p_1 + p_2 = 1` controlling whether to bias toward elements common to many mappings vs. elements specific to a particular mapping. The relative similarity is symmetric when `p_1 = p_2 = 0.5`. *(p.286–287)*

### Support of a rewriting
$$
L_M(m) = \frac{\sum_{m' \in M} S(m, m')}{|M|}
$$
Where: `M` is the set of mappings being adapted (the evolution batch), `S(m, m')` is the relative similarity above. The support is used as a tie-breaker among candidate rewritings — a rewriting that is a higher-support choice across the batch is ranked above one specific to a single mapping. *(p.287, eq. 2)*

### ToMAS Advantage (experimental metric)
$$
\text{Advantage} = 1 - \frac{\text{mappings generated by ToMAS}}{\text{mappings generated by mapping tool} + \text{correspondences}}
$$
Where: numerator counts mappings the user must browse with ToMAS; denominator counts the user effort under the from-scratch alternative (rewrite all correspondences, browse Clio-generated mappings). Advantage of `0.7` means `70%` user-effort savings. *(p.290)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Similarity weight (mapping 1) | p_1 | — | 0.5 | (0, 1) | p.286 | Bias toward common elements |
| Similarity weight (mapping 2) | p_2 | — | 0.5 | (0, 1) | p.286 | Constraint p_1 + p_2 = 1; symmetric ranking when equal |
| Worst-case complexity (chase + LA) | — | — | — | O(k^L · 2^k · log k * n) | p.287 | n schema size; k max degree of element; L number of mappings, per Maier et al. [26] |
| Test schema sizes (atomic elements) | — | — | — | 16–159 | p.288 | ProjectGrants 16, DBLP 88, TPC-H 51, Mondial 159, GeneX 88 |
| Test schema constraint counts | — | — | — | 0–15 | p.288 | Bracketed values in Table 1 |
| Test mapping counts | — | — | — | 2–60 | p.288 | Per Table 1, last column |
| Random schema-change sequence length | — | — | — | up to 17 | p.290 Fig. 9 | x-axis of advantage curve |
| Average adaptation time (any operator) | — | ms | < 1000 | — | p.289 Fig. 8 | Most operators well under 1s except large-schema constraint removal |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| GeneX, large mapping (29 joins), constraint removal | mean adaptation time | > 1000 ms | — | — | Worst case among tested operators | p.289 |
| ToMAS Advantage, ProjectGrants after 8 changes | unitless | ≈ 0.46 | — | — | Small-schema fully restructured | p.290 Fig. 9 |
| ToMAS Advantage, Mondial after 17 changes | unitless | ≈ 0.95 | — | — | Large-schema, modest evolution | p.290 Fig. 9 |
| ToMAS Advantage, GeneX after 17 changes | unitless | ≈ 0.95 | — | — | Largest mapping count | p.290 Fig. 9 |
| AddCon time, GeneX | ms | ~720 | — | — | Constraint addition involves chase | p.289 Fig. 8 |
| RemCon time, GeneX | ms | ~720 | — | — | Constraint removal: structural assoc reconstruction + chase + subsumption | p.289 Fig. 8 |
| DelEl time, Mondial | ms | ~480 | — | — | Highest among DelEl tests | p.289 Fig. 8 |
| RenEl time | ms | < 50 | — | — | Cheap across all schemas | p.289 Fig. 8 |
| CreateEl time | ms | < 50 | — | — | No mapping update; only type-check | p.289 Fig. 8 |

## Methods & Implementation Details

### Schema model *(p.277)*
- Types: `Type ::= Set | Tuple | Atomic`. Sets contain typed elements; Tuples have named fields with typed values; Atomics are leaves with NRA-compatible types (Int, String, etc.).
- A schema is a tree of types extended with referential-integrity edges (foreign keys) — together this is the **schema graph**.
- A schema element is identified by a path expression (a query over the root element). Schema elements may be optional or chosen from alternatives (`choice`).

### Mapping language *(p.279)*
- A mapping is a constraint `foreach X^S exists X^T where φ` expressing that for every binding of source variables `X^S` satisfying associated source predicates, there must be a binding of target variables `X^T` satisfying target predicates and the equality body `φ`.
- `φ` is a conjunction of equalities of element projections via **correspondences** (atomic-to-atomic identifications).

### Structural associations *(p.279)*
- Definition 11: A structural association is a navigation in the schema graph, captured as a `foreach`-clause introducing a tuple of variables along the structural parent-child edges only.
- Two structural associations are equal when they introduce the same variable bindings up to renaming.

### Logical associations *(p.279–280)*
- Definition 12: A **logical association** extends a structural association by **chasing** with the schema's NRA constraints (key, foreign key, inclusion). Each chase step joins the structural association with another structural association along an FK edge.
- Definition 13: `LA(S)` is the set of all **maximal logical associations** of `S` — those closed under further chasing. Maximality is well-defined because the chase terminates (Maier–Mendelzon–Sagiv [26]).

### Mapping consistency check *(p.280, Defn 14)*
- A mapping `m = ⟨A_s, A_t, ψ⟩` over `⟨S, T⟩` is consistent iff `A_s` is dominated by some maximal logical association of `S`, `A_t` is dominated by some maximal logical association of `T`, and `ψ` is well-typed (each correspondence equates projections of compatible NRA types).

### Atomic schema-evolution operators *(p.281–285)*
1. **Add Constraint** (`addCon`): A new constraint `C` (FK or key) is added. For each affected mapping containing a structural association `A` covered by the new constraint's domain, chase `A` with `C` to either obtain a new logical association `A^L` (then re-emit `m` with `A^L`) or detect that the result is already dominated (drop the redundant rewriting). May produce additional rewritings if `C` is non-functional. *(p.281–282 Algorithm 1)*
2. **Remove Constraint** (`remCon`): The reverse — undo prior chasing. The structural associations that the removed constraint was used to derive are re-emitted; rewritings whose body depended on the removed FK are dropped. *(p.282–283 Algorithm 2, Example 8)*
3. **Copy Element** (`copyEl`): Duplicate an element to a new location (with a fresh structural copy and any constraints chosen to be copied). For each mapping that referenced the old element, possibly emit an adapted rewriting using the new copy. *(p.283)*
4. **Move Element** (`moveEl`): Adapt mappings as if the element were renamed in its old location and a new element of the same name appeared in the new location. Implemented as a composition of copy + delete + recompute. *(p.283–284)*
5. **Create Element** (`createEl`): No mappings are updated; only a type-check is performed before insertion. *(p.288, p.289)*
6. **Delete Element** (`delEl`): First remove correspondences and constraints using the element, then drop mappings that referenced it; cost is at least as much as constraint removal. *(p.284, p.289)*
7. **Rename Element** (`renEl`): A simple syntactic rename of the element wherever it appears in mappings, with no chasing. Cheap. *(p.285)*

### Adapting schema-constraint changes *(p.285)*
- **Adding a constraint**: chases at most along one new join step per affected structural association; uses the schema graph + structural-association cache.
- **Removing a constraint**: requires reconstructing the structural-association set, chasing, and subsumption checking against affected logical associations — empirically the most expensive operator on most schemas (Fig. 8).

### Adapting structural changes *(p.285)*
- For each move/copy/rename of element `e` to `e'` in a new location, the algorithm walks every mapping that had a `foreach` introducing a variable for `e`, replaces the variable with one for `e'` (or with two: one in the old location, one in the new), and emits multiple candidate rewritings. *(p.285)*

### Pseudo-code structure *(p.281, 283)*
- `Algorithm 1` (constraint addition):
  1. For each mapping `m ∈ M` containing a structural association `A`:
  2. Try to chase `A` with the new constraint `C`.
  3. If chase yields a strictly stronger association `A^L`, emit `m'` = same `m` but with `A^L` as `A_s` (or `A_t`).
  4. If the chase result is already dominated by an existing association, do nothing.
- `Algorithm 2` (constraint removal):
  1. Identify the affected mappings (those with associations whose body depends on `C`).
  2. Recompute structural associations for the affected schemas.
  3. Re-chase with the remaining constraints; for each newly maximal association, emit a candidate rewriting.
  4. Drop rewritings whose bodies cannot be expressed without `C`.

### Mapping ranking *(p.286–287)*
- After adaptation produces a set of candidate rewritings, the **ranker** scores each candidate against the original mapping using the relative-similarity formula above, optionally aggregated with the support `L_M(m)` across the batch.
- Higher-support, higher-similarity rewritings are returned first to the user.

### Tool architecture *(p.288, Fig. 6)*
- **Wrapper** layer (relational and XML implementations) imports schemas/mappings into the internal NRA representation.
- **Mapping Analyzer** computes structural & maximal logical associations, also identifies which existing-mapping associations are *user associations* (chosen by the user vs. derived by the chase). User associations are preserved verbatim under evolution.
- **Evolution Engine** runs the per-operator algorithms.
- **Ranker** orders candidate rewritings.
- **Graphical user interface** (Fig. 7) shows source and target schema trees; user can edit schemas with operations like Add/Remove Constraint, Create/Remove/Rename/Copy/Move Element from a context menu.

### Edge cases / sensitivity analyses *(p.289–291)*
- DBLP (zero constraints) is fastest because there is no chase; large constraint counts (TPC-H) make the chase the cost driver.
- ProjectGrants is small but after 8 changes is essentially restructured, so ToMAS Advantage drops to ≈ 0.46 because preserving prior semantics is no longer meaningful — this is a soft limit of the technique.
- Larger schemas (Mondial, GeneX) preserve advantage even after 17 changes because realistic schema evolution rarely overhauls the original semantics.
- Compared to **Rondo** [29] (model-management compose-based mapping adaptation): ToMAS uses incremental ops directly, while Rondo needs an old-vs-new schema mapping then composes. Rondo can produce more rewritings because it ignores the existing mapping set; ToMAS preserves user choices but assumes incremental evolution is given.

## Figures of Interest
- **Fig. 1 (p.277):** Sample mapping system showing source schema (companies/contacts/projects), target schema (privProjects/companies/catalog), and three `foreach … exists … where` mappings between them.
- **Fig. 2 (p.279):** Source and target schemas as graphs.
- **Fig. 3 (p.281–284):** Examples of structural & logical associations and chases.
- **Fig. 4 (p.281):** Example of constraint addition affecting multiple mappings.
- **Fig. 5 (p.284):** Example of an element move under constraint changes.
- **Fig. 6 (p.288):** ToMAS architecture (Wrapper → Mapping Analyzer → Evolution Engine ↔ Graphical UI ↔ Ranker).
- **Fig. 7 (p.288):** ToMAS user interface with source (S:Red), target (T:Red), and context menu of operations (Add Constraint, Remove Constraint, Create Element, Remove Element, Rename Element, Copy Element, Move Element).
- **Fig. 8 (p.289):** Average adaptation time per operator across the five test schemas — bar chart.
- **Fig. 9 (p.290):** ToMAS Advantage as a function of the number of schema changes for ProjectGrants, DBLP, Mondial, TPC-H, GeneX.
- **Fig. 10 (p.290):** Two relational designs for the IMDB DTD (a vs b shredding methods) used in the physical-design case study.
- **Fig. 11 (p.291):** A representative XQuery mapping for IMDB with eight joins and nesting depth 2 — illustrates the complexity ToMAS abstracts away.

## Results Summary
- ToMAS adapts mappings in well under one second for the cheap operators (rename, create) and within a few hundred milliseconds for chase-driven operators on schemas of up to ~160 atomic elements with ~15 constraints. *(p.289 Fig. 8)*
- The largest-mapping case (GeneX, 29-join mapping) pushes adaptation past 1s on constraint-removal — a worst case driven by structural-association reconstruction. *(p.289)*
- ToMAS Advantage is sustained at 0.7–0.95 across most schemas after up to 17 schema changes; only fully restructured small schemas degrade the advantage to ~0.46. *(p.290 Fig. 9)*
- IMDB physical-design case study: ToMAS shreds an XML DTD into two alternative relational schemas, generating XQuery mappings (Fig. 11) automatically; the entire process is driven by the same evolution-operator framework. *(p.291–292)*

## Limitations
- Advantage degrades when the schema is small and many changes accumulate so that the evolved schema's semantics differ substantially from the original — preserving the original mapping no longer matches the user's intent. *(p.290)*
- The framework requires the schema-change sequence as input (incremental list of operators); when only an old/new schema pair is available, a different approach (Rondo's compose) is needed. ToMAS-vs-Rondo trade-offs deserve more investigation. *(p.290)*
- The mapping analyzer's chase has worst-case `O(k^L · 2^k · log k · n)` cost (Maier et al. [26]); large constraint sets and high-degree elements can be expensive. *(p.287)*
- Only relational and XML wrappers are implemented; other models would need new wrappers. *(p.288)*
- The current ranking is similarity- and support-based; richer probabilistic or learning-based ranking is left to future work. *(p.286–287)*

## Arguments Against Prior Work
- **View adaptation** (Bellahsene 1998 [3]; Mohania & Dong [23]; Mumick et al. [28]; Lerner [18,19]): adapts a single view at a time, locally; ToMAS handles structural changes that affect many components of a schema and many mappings simultaneously. *(p.275)*
- **View synchronization (EVE)** (Lee, Nica, Rundensteiner [33]): targets distributed view repair under autonomous source changes; assumes view definition does not need to capture user choices over alternative formulations. *(p.275)*
- **Schema evolution with simple primitives** (McBrien & Poulovassilis [27]; Spaccapietra & Parent [33]): catalog of primitives is similar but they do not provide automatic mapping-adaptation algorithms with consistency guarantees. *(p.276)*
- **Schema-mapping discovery from scratch** (Clio: Miller, Haas, Hernández [25]; Popa et al. [31]; Madhavan et al. [22]): regenerates the entire mapping set, so the user must re-pick the intended-semantics mapping each time — high effort and loses prior user choices. ToMAS directly preserves user choices. *(p.290)*
- **Model management compose** (Rondo: Melnik, Rahm, Bernstein [29]): produces an adapted mapping by composing the old-mapping with an old-to-new schema mapping; ignores the existing mapping set so may produce more rewritings than needed and does not preserve user choices unless those choices happen to be re-derivable. *(p.290)*
- **GAV/LAV/GLAV mappings** (Lenzerini [21]; Friedman/Levy/Millstein [12]): provide the formal substrate but do not address evolution under schema change. ToMAS targets GLAV-style mappings expressed in a nested NRA form. *(p.276)*

## Design Rationale
- **Why nested relational algebra?** Supports both relational and XML data uniformly via a `Set | Tuple | Atomic` type system, so the same evolution algorithms apply across data models. *(p.276–277)*
- **Why structural and logical associations?** A logical association captures all data semantics derivable from schema constraints (key, FK), so consistency reduces to membership in `LA(S)` after change. The structural/logical split lets the chase remain incremental. *(p.279–280)*
- **Why incremental evolution operators rather than full regeneration?** To preserve **user mapping choices** that are implicit in the existing mapping set — these are the choices not derivable from schema constraints alone (which mapping among many semantically valid alternatives the user picked). Regeneration loses those choices. *(p.290)*
- **Why a small primitive operator set with composites built from primitives?** Each operator implements minimum-change rewriting, and consistency is then preserved by induction on operator composition. Higher-level operations (e.g., `moveEl`) are programmed in terms of primitives. *(p.281–285)*
- **Why ranking + support rather than a single best?** Multiple rewritings can be semantically valid and the user must pick; ranking minimizes user browsing while support across the batch surfaces the systematically most consistent rewriting. *(p.286–287)*

## Testable Properties
- After any operator application, every emitted mapping must be in `LA(S') × LA(T')` for the modified schemas `S', T'`. *(p.280)*
- Constraint addition can only **strengthen** (add to) the set of logical associations; logical associations valid before the addition are valid after, plus the new chase results. *(p.281–282)*
- Constraint removal can only **weaken** the set of logical associations; mappings whose bodies cannot be re-expressed under the weakened constraint set must be dropped or re-cast over weaker structural associations. *(p.282–283)*
- Element renaming preserves the cardinality of the mapping set; it is a syntactic substitution. *(p.285, p.289 Fig. 8: lowest cost)*
- Element creation does not change any existing mapping; only a type-check on the inserted structure is performed. *(p.288–289)*
- Relative similarity `S(m_1, m_2)` is symmetric when `p_1 = p_2 = 0.5`. *(p.287)*
- Relative similarity is in `[0, 1]` when `p_1 + p_2 = 1` and `m_1, m_2` are drawn from the same element universe. *(p.287)*
- Higher support `L_M(m)` indicates a mapping that better preserves the *batch's* shared element vocabulary; the ranker prefers it. *(p.287)*
- Adaptation cost on a schema with no constraints (DBLP) is dominated by structural-association walking; with many constraints (TPC-H), it is dominated by the chase. *(p.289)*

## Relevance to Project
This paper formalizes the exact problem propstore hits during a concept-model migration: a single change in the source-of-truth schema (here, the rename of `concept` → `concepts` link) triggers a cascade of dependent rewrites — `documents.py` (the mapping carrier), sidecar projections (data-level views over the new structure), world model (constraint-bearing views), graph builders (structural associations), `aspic_bridge` (constraint-respecting projection into argumentation types), and web views (terminal projections). Velegrakis defines:
1. **Where the rewrites are required** — `LA(S)` membership after schema change. propstore can mirror this by computing the maximal logical associations of its YAML schemas (concept files, claim files, context files) and treating each downstream projection (sidecar SQL, graph builder, ASPIC+ types) as a mapping that must remain in `LA(target_layer)` after the source change. *(p.280)*
2. **A small, total operator set that any schema change can be decomposed into** — propstore migrations can be similarly decomposed into rename/move/copy/createEl/delEl/addCon/remCon, each with a known per-operator rewrite procedure for each downstream layer. This matches the propstore CLAUDE.md design principle that source-of-truth changes flow through projections. *(p.281–285)*
3. **A formal user-choice preservation discipline** — propstore's "non-commitment until render" requires that heuristically-collapsed migrations not destroy user-authored disagreement. Velegrakis's distinction between **user associations** (preserved verbatim) and **derived associations** (recomputed under chase) is a usable boundary: user-authored claim/concept choices are preserved, sidecar/graph/aspic projections are recomputed. *(p.288)*
4. **A ranking criterion for candidate rewritings** — When propstore must propose multiple migration paths (concept→concepts vs concept→list_of_concepts vs polysemous concept), the relative-similarity + support metric is directly applicable to rank candidate migrations by how well they preserve the *batch* of existing mappings. *(p.286–287)*
5. **A worked tool architecture** — Mapping Analyzer + Evolution Engine + Ranker + UI. propstore's analogues would be the schema/concept indexer + migration engine + proposal ranker + the CLI. *(p.288)*

## Open Questions
- [ ] How does ToMAS-style mapping adaptation interact with **probabilistic provenance** (propstore's typed provenance: measured, calibrated, stated, defaulted, vacuous)? Velegrakis is purely deterministic.
- [ ] Can the ranking criterion (relative similarity + support) be replaced or augmented by an argumentation-aware preference (e.g., a priority over rewritings derived from ASPIC+ priorities)?
- [ ] What is the analogue of `LA(S)` for **belief sets** (model-theoretic worlds in propstore)? `LA(S)` is over schema graphs + FKs; a belief-set analogue would chase over IC-merge constraints and entrenchment orderings.
- [ ] How does ToMAS handle composition with itself (multiple successive evolutions applied without intermediate user verification)? Their experiments suggest soft drift on small schemas.
- [ ] When does ToMAS fail to find any consistent rewriting? Velegrakis does not give a completeness theorem; they only describe the operator-by-operator algorithm.
- [ ] Can the framework be extended to **mappings between contexts** (propstore `ist(c, p)` lifting rules), not just between data schemas?

## Collection Cross-References

### Already in Collection
- (none — none of the cited references match papers currently in the collection)

### New Leads (Not Yet in Collection)
- Maier D, Mendelzon AO, Sagiv Y (1979) "Testing implications of data dependencies" [ref 26] — provides the chase algorithm and `O(k^L · 2^k · log k · n)` complexity bound that powers the logical-association computation; foundational if propstore implements a chase-style migration evaluator.
- Melnik S, Rahm E, Bernstein P (2003) "Rondo: a programming platform for generic model management" [ref 29] — the compose-based alternative to ToMAS; trade-offs are explicitly discussed in the paper and would be required reading before choosing a propstore migration approach.
- Popa L, Velegrakis Y, Miller RJ, Hernandez MA, Fagin R (2002) "Translating Web data" [ref 31] — defines the Clio mapping language ToMAS extends.
- Miller RJ, Haas LM, Hernandez M (2003) "Schema mapping as query discovery" [ref 25] — Clio mapping discovery; the from-scratch baseline ToMAS competes against.
- Velegrakis Y, Miller RJ, Popa L (2003) "Mapping adaptation under evolving schemas" (VLDB) [ref 36] — conference version of this paper.
- Madhavan J, Halevy AY (2003) "Composing mappings among data sources" [ref 24] — the compose operator behind Rondo.
- Lenzerini M (2002) "Data integration: a theoretical perspective" [ref 21] — GAV/LAV/GLAV foundations.
- Lerner BS (2000) "A model for compound type changes encountered in schema evolution" [ref 19] — schema-evolution operator catalog.

### Supersedes or Recontextualizes
- (none — this is a 2004 paper and does not supersede any current collection paper)

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)

**Migration framework family (all share the `migration-framework` tag):**
- [A Nanopass Infrastructure for Compiler Education](../Sarkar_2004_Nanopass/notes.md) — Sarkar's nanopass model is ToMAS's structural twin one layer up: each schema-evolution operator is a "nanopass" mapping a typed source-schema state to a typed target-schema state, with the same minimum-change discipline and the same operator-log-as-history pattern. Where ToMAS guarantees mapping consistency (membership in `LA(S')`), nanopass guarantees AST grammar conformance per pass; both are decomposing a single complex change into a sequence of typed minimum-change steps. (**Strong** — both are explicitly migration frameworks, both decompose change into a small operator set, both leave the operator log as the migration history.)
- [A Component-Based Framework For Ontology Evolution](../Klein_2003_ComponentBasedFrameworkOntologyEvolution/notes.md) — Klein and Noy define an ontology-change operator catalog (Basic vs Complex, parametrized by a single component) that is structurally analogous to ToMAS's atomic schema operators (rename/copy/move/create/delete element; add/remove constraint). Both papers argue that high-level evolutions must be expressible as compositions of typed atomic operations, and both treat the operation log as a first-class artifact of the evolution. ToMAS goes further by formalizing the consistency criterion (logical-association membership) and the cross-mapping rewriting algorithm. (**Strong** — same operator-decomposition methodology, complementary domains.)
- [Relational Lenses: A Language for Updatable Views](../Bohannon_2006_RelationalLensesLanguageUpdatable/notes.md) — Relational lenses give the *information-preservation* law (GetPut/PutGet) that any propstore mapping rewriting must satisfy in the round-trip direction; ToMAS gives the *consistency* criterion (membership in `LA(S')`) for the forward direction. Both papers depend on functional-dependency / key-constraint sets being explicit and propagated through the transformation, and both use a small combinator/operator set whose well-typedness statically discharges the global property. Different tradition (PL bidirectional transformations vs database mapping management), same empirical convergence on "constraint-aware compositional rewriting." (**Strong** — both are the foundation of propstore's migration framework; pairing them gives both directions of the round-trip law plus the schema-evolution decomposition.)

---

## Related Work Worth Reading
- Lenzerini (2002) "Data integration: a theoretical perspective" [21] — GAV/LAV/GLAV foundations.
- Friedman, Levy, Millstein (1999) [12] — GLAV mappings.
- Miller, Haas, Hernández (2003) "Schema mapping as query discovery" [25] — Clio.
- Popa, Velegrakis, Miller, Hernández, Fagin (2002) "Translating Web data" [31] — the mapping language ToMAS extends.
- Madhavan, Halevy (2003) "Composing mappings among data sources" [24] — the compose operator that Rondo uses.
- Melnik, Rahm, Bernstein (2003) "Rondo: a programming platform for generic model management" [29] — the alternative model-management approach to mapping adaptation.
- Lee, Nica, Rundensteiner (2002) "The EVE approach: view synchronization in dynamic distributed environments" [33] — view synchronization.
- Maier, Mendelzon, Sagiv (1979) "Testing implications of data dependencies" [26] — chase termination & complexity bound used here.
- Velegrakis, Miller, Popa (2003) "Mapping adaptation under evolving schemas" (VLDB) [36] — earlier conference version of this paper.
- Velegrakis (2004) PhD thesis "Managing schema mappings in highly heterogeneous environments" [35] — full technical report.
