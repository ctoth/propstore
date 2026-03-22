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
Proposes a complete argument mining pipeline for clinical trial (RCT) abstracts using transformer-based models (BERT variants + sequence labeling) for component detection and relation prediction, achieving macro F1 of 0.87 and 0.68 respectively. *(p.1)*

## Problem Addressed
Evidence-based decision making in healthcare requires clinicians to evaluate large volumes of randomized controlled trial (RCT) literature. *(p.1)* While reasoning frameworks for clinical argumentation exist, the mining stage (automatically extracting argumentative structures from text) has received little attention, particularly for healthcare text which has domain-specific features like medical abbreviations, complex inter-component relations spanning entire abstracts, and polarity-dependent measurements. *(p.1)*

## Key Contributions
- Extended an existing clinical trial argument dataset with 500 new RCT abstracts from MEDLINE, yielding 4198 argument components and 2601 argument relations across 5 disease categories *(p.1)*
- Proposed a complete AM pipeline: sequence tagging for component detection + transformer-based relation classification *(p.1)*
- Systematic evaluation of multiple transformer architectures (BERT, BioBERT, SciBERT, RoBERTa) with different neural sequence labeling layers (LSTM, GRU, CRF) *(p.1)*
- Introduced a MultiChoice architecture for relation classification as an alternative to standard sentence-pair classification *(p.1)*
- Outperformed state-of-the-art end-to-end AM systems on this dataset *(p.1)*

## Methodology

### Dataset
- 500 RCT abstracts from MEDLINE/PubMed database *(p.2)*
- 5 disease categories: neoplasm, glaucoma, hepatitis, diabetes, hypertension *(p.2)*
- Annotated with argumentative components (evidence, claims) and relations (attack, support) *(p.2)*
- Total: 4198 argument components, 2601 argument relations *(p.2)*
- Annotation performed via BRAT tool by 2 annotators with biomedical background *(p.2)*
- Inter-annotator agreement (IAA): calculated with Krippendorff's alpha on subset (detailed in [25]) *(p.2)*
- Each RCT abstract follows a structured template: background, methods, results, conclusion *(p.2)*
- Training: 390 abstracts (neoplasm 155, glaucoma 100, mixed diseases 135) *(p.2)*
- Test in-domain: 70 neoplasm abstracts *(p.2)*
- Test out-of-domain: 40 glaucoma abstracts (to evaluate cross-disease generalization) *(p.2)*
- Table 1 provides per-disease breakdown: neoplasm has 1844 components / 1133 relations, glaucoma 848/521, mixed 1506/947 *(p.2)*

### Argument Components
Two types: *(p.2-3)*
- **Evidence**: observational statements justifying the support of a claim (results, measurements) *(p.3)*
- **Claims**: concluding observations about the outcomes of the trial; can be major (main conclusion) or minor (intermediate) *(p.3)*
- Major claims are highlighted with a dashed underline in annotation; not distinguished by the classifier *(p.3)*
- Claims in the context of RCT abstracts are conclusions the authors draw about the outcomes; a claim explicitly or implicitly describes the relation of a new treatment vs. a standard treatment or placebo *(p.3)*
- Evidence can be implicit statements about the significance of the study outcome *(p.3)*

### Argumentative Relations
- **Support**: the source component supports the target *(p.3)*
- **Attack**: the source component attacks/contradicts the target *(p.3)*
- Relations are directed edges from source to target *(p.3)*
- Most components have at most one outgoing edge *(p.3)*
- Relations can span across the entire abstract (not just adjacent sentences) *(p.3)*
- Attack relations are less frequent than support; polarity of measurements ("increased blood pressure") can be positive or negative depending on context/disease *(p.3)*
- All types of relations are possible between any component types (evidence-to-evidence, claim-to-claim, etc.), but some subtypes are compared to frequency of others *(p.3)*
- Most common: evidence supports claim; a few evidence attack claim; relatively few claim-claim or evidence-evidence relations *(p.3)*
- An evidence can support a minor claim and additionally attack the major claim *(p.3)*
- A claim can have multiple incoming support edges from different evidence, plus one additional outgoing edge, resulting in a "focus" topology rather than a tree *(p.3)*

### Pipeline Architecture (Figure 1, p.4)

**Stage 1: Argument Component Detection** *(p.3-4)*
- Sequence tagging approach using BIO scheme *(p.3)*
- Labels: B-Claim, I-Claim, B-Evidence, I-Evidence, O *(p.3)*
- Architecture: Embedding layer -> Transformer encoder -> Sequence classification (LSTM/GRU/CRF) *(p.4)*
- Input: tokenized abstract text *(p.4)*

