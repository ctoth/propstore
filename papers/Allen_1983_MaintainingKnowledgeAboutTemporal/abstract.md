# Abstract

## Original Text (Verbatim)

The problem of representing temporal knowledge arises in many areas of computer science. In applications in which such knowledge is imprecise or relative, current representations based on date lines or time instants are inadequate. An interval-based temporal logic is introduced, together with a computationally effective reasoning algorithm based on constraint propagation. This system is notable in offering a delicate balance between expressive power and the efficiency of its deductive engine.

A notion of *reference* intervals is introduced which captures the temporal hierarchy implicit in many domains, and which can be used to precisely control the amount of deduction performed automatically by the system. Examples are provided for a data base containing historical data, a data base used for modeling processes and process interaction, and a data base for an interactive system where the present moment is continually being updated.

(Source: Rochester TR 86 (revised), October 1983, PDF p.2.)

---

## Our Interpretation

Relative, imprecise temporal knowledge cannot be held by dates or instants, so Allen takes intervals as primitive, stores disjunctive relation sets between pairs, and closes them by constraint propagation over a composition table. Reference intervals bound the propagation and push cross-cluster inference to query time. For propstore this is the formal basis of interval relations over description claims and a pattern for keeping unresolved alternatives in storage.
