---
title: "A Nanopass Infrastructure for Compiler Education"
authors: "Dipanwita Sarkar, Oscar Waddell, R. Kent Dybvig"
year: 2004
venue: "ICFP '04: Proceedings of the Ninth ACM SIGPLAN International Conference on Functional Programming"
doi_url: "https://doi.org/10.1145/1016848.1016878"
pages: "201-212"
affiliations: "Indiana University; Abstrax, Inc.; Indiana University"
funding: "Microsoft Research University Relations gift (D. Sarkar)"
note: "Pages in this paper are paginated 201-212 in the proceedings; PDF page-NNN is paper page (201+NNN). All citations below use proceedings page numbers."
produced_by:
  agent: "claude-opus-4-7[1m]"
  skill: "paper-reader"
  status: "stated"
  timestamp: "2026-04-25T08:39:36Z"
---
# A Nanopass Infrastructure for Compiler Education

## One-Sentence Summary
Defines a methodology and a Scheme-embedded DSL (`define-language`, `define-pass`, plus a pass expander) for building compilers as long sequences of tiny passes whose intermediate-language grammars are formally specified, automatically realized as strongly-typed record ASTs, and statically checked at the boundary between every pass.

## Problem Addressed
Conventional ("monolithic") compilers fold many unrelated analyses, transformations, and optimizations into a few large passes. They are hard to read, hard to extend, and bugs cannot be isolated to one pass *(p.201)*. The earlier "micropass" methodology (a compiler as 50+ tiny passes) helps, but writing many small passes duplicates AST traversal/rewriting code, the per-pass output grammars are written as documentation only and are *not enforced*, unhandled cases silently fall through to general clauses producing malformed output that breaks later passes, and the pile of traversals is slow *(p.202)*.

## Key Contributions
- **Nanopass methodology**: a compiler is a sequence of fine-grained passes, each performing exactly one of {simplification, verification, conversion, analysis, improvement} *(p.203)*.
- **`define-language`**: a DSL form that formally specifies an intermediate language and *implicitly* generates: (1) a set of strongly-typed record types representing ASTs, (2) an s-expression-to-record parser, (3) a record-to-s-expression unparser, (4) an s-expression-pattern-to-record partial parser used by the pass macros *(p.204)*.
- **Language inheritance** via `extends` plus `+`/`-` modifiers on terminals and productions, so each new IL is expressed as a *diff* against the previous IL *(p.206)*.
- **`define-pass` plus a pass expander**: a pass writes transformer clauses only for forms that *change*; the pass expander uses the strongly-typed input/output language definitions to fill in trivial structural recursion automatically *(p.206-207)*.
- **Reference-implementation cross-check**: every IL has an unparser back to host-language Scheme, so each pass's output can be evaluated and compared against a reference implementation's result on every test input, isolating correctness regressions to one pass *(p.203)*.
- **Empirical case study**: a 50-pass Scheme→Sparc-assembly compiler delivered as a 15-week course, with measured per-pass code-size reduction of roughly 3-4x vs micropass tools (`remove-not` 25→7 lines, `convert-assigned` 55→20 lines) *(p.211)*.

## Methodology
Compiler is a chain of passes
`L0 → L1 → L2 → ... → Ln`
where each `Li` is a `define-language`-declared IL and each transition is a `define-pass` whose signature literally is `Li -> Lj`. Per-pass discipline (one of):
- **Simplification** — translate input into an IL whose grammar lacks the eliminated form (e.g., remove `not`) *(p.203)*.
- **Verification** — re-typecheck the input against an invariant not expressible in the grammar (e.g., bound-variable uniqueness); output IL identical to input IL *(p.203)*.
- **Conversion** — make explicit something the lower IL does not directly support (e.g., basic blocks → linear instruction stream with branches) *(p.203)*.
- **Analysis** — collect information by traversing the input, annotate the output AST in `common` slots (e.g., free-variable sets on `lambda`); same input/output IL *(p.203)*.
- **Improvement** — optimization pass; same input/output IL so it can be individually toggled *(p.203)*.

A verification or improvement pass is required to produce a program in the *same* IL as its input so it can be enabled/disabled per-run; this is what makes the chain robust to switch-permutation regression testing *(p.203)*.

