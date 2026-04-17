# Semantic Substrate Papers

These are the papers to process (stubs → full read) and, where needed, retrieve, before the concept/semantic-layer retrofit. The retrofit is driven by the 2026-04-16 code review (`reviews/2026-04-16-code-review/axis-3d-semantic.md`), which found **zero faithful implementations** of any semantic-substrate paper currently cited by `CLAUDE.md`.

The work splits into four sub-phases. Each sub-phase produces a deliverable specification that the subsequent concept-retrofit implementation work will compile against.

## P1 — Provenance foundations

Every downstream type redesign (Opinion, Resolution, SourceTrust, Claim) bakes in provenance assumptions. Read these first so the provenance type is decided before anything else.

**Storage-mechanism decision (2026-04-16):** the logical form of a provenance record is a named graph per Carroll 2005. The *storage realization* is **git-notes on a dedicated notes ref** (`refs/notes/provenance`), attached to claim-object SHAs. Dulwich ≥ 1.1.0 (the propstore pin) supports notes natively via `dulwich.notes`. This keeps provenance non-contaminating with respect to claim identity (notes live on a parallel ref, not in the object graph they annotate), git's object model handles dedup automatically (identical named-graph payloads hash to the same note object), and the carrier is substrate-independent — works with local dulwich, GitHub/GitLab remotes, Cloudflare Artifacts (which natively supports the same notes protocol), or any git-speaking backend. No parallel provenance table.

### In corpus, currently stub (must be processed)

- `Buneman_2001_CharacterizationDataProvenance` — foundational why/where/how distinction for data provenance.
- `Carroll_2005_NamedGraphsProvenanceTrust` — named graphs as the serialization carrier for provenance+trust.

### In corpus, depth unknown (verify coverage)

- `Groth_2010` (statement-level provenance / nanopubs precursor) — already referenced from `repo-merge-papers.md`; confirm this directory has real notes.

### May need retrieval

- **Moreau 2013**, _The PROV Ontology: Provenance Interchange on the Web_ — W3C PROV-O. Concrete ontology shape for provenance facts if we want interoperability. Fetch if absent.
- **Green, Karvounarakis, Tannen 2007**, _Provenance Semirings_ — the algebraic structure that makes provenance compose under joins/unions. Fetch if absent; optional but high leverage.

## P2 — Lemon as concept container

Highest ROI per page. Maps onto the existing `form_utils.py` / `core/concepts.py` split; formalizes the accidental alignment into a principled `LexicalEntry → Form → LexicalSense → OntologyReference` shape.

### In corpus, currently unread (must be processed)

- `Buitelaar_2011_OntologyLexicalizationLemon` — the canonical lemon spec.

### May need retrieval

- **Cimiano, McCrae, Buitelaar 2020** (or closest recent), _Lexicon Model for Ontologies: Community Report_ — current lemon / OntoLex-Lemon. Buitelaar 2011 is the seed; the 2020+ community spec is what implementations actually target. Fetch if absent.

## P3 — Qualia, proto-roles, and description-kinds

**Two layered reframing notes (2026-04-16):**

**First reframe — FrameNet drop:** the original draft targeted "Fillmore frames + Pustejovsky qualia" and proposed importing FrameNet. On closer inspection, FrameNet is a lexicographic catalog without formal algebra — `Causation.Cause` is a string label with a prose definition, not a typed slot with entailments — and Fillmore 1982 is a pre-formal conceptual paper that motivated FrameNet's taxonomic work, not a formalism target. We dropped FrameNet entirely.

**Second reframe — Davidsonian event drop, descriptivist event semantics adopted:** the post-FrameNet draft committed to Davidsonian / neo-Davidsonian events as first-class typed individuals (Parsons 1990). On closer reading, Davidson required event identity to be a metaphysical fact about the world (1969 causal identity, abandoned as circular; 1985 spatiotemporal identity, contested). propstore is not in the business of asserting metaphysical event-individuation conditions; doing so would re-introduce pre-descriptive individuation that the project's non-commitment discipline rejects elsewhere. We are dropping Davidson, dropping Parsons, dropping the `Event` type, dropping `causes`/`precedes` as primitives between determinate event referents.

