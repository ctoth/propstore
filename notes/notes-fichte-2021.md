# Notes: Processing Fichte 2021

## GOAL
Process "Decomposition-Guided Reductions for Argumentation and Treewidth" by Fichte, Hecher, Mahmood, Meier (IJCAI 2021) into the propstore collection.

## DONE
- Searched for paper (title was slightly wrong - "Disposition-guided...graph knots" vs actual "Decomposition-Guided...Treewidth")
- Found DOI: 10.24963/ijcai.2021/259
- Retrieved PDF via fetch_paper.py - success, 202.6K
- Paper dir: papers/Fichte_2021_Decomposition-GuidedReductionsArgumentationTreewidth
- Contains: paper.pdf, metadata.json
- Page count: 7 pages

## PAPER SUMMARY
- Title: Decomposition-Guided Reductions for Argumentation and Treewidth
- Authors: Johannes Fichte, Markus Hecher, Yasir Mahmood, Arne Meier
- Venue: IJCAI 2021, pp. 1880-1886
- Key idea: Design reductions from argumentation problems to SAT/QBF that linearly preserve treewidth
- Covers: abstract argumentation (Dung's framework) and logic-based argumentation (Besnard-Hunter)
- Semantics covered: stable, admissible, complete, preferred, semi-stable, stage
- Main results: O(k) treewidth awareness for DG reductions, matching ETH lower bounds
- Table 1 (p.6) summarizes all results
- Three logic-based problems: ARG, ARG-Check, ARG-Rel with new upper/lower bounds

## CURRENT STATE
- All 7 pages read (PDF direct read worked well, page images also created)
- Ready to write notes.md, description.md, abstract.md, citations.md

## RECONCILIATION FINDINGS
- Mahmood_2025 paper is by same group (Mahmood, Hecher, Fichte) - extends this work to clique-width
- Dung_1995 is in collection - this paper cites it as foundational
- No other collection papers cite Fichte 2021 directly
- Strong conceptual link: Mahmood_2025 explicitly extends this 2021 paper (treewidth -> clique-width)
- Moderate conceptual link: Dung_1995 (foundational framework used throughout)

## RECONCILIATION DONE
- Mahmood_2025 updated: lead moved to "Now in Collection", Related Work annotated
- index.md updated with Fichte_2021 entry
- Cross-references written in this paper's notes.md
- Open question annotated (other graph parameters -> clique-width by Mahmood 2025)

## CLAIM EXTRACTION STATE
- No claims.yaml exists -> create mode
- Concepts needed but missing from registry:
  - treewidth, dg_reduction, logic_based_argumentation, exponential_time_hypothesis,
    quantified_boolean_formula, primal_graph
- Concepts already in registry:
  - tree_decomposition, argumentation_framework, stable_extension, admissible_set,
    complete_extension, preferred_extension, semi_stable_extension, stage_extension,
    conflict_free_set, sat_encoding, ddg_reduction, clique_width, attack_relation,
    credulous_reasoning, skeptical_reasoning

## NEXT
1. Register missing concepts via pks concept add
2. Extract claims and write claims.yaml
3. Write batch report
