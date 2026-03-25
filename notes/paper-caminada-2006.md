# Caminada 2006 - Paper Retrieval Notes

## 2026-03-24

**Paper:** Caminada (2006) "On the Issue of Reinstatement in Argumentation"
**DOI:** 10.1007/11853886_11
**Venue:** JELIA 2006, LNCS 4160, pp 111-123

### Retrieval Progress
- Search script: arxiv search returned irrelevant results (not an arxiv paper)
- Web search: found DOI 10.1007/11853886_11 on SpringerLink
- fetch_paper.py: metadata resolved from Semantic Scholar, PDF not open-access (fallback_needed=true)
- Sci-hub attempt: navigated to sci-hub.st/10.1007/11853886_11, extracted iframe PDF URL
- Download: curl returned 898-byte HTML file, NOT a valid PDF
- **BLOCKER:** Need to retry download with different curl flags or try direct browser save

### Directory Created
- papers/Caminada_2006_IssueReinstatementArgumentation/
- metadata.json exists

### Resolution
- First download attempt (curl) blocked by DDoS-Guard
- First browser download (349KB, 26pp) was WRONG paper (Baroni & Giacomin 2007)
- Second browser download from same sci-hub URL got correct paper (436KB, 13pp)
- Verified: correct paper by Martin Caminada, LNAI 4160, pp 111-123
- All 13 pages read successfully

### Key Content Observed
- Defines AF-labellings with three labels: in, out, undec
- Reinstatement labelling (Def 5): out iff exists in attacker; in iff all attackers out
- Ext2Lab and Lab2Ext conversion functions between extensions and labellings
- Maps labelling restrictions to Dung semantics (Table 1):
  - no restrictions = complete, empty undec = stable, maximal in = preferred
  - maximal out = preferred, maximal undec = grounded, minimal in = grounded
  - minimal out = grounded, minimal undec = semi-stable
- Introduces semi-stable semantics via minimal undec labellings
- Semantic hierarchy: stable > semi-stable > preferred > complete, grounded > complete
- Section 5 compares sceptical/credulous reasoning under complete vs preferred
- Floating arguments example (Fig 4): A-B mutual defeat, C attacked by both, D attacked by C
- Section 6 discusses preferred semantics using excluded middle principle
- Theorems 13-14: complete extensions = complete semantics; conditions for excluded middle
- Definition 9: "condensed" labellings (no undec, relation-based)

### Next Steps
- Write notes.md, description.md, abstract.md, citations.md
- Extract claims
- Write report
