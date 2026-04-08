---
title: "Assessing the Cross-Linguistic Utility of Abstract Meaning Representation"
authors: "Shira Wein, Nathan Schneider"
year: 2023
venue: "Computational Linguistics"
doi_url: "https://doi.org/10.1162/coli_a_00501"
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-04-03T08:13:19Z"
---
# Assessing the Cross-Linguistic Utility of Abstract Meaning Representation

## One-Sentence Summary
This paper systematically investigates whether Abstract Meaning Representation (AMR), originally designed for English, can faithfully capture the meaning of non-English languages, finding that source language significantly impacts AMR structure and developing annotation schemas, graph comparison methods, and evaluation metrics for cross-lingual AMR divergence detection.

## Problem Addressed
AMR was designed for English and has been adapted to multiple languages, but it was unclear (1) what types and causes of differences exist between parallel AMRs in different languages, (2) how to measure the amount of structural difference between cross-lingual AMR pairs, and (3) to what degree the source language itself affects AMR structure. *(p.1)*

## Key Contributions
- A novel Smatch-based graph comparison method for quantifying structural differences in cross-lingual AMR pairs *(p.2)*
- A divergence annotation schema classifying structural divergences by type (focus, non-core role, switch arg/non-core, arg differences) and cause (semantic, annotation, syntactic) *(p.19-20)*
- Empirical evidence that source language has a dramatic effect on AMR structure: Smatch scores between cross-lingual AMRs and gold English AMRs fall below 50% *(p.9)*
- Three cross-lingual Smatch variants (XSmatch, XSmatchpp, XSmatch_s) for comparing AMRs across languages *(p.29)*
- Demonstration that AMR can serve as a fine-grained measure of semantic divergence, superior to string-level metrics *(p.27)*
- Human evaluation showing AMR-based Smatch is best metric for cross-lingual AMR evaluation (highest correlation with human similarity judgments) *(p.31)*
- A pipeline for automatic detection of cross-lingual AMR divergence via binary classification achieving F1 of 0.87 on equivalent pairs and 0.90 for equivalent/near-equivalent combined *(p.40)*
- Evidence that cross-lingual AMR captures fine-grained semantic divergence that string-level equivalence cannot detect *(p.35)*

## Study Design (empirical papers)
- **Type:** Multi-experiment empirical study with manual annotation, automatic parsing, and human evaluation *(p.8-10)*
- **Population:** Multiple parallel corpora: 125 Chinese-English AMR pairs from The Little Prince (CAMR dataset), 50 Spanish-English pairs from The Little Prince (Migueles-Abraira, Agirre, Diaz de Ilarraza 2018), 200 English-Spanish web annotations (AMR 2.0), 250 Spanish-English parallel sentence pairs for divergence annotation, 100 French-English pairs, 301 Spanish-English annotated pairs, 1033 French-English REFreSD sentence pairs *(p.4, 10, 17, 24, 37, 42)*
- **Intervention(s):** Comparison of AMR structures produced from different source languages; manual relexicalization of Chinese tokens to English; automatic parsing via translate-then-parse and parse-then-lexicalize pipelines *(p.9, 14-15)*
- **Comparator(s):** Gold English AMR annotations as baseline; string-level metrics (BERTscore, multilingual BERTscore) as comparison metrics *(p.28, 43)*
- **Primary endpoint(s):** Smatch score between cross-lingual and gold English AMRs; inter-annotator agreement (IAA) for divergence annotation; F1 for automatic divergence detection *(p.10, 24, 40)*
- **Secondary endpoint(s):** Pearson correlation between automatic metrics and human similarity judgments; precision/recall curves for semantic equivalence detection *(p.31, 42)*
- **Follow-up:** Four supplementary experiments extending initial Chinese-English findings to Spanish, French, and automatically parsed data *(p.2)*