**Stage 2: Relation Classification** *(p.4-5)*
Two architectural variants:

**(i) SentClf (Sentence Classification)** *(p.5)*
- Each pair of argument components is classified independently
- Three classes: Support, Attack, NoRelation
- Pooled representation of component pair passed to linear layer + softmax
- Advantage: a component can have relations with multiple others
- Disadvantage: tends to create false positives (linking to multiple components when most have one edge)

**(ii) MultiChoice** *(p.5)*
- Each source component is given all other components as target candidates
- Goal: determine most probable target from list
- Adds "noLink" option for components with no outgoing edge
- Based on grounded common sense inference formulation

## Key Equations

$$
P_i = \frac{e^{V \cdot C_i}}{\sum_{j=1}^{n} e^{V \cdot C_j}}
$$

Where: $V \in \mathbb{R}^H$ is a trainable weight vector, $C_i \in \mathbb{R}^H$ is the vector representation of choice $i$, $H$ is the hidden size of the encoder output, and $n$ is the number of choices. This is the softmax over all possible link candidates in the MultiChoice architecture. *(p.5)*

## Parameters

| Name | Symbol | Units | Default | Range | Notes | Page |
|------|--------|-------|---------|-------|-------|------|
| Macro F1 component detection (best) | - | - | 0.87 | - | SciBERT + GRU + CRF on neoplasm test | p.6 |
| Macro F1 relation prediction (best) | - | - | 0.68 | - | RoBERTa MultiChoice on neoplasm test | p.6 |
| Training abstracts | - | count | 390 | - | neoplasm + glaucoma + mixed | p.2 |
| Test in-domain abstracts | - | count | 70 | - | neoplasm | p.2 |
| Test out-of-domain abstracts | - | count | 40 | - | glaucoma | p.2 |
| Total argument components | - | count | 4198 | - | across 500 abstracts | p.2 |
| Total argument relations | - | count | 2601 | - | across 500 abstracts | p.2 |
| Avg components per abstract | - | count | ~8.4 | - | 4198/500 | p.2 |
| Avg relations per abstract | - | count | ~5.2 | - | 2601/500 | p.2 |
| Learning rate (sequence tagging) | - | - | 0.00002 | - | from prior work [25] | p.5 |
| Batch size (sequence tagging) | - | - | 32 | - | from prior work [25] | p.5 |
| Epochs (sequence tagging) | - | count | 4-5 | - | determined on validation | p.5 |
| Sequence length cutoff | - | tokens | - | - | BPE tokenization, 512 max | p.4 |
| Hidden size H | H | - | 768 | - | BERT base hidden dimension | p.5 |
| Neoplasm components | - | count | 1844 | - | in training+test split | p.2 |
| Neoplasm relations | - | count | 1133 | - | in training+test split | p.2 |
| Glaucoma components | - | count | 848 | - | in training+test split | p.2 |
| Glaucoma relations | - | count | 521 | - | in training+test split | p.2 |
| Mixed disease components | - | count | 1506 | - | hepatitis+diabetes+hypertension | p.2 |
| Mixed disease relations | - | count | 947 | - | hepatitis+diabetes+hypertension | p.2 |

## Implementation Details

### Embeddings Tested *(p.4)*
1. **GloVe** (300d, trained on Wikipedia + Gigaword 5) *(p.4)*
2. **fastText** (300d, character-based) *(p.4)*
3. **BPEmb** (300d, byte-pair encoding subword) *(p.4)*
4. **ELMo** (contextualized, 3-layer biLSTM) *(p.4)*
5. **Flair** (character-level LM embeddings, forward + backward) *(p.4)*
6. **BERT** (static embeddings from pretrained, no fine-tuning) *(p.4)*
7. **BERT + FT** (fine-tuned BERT) *(p.4)*
8. **BioBERT** (BERT pretrained on PubMed abstracts + PMC articles) *(p.4)*
9. **SciBERT** (BERT pretrained on Semantic Scholar corpus, 82% biomedical + 18% CS) *(p.4)*
10. **RoBERTa** (robustly optimized BERT pretraining) *(p.4)*

### Sequence Labeling Layers *(p.4)*
- LSTM, GRU, CRF, and combinations (LSTM+CRF, GRU+CRF) *(p.4)*
- Bidirectional variants for LSTM and GRU *(p.4)*