Each pass is implemented as Scheme code via `syntax-case` macro extensions; macros lower the high-level pass spec into pattern-matching code over AST records *(p.203)*.

## Key Equations / Constructs

### Language definition

$$
(\textbf{define-language}\ name\ \{\textbf{over}\ tspec^+\}\ \textbf{where}\ production^+)
$$

Where:
- `tspec ::= (metavariable+ in terminal)` — declares terminals (variable, boolean, integer, ...) externally defined; metavariable `x` implicitly licenses `x`, `x1`, `x2`, ... *(p.203)*
- `production ::= ({metavariable+ in} nonterminal alternative+)` — pairs a nonterminal with one or more alternatives.
- `production` may also carry common slots: `({metavariable+ in} (nonterminal common+) alternative+)` — common slots store annotations such as source info or analysis byproducts *(p.203-204)*.
- `alternative ::= metavariable | (keyword form...) [property+]` — at most one parenthesized alternative per production may begin with a non-keyword (the application form), which keeps parser disambiguation deterministic *(p.204)*.
- `property ::= (key value)`; the `=>` (translates-to) property gives an explicit translation into host-language semantics, used by the unparser/evaluator *(p.204)*.
*(p.203-204)*

### Language inheritance

$$
(\textbf{define-language}\ name\ \textbf{extends}\ base\ \{\textbf{over}\ \{mod\ tspec\}^+\}\ \textbf{where}\ \{mod\ production\}^+)
$$

Where `mod ∈ {+, -}`. `+` adds, `-` removes. Inheritance is purely *notational*: the child language is materially equivalent to a fresh full `define-language`; child and parent record types are **disjoint** *(p.206)*.
*(p.206)*

### Pass definition

$$
(\textbf{define-pass}\ name\ \mathit{input\text{-}lang}\ \texttt{->}\ \mathit{output\text{-}lang}\ transform...)
$$

Where each `transform` is

$$
(name : nonterminal\ arg... \texttt{->} val\ val...\ [input\text{-}pattern\ \{guard\}\ output\text{-}expression]...)
$$

Special output languages: `void` (effect-only passes — info collection), `datum` (compute a host-language value, e.g., size estimate). Otherwise the first return value must be of the declared output-language nonterminal type *(p.206)*.
*(p.206-207)*

### Subpattern forms (matching input)

For metavariable `a` over input nonterminal `A`, `b` over output nonterminal `B`, transformer `f : A → B`:

1. `,a` — bind a to the matching input subform *(p.207)*.
2. `,[f : a -> b]` — recurse with f, bind a to input, b to result *(p.207)*.
3. `,[a -> b]` — sugar for 2 when f is the unique transformer of type `A → B` (relies on per-pass typing) *(p.207)*.
4. `,[b]` — sugar for `,[a -> b]` when input is of form `A` *(p.207)*.

Multi-arg/multi-return form: `,[f : a x ... -> b y ...]` *(p.207)*.

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Total passes in delivered course compiler | — | passes | 50 | — | 201, 211 | Scheme→Sparc, including verification passes |
| Course length | — | weeks | 15 | — | 202 | One per row of Table 1 |
| Languages defined for the course compiler | — | ILs | "fewer than passes" | — | 203 | Most adjacent passes share IL via verification/improvement category |
| `remove-not` pass size, micropass tools | — | lines | 25 | — | 211 | Smallest micropass pass |
| `remove-not` pass size, nanopass tools | — | lines | 7 | — | 211 | ~3.5x reduction |
| `convert-assigned` pass size, micropass | — | lines | 55 | — | 211 | |
| `convert-assigned` pass size, nanopass | — | lines | 20 | — | 211 | ~2.75x reduction |
| Pass-expander applicability | — | — | order-insensitive structural recursion | — | 211 | Cannot fill in flow-sensitive passes (live analysis) |
| `mod` operators on inheritance | — | — | `+` (add), `-` (remove) | — | 206 | No `replace` operator; equivalent to remove+add |
| Special output languages | — | — | `void`, `datum` | — | 206 | For effect-only or host-value-returning passes |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Per-pass LOC reduction (`remove-not`) | factor | 3.57x (25→7) | — | — | Indiana University compiler course | 211 |
| Per-pass LOC reduction (`convert-assigned`) | factor | 2.75x (55→20) | — | — | Indiana University compiler course | 211 |
| Pass count delivered | count | 50 in 15 weeks | — | — | One-semester senior/graduate course | 202, 211 |