What replaces them: **events as defeasible coreference**. Description-kinds (`Observation`, `Measurement`, `Assertion`, `Decision`, `Reaction`) are concepts. Particular descriptions are claims of these concepts. What we informally call "an event" is a render-time inference: a cluster of description-claims under a merge-hypothesis whose justification is a defeasible Dung argument resolvable at query time. See `docs/event-semantics.md` for the full position. Hobbs 1985, Quine 1968, late-period Putnam, Davidson, and Parsons are optional explanatory/rejection context for that decision; they are not implementation blockers for the non-Davidsonian type system.

### In corpus, confirm processed (primary)

- `Pustejovsky_1991` (generative lexicon) — qualia structure: formal, constitutive, telic, agentive. Type-driven coercion is the generative mechanism. **Primary.**
- `Dowty_1991_ThematicProtoRoles` — proto-agent / proto-patient graded entailments; Argument Selection Principle. **Primary.**

### In corpus, read for concept only (not an implementation target)

- `Fillmore_1982_FrameSemantics` — foundational conceptual paper on frames as cognitive structures. Read to understand the motivation, not as a formalism target. The formal surrogates are Pustejovsky qualia + Dowty proto-roles + the descriptivist description-kinds (NOT FrameNet, NOT Davidsonian events).

### Optional explanatory/rejection context

- **Hobbs 1985**, _Ontological Promiscuity_. Useful for documenting the licensing-to-posit move behind descriptivist event semantics; not an implementation blocker.
- **Quine 1968**, _Ontological Relativity_. Useful for documenting reference relativity; not an implementation blocker.
- **Pustejovsky 2013** or closest recent qualia / generative-lexicon refinement. Useful; optional.
- **Putnam late-period** (post-1990 internal realism essays — _Realism with a Human Face_ is a reasonable entry point). Secondary; useful for the philosophical lineage.
- **Jackendoff 1990**, _Semantic Structures_. Alternative formal semantic ontology; read for comparison with Pustejovsky. Optional.
- **Levin-Rappaport Hovav 2005**, _Argument Realization_. Operational tests of Dowty's predictions. Optional.

### Optional read for "what we considered and rejected and why"

- **Davidson 1967**, _The Logical Form of Action Sentences_. The foundational event-semantics paper. Read to understand the position propstore considered and rejected.
- **Davidson 1969**, _The Individuation of Events_, and **Davidson 1985**, _Reply to Quine on events_ (or near). The metaphysical event-identity essays. Read both to see the commitment we are not making.
- **Parsons 1990**, _Events in the Semantics of English_. The maximally-developed neo-Davidsonian reference. Read to see the cleanest version of the position we chose against; instructive contrast with the descriptivist approach.

### NOT implementation targets

- **Baker 1998** (FrameNet operationalization) — lexicography without formal inference. Read only if you want to understand why FrameNet is insufficient for a reasoning system.
- **FrameNet inventory** (Berkeley data). Not imported. propstore is not an NLP parser; string-labelled role slots without entailments add no formal content.
- **Fillmore-Atkins 1992, Ruppenhofer FrameNet II handbook.** Lexicographic practitioner guides; not applicable.
- **Davidsonian or neo-Davidsonian event reification.** No `Event` type. No `causes(e1, e2)` between determinate event individuals. See `docs/event-semantics.md`.

## P4 — Micropublications + McCarthy contexts

The hardest semantic piece, biggest leverage. `ist(c, p)` turns every claim into a context-qualified statement. Do this last in Track A because the concept-registry shape from P2-P3 cascades into how contexts compose over concepts.

