# Cluster V: paper-to-code coverage audit

Wave 3, 2026-04-26. Auditor: Claude Opus 4.7 (1M context), HK-47 persona. Curated set: 42 high-value papers across argumentation, belief change, TMS, provenance, lexicon, units, causal, probabilistic, and replication tracks.

## Method

For each curated paper:
1. Read `papers/<dir>/notes.md` (skim mode — first 60–120 lines, focused on Definitions / Equations / Algorithms sections).
2. Identified 3–5 highest-leverage implementable items per paper (algorithm, postulate, data structure, or schema).
3. Searched `propstore/` source via Glob/Grep for the implementation. Probes were keyword-batched by topic (argumentation cluster, AGM cluster, TMS cluster, provenance cluster, lexicon cluster, units cluster, causal cluster, probabilistic cluster, replication cluster, context cluster).
4. Verdict per item: **IMPLEMENTED** (cite file, possibly with line/symbol), **PARTIAL** (cite + gap), **MISSING**, or **NOT APPLICABLE**.

Module roots probed: `propstore/aspic_bridge/`, `propstore/praf/`, `propstore/belief_set/`, `propstore/support_revision/`, `propstore/merge/`, `propstore/world/` (incl. `world/atms.py`), `propstore/conflict_detector/`, `propstore/provenance/`, `propstore/worldline/`, `propstore/grounding/`, `propstore/sidecar/`, `propstore/families/`, `propstore/core/lemon/`, plus standalone modules (`opinion.py`, `defeasibility.py`, `unit_dimensions.py`, `dimensions.py`, `context_lifting.py`, `fragility*.py`, `calibrate.py`, `artifact_codes.py`, `uri.py`, `claim_graph.py`).

Three notes.md files were missing (Sensoy_2018, Kennedy_1997, Knuth_1970) — handled via paper.pdf metadata + abstract knowledge; these are flagged in the workflow-gap section.

