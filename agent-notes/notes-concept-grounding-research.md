# Concept Grounding and Import Research

Date: 2026-08-04
State: read-only research in progress; this note is intentionally uncommitted.

## Current findings

- Propstore's `grounding` package is Datalog/ASPIC rule grounding: it compiles rules, instantiates grounded rule/fact structures, and records grounding completeness. It is not Harnad-style symbol grounding.
- The live canonical `Concept` charter currently carries artifact identity, canonical name, optional definition, category values, an ontology reference, and an optional OntoLex-Lemon lexical entry.
- Lemon separates surface form, lexical entry, lexical sense, and ontology reference. This handles homography and polysemy better than name-based identity, but the ontology URI remains another symbol unless its referent is independently grounded.
- Snapshot import preserves separate repository-scoped concept identities and rewrites typed references on an isolated import branch. Canonical-name equality does not merge concepts.
- Current alignment treats shared ontology URI as the only identity-bearing signal; matching names/tokens do not establish identity. Shared URI plus conflicting definitions produces attacks; otherwise candidates remain non-attacking. A human decides and promotes one alternative.
- `EquivalenceWitnessStore` records policy- and evidence-scoped witnesses without changing candidate identity. `SameAs` provides graded, defeasible identity assertions. These are directionally sound non-collapse mechanisms.
- Concept embeddings use canonical name, aliases, and definition. The code correctly labels similarity as heuristic; embeddings are candidate-generation evidence, not grounding or equivalence proof.

## Literature observations

- Harnad's proposed solution grounds a base vocabulary bottom-up in nonsymbolic iconic and learned categorical representations; higher-order symbols inherit grounding compositionally. Dictionary-only definition chains do not solve the problem.
- For a scientific knowledge store, "reality" is reached through observation, measurement, intervention, datasets, and instrument traces rather than direct access. A grounding record should preserve the observable property or referent, procedure, conditions, calibration/model, result/evidence, uncertainty, and provenance.
- Current ontology-matching SOTA is hybrid: lexical/structural/instance candidate generation, embeddings and LLM judgments, logical coherence checking/repair, and selective human validation. OAEI 2025 explicitly evaluates relations beyond equivalence (equivalent, broader, narrower, overlap, disjoint).
- Multimodal and vision-language-action models provide perceptual/action coupling, but they are fallible learned witnesses. They do not justify unconditional identity collapse.

## Architectural direction under consideration

- Keep concept artifact identity distinct from meaning/alignment claims.
- Represent grounding as typed, versioned evidence bundles rather than extra strings on `Concept`: lexical anchors; intensional constraints; positive/negative/borderline exemplars; measurement or discrimination procedures; action/intervention outcomes; context; provenance; uncertainty.
- Replace binary same/not-same import reasoning with typed mapping hypotheses: same individual, class equivalence, narrower, broader, overlap, disjoint, translation-under-policy, and unresolved.
- Treat candidate generators (URI equality, lexical match, embeddings, LLMs) as evidence producers only. Validate mappings through extensional tests, inferential/constraint preservation, logical coherence, operational probes, and expert review.
- Maintain mapping validity against exact source/target commits and invalidate or re-evaluate it when either concept or its grounding evidence changes.

## Open questions / blockers

- Decide whether Propstore should merely record epistemic grounding supplied by external observation systems or also execute grounding probes. The former fits the current repository architecture more naturally.
- Decide the generic owner and typed shape for grounding evidence before any implementation; it should not be embedded as a concept-family special-case if claims, predicates, quantities, and relations also need the mechanism.
- Clarify the exact semantics of promotion: selecting one imported artifact is not the same operation as asserting an equivalence mapping or creating a new reconciled concept.

## Next action

- Synthesize a concrete current-state critique and an ideal layered model for discussion, then identify the smallest useful vertical slice if implementation is later requested.

## Paper retrieval checkpoint - 2026-08-04

State: retrieval is in progress under the `research-papers:paper-retriever` protocol.

- Chrome DevTools access was verified against the user's live unlocked Chrome profile before retrieval began. The connector successfully listed the open pages.
- Existing relevant paper artifacts found and reserved for verification rather than duplication:
  - `papers/Buitelaar_2011_OntologyLexicalizationLemon`
  - `papers/Raad_2019_SameAsProblemSurvey`