## Methods & Implementation Details

### Per-pass discipline
- One specific task per pass (simplify, verify, convert, analyze, improve) *(p.203)*.
- Verification/improvement passes have identical input and output IL so they are toggleable without disturbing the chain *(p.203)*.
- Adjacent ILs differ only "slightly" because each pass changes only the affected forms; this is what makes language inheritance practical *(p.203)*.

### Typed IR boundary mechanism
- `define-language` materializes a base record type, a per-nonterminal subtype, and a per-alternative subtype. Common-element fields land on the nonterminal subtype; alternative-specific fields on the alternative subtype *(p.204)*.
- Strong typing of record constructors makes ASTs **well-formed by construction**: a constructor for an `if` record refuses arguments that are not records of the appropriate field types *(p.205, p.207)*.
- Per-pass type signatures (`L_i -> L_j`) drive transformer dispatch on AST records via "efficient type dispatch" rather than linear pattern scan *(p.207)*.
- The pass expander commonizes recursion results so structural recursion clauses introduced by both the user and the expander do not double-evaluate *(p.207)*.

### Validation per pass
Three independent validation channels are layered:
1. **Static**: input and output records must satisfy the IL grammar by construction; constructor-time type errors prevent malformed output from leaving a pass *(p.207)*.
2. **Implicit grammatical guard**: the partial parser converts input *patterns* into typed record patterns, so when a pattern such as `(if (not ,e1) ,e2 ,e3)` is parsed against L2, the embedded `primapp` constraint comes from the L2 grammar, not the user *(p.208)*.
3. **Reference-implementation comparison**: every IL is unparseable back into host-language Scheme; the development driver evaluates the output of each pass and compares the result to the reference implementation's result on each test program, isolating any correctness-preservation failure to a single pass *(p.203)*.
4. **Verification passes** added to the chain whenever there are invariants too rich for the grammar (uniqueness of bound variables, etc.) *(p.203)*. They produce the same IL they consume, so they are toggleable.

### Cumulative organization
Per Table 1 (p.202), 50 passes are organized by week and by primary task:
- Week 1: simplification (verify-scheme, rename-var, remove-implicit-begin, remove-unquoted-constant, remove-one-armed-if, verify-a1-output)
- Week 2: assignment conversion (remove-not, mark-assigned, optimize-letrec, remove-impure-letrec, convert-assigned, verify-a2-output)
- Week 3: closure conversion (optimize-direct-call, remove-anonymous-lambda, sanitize-binding-forms, uncover-free, convert-closure, optimize-known-call, uncover-well-known, optimize-free, optimize-self-reference, analyze-closure-size, lift-letrec, verify-a3-output)
- Week 4: canonicalization (introduce-closure-primitives, remove-complex-constant, normalize-context, verify-a4-output)
- Week 5: pointer encoding/allocation (specify-immediate-representation, specify-nonimmediate-representation)
- Week 6: start of UIL compiler (verify-uil)
- Week 7: introducing labels and temps (remove-complex-opera*, lift-letrec-body, introduce-return-point, verify-a7-output)
- Week 8: virtual registerizing (remove-nonunary-let, uncover-local, the-return-of-set!, flatten-set!, verify-a8-output)
- Week 9: brief digression (generate-C-code) — not in final compiler
- Week 10: register allocation setup (uncover-call-live, optimize-save-placement, eliminate-redundant-saves, rewrite-saves/restores, impose-calling-convention, reveal-allocation-pointer, verify-a10-output)
- Week 11: start of register allocation (uncover-live-1, uncover-frame-conflict, strip-live-1, uncover-frame-move, verify-a11-output)
- Week 12: setting up call frames (uncover-call-live-spills, assign-frame-1, assign-new-frame, optimize-fp-assignments, verify-a12-output)
- Week 13: introducing spill code (finalize-frame-locations, eliminate-frame-var, introduce-unspillables, verify-a13-output)
- Week 14: register assignment (uncover-live-2, uncover-register-conflict, verify-unspillables, strip-live-2, uncover-register-move, assign-registers, assign-frame-2, finalize-register-locations, analyze-frame-traffic, verify-a14-output)
- Week 15: generating assembly (flatten-program, generate-Sparc-code)
*(p.202, Table 1)*

