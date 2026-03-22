# Abstract

## Original Text (Verbatim)

Argument(ation) Mining (AM) typically aims at identifying argumentative components in text and predicting the relations among them. Evidence-based decision making in the healthcare domain targets at supporting clinicians in their deliberation process to establish the best course of action for the case under evaluation. Although the reasoning stage of this kind of frameworks received considerable attention, little effort has been devoted to the mining stage. We extended an existing dataset by annotating 500 abstracts of Randomized Controlled Trials (RCT) from the MEDLINE database, leading to a dataset of 4198 argument components and 2601 argument relations on different diseases (i.e., neoplasm, glaucoma, hepatitis, diabetes, hypertension). We propose a complete argument mining pipeline for RCTs, classifying argument components as evidence and claims, and predicting the relation, i.e., attack or support, holding between those argument components. We experiment with deep bidirectional transformers in combination with different neural architectures (i.e., LSTM, GRU and CRF) and obtain a macro F1-score of .87 for component detection and .68 for relation prediction, outperforming current state-of-the-art end-to-end AM systems.

---

## Our Interpretation

The paper addresses the gap between argumentation reasoning frameworks and the upstream task of automatically extracting argumentative structures from healthcare text. By building a substantial annotated dataset of RCT abstracts and applying transformer-based models in a two-stage pipeline (component detection then relation classification), they show that modern NLP architectures can effectively identify evidence/claim components and their attack/support relations in clinical text, significantly outperforming prior approaches.