- Successfully retrieved through the open-access/arXiv path so far:
  - Masse et al. 2008, *How Is Meaning Grounded in Dictionary Definitions?*
  - Kim et al. 2024, *OpenVLA: An Open-Source Vision-Language-Action Model*
  - Hertling and Paulheim 2023, *OLaLa: Ontology Matching with Large Language Models*
  - Qiang et al. 2023, *Agent-OM: Leveraging LLM Agents for Ontology Matching*
  - Lushnei et al. 2025, *Large Language Models as Oracles for Ontology Alignment*
  - Song et al. 2025, *GenOM: Ontology Matching with Description Generation and Large Language Model*
  - Spivak and Kent 2011, *Ologs: a categorical framework for knowledge representation*
  - Spivak 2010, *Functorial Data Migration*
  - Schultz and Wisnesky 2015, *Algebraic Data Integration*
  - Schultz et al. 2016, *Algebraic Databases*
  - Lange et al. 2012, *The Distributed Ontology Language (DOL): Use Cases, Syntax, and Extensibility*
- Blocker/fallback:
  - Harnad's *The Symbol Grounding Problem* resolved to the correct arXiv metadata and DOI, but both legacy arXiv PDF URLs returned 404. The retriever correctly created no incomplete directory. Retrieve it from the known author/publisher-hosted copy, then materialize metadata.
- Observations:
  - Semantic Scholar returned rate-limit failures in several runs, but arXiv metadata and PDFs still succeeded; this is not a retrieval blocker.
  - The title search helper is poor for older chapters and workshop papers, so their identity must be resolved with known DOI or canonical author/publisher URLs rather than accepting fuzzy search results.
- Next action:
  - Finish the strong-identifier arXiv batch, resolve the older-title manifest, use Chrome/configured fallback only where open retrieval fails, then validate every PDF signature, size, title, authors, year, and metadata file.

### Retrieval continuation

- Additional open-access retriever successes:
  - Lange et al. 2012, *DOL: Ontology Integration and Interoperability Applied to Mathematical Formalization* (explicit output directory avoided a canonical-name collision with the DOL use-cases paper)
  - Jimenez-Ruiz and Cuenca Grau 2011, *LogMap: Logic-Based and Scalable Ontology Matching*
  - Clark and Brennan 1991, *Grounding in Communication*
  - Spivak and Wisnesky 2012, *Relational Foundations for Functorial Data Migration*
  - Brown, Spivak, and Wisnesky 2019, *Categorical Data Integration for Computational Science*
- Direct open-repository PDFs downloaded and signature/size validated:
  - Harnad 1990, *The Symbol Grounding Problem*; metadata subsequently materialized from the DOI
  - Steels 2001, *Language Games for Autonomous Robots*
  - Hitzler et al. 2005, *What Is Ontology Merging? A Category-Theoretical Perspective Using Pushouts*
  - Goguen and Burstall 1990 report, *Institutions: Abstract Model Theory for Specification and Programming*
  - Jones, Bergen, and Trott 2024, *Do Multimodal Large Language Models and Humans Ground Language Similarly?*; metadata materialized from DOI
  - Gubelmann 2024, *Pragmatic Norms Are All You Need*; metadata materialized from DOI
  - Jones and Trott 2024, *Multimodal Language Models Show Evidence of Embodied Simulation*
  - Li et al. 2024, *GroundingGPT*
- Unresolved or manual-metadata work:
  - The CiteSeerX Zimmermann 2006 direct PDF URL returned 404 and left only an empty identity-specific directory; use the institutional author-repository copy.
  - Semantic Scholar could not resolve Steels or the two ACL entries `2024.lrec-main.1041` and `2024.acl-long.360`; their canonical PDFs are present, so materialize metadata from canonical bibliographic records.
  - Hitzler and Goguen/Burstall also need final metadata materialization.
  - Harnad 1995 is canonical public HTML and remains queued for sandboxed Chrome print-to-PDF.

### Retrieval checkpoint - Chrome fallbacks complete

State: all previously unresolved core papers now have validated PDF artifacts; metadata and final coverage auditing remain in progress.

