# Paper Process: Prakken 2006 Formal Systems for Persuasion Dialogue

## 2026-03-24

**GOAL:** Retrieve, read, and process Prakken 2006 "Formal systems for persuasion dialogue" (Knowledge Engineering Review).

**DONE:**
- Step 1 (Retrieve): PDF downloaded from author's website (webspace.science.uu.nl), 26 pages, 344KB. Directory: papers/Prakken_2006_FormalSystemsPersuasionDialogue/
- Step 1.5: metadata.json created manually (S2 was rate-limited)
- Step 2A (Read): All 26 page images read
- Step 3 (Notes): notes.md written with full extraction
- Step 4 (Description): description.md written
- Step 5 (Abstract): abstract.md written
- Step 6 (Citations): citations.md written with full reference list

**IN PROGRESS: Step 7 (Reconcile)**

Forward cross-references found:
- Dung_1995_AcceptabilityArguments — cited as foundational AF
- Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation — Cayrol cited indirectly
- Pollock_1987_DefeasibleReasoning — Pollock cited
- Vreeswijk_1997 — cited but NOT in collection
- Simari_1992 — in collection but not directly cited
- Amgoud_2008/2011 — in collection, Amgoud et al. 2000 cited
- Prakken_2012_AppreciationJohnPollock'sWork — same author's later paper, cites this 2006 paper in its citations.md line 50

Reverse citations found:
- Prakken_2012 citations.md lists "Prakken, H. (2006), 'Formal Systems for Persuasion Dialogue'" — but the notes.md doesn't mention it in cross-references

Conceptual links:
- Modgil_2014/2018 ASPIC+ — structured argumentation connects to dialogue protocol design
- Clark_2014_Micropublications — claim/challenge/support structure maps to speech acts

**DONE (continued):**
- Step 7 (Reconcile): Collection Cross-References written in Prakken 2006 notes.md. Prakken 2012 updated with reverse cross-ref. Forward refs: Dung_1995, Pollock_1987, Cayrol_2005. Reverse: Prakken_2012 cites this. Conceptual links: Modgil_2014, Modgil_2018, Clark_2014, Dixon_1993, deKleer_1986.
- Step 8 (Index): papers/index.md updated with new entry.
- Concept registration: persuasion_dialogue (concept483), dialogue_protocol (concept484), assertion_attitude (concept485) registered. Existing relevant: commitment_store (concept480), dialogue_game (concept479), locution (concept481), dialogue_typology (concept482), argumentation_framework, argumentation_semantics.

**IN PROGRESS: Step 4 (Extract Claims)**
- Context: this paper is cross-cutting (dialogue systems perspective on argumentation), not purely abstract argumentation. Will leave context universal or use ctx_abstract_argumentation since it builds on Dung.
- Paper is a review/survey — claims will be observations, mechanisms, comparisons, limitations. No experimental parameters or benchmark results.

**REMAINING:**
- Write claims.yaml
- Validate claims
- Step 5 (report)
