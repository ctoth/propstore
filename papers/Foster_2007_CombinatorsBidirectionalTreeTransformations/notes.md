---
title: "Combinators for Bi-Directional Tree Transformations: A Linguistic Approach to the View Update Problem"
authors: "J. Nathan Foster, Michael B. Greenwald, Jonathan T. Moore, Benjamin C. Pierce, Alan Schmitt"
year: 2007
venue: "ACM Transactions on Programming Languages and Systems"
doi_url: "https://doi.org/10.1145/1232420.1232424"
pages: 64
---

# Combinators for Bi-Directional Tree Transformations: A Linguistic Approach to the View Update Problem

## One-Sentence Summary
Foster et al. define lenses as typed get/put pairs, give the GetPut/PutGet/PutPut laws, and build a combinator language for total, well-behaved bidirectional tree transformations that can preserve enough information for safe view update and synchronization. *(pp.1-4, pp.5-8)*

## Problem Addressed
The view-update problem asks how edits to an abstract view should be reflected back into an underlying concrete structure. The paper targets tree-structured data in Harmony, where browser bookmarks and other XML-like artifacts must be synchronized through common abstract views while preserving filtered-out concrete information where required. *(pp.2-5, pp.39-44)*

## Key Contributions
- Defines a semantic model of lenses as partial functions `get : V -> V` and `putback : V x V -> V`, then specifies well-behavedness through GetPut and PutGet laws. *(p.6)*
- Separates well-behavedness from totality so programs can be proved not to fail on their intended source/target types. *(pp.7-8)*
- Adds optional PutPut/very-well-behavedness, while explicitly not requiring it for several useful combinators because it is pragmatically too restrictive. *(pp.7, 22, 25, 48)*
- Uses an information ordering on lenses, complete partial orders, continuity, and fixed points to justify recursive lens definitions. *(pp.9-11)*
- Introduces a "missing" placeholder Omega so putback can create concrete data when no old concrete counterpart exists. *(pp.11-12)*
- Provides primitive and derived combinators for identity, composition, constants, hoist/plunge, fork/filter/prune/focus/rename/add/map/wmap/copy/merge, conditionals, list operations, flatten, pivot, and join. *(pp.12-49)*
- Shows a realistic bookmark synchronizer example where a concrete HTML bookmark tree is mapped into an abstract bookmark tree and updates are put back into the original concrete representation. *(pp.39-45)*
- Relates the lens laws to classical database view-update semantics, constant complement approaches, dynamic views, relational triggers, tree-view updates, reversible languages, and relational lenses. *(pp.49-57)*

## Methodology
The paper is a programming-language design and formal-semantics paper. It starts from view-update laws, defines semantic spaces and typing judgments for well-behaved and total lenses, then builds a typed combinator language. Proofs are mostly sketched in the article and deferred to an electronic appendix; the article states the lemmas and design rationale needed for implementation. *(pp.6-13, p.64)*

## Key Equations / Formal Laws

Lens definition:

$$
l = (l^{\uparrow} : V \rightharpoonup V,\; l^{\downarrow} : V \times V \rightharpoonup V)
$$

`l^up` is get and `l^down` is putback. *(p.6)*

Well-behavedness type obligations for `l in C <=> A`:

$$
l^{\uparrow}(C) \subseteq A
$$

$$
l^{\downarrow}(A \times C) \subseteq C
$$

These say get maps concrete values in `C` into abstract values in `A`, and putback maps abstract/concrete pairs back into `C`. *(p.6)*

GetPut:

$$
l^{\downarrow}(l^{\uparrow} c, c) = c
$$

For every `c in C`, immediately putting back the view obtained from `c` must return `c`. *(p.6)*

PutGet:

$$
l^{\uparrow}(l^{\downarrow}(a,c)) = a
$$

For every `(a,c) in A x C`, putting an abstract view into a concrete view and then getting must recover exactly `a`. *(p.6)*

PutPut:

$$
l^{\downarrow}(a', l^{\downarrow}(a,c)) = l^{\downarrow}(a', c)
$$

Sequential putbacks collapse to the last putback, modulo definedness. Lenses satisfying GetPut, PutGet, and PutPut are "very well behaved." *(p.7)*

Totality:

$$
C \subseteq dom(l^{\uparrow}) \quad \land \quad A \times C \subseteq dom(l^{\downarrow})
$$

Total lenses must be defined on all source and target cases covered by their type. This is the paper's runtime-safety property for synchronizers. *(pp.7-8)*