## Methodology
The paper proceeds through multiple experiments: (1) Manual annotation of Chinese-English parallel AMRs from The Little Prince, where Chinese tokens are relexicalized to English to isolate structural effects of source language, then Smatch is used to compare resulting AMRs against gold English AMRs. (2) Development of a divergence annotation schema applied to 250 Spanish-English AMR pairs, classifying each structural divergence by type and cause. (3) Cross-lingual Smatch metric development (XSmatch, XSmatchpp, XSmatch_s) using translation tables, WordNet synonymy, and sentence embeddings to compare AMRs across languages without relexicalization. (4) Human evaluation comparing AMR-based metrics against string-level metrics for cross-lingual semantic similarity. (5) Automatic divergence detection pipeline using Smatch to identify semantically equivalent vs. divergent parallel sentence pairs, tested on gold and automatically parsed AMRs. (6) Comparison of AMR vs. string-level (BERTscore) metrics for semantic equivalence detection in the REFreSD dataset. *(p.2, 8-9, 18-19, 27-29, 37-42)*

## Key Equations / Statistical Models

$$
\text{Smatch}(G_1, G_2) = \max_{m} F1(m)
$$
Where: $G_1, G_2$ are AMR graphs; $m$ is an alignment (mapping) of nodes between graphs; F1 is the F-score computed over matching triples (variable, concept, relation triples) under that alignment. Smatch works by inducing an alignment between nodes that maximizes overlap between the graphs.
*(p.3)*

$$
\text{IAA} = \text{Smatch}(A_1, A_2)
$$
Where: $A_1, A_2$ are AMR annotations from two annotators for the same sentence. Average IAA reported as 0.86 for the Chinese-English annotations.
*(p.10)*

$$
\text{XSmatch}(G_{src}, G_{tgt}) = \text{Smatch}(\text{relexicalize}(G_{src}), G_{tgt})
$$
Where: relexicalization translates non-English tokens to English using a simple approach of word-aligned concept substitution combined with role-name deterministic translation.
*(p.29)*

