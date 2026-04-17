# Abstract

## Original Text (Verbatim)

These notes discuss formalizing contexts as *first class objects*. The basic relations are

`ist(c, p)`    meaning that the proposition `p` is true in the context `c`, and

`value(c, e)`    designating the value of the term `e` in the context `c`.

Besides these there are *lifting formulas* that relate the propositions and terms in subcontexts to possibly more general propositions and terms in the outer context. Subcontexts are often specialized with regard to time, place and terminology.

Introducing contexts as formal objects will permit axiomatizations in limited contexts to be expanded to *transcend* the original limitations. This seems necessary to provide AI programs using logic with certain capabilities that human fact representation and human reasoning possess. Fully implementing transcendence seems to require further extensions to mathematical logic, i.e. beyond the nonmonotonic inference methods first invented in AI and now studied as a new domain of logic.

---

## Our Interpretation

This is the canonical McCarthy/Buvač expanded statement of context logic: contexts are abstract objects, truth-in-context is a first-order relation `ist(c, p)`, and lifting axioms (time, place, terminology, assumptions, situation) move facts between contexts instead of forcing a single unified theory. The motivating problem is AI's "generality problem" — axiomatizations useful in one context carry implicit assumptions that break under wider use; transcendence via lifting lets the system drop those assumptions on demand rather than rewrite the theory. For propstore this is the primary source: it authorizes holding multiple context-qualified truths in storage and deferring reconciliation to render-time lifting, rather than collapsing disagreement at ingest.