Footnotes (p.202): superscript 1 = passes supplied by the instructor; 2 = challenge passes for graduate students; 3 = `optimize-known-call` is actually written during Week 4 even though listed in Week 3; 4 = `generate-C-code` is not in the final compiler. Most passes run exactly once; the register/frame allocator passes are repeated until all variables have homes.

Naming convention: many passes have name prefixes that announce their category (`verify-*` = verification, `remove-*` and `simplify-*` = simplification, `uncover-*` = analysis, `convert-*` = conversion, `optimize-*` = improvement, `assign-*` and `finalize-*` = conversion at allocation level, `eliminate-*` = simplification).

### How a new pass is added
1. Write a `define-language` for the *output* IL, ideally as `extends` of the input IL with `+`/`-` diffs *(p.206)*.
2. Write `define-pass new-name InputL -> OutputL` with transformer clauses only for the forms that change *(p.206-207)*.
3. The pass expander generates the trivial structural cases by consulting the two language definitions *(p.206)*.
4. Optionally insert a verification pass after the new pass that checks any invariants not expressible in the output grammar *(p.203)*.
5. Run the test suite under the development driver; if a comparison against the reference implementation fails, the failure is localized to this pass by construction *(p.203)*.

### Worked example: `remove-not` (p.208)
- Input/output IL: L2 → L2 (same grammar; this is *not* a new IL because the `not` form is realized as a `primapp`, not a distinct grammar form).
- Pass body has only two transformer clauses:
  - `[(if (not ,[e1]) ,[e2] ,[e3])` → `` `(if ,e1 ,e3 ,e2) `` ` (swap branches when `not` is the test).
  - `[(primapp ,pr ,[e]) (eq? 'not pr)` → `` `(if ,e #f #t) `` ` (general elimination via `if`).
- The pass expander emits, from the language definition, code that:
  - Type-tests the input record (`if.L2?`, `primapp.L2?`).
  - Recurses on subforms via implicit calls to `process-expr`.
  - Reconstructs the result via `make-if.L2`.
  - Falls through to the expander's auto-generated structural recursion on every other L2 alternative.

### Worked example: `optimize-direct-call` (p.209)
- Input/output IL: L2 → L3, where L3 = L2 + `(let ((x e) ...) body)`.
- Single transformer clause:
  - `[((lambda (,x ...) ,[body]) ,[e] ...)` → `` `(let ((,x ,e) ...) ,body) `` `
- Demonstrates inheritance (`define-language L3 extends L2 where + (Expr (let ((x e) ...) body))`) and the partial parser handling more involved `maplist-of` patterns.

### Worked example: assignment conversion (p.209-210)
- Two passes:
  - `mark-assigned : L4 -> void` (purely effectful; sets a flag on variable records).
  - `convert-assigned : L4 -> L5` (rewrites references to assigned variables as `(primapp car x)`, assignments as `(primapp set-car! x e)`, and introduces fresh `let`-bindings of assigned vars to single-cell pairs `(primapp cons xr #f)`).
- L5 = L4 with `(Command (set! x e))` removed.
- Helper `split-vars` partitions a variable list into (untouched vars, replacement vars, original vars) — host-language Scheme procedure used inside the pass body.

### Pass expander limitations
- Pass expander fills in only structural cases insensitive to recursion order on subforms (most passes) *(p.211)*.
- Passes that need flow-sensitive traversal (e.g., live-variable analysis) must be written out in full *(p.211)*.
- Future-work proposal: extend language definitions to declare flow information and let `define-pass` request forward/backward flow-sensitive recursion *(p.211)*.

### Cost
- Many repeated traversals → compile-time speed unsuitable for production *(p.202, 211)*.
- Future work: a pass combiner that fuses several passes into one super-pass via deforestation [Wadler 1988], so improvement passes can be developed independently but run together *(p.211)*.
- Acknowledged risk: phase-ordering interactions become more visible at fine granularity (cite [LaLonde&desRivieres 1982], [Whitfield&Soffa 1990]) *(p.211)*.