Information ordering:

$$
l \prec l' \iff dom(l^{\uparrow}) \subseteq dom(l'^{\uparrow}) \land dom(l^{\downarrow}) \subseteq dom(l'^{\downarrow}) \land l,l' agree on common domains
$$

`l'` is more informative than `l` when its get/putback are defined on larger domains and agree where both are defined. *(p.9)*

Fixed point for recursive lenses:

$$
fix(f) = \bigsqcup_n f^n(\bot)
$$

The least fixed point exists for continuous functions over the CPO of well-behaved lenses. *(p.10)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Lens universe | V | views | - | arbitrary structures; later finite deterministic trees | 5, 14 | The semantic model first abstracts from trees, then instantiates to finite edge-labelled trees. |
| Concrete type | C | set of views | - | subset of V | 6 | Source/concrete side of a lens type. |
| Abstract type | A | set of views | - | subset of V | 6 | Target/abstract side of a lens type. |
| Missing placeholder | Omega | special view | - | V extended to V_Omega | 11 | Used only as the second argument to putback to mean "create new concrete view." |
| Tree label set | N | names | - | countably infinite names | 14 | Child labels for deterministic finite trees. |
| Shuffle closure | T^diamond | set of trees | - | all domain-respecting shufflings of children | 21-22 | Required to type `map` soundly. |
| List type | [C] | set of list-encoded trees | - | empty list or cons cells with head in C | 29 | Lists are encoded using child labels `*h` and `*t`. |
| Prototype performance | - | appointments/minute | few thousand per minute | small demos | 59 | OCaml prototype sufficient for demos but not high-throughput biological data. |

## Effect Sizes / Key Quantitative Results

No empirical effect sizes are reported. The paper reports formal laws, type judgments, examples, and qualitative prototype experience. *(pp.1-64)*

## Methods & Implementation Details
- Harmony uses lenses to transform concrete native formats into common abstract trees, synchronize the abstract views, then put the changed abstract tree back through the original concrete tree to produce a new concrete file. *(pp.2-5, pp.39-40)*
- The authors emphasize state-based synchronization rather than trace-based update scripts: they care about final source/view states, not the exact sequence of user edits. *(p.5)*
- Each combinator carries a type declaration; the declaration is intended to guarantee well-behavedness and, for the main practical language, totality. Recursive totality sometimes requires global reasoning beyond local type checks. *(pp.3-4, pp.8-13)*
- Composition `l;k` gets through `l` then `k`, and putbacks through `k` then `l`, threading the intermediate view `l^up c`; the operator has separate typing rules for well-behaved and total arguments. *(pp.12-13)*
- `const v d` gets a constant `v`; putback restores old concrete `c` if present, otherwise creates default `d`. This is the primitive point where discarded information can be supplied on creation. *(pp.13-14)*
- Tree values are finite partial functions from names to subtrees; absent children read as Omega, and the empty tree `{}` is distinct from Omega. *(pp.14-15)*
- `hoist n` removes a top edge named `n`; `plunge n` adds one. These are root-structure operations used heavily in larger transformations. *(p.15)*
- `xfork pc pa l1 l2` splits a tree by concrete/abstract child-name partitions, applies two sublenses, and recombines results. `fork p` is the common case where partitions match. *(p.16)*
- `filter p d` keeps children in `p` and restores or defaults the filtered-out part on putback; `prune n d`, `add n t`, `focus n d`, `hoist_nonunique`, and `rename m n` are derived from fork/filter/hoist/plunge/const. *(pp.17-20)*
- `map l` applies a lens to each child subtree. Its typing requires source and target tree sets to have equal domains and be shuffle-closed; otherwise putback can create a tree outside the source type. *(pp.20-22)*
- `map` intentionally does not satisfy PutPut; the authors prefer `map` plus no PutPut over losing information by replacing projected concrete information with defaults. *(p.22)*
- `wmap m` maps each child name to a possibly different lens and is used to give field-specific transformations. *(p.23)*
- `copy m n` duplicates a child in get and discards one duplicate in putback; equality constraints are essential for PutGet because otherwise copied values can diverge. *(p.24)*
- `merge m n` is the inverse design point: it merges two concrete children into one abstract child and puts the updated abstract value back into both concrete locations, preserving an equality dependency. *(pp.25-26)*
- Concrete conditionals (`ccond`) branch on the concrete input; abstract conditionals (`acond`) branch on the abstract putback input and require disjoint target regions. The general `cond` combines both with fixup functions. *(pp.26-29)*
- List lenses encode lists as trees using `*h`/`*t`; derived list combinators include `list_map`, `list_reverse`, `group`, `concat`, and `list_filter`. *(pp.29-39)*
- `list_filter D E` projects out `E` elements in get and restores or interleaves `E` elements during putback while maintaining D/E constraints; its totality proof is more involved and uses Lemma 3.19. *(pp.35-39)*
- The bookmark example shows an incremental lens-development style: repeatedly hoist, rename, prune, map, and compose until a concrete HTML bookmark tree becomes an abstract bookmark tree, while putback restores concrete tags, attributes, and order where necessary. *(pp.39-45)*
- Relational data is represented as ordered lists of keyed records; `flatten`, `pivot`, and `join` make keyed structure explicit enough that synchronization can proceed child-wise. *(pp.45-49)*
- The relational `join` is inspired by full outer join and is bijective: no information is lost by get, so putback can ignore its old concrete argument. *(p.49)*
- Static typechecking was not fully implemented; the prototype does runtime checking/debugging, while the authors identify algebraic type inference/checking as future work. *(p.59)*

## Figures of Interest
- **Fig. 1 (p.16):** Visualizes `xfork` get as splitting a concrete tree into partitions, applying sublenses, and concatenating results.
- **Fig. 2 (p.40):** Abstract bookmark types (`ALink`, `AFolder`, `AContents`, `AItem`) used by the example.
- **Fig. 3 (p.41):** Sample Netscape-style HTML bookmark input.
- **Fig. 4 (p.41):** Concrete tree produced by the generic HTML reader.
- **Fig. 5 (p.42):** Concrete bookmark types for HTML encodings.
- **Fig. 6 (p.42):** Sample abstract bookmark tree.
- **Fig. 7 (p.44):** Full bookmark lens program with annotations for link/folder/item/bookmarks.
- **Fig. 8 (p.45):** Incremental development of the `link` lens.
- **Fig. 9 (p.46):** Example abstract-tree update and resulting concrete tree after putback.
- **Fig. 10 (p.58):** Harmony web demo screenshot.

## Results Summary
The formal result is a language of lens combinators whose stated type declarations are designed to guarantee GetPut/PutGet and, for intended usage, totality. The authors claim this is the first approach they know of that makes totality a primary goal while preserving compositional reasoning about lens programs. *(pp.8, 50, 58-59)*

## Limitations
- The paper does not present a complete automated typechecker; static checking is named as urgent future work. *(p.59)*
- Many proofs are deferred to an electronic appendix rather than included in the main article. *(p.4, p.64)*
- Some useful combinators (`map`, `flatten`, conditionals) do not satisfy PutPut, so very-well-behavedness is not the universal design target. *(pp.7, 22, 25, 48)*
- The tree model is finite, unordered, edge-labelled, and deterministic; ordered data and XML are encoded indirectly as lists. *(p.14, p.29)*
- The paper says its tree-level relational lenses are only a small step and not a full treatment of relational view update; Bohannon et al. 2006 is the more comprehensive relational proposal. *(p.49, p.56)*
- The OCaml prototype is fast enough for small demos but not yet for high-throughput applications such as biological databases. *(p.59)*

## Arguments Against Prior Work
- Classical view-update work often starts from a pre-existing get/query language and tries to infer putback; Foster et al. argue this creates ambiguity and instead design get and putback together in one language. *(pp.49-50, p.56)*
- Constant complement approaches provide uniqueness but can be too restrictive; open/dynamic view approaches are more permissive but may expose more of the underlying database to users. *(pp.50-52)*
- Program inversion and reversible languages require each step to be invertible and have no separate putback; lenses intentionally allow get to project away information as long as putback restores it from the old concrete value. *(pp.53-56)*
- XML view-update systems based on isomorphism between concrete XML and database objects avoid ambiguity but do not solve the case where the view deliberately hides concrete structure. *(pp.55-56)*

## Design Rationale
- Pairing get and putback in a single lens expression is the core design move: the update policy is not inferred later but authored with the projection. *(pp.3-4, p.50)*
- Type declarations are used as design constraints, not just documentation; they helped expose design mistakes early and structure compositional reasoning. *(pp.12-13, p.43, p.58)*
- Omega gives a disciplined creation story: when there is no old concrete tree, putback receives a distinguished missing value and specific combinators decide how defaults are introduced. *(pp.11-12, pp.22-23)*
- The language favors GetPut and PutGet over universal PutPut because many practical transformations need to preserve old concrete information even when multiple putbacks would not collapse. *(pp.7, 22, 48)*
- Relational keys should be made structurally obvious before synchronization; `flatten`, `pivot`, and `join` are used to align by key rather than by arbitrary order. *(pp.46-49)*

## Testable Properties
- A propstore projection lens must satisfy GetPut: rendering/projecting a stored object and putting that view back into the same object returns the original object. *(p.6)*
- A propstore projection lens must satisfy PutGet: putting an edited view into an old object and rendering/projecting again returns exactly the edited view. *(p.6)*
- A production projection policy should declare source and target types and be total on them, or the system should reject the policy for unattended migration/synchronization. *(pp.7-8)*
- If a projection filters out information, putback must either restore it from the old concrete object or introduce an explicit default only in an Omega/creation case. *(pp.11-14, pp.17-18)*
- A map-like projection over unordered children requires source and target domain compatibility and shuffle closure; otherwise putback can produce a value outside the claimed source type. *(pp.20-22)*
- Copy-like projections require equality constraints between copied fields, or PutGet can fail after divergent edits. *(p.24)*
- Merge-like projections are valid when the design intentionally propagates one abstract update back to multiple concrete locations. *(pp.25-26)*
- Flatten/pivot/join-style relational projections should preserve key alignment before synchronization; otherwise ordered concrete lists can produce misleading position-based matches. *(pp.45-49)*

## Relevance to Project
For propstore, this is the missing bridge between "projection" and "information-preserving transformation." It provides the formal contract for a projection surface: every rendered view should come with a putback policy, a type/domain claim, and testable round-trip laws. It also clarifies why provenance-bearing stores should treat lossy projections as acceptable only when the lost material is recoverable from the old concrete state, encoded as a default/creation policy, or explicitly declared outside the preservation contract. *(pp.6-8, pp.11-14, pp.49-50)*

## Claims Backed For Propstore
- Projection is not merely a read function; a trustworthy projection is a paired get/putback policy. *(p.6)*
- Information preservation can be tested by round-trip laws rather than asserted informally. *(p.6)*
- Totality is a separate requirement from well-behavedness and should be checked for the intended source/target types. *(pp.7-8)*
- Creation and missing-source cases require explicit defaults or special missing values, not implicit reconstruction. *(pp.11-12)*
- Typed combinators give a compositional way to build larger projections from smaller projections while carrying preservation obligations. *(pp.12-13, pp.43-44)*
- Relational lenses are a direct continuation of this story for native relational data; Foster et al. explicitly point to Bohannon et al. 2006 as the more comprehensive relational extension. *(p.56)*

## Open Questions
- [ ] Which propstore projection surfaces need full PutPut, and which only need GetPut/PutGet?
- [ ] Can propstore encode source/target type declarations for claim projections, context projections, and provenance projections in a way that is mechanically checkable?
- [ ] What is the propstore equivalent of Omega for a newly created claim/provenance artifact with no prior concrete source?
- [ ] Can provenance annotations make filtered-out information explicit enough that putback defaults are auditable?
- [ ] Should propstore projection combinators be authored as a small DSL rather than ordinary helper functions?

## Related Work Worth Reading
- Bohannon, Vaughan, and Pierce 2006, *Relational lenses: A language for updatable views* - the relational extension already present in this collection. *(p.56)*
- Bancilhon and Spyratos 1981, *Update semantics of relational views* - constant complement approach. *(pp.49-51, p.61)*
- Gottlob, Paolini, and Zicari 1988, *Properties and update semantics of consistent views* - dynamic views/open-view account. *(pp.49-51, p.62)*
- Hegner 2004, *An order-based theory of updates for closed database views* - monotonicity and update uniqueness. *(pp.51-52, p.62)*
- Hu, Mu, and Takeichi 2004, *A programmable editor for developing structured documents based on bidirectional transformations* - related editor-oriented bidirectional language with weaker PutGet variants. *(pp.53-54, p.62)*
- Meertens 1998, *Designing constraint maintainers for user interaction* - relation-valued get/putback analogue. *(p.53, p.63)*
- Abiteboul, Cluet, and Milo 1997, *Correspondence and translation for heterogeneous data* - bijective/correspondence-style tree transformations. *(pp.54-55, p.61)*
