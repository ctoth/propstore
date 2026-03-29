# Abstract

## Original Text (Verbatim)

We study belief change in the branching-time structures introduced in [8]. First, we identify a property of branching-time frames that is equivalent (when the set of states is finite) to AGM-consistency, which is defined as follows. A frame is AGM-consistent if the partial belief revision function associated with an arbitrary state-instant pair and an arbitrary model based on that frame can be extended to a full belief revision function that satisfies the AGM postulates. Second, we provide a set of modal axioms that characterize the class of AGM-consistent frames within the modal logic introduced in [8]. Third, we introduce a generalization of AGM belief revision functions that allows a clear statement of principles of iterated belief revision and discuss iterated revision both semantically and syntactically.

---

## Our Interpretation

The paper answers a fundamental question: when does a branching-time structure (where beliefs evolve in response to different possible informational inputs at branch points) behave consistently with the AGM postulates for belief revision? The answer is a concrete, checkable frame property called PLS that tests cyclic consistency of belief-information intersections across sibling instants. This is critical for propstore because it provides the formal criterion for when branching knowledge contexts (analogous to git branches) support well-defined belief revision operations, and the iterated revision functions provide the machinery for tracking how revision history affects future revision behavior.