$$
\text{Divergence threshold} = t \text{ s.t. } \text{Smatch} < t \Rightarrow \text{divergent}
$$
Where: threshold $t$ is set at the F1-maximizing point; F1 score of 0.87 for equivalent pairs, 0.90 for equivalent+near-equivalent combined at various thresholds.
*(p.40-42)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Image density for conversion | - | DPI | 150 | - | - | Used for page image rendering |
| Average IAA (Chinese-English annotations) | IAA | Smatch | 0.86 | - | 10 | Two bilingual annotators |
| Average Smatch (Chinese AMR vs gold English) | - | Smatch | <0.50 | - | 9 | After relexicalization |
| Average sentence length (English, Little Prince) | - | tokens | 13.5 | - | 10 | For 100 annotated sentences |
| Average sentence length (Chinese, Little Prince) | - | tokens | 19.5 | - | 10 | For 100 annotated sentences |
| Average concepts per English AMR (Little Prince) | - | count | 14.35 | - | 10 | Average node count |
| Average concepts per Chinese AMR (Little Prince) | - | count | 14.19 | - | 10 | Average node count |
| Smatch (Chinese-English, relexicalized) annotation set | - | F1 | 42.54 | - | 17 | Average across pairs for "Diffs" column |
| Smatch (Translate-then-parse vs gold) | - | F1 | ~52.4 | - | 17 | Average for translate-then-parse approach |
| XSmatch Pearson correlation with human judgments (Sp-En) | r | - | 0.72 | - | 31 | For Spanish-English pairs |
| XSmatch_s Pearson correlation with human judgments (Sp-En) | r | - | 0.62 | - | 31 | Embedding-based variant |
| BERTscore Pearson correlation with human judgments (Sp-En) | r | - | 0.55 | - | 31 | String-level baseline |
| Multilingual BERTscore Pearson correlation with human (Sp-En) | r | - | varies | - | 31 | Lower than Smatch |
| Human similarity scale | - | ordinal | - | 0-5 | 30 | 0=completely unrelated, 5=completely equivalent |
| Divergence annotation IAA (Sp-En) | kappa | - | 0.61-0.67 | - | 25 | For Little Prince subset |
| Automatic divergence detection F1 (equivalent) | F1 | - | 0.87 | - | 40 | On gold English-French AMRs |
| Automatic divergence detection F1 (equiv+near-equiv) | F1 | - | 0.90 | - | 40 | Combined classification |
| Brisker & Carpuat (2020) F1 on same data | F1 | - | 0.75 | - | 40 | Baseline comparison |
| Precision at 80% recall (equivalence detection) | P | - | ~0.80 | - | 42 | On REFreSD dataset |
| Average divergences per AMR (Little Prince Sp-En) | - | count/AMR | 1.4 | - | 25 | For 50 parallel pairs |
| Average divergences per AMR (news/web Sp-En) | - | count/AMR | 1.23 | - | 26 | For 200 web annotation pairs |
| Smatch score threshold for REFreSD divergence | t | - | 0.6 | - | 42 | Approximate from precision/recall curve |
| XSmatch score (gold En-Fr parallel AMRs) | - | F1 | 0.143 | - | 41 | Monolingual Smatch on auto-parsed |
| Sentence length correlation with Smatch | r | - | negative | - | 32 | Longer sentences have lower similarity |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Chinese AMR vs gold English AMR similarity | Smatch F1 | <0.50 | - | - | 125 Little Prince sentence pairs | 9 |
| Translate-then-parse Smatch | F1 | 52.4% | - | - | Chinese-to-English translation then parse | 17 |
| Parse-then-lexicalize Smatch | F1 | lower than translate-then-parse | - | - | Direct Chinese parse, relexicalize | 17 |
| XSmatch correlation with human judgment (Sp-En) | Pearson r | 0.72 | - | - | 50 Spanish-English parallel pairs | 31 |
| BERTscore correlation with human judgment | Pearson r | 0.55 | - | - | Same 50 pairs | 31 |
| Divergence detection F1 (equivalent class) | F1 | 0.87 | - | - | 100 gold English-French AMR pairs | 40 |
| Divergence detection F1 (equiv+near) | F1 | 0.90 | - | - | Same dataset | 40 |
| Brisker & Carpuat baseline F1 | F1 | 0.75 | - | - | Same 100 French-English pairs | 40 |
| REFreSD equivalence detection | F1 | 0.43 | - | - | 1033 sentence pairs, auto-parsed | 41 |
| Smatch on auto-parsed En-Fr (translate-parse) | F1 | 0.143 | - | - | Full REFreSD corpus via SGL parser | 41 |
| Human similarity avg score (most similar) | Mean | ~4.5/5 | - | - | Top-ranked pairs by AMR Smatch | 44 |
| Human similarity avg score (least similar) | Mean | ~2.5/5 | - | - | Bottom-ranked pairs by AMR Smatch | 44 |
| En-Fr auto XSmatch on gold annotations | F1 | 0.647 | - | - | Gold AMR pairs, French section | 37 |
| Sp-En Smatch (Little Prince, our annotations) | F1 | ~0.45 | - | - | For Annotator 1 | 11 |
| Sp-En Smatch (Little Prince, Annotator 2) | F1 | ~0.45 | - | - | For Annotator 2 | 11 |

## Methods & Implementation Details
- AMR is a rooted, labeled, directed graph where nodes are instances of semantic concepts, edges are labeled with semantic roles. AMR abstracts away from surface details like word order, morphology, and syntax to focus on core meaning (who does what to whom). *(p.3)*
- AMR uses PropBank framesets (e.g., `say-01`, `want-01`) for predicates, with numbered arguments (`:arg0`, `:arg1`, etc.) and non-core roles (`:manner`, `:time`, `:location`, etc.). *(p.3)*
- Smatch metric computes similarity by finding alignment of nodes between two AMR graphs that maximizes F1 over matching triples. It is the standard AMR evaluation metric. *(p.3)*
- For the Chinese-English experiment: manually translate Chinese concepts to equivalent English tokens, then compute Smatch against gold English AMR. This isolates structural effects from lexical differences. *(p.9)*
- The annotation process for Chinese-English AMRs: (1) manually translate Chinese concepts to English tokens, (2) check parallel gold English AMR for vocabulary, (3) if semantically close enough, use tree from English AMR for manually generated translation. *(p.10)*
- Four design differences identified in Chinese vs. English annotation guidelines: (1) CAMR uses concept for elaboration rather than parenthetical, (2) CAMR uses `:arg0` for event annotation rather than proposition, (3) CAMR uses `cause-of` instead of `cause-01`, (4) CAMR occasionally uses `:beneficiary` instead of `:arg1` for indirect objects. *(p.13)*
- XSmatch variants: *(p.29)*
  - **XSmatch**: manually translate tokens using concept-to-concept substitution and WordNet synonyms. Uses EasyNMT for translation, spaCy OpusNMT model.
  - **XSmatchpp**: modified version of XSmatch that translates entire AMR string, extracting concept-level alignments. More intensive than XSmatch.
  - **XSmatch_s** (embedding-based): incorporates word embeddings into Smatch using LaBSE (Language-agnostic BERT Sentence Embeddings) to account for cross-lingual concept similarity without translation. Elects a constant lemma of the word, projects it, and encodes to a LaBSE embedding. Benefits: does not require exact string matching. *(p.29)*