- Chrome access was re-confirmed through the live DevTools connector; no unlock was required.
- Chrome's PDF viewer downloaded Zimmermann et al. 2006, *Formalizing Ontology Alignment and its Operations with Category Theory*, from Wright State CORE Scholar. The resulting 13-page PDF has a valid `%PDF` signature and is 261,720 bytes.
- Chrome headless printing captured Harnad 1995, *Grounding Symbols in Sensorimotor Categories with Neural Networks*, from the canonical Southampton HTML. The resulting 4-page PDF has a valid `%PDF` signature and is 132,670 bytes.
- The paper retriever was also run for Sui et al. 2025, *From Grounding to Manipulation*. Semantic Scholar rate limiting prevented metadata resolution, so the protocol's direct open-access fallback retrieved the canonical ACL PDF; it is valid and 4,209,546 bytes.
- Observation: publisher downloads handled by Chrome may initially appear as UUID-named `.tmp` files even after the complete PDF bytes are present. Validate the signature and size before moving such a file into its identity-specific paper directory.
- Non-blocking cleanup issue: the temporary Chrome headless profile remains at `.tmp-paper-retriever-harnad-profile` because the command safety layer rejected recursive removal after validation. It contains no reparse points and is not a paper artifact.
- Next action: retrieve the OAEI 2025 results and Agent-OM results papers, materialize canonical metadata for direct-download fallbacks, validate every targeted `paper.pdf` and `metadata.json`, and report any unresolved item explicitly.

### Paper-reader checkpoint - wave execution started

State: retrieval is complete and `research-papers:paper-reader` is now the active workflow for all 29 newly retrieved papers.

- Final retrieval gate: 29/29 paper directories contain a valid `%PDF` file over 100 KiB and parseable metadata with non-empty title, author list, and year.
- Added the canonical ACL paper *From Grounding to Manipulation*, the OAEI 2025 campaign results paper, and the Agent-OM OAEI 2025 results paper after the retriever's Semantic Scholar resolution path was rate-limited or returned no record; each direct open-access fallback PDF passed signature and size checks.
- Read the full `paper-reader` workflow and its required nested `reconcile` workflow. Shared reconciliation, `papers/index.md`, `papers/keymap.tsv`, and `papers/_reader_done.tsv` are reserved for the root agent as a serialized collection-wide step.
- User explicitly requested subagents. Three strongest-full-model readers are running in waves, one paper per agent turn, with exclusive paper-directory ownership and instructions to visually inspect every page, write incrementally, and never substitute OCR/text extraction for the page-image lane.
- Wave 1 assignments: Schultz et al. 2016 *Algebraic Databases* (83 pages), Spivak and Kent 2011 *Ologs* (52 pages), and Goguen and Burstall 1990 *Institutions* (50 pages).
- Complete page-image lanes have now been rendered and count-verified for every paper: 29 directories and 727 `page-NNN.png` images total. The future waves can begin at visual page inspection.
- Observation: long helper runs may return an execution session id after the first rendered paper; the session must be polled to completion so later papers in the batch are not mistaken for completed work.
- Current blocker: none in paper retrieval or rendering. The temporary Chrome profile cleanup remains safety-policy-blocked but does not affect paper reading.
- Next action: complete Wave 1 paper-owned artifacts, audit them against the skill, serialize reconciliation/index/keymap/ledger updates, then dispatch the next three one-paper reader turns. Continue waves until all 29 papers are fully processed and collection validation passes.

### Paper-reader checkpoint - Wave 1 progress

State: Wave 1 remains three distinct papers assigned one-per-reader; there is no duplicate reading dispatch.

- Reader A owns only Schultz et al. 2016, *Algebraic Databases* (83 pages). It has read through page 61 and has written 42,994 bytes of incremental notes; the remaining pages and final paper-owned artifacts are still in progress.
- Reader B owns only Spivak and Kent 2011, *Ologs* (52 pages). It has visually read all 52 page images and produced notes, description, abstract, citations, and metadata; final audit is in progress.
- Reader C owned only Goguen and Burstall 1990, *Institutions* (50 pages). It completed all five paper-owned text artifacts after visually reading all 50 images. Its notes are 42,820 bytes, citations preserve all 93 references, metadata is valid with `cite_key` first and `document_type: report`, and its scoped audit passed.
- Root independently confirmed the Goguen directory has 50 page images plus all five required text artifacts. No PDF or PNG was staged.
- Observation: the user's question about duplicate dispatch was answered with the exact one-paper-per-agent mapping. Future waves will preserve the same rule: each agent receives one new, distinct paper only after its prior turn completes.
- Current blocker: none. Wave 2 is intentionally held until all three Wave 1 readers finish, matching the requested wave discipline.
- Next action: receive the final two Wave 1 audits, run serialized reconciliation/index/keymap/ledger work for the three completed papers, then issue three distinct Wave 2 assignments.

