---
title: "LLM-ASPIC+: A Neuro-Symbolic Framework for Defeasible Reasoning"
authors: "Xiaotong Fang, Zhaoqun Li, Chen Chen, Beishui Liao"
year: 2025
venue: "ECAI 2025"
doi_url: "https://doi.org/10.3233/FAIA241032"
---

# LLM-ASPIC+: A Neuro-Symbolic Framework for Defeasible Reasoning

## One-Sentence Summary
Provides a concrete pipeline for using LLMs as the neural front-end (knowledge extraction, rule grounding, belief formation) feeding into a symbolic ASPIC+ back-end (argumentation construction, grounded extension computation) for defeasible reasoning over contradictory natural language information.

## Problem Addressed
LLMs struggle with defeasible reasoning — they cannot dynamically assess and reconcile contradictory evidence throughout a reasoning process. Unlike symbolic systems that systematically resolve conflicting information, LLMs often fail to determine when new evidence should override previous conclusions, leading to persistent flawed inferences. *(p.1)*

The core issue: LLMs can extract knowledge but cannot formally manage the conflict resolution that defeasible reasoning requires. Pure symbolic systems can resolve conflicts but cannot handle natural language input. *(p.1)*

## Key Contributions
- A neuro-symbolic framework (LLM-ASPIC+) that combines LLM language capabilities with ASPIC+ formal argumentation for defeasible reasoning *(p.0)*
- Three-phase pipeline: Neural Grounding & Reasoning -> Contradiction Detection -> Formal Argumentation Computation *(p.1)*
- SOTA on BoardGameQA benchmark: 67.1% accuracy (vs CoT 51.3%, CoT+SC 54.2%) and 63.0% on RuletakerQA-D *(p.0, p.4)*
- A new dataset MineQA for evaluating defeasible reasoning *(p.1)*
- Detailed error analysis categorizing 7 failure modes of the neuro-symbolic approach *(p.6)*

## Methodology

### Architecture Overview (Figure 2, p.3)

The framework has two major components:

**Component 1: Neural Grounding & Reasoning (LLM-driven)**
Three core operations:
1. Converting unstructured language into structured representations
2. Activating context-sensitive inference pathways
3. Dynamically expanding reasoning contexts by instantiating rules to populate the belief set *(p.1)*

This phase culminates in identifying contradictions within the synthesized belief set, pinpointing conflict pairs that seed attack relations. *(p.1)*

**Component 2: Formal Argumentation Computation (Symbolic)**
- Output from Component 1 fed into ASPIC+ solver
- Constructs argumentation theory
- Computes grounded extension (chosen because it always exists and is unique) *(p.1)*
- Extension integrated with original question through template-based prompting
- LLM classifies conclusion as proved/disproved/unknown *(p.1)*

### Detailed Pipeline (Algorithm 1, p.3)

**Input:** BoardGameQA instance with machines d (a set of natural language statements including facts, strict rules, and defeasible rules)

**Procedure:**

1. **Initialize:** B_0 = facts from d (the initial belief set)

