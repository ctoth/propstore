# Abstract

## Original Text (Verbatim)

Giunchiglia, F. and L. Serafini, Multilanguage hierarchical logics, or: how we can do without modal logics, Artificial Intelligence 65 (1994) 29-70.

MultiLanguage systems (ML systems) are formal systems allowing the use of multiple distinct logical languages. In this paper we introduce a class of ML systems which use a hierarchy of first-order languages, each language containing names for the language below, and propose them as an alternative to modal logics. The motivations of our proposal are technical, epistemological, and implementational. From a technical point of view, we prove, among other things, that the set of theorems of the most common modal logics can be embedded (under the obvious bijective mapping between a modal and a first-order language) into that of the corresponding ML systems. Moreover, we show that ML systems have properties not holding for modal logics and argue that these properties are justified by our intuitions. This claim is motivated by the study of how ML systems can be used in the representation of beliefs (more generally, propositional attitudes) and provability, two areas where modal logics have been extensively used. Finally, from an implementation point of view, we argue that ML systems resemble closely the current practice in the computer representation of propositional attitudes and metatheoretic theorem proving.

---

## Our Interpretation

The authors argue that modality should be formalized via *structure added to logic* (a hierarchy of distinct languages linked by bridge rules) rather than via *extension of the language* (a modal operator). They define MK (for provability) and MBK (for belief) as concrete ML systems that are syntactically equivalent to modal K yet exhibit locality properties modal logic cannot: local inconsistency doesn't imply global inconsistency, no finite assumption set can render all theories inconsistent, and views at different levels of the hierarchy can hold incompatible beliefs without poisoning the whole system. This is directly relevant to propstore's non-commitment principle — the repository needs a formal proof-theoretic foundation for holding rival normalizations without collapsing them, and Theorems 5.3/5.4 provide exactly that.