### Paper-reader checkpoint - Wave 2 complete

State: Waves 1 and 2 have completed six distinct papers with no duplicate reader assignment.

- Wave 1 shared steps are complete for *Institutions*, *Ologs*, and *Algebraic Databases*: collection cross-references were added with strong links bidirectionally annotated, linked `papers/index.md` entries were appended, and canonical `papers/_reader_done.tsv` entries were created.
- The required keymap helper was run but failed before producing `papers/keymap.tsv`. The failure is isolated to three older, out-of-scope metadata records whose first author is an object rather than a string: `Guha_1991_ContextsFormalization`, `Josang_2001_LogicUncertainProbabilities`, and `Prakken_2006_FormalSystemsPersuasionDialogue`. Newly retrieved paper metadata is not the cause. These old records remain untouched.
- Wave 2 completed three distinct papers: Spivak and Wisnesky, *Relational Foundations for Functorial Data Migration* (48/48 images, all 17 references); Schultz and Wisnesky, *Algebraic Data Integration* (44/44 images, all 40 references); and Kim et al., *OpenVLA* (37/37 images, all 117 references).
- The two formal Wave 2 papers have been reconciled against the completed collection, indexed, and ledgered. OpenVLA's shared steps are next.
- OpenVLA notes contain 4,213 words of page-provenanced architecture, training, dataset, evaluation, ablation, and limitation extraction. Its five paper-owned artifacts passed the reader's audit.
- Temporary viewing composites remain at `C:\Users\Q\AppData\Local\Temp\openvla-reader-white` because two validated cleanup attempts were rejected before execution. The earlier `.tmp-paper-retriever-harnad-profile` also remains for the same policy reason. Neither is under `papers/`, and canonical PDFs/images are untouched.
- A mandatory checkpoint in Reader B created ignored, uncommitted `notes-schultz-algebraic-data-integration.md`; it is an audit note only and has not been staged.
- Current blocker: no reading blocker. Collection-wide keymap generation remains blocked by the three pre-existing incompatible metadata records.
- Next action: reconcile/index/ledger OpenVLA, then dispatch Wave 3 to three distinct papers: GenOM (37 pages), OAEI 2025 results (35 pages), and Agent-OM 2023 (31 pages).

### Paper-reader checkpoint - Wave 3 in progress

State: seven papers are fully reader-complete and Wave 3 is reading three distinct ontology-matching papers.

- OpenVLA's shared pass is complete. Root corrected two reader-audit gaps before indexing: `description.md` now uses the required tag frontmatter and single-paragraph format, while `citations.md` and `notes.md` now include key follow-up citations, related work, and collection cross-reference sections. It is indexed and ledgered as `kim2024openvla`.
- The keymap blocker is resolved. The three old metadata records were narrowly normalized from one-field author objects to the exact equivalent author strings, then the official `build_keymap.py` helper succeeded and wrote `papers/keymap.tsv`. Completed-paper keys were verified in the generated map.
- Wave 3 assignments remain one-per-reader: Song et al. 2025 *GenOM* (37 pages), Pour et al. 2025 *OAEI Results* (35 pages), and Qiang et al. 2023 *Agent-OM* (31 pages).
- Current persisted progress: GenOM through page 29, OAEI results through page 25, and Agent-OM explicitly through page 15 with its first incremental notes batch saved. A regex-derived `516` for Agent-OM is a reference-number false positive, not page progress.
- Agent-OM pages 7-8 required transparent-page white-background viewing composites outside `papers/`, at `C:\Users\Q\AppData\Local\Temp\agent-om-reader-white`; canonical page images are unchanged.
- Current blocker: none. Temporary viewing directories may remain if validated deletion is rejected by policy, as with OpenVLA.
- Next action: finish and audit all three Wave 3 paper-owned artifact sets, run serialized reconciliation/index/keymap/ledger updates, then dispatch Wave 4 to three new distinct papers.

### Paper-reader checkpoint - Wave 3 artifacts complete

State: all Wave 3 pages have been visually read and all five paper-owned artifacts exist for each paper; two final audits are concluding.