### Training Details
- Used AbstRCT dataset from Mayer et al. [25] *(p.2)*
- Cross-validation on training set for hyperparameter selection *(p.5)*
- Evaluation: token-level macro F1 for component detection, sentence-pair F1 for relations *(p.5)*

### Key Implementation Observations
- BIO scheme necessary because multiple components can be adjacent in text *(p.3)*
- Without BIO, adjacent components merge into single component *(p.3)*
- B-token vs I-token imbalance causes mislabeling errors *(p.6)*
- Components in concluding sentences often comprise multiple claims *(p.3)*
- Static embeddings (GloVe, fastText, BPEmb) used as input to sequence model; no fine-tuning of the embedding *(p.4)*
- Flair embeddings: character-based language model, forward and backward, concatenated with word representations *(p.4)*
- BERT used in two modes: (a) static (extract embeddings, no fine-tuning) and (b) fine-tuned end-to-end *(p.4)*
- BioBERT trained on PubMed abstracts and PMC full articles *(p.4)*
- SciBERT trained on 1.14M papers from Semantic Scholar (82% biomedical, 18% CS); uses its own WordPiece vocabulary (scivocab) *(p.4)*

## Figures of Interest
- **Fig 1 (p.4):** Full argument mining pipeline illustration showing sequence tagging -> component extraction -> relation classification flow
- **Table 1 (p.2):** Extended dataset statistics showing component/relation counts per disease, split into evidence/claim counts and support/attack counts
- **Table 2 (p.6):** Results of multi-class sequence tagging (F1 and macro F1) for all embedding+architecture combinations on neoplasm and glaucoma test sets, plus mixed test
- **Table 3 (p.6):** Results of relation classification (macro F1) across models

## Results Summary

### Component Detection (Table 2, p.6)
- Best overall: SciBERT + GRU + CRF = 0.87 macro F1 (neoplasm) *(p.6)*
- SciBERT slightly better than other BERT variants for sentence classification tasks *(p.6)*
- Fine-tuned BERT significantly outperforms static BERT embeddings *(p.6)*
- GRU + CRF combination generally best sequence labeling architecture *(p.6)*
- Out-of-domain (glaucoma): performance drops but remains reasonable *(p.6)*
- ELMo and Flair show lower performance than fine-tuned BERT variants *(p.6)*
- Static embeddings (GloVe, fastText, BPEmb) substantially worse *(p.6)*
- BERT+FT outperforms static BERT by a large margin, showing fine-tuning is crucial *(p.6)*
- BioBERT and SciBERT show a better performance than general BERT+FT, but not by a huge margin *(p.6)*
- The mixed test set shows the model's ability to handle diverse diseases simultaneously *(p.6)*
- Explanation: clinical texts are domain-specific but natural language reports of measurements use only a few measured parameters, so claims can be made about everything; another observation is that performance of models trained on neoplasm data does not significantly decrease for tests on other disease types *(p.6)*

### Relation Classification (Table 3, p.6)
- Best: RoBERTa SentClf = 0.68 F1 (neoplasm), comparable on glaucoma *(p.6)*
- MultiChoice architecture: RoBERTa best at 0.67 neoplasm *(p.6)*
- Tree-LSTM end-to-end baseline: 0.55 F1 *(p.6)*
- RoBERTa more stable across domains (only drops 0.01 on out-of-domain) *(p.6)*
- SciBERT drops 0.06 on out-of-domain despite being best in-domain *(p.6)*
- SentClf slightly better F1 but creates more false positive links *(p.6)*
- MultiChoice better at respecting single-outgoing-edge constraint *(p.6)*
- Two Tree-LSTM based end-to-end systems performed the worst with 0.55 F1; this can be explained by the potential recoil that an NLI-system suffers when classifying two fairly long passages *(p.6)*
- Similar to sequence tagging, one can see a notable increase in performance when applying a BERT model; comparing the specialized BERT models, RoBERTa delivers consistently over the different metrics by up to 0.08 F1 score *(p.6)*

### End-to-End Pipeline *(p.7)*
- Complete pipeline: component detection -> relation classification
- Two LSTM-based end-to-end systems from prior work perform at 0.55 F1
- Transformer-based approach significantly outperforms these baselines