- Divergence annotation schema: *(p.19-20)*
  - **Cause of divergence:** Semantic (translation choice, e.g., "an instant later" / "instantly"), Annotation (annotator disagreement, e.g., rooting AMR at "erupt" vs. "seem"), Syntactic (inherent language difference, e.g., "belonged to a businessman" / "was of a businessman")
  - **Type of structural divergence:** Different focus, Non-core role differences (added/omitted non-core role, different non-core role chosen), Switch arg and non-core (added/omitted arg), Arg differences (different arg chosen)
- For automatic divergence detection pipeline: *(p.39)*
  1. Manually translate Chinese concepts to equivalent English tokens
  2. Translate concept and role names using deterministic rules
  3. Run Smatch between the relexicalized source-language AMR and gold English AMR
  4. Set threshold to classify as equivalent vs. divergent
- Modified cross-lingual version of Smatch for automatic evaluation: design aligns AMR nodes across languages using role-name translation tables, concept mapping via EasyNMT, WordNet synonym matching, and deterministic translation of role names. *(p.39)*
- Human evaluation used 6-point similarity scale (0-5): 0=completely unrelated, 1=not equivalent but share some subjects, 2=not equivalent but share some details, 3=roughly equivalent, 4=equivalent except for some details, 5=completely equivalent. *(p.30)*
- Two bilingual linguistics students (English+Chinese) trained as annotators. *(p.10)*
- For Spanish-English: annotations produced by designer of annotation scheme plus second annotator fluent in both languages. *(p.24)*
- Brisker and Carpuat (2020) baseline system used for comparison on divergence detection. Their system uses string-level and translation features. *(p.40)*

## Figures of Interest
- **Fig 1 (p.1):** English and Spanish AMR examples for "She little girl wants to dance" showing both text-based PENMAN and graph-based AMR illustrations
- **Fig 2 (p.7):** Spanish-English AMR pair example showing semantic divergence due to translation choice ("What planet are you from?" in different structures)
- **Fig 3 (p.9):** Annotation approach diagram: original English annotation, original Chinese annotation, and relexicalized Chinese annotation
- **Fig 4 (p.11):** Both annotations (Annotator 1 and 2) for one Chinese-English sentence pair showing inter-annotator variation
- **Fig 5-6 (p.12):** Gold English AMR and annotated Chinese AMR for parallel sentences showing structural divergence even with English concept labels
- **Fig 7 (p.13):** Parallel sentence pair with "Boa constrictors swallow their prey whole" showing annotation guideline differences
- **Fig 8 (p.15):** Flow diagram of translate-then-parse and parse-then-lexicalize processes
- **Fig 9 (p.20):** Taxonomy of types of structural divergence (tree diagram)
- **Fig 10 (p.20):** Taxonomy of causes of structural divergence (tree diagram)
- **Fig 11 (p.26):** Heatmap of divergence instances by type and cause for 50 Little Prince Spanish-English pairs
- **Fig 12 (p.26):** Heatmap of divergence instances by type and cause for 200 Spanish AMR web annotations
- **Fig 13 (p.34):** Two parallel Spanish-English AMRs showing effect of named entities on AMR divergence
- **Fig 14 (p.34):** Parallel French-English REFreSD sentences showing divergent and non-divergent examples
- **Fig 15 (p.36):** AMR pair showing sentences with non-core roles (`:manner`, `:degree`, `:time`) useful for detecting parallelism
- **Fig 16 (p.37):** Two parallel sentences from REFreSD dataset showing AMR divergence even when labeled "no meaning divergence"
- **Fig 17 (p.38):** Two parallel French-English AMRs from CAMR-equivalent dataset showing structural divergence despite semantic equivalence
- **Fig 18 (p.42):** Precision/recall curve for equivalence detection on 1033 REFreSD sentence pairs
- **Fig 19 (p.44):** Scatter plot showing all data points (human judgments, AMR similarity, BERTscore, multilingual BERTscore) for 301 Spanish-English annotated pairs