- Song et al. 2025 *GenOM*: 37/37 canonical page images read; `notes.md`, `description.md`, `abstract.md`, `citations.md`, and corrected `metadata.json` are present. The reader reports Appendix C and synthesis coverage; final directory audit is in progress.
- Pour et al. 2025 *Results of the Ontology Alignment Evaluation Initiative 2025*: 35/35 images read; all five artifacts are present, including all 71 references; final structural/content audit is in progress.
- Qiang et al. *Agent-OM*: 31/31 images read and audit passed. Notes contain 3,646 words covering architecture, prompts, retrieval, matching, reciprocal-rank fusion, validation, datasets, metrics, quantitative results, token costs, hyperparameters, limitations, reproducibility appendices, and the bundled 2025 follow-up. Citations preserve 89 archival plus 27 follow-up references. Metadata records the published 2024 identity and `qiang2024agentom` cite key despite the retrieval directory's earlier catalog year.
- Agent-OM's transparent-page composites remain at `C:\Users\Q\AppData\Local\Temp\agent-om-reader-white`; no stronger cleanup primitive was attempted after the established policy rejection pattern.
- The official collection keymap remains successfully generated after the earlier normalization; it will be refreshed after Wave 3 ledger additions.
- Current blocker: none.
- Next action: receive GenOM and OAEI final audit reports, reconcile/index/ledger all three Wave 3 papers, refresh keymap, then dispatch Wave 4 to three distinct papers.

### Paper-reader checkpoint - Wave 7 in progress

State: 19 of 29 new papers are fully read, reconciled, indexed, keyed, and ledgered; Wave 7 is reading three more distinct papers.

- Waves 4-6 completed ten additional papers without duplicate assignment: Functorial Data Migration, human-vs-MLLM grounding, GroundingGPT, LLMs-as-LogMap-oracles, foundation-model robotic manipulation, DOL use cases, LogMap, pragmatic norms and LLM symbol grounding, and Harnad's 1990 symbol-grounding paper.
- Wave 6 shared work is complete. Root added bidirectional collection links among LogMap and the LLM ontology matchers, and among Harnad, Gubelmann, and the empirical multimodal/action papers; then appended linked index entries and completion-ledger rows.
- The official keymap helper succeeded after Wave 6 and contains `jimenezruiz2011logmap`, `gubelmann2024pragmatic`, and `harnad1990symbol`. `git diff --check` also passed.
- Wave 7 remains one paper per reader: Zimmermann et al. 2006 on category-theoretic ontology alignment (13 pages), Brown et al. 2019 on categorical data integration (10 pages), and Masse et al. 2008 on meaning-grounded dictionary definitions (9 pages).
- Seven papers will remain after Wave 7: OLaLa, Agent-OM OAEI 2025, Steels's language games, the DOL mathematical-formalization paper, Jones and Trott on embodied simulation, Clark on grounding in communication, plus the two-paper final wave containing Hitzler on pushout merging and Harnad 1995. Because this list totals eight, the expected post-Wave-7 remainder is eight, not seven; the earlier arithmetic was corrected here.
- Current blocker: none. The agents are following the complete paper-reader skill and own only their respective paper directories; root retains all shared collection files.
- Next action: audit and reconcile Wave 7, then continue distinct-paper waves until the remaining eight papers and the final collection-wide integrity audit are complete.

### Paper-reader checkpoint - collection complete

State: all 29 newly retrieved papers are fully processed under the paper-reader workflow and the final collection audit passes.

