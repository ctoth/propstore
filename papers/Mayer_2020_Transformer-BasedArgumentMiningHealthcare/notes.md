---
title: "Transformer-based Argument Mining for Healthcare Applications"
authors: "Tobias Mayer, Elena Cabrio, Serena Villata"
year: 2020
venue: "ECAI 2020 - 24th European Conference on Artificial Intelligence"
doi_url: "https://doi.org/10.3233/FAIA200334"
pages: "2108-2115"
affiliation: "Universite Cote d'Azur, CNRS, Inria, I3S, France"
---

# Transformer-based Argument Mining for Healthcare Applications

## One-Sentence Summary
Proposes a complete argument mining pipeline for clinical trial (RCT) abstracts using transformer-based models (BERT variants + sequence labeling) for component detection and relation prediction, achieving macro F1 of 0.87 and 0.68 respectively.

## Problem Addressed
Evidence-based decision making in healthcare requires clinicians to evaluate large volumes of randomized controlled trial (RCT) literature. While reasoning frameworks for clinical argumentation exist, the mining stage (automatically extracting argumentative structures from text) has received little attention, particularly for healthcare text which has domain-specific features like medical abbreviations, complex inter-component relations spanning entire abstracts, and polarity-dependent measurements.

## Key Contributions
- Extended an existing clinical trial argument dataset with 500 new RCT abstracts from MEDLINE, yielding 4198 argument components and 2601 argument relations across 5 disease categories
- Proposed a complete AM pipeline: sequence tagging for component detection + transformer-based relation classification
- Systematic evaluation of multiple transformer architectures (BERT, BioBERT, SciBERT, RoBERTa) with different neural sequence labeling layers (LSTM, GRU, CRF)
- Introduced a MultiChoice architecture for relation classification as an alternative to standard sentence-pair classification
- Outperformed state-of-the-art end-to-end AM systems on this dataset

## Methodology

### Dataset
- 500 RCT abstracts from MEDLINE/PubMed database
- 5 disease categories: neoplasm, glaucoma, hepatitis, diabetes, hypertension
- Annotated with argumentative components (evidence, claims) and relations (attack, support)
- Total: 4198 argument components, 2601 argument relations
- Annotation performed via BRAT tool by 2 annotators with biomedical background
- Inter-annotator agreement (IAA): calculated with Krippendorff's alpha on subset (detailed in [25])
- Each RCT abstract follows a structured template: background, methods, results, conclusion
- Training: 390 abstracts (neoplasm 155, glaucoma 100, mixed diseases 135)
- Test in-domain: 70 neoplasm abstracts
- Test out-of-domain: 40 glaucoma abstracts (to evaluate cross-disease generalization)

### Argument Components
Two types:
- **Evidence**: observational statements justifying the support of a claim (results, measurements)
- **Claims**: concluding observations about the outcomes of the trial; can be major (main conclusion) or minor (intermediate)
- Major claims are highlighted with a dashed underline in annotation; not distinguished by the classifier

### Argumentative Relations
- **Support**: the source component supports the target
- **Attack**: the source component attacks/contradicts the target
- Relations are directed edges from source to target
- Most components have at most one outgoing edge
- Relations can span across the entire abstract (not just adjacent sentences)

### Pipeline Architecture (Figure 1, page 4)

**Stage 1: Argument Component Detection**
- Sequence tagging approach using BIO scheme
- Labels: B-Claim, I-Claim, B-Evidence, I-Evidence, O
- Architecture: Embedding layer -> Transformer encoder -> Sequence classification (LSTM/GRU/CRF)
- Input: tokenized abstract text

**Stage 2: Relation Classification**
Two architectural variants:

**(i) SentClf (Sentence Classification)**
- Each pair of argument components is classified independently
- Three classes: Support, Attack, NoRelation
- Pooled representation of component pair passed to linear layer + softmax
- Advantage: a component can have relations with multiple others
- Disadvantage: tends to create false positives (linking to multiple components when most have one edge)

**(ii) MultiChoice**
- Each source component is given all other components as target candidates
- Goal: determine most probable target from list
- Adds "noLink" option for components with no outgoing edge
- Based on grounded common sense inference formulation

## Key Equations

$$
P_i = \frac{e^{V \cdot C_i}}{\sum_{j=1}^{n} e^{V \cdot C_j}}
$$

Where: $V \in \mathbb{R}^H$ is a trainable weight vector, $C_i \in \mathbb{R}^H$ is the vector representation of choice $i$, $H$ is the hidden size of the encoder output, and $n$ is the number of choices. This is the softmax over all possible link candidates in the MultiChoice architecture.

## Parameters

| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|
| Macro F1 component detection (best) | - | - | 0.87 | - | SciBERT + GRU + CRF on neoplasm test |
| Macro F1 relation prediction (best) | - | - | 0.68 | - | RoBERTa MultiChoice on neoplasm test |
| Training abstracts | - | count | 390 | - | neoplasm + glaucoma + mixed |
| Test in-domain abstracts | - | count | 70 | - | neoplasm |
| Test out-of-domain abstracts | - | count | 40 | - | glaucoma |
| Total argument components | - | count | 4198 | - | across 500 abstracts |
| Total argument relations | - | count | 2601 | - | across 500 abstracts |
| Avg components per abstract | - | count | ~8.4 | - | 4198/500 |
| Avg relations per abstract | - | count | ~5.2 | - | 2601/500 |
| Learning rate (sequence tagging) | - | - | 0.00002 | - | from prior work [25] |
| Batch size (sequence tagging) | - | - | 32 | - | from prior work [25] |
| Epochs (sequence tagging) | - | count | 4-5 | - | determined on validation |
| Sequence length cutoff | - | tokens | - | - | BPE tokenization, 512 max |
| Hidden size H | H | - | 768 | - | BERT base hidden dimension |

## Implementation Details

### Embeddings Tested
1. **GloVe** (300d, trained on Wikipedia + Gigaword 5)
2. **fastText** (300d, character-based)
3. **BPEmb** (300d, byte-pair encoding subword)
4. **ELMo** (contextualized, 3-layer biLSTM)
5. **Flair** (character-level LM embeddings, forward + backward)
6. **BERT** (static embeddings from pretrained, no fine-tuning)
7. **BERT + FT** (fine-tuned BERT)
8. **BioBERT** (BERT pretrained on PubMed abstracts + PMC articles)
9. **SciBERT** (BERT pretrained on Semantic Scholar corpus, 82% biomedical + 18% CS)
10. **RoBERTa** (robustly optimized BERT pretraining)

### Sequence Labeling Layers
- LSTM, GRU, CRF, and combinations (LSTM+CRF, GRU+CRF)
- Bidirectional variants for LSTM and GRU

### Training Details
- Used AbstRCT dataset from Mayer et al. [25]
- Cross-validation on training set for hyperparameter selection
- Evaluation: token-level macro F1 for component detection, sentence-pair F1 for relations

### Key Implementation Observations
- BIO scheme necessary because multiple components can be adjacent in text
- Without BIO, adjacent components merge into single component
- B-token vs I-token imbalance causes mislabeling errors
- Components in concluding sentences often comprise multiple claims

## Figures of Interest
- **Fig 1 (page 4):** Full argument mining pipeline illustration showing sequence tagging -> component extraction -> relation classification flow
- **Table 1 (page 2):** Extended dataset statistics showing component/relation counts per disease
- **Table 2 (page 6):** Results of multi-class sequence tagging (F1 and macro F1) for all embedding+architecture combinations on neoplasm and glaucoma test sets, plus mixed test
- **Table 3 (page 6):** Results of relation classification (macro F1) across models

## Results Summary

### Component Detection (Table 2)
- Best overall: SciBERT + GRU + CRF = 0.87 macro F1 (neoplasm)
- SciBERT slightly better than other BERT variants for sentence classification tasks
- Fine-tuned BERT significantly outperforms static BERT embeddings
- GRU + CRF combination generally best sequence labeling architecture
- Out-of-domain (glaucoma): performance drops but remains reasonable
- ELMo and Flair show lower performance than fine-tuned BERT variants
- Static embeddings (GloVe, fastText, BPEmb) substantially worse

### Relation Classification (Table 3)
- Best: RoBERTa SentClf = 0.68 F1 (neoplasm), comparable on glaucoma
- MultiChoice architecture: RoBERTa best at 0.67 neoplasm
- Tree-LSTM end-to-end baseline: 0.55 F1
- RoBERTa more stable across domains (only drops 0.01 on out-of-domain)
- SciBERT drops 0.06 on out-of-domain despite being best in-domain
- SentClf slightly better F1 but creates more false positive links
- MultiChoice better at respecting single-outgoing-edge constraint

### End-to-End Pipeline
- Complete pipeline: component detection -> relation classification
- Two LSTM-based end-to-end systems from prior work perform at 0.55 F1
- Transformer-based approach significantly outperforms these baselines

## Limitations
- Only abstracts annotated (not full articles) due to practical constraints
- Full article application shows notable increase in false positives for relation classification
- MultiChoice architecture loses predictive power with double-digit component counts
- BIO scheme causes B-token vs I-token imbalance errors
- Determining exact component boundaries is challenging (especially connectives like "however")
- Cannot capture polarity of measurements from text alone (e.g., "increased blood pressure" can be positive or negative depending on context)
- External expert knowledge needed for medical domain nuances
- Medical abbreviations not explicitly handled
- No cross-RCT relation annotation (future work)

