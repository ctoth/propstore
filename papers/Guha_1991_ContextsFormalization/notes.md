---
title: "Contexts: A Formalization and Some Applications"
authors: "Ramanathan V. Guha"
year: 1991
venue: "PhD Thesis, Stanford University (STAN-CS-91-1399-Thesis; MCC Technical Report ACT-CYC-423-91)"
doi_url: "https://www.filosoficas.unam.mx/~morado/TextosAjenos/guha-thesis.pdf"
pages: 147
supervisor: "John McCarthy (advisor); with Douglas Lenat (MCC)"
institution: "Stanford University Department of Computer Science"
note: "Typeset revision dated Feb 10, 1995 carries same content as 1991 thesis."
citation: "Guha, R. V. (1991). Contexts: A Formalization and Some Applications. PhD Thesis, Stanford University."
---

# Contexts: A Formalization and Some Applications

## One-Sentence Summary
Guha formalizes contexts as first-class logical objects with an `ist(c, p)` predicate, syntax, semantics (context structures), proof theory (Enter/Exit rules), and a Default Coreference Rule; he then demonstrates through 21 worked examples how this apparatus supports microtheories, problem-solving contexts, hypothetical reasoning, polysemy, perspectives, granularity, and database integration in Cyc. *(pp.1-146)*

## Problem Addressed
Traditional symbolic AI assumes knowledge-base sentences are objective, decontextualized truths. Real knowledge depends on implicit assumptions, vocabulary choices, temporal/spatial scope, perspectives, modalities, and discourse situation. Without a formal context mechanism these dependencies are invisible to the system, which leads to: (a) incompatible microtheories that can't share assertions safely, (b) default rules that cannot state their "abnormality" preconditions cleanly in the target vocabulary, (c) impossibility of "keeping apart" mutually-inconsistent approximations of the same object, (d) inability to integrate heterogeneous databases with conceptually-related but schematically-different content, and (e) cumbersome first-order representations of naturally-context-dependent utterances. *(pp.3-10, 41-56)*

## Key Contributions
- First-class contexts in first-order logic with `ist(c, p)` predicate *(p.7-8, 17-22)*
- Formal syntax and semantics for contexts (Context Structures CS with L(C) and CM(C)) *(p.20-23)*
- Proof theory with Enter/Exit rules and modified UI *(p.25-27)*
- Lifting as relative decontextualization (Default Context-independence Rule DCR-P/DCR-T; Composition Rule CR; abnormality predicates ab-dcp/ab-dct) *(p.31-34)*
- Explicit distinction between microtheories (Mts), Problem Solving Contexts (PSCs), and Discourse Contexts *(p.41-42)*
- Functions constructing new contexts from old: `fixTime(c, T)`, `fixTimeType(c, X)`, `fixVariable(c, f, e)`, `ignorePart(c, DT)`, `ignoreAspect(c, A)`, `staticMt(c)`, `DBContext(D)`, `perspectiveMt(E, A)`, `TPD(A)` *(p.63-64, 71, 107, 112, 121)*
- Scope of context formalized as `presentIn(c, x)` *(p.23, 82-84)*
- Articulation Axioms (AA) = lifting rules for database integration (N instead of N² translations) *(p.111-113)*
- "The-terms" (prototypes/dynamic-scope variables) as compact surrogates for universally-quantified descriptions *(p.88-92)*
- Word-sense mechanism: `wordSense(c, pred, Sense)` + `predFunction(pred, Sense)` second-order reformulation *(p.103-104)*
- Perspective formalization: `perspectiveMt(A, s(A))` vs neutral TPD(A) *(p.107-109)*
- Utterance / Discourse context hierarchy for NLU with pronouns, indexicals, definite/indefinite articles, variadic Etc, preposition predicates *(p.123-131)*

## Study Design
Non-empirical: formal theory development with demonstrator application (car selection via Cyc) rather than controlled experiment.