## Results Summary
- Source language has a dramatic effect on AMR structure. Even when Chinese tokens are relexicalized to English, Smatch scores between Chinese-derived AMRs and gold English AMRs fall below 50%, indicating substantial structural divergence caused by the source language itself. *(p.9, 14)*
- The translate-then-parse approach (translating the sentence to English first, then parsing) yields more similar AMRs to gold English than parse-then-lexicalize (parsing in source language then relexicalizing), suggesting translation acts as a normalizer. *(p.14-15)*
- Qualitative analysis shows AMR divergences stem from three causes: semantic divergences (non-literal translation), annotation divergences (annotator choice), and syntactic divergences (inherent structural language differences like pro-drop in Chinese). *(p.20)*
- The divergence annotation schema reveals that different focus and annotation divergences are the most common types across both Little Prince and web data. *(p.25-26)*
- Syntactic divergences are more prominent in web/news data than literary text, likely because literary text requires more creative translation. *(p.25)*
- XSmatch (AMR-based) correlates more strongly with human similarity judgments (r=0.72 for Spanish-English) than string-level BERTscore (r=0.55), demonstrating AMR captures semantic similarity better than string comparison. *(p.31)*
- Sentence length is negatively correlated with Smatch scores; longer sentences tend to have lower similarity scores. *(p.32)*
- The automatic divergence detection pipeline achieves F1 of 0.87 on equivalent pairs from gold AMRs, outperforming the Brisker & Carpuat (2020) baseline (F1=0.75). *(p.40)*
- On automatically parsed AMRs (REFreSD, 1033 pairs), performance drops to F1=0.43 due to parsing noise, but AMR-based detection still captures semantic divergences invisible to string-level metrics. *(p.41)*
- AMR can detect fine-grained semantic divergences including n-word paraphrases, lexical choice differences, and structural reframing that string-level equivalence misses. *(p.33-35)*
- Spanish and French source languages both cause structural effects on AMR similar to Chinese, though Spanish/English being more syntactically similar produces less divergence than Chinese/English. *(p.17)*

## Limitations
- AMR was designed for English, so many concepts, frame semantics, and role inventories are English-centric. Non-English languages may require different concept sets. *(p.1, 5)*
- The relexicalization approach (translating concepts to English) introduces noise and does not fully isolate structural from lexical effects. *(p.9)*
- Small dataset sizes for some experiments (50 Spanish-English Little Prince pairs, 100 French-English gold pairs). *(p.24, 40)*
- Human evaluation uses only 6-point scale and may not capture fine-grained similarity differences. *(p.30)*
- Automatic parsing quality significantly degrades divergence detection performance (F1 drops from 0.87 on gold to 0.43 on auto-parsed AMRs). *(p.41)*
- The divergence annotation schema requires two annotators fluent in both languages, limiting scalability. *(p.24)*
- Some annotation guideline differences between CAMR (Chinese AMR) and English AMR are design choices, not linguistic divergences, which inflate measured structural differences. *(p.13)*
- The paper does not test on morphologically rich languages (e.g., Turkish, Finnish, Arabic) where AMR's abstractive power might face greater challenges. *(p.46)*
- Named entity handling differs across AMR annotation projects, causing artificial divergence in Smatch scores. *(p.17, 34)*