## Testable Properties
- Component detection macro F1 should be >= 0.80 for in-domain clinical text
- Relation prediction macro F1 should be >= 0.60 for in-domain clinical text
- SciBERT should outperform general BERT for biomedical sequence tagging
- RoBERTa should show more stable cross-domain performance than SciBERT
- GRU+CRF should outperform LSTM alone for sequence tagging
- Fine-tuned transformers should significantly outperform static embeddings
- SentClf should produce more false positive links than MultiChoice
- MultiChoice should better respect single-outgoing-edge constraint

## Relevance to Project
This paper demonstrates argument mining applied to a specific domain (healthcare/clinical trials), showing how argumentative components (evidence, claims) and relations (attack, support) can be automatically extracted from structured text. The pipeline architecture (component detection then relation classification) and the argument scheme (evidence supports/attacks claims) are directly relevant to understanding how argumentation structures can be computationally represented and extracted. The dataset and annotation methodology provide a concrete example of grounding abstract argumentation theory in domain-specific text.

## Open Questions
- [ ] How well does the pipeline generalize to completely new disease domains not seen in training?
- [ ] Can the MultiChoice architecture scale to full-text articles with many more components?
- [ ] How to incorporate external medical knowledge to resolve polarity ambiguities?
- [ ] What is the relationship between this work and the ACTA tool [26]?
- [ ] How does cross-RCT argument graph reasoning work?

## Related Work Worth Reading
- Mayer et al. [25] (COMMA 2018) - Argument mining on clinical trials (predecessor dataset)
- Mayer et al. [26] (IJCAI 2019) - ACTA tool for argumentative clinical trial analysis
- Stab and Gurevych [38] (Comp. Linguist. 2017) - Parsing argumentation structures in persuasive essays
- Eger et al. [11] (ACL 2017) - Neural end-to-end learning for computational argumentation mining
- Galassi et al. [12] (ArgMining 2018) - Argumentative link prediction using residual networks
- Reimers et al. [36] (ACL 2019) - Classification and clustering of arguments with contextualized word embeddings
- Beltagy et al. [5] (EMNLP-IJCNLP 2019) - SciBERT pretrained language model
- Cabrio and Villata [7] (IJCAI 2018) - Five years of argument mining survey

## Collection Cross-References

### Already in Collection
- (none of this paper's cited references are in the collection)

### New Leads (Not Yet in Collection)
- Stab and Gurevych (2017) - "Parsing argumentation structures in persuasive essays" - dominant framework for component+relation AM pipelines; baseline comparison
- Eger et al. (2017) - "Neural end-to-end learning for computational argumentation mining" - Tree-LSTM baseline used in this paper
- Reimers et al. (2019) - "Classification and clustering of arguments with contextualized word embeddings" - relevant for understanding how transformer representations capture argumentative semantics
- Cabrio and Villata (2018) - "Five years of argument mining: a data-driven analysis" - survey by the same group covering the evolution of argument mining

### Supersedes or Recontextualizes
- (none in collection)

### Conceptual Links (not citation-based)

**Argumentation theory grounding:**
- [[Walton_2015_ClassificationSystemArgumentationSchemes]] -- **Strong.** Walton provides the canonical taxonomy of argumentation schemes that Mayer et al. apply empirically: the evidence-to-claim support patterns in clinical trials correspond to specific scheme types in Walton's hierarchy (particularly "argument from evidence to hypothesis" and "practical reasoning" schemes). Walton's paper provides the theoretical "what kinds of arguments exist" while Mayer's provides computational methods for detecting them in domain text.
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] -- **Strong.** Mayer's pipeline extracts exactly the structure Cayrol formalizes: bipolar argumentation frameworks with both support and attack relations between arguments. The extracted evidence-claim-support/attack graphs from RCT abstracts are instances of Cayrol's BAFs, and Cayrol's acceptability semantics (d-admissible, s-admissible, c-admissible) could be applied to determine which clinical arguments are jointly acceptable.
- [[Dung_1995_AcceptabilityArguments]] -- **Moderate.** Mayer's relation classification produces attack graphs that are instances of Dung's abstract argumentation frameworks. However, Mayer's framework is bipolar (support + attack) while Dung handles only attack; Cayrol's extension is the more direct formal match.

**Claim and evidence representation:**
- [[Clark_2014_Micropublications]] -- **Strong.** Clark's micropublications model provides the semantic representation layer for exactly the kind of structures Mayer extracts computationally. Clark's claim-evidence-argument model (grounded in Toulmin-Verheij argumentation) defines the ontological types (claims, evidence/data, support, challenge) that Mayer's pipeline detects in text. Clark's model could serve as the target schema for structuring the output of Mayer's mining pipeline.
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] -- **Moderate.** ASPIC+ provides formal rules for constructing and evaluating structured arguments from premises and inference rules. The argument components Mayer extracts (evidence, claims) and their relations (support, attack) map to ASPIC+ elements: evidence maps to premises, claims to conclusions, and the support/attack relations map to ASPIC+'s defeasible inference rules and three attack types.

### Cited By (in Collection)
- (none found)
