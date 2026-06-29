"""Render-time coreference resolution over description-claim merge arguments.

Coreference is NOT stored. Given a set of :class:`MergeArgument` hypotheses and
the attacks among them, this module builds a Dung
:class:`~argumentation.dung.ArgumentationFramework` and resolves which merges hold
*at render time* under a chosen argumentation semantics. Because the result is
policy-dependent, the SAME merge arguments yield DIFFERENT coreference clusters
under different semantics — e.g. a pair of mutually-attacking merge hypotheses
admits no coreference under the sceptical ``grounded`` semantics but yields rival
clusters under the credulous ``preferred`` semantics. Storage holds the rival
hypotheses; the render decides (CLAUDE.md non-commitment).

This is the consumer that crosses the argumentation boundary: it imports the
``argumentation`` package and calls its extension functions directly, on the
argument ids carried by the merge arguments. The merge-argument DATA itself lives
in :mod:`propstore.core.lemon.description_kinds`, which imports no engine.
"""

from __future__ import annotations

import msgspec

from argumentation.dung import (
    ArgumentationFramework,
    grounded_extension,
    preferred_extensions,
)

from propstore.core.lemon.description_kinds import (
    DescriptionKindMergeProtocol,
    MergeArgument,
)


class CoreferenceQuery(msgspec.Struct, frozen=True):
    """A resolved-at-render coreference query over merge arguments.

    Holds the merge ``protocol`` (the stored hypotheses + attacks), the derived
    Dung ``framework``, and the ``merge_arguments`` themselves. :meth:`clusters`
    computes the coreference clusters under a given argumentation ``semantics``;
    the answer changes with the semantics (render policy), never with storage.
    """

    protocol: DescriptionKindMergeProtocol
    framework: ArgumentationFramework
    merge_arguments: tuple[MergeArgument, ...]

    def _clusters_for_extension(self, accepted: frozenset[str]) -> frozenset[frozenset[str]]:
        """Merge the supports of every accepted argument into connected clusters."""

        by_id = {argument.argument_id: argument for argument in self.merge_arguments}
        parent: dict[str, str] = {}

        def find(node: str) -> str:
            parent.setdefault(node, node)
            root = node
            while parent[root] != root:
                root = parent[root]
            while parent[node] != root:
                parent[node], node = root, parent[node]
            return root

        def union(left: str, right: str) -> None:
            parent[find(left)] = find(right)

        claims: set[str] = set()
        for argument_id in accepted:
            argument = by_id.get(argument_id)
            if argument is None:
                continue
            supports = argument.supports
            claims.update(supports)
            for claim_id in supports[1:]:
                union(supports[0], claim_id)

        components: dict[str, set[str]] = {}
        for claim_id in claims:
            components.setdefault(find(claim_id), set()).add(claim_id)
        return frozenset(frozenset(members) for members in components.values())

    def clusters(self, *, semantics: str) -> tuple[frozenset[str], ...]:
        """Return the coreference clusters admitted under ``semantics``.

        ``grounded`` (sceptical) uses the single grounded extension; ``preferred``
        (credulous) unions the clusters across all preferred extensions. The
        difference is the policy-dependence proof: mutually-attacking merges give
        ``()`` under grounded but rival clusters under preferred.
        """

        if semantics == "grounded":
            return tuple(self._clusters_for_extension(grounded_extension(self.framework)))
        if semantics == "preferred":
            clusters: set[frozenset[str]] = set()
            for extension in preferred_extensions(self.framework):
                clusters |= self._clusters_for_extension(extension)
            return tuple(clusters)
        raise ValueError(f"unknown argumentation semantics: {semantics!r}")


def coreference_query(
    merge_arguments: tuple[MergeArgument, ...],
    *,
    attacks: tuple[tuple[str, str], ...] = (),
) -> CoreferenceQuery:
    """Build a render-time :class:`CoreferenceQuery` from merge arguments + attacks.

    The merge ``protocol`` validates that every attack names a known argument; the
    Dung framework is then constructed over the argument ids and the attack pairs
    (used as both attacks and defeats — coreference merges carry no preference
    layer).
    """

    arguments = tuple(merge_arguments)
    protocol = DescriptionKindMergeProtocol(
        merge_arguments=arguments,
        attacks=tuple(attacks),
    )
    argument_ids = frozenset(argument.argument_id for argument in arguments)
    defeats = frozenset((attacker, target) for attacker, target in attacks)
    framework = ArgumentationFramework(
        arguments=argument_ids,
        defeats=defeats,
        attacks=defeats,
    )
    return CoreferenceQuery(
        protocol=protocol,
        framework=framework,
        merge_arguments=arguments,
    )