## Methodology
1. Start from McCarthy's informal proposal `ist(c, p)` *(p.7, 9)*
2. Define first-order syntax and model-theoretic semantics giving contexts rich-object status and referential opacity *(p.17-23)*
3. Build proof theory with context-sequence-labeled lines and Enter/Exit operations *(p.25-27)*
4. Distinguish two default lifting rules: DCR-T (term coreference) and DCR-P (predicate context-independence); introduce abnormality predicates to block defaults; composition rule for non-atomic formulas *(p.33-34)*
5. Identify two problem-solving strategies: **Lift and Solve** vs **Shift and Solve**; Cyc uses Lift and Solve by default, switches only for hardwired query classes *(p.49-50, 67)*
6. Demonstrate through 21 escalating examples in Ch.3 *(p.55-115)*
7. Compare to related AI work: ATMS, FOL/Fausto, Common Lisp packages, partitioned semantic nets, Forbus's qualitative simulation *(p.133-134)*

## Key Equations / Logical Axioms

$$
\mathrm{ist}(c, p)
$$
"p is true in context c" — fundamental predicate. `p` is referentially opaque inside `ist`. *(p.7-8)*

$$
\langle U, CS, S\rangle \models_{C} F \iff U \in CM(C) \land F\text{ meaningful in }C \land \text{FOL satisfaction recursion holds}
$$
Where U = universe, CS = context structure assigning L(C) and CM(C), S = variable assignment, F meaningful iff every non-ist symbol is in L(C). *(p.22)*

$$
\models_{C} \mathrm{ist}(c_k, p) \iff c_k \text{ is a context} \land \forall M \in CM(c_k),\ M \models p \text{ in } c_k
$$
Satisfaction clause for `ist`. *(p.22)*

$$
\mathrm{DCR\text{-}P}:\quad \mathrm{ist}(c_1, P(x)) \land \lnot\mathrm{ab\text{-}dcp}(c_1, c_2, P, x) \Rightarrow \mathrm{ist}(c_2, P(x))
$$
Default predicate context-independence. *(p.33-34)*

$$
\mathrm{DCR\text{-}T}:\quad \mathrm{ist}(c_1, (a = b)) \land \lnot\mathrm{ab\text{-}dct}(c_1, c_2, a, b) \Rightarrow \mathrm{ist}(c_2, (a = b))
$$
Default term coreference across contexts. *(p.33-34)*

$$
\mathrm{ist}(\mathrm{fixTime}(c, T_i), p) \iff \mathrm{ist}(c, \mathrm{holds}(T_i, p))
$$
Projection of c onto a fixed time Ti. *(p.63, A16)*

$$
\mathrm{ist}(\mathrm{fixTimeType}(c, X), p) \iff \mathrm{ist}(c, \forall t_i\ \mathrm{during}(t_i, I_i) \land \mathrm{allInstanceOf}(I_i, X) \Rightarrow p)
$$
Projection of c onto a "during-X" temporal type. *(p.71, A31)*

$$
\mathrm{ist}(c_i, \lnot A(x)) \iff \lnot\mathrm{presentIn}(c_j, x)
$$
A is the strongest assumption of c_i; `presentIn` is the scope relation. *(p.84, A49)*

$$
\mathrm{timeFormalismUsedBy}(c_i, \mathrm{ImplicitFixedTime}) \land \lnot\mathrm{timeFormalismUsedBy}(c_j, \mathrm{ImplicitTime}) \land \mathrm{ist}(c_i, p) \land (=\mathrm{timeOf}(c_i)\ t_i) \Rightarrow \mathrm{ist}(c_j, \mathrm{holds}(t_i, p))
$$
Implicit-time to explicit-time lifting. *(p.61, A9)*

$$
\mathrm{ist}(\mathrm{perspectiveMt}(A, s(A)), \mathrm{performer}(A, x)) \iff \mathrm{ist}(\mathrm{TPD}(A), s(A, x))
$$
Perspective actor is "performer" in perspective context. *(p.108, A84)*

$$
\mathrm{wordSense}(\mathit{mt}_1, s) = \mathrm{ActualPerformerSense} \land \mathrm{wordSense}(\mathit{mt}_2, s) = \mathrm{LegalEntitySense} \land \mathrm{ist}(\mathit{mt}_1, \mathrm{representsAgent}(y, z)) \Rightarrow [\mathrm{ist}(\mathit{mt}_1, s(x, y)) \iff \mathrm{ist}(\mathit{mt}_2, s(x, z))]
$$
Lifting across actor-slot senses via metonymy. *(p.103, A79)*

