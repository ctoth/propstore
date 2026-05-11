# Abstract

## Original Text (Verbatim)

We propose a novel approach to the view update problem for tree-structured data: a domain-specific programming language in which all expressions denote bi-directional transformations on trees. In one direction, these transformations--dubbed lenses--map a "concrete" tree into a simplified "abstract view"; in the other, they map a modified abstract view, together with the original concrete tree, to a correspondingly modified concrete tree. Our design emphasizes both robustness and ease of use, guaranteeing strong well-behavedness and totality properties for well-typed lenses.

We begin by identifying a natural mathematical space of well-behaved bi-directional transformations over arbitrary structures, studying definedness and continuity in this setting. We then instantiate this semantic framework in the form of a collection of lens combinators that can be assembled to describe bi-directional transformations on trees. These combinators include familiar constructs from functional programming (composition, mapping, projection, conditionals, recursion) together with some novel primitives for manipulating trees (splitting, pruning, copying, merging, etc.). We illustrate the expressiveness of these combinators by developing a number of bi-directional list-processing transformations as derived forms. An extended example shows how our combinators can be used to define a lens that translates between a native HTML representation of browser bookmarks and a generic abstract bookmark format.

## Our Interpretation

This paper gives the semantic and programming-language foundation for treating projections as paired, typed, law-governed transformations rather than one-way renderers. For propstore, its main value is the precise GetPut/PutGet/totality contract and the design pattern of composing small typed projection/update combinators into larger information-preserving views.