## Limitations
- Only abstracts annotated (not full articles) due to practical constraints *(p.7)*
- Full article application shows notable increase in false positives for relation classification *(p.7)*
- MultiChoice architecture loses predictive power with double-digit component counts *(p.7)*
- BIO scheme causes B-token vs I-token imbalance errors *(p.6)*
- Determining exact component boundaries is challenging (especially connectives like "however") *(p.6)*
- Cannot capture polarity of measurements from text alone (e.g., "increased blood pressure" can be positive or negative depending on context) *(p.3)*
- External expert knowledge needed for medical domain nuances *(p.3)*
- Medical abbreviations not explicitly handled *(p.1)*
- No cross-RCT relation annotation (future work) *(p.7)*
- In clinical texts, natural language reports of measurements use only a few measured parameters and claims can be made about everything; this makes relation detection harder *(p.6)*

## Testable Properties
- Component detection macro F1 should be >= 0.80 for in-domain clinical text *(p.6)*
- Relation prediction macro F1 should be >= 0.60 for in-domain clinical text *(p.6)*
- SciBERT should outperform general BERT for biomedical sequence tagging *(p.6)*
- RoBERTa should show more stable cross-domain performance than SciBERT *(p.6)*
- GRU+CRF should outperform LSTM alone for sequence tagging *(p.6)*
- Fine-tuned transformers should significantly outperform static embeddings *(p.6)*
- SentClf should produce more false positive links than MultiChoice *(p.6)*
- MultiChoice should better respect single-outgoing-edge constraint *(p.6)*

## Relevance to Project
This paper demonstrates argument mining applied to a specific domain (healthcare/clinical trials), showing how argumentative components (evidence, claims) and relations (attack, support) can be automatically extracted from structured text. *(p.1)* The pipeline architecture (component detection then relation classification) and the argument scheme (evidence supports/attacks claims) are directly relevant to understanding how argumentation structures can be computationally represented and extracted. *(p.4)* The dataset and annotation methodology provide a concrete example of grounding abstract argumentation theory in domain-specific text. *(p.2-3)*

## Open Questions
- [ ] How well does the pipeline generalize to completely new disease domains not seen in training? *(p.6)*
- [ ] Can the MultiChoice architecture scale to full-text articles with many more components? *(p.7)*
- [ ] How to incorporate external medical knowledge to resolve polarity ambiguities? *(p.3)*
- [ ] What is the relationship between this work and the ACTA tool [26]? *(p.1)*
- [ ] How does cross-RCT argument graph reasoning work? *(p.7)*

## Related Work Worth Reading
- Mayer et al. [25] (COMMA 2018) - Argument mining on clinical trials (predecessor dataset) *(p.2)*
- Mayer et al. [26] (IJCAI 2019) - ACTA tool for argumentative clinical trial analysis *(p.1)*
- Stab and Gurevych [38] (Comp. Linguist. 2017) - Parsing argumentation structures in persuasive essays -> NOW IN COLLECTION: [[Stab_2016_ParsingArgumentationStructuresPersuasive]] *(p.2)*
- Eger et al. [11] (ACL 2017) - Neural end-to-end learning for computational argumentation mining *(p.2)*
- Galassi et al. [12] (ArgMining 2018) - Argumentative link prediction using residual networks *(p.2)*
- Reimers et al. [36] (ACL 2019) - Classification and clustering of arguments with contextualized word embeddings *(p.2)*
- Beltagy et al. [5] (EMNLP-IJCNLP 2019) - SciBERT pretrained language model *(p.4)*
- Cabrio and Villata [7] (IJCAI 2018) - Five years of argument mining survey *(p.2)*

## Collection Cross-References

### Already in Collection
- (none of this paper's cited references are in the collection)

### Now in Collection (previously listed as leads)
- [[Stab_2016_ParsingArgumentationStructuresPersuasive]] — Establishes the dominant framework for component+relation AM pipelines using CRF sequence labeling for component identification, SVM for classification/relation detection, and ILP joint optimization for global structural constraints. Mayer et al. 2020 builds directly on this pipeline architecture but replaces feature-engineered classifiers with transformer-based models (SciBERT, RoBERTa), achieving significant improvements particularly on relation classification. *(p.2)*

### New Leads (Not Yet in Collection)
- Eger et al. (2017) - "Neural end-to-end learning for computational argumentation mining" - Tree-LSTM baseline used in this paper *(p.2)*
- Reimers et al. (2019) - "Classification and clustering of arguments with contextualized word embeddings" - relevant for understanding how transformer representations capture argumentative semantics *(p.2)*
- Cabrio and Villata (2018) - "Five years of argument mining: a data-driven analysis" - survey by the same group covering the evolution of argument mining *(p.2)*

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