2. **For each iteration i = 1 to n:**

   a. **Extract Stage:** LLM leverages background knowledge to determine which premises of rules are satisfied by the current belief set. For each rule R, LLM checks if premises match beliefs in B_{i-1}. *(p.3)*

   b. **Transition Stage:** Uses previously obtained belief set to activate defeasible rules to attain new beliefs. The extracted rules R1, R2, etc. are activated — LLM performs mathematical/logical reasoning. E.g., "The dog has 3 friends" + rule about friends -> conclude new fact. *(p.3)*

   c. **Contradiction Detection:** Identify pairs of beliefs (s_i, s_j) where one is the negation of the other. These form conflict pairs. *(p.3)*

   d. **Argumentation Construction:** Build argumentation theory AT from the belief set and conflict pairs *(p.3)*

   e. **Grounded Extension:** Compute grounded extension E = ASPIC+(AT, delta') *(p.4)*

3. **Question Answering:** Template-based prompting with extension results, LLM classifies as proved/disproved/unknown *(p.4)*

**Key formula:**

$$
\delta' = L(F_d) \cap \{b(s) \mid b \in S\}
$$
Where: $\delta'$ is the set of defeasible conclusions relevant to the current conflict, $L(F_d)$ is labels from defeasible rules, $b(s)$ are beliefs in the current belief set $S$
*(p.4)*

The ASPIC+ extension E is computed:
$$
E = ASPIC+(AT, \delta')
$$
*(p.4)*

### What's Neural vs What's Symbolic

| Component | Neural (LLM) | Symbolic (ASPIC+) |
|-----------|-------------|-------------------|
| Knowledge extraction from NL | X | |
| Rule premise satisfaction checking | X | |
| Mathematical/logical reasoning in instantiation | X | |
| Contradiction identification | X | |
| Attack relation construction | | X |
| Argumentation theory construction | | X |
| Grounded extension computation | | X |
| Final answer classification | X | |

The LLM does ALL the natural language understanding and belief formation. ASPIC+ does ALL the conflict resolution and extension computation. The boundary is clean: LLM produces a belief set + contradiction pairs, ASPIC+ resolves which beliefs survive. *(p.1, p.3)*

## ASPIC+ Formal Definitions Used

### Argumentation System
AS = (RS, n, <=_d) where:
- RS = R_s union R_d (strict rules R_s and defeasible rules R_d)
- n: R_d -> L is a naming function for defeasible rules
- <=_d is a reflexive and transitive binary relation on R_d (preorder for rule preferences)
*(p.2)*

### Knowledge Base
K = (K_n, K_p) where:
- K_n = axiom premises (not attackable)
- K_p = ordinary premises (attackable)
*(p.2)*

### Argumentation Theory
AT = (AS, K) where AS is an argumentation system and K is a knowledge base *(p.2)*

### Arguments (recursive definition)
- A axiom/ordinary premise is an argument with conclusion = itself
- If A_1,...,A_n are arguments with conclusions c_1,...,c_n, and there exists a strict/defeasible rule r: c_1,...,c_n -> c (or =>c), then A_1,...,A_n, r is an argument with conclusion c *(p.2)*

### Attack Types
1. **Rebutting:** A rebuts B if conclusion of A is contrary to conclusion of B (on a defeasible top rule)
2. **Undermining:** A undermines B if conclusion of A is contrary to an ordinary premise of B
3. **Undercutting:** A undercuts B if conclusion of A is the negation of the name of a defeasible rule used in B *(p.2)*

### Defeat
B defeats A iff B successfully attacks A considering preferences:
- B rebuts A on subargument A' and A' <=_d B (not strictly preferred)
- B undermines A
- B undercuts A on a defeasible rule in A *(p.2)*

### Semantics
Grounded extension chosen — always exists, unique, most skeptical. *(p.1)*

Complete, preferred, stable extensions also defined but not used. *(p.2)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Reasoning depth | n | steps | - | 1-5 | p.4 | Iterations of extract-transition loop |
| Temperature | T | - | 1.0 | - | p.4 | For LLM inference (except SaLM) |
| Temperature (SaLM) | T | - | 0 | - | p.4 | SaLM uses 0 temperature |
| Training samples | - | count | 1000 | - | p.4 | Per split (train/val/test) |
| Accuracy metric | - | % | - | 51.3-67.1 | p.4 | Range across methods on BoardGameQA |

## Implementation Details

- **LLM Models tested:** GPT-4o, Gemini 2.0, SaLM *(p.4)*
- **Datasets:** BoardGameQA (synthetic, controllable depth 1-5, 3 classes: Proved/Disproved/Unknown), RuletakerQA-D, MineQA (newly created) *(p.4)*
- **ASPIC+ solver:** Referenced as [25, 19] — external solver, not custom-built *(p.1)*
- **Prompting:** Template-based prompting for each stage (Extract, Transition, Contradiction, Final QA) *(p.3, p.4)*
- **Two-step reasoning variant:** First step uses large language model to identify relevant rules; second step derives conclusions. Compared to one-step approach. *(p.5)*
- **Belief formation is iterative:** Extract-transition loop runs for n iterations, expanding beliefs each round *(p.3)*
- **Contradiction detection runs AFTER belief formation:** Not during — the full belief set is built first, then contradictions identified *(p.3)*

## Figures of Interest
- **Fig 1 (p.0):** Comparison of pure LLM approach vs LLM-ASPIC+ — shows how pure LLM takes all text and attempts direct reasoning, while LLM-ASPIC+ separates into neural extraction + symbolic resolution
- **Fig 2 (p.3):** Full architecture diagram. Shows pipeline: Example BoardGameQA -> Extract/Transition/Contradiction stages -> Final Construction -> Create Argumentation Theory -> ASPIC+ Answer Question. Labels show what's neural (Prompt, Deprecated, Unknown) vs symbolic
- **Fig 3 (p.5):** Confusion matrices for LLM-ASPIC+ showing performance across Proved/Disproved/Unknown classes
- **Fig 4 (p.5):** Comparative evaluation across reasoning depths 1-5, showing graceful degradation

## Results Summary

### BoardGameQA Performance *(p.4-5)*
| Method | Model | Accuracy |
|--------|-------|----------|
| CoT | GPT-4o | 51.3% |
| CoT+SC | GPT-4o | 54.2% |
| Reasoning | GPT-4o | 47.8% |
| SaLM | Gemini 2.0 | 56.8% |
| LLM-ASPIC+ | GPT-4o | 67.1% |
| LLM-ASPIC+ | Gemini 2.0 | 63.0% (on MineQA) |

### Key Performance Characteristics
- LLM-ASPIC+ achieves graded degradation from depth 3 to 5, better than pure LLM approaches *(p.5)*
- Performance particularly strong on Disproved and Proved classes (73.7% and 77.5% respectively on one configuration) *(p.5)*
- Unknown class is hardest — 48.0% accuracy *(p.5)*
- Two-step reasoning outperforms one-step on BoardGameQA *(p.5)*

### RuletakerQA-D Performance *(p.4)*
LLM-ASPIC+ (Variant 2) on MineQA: 63.0% accuracy

### Comparison to Pure LLM
- CoT alone: 51.3% — LLM-ASPIC+ adds 15.8 percentage points *(p.4)*
- The symbolic ASPIC+ component provides the conflict resolution that LLMs fundamentally lack *(p.5)*

## Limitations

### Acknowledged by Authors
- Performance degrades at higher reasoning depths (depth 4-5) *(p.5)*
- Unknown class particularly difficult — extension-inconclusive cases hard to classify *(p.5)*

### Error Analysis (7 categories, p.6)

1. **Error in Extraction:** LLM can extract rules but struggles with exact sentence matching in Extract task — fails to correctly map NL rules to their formal counterparts *(p.6)*

2. **Error in Instantiation:** LLM fails to correctly derive conclusions from extracted rules using logic — e.g., cannot instantiate variable bindings correctly *(p.6)*

3. **Error in Trigger:** Trigger task fails due to defeasible nature — LLM does not automatically consider cross-condition states, especially negation. Most common error: LLM assigns an attackable rule as unattackable, or fails to recognize a satisfied rule *(p.6)*

4. **Error in Conclusion:** LLM generates incorrect responses at final classification stage *(p.6)*

5. **Natural Language-Formal Mismatch:** Discrepancy between NL rules and formal representations — e.g., "all birds can fly" in language erroneously expresses "all birds condition" as "anything that can fly" *(p.6)*

6. **Overly Narrow Rule Assumptions:** LLM introduces spurious assumptions not in source text — e.g., reading "not work in marketing" as a general occupational descriptor rather than specific constraint *(p.6)*

7. **Misrepresentation of Domain Knowledge:** LLM fabricates/hallucinates knowledge by adding "primary" or "fundamental" qualifiers not present in source; also introduces inconsistencies between reasoning steps and dataset labels *(p.6)*

## Arguments Against Prior Work
- Pure LLMs (even with CoT) cannot handle defeasible reasoning because they lack a retraction mechanism and struggle to dynamically assess contradictory evidence *(p.1)*
- CoT and CoT+SC approaches plateau around 51-54% accuracy on BoardGameQA — insufficient for defeasible reasoning *(p.4)*
- Logic-LM [23] and SatLM [35] use symbolic solvers but don't handle the defeasible/non-monotonic aspect — they focus on classical logical reasoning *(p.1)*
- ArgLLMs [12] integrate abstract argumentation but don't use the full ASPIC+ structured argumentation with rule preferences *(p.1)*

## Design Rationale
- **Why grounded extension?** Always exists and is unique, making it practical and reliable. Preferred/stable extensions can have multiple solutions requiring choice. *(p.1)*
- **Why iterative belief formation?** Single-pass extraction misses derived beliefs. The extract-transition loop allows discovering new beliefs from previously derived ones — essential for multi-step reasoning. *(p.3)*
- **Why separate neural and symbolic phases?** LLMs are good at NL understanding but bad at formal conflict resolution. ASPIC+ is good at conflict resolution but can't process NL. Clean separation leverages both strengths. *(p.1)*
- **Why contradiction detection after full belief formation?** Need the complete belief set to identify all conflicts — running ASPIC+ on partial beliefs would miss contradictions that emerge from later derivation steps. *(p.3)*

## Testable Properties
- Given a set of facts and rules, the iterative extract-transition loop must monotonically grow the belief set (new beliefs added each iteration until fixpoint) *(p.3)*
- Every contradiction pair (s_i, s_j) in the belief set must satisfy: s_i = negation(s_j) *(p.3)*
- The grounded extension must be a subset of every complete extension *(p.2)*
- The grounded extension must be unique for any given argumentation theory *(p.1)*
- An axiom premise (K_n) cannot be the target of an undermining attack *(p.2)*
- A strict rule cannot be the target of an undercutting attack *(p.2)*
- Performance should degrade gracefully with reasoning depth, not catastrophically *(p.5)*

## Relevance to Project

**Directly relevant to propstore's architecture.** This paper validates the design pattern we need:

1. **LLM as extraction front-end, ASPIC+ as resolution back-end** — This is exactly the replacement for our "garbage NLI/embedding that maps to bare floats." Instead of embedding similarity scores, use LLMs to extract structured beliefs and contradiction pairs, then feed to ASPIC+.

2. **The belief formation loop** (extract -> transition -> expand) maps to propstore's claim extraction pipeline. Currently we extract claims; this paper shows we should also extract *rules* and *derive new beliefs* iteratively.

3. **Contradiction detection as a distinct phase** — We currently don't have this. The paper shows that contradiction pairs should be explicitly identified before argumentation, not discovered implicitly during AF construction.

4. **Grounded extension as default semantics** — The paper's choice aligns with our needs: unique, always-exists, most skeptical. Good default for a system that shouldn't over-commit.

5. **The error taxonomy (7 categories)** is directly useful for designing our LLM extraction validation pipeline — we should test for each of these failure modes.

6. **Key gap for us:** The paper uses BoardGameQA (synthetic, well-structured NL). Our data is messy real-world claims. The extraction accuracy will likely be worse. We need robustness to extraction errors that this paper doesn't address.

## Open Questions
- [ ] What ASPIC+ solver implementation do they use? References [25, 19] — need to check (likely Modgil & Prakken's implementation)
- [ ] How does the framework handle cases where the LLM extraction is wrong? The error analysis identifies the problem but doesn't propose solutions
- [ ] Can the iterative belief formation loop be made to work with propstore's existing claim/stance structure?
- [ ] The paper uses grounded extension exclusively — should we also support preferred/stable for different use cases?
- [ ] How does this scale with corpus size? BoardGameQA has bounded problem size; propstore corpora can be arbitrarily large
- [ ] The paper doesn't discuss confidence/probability — beliefs are binary (in the set or not). How do we bridge to our float-based confidence scores?

## Related Work Worth Reading
- **BoardGameQA [15]:** Kazemi et al. — the benchmark dataset used, based on Defeasible Theory *(p.1)*
- **Logic-LM [23]:** Pan et al. — pioneered LLM + symbolic solver combination, but for classical logic *(p.1)*
- **SatLM [35]:** Ye et al. — transforms NL reasoning to SAT problems *(p.1)*
- **ArgLLMs [12]:** Khatun & Hossain — integrates abstract argumentation into LLM architecture *(p.1)*
- **DeLP-COT [16]:** Chain-of-Thought for defeasible logical reasoning *(p.1)*
- **ASPIC+ framework [25, 19]:** Modgil & Prakken — the formal framework used *(p.2)*
- **Toolformer [28]:** Schick et al. — LLM autonomous tool invocation methodology *(p.1)*

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — cited as [6]; foundational AF semantics (admissible, preferred, stable, grounded extensions) that the ASPIC+ solver builds upon
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — cited as [17]; the ASPIC+ tutorial paper defining the framework (strict/defeasible rules, three attack types, preference-based defeat) that LLM-ASPIC+ directly uses
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — cited as [19]; the full technical ASPIC+ paper with complete proofs, referenced for the solver implementation
- [[Pollock_1987_DefeasibleReasoning]] — cited as [22]; foundational defeasible reasoning paper defining rebutting vs undercutting defeat that ASPIC+ formalizes

### New Leads (Not Yet in Collection)
- Kazemi et al. 2023 (BoardGameQA) — "BoardGameQA: A dataset for natural language reasoning with contradictory information" — the primary benchmark; understanding its structure needed for reproducing/extending results
- Khatun & Hossain 2025 (ArgLLMs) — "Argumentative LLMs for explainable AI in medical informatics" — alternative architecture integrating abstract AF directly into LLM rather than as external solver
- Pan et al. 2023 (Logic-LM) — "Logic-LM: Empowering large language models with symbolic solvers" — prior art on LLM + symbolic solver for classical (not defeasible) logic

### Supersedes or Recontextualizes
- (none — this is a novel integration, not a correction or extension of an existing collection paper)

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)
**ASPIC+ with incomplete information:**
- [[Odekerken_2023_ArgumentationReasoningASPICIncompleteInformation]] — **Strong.** Both papers extend ASPIC+ for real-world settings where information is incomplete/uncertain. Odekerken handles incomplete KBs with four justification statuses (unsatisfiable, defended, out, blocked); Fang handles the extraction problem (getting structured beliefs from NL). They are complementary: Fang's LLM extraction will inevitably produce incomplete KBs, and Odekerken's framework provides the formal semantics for reasoning with whatever the LLM manages to extract. Together they cover the full pipeline from messy NL input to principled reasoning under incompleteness.

**Probabilistic vs binary beliefs:**
- [[Hunter_2017_ProbabilisticReasoningAbstractArgumentation]] — **Strong.** Fang's framework uses binary beliefs (in the belief set or not); Hunter provides the formal machinery for graded/probabilistic acceptability over AFs. For propstore, we need both: LLM-ASPIC+ style extraction feeding into Hunter-style probabilistic reasoning rather than binary extension membership. This bridges Fang's "beliefs are binary" limitation with the probability functions Hunter defines.

**Neural argument mining:**
- [[Mayer_2020_Transformer-BasedArgumentMiningHealthcare]] — **Moderate.** Both use neural models (transformers/LLMs) to extract argumentation structure from NL text. Mayer's pipeline (component detection + relation classification) is a more fine-grained extraction approach than Fang's belief formation loop. Mayer identifies argument components and support/attack relations directly; Fang extracts beliefs and detects contradictions. Different granularity, same problem space.

**Belief revision and ATMS:**
- [[Dixon_1993_ATMSandAGM]] — **Moderate.** Fang's iterative belief formation loop (building up beliefs, detecting contradictions, resolving via ASPIC+) is structurally similar to ATMS context switching + AGM revision that Dixon proved equivalent. The ATMS approach labels every datum with assumption sets rather than committing to one belief set — a more principled alternative to Fang's "build one belief set then resolve contradictions" approach.
