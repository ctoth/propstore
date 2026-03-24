# Re-read Session 2026-03-22 (TMS papers batch)

## Goal
Re-read 6 TMS/belief-revision papers, verify/add page citations, add "Arguments Against Prior Work" and "Design Rationale" sections if missing.

## Papers to process
1. Falkenhainer 1987 - DONE. Added Arguments Against Prior Work + Design Rationale sections.
2. Martins 1983 - READ all 4 pages (pp.370-373). Need to add sections now.
3. Dixon 1993 - not yet started
4. Doyle 1979 - not yet started
5. McAllester 1978 - not yet started
6. Alchourron 1985 - not yet started

## Martins 1983 observations from re-read
- 4 pages (pp.370-373)
- Existing notes thorough with page citations
- Missing sections: Arguments Against Prior Work, Design Rationale
- Arguments against prior work found:
  - p.370: Doyle's TMS records dependencies but doesn't handle multiple agents with contradictory beliefs in same KB
  - p.370: McAllester's three-valued TMS and McDermott's contexts also don't handle multi-agent belief
  - p.370: Prior systems need separate NOGOOD list; MBR distributes this info in restriction sets
  - p.373: "no need to explicitly mark propositions as believed or disbelieved" (unlike Doyle)
  - p.373: "no need to worry about circular proofs"
  - p.373: "no need to keep a separate data structure to record previous contradictions" (contrasting Doyle's NOGOOD list)
- Design rationale:
  - p.370: SWM logic chosen because it records dependencies (like relevance logic) while allowing irrelevancies
  - p.371: Contexts as sets of hypotheses - gives 2^n belief spaces from n hypotheses
  - p.371: Two rules only (~I and URS) - minimal mechanism for contradiction handling
  - p.371: CBS retrieval filters - only return propositions derivable from current context
  - p.373: Propositions never deleted, just dropped from context - network preserves all derivations

## Dixon 1993 observations from re-read
- 6 pages (pp.534-539), all readable
- Existing notes already have BOTH "Arguments Against Prior Work" and "Design Rationale" sections
- Re-read confirms page citations are accurate
- Minor additions I could make from re-reading:
  - p.534: Explicitly states "the world would dispute the necessity of having a method of managing beliefs" - foundational vs coherence debate framing
  - p.534: Foundational theory described as "beliefs supported by chains of justification back to foundational beliefs"
  - p.534: Coherence theory "a belief is justified if it coheres with other beliefs"
  - p.534: "conservatism" principle - modify belief set as little as possible
  - p.535: AGM operations produce closed theories which are "usually infinite"
  - p.536: Key insight - only 5 entrenchment levels needed, partial ordering sufficient
  - p.537: "the job of the problem solver, not the TMS" for determining atom relevance
  - p.538-539: Full induction proof for Theorem 1, both expansion and contraction cases
- Existing notes are comprehensive and accurate. No changes needed.

## Status
- Falkenhainer 1987: DONE (added 2 sections)
- Martins 1983: DONE (added 2 sections)
- Dixon 1993: DONE (already had both sections, verified accuracy)
- Doyle 1979: IN PROGRESS - read pages 000-003 (pp.231-234). 42 pages total. Need more pages.
- McAllester 1978: not yet started
- Alchourron 1985: not yet started

## Doyle 1979 observations so far (pp.231-234)
- Existing notes very thorough, missing both "Arguments Against Prior Work" and "Design Rationale"
- Arguments against prior work found so far:
  - p.232: Conventional view of reasoning suffers from monotonicity - beliefs never shrink, only grow
  - p.232: Monotonicity leads to three problems: commonsense reasoning, frame problem, control
  - p.232-233: Conventional view suffers from atomicity - each belief isolated, semantics not represented
  - p.233: Frame problem: control inferences useless in monotonic systems (adding rules just adds more inferences)
  - p.233: Minsky's [36] criticisms of the logistic approach to problem solving amplified here
  - p.234: Traditional view takes fundamental beliefs as "observations" or "sense data" - Doyle rejects truth-seeking
  - p.234: "Rational thought is the process of finding reasons for attitudes" - not discovering truth
- Design rationale found so far:
  - p.231: Record reasons for beliefs to enable principled revision
  - p.231: TMS as subsystem of problem solver, not standalone
  - p.234: Reasons-based rather than truth-based: belief status from valid reasons, not truth values
  - p.234: In/out asymmetry: no reason can make P out; only absence of valid reasons makes P out
- Additional findings from pp.235-238, 265-269:
  - p.235: Traditional retraction was unreasoned; new approach uses "reasoned retraction of assumptions"
  - p.238: Three-element belief sets criticized; four-element needed (in/out distinct from true/false)
  - p.267: Prior belief revision restricted to "backtracking algorithms operating on rather simple systems"
  - p.267: Exception: Colby [6] who used credibility + emotional importance measures
  - p.269: MICRO-PLANNER, CONNIVER, QA4 context mechanisms criticized - discarding sources makes error correction impossible
  - p.236: Three fundamental actions only: create node, add justification, mark contradiction
  - p.237: Non-monotonic justification enables tentative guesses
  - p.266: CP-justifications make implementation complex; simpler version suggested
  - p.268: "Belief Revision System" better name; opinions vs beliefs distinction
  - p.269: Recording justification overhead justified by enabling error correction
- Ready to add sections to notes.md