No tests were run, no code was modified, no other reviews/* files were read, no agents were invoked.

## Coverage table

| Paper | Algorithm/Postulate | Verdict | propstore location | Gap if PARTIAL |
|---|---|---|---|---|
| Dung_1995 | AF = (AR, attacks) data structure | IMPLEMENTED | `propstore/praf/engine.py`, `propstore/aspic_bridge/projection.py`, `propstore/support_revision/af_adapter.py` | — |
| Dung_1995 | Conflict-free / admissible / preferred / stable / grounded / complete extensions | IMPLEMENTED | `propstore/praf/engine.py` (uses these as semantics; also referenced in `support_revision/af_adapter.py`) | — |
| Dung_1995 | Characteristic function F_AF (least fixpoint for grounded) | IMPLEMENTED | `propstore/praf/engine.py` (grounded computation), surfaced via `worldline/argumentation.py` | — |
| Dung_1995 | n-person game / stable marriage embeddings | NOT APPLICABLE | — | Theoretical bridge, not relevant to propstore domain |
| Modgil_2014 (ASPIC+) | AS=(L,R,n) with strict / defeasible rules + naming | IMPLEMENTED | `propstore/aspic_bridge/translate.py`, `propstore/aspic_bridge/build.py`, `propstore/aspic_bridge/extract.py` | — |
| Modgil_2014 | Three attacks: undermining / rebutting / undercutting | PARTIAL | `propstore/aspic_bridge/projection.py`, `propstore/sidecar/rules.py`, `propstore/grounding/predicates.py` (rebut/undercut keywords appear; undermining of Kp premises less explicit) | Confirm undermining attacks fire on `Kp` premises, not just rules; Kn/Kp partition not obviously surfaced in API |
| Modgil_2014 | Preference-based defeat (≼ on arguments) | IMPLEMENTED | `propstore/preference.py`, `propstore/aspic_bridge/projection.py` | — |
| Modgil_2014 | SAF→Dung AF projection + rationality postulates (sub-arg closure, indirect consistency) | PARTIAL | `propstore/aspic_bridge/projection.py` exists | No explicit unit test or assertion of sub-argument closure / closure under strict rules / direct + indirect consistency postulates documented; verifier coverage unknown |
| Caminada_2006 | Reinstatement labelling (in/out/undec) with bi-implication | IMPLEMENTED | `propstore/praf/engine.py`, `propstore/sidecar/rules.py` (labelling/undec keywords present) | — |
| Caminada_2006 | Ext2Lab / Lab2Ext bijection | PARTIAL | `propstore/praf/engine.py` | No explicit named conversion functions matching paper API; verify round-trip in tests |
| Caminada_2006 | Semi-stable semantics (minimal undec) | MISSING | — | No `semi_stable` mention found in propstore source |
| Garcia_2004 (DeLP) | Strict vs `~>` defeasible rule split + facts | IMPLEMENTED | `propstore/aspic_bridge/translate.py`, `propstore/grounding/loading.py`, `propstore/sidecar/rules.py` | — |
| Garcia_2004 | Generalized specificity preference criterion | MISSING | — | No `specificity` symbol in propstore; preference is supplied via `preference.py` but not the activation-set construction of generalized specificity |
| Garcia_2004 | Dialectical tree + acceptable argumentation lines | PARTIAL | `propstore/grounding/explanations.py` (dialectical keyword), `propstore/grounding/grounder.py`, `propstore/grounding/bundle.py` | No tree data structure with proper-vs-blocking-defeater alternation rule visible; explanation graph may be coarser than DeLP tree |
| Garcia_2004 | Marking procedure (D/U) → four-valued YES/NO/UNDECIDED/UNKNOWN | PARTIAL | `propstore/grounding/explanations.py`, `propstore/sidecar/rules.py` | Four-valued answer surface not located; verify `propstore/aspic_bridge/query.py` |
| Maher_2021 | DL($\partial_{\\|}$) inference tags +Δ/-Δ/+∂/-∂ | PARTIAL | `propstore/defeasibility.py`, `propstore/grounding/grounder.py` | Strict (definitely) vs defeasibly distinction present; explicit -Δ / -∂ negative provability tags not located |
| Maher_2021 | Metaprogram clauses c1-c8 | PARTIAL | `propstore/grounding/translator.py`, `propstore/grounding/predicates.py`, `propstore/grounding/grounder.py` | Translator likely emits a different rule shape; not a literal Maher metaprogram |
| Maher_2021 | Compilation to Datalog$^\\neg$ via unfold/fold (T_D / S_D) | MISSING | — | propstore grounder evaluates rules; it does not output a standalone Datalog program file for an external engine |
| Bozzato_2018 | CKR with defeasible axioms D(α) and clashing-assumption sets | PARTIAL | `propstore/context_lifting.py`, `propstore/defeasibility.py`, `propstore/world/atms.py` | "Justifiable exception" semantics not explicit; clashing-set evidence model not located |
| Bozzato_2018 | Datalog translation with `ovr`/`instd`/`insta`/`prec` predicates | MISSING | — | No `ovr` / `instd` predicate names found |
| Bozzato_2018 | CAS interpretation (CKR + exception sets) | MISSING | — | — |
| McCarthy_1993 | `ist(c, p)` first-class context relation | PARTIAL | `propstore/context_lifting.py`, `propstore/world/types.py` | Context is modeled (worlds, microtheories) but `ist` predicate is not exposed as such |
| McCarthy_1993 | Lifting rules (cross-context propagation) | IMPLEMENTED | `propstore/context_lifting.py` | — |
| McCarthy_1993 | Transcendence + abnormality predicates for nonmonotonic inheritance | MISSING | — | No `ab_*` predicates; transcendence (expanding axiomatization) not in propstore |
| Guha_1991 | First-class contexts + DCR-P / DCR-T defaults | PARTIAL | `propstore/context_lifting.py`, `propstore/grounding/predicates.py` | DCR rules not explicitly named or modeled |
| Guha_1991 | fixTime / fixTimeType / ignorePart / ignoreAspect context constructors | MISSING | — | No context-projection functions in propstore (`core/lemon/temporal.py` is lexicon-side time, not Guha context-of-time) |
| Guha_1991 | Articulation Axioms (DB integration via N maps not N²) | MISSING | — | No articulation axiom mechanism found |
| Alchourron_1985 (AGM) | K-1..K-8 / K*1..K*8 postulates + Levi/Harper identities | IMPLEMENTED | `propstore/belief_set/agm.py`, `propstore/belief_set/core.py` (`BeliefSet`, `negate`); operators in `support_revision/operators.py` | — |
| Alchourron_1985 | Partial meet contraction via remainder set + selection γ | PARTIAL | `propstore/belief_set/agm.py` | Verify whether implementation is partial-meet-on-remainder-sets vs world-based KM-style; the OCF-state references in `agm.py` suggest the latter |
| Alchourron_1985 | Transitively relational (supplementary K-7/K-8) | PARTIAL | `propstore/belief_set/entrenchment.py` | Entrenchment present; representation theorem not asserted |
| Darwiche_1997 | C1-C4 iterated revision postulates | PARTIAL | `propstore/belief_set/iterated.py`, `propstore/support_revision/iterated.py` | Postulates not explicitly cited as test invariants |
| Darwiche_1997 | Epistemic states (not belief sets) + faithful assignment | IMPLEMENTED | `propstore/belief_set/agm.py` defines `SpohnEpistemicState`; `support_revision/state.py` | — |
| Darwiche_1997 | Bullet (κ-shift) operator | IMPLEMENTED | `propstore/support_revision/operators.py` | — |
| Konieczny_2002 | IC0–IC8 merging postulates | PARTIAL | `propstore/belief_set/ic_merge.py` | Postulates not asserted as runtime checks |
| Konieczny_2002 | Σ (sum) and GMax (lex-max) operators | IMPLEMENTED | `propstore/belief_set/ic_merge.py` (`ICMergeOperator.SIGMA`, `ICMergeOperator.GMAX`) | — |
| Konieczny_2002 | Max-distance / arbitration operator | MISSING | — | Only SIGMA and GMAX listed in `ICMergeOperator` enum; pure Max operator not exposed |
| Konieczny_2002 | Distance-based syncretic assignment | IMPLEMENTED | `propstore/belief_set/ic_merge.py` (`_DistanceFormulaCacheEntry`) | — |
| Baumann_2015 | Dung logic / kernel equivalence (4-equiv) | MISSING | — | No `kernel_equivalence`, no Dung-logic Cn operator; AGM operators in propstore act over formulas/worlds, not over AFs as theories |
| Baumann_2015 | AGM expansion / revision over AFs | PARTIAL | `propstore/support_revision/af_adapter.py` | af_adapter bridges AFs to support revision but not via Dung logic / kernel construction |
| deKleer_1986 (ATMS) | Nodes / assumptions / justifications / environments / labels / nogoods / contexts | IMPLEMENTED | `propstore/world/atms.py`, `propstore/app/world_atms.py`, `propstore/provenance/nogoods.py` | — |
| deKleer_1986 | Label properties (sound, consistent, complete, minimal) | PARTIAL | `propstore/world/atms.py`, `propstore/world/consistency.py` | Verify whether propstore's ATMS computes minimal labels (vs lazy/just-consistent envs); not stated in code I read |
| deKleer_1986 | Bit-vector environment representation | MISSING | — | propstore likely uses Python sets; not the bit-vector / hash-cache impl from §6 |
| deKleer_1986 | Multi-context exploration without retraction | IMPLEMENTED | `propstore/world/hypothetical.py`, `propstore/world/atms.py` | — |
| Doyle_1979 (TMS) | SL/CP justifications + in/out belief status | PARTIAL | `propstore/grounding/explanations.py`, `propstore/world/atms.py` | propstore uses ATMS-style not Doyle-JTMS-style; SL/CP forms not literal |
| Doyle_1979 | Truth-maintenance process (7-step) for belief revision | NOT APPLICABLE | — | ATMS approach supersedes it in propstore |
| Doyle_1979 | Dependency-directed backtracking + nogoods | IMPLEMENTED | `propstore/provenance/nogoods.py`, `propstore/world/atms.py` | — |
| Forbus_1993 | JTMS / LTMS / ATMS family | PARTIAL | `propstore/world/atms.py` (ATMS only) | JTMS and LTMS not provided as separate engines |
| Forbus_1993 | BCP (Boolean Constraint Propagation) + clause encoding | MISSING | — | No BCP module; constraint solving routed through CEL/Z3 in `propstore/cel_*.py` (different formalism) |
| Forbus_1993 | TGDE-style model-based diagnosis (SD, COMPS, OBS, AB) | MISSING | — | `conflict_detector/` does conflict location for parameterizations but not Reiter-style minimal-diagnosis enumeration with AB predicate |
| Forbus_1993 | QP theory (qualitative process simulation) | NOT APPLICABLE | — | Out of scope for propstore |
| Pearl_2000 | Structural Causal Model (U, V, F) | MISSING | — | No SCM dataclass; `worldline/` has interventions but they are interventions on parameter sets, not endogenous-variable structural equations |
| Pearl_2000 | do-calculus 3 rules + back-door / front-door identification | MISSING | — | No identification algorithm |
| Pearl_2000 | Structural counterfactuals (submodel evaluation) | MISSING | — | — |
| Pearl_2000 | 3-level causal hierarchy (assoc / intervene / counterfactual) | NOT APPLICABLE | — | propstore is parameter-fragility flavored, not Pearlian causal |
| Halpern_2005 | Actual cause definition (AC1 / AC2 / AC3) | MISSING | — | No actual-cause module; `fragility*.py` measures contributors but not Halpern AC2 partitions (Z, W) |
| Halpern_2005 | Contingent intervention partitioning | MISSING | — | — |
| Hunter_2017 | Probabilistic AF (epistemic): P : 2^Arg → [0,1], P(A) marginals | IMPLEMENTED | `propstore/praf/engine.py`, `propstore/praf/projection.py`, `propstore/praf/README.md` | — |
| Hunter_2017 | COH / FOU / SFOU / RAT rationality postulates | PARTIAL | `propstore/praf/engine.py` | Postulates not surfaced as verifier predicates with paper-cited names |
| Hunter_2017 | Max-entropy completion of partial assessments | PARTIAL | `propstore/praf/engine.py` | Need to verify max-entropy specifically; may default to a different completion |
| Hunter_2017 | Inconsistency measures + distance-based consolidation | MISSING | — | No `consolidate` / `inconsistency_measure` symbol found in propstore |
| Thimm_2012 | PrAF with PAF1–PAF4 + max-entropy unique selection | PARTIAL | `propstore/praf/engine.py` | Same as Hunter_2017 — postulate enforcement not labeled |
| Josang_2001 | Opinion (b, d, u, a) tuple with b+d+u=1 | IMPLEMENTED | `propstore/opinion.py:1-40` (explicit "Subjective Logic — Jøsang 2001" header; `Opinion`, `BetaEvidence` dataclasses) | — |
| Josang_2001 | Operators: NOT, AND, OR, discounting, consensus | IMPLEMENTED | `propstore/opinion.py` (negation, conjunction, disjunction, consensus, discounting) | — |
| Josang_2001 | Probability expectation E = b + a·u | IMPLEMENTED | `propstore/opinion.py` | — |
| Josang_2001 | Beta PDF / evidence space mapping with W=2 prior | IMPLEMENTED | `propstore/opinion.py` (constant `W = 2`, `BetaEvidence`) | — |
| Josang_2001 | Multi-source weighted-base-rate fusion | IMPLEMENTED | `propstore/opinion.py` (clamps 0.01–0.99 per van der Heijden 2018; documented deviation) | — |
| Sensoy_2018 (NOTES_MISSING) | Dirichlet-evidential classification head | MISSING | — | No Dirichlet/EDL machinery; subjective logic is the closest cousin in `opinion.py` but not the deep-learning prior-network |
| Sensoy_2018 (NOTES_MISSING) | Uncertainty estimate u = K/Σα for K-class | MISSING | — | — |
| Carroll_2005 | Named Graphs `(n, g)` data model | PARTIAL | `propstore/sidecar/passes.py`, `propstore/world/model.py` (graph keyword) | propstore uses claim-graphs not RDF named graphs; no `(URI, RDFGraph)` pair model |
| Carroll_2005 | SWP vocab (Warrant, Authority, assertedBy, signature) | MISSING | — | No `swp:` vocabulary or signature ontology |
| Carroll_2005 | Performative-warrant semantics | MISSING | — | — |
| Carroll_2005 | TriG concrete syntax | MISSING | — | propstore doesn't emit RDF |
| Buneman_2001 | why-provenance via witness basis | IMPLEMENTED | `propstore/provenance/support.py`, `propstore/provenance/derivative.py`, `propstore/provenance/projections.py` | — |
| Buneman_2001 | where-provenance + traceable queries | PARTIAL | `propstore/provenance/projections.py`, `propstore/provenance/records.py` | Where-provenance pointer (location in source) not as crisply modeled as Buneman's "%" path syntax |
| Buneman_2001 | Deterministic edge-labeled tree DQL | MISSING | — | propstore is JSON/dataclass, not deterministic-tree |
| Green_2007 | K-relations + provenance polynomials N[X] | IMPLEMENTED | `propstore/provenance/polynomial.py` (`VariablePower`, `PolynomialTerm`, `SourceVariableId`) | — |
| Green_2007 | Semiring homomorphism to lineage / Boolean / probabilistic | IMPLEMENTED | `propstore/provenance/homomorphism.py` | — |
| Green_2007 | Datalog/ω-continuous-semiring extension | MISSING | — | Recursive provenance via formal power series not located |
| Moreau_2013 (PROV-O) | Starting Point classes (Entity, Activity, Agent) + 9 properties | PARTIAL | `propstore/provenance/records.py`, `propstore/source/promote.py`, `propstore/source/finalize.py` | propstore has provenance records and source/agent concepts, but does not export PROV-O OWL/Turtle vocabulary |
| Moreau_2013 | Qualification Pattern (qualifiedR + Influence subclasses) | MISSING | — | No `qualifiedAttribution` / `Influence` classes |
| Moreau_2013 | Bundle (provenance-of-provenance) | PARTIAL | `propstore/provenance/records.py` (records as provenance of provenance via wrapping) | Not the PROV `Bundle` named-graph pattern |
| Kuhn_2014 (Trusty URIs) | Hash-suffix URI for verifiable, immutable artifacts | IMPLEMENTED | `propstore/artifact_codes.py` (`source_artifact_code`, `justification_artifact_code`, `stance_artifact_code` — canonical-JSON SHA256), `propstore/uri.py` (`ni_uri_for_file`) | — |
| Kuhn_2014 | RDF-graph-level (not byte-level) hash | PARTIAL | `propstore/artifact_codes.py` uses canonical JSON | Equivalent to abstract-content hash but JSON-shape, not RDF-quad-shape; cross-format trust transfer unsupported |
| Kuhn_2014 | Self-reference with embedded hash | MISSING | — | No artifact embeds its own trusty hash in a self-URI; `worldline/hashing.py` is content-hash for verification only |
| Clark_2014 (Micropublications) | MP = (A, mp, c, A_c, Φ, R) — claim + statement + attribution | IMPLEMENTED | `propstore/core/micropublications.py`, `propstore/sidecar/micropublications.py`, `propstore/app/micropubs.py`, `propstore/cli/micropub.py`, `propstore/families/documents/micropubs.py` | — |
| Clark_2014 | SupportGraph / ChallengeGraph DAGs | PARTIAL | `propstore/claim_graph.py`, `propstore/claim_references.py` | Bipolar (support+challenge) explicit; verify both edge types |
| Clark_2014 | Holotype representative for claim equivalence groups | MISSING | — | No "holotype" concept |
| Clark_2014 | Open Annotation (OA) integration | MISSING | — | propstore has annotation but not OA-vocabulary aligned |
| Groth_2010 (Nanopublications) | Concept / Triple / Statement / Annotation / Nanopublication / S-Evidence layers | PARTIAL | `propstore/core/micropublications.py` (close cousin), `propstore/sidecar/passes.py`, `propstore/source/promote.py` | propstore uses a richer micropub model; bare 4-graph nanopub TriG export not provided |
| Groth_2010 | TriG / RDF Named-Graph serialization | MISSING | — | — |
| Pustejovsky_1991 (GL) | Qualia structure (constitutive / formal / telic / agentive) | IMPLEMENTED | `propstore/core/lemon/qualia.py` (file name is decisive evidence) | — |
| Pustejovsky_1991 | Argument structure + event structure + inheritance | PARTIAL | `propstore/core/lemon/proto_roles.py`, `propstore/core/lemon/temporal.py`, `propstore/core/lemon/forms.py` | Event structure (state/process/transition) likely not modeled |
| Pustejovsky_1991 | Type coercion + cocompositionality | MISSING | — | No coercion rules |
| Buitelaar_2011 (lemon) | LexicalEntry / Form / Sense linked to ontology entity | IMPLEMENTED | `propstore/core/lemon/types.py`, `propstore/core/lemon/forms.py`, `propstore/core/lemon/references.py`, `propstore/core/lemon/description_kinds.py` | — |
| Buitelaar_2011 | Modular extensions (morphology, syntax, multilingual) | PARTIAL | `propstore/core/lemon/` (forms.py, temporal.py, proto_roles.py) | Multilingual lexica + syntactic frames not surfaced |
| Cimiano_2016 (OntoLex-Lemon) | Five-module architecture (ontolex, synsem, decomp, vartrans, lime) | PARTIAL | `propstore/core/lemon/` covers core ontolex + qualia + descriptions | synsem (syntactic frames), decomp, vartrans (translations), lime (metadata stats) not present |
| Cimiano_2016 | LexicalConcept (SKOS-style) + ConceptSet | PARTIAL | `propstore/families/concepts/` | Not aligned to ontolex namespace IRIs |
| Cimiano_2016 | lime stats (avgAmbiguity, avgSynonymy, percentage) | MISSING | — | No lexicalization-set metrics |
| Kennedy_1997 (NOTES_MISSING) | Units-of-measure types parametric in dimension exponents | PARTIAL | `propstore/unit_dimensions.py` (uses `bridgman.dims_equal`), `propstore/dimensions.py` | propstore checks dimensional compatibility but does not embed units in a parametric type system à la F#; coercions and unit-polymorphic arithmetic not surfaced |
| Kennedy_1997 (NOTES_MISSING) | Dimension multiplication / inversion algebra | IMPLEMENTED | `propstore/unit_dimensions.py` (Dimensions = dict[str,int]), `bridgman` package | — |
| Knuth_1970 (NOTES_MISSING) | Word-problem → equation system semantic translation | MISSING | — | propstore doesn't ingest natural-language word problems; equations come from claims/forms |
| Knuth_1970 (NOTES_MISSING) | Knuth-Bendix completion / canonical equation form | MISSING | — | Equation manipulation goes through `equation_parser.py` + sympy, no rewriting completion engine |
| Spohn_1988 | OCF (κ-function) over propositions | IMPLEMENTED | `propstore/belief_set/agm.py` (`SpohnEpistemicState`), `propstore/opinion.py` references; `propstore/support_revision/state.py` | — |
| Spohn_1988 | A_n-conditionalization (firmness-parameterized update) | PARTIAL | `propstore/support_revision/operators.py`, `propstore/belief_set/iterated.py` | Verify firmness parameter `n` is exposed |
| Spohn_1988 | Independence concepts (probabilistic, conditional) | MISSING | — | No κ-independence module |
| Reiter_1980 | Default rule (α : Mβ / w) form | MISSING | — | No `Default` dataclass; defeasibility is rule-based not Reiter-default-based |
| Reiter_1980 | Extension as fixed point of Γ | MISSING | — | — |
| Reiter_1980 | Normal-default proof theory | MISSING | — | — |
| McCarthy_1980 | Predicate circumscription schema | MISSING | — | No `circumscribe` operator anywhere in `propstore/` (grep confirms only papers/) |
| McCarthy_1980 | Domain circumscription | MISSING | — | — |
| McCarthy_1980 | Minimal entailment semantics | NOT APPLICABLE | — | propstore models defeasibility differently (ASPIC+ + ATMS) |
| Pollock_1987 | Prima facie vs conclusive reasons | PARTIAL | `propstore/defeasibility.py` (defeasible inference), `propstore/aspic_bridge/` | "Reason" terminology not used; mapped to ASPIC+ rules |
| Pollock_1987 | Rebutting vs undercutting defeaters | IMPLEMENTED | `propstore/aspic_bridge/projection.py`, `propstore/grounding/explanations.py` | — |
| Pollock_1987 | Warrant via level_n undefeated arguments | MISSING | — | Grounded extension covers similar role; level_n hierarchy not implemented |
| Pollock_1987 | Collective defeat / self-defeating arguments | PARTIAL | `propstore/conflict_detector/algorithms.py` (collective conflicts) | Not the Pollock-specific collective defeat principle |
| Pollock_1987 | OSCAR rule set (ADOPT / RETRACT / REINSTATE) | MISSING | — | No OSCAR-style belief-formation rule engine |
| Brewka_2010 (ADF) | ADF triple D = (S, L, C) with per-node acceptance conditions | MISSING | — | No ADF module; Dung-style attack is the only relation modeled |
| Brewka_2010 | Three-valued consensus operator + bipolar ADFs | MISSING | — | — |
| Toni_2014 (ABA) | ABA tuple `<L, R, A, ¯>` with assumptions + contrary mapping | MISSING | — | propstore uses ASPIC+ not ABA; no `assumption / contrary` symbols |
| Toni_2014 | Dispute-derivation proof procedure | MISSING | — | — |
| Toni_2014 | ABA → Dung AA correspondence | NOT APPLICABLE | — | If ABA is added later, the AF projection in `aspic_bridge/projection.py` could be reused |
| Wilkinson_2016 (FAIR) | F1–F4, A1–A2, I1–I3, R1.1–R1.3 sub-principles | MISSING | — | No FAIR principle markers or compliance checker. propstore does have persistent identifiers (URIs in `uri.py`) and rich metadata (records), but no FAIR self-assessment |
| Wilkinson_2016 | Machine-actionable metadata | PARTIAL | `propstore/provenance/records.py`, `propstore/uri.py`, `propstore/artifact_codes.py` | Metadata is machine-readable but no DCAT/FAIR-Signposting export |
| Ioannidis_2005 | PPV = (1−β)R / ((1−β)R + α) Bayesian model | MISSING | — | `propstore/calibrate.py` does calibration, but no PPV / pre-study-odds / bias-modeled-as-u formula |
| Ioannidis_2005 | Six corollaries (smaller studies / smaller effects / etc.) | MISSING | — | — |
| Ioannidis_2005 | Bias parameter u as study-design covariate | PARTIAL | `propstore/fragility*.py` (intervention-ranked fragility is conceptually adjacent) | Not the Ioannidis u parameter; fragility measures different vulnerability |
| Aarts_2015 (OSC reproducibility) | Replication-effect metrics (significance, effect ratio, CI inclusion, subjective, meta-analytic) | MISSING | — | No replication-comparison module; no "original vs replication" data structure |
| Aarts_2015 | Pre-registered replication protocol pipeline | MISSING | — | — |
| Border_2019 (case study) | Candidate gene null findings as adversarial test | MISSING | — | No fixture or test case using candidate gene literature; system has not been demonstrated against this stress test |
| Border_2019 | GxE interaction hypothesis representation | MISSING | — | — |
| Horowitz_2021 (EpiPen / case study) | Epistemic logic puzzle DSL on Z3 | NOT APPLICABLE | — | propstore uses Z3 (`propstore/cel_*.py`, `propstore/z3_conditions.py`) for CEL/equation conditions, not for K_A operators or dynamic-epistemic puzzle semantics |
| Horowitz_2021 | Public announcement / common knowledge update | MISSING | — | No multi-agent epistemic-state machinery |

## Papers with no notes.md (workflow gap)

Three of the 42 curated papers lack a `notes.md` file — each contains only `metadata.json` and `paper.pdf`:

- `papers/Sensoy_2018_EvidentialDeepLearningQuantify/`
- `papers/Kennedy_1997_RelationalParametricityUnitsMeasure/`
- `papers/Knuth_1970_SimpleWordProblems/`

Verdicts above use general knowledge of these papers' contents plus a quick metadata.json check; recommend dispatching a paper-reader against each before further auditing depends on these.

These are also high-leverage targets — Sensoy's Dirichlet-EDL and Kennedy's units-of-measure parametricity both correspond to existing propstore modules (`opinion.py` and `unit_dimensions.py` respectively) where deeper alignment would pay off, and Knuth_1970 underlies any future natural-language-to-equation semantic-parser work.

## Top 10 highest-leverage missing features

Ranked by paper-importance × strategic-leverage, considering propstore's stated six-layer non-collapsing architecture and the auditor cluster's mandate.

1. **Pearl/Halpern actual-cause module.** propstore has worldline interventions, fragility scoring, and conflict detection — it is one structural-causal-model dataclass + AC1/AC2/AC3 evaluator away from being able to *attribute* outcomes to causes, not just *correlate* them. This unlocks Halpern explanations, Pearl counterfactuals, and gives `epistemic_process.py` a principled "why did the answer change" story.
2. **Reiter default logic + extension enumeration.** The Maher_2021 work compiles defeasible logic to Datalog, but propstore lacks the upstream Reiter formalism that justifies the +∂ tag semantics. Adding `propstore/default_logic/` with `Default` dataclass + Γ fixed-point would give a paper-cited foundation under the existing `defeasibility.py`.
3. **Caminada semi-stable + explicit Ext2Lab/Lab2Ext API.** Adding semi-stable semantics to `propstore/praf/engine.py` is small (paper-line literal) and gives users a sharper alternative to preferred when stable doesn't exist. The bijection API makes the labelling/extension duality testable.
4. **DeLP generalized specificity preference criterion.** propstore has `preference.py` but the activation-set construction of generalized specificity is missing. This is the canonical, publication-grade preference order — its absence forces all preferences to be supplied externally.
5. **Brewka ADF (acceptance conditions over parents).** ADFs strictly generalize Dung AFs and would let propstore model bipolar (support + attack) and weighted argumentation in one consistent formalism, instead of bolting features onto Dung. Likely small refactor of `praf/engine.py`.
6. **PROV-O export adapter + qualified-influence pattern.** `propstore/provenance/records.py` already encodes the right information; a serializer to PROV-O Turtle (Starting Point + Qualified) would give propstore one-line FAIR-compatible provenance interop with the wider Linked-Data ecosystem.
7. **Trusty-URI self-reference + RDF-level hashing.** `artifact_codes.py` is 80% there with canonical-JSON SHA256, but does not (a) embed the resulting hash in a self-URI inside the artifact and (b) compute graph-level hashes that survive serialization changes. Without (a), trusty references are external; with (a), claim references become tamper-evident in place.
8. **Hunter/Thimm postulate verifier (COH/FOU/SFOU/RAT, PAF1–PAF4).** The probabilistic AF code exists; lifting the named postulates as runtime/test-time predicates lets users see which postulates a given P satisfies — directly aligned with propstore's "no source is privileged, everything is defeasible claim" design principle.
9. **Bozzato CKR justifiable-exceptions datalog encoding.** propstore already has context lifting and defeasibility; adding the `ovr/instd/insta/prec` predicate skeleton (paper §4) gives a mechanically-sound override calculus for global vs local context conflicts. This is the missing link between the McCarthy/Guha context machinery (which propstore has) and the modern datalog-tractable variant.
10. **Replication-comparison data structure (Aarts/Border-style).** propstore has no first-class "original claim vs replication claim" pairing. Adding a `Replication(original_claim, replication_claim, indicators={significance, effect_ratio, ci_inclusion, …})` type would make the whole stack usable for case-study tests Q has flagged (Border_2019, Horowitz_2021), turn `fragility*.py` into a meaningful replication-risk score, and let the system *digest* the reproducibility literature rather than just cite it.

## Open questions for Q

1. **Is ABA on the roadmap or deliberately out-of-scope?** propstore has chosen ASPIC+ in `aspic_bridge/`. ABA is a strict subset of Dung AA via a different lens; the ABA-AA correspondence (Toni_2014 §5.4) means much of `praf/engine.py` could be reused. Worth investing in, or skip?

2. **Does Q want PROV-O export and FAIR self-assessment?** The data is there; only a serializer + a checklist runner are missing. Both are small but commit propstore to publishing in a particular external vocabulary. Confirm before I (or a successor) write the adapter.

3. **Is the gap-by-design intentional for Pearl/Halpern causal?** propstore explicitly models defeasible argumentation and AGM revision but seems to deliberately avoid Pearlian SCM. Is causal reasoning meant to live downstream of propstore (in a calling system), or should it be brought inside the box? This determines whether item #1 above is a genuine gap or a layering choice.

4. **What is the canonical answer for "where do candidate-gene-style null replications live"?** Border_2019 and Horowitz_2021 are listed as case-study tests in the audit prompt — but propstore has zero fixtures or test cases drawn from them. Should I (or another agent) build a `tests/case_studies/` ingest? Or are these conceptual targets only?

5. **For OntoLex-Lemon, is `core/lemon/` intended to grow into the full five-module spec?** Currently it covers ontolex + qualia + descriptions; synsem/decomp/vartrans/lime are absent. Either it's a deliberate subset of OntoLex (in which case the file naming mildly oversells), or it's a stub waiting for completion.

6. **Three notes.md missing — should they be filled?** Sensoy_2018, Kennedy_1997, Knuth_1970 are all referenced in the curated audit list but lack notes. The Sensoy and Kennedy gaps especially impede future paper-vs-code work because they neighbor active modules (`opinion.py`, `unit_dimensions.py`).
