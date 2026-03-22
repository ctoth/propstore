# Re-read: de Kleer 1986 ATMS

## Goal
Re-read all 36 pages, add page citations to notes.md

## Page mapping (journal page -> image file)
- page-000 = p.127 (title, abstract, Section 1 Introduction)
- page-001 = p.128 (Section 1.1 Basic results developed in this paper)
- page-002 = p.129 (Section 1.1 cont'd - three TMS roles, ATMS vs JTMS comparison)
- page-003 = p.130 (spatial metaphor, context switching in ATMS)
- page-004 = p.131 (Section 1.2 Reasoning with inconsistency, RUP comparison)
- page-005 = p.132 (default reasoning example with :M operator, ATMS labels example)
- page-006 = p.133 (Section 1.3 History of the ATMS idea, Section 2 Search, 2.1 constraint language)
- page-007 = p.134 (constraint language details, oneof disjunction)
- page-008 = p.135 (enumeration example, chronological backtracking)
- page-009 = p.136 (four defects of backtracking: futile, rediscovering contradictions, rediscovering inferences, incorrect ordering)
- page-010 = p.137 (dependency-directed backtracking, nogood sets, Section 3 Limitations of Current TMSs)
- page-011 = p.138 (Section 3.1 Doyle's TMS, Section 3.2 TMS limitations begin: single-state, overzealous contradiction avoidance)
- page-012 = p.139 (switching states, dominance of justifications, machinery is cumbersome, unouting)
- page-013 = p.140 (unouting example detailed, four solutions to unouting)
- page-014 = p.141 (Section 4 The Basic ATMS, 4.1 Problem-solver architecture, Fig 1)
- page-015 = p.142 (Fig 1 properties, Section 4.2 Basic definitions)
- page-016 = p.143 (justification notation, environment, derivability, inconsistency, context, characterizing environment)
- page-017 = p.144 (Section 4.3 Labels - consistency, soundness, completeness, minimality)
- page-018 = p.145 (minimality, four node categories: true/in/out/false)
- page-019 = p.146 (Section 4.4 Basic data structures - node triple, four node types)
- page-020 = p.147 (assumed node, derived node, gamma_perp, nogoods)
- page-021 = p.148 (Section 4.5 environment lattice, Fig 2 reference, Section 4.6 Basic operations)
- page-022 = p.149 (Fig 2 - environment lattice diagram)
- page-023 = p.150 (Section 4.6 cont'd - three primitive operations, Section 4.7 Basic algorithms)

## Remaining pages read
- page-024 = p.151 (label update algorithm detailed, cross-product computation, DNF conversion)
- page-025 = p.152 (label update cont'd: gamma_perp handling, node slots, env slots, justification slots, Section 4.8 Complexity)
- page-026 = p.153 (complexity: efficiency proportional to environments considered, Section 4.9 Retracting justifications)
- page-027 = p.154 (Section 4.10 Classes, Section 5 Limitations Removed)
- page-028 = p.155 (Section 5 cont'd: dominance of justifications, machinery, circular justifications, unouting)
- page-029 = p.156 (unouting detailed example with ATMS)
- page-030 = p.157 (Section 6 Implementation Issues - bit-vectors, hash tables, nogood database)
- page-031 = p.158 (three-cache optimization, garbage collection of assumptions ~30%)
- page-032 = p.159 (garbage collection details, bit-vector alternatives, lazy label updates)
- page-033 = p.160 (assumption/environment additional slots, Section 7 Summary - four properties)
- page-034 = p.161 (summary cont'd, acknowledgment, references 1-17)
- page-035 = p.162 (references 18-23)

## Key findings so far
- Paper pages 127-162, 36 pages total
- Fig 1 is on p.141 (page-014), not "page 15/141" as notes say
- Fig 2 is on p.149 (page-022), not "page 23/149"
- The existing notes figure references use "page X/Y" format where X is the image number and Y is the journal page - will normalize to journal page
- Seven TMS limitations are in Sections 3.1-3.2 (pp.138-139)
- Four label properties defined on p.144
- Four node categories on p.145
- Basic data structures on p.146
- Environment lattice on p.148
- Three basic operations on p.150
- Constraint language in Section 2.1 (p.133-134) not mentioned in existing notes
- The distinction between "assumption" (decision to assume) and "assumed datum" (what is assumed) is made explicit on p.142
