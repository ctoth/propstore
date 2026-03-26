# Abstract

## Original Text (Transcribed)

Many systems of structured argumentation explicitly require that the facts and rules that make up the argument for a conclusion be the minimal set required to derive the conclusion. ASPIC+ does not place such a requirement on arguments, instead requiring that every rule and fact that are part of an argument be used in its construction. Thus ASPIC+ arguments are minimal in the sense that removing any element of the argument would lead to a structure that is not an argument. In this brief note we discuss these two types of minimality and show how the first kind of minimality can, if desired, be recovered in ASPIC+.

---

## Our Interpretation

The paper separates two ideas that are often conflated in implementations: whether every premise/rule carried by an argument is actually used, and whether the argument uses the smallest possible support set among all ways to derive the same conclusion. ASPIC+ gives the first guarantee automatically but not the second. The authors then show how to recover the stronger notion by excluding circular and redundant arguments, yielding a more canonical argument representation.
