from propstore.opinion import Opinion
from propstore.source.alignment import classify_relation


def _proposal(
    source: str,
    *,
    proposed_name: str,
    definition: str,
) -> dict[str, str]:
    return {
        "source": source,
        "local_handle": source.rsplit("/", 1)[-1],
        "proposed_name": proposed_name,
        "definition": definition,
        "form": "structural",
    }


def test_classify_relation_returns_ignorance_for_vacuous_opinion() -> None:
    relation = {
        "left": _proposal(
            "tag:local@propstore,2026:source/a",
            proposed_name="shared_name",
            definition="first source definition",
        ),
        "right": _proposal(
            "tag:local@propstore,2026:source/b",
            proposed_name="shared_name",
            definition="second source definition",
        ),
        "opinion": Opinion.vacuous(),
    }

    assert classify_relation(relation) == "ignorance"