### In corpus, currently stub (must be processed)

- `Clark_2014_Micropublications` — canonical directory after dedupe. The earlier `Clark_2014_MicropublicationsSemanticModel` directory held the complete PDF/png/notes artifact and has been renamed to the canonical path; `papers/index.md` references the canonical directory.
- `McCarthy_1993` (context formalization / `ist(c, p)`) — almost certainly a stub per axis 3d; paper manifest flagged as foundational high-priority.
- `Guha_1991_ContextsFormalization` — Guha's thesis is titled _Contexts: A Formalization and Some Applications_ and covers both the formalization and applications material previously listed as two separate workstream entries.

### May need retrieval

- **Giunchiglia, Serafini 1994**, _Multilanguage Hierarchical Logics_ — local model semantics for context; the computational companion to McCarthy's philosophical `ist`. Fetch if absent.
- **McCarthy-Buvac 1997**, _Formalizing Context (Expanded Notes)_ — the more implementable version of the 1993 paper. Fetch if absent.
- **Bozzato-Serafini-Eiter 2018** (CKR — Contextualized Knowledge Repositories) — already in corpus for axis-7 defeasibility; cross-reference here because CKR is how `ist(c, p)` composes with a knowledge base.

## Priority

- **High, must-process:** Buneman 2001, Carroll 2005, Buitelaar 2011, Pustejovsky 1991, Dowty 1991, Clark 2014 (deduped), McCarthy 1993, Guha 1991 ×2.
- **High, may-fetch:** Moreau 2013 (PROV-O), Cimiano et al. OntoLex-Lemon community report, Giunchiglia-Serafini 1994.
- **Medium:** Fillmore 1982 (concept grounding only — not an implementation target), Green-Karvounarakis-Tannen 2007, Pustejovsky 2013, McCarthy-Buvac 1997.
- **Low / optional:** Hobbs 1985, Quine 1968, Putnam internal realism, Davidson event papers, Parsons 1990, Jackendoff 1990, Levin-Rappaport Hovav 2005.
- **Not targets:** Baker 1998 FrameNet (read only to understand why it is not sufficient), Fillmore-Atkins 1992, Ruppenhofer FrameNet II handbook, FrameNet inventory itself.

## What each phase produces

Each sub-phase deliverable is a type-level specification that the implementation work can compile against. Rough shapes:

- **P1 output:** `Provenance` spec — named-graph / witness-chain structure; what fields, what algebra under composition (unions, joins), how it rides with Opinion.
- **P2 output:** concept-registry schema — `LexicalEntry`, `Form`, `LexicalSense`, `OntologyReference` with their links. `form_utils.py` rewrite target.
- **P3 output:** `QualiaStructure` + `DescriptionKind` + `ProtoRoleBundle` specs — what slots a `LexicalSense` carries. Qualia compose via typed coercion (Pustejovsky); description-kinds make observations, measurements, assertions, decisions, and reactions into concepts whose particulars are claims; proto-roles decorate roles with graded entailments (Dowty). Fillmore 1982 is read as conceptual background but not implemented.
- **P4 output:** `ist(c, p)` contexts as first-class logical objects; claim ≡ (context, proposition) rather than bare proposition; micropub shape around it (evidence, stance, supporting contexts).

## Why these, not more

The review found the semantic layer rhetoric unsupported by code — not that the code is wrong, but that it implements something genuinely different (a dimensional-quantity ontology + SKOS-style taxonomy + visibility-inheritance contexts + string-token Jaccard reconciliation) from what `CLAUDE.md` advertises. The fix is either (a) a papers run to retrofit the substrate to match the rhetoric, or (b) an honest `CLAUDE.md` rewrite describing what the code actually is. Option (a) is what this markdown plans for. Additional papers beyond this list (ontology-design principles, SKOS alignment, DL-Lite, etc.) can wait — they layer onto the substrate, not replace it.
