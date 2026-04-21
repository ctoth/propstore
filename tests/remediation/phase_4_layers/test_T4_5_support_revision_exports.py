import pytest


def test_support_revision_does_not_export_agm() -> None:
    import propstore.support_revision as sr

    with pytest.raises(AttributeError):
        sr.revise
    with pytest.raises(AttributeError):
        sr.restrained_revise