$$
\mathrm{ist}(\mathrm{CFT}, \mathrm{features}(\mathrm{car}, \mathrm{AntiLockBrakes})) \iff \mathrm{ist}(\mathrm{AutoMt}, \forall x\ \mathrm{allInstanceOf}(x, \mathrm{car}) \Rightarrow \exists y\ \mathrm{allInstanceOf}(y, \mathrm{AntilockBrakes}) \land \mathrm{parts}(x, y))
$$
Articulation axiom from database context to general Mt. *(p.113, A100)*

## Parameters (formal constructs)

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| ist predicate | ist(c, p) | - | - | - | 7-8 | First-order context predicate; referentially opaque |
| Context structure | CS | - | - | - | 21 | Assigns language L(C) and model set CM(C) to each context |
| Context language | L(C) | - | - | - | 21 | Vocabulary of context C |
| Context models | CM(C) | - | - | - | 21 | Set of FOL models in which all assertions of C hold |
| Domain of context | presentIn(c, x) | boolean | - | - | 23, 82 | Objects in scope of c |
| Corefer predicate | corefer(C1, A, C2, B) | boolean | - | - | 23 | A in C1 and B in C2 denote same object |
| Abnormality predicate for DCR-P | ab-dcp | - | false | - | 34 | Blocks predicate lifting |
| Abnormality predicate for DCR-T | ab-dct | - | false | - | 34 | Blocks term coreference |
| Default context-indep rule | DCR | - | - | - | 33 | Symbol meaning doesn't change between contexts by default |
| Composition Rule | CR | - | - | - | 34 | Lifting non-atomic formulas |
| Microtheory suffix | Mt | - | - | - | 41 | Groups of related assertions tagged with Mt |
| Problem Solving Context | PSC | - | - | - | 42 | Tailored for specific problems |
| fixTime function | fixTime(c, T) | - | - | - | 63 | Projects c to context with time fixed at T |
| fixTimeType function | fixTimeType(c, X) | - | - | - | 71 | Projects c to "during-X" context |
| staticMt function | staticMt(c) | - | - | - | 62 | Static part of a dynamic theory |
| selectionObject | selectionObject(c) | - | - | - | 78 | Hypothetical object being selected |
| selectionFor | selectionFor(c) | - | - | - | 78 | Person for whom selection is done |
| derivedContexts | derivedContexts(c_i, c_j) | - | - | - | 79 | Closure via fixTime/fixTimeType |
| defaultTime | defaultTime(c, t) | - | - | - | 64 | Default temporal location of assertions in c |
| wordSense | wordSense(c, pred, Sense) | - | - | - | 103 | Which sense of a polysemous predicate |
| predFunction | predFunction(pred, Sense) | - | - | - | 103 | Second-order constructor for sense-specific predicate |
| perspectiveMt | perspectiveMt(E, A) | - | - | - | 107 | Perspective of actor A on event E |
| TPD | TPD(A) | - | - | - | 107 | Third-person neutral description |
| DBContext | DBContext(D) | - | - | - | 112 | Context whose theory is info in database D |
| Articulation Axiom | AA | - | - | - | 111 | Lifting rule between DBContexts and general Mts |
| Error of theory | error(M, f) | numeric | - | - | 94 | Estimated error of predicate f in theory M |
| Precision required | precisionRequired(PSC, f) | numeric | - | - | 94 | Error tolerance of PSC for predicate f |
| approxModel relation | approxModel(c, c') | - | transitive | - | 122 | c' is approximation of c; transitive |
| Utterance context | UC | - | - | - | 124 | Per-utterance context; ordered temporally |
| Discourse context | DC | - | - | - | 124 | Parent context of utterance contexts |
| priorContext | priorContext(c, c') | - | default=previousContext | - | 128 | For "Going back to..." cue-statement restructuring |
| discourse-function Etc | Etc(x, y, ...) | - | - | - | 125 | Variadic indefinite-extension term |
| definite reference | (The X) | - | - | - | 125 | Bound by context preamble |
| indefinite reference | (A X) | - | - | - | 125 | Existential introduction |

## Rules / Algorithms

### Proof Theory (p.25-27)
Lines of a proof carry a context sequence [C1, ..., Cn]. Inference rules (a)–(l) include:
1. FOL rules applied within any Ci
2. Modus Ponens can be applied from the outside context
3. Conjunction splitting across contexts
4. Consistency rule: `ist(c, p) => ¬ist(c, ¬p)` (given c is consistent)
5. Modified Universal Instantiation respecting `presentIn`
6. Quantifier-ist interaction: `ist(c, ∀x p(x))` does NOT imply `∀x ist(c, p(x))` (Barkan formula FAILS) *(p.24)*
7. Enter Ci / Exit Ci modify the context sequence

### Lift and Solve (p.49-53)
1. Given query Q posed in PSC
2. Access Module scans candidate Mts for relevant axioms
3. Lifting Module computes modified forms for target PSC: apply DCR-T/DCR-P, domain assumptions (A(x)=>R1(x)), temporal rules (A5-A10), scope restrictions
4. Check **Relevance**: `moreRelevantMt(Ct, Mt1, Mt2)` and transitive closures *(p.52)*
5. Check **Appropriateness**: precision bounds — if `error(M, f) > precisionRequired(PSC, f)` then `ab-dcf(M, PSC, f, x)` (A68) blocks lifting *(p.94)*
6. Risky lifting: cursory consistency check only; backtrack on later conflict *(p.52)*
7. Apply conventional theorem prover in PSC with lifted axioms
8. On conflict, accumulate ab-literals not-yet-discharged; discharge in more general context *(p.66)*

### Shift and Solve (p.49, 67)
1. Switch into existing context where vocabulary matches
2. Solve query there
3. Lift answer back to source PSC
4. Cyc hardwires which queries trigger switch; answer quality preserved even if switch is wrong

### Device Model Generation (p.121-123)
1. Start with accurate model CDT0 of device type DT
2. Derive approximations via standard assumption types: fixVariable, ignorePart, ignoreAspect (recursively composable)
3. Relate via `approxModel(c, c')` which is transitive
4. Eliminate internally inconsistent models (`ist(c, False)` → `not baseMt(ci, c)`)
5. Propagate exclusion: `not baseMt(ci, c)` ∧ `approxModel(c, cj)` → `¬baseMt(ci, cj)`
6. Selection heuristics: don't assume away answer; eliminate by error bound; eliminate if model doesn't decide query; prefer simpler

### Pronoun "it" Resolution (p.127-129)
1. Apply linguistic-semantic constraint: `¬male(y) ∧ ¬female(y)`
2. Restrict candidates to previous UC domains: `∃ cj allPreviousUC(ci, cj) ∧ presentIn(cj, x)`
3. Minimize presentIn (domain closure)
4. Prefer closer contexts via priority on ab-it
5. Apply structural discourse info (priorContext distinct from previousContext on "Going back to")
6. Use speaker/listener background, felicity constraints (new-info preference), common sense (liquid-can-be-drunk)

### Database Integration (p.111-114)
1. For each DB D, create DBContext(D) whose theory encodes tuples
2. For n-ary relation R, introduce per-field predicate cfi; key axiom A95 identifies tuples
3. Write Articulation Axioms AA lifting from DBContext to general context (AutoMt/CSPSC)
4. Query routed from general context to relevant DBContexts; each translated to SQL
5. Handle inconsistency: CWA applied in common context not per-DB; interval rule for conflicting values (A102); preference ordering on ab-predicates; variable unit of measure to gloss over

## Figures of Interest
- **Fig: Context DAG (p.23)**: `CM` defines DAGs of contexts; no self-reference. Nesting one level deep assumed in rest of thesis *(p.24)*
- **Fig: Application interface (p.135-136)**: 5-pane GUI for car selection demo: question list, sample entries/DB summary, user statements, candidate list, answer interactor

## Results Summary
The formalism handles all 21 example categories coherently in a single uniform apparatus:
1. Fixing time implicitly to "Now"
2. Structuring theories using static/dynamic temporal properties
3. Making implicitness of time a default
4. Quantifying time universally as default
5. Intermediate temporal constraints ("during winter")
6. Kludging temporal aspects of predicates
7. Hypothetical reasoning
8. Domain assumptions via scope restriction
9. Unstatable assumptions (beliefs requiring richer Mt)
10. Restricted-scope axioms (battery age)
11. "The-terms" as prototypes / dynamic-scope variables
12. Multiple conflicting theories — error estimation
13. Multiple conflicting theories — assumption-based
14. Non-numeric approximations (ContainerMt)
15. Approximation with vs without contexts (MapContext roads-as-lines)
16. Polysemous predicate symbols (seller senses)
17. Functional vs structural definitions
18. Perspectives (TPD vs perspectiveMt)
19. Granularity in NL queries (location -> phoneNumber)
20. Database integration via articulation axioms
21. Mutual DB inconsistency handling

Demo session on Chris-buying-car: starts at 324 candidate cars; after 11 answers and many tentative inferences reaches 3 cars (DodgeSpiritR/t, Volvo240, ToyotaCelicaGtS) *(p.140-146)*. Final Dodge Spirit R/T DB dump at p.145-146 shows DB conflicts between Consumer Reports and Consumer Guide handled via A101-A102 mechanisms.

## Limitations
- Only one level of ist nesting assumed for the entire thesis *(p.24)* — multiple nesting left open
- Cyc implementation currently hardwires which queries trigger Shift-and-Solve *(p.67)*
- "Risky lifting" policy: consistency check cursory; inconsistencies discovered only at problem-solving time *(p.52)*
- Author acknowledges Forbus's "consider" mechanism is "closest in spirit" but differs by attaching assumptions to individual statements rather than theories *(p.134)*
- staticMt-based scheme for temporal structuring was "preferable" earlier but Cyc today does NOT use it *(p.62)*
- EBL (Explanation Based Learning) "in practice... only slow a system down" (cites Steve Minton) *(p.77)*
- The "compilation" AI view of naive-from-principled rules via EBL is rejected *(p.77)*
- Barkan formula `ist(c, ∀x p(x)) <=> ∀x ist(c, p(x))` does NOT hold *(p.24)*
- No formal bibliography; in-text citations only
- System complains but cannot proceed when domain assumption violated (e.g., user from Peru) *(p.144)*

## Arguments Against Prior Work
- **vs ATMS [deKleer]**: ATMS contexts are propositional assumption sets enumerated a priori; our contexts are first-class rich objects not enumerated *(p.133)*
- **vs FOL/Fausto [Weyrauch]**: FOL meta/base don't share ontology; no quantification across theories; no relative decontextualization *(p.133)*
- **vs Common Lisp packages [Steele]**: programming-language construct; no assumptions; no relative decontextualization *(p.133)*
- **vs Partitioned Semantic Nets [Henricks, KEE, MRS, Russell]**: theories are truly separate; no inter-theory interaction; no assumptions behind theories *(p.133-134)*
- **vs Forbus's "consider" statements**: attach assumptions to individual statements, not theories; no representation change mechanism; no relative decontextualization *(p.134)*
- **vs Kamp's Discourse Theory**: DT treats contexts as data structures outside domain; assumes THE correct decontextualized translation exists *(p.132)*
- **vs Grosz & Sidner DST**: DST focuses on discourse structure not meaning determination *(p.132)*
- **vs EBL [Minton]**: compilation-of-principled-rules approach doesn't work in practice *(p.77)*
- **vs deKleer's device models**: context-independent models require impossibly detailed universal models *(p.119)*

## Design Rationale
- **Why contexts must be first-class rich objects**: permits quantification over them (as in `(forall c_i utteranceContext(c_i) => ...)`), allows defining contexts as functions of other contexts (fixTime, perspectiveMt), enables applications to choose among candidate contexts at runtime *(p.17)*
- **Why forall-inside-ist differs from forall-outside-ist** *(p.62)*: AutoMt's scope is restricted; quantifying outside the ist gives wrong results
- **Why ist is referentially opaque** *(p.18)*: same object may have different denotations across contexts; names aren't rigid designators universally
- **Why default coreference + abnormality predicates beats explicit coreference schemas**: compact representation, overridable, supports "risky" lifting with backtracking *(p.33-34, 52)*
- **Why contexts over default reasoning alone**: default reasoning requires exceptions be STATABLE in vocabulary; contexts handle unstatable exceptions by stating them in a more general context *(p.63, 85)*
- **Why "the-terms" over Iota operator**: Iota-terms are undefined when multiple objects satisfy; "the-terms" are plain nonatomic terms that get converted to variables at lifting time *(p.91)*
- **Why predFunction (second-order reformulation) for polysemy**: keeps axioms first-order WITHIN a single context; second-order machinery confined to inter-context translation *(p.103)*
- **Why separate TPD(A) from perspectiveMt(E, A)**: allows different actors' partial descriptions to compose back into a neutral third-person description *(p.107-109)*
- **Why Articulation Axioms over direct DB-to-DB translation**: N rules instead of N²; single general vocabulary is Cyc; scales to heterogeneous collections *(p.111)*
- **Why error-based blocking of lifting**: more general than assumption-checking when assumptions aren't statable (Newtonian mechanics vs Relativity) *(p.95)*

## Testable Properties
- **ist(c, P1 ∧ P2) ⇔ ist(c, P1) ∧ ist(c, P2)** (consistency of ist) *(p.22-24)*
- **Barkan formula FAILS**: `ist(c, ∀x p(x)) ⇔ ∀x ist(c, p(x))` does NOT hold *(p.24)*
- **CM defines DAG**: no self-referential contexts *(p.23)*
- **approxModel is transitive**: `approxModel(c1, c2) ∧ approxModel(c2, c3) ⇒ approxModel(c1, c3)` *(p.122)*
- **Scope monotonicity under lifting**: if target context has weaker assumptions, (forall x R(x)) lifts to (forall x A(x) ⇒ R_1(x)) where A is origin's strongest assumption *(p.83-84)*
- **presentIn maximization heuristic**: assume presentIn holds unless negation derivable *(p.83-84)*
- **Default senses**: `wordSense(c, x, FunctionalSense) ⇔ wordSense(c, x, StructuralSense)` as default biconditional *(p.105)*
- **derivedContexts closure**: `derivedContexts(c, fixTime(c, t_i))` and `derivedContexts(c, fixTimeType(c, X))` hold *(p.79)*
- **Selection object scope**: `selectionObject(c_i, o) ∧ ¬derivedContext(c_i, c_j) ⇒ ¬presentIn(c_j, o)` *(p.79)*
- **CWA mustn't be per-DB**: closed-world assumption should apply in common context, not per-DBContext, else false contradictions *(p.114)*
- **Unique-denotation-per-term in UC**: within a single utterance context, each term denotes exactly one object *(p.126)*

## Relevance to Project
This paper is foundational for propstore's **concept/semantic layer** in two very direct ways:

**(1) McCarthy-style context formalization is an explicit pillar of propstore's architecture.** The project CLAUDE.md cites "context formalization (McCarthy 1993)" and says "Contexts are first-class logical objects qualifying when propositions hold (McCarthy 1993 `ist(c, p)`)." Guha is McCarthy's student and this thesis IS the operationalization of McCarthy's informal proposal — the `ist` predicate, the proof theory, the model-theoretic semantics, and the DCR/DCT default-coreference machinery.

**(2) Lifting as relative decontextualization directly maps to propstore's formal non-commitment discipline.** Guha's core insight — that you CANNOT fully decontextualize in storage, that formulas carry their contextual dependencies, that DCR is only a DEFAULT blockable by abnormality predicates — matches propstore's rule "never collapse disagreement in storage unless user explicitly requests migration." The ab-dcp/ab-dct pattern is essentially the project's proposal-vs-source distinction: proposals with provenance, render-time resolution, not build-time gates.

Specific propstore components that map to Guha constructs:
- `ist(c, p)` ↔ propstore's `(context, claim)` pair in claims.yaml
- Context as first-class object ↔ propstore contexts in `contexts/`
- Microtheory (Mt) suffix ↔ propstore's source branches in `propstore/repo/`
- Problem Solving Context ↔ rendering policy / query-time filter
- Default Coreference Rule ↔ propstore's default vocabulary reconciliation
- Abnormality predicates ↔ proposal rejection / render-time overrides
- Lift and Solve vs Shift and Solve ↔ two propstore query strategies (import into local context vs route to foreign context)
- Articulation Axioms ↔ propstore's vocabulary reconciliation across paper-local concepts.yaml
- Error/precision-based lifting block (A68) ↔ propstore's calibration + honest-ignorance discipline
- fixTime projection ↔ temporal context qualification in propstore
- presentIn scope relation ↔ propstore's domain-restricted claims
- Two inconsistency kinds (CWA vs value) ↔ propstore distinguishing missing evidence from actual conflict
- Mutual DB inconsistency handling ↔ propstore argumentation-layer attacks over rival concept merges

Propstore may also want to directly implement:
- The "risky lifting + backtrack" policy as an alternative to strict consistency
- Interval-conclusion rule (A102) for merging conflicting numeric claims
- Perspective machinery for claims-by-author (each author is a "perspective" on shared events)
- "The-terms" mechanism for paper-local prototypes that get replaced with concrete bindings at render time

## Open Questions
- [ ] Does propstore's IC merge formally realize Guha's "risky lifting + backtrack" semantics? (see propstore/repo/ IC merge operators)
- [ ] Can ASPIC+ bridge handle Guha's `ist(c, ¬p)` distinction from `¬ist(c, p)`? (currently unclear)
- [ ] Is propstore's `KindType.TIMEPOINT` compatible with `fixTime`-style projections?
- [ ] How does propstore's recency resolution strategy relate to "temporally closer context preferred" (A128-like) heuristics?
- [ ] Can the articulation axiom N-vs-N² benefit be realized for concept reconciliation across papers?
- [ ] Is the Barkan-formula-failure acknowledged in propstore's universal quantification handling?

## Related Work Worth Reading
- McCarthy, J. (1993) "Notes on Formalizing Context" — the informal proposal Guha operationalizes
- Forbus & Falkenhainer — qualitative simulation with "consider" statements; related but cruder
- deKleer ATMS — propositional assumption sets; does NOT do relative decontextualization
- Weyrauch FOL / Fausto — multiple theory framework lacking shared ontology
- Grosz & Sidner — discourse structure theory, orthogonal in focus
- Kamp's Discourse Representation Theory — treats contexts as data structures
- Weld — theory of when extreme-value assumptions are valid
- Minton on EBL — empirical argument against compilation approaches
- Lenat & Guha "Building Large Knowledge-Based Systems" (the Cyc book, referenced as `[cyc book]`) — substrate for this thesis
- Hobbes — planning with simplified geometric shapes (example 15)
- KRL — "perspective" term use in earlier AI literature

## Cyc Vocabulary Glossary
- **Mt**: Microtheory suffix (HumanKinshipMt, AutoMt, BuyingGMt, NaiveMoneyMt, WorkPlaceBehaviorMt, ContainerMt, MapContext, StaticAutoMt, WinterMt, WorkPlaceAgreementMt, NaiveTransactionsMt, NaiveKinshipMt, JobMt, BaseKB)
- **PSC**: Problem Solving Context (CSPSC = Car Selection PSC, CSPSC-T1, CSPSC_W = fixTimeType(CSPSC Winter), MajorPurchaseSelectionPSC, CarBuyingForChrisContext)
- **Actor Slots**: performer, victim, buyer, seller, observer, referee, driver, vehicle, object, objectBought, performedBy
- **Relation predicates**: instanceOf, allInstanceOf, parts, slotValueHasInsOf, ownedBy, usedBy, drivenBy, hasFeatures, during, occursAt, corefer, presentIn, derivedContexts, selectionObject, selectionFor, selectionObjectType, timeFormalismUsedBy, domainAssumptions, precisionRequired, defaultTime, defaultImplicitTime, holds, holdsDuring, contextTask, informationRequirement, genlSlots, baseMt, approxModel, deviceModel, aspectType, aspectIncluded, narrator, contextTopic, utteranceContext, allPreviousUC, priorContext, nearer, discContext, hasDiscourseContextOf, importsFrom, dbObject, contextTopic
- **ab-...**: abnormality predicates (ab-dcp, ab-dct, ab-A21, ab-financialLiquidity, ab-it, ab-pc, ab-price, ab-dcf)
