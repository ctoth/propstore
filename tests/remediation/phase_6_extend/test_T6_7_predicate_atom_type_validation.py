import pytest

from propstore.cel_checker import KindType
from propstore.families.documents.predicates import PredicateDocument
from propstore.grounding.predicates import (
    PredicateArgKindError,
    PredicateAtom,
    PredicateRegistry,
)


def test_validate_atom_rejects_wrong_argument_kind():
    registry = PredicateRegistry(
        (
            PredicateDocument(
                id="measured_value",
                arity=1,
                arg_types=(KindType.QUANTITY.value,),
                derived_from=None,
                description=None,
            ),
        )
    )
    atom = PredicateAtom(
        predicate_id="measured_value",
        arguments=("observation_time",),
        argument_types=(KindType.TIMEPOINT,),
    )

    with pytest.raises(PredicateArgKindError, match="argument 1"):
        registry.validate_atom(atom)