## Arguments Against Prior Work
- Prior cross-lingual AMR work (Xue et al. 2014; Hajic et al. 2014) focused on morphophonetic variation adaptation rather than investigating whether AMR comprehensively captures meaning of non-English languages. *(p.1-2)*
- String-level similarity metrics (BERTscore, multilingual BERTscore) are inferior to AMR-based Smatch for detecting fine-grained semantic divergence, as they conflate syntactic similarity with semantic equivalence. *(p.27, 31)*
- The Brisker and Carpuat (2020) system for divergence detection, while effective at string level, cannot capture structural semantic divergences visible in AMR graphs. *(p.40)*
- Previous cross-lingual AMR evaluation work (Damonte and Cohen 2018, 2020) compared only translate-then-parse results without measuring the effect of source language on AMR structure independently. *(p.5)*
- Prior Smatch variants (S2match, SemBLEU) use string-based approaches that do not account for cross-lingual concept matching. *(p.29)*

## Design Rationale
- AMR graphs are compared using Smatch rather than other graph metrics because Smatch is the standard AMR evaluation metric and provides interpretable F1 scores over triple-level alignment. *(p.3)*
- The relexicalization approach (replacing Chinese/Spanish tokens with English equivalents) was chosen to isolate structural from lexical effects on AMR comparison. *(p.9)*
- The divergence annotation schema separates cause (semantic/annotation/syntactic) from type (focus/non-core/arg) because these are independent dimensions: the same structural divergence type can arise from different causes. *(p.19-20)*
- XSmatch uses deterministic role-name translation rather than learned translation because AMR role names are a closed set with near-deterministic cross-lingual correspondences. *(p.29)*
- LaBSE embeddings were chosen for XSmatch_s because LaBSE is language-agnostic and supports 109 languages, making it suitable for cross-lingual concept matching without translation. *(p.29)*
- The authors chose The Little Prince as primary corpus because it exists as parallel AMR annotations in multiple languages (English, Chinese, Spanish), enabling controlled comparison. *(p.4, 24)*

## Testable Properties
- Cross-lingual AMR Smatch scores should be lower than monolingual Smatch scores for the same semantic content, because source language introduces structural divergence. *(p.9)*
- Translate-then-parse should yield higher Smatch scores against gold English AMRs than parse-then-lexicalize, because translation normalizes toward English structure. *(p.14-15)*
- AMR-based metrics (Smatch) should correlate more strongly with human semantic similarity judgments than string-based metrics (BERTscore) for parallel sentences. *(p.31)*
- Syntactic divergences should be more common than semantic divergences in parallel sentences from news/web domain (vs. literary domain). *(p.25)*
- Longer parallel sentences should have lower Smatch scores (negative correlation between sentence length and Smatch). *(p.32)*
- An F1 threshold on Smatch can distinguish semantically equivalent from divergent parallel sentence pairs with F1 > 0.85 on gold AMR annotations. *(p.40)*
- Non-core AMR roles (`:manner`, `:degree`, `:time`) are particularly helpful for identifying parallelism/lack of parallelism between sentences. *(p.36)*
- Named entities with wiki links cause artificial Smatch divergence when different language editions link to different Wikipedia articles. *(p.17, 34)*

## Relevance to Project
**Rating: Medium-High** — The core finding — that structured graph-based meaning representations capture finer-grained semantic differences than string-level comparison — validates propstore's entire approach to concept representation. The divergence annotation schema is directly relevant to vocabulary reconciliation. This paper belongs to the concept-layer cluster alongside Fillmore, Pustejovsky, Baker, Buitelaar, Clark, Dowty, McCarthy, and Kallem.

