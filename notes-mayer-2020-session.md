# Session Notes: Mayer 2020 Paper Processing

## Task
Process paper "Transformer-Based Argument Mining for Healthcare Applications" (Mayer, Cabrio, Villata, ECAI 2020) via paper-process skill.

## Status
- Retrieval: SUCCESS via HAL (hal-02879293). sci-hub did not have it, IOS Press paywalled.
- PDF: 9 pages, 416K, valid PDF 1.4
- Page images: 9 pages converted to PNG
- Page 0: HAL cover page (not paper content)
- Page 1: Title page + intro (actual paper starts here)
- Page 2: Dataset description, annotation of argument components
- Page 3: Annotation of argumentative relations, AM pipeline for clinical trials
- Page 4: Figure 1 (pipeline), embeddings discussion, relation classification intro
- Page 5: BLACK PAGE - rendering issue, need to re-read or use PDF reader
- Pages 6-8: Not yet read

## Key Findings So Far
- Paper extends an existing dataset by annotating 500 RCT abstracts from MEDLINE
- Dataset: 4198 argument components, 2601 argument relations
- Diseases: neoplasm, glaucoma, hepatitis, diabetes, hypertension
- Two component types: evidence and claims
- Relations: attack or support between components
- Uses deep bidirectional transformers (BERT etc.) + LSTM/GRU/CRF
- Results: macro F1 = 0.87 for component detection, 0.68 for relation prediction
- Pipeline has two stages: argument component detection, then relation classification
- Embeddings tested: GloVe, ELMo, static BERT, fine-tuned BERT, SciBERT
- SciBERT slightly better for sentence classification tasks

## Current Blocker
Page 5 is black. Need to try reading it via PDF reader or re-render. Still need pages 6-8.

## Progress
- Pages 5 and 7 render black (PDF issue), but pdftotext extracted full text successfully
- All 9 pages read and content extracted
- notes.md: DONE
- description.md: DONE
- abstract.md: DONE
- citations.md: DONE
- Reconciliation: IN PROGRESS
  - Forward: 0 cited refs in collection, 4 new leads
  - Reverse: 0 collection papers cite this one
  - Conceptual links added (strong): Walton 2015, Cayrol 2005, Clark 2014
  - Conceptual links added (moderate): Dung 1995, Modgil 2014
  - Bidirectional annotations: Added to Walton 2015 and Cayrol 2005
  - Still need: Clark 2014 bidirectional annotation

## Remaining
1. Add bidirectional annotation to Clark 2014
2. Update papers/index.md (Step 8)
3. Run extract-claims skill (Step 4 of paper-process)
4. Write report to ./reports/lead-Mayer-2020-report.md
