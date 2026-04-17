# Axis 8 — Real Capability and Potential

Compiled from cross-axis findings. Be real and precise: what can this actually do today, what is it strictly not, and where could it go with focused work?

## What propstore is today

Stripped of rhetoric, examined by code:

**A git-backed claim-and-stance store with branch-level non-commitment, an LLM-driven proposal pipeline that respects a promote boundary, an argumentation layer with real Dung and ASPIC+ surface, a genuinely high-fidelity de Kleer ATMS, a content-addressed sidecar for query, and a real datalog grounder via `gunray`. Surrounding that core are several modules that borrow the names of classical formalisms (AGM revision, Konieczny IC merge, Denoeux decision criteria, Jøsang WBF) while implementing operators that behave differently — useful operators, but not the ones the citations announce.**

This is not a small thing. The core works. The gaps are in the layer between "core works" and "CLAUDE.md's theoretical rhetoric."

## What propstore can do today, by verified capability

Capabilities below are verified against axis findings — either by positive finding, or by silence from every axis that could have contradicted them.

### Storage + merge
- Store claims, stances, sources, concepts, forms, contexts on git-backed branches (dulwich backend, content-addressed).
- Separate proposal branches for heuristic output; `pks promote` as the only path to source-of-truth mutation (axis 1 Finding 4.1 positive).
- Two-parent semantic merge commits with CEL/Z3-backed conflict classification (confirmed at `repo/merge_commit.py:146`; axis 3c).
- Partial-argumentation-framework output from merge, mapping cleanly onto Coste-Marquis 2007 partial AFs (axis 3c).
- Leximax / sum / max aggregation across merge frameworks for the small-|A| brute-force regime (axis 3c, `paf_merge.py`).

### Argumentation core
- Dung semantics (conflict-free, admissible, complete, grounded, preferred, stable) over a claim graph (axis 3a — some breadth gaps like semi-stable, ideal, stage, CF2 noted as missing, none advertised as present).
- ASPIC+ recursive argument construction per Modgil-Prakken 2018 Defs 1-22 (confirmed at `aspic.py:664-964`; axis 3a).
- Bipolar argumentation (Cayrol/Amgoud surface).
- Goal-directed backward-chaining via `query_claim` / `build_arguments_for` (confirmed at `aspic_bridge/query.py:65-126`; axis 3a).
- Probabilistic argumentation via PrAF with a treedecomp backend — within its *actual* complexity (row count `O(2^|defeats| * 2^|args|)`, not the advertised `O(2^tw)`).

### Uncertainty + fusion (as of 2026-04-14)
- Subjective logic opinions with enforced `b+d+u=1` invariant and first-class vacuous representation (`opinion.py:33-43`; recently hardened).
- Consensus fusion (cancellation-free `v = 1 - u` form as of commit 34d0074).
- CCF fusion via real van der Heijden 2018 Def 5 three-phase algorithm, reproducing the paper's Table I exactly, returning vacuous `(0, 0, 1)` on dogmatic disagreement (commit c7a9215). This is *the* correct behavior for honest ignorance under disagreement.
- Conjunction / disjunction (binomial).
- Base-rate fusion (propstore convention layered on Def 5 for the per-source prior case).
- `__eq__` / `__hash__` invariant-preserving (recent fix).

### Knowledge representation
- Content-addressed artifact store (`propstore/artifacts/`) with family-indexed document types.
- Dimensional-quantity ontology via pint (`form_utils.py`, `unit_dimensions.py`).
- SKOS-style concept taxonomy with `broader`/`narrower`/`related` relationships.
- Visibility-inheritance contexts (ancestry-based; not `ist(c, p)`-style).
- Partial micropublication structure — stance + evidence + source tracking, minus the context-qualified composition rule Clark 2014 specifies.