Specific points of contact:
1. **Graph structure validates concept-layer design**: The paper's central empirical result — AMR-based Smatch correlates with human similarity judgments at r=0.72 vs BERTscore's r=0.55 (p.31) — is direct evidence that structured semantic representations outperform string-level comparison for meaning comparison. This validates propstore's choice to represent concepts as structured objects with typed dimensions and relations rather than as embeddings or string labels.
2. **Divergence annotation schema maps to vocabulary reconciliation**: The three-cause classification (semantic divergence, annotation divergence, syntactic divergence) at p.19-20 maps directly onto the kinds of disagreement propstore's vocabulary reconciliation must handle. When two sources use different concept structures for the same phenomenon, the system needs to classify WHY they differ — genuine semantic disagreement vs. representational convention vs. structural artifact — before deciding whether to merge, preserve both, or flag for adjudication.
3. **Source-language effects = source-perspective effects**: The finding that source language dramatically affects AMR structure even for the same semantic content (Smatch < 0.50, p.9) is the cross-linguistic analog of propstore's non-commitment discipline. Different sources will produce structurally different representations of the same claim, and the system must preserve these differences with provenance rather than collapsing them into a single canonical form.
4. **Smatch as concept comparison metric**: The Smatch graph-comparison approach — aligning nodes between structured representations and computing F1 over matching triples (p.3) — provides a concrete model for how propstore could compare competing concept definitions or measure structural similarity between claims from different sources. The XSmatch variants (p.29) demonstrate how to handle comparison across different vocabularies, which is exactly the vocabulary reconciliation problem.
5. **Fine-grained divergence detection beyond string comparison**: The paper demonstrates that AMR detects semantic divergences invisible to string-level metrics — n-word paraphrases, lexical choice differences, structural reframing (p.33-35). This directly supports propstore's need for structural rather than surface-level comparison when reconciling claims from different sources.

## Open Questions
- [ ] How would AMR divergence detection perform on morphologically rich languages (Turkish, Arabic, Finnish)?
- [ ] Can the divergence annotation schema be extended to handle pragmatic/discourse-level divergences?
- [ ] How do automatic AMR parsers for non-English languages compare in quality to English parsers?
- [ ] Could the XSmatch_s embedding approach be improved with newer multilingual models (e.g., XLM-RoBERTa)?
- [ ] What is the relationship between AMR divergence and translation quality metrics (BLEU, COMET)?

## Related Work Worth Reading
- Banarescu et al. 2013 — Original AMR specification and annotation guidelines
- Cai and Knight 2013 — Smatch metric definition
- Damonte and Cohen 2018, 2020 — Cross-lingual AMR parsing evaluation
- Brisker and Carpuat 2020 — Divergence detection with fine-grained classification
- Xue et al. 2014 — AMR annotation for Chinese
- Li et al. 2016 — CAMR (Chinese AMR) specification
- Migueles-Abraira, Agirre, and Diaz de Ilarraza 2018 — Spanish AMR annotations
- Opitz et al. 2020 — AMR similarity metrics (S2match)
- Feng et al. 2017 — Scalable AMR alignment
- Uhrig et al. 2021 — Translate-then-parse for cross-lingual AMR

## Collection Cross-References

### Already in Collection
- (none — key cited papers Banarescu 2013, Cai & Knight 2013, Damonte & Cohen 2018/2020, Brisker & Carpuat 2020, Xue et al. 2014 are not in the collection)

### New Leads (Not Yet in Collection)
- Banarescu et al. (2013) — "Abstract Meaning Representation for Sembanking" — foundational AMR specification, relevant for understanding the representation format
- Cai and Knight (2013) — "Smatch: An Evaluation Metric for Semantic Feature Structures" — defines the standard graph comparison metric used throughout
- Damonte and Cohen (2018) — "Cross-Lingual Abstract Meaning Representation Parsing" — direct predecessor on cross-lingual AMR evaluation
- Brisker and Carpuat (2020) — "Language Divergences across Multiple Parallel Corpora" — string-level divergence detection baseline

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)
- [[Fillmore_1982_FrameSemantics]] — AMR's predicate-argument structure draws on frame semantics (PropBank frames are FrameNet-adjacent); Wein's finding that AMR structure is language-dependent echoes frame semantics' observation that frames are culturally/linguistically situated
- [[Baker_1998_BerkeleyFrameNet]] — AMR concept labels use PropBank framesets which are related to FrameNet frames; cross-lingual frame applicability is a shared concern
- [[Clark_2014_Micropublications]] — Both papers address how to represent meaning in structured graph form (AMR graphs vs. micropublication argumentation graphs); Wein's Smatch metric for graph comparison is analogous to the structural comparison needed for micropublication alignment
- [[Dowty_1991_ThematicProtoRoles]] — AMR's numbered argument roles (arg0, arg1) are grounded in thematic proto-role theory; Wein shows these role assignments diverge cross-linguistically, which has implications for any universal semantic role scheme