## Figures of Interest
- **Illustration 1 (p.204):** Compiler-writer interacts via s-expression syntax even though storage is records — programmer-facing syntax decouples from internal representation.
- **Figure 1 (p.205):** A `define-language` for L0 alongside its corresponding grammar in BNF.
- **Figure 2 (p.205):** The 12 record-type definitions automatically generated for L0 (`L0`, `program`, `expr`, `command`, then alternative subtypes).
- **Figure 3 (p.205):** The mutually-recursive `parse-program`/`parse-expr`/`parse-command` parser generated for L0.
- **Figure 4 (p.208):** Tiny three-nonterminal language L2 (Program/Expr/Command-like with `primapp`) used as the running example.
- **Figure 5 (p.208):** The 7-line `remove-not` pass.
- **Figure 6 (p.209):** L3 defined by inheritance: `(define-language L3 extends L2 where + (Expr (let ((x e) ...) body)))`.
- **Figure 7 (p.209):** The `optimize-direct-call` (beta-reduction) pass.
- **Figure 8 (p.210):** The `convert-assigned` pass plus its `split-vars` helper.
- **Table 1 (p.202):** The 50-pass weekly schedule for the course compiler.

## Results Summary
- 50-pass Scheme→Sparc compiler delivered in a 15-week senior/graduate course at Indiana University *(p.202, 211)*.
- Pass-by-pass code reduction: `remove-not` 25→7 lines, `convert-assigned` 55→20 lines, with similar reductions across most passes; "size of a few passes cannot be reduced" (e.g., the code generator, which must explicitly handle every grammar element) *(p.211)*.
- Bug isolation: the reference-implementation comparison pinpoints correctness regressions to a single pass *(p.203)*.
- Adding a new optimization no longer requires "shoe-horning" code into an existing pass; new code lives in a new pass file *(p.211)*.

## Limitations
- **Compile-time speed**: many traversals make the resulting compiler too slow for production use *(p.202, 211)*. Future work: pass combiner via deforestation.
- **Pass expander cannot handle flow-sensitive passes**: live-variable analysis and similar must be written out longhand *(p.211)*.
- **Phase ordering**: fine-grained passes can exacerbate phase-ordering anomalies; resolution can require iteration to fixpoint or rework into super-optimizers, undermining the methodology's separation properties *(p.211)*.
- **Misleading runtime intuition for students**: the slow nanopass compiler can give students an inaccurate impression of compiler speed in industry *(p.202)*.
- **Inheritance is only notational**: child and parent record types are *disjoint*, so a `+`-only-extension pass still has to materialize new records — there is no zero-cost subtype reuse *(p.206)*. (This matters for migration-framework analogies where carrying old records forward unchanged would be desirable.)

## Arguments Against Prior Work
- **Monolithic compilers** (production norm): bury related and unrelated transformations in the same pass, so bugs cannot be isolated and adding new optimizations requires major restructuring *(p.201)*.
- **Plain micropass tools** (their own predecessor): force per-pass duplication of AST traversal/rewriting code; pass-output grammars exist only as comments and are not enforced, so an unhandled case silently falls through to a more general clause and corrupts later passes *(p.202)*.
- **Zephyr ASDL [16]**: covers IL representation only, not pass definition; nanopass extends ASDL's idea by integrating language definitions with pass-expander dispatch *(p.210)*.
- **TIL [11]**: type-checks IL outputs but is not designed around fine-grained pass decomposition; nanopass argues that per-IL grammar enforcement plus reference-implementation comparison subsumes typed-IL benefits while supporting many more passes *(p.210)*.
- **Polyglot [9]**: achieves "work proportional to nodes/passes affected" via OOP machinery; nanopass argues language inheritance + pass expander gets the same property with less syntactic and conceptual overhead *(p.210)*.
- **Tm [12,13]**: a low-level relative; tree-walker templates similar to `define-pass` exist but Tm lacks input pattern syntax for nested record matching and lacks extensible properties *(p.210)*.
- **PFC [3], SUIF [1,2]**: PFC uses macro expansion for boilerplate (closest precedent for the pass expander); SUIF provides one IL with views, opposite of nanopass's many ILs. Nanopass formalizes language definitions, makes host-language conversion automatic, and separates traversal from IL/pass code *(p.210-211)*.
- **Super-optimizers** (Click&Cooper [4], Lerner et al. [8], etc.): combine many optimizations into one phase to avoid phase-ordering issues; nanopass authors explicitly reject this approach because it reproduces the monolithic-pass problem and makes new optimizations expensive to add. They propose a future *pass combiner* that auto-fuses developed-separately passes via deforestation *(p.211)*.

