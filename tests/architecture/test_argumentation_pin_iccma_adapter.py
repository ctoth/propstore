from __future__ import annotations

from types import SimpleNamespace

from argumentation.dung import ArgumentationFramework
from argumentation.solver_adapters.iccma_af import (
    ICCMAOutputKind,
    ICCMASolverSuccess,
    parse_iccma_output,
    solve_af_acceptance,
)


def af(args: set[str], defeats: set[tuple[str, str]]) -> ArgumentationFramework:
    return ArgumentationFramework(arguments=frozenset(args), defeats=frozenset(defeats))


def test_argumentation_pin_exposes_iccma_2023_decision_output_parser() -> None:
    dc = parse_iccma_output("DC-ST", "YES\nw 1\n", query="1")
    ds = parse_iccma_output("DS-PR", "NO\nw 2\n", query="1")
    se = parse_iccma_output("SE-ST", "NO\n")

    assert dc.kind is ICCMAOutputKind.DECISION
    assert dc.answer is True
    assert dc.witness == frozenset({"1"})
    assert ds.answer is False
    assert ds.witness == frozenset({"2"})
    assert se.kind is ICCMAOutputKind.SINGLE_EXTENSION
    assert se.no_extension is True


def test_argumentation_pin_uses_official_iccma_2023_cli_shape(monkeypatch) -> None:
    calls: list[list[str]] = []

    monkeypatch.setattr(
        "argumentation.solver_adapters.iccma_af.shutil.which",
        lambda binary: binary,
    )

    def fake_run(command, *, capture_output, text, timeout, check):
        calls.append(command)
        assert capture_output is True
        assert text is True
        assert timeout == 3.0
        assert check is False
        return SimpleNamespace(returncode=0, stdout="YES\nw 1\n", stderr="")

    monkeypatch.setattr(
        "argumentation.solver_adapters.iccma_af.subprocess.run",
        fake_run,
    )

    result = solve_af_acceptance(
        af({"1", "2"}, {("1", "2")}),
        semantics="stable",
        task="credulous",
        query="1",
        binary="fake-iccma-solver",
        timeout_seconds=3.0,
    )

    assert isinstance(result, ICCMASolverSuccess)
    assert result.answer is True
    assert calls
    command = calls[0]
    assert command[:4] == ["fake-iccma-solver", "-p", "DC-ST", "-f"]
    assert command[5:] == ["-a", "1"]