- Every paper was assigned to exactly one reader per wave. Each reader reread the complete skill, visually inspected every canonical page image in order, produced all five paper-owned artifacts, and reported a scoped audit before root reconciled shared files.
- Final coverage is 29 unique ledger entries, 685 PDF pages, and 685 contiguous rendered PNGs. Every paper has nonempty `notes.md`, `description.md`, `abstract.md`, `citations.md`, and `metadata.json`; metadata cite keys are unique and first, authors are typed strings, document types are present, and required abstract/citation/description structures pass.
- Root completed bidirectional collection reconciliation, appended all linked `papers/index.md` entries, regenerated `papers/keymap.tsv` with the official helper, and appended `papers/_reader_done.tsv`. Every ledger directory occurs exactly once in the index and keymap.
- The identity gate caught one important retriever failure: the original `Clark_1991_GroundingCommunication/paper.pdf` was Barry Simon's unrelated 1973 mathematics paper. Chrome opened the correct Stanford author-hosted Clark/Brennan chapter; root downloaded and validated the 447,507-byte PDF, rendered 12 correct spreads covering printed pp.127-149, updated metadata, and moved the wrong source to recoverable temp quarantine at `C:\Users\Q\AppData\Local\Temp\propstore-clark-wrong-simon-20260804`. The reader then restarted and independently passed the full identity/page/artifact audit.
- The final format pass corrected three early abstract templates and three early citation headings to the exact paper-reader schema. A stale-cross-reference scan found zero remaining “awaiting reader pass” markers.
- Final repository gate: zero collection errors, zero tracked canonical PDFs/PNGs, zero staged binaries, zero staged files, and `git diff --check` clean. The original unrelated `pyghidra_mcp_projects/` remains untouched.
- The official keymap required narrow normalization of three pre-existing author fields from one-field `{name: ...}` objects to equivalent strings: Guha 1991, Jøsang 2001, and Prakken 2006. These task-induced metadata edits remain uncommitted with the new collection artifacts.
- Temporary white-background viewing composites and the earlier Chrome headless profile remain outside canonical paper assets where cleanup was rejected by the safety layer. No stronger cleanup operation was attempted.
- Current blocker: none. The collection is ready for cross-paper synthesis on grounding, concept import, relation vocabularies, category theory, and current ontology-matching approaches.

### Grounding-architecture synthesis checkpoint

State: the 29-paper reading phase is complete; an implementation-oriented research synthesis is in progress under `research-papers:research`.

- Current Propstore reality has been re-verified in production code: `Concept` owns canonical concept identity and OntoLex fields; alignment owns pinned imported alternatives plus an explicit decision; shared ontology URI is the only current identity-bearing alignment signal; equivalence witnesses never rewrite identity; `SameAs` is graded and defeasible; existing `propstore.grounding` is logical rule grounding, not symbol grounding.
- The missing capability is not another matcher. It is a generic, typed semantic-evidence subsystem able to record observation, discrimination, intervention/action, referential coordination, communicative repair, and normative-use witnesses without turning any of them into identity.
- The emerging synthesis rejects a scalar `grounded` flag. Grounding must be rendered as a context- and purpose-indexed profile over distinct dimensions: lexical/definitional, formal/ontological, perceptual, sensorimotor, causal-referential, communicative, and normative/inferential.
- Harnad supplies the non-symbolic anchor and compositional-inheritance story; Masse supplies the anchor/reachability constraint for definition graphs; Clark and Steels supply task-relative common-ground evidence and repair; Gubelmann supplies the competing norm-governed account and a warning not to collapse engineering capacities into one metaphysical symbol-grounding problem.
- Category theory supplies typed mapping objects, composition laws, preservation contracts, data migration, and merge universal properties. It cannot discover that two concepts mean the same thing. A pushout is valid only relative to an accepted mapping and a chosen category/morphism class; increasing correspondence expressivity can destroy merge-as-pushout.
- Current standards/implementation checks support reusing SOSA/SSN vocabulary for observations and actuations, PROV-O for derivation/activity provenance, OntoLex-Lemon for lexical senses/references, and a guarded SKOS-like mapping vocabulary. SKOS `exactMatch` is transitive and therefore too strong as the default evidence relation.
- Three distinct subagents are working in parallel on non-overlapping synthesis lanes: causal/perceptual/social grounding, categorical import/mapping, and current SOTA implementations. Each owns only its lane report; root owns the integrated report.
- Current blocker: none.
- Next action: receive and audit the three lane reports, integrate them into `reports/research-actual-grounding-architecture.md`, verify source links and architectural ownership, then deliver the report without implementing code.

### Grounding-architecture integration checkpoint

State: all three non-overlapping synthesis lanes are complete and the integrated report now exists at `reports/research-actual-grounding-architecture.md`.