## Design Rationale
- **Why fine grain**: each pass corresponds 1:1 with a logical compilation step; bugs can be isolated to a single pass; new optimizations are added as new files rather than as edits to existing passes *(p.201, 211)*.
- **Why formal grammars per IL**: prior micropass practice wrote grammars as documentation but did not enforce them; unhandled cases fell through silently. Formal `define-language` definitions enforce the grammar as the AST record type system *(p.202)*.
- **Why s-expressions on the surface but records internally**: s-expressions are the natural Scheme programmer interface and ease tracing/debugging; records give strong typing, fast pattern dispatch, and prevent malformed ASTs by construction *(p.204)*.
- **Why language inheritance**: most passes change the IL only slightly; expressing each new IL as a `+/-` diff against the previous keeps the codebase readable and avoids re-stating shared productions *(p.203, 206)*.
- **Why parent/child record types are disjoint** (despite using inheritance syntax): preserves the property that records are tagged with their owning language, so type dispatch in a pass cannot accidentally accept a record from the wrong IL. The trade-off is that even an additive pass must construct new records *(p.206)*.
- **Why the pass expander only handles order-insensitive recursion**: keeps the expander simple; flow-sensitive analyses inherently need user-specified traversal order *(p.211)*.
- **Why `void` and `datum` output languages**: explicit categorical types for effect-only and value-returning passes; otherwise a pass writer would have to invent a degenerate "result" IL *(p.206)*.
- **Why verification passes share IL with their input**: makes them toggleable for development speed without disturbing later passes *(p.203)*.
- **Why reference-implementation comparison**: an executable, runtime check that an IL transformation preserves meaning, complementing the static grammar check *(p.203)*.

## Testable Properties
- After every nanopass pass, the resulting AST is well-formed in the declared output language by construction (record constructors reject malformed children) *(p.205, 207)*.
- For every IL `Li` in the chain, `unparse(parse(prog)) ≡ prog` modulo the `=>` translates-to property — both directions are generated automatically *(p.204, 206)*.
- For every pass `P : Li -> Lj` and every reference test program `t` that runs in `Li`, `eval_host(unparse_Lj(P(parse_Li(t))))` must equal the reference implementation's result on `t`; otherwise `P` has a correctness regression *(p.203)*.
- A `define-language extends` form whose `+/-` modifiers leave a parent production unchanged still generates a fresh record type for that production in the child language; the child does not share record identity with the parent *(p.206)*.
- The pass expander generates correct boilerplate for any pass whose IL transformation is insensitive to recursion order on subforms *(p.211)*. Property: such a pass written with only the changed-form clauses must produce the same output as the same pass written with all clauses spelled out.
- Per-pass LOC must scale with the number of *changed* forms, not the number of total forms in the IL (otherwise the methodology has failed) *(p.211)*.
- A verification or improvement pass must satisfy `output_IL == input_IL` so that it is individually toggleable *(p.203)*.

## Relevance to Project

Direct architectural template for a propstore *storage-schema migration framework* — answering each of the four focus areas:

1. **Typed IR boundaries.** Every pass declares `InputLang -> OutputLang` and the language definitions automatically materialize disjoint record types per language. Mapping to propstore: each schema version is its own typed object family (Pydantic/dataclass/SQLA model namespace), declared by an explicit "schema version" definition; a migration is a function with a typed signature `Schema_2026_04_27 -> Schema_2026_04_28`. The recent concept→concepts cutover (commits 2f55956..211aa44, version stamp 2026.04.27 → 2026.04.28) had no such typed boundary; both shapes coexisted under the same Python class names.

2. **Single-pass discipline.** Five categories — *simplification, verification, conversion, analysis, improvement* — and the rule that verification/improvement passes share IL with their input. For propstore: every migration step is *one* of {strip-field, rename-field, derive-field, validate-invariant, normalize-existing, optimize-storage}. Mixed migrations are illegal. The analogue of `verify-*` passes is a per-version invariant check (e.g., "every claim references a concept link, never a primary concept fallback") that runs over the post-migration corpus and certifies the new shape before the next migration runs. The earlier cutover bundled normalization, fallback removal, and view rewrites into one ad-hoc set of commits; under nanopass discipline these would have been four separately-numbered passes each producing a verifiable output schema.

