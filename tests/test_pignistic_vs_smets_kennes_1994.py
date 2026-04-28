"""Decision-criterion naming tests for pignistic vs projected probability.

Paper anchors are actual paper page numbers:
- Jøsang 2001 Definition 6 probability expectation: p.5.
- Smets & Kennes 1994 BetP equation: journal p.202.
- Denoeux 2019 pignistic criterion review: pp.17-18.
"""

import click
import pytest

from propstore.cli.world import reasoning as world_reasoning_cli
from propstore.cli.worldline import _apply_reasoning_options
from propstore.world.types import DecisionValueSource, apply_decision_criterion


def _click_choice_for(command: click.Command, option_name: str) -> click.Choice:
    for parameter in command.params:
        if isinstance(parameter, click.Option) and parameter.name == option_name:
            assert isinstance(parameter.type, click.Choice)
            return parameter.type
    raise AssertionError(f"missing click option {option_name!r}")


def _worldline_reasoning_choice(option_name: str) -> click.Choice:
    def dummy() -> None:
        return None

    command = click.command()(_apply_reasoning_options(dummy))
    return _click_choice_for(command, option_name)


@pytest.mark.parametrize("base_rate", [0.1, 0.3, 0.5, 0.7, 0.9])
def test_pignistic_binomial_betp_ignores_base_rate(base_rate: float) -> None:
    """Smets-Kennes BetP gives b + u/2 for a binomial frame."""
    result = apply_decision_criterion(
        0.5,
        0.2,
        0.3,
        base_rate,
        confidence=None,
        criterion="pignistic",
    )

    assert result.source is DecisionValueSource.OPINION
    assert result.value == pytest.approx(0.65)


@pytest.mark.parametrize("base_rate", [0.1, 0.3, 0.5, 0.7, 0.9])
def test_projected_probability_uses_josang_base_rate(base_rate: float) -> None:
    """Jøsang Def 6 projected probability is b + a*u."""
    result = apply_decision_criterion(
        0.5,
        0.2,
        0.3,
        base_rate,
        confidence=None,
        criterion="projected_probability",
    )

    assert result.source is DecisionValueSource.OPINION
    assert result.value == pytest.approx(0.5 + base_rate * 0.3)


def test_pignistic_and_projected_probability_disagree_off_uniform_base_rate() -> None:
    pignistic = apply_decision_criterion(
        0.5,
        0.2,
        0.3,
        0.7,
        confidence=None,
        criterion="pignistic",
    )
    projected = apply_decision_criterion(
        0.5,
        0.2,
        0.3,
        0.7,
        confidence=None,
        criterion="projected_probability",
    )

    assert pignistic.value == pytest.approx(0.65)
    assert projected.value == pytest.approx(0.71)
    assert projected.value - pignistic.value == pytest.approx((0.7 - 0.5) * 0.3)


def test_cli_choice_lists_include_projected_probability() -> None:
    world_choices = _click_choice_for(
        world_reasoning_cli.world_resolve,
        "decision_criterion",
    ).choices
    worldline_choices = _worldline_reasoning_choice("decision_criterion").choices

    for choices in (world_choices, worldline_choices):
        assert "pignistic" in choices
        assert "projected_probability" in choices