- Causal/social lane: confirmed that grounding must be a product of independently typed, scoped, defeasible relations rather than a scalar or ladder. It supplied episode lifecycles and executable falsifiers for category, localization, action, communicative uptake, convention, and normative-use claims.
- Categorical/import lane: confirmed that category theory contributes typed mappings, preservation laws, composition, migration, and mapping-relative universal constructions, not mapping discovery. It supplied the crucial split between generic semantic-evidence and semantic-integration owners and the `verified/refuted/unknown/timeout/unsupported` verifier boundary.
- SOTA lane: verified current official implementations and licenses as of 2026-08-04. LogMap/MELT are the strongest reusable external matching/evaluation pieces; Hets is an optional GPL verifier; CQL has custom commercial terms; Agent-OM is non-commercial/share-alike; GenOM has no detected license; Ontohub is stale; multimodal/VLA systems remain evidence producers only.
- Root added the 29 July 2026 AgentMap preprint as a very recent research lead. Its joint equivalence/subsumption task reinforces first-class relation kind and direction but is too new to be a core dependency or policy authority.
- The integrated report's architectural conclusion is now: one generic semantic-evidence owner, one separate generic semantic-integration owner, existing family-specific proposal/identity/promotion owners unchanged, and no direct path from similarity/model output to canonical mutation.
- Current blocker: none.
- Next action: run the final report/link/format audit, obtain exact memory citation line ranges, update the plan, and deliver the report. No code implementation is authorized or planned in this turn.

### Architectural correction checkpoint - 2026-08-05

State: revising `reports/research-actual-grounding-architecture.md` in response to the user's review; no production code changes are authorized.

- Confirmed the large miss in live Propstore code. Coreference already stores rival merge arguments and computes clusters at render time through `ArgumentationFramework`, with grounded semantics withholding mutually attacked merges and preferred semantics returning rival clusters. `structured_projection.py` already selects grounded, complete, preferred, and stable semantics without reimplementing them.
- Therefore grounding must not introduce a parallel support/attack lifecycle or stored `supported/attacked/disputed/unknown` status. Evidence facts and grounding conclusions become structured arguments; the grounding profile is a query-time AF projection under named semantics. Grounded gives the skeptical view; preferred/stable expose rival grounding stories.
- Confirmed the quantitative value layer already exists. `PropstorePrAF` carries `OpinionWithProvenance`; missing calibration is `NoCalibration` or a vacuous opinion. A grounding instrument statistic may enter this layer only through an explicit calibration with evidence count/base rate/provenance. It must not be fused by inventing confidence.
- Read the current authority in `C:\Users\Q\code\meanings\reports\grounding-question.md`. Its standing result is negative but precise: the existing `G = I(X;V)` implementation has deterministic `V` given row identity, so `G = H(V)` and measures the verdict histogram, not external contact. Mutual information is also invariant to symbol relabeling; a human codebook can still supply the borrowed symbol-world mapping.
- Reconciliation: `G = I(X;V)` is retained as an optional, apparatus-relative evidence statistic only when `X`, `V`, sampling, coarsening, nulls, independence assumptions, and intended warrant are declared and an incorrect symbol-world binding changes the independently measured outcome. It does not define the grounding profile. An AF evaluates what an apparatus run warrants.
- Confirmed executable near-term instruments in `meanings`: the earlier implicit base is 326 ICs (317 L0 plus nine augmented); current campaign arms later moved to 331/484 ICs. Dictionary FVS/SCC analysis locates construction-relative anchor positions but does not supply external grounding. Existing cross-dictionary work finds a stable MinSet size budget (OEWN about 3.15%, GCIDE about 3.18%) but mostly local membership. Lancaster feasibility found only 775 eligible ICs before stricter controls, below the frozen 1,000-test gate, so no sensorimotor outcome was scored.
- The corrected first vertical slice will ingest/replay dictionary-graph anchoring and cross-dictionary stability as typed apparatus results, project their support/attacks through the existing AF layer, and preserve the honest conclusion: structural anchor budget supported; particular universal base and external grounding supply not established.
- Ontology matching/category theory will be reduced to a boundary section and delegated to the already-written sibling categorical-import and SOTA reports. The formal mapping pilot will be removed from the funded grounding plan.
- `NormUseEpisode` will be removed as a premature typed schema. Normative evidence remains an annotated transcript/source artifact plus ordinary claims/stances until operational field semantics and an executable consumer exist.
- Recording vs execution is now decided for this architecture: Propstore records, argues over, and renders probe results; `meanings` or external experiment systems execute them. No sensor/robot-specific episode union is built without a real producer.
- Subject-reference ordering is corrected: define the narrow subject/reference contract needed by the dictionary slice before closing any evidence union. Do not begin with a generic cross-family `GroundingSubject` union.
- Current blocker: none.
- Next action: rewrite the report around AF projection and apparatus results, rescope alignment material, revise the implementation sequence and effort, then audit links and consistency.
