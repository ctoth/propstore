# Research pass: which papers are we missing (2026-10-19)

## Goal

Q asked: "what papers're we missing that we really need to have?" Produce a
ranked, evidence-backed list, then retrieve + read what Q picked.

## State

Retrieval round finished. Nothing committed. All on master in the main
checkout, alongside Q's pre-existing uncommitted paper changes.

Read (paper-retriever + paper-reader; each verified on disk: paper.pdf,
pngs/ count = pages, notes.md, index entry):
- `Lamport_1978_TimeClocksOrderingEvents` (author-hosted CACM scan, 8pp)
- `Zilberstein_1996_UsingAnytimeAlgorithmsIntelligent` (AAAI OJS, 11pp)
- `Klawonn_1992_DynamicBeliefTransferableBelief` (arXiv 1303.5408, 8pp;
  renamed from Klawonn_2013_ — arXiv year — and fixed index.md, keymap.tsv,
  _reader_done.tsv)
- `Buvac_1993_PropositionalLogicContext` (author .ps, 8pp; AAAI CDN copy
  AAAI93-062.pdf is truncated at p.417)
- `Buvac_1995_MetamathematicsContexts` (author accepted manuscript, 39pp,
  unpaginated — citations are manuscript pages, not journal pages)
- `Prakken_1997_Argument-BasedExtendedLogicProgramming` (author PDF, 52pp,
  PDF page numbers)
- `Laurie_2013_CertificateTransparency` (RFC 6962 html print, 24pp; cites
  RFC [Page N])
- `Crosby_2009_EfficientDataStructuresTamper-Evident` (usenix OA, 17pp)
- `Mazières_2002_BuildingSecureFileSystems` (author .ps, 10pp numbered 1-10,
  not proceedings 108-117)

Half-built, needs Q's decision:
- `Allen_1983_MaintainingKnowledgeAboutTemporal/` holds Rochester TR 86
  (revised, Oct 1983, "To appear, Commun. of the ACM, 1984" — verified from
  page images) as paper.pdf + 45 pngs + metadata.json citing the CACM DOI. Not
  read. ACM DL download blocked (403; cookie-blocked JS fetch).

Not retrieved (no directories created): Adams 1975, Walley 1991, Besnard &
Hunter 2008, Nute 1994, Makinson 1988.

## Decisions

- Q picked all four tiers. Q: "recommend against paper process, just use paper
  reader" — retriever + reader only; no source branch, no pks, no
  tag/reconcile.
- Dropped Jøsang & Kaplan 2016: held Jøsang 2016 book covers trust networks
  (Ch. 14) and subjective networks (Ch. 17).
- Two subagents wrote duplicate agent-notes files; folded here and deleted.

## Surprises

- Paywall path is dead for every agent: Claude-in-Chrome permission prompt
  timed out waiting for Q's Allow click; sci-hub shows a CAPTCHA ("are you are
  robot?"); Unpaywall 422 on the skill's placeholder email; Semantic Scholar
  429; no institutional proxy.
- Walley's book: S2 says 1990, edition is 1991 (DOI 10.1007/978-1-4899-3472-7).
- Besnard & Hunter DOI resolves on Crossref, 404 on S2. Nute chapter DOI
  10.1093/oso/9780198537472.003.0007 (Crossref), not on S2.
- Agents flagged possible as-printed errors (their reading, unverified):
  Klawonn p.132 conditioning sum, Theorem 1 ⊑ direction; AAAI-93 Buvač (D)
  missing ¬; Prakken & Sartor "Condition (3) of Definition 2.2" nonexistent.
- Citation drift found during the survey: `propstore/core/literal_keys.py:13`
  and `families/predicates.py:206` cite "Diller, Borg, Bex 2025" for content
  in the held Diller/Gaggl/Hanisch/Monterosso/Rauschenbach 2025 KR paper;
  `docs/event-semantics.md:59` tags held Hobbs 1985 "to fetch" and `:68` says
  Allen 1983 "already consumed"; `:69` tags Lamport "to fetch" (now held).

## Round 2 (Q's answers 2026-10-19)

Q: Allen = use TR preprint; paywalled 5 = skip; follow-up = reconcile + fix
citation drift + commit.
- Allen metadata.json rewritten to describe TR 86 (doi null, CACM DOI in
  retrieval_note).
- One agent dispatched: paper-reader on Allen, then reconcile on all 10 new
  dirs sequentially.
- docs/event-semantics.md fixed: Hobbs, Allen, Lamport now point at papers/
  dirs (diff is only these 3 lines).
- `.py` docstring drift (literal_keys.py:13, predicates.py:206 "Diller, Borg,
  Bex 2025") NOT edited: code, waits for Q's "make it so".
- Commit plan: keymap.tsv and _reader_done.tsv are untracked and also list
  Q's uncommitted 29-paper grounding batch -> leave out. papers/index.md diff
  mixes Q's batch with ours -> stage only our hunks via a patch applied with
  `git apply --cached`. Branch first (on master): research/missing-papers-2026-10-19.

## Next step

After reconcile agent reports: verify, then commit per plan above.

## Old next step (superseded)

Q decides: (1) Allen TR vs. hand-fetched CACM PDF; (2) whether to allow
Chrome + solve sci-hub CAPTCHA for the five paywalled items, or drop PDFs in
by hand; (3) whether to run reconcile on the new papers, fix the citation
drift, and commit.