3. **Validation/typing per pass.** Three layers map cleanly onto propstore: (a) static grammar enforcement = Pydantic/dataclass schema definitions per version, refusing to construct an `S_v(n+1)` value from `S_v(n)` fields; (b) implicit grammatical guards at the pattern level = JSON-Schema or YAML-schema validation on stored docs at branch boundaries; (c) reference-implementation comparison = run the reading-side render policies before and after the pass and require identical results on the reference test corpus. Plus *verification passes* between each migration to assert structural invariants the type system can't express.

4. **Cumulative organization.** The 50-pass course schedule (Table 1, p.202) is the model: number passes sequentially, name them with category-prefix verbs (`remove-*`, `verify-*`, `convert-*`, etc.), group into "weeks" (or release windows), and require an automated test driver that compares each pass's output against the reference. Express each new schema as `extends` of the previous schema with `+ field` / `- field` / `+ table` / `- table` modifiers, so the schema delta itself is a first-class artifact (not just a git diff). The recent cutover left no machine-readable "schema-2026-04-27 → schema-2026-04-28" diff; under nanopass discipline that diff would be the migration spec.

Specific payloads:
- Build a `define-schema-version` and `define-migration` pair as the propstore analogue of `define-language`/`define-pass`.
- Insist that every storage migration carry a typed input schema reference and a typed output schema reference.
- Run a verifier pass (which is itself a `Sv -> Sv` migration that fails on invariant violation) immediately after every shape-changing migration.
- Maintain a sequenced log analogous to Table 1 — release-window grouped, category-prefixed, schema-version-stamped — so a future reader can reconstruct the migration history one pass at a time.
- Limitation to import: child and parent record types are disjoint; for propstore that means a migration must explicitly construct new objects, not mutate old ones in place — aligns directly with the project principle "Immutable except by explicit user migration."

## Open Questions
- [ ] Concrete propstore design: is the analogue of `void`/`datum` passes useful for storage migrations (e.g., cache-warming or sidecar reindexing)?
- [ ] Phase-ordering concerns appear at compile granularity; do storage migrations have an analogue (e.g., a normalization that becomes wrong after a later schema change)? If so, what's our equivalent of the "pass combiner"?
- [ ] How does the reference-implementation comparison map onto propstore? The natural analogue is render-policy output equality, but render policies are by design heterogeneous — do we instead pin a single "canonical render" as the reference?
- [ ] Should the inheritance discipline be additive-only for propstore migrations, or do we accept removal as a `-` mod with the same disjoint-record consequence?

## Collection Cross-References

