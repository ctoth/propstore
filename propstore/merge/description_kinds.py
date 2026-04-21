from __future__ import annotations

from dataclasses import dataclass

from argumentation.dung import (
    ArgumentationFramework,
    grounded_extension,
    preferred_extensions,
    stable_extensions,
)

from propstore.core.lemon.description_kinds import (
    DescriptionKindMergeProtocol,
    MergeArgument,
)


@dataclass(frozen=True, slots=True)
class CoreferenceQuery:
    protocol: DescriptionKindMergeProtocol
    framework: ArgumentationFramework

    @property
    def merge_arguments(self) -> tuple[MergeArgument, ...]:
        return self.protocol.merge_arguments

    def clusters(self, *, semantics: str = "grounded") -> tuple[frozenset[str], ...]:
        if semantics == "grounded":
            extensions = (grounded_extension(self.framework),)
        elif semantics == "preferred":
            extensions = tuple(preferred_extensions(self.framework))
        elif semantics == "stable":
            extensions = tuple(stable_extensions(self.framework))
        else:
            raise ValueError(f"unknown coreference semantics: {semantics}")

        by_id = {argument.argument_id: argument for argument in self.merge_arguments}
        clusters = {
            frozenset(by_id[argument_id].description_claim_ids)
            for extension in extensions
            for argument_id in extension
            if argument_id in by_id
        }
        return tuple(sorted(clusters, key=lambda cluster: tuple(sorted(cluster))))


def coreference_query(
    merge_arguments: tuple[MergeArgument, ...],
    *,
    attacks: tuple[tuple[str, str], ...] = (),
) -> CoreferenceQuery:
    protocol = DescriptionKindMergeProtocol(
        merge_arguments=merge_arguments,
        attacks=attacks,
    )
    return CoreferenceQuery(
        protocol=protocol,
        framework=ArgumentationFramework(
            arguments=protocol.argument_ids,
            defeats=frozenset(attacks),
        ),
    )