### Reasoning infrastructure
- ATMS per de Kleer 1986: nodes, justifications, assumptions, environment labels with minimality + consistency + completeness + soundness invariants, runtime-verified via `verify_labels()` at `world/atms.py:1016-1072` (axis 3e **high-fidelity** verdict, visually confirmed against paper PNG).
- Z3-backed condition satisfiability for CEL expressions — at the bool-valued projection.
- CEL type system (close to Google's CEL spec with propstore-specific extensions like `KindType.TIMEPOINT`).
- Tree decomposition for probabilistic argumentation backends.

### Defeasibility
- Datalog grounding via external `gunray` package, in the Diller 2025 §3 Def 7/9 sense (axis 7 positive verdict: "real datalog layer, not a label").
- ASPIC+ strict/defeasible rule-type distinction at the structural level (no priority information populated).

### LLM / heuristic layer
- LLM-driven stance classification into proposal branches (`propstore/classify.py`).
- Embedding-based similarity for concept alignment proposals (`propstore/embed.py`, `propstore/relate.py`).
- Jaccard-token reconciliation for sources (`source/alignment.py`).
- Sensitivity/fragility scoring — operates on fabricated dogmatic opinions today, but the plumbing is in place.

### CLI + tooling
- `pks` CLI with ~20 subcommands covering concept/context/claim/form/source/verify/validate/build/query/world/worldline/grounding/merge/import/log/diff/show/checkout/promote (confirmed at `propstore/cli/__init__.py`).
- Content-hash-addressed sidecar with on-demand rebuild.
- 2496 tests, 365 property-based via Hypothesis, running green at ~4.5 minutes for the property-marked subset.

## What propstore strictly is not today

The negations are as important as the affirmations.

- **Not a frame-semantic concept registry.** Fillmore 1982 frames do not exist in code.
- **Not a generative-lexicon system.** Pustejovsky 1991 qualia do not exist in code.
- **Not a lemon-compliant ontology lexicalization.** Buitelaar 2011 `LexicalEntry → Form → LexicalSense → OntologyReference` does not exist.
- **Not an `ist(c, p)` context system.** McCarthy 1993 contexts-as-logical-terms are implemented as visibility-inheritance tags.
- **Not an AGM belief revision system.** AGM postulates K*1-K*8 are not syntactically expressible over the current `BeliefAtom` representation; no postulate is property-tested.
- **Not a Konieczny IC merge system.** The candidate space is observed-values-product, not `μ`-models. Majority-vote-under-constraint, not belief-base merge.
- **Not a Denoeux BetP implementation.** The function labeled `pignistic` computes Jøsang's E(ω).
- **Not a WBF implementation.** The function labeled `wbf` computes aCBF with missing factors.
- **Not an AF revision implementation.** Baumann/Diller/Cayrol machinery is absent.
- **Not an honest-ignorance system.** `_DEFAULT_BASE_RATES` fabricates priors; `praf/engine.py` defaults to dogmatic_true; Z3 unknowns silently become OVERLAP; classify produces invariant-violating opinions; source trust defaults 0.5 without provenance.

These are not failures. They are unfinished work. The task is to either implement the missing machinery, or rename honestly — the review argues both are acceptable, as long as the choice is explicit.

## What propstore could become with focused work

Three independent-ish capability horizons.

### Horizon 1 — "A reasoning corpus that holds disagreement with provenance" (Z-tracks + A-P1 complete)

**Concrete capability:** every probability in the system carries provenance (measured, calibrated, defaulted, vacuous); every Z3 solver result distinguishes sat/unsat/unknown with explicit timeout handling; every LLM/heuristic output is tagged to a proposal family; every build-time filter moves to render-time policy; every CLAUDE.md citation is test-backed or retracted.

**What this enables:**
- Epistemic queries: "which claims in this corpus rest on defaulted priors?" — directly answerable.
- Audit workflows: "what did this claim look like before the Z3 solver timed out?" — recoverable.
- Trust propagation: "did any fusion in this argument's support chain use `status='vacuous'`?" — typed.
- Reproducibility: the review surfaced that every conclusion drawn from the current system is conditioned on invisible fabricated priors. Horizon 1 removes that.

**Timeline:** a week at this project's cadence (Z-1, Z-2, Z-3 agent-days each; A-P1 a few days).

**What no other open tool does this way:** typed provenance on a git-branch-level non-commitment store. Knowledge graphs with provenance exist (PROV-O, nanopublications); git-backed belief-revision systems exist in research prototypes; branch-level non-commitment with a typed honest-ignorance algebra does not ship anywhere else I am aware of.

### Horizon 2 — "A genuine semantic OS" (Track A complete — A-P1..P4)

**Concrete capability:** `LexicalEntry → Form → LexicalSense → OntologyReference` as the concept registry; `Frame` + `FrameElement` + `QualiaStructure` populating the sense slot; `ist(c, p)` as the primary claim shape; Clark micropublications as the composition rule.

**What this enables:**
- `pks query "what does climate-science-2024 believe about p.doubling-effect?"` — an `ist(c, p)` query, natively.
- Frame-element-typed attacks: "argument A attacks argument B because they bind incompatible frame elements to the same role" — first-class detection.
- Generative-lexicon reasoning: "what concepts can play the `telic` of 'knife'?" — a qualia-indexed query.
- Cross-repo concept alignment via lemon-aware sense matching, not Jaccard.
- Micropub-level citation + evidence linking — reproducible scientific argumentation units.

**Timeline:** three-to-four weeks at this project's cadence.

**What no other open tool does this way:** a lemon-shaped concept registry with frames, qualia, and first-class `ist(c, p)` contexts, backed by argumentation semantics and a non-commitment merge operator, is not something I can point to an existing implementation of. The research literature exists (the papers on the list); operational systems that cash them out do not.

### Horizon 3 — "A reference argumentation + revision framework" (Tracks A, B, C complete)

**Concrete capability:** AGM-postulate-verified revision operators; AF revision per Baumann/Diller/Cayrol; Konieczny IC merge at the model-theoretic level; defeasibility with real priority propagation; ABA as an alternative semantics where wanted.

**What this enables:**
- Reference implementation for argumentation researchers testing new operators against classical postulates.
- Test bed for LLM-assisted scientific reasoning where the argumentation infrastructure is trusted and the LLM's outputs are the proposal-level content.
- Benchmarks for merge + revision operators against real multi-source knowledge bases.

**Timeline:** months, but agent-months, not engineer-months. The papers are all in the corpus; the test infrastructure exists; the argumentation surface is already extensive.

**What no other open tool does this way:** I do not know of a single research or production codebase that implements AGM + DP + IC + AF revision all together with postulate-verified property tests over a real-world non-commitment knowledge store. Some research prototypes do one postulate family; none do all.

## Proximal capabilities worth pursuing in order

1. **Z-1 + Z-2 bundle + A-P1** (Horizon 1). Gives propstore a qualitatively new property (typed provenance + honest ignorance) with minimum paper dependency. Every subsequent horizon benefits.
2. **A-P2 + A-P3** (partial Horizon 2 — concept substrate). Lemon + frames + qualia. Changes the concept registry from SKOS-adjacent to semantic-web-native. Large alignment/reconciliation wins.
3. **A-P4** (full Horizon 2 — context substrate). `ist(c, p)` + micropubs. The biggest migration; the most distinguishing capability.
4. **Z-3 citation cleanup** (cross-cutting). Every touched module gets its citations fixed; a `docs/gaps.md` replaces CLAUDE.md's Known Limitations. This is cheap but uniquely important: it is the only intervention that directly addresses the "citing paper for authority while implementing something different" pattern that appears across the review.
5. **Track B** (Horizon 3 part 1). Real AGM. The revision module becomes what its name advertises.
6. **Track C** (Horizon 3 part 2). Defeasibility semantics settled; priority information flows end-to-end.

## Honest assessment of where it could go with a little help

The project has completed, in its first month, what most academic research prototypes attempt in two-to-three years. The core is unusually competent (ATMS is high-fidelity; ASPIC+ argument construction is verified against the paper; CCF was fixed to the paper's Table I within days of discovery; git-backed non-commitment is a genuinely novel composition). The gaps are in *principle adherence* (the system lies about its confidence in several places) and *semantic-substrate cashing-out* (the rhetoric is ahead of the code).

Both are fixable at the speed this project operates at. Horizon 1 is a week. Horizon 2 is a month. Horizon 3 is a few months. At the end of those months, propstore plausibly becomes one of the *reference* open implementations of non-commitment argumentation-backed knowledge storage. There are narrower tools (provenance-only; argumentation-only; revision-only). There is not, to my awareness, another tool that composes them.

The failure mode to avoid: letting the rhetoric-code gap widen. The review found fifteen structural limitations not mentioned in the declared Known Limitations. The principled remediation is not just to close the gaps — it is to install the discipline that prevents their recurrence. Every citation property-tested. Every claim in CLAUDE.md verified by a finding or a workstream. Every "implemented" label backed by a passing postulate test. Without that discipline, the gaps will reopen faster than agents can close them.

## Open questions

- Is the AI-safety / interpretability application the primary intended use, or is it argumentation research, or scientific reasoning tooling, or something else? The ordering of capability horizons depends on this.
- How tolerant are you of breaking changes during the Horizon 2 migration? Track A's P4 in particular is the biggest migration in the project's short history.
- Is there a funding / publication / deployment pressure that prioritizes one horizon over another, or is this a "build the right thing at agent speed" project with no external clock?