### Already in Collection
- (none — this paper's references are compiler-construction papers and none are in the propstore collection)

### New Leads (Not Yet in Collection)
- Wang, Appel, Korn, Serra (1997) — "The Zephyr Abstract Syntax Description Language" — IR-only ancestor of `define-language`; useful baseline for what a propstore schema-definition layer looks like in isolation.
- Tarditi, Morrisett, Cheng, Stone, Harper, Lee (1996) — "TIL: a type-directed optimizing compiler for ML" — empirical evidence that per-pass IL type-checking catches bugs; closest precedent for the validation discipline propstore needs at every storage migration boundary.
- Dybvig, Hieb, Bruggeman (1993) — "Syntactic Abstraction in Scheme" — the `syntax-case` macro system that makes `define-language`/`define-pass` implementable; background for any host-language reimplementation.
- Wadler (1988) — "Deforestation: Transforming Programs to Eliminate Trees" — the technique nanopass authors hypothesize for fusing many independently developed improvement passes into a single fast pass.
- Nystrom, Clarkson, Myers (2003) — "Polyglot: An Extensible Compiler Framework for Java" — alternative OOP-based answer to "how does pass/IL extension scale?"; useful contrast for a propstore design discussion of which extensibility model fits Python.
- Click and Cooper (1995) — "Combining Analyses, Combining Optimizations" — super-optimizer line; nanopass argues *against* the monolithic structure these encourage. Read to understand the tradeoff.
- Lerner, Grove, Chambers (2002) — "Composing Dataflow Analyses and Transformations" — also super-optimizer-flavored.
- LaLonde, des Rivieres (1982); Whitfield, Soffa (1990) — phase-ordering background.

### Supersedes or Recontextualizes
- (none — this paper introduces a methodology rather than superseding any collection paper)

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)
- [A Component-Based Framework For Ontology Evolution](../Klein_2003_ComponentBasedFrameworkOntologyEvolution/notes.md) — Klein and Noy formalize ontology change as a typed log of basic/complex change operations on a *change ontology*, parallel to nanopass's typed `define-pass` clauses on a typed IL. Both papers argue that the *delta* between two structural versions should itself be first-class typed data, not merely a free-form diff. Klein's three-representation framework (structural diff + change-operation log + conceptual narrative) is the ontology-evolution analogue of Sarkar's (`define-language` + `define-pass` + reference-implementation comparison). For propstore, these two papers together specify almost the entire shape of a real schema-migration framework: Klein gives the *what changed* vocabulary, Sarkar gives the *how to chain typed transformations* discipline.
- [A Survey of Schema Versioning Issues for Database Systems](../Roddick_1995_SurveySchemaVersioningIssues/notes.md) — Roddick's vocabulary distinction (schema *modification* vs. schema *evolution* (data preservation) vs. schema *versioning* (retained past versions)) is the database-systems equivalent of nanopass's distinction between "same IL passes" and "IL-changing passes." A propstore migration framework needs both axes: Roddick's evolution/versioning architectural taxonomy plus Sarkar's typed-pass discipline within each migration.
- [Relational Lenses: A Language for Updatable Views](../Bohannon_2006_RelationalLensesLanguageUpdatable/notes.md) — Bohannon, Pierce, Vaughan define a typed combinator language where each combinator denotes a paired `get`/`put` and the type system enforces lens laws (GetPut, PutGet, PutPut). Sarkar defines a typed pass language where each pass denotes an `Li → Lj` transformer and the type system enforces grammar conformance plus reference-implementation equivalence. Both papers occupy the same design point — small typed combinator DSLs with statically-checked semantic laws — for two different problem domains (updatable views vs. compiler IRs). A propstore migration framework that wants *bidirectional* migrations (forward and rollback) would want to combine the lens combinator structure with nanopass's pass-expander pattern.
- [Preserving mapping consistency under schema changes](../Velegrakis_2004_PreservingMappingConsistencyUnder/notes.md) — Velegrakis, Miller, Popa decompose schema evolution into a small operator set (rename/copy/move/create/delete element; add/remove constraint) and require each operator to preserve mapping consistency (membership in the set of maximal logical associations after the change). This is exactly nanopass's discipline lifted from compiler ILs to database mapping systems: each operator is a "nanopass" between typed schema states whose well-typedness is the consistency criterion. Both papers argue that one-shot regeneration loses prior structure (user-chosen mappings in ToMAS, hand-tuned per-pass logic in nanopass) that incremental typed operator chains preserve. ToMAS additionally provides a similarity+support ranker for picking among multiple consistent rewritings — the one piece nanopass leaves to the compiler author.

## Related Work Worth Reading
- Wang, Appel, Korn, Serra (1997). "The Zephyr Abstract Syntax Description Language." USENIX DSL — IR-only ancestor.
- Tarditi, Morrisett, Cheng, Stone, Harper, Lee (1996). "TIL: a type-directed optimizing compiler for ML." PLDI — typed IL ancestor; explicit forerunner of "type-check the output of every pass."
- Nystrom, Clarkson, Myers (2003). "Polyglot: An Extensible Compiler Framework for Java." CC — extensibility-via-OOP alternative to language inheritance.
- van Reeuwijk (1992, 2003). Tm and template-based metacompilation — low-level relatives of `define-pass`.
- Wadler (1988). "Deforestation." ESOP — the technique nanopass authors hypothesize will let a "pass combiner" fuse independently developed improvement passes.
- LaLonde and des Rivieres (1982). "A flexible compiler structure that allows dynamic phase ordering." — phase-ordering background.
- Whitfield and Soffa (1990). "An approach to ordering optimizing transformations." — phase-ordering background.
- Click and Cooper (1995). "Combining analyses, combining optimizations." TOPLAS — super-optimizer line; nanopass argues *against* the monolithic structure these encourage.
- Lerner, Grove, Chambers (2002). "Composing dataflow analyses and transformations." POPL — also super-optimizer-flavored.
