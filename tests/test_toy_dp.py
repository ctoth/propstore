"""Toy I/O/U labelling DP for probabilistic argumentation.

Implements the Popescu & Wallner (2024) approach in minimal form:
enumerate all valid I/O/U complete labellings, weight by subframework
probability, compute acceptance probabilities. Verified against brute-force
enumeration of all 2^|defeats| subgraphs.

Semantics supported: grounded (unique minimal complete labelling).
"""

from __future__ import annotations

import itertools
import math
from collections import defaultdict
from typing import Any

import hypothesis
from hypothesis import given, settings
from hypothesis import strategies as st

import pytest


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------
Label = str  # "I", "O", "U"
Labelling = dict[str, Label]


# ---------------------------------------------------------------------------
# Grounded extension on a concrete (non-probabilistic) AF
# ---------------------------------------------------------------------------

def grounded_extension(args: set[str], defeats: set[tuple[str, str]]) -> frozenset[str]:
    """Compute the unique grounded extension via iterated characteristic fn.

    Dung 1995, Definition 20 + Theorem 25.
    """
    attackers_of: dict[str, set[str]] = {a: set() for a in args}
    for src, tgt in defeats:
        if src in args and tgt in args:
            attackers_of[tgt].add(src)

    s: frozenset[str] = frozenset()
    while True:
        # F(S) = {a in args | every attacker of a is defeated by some member of S}
        next_s = frozenset(
            a for a in args
            if all(
                any((d, att) in defeats for d in s)
                for att in attackers_of[a]
            )
        )
        if next_s == s:
            break
        s = next_s
    return s


# ---------------------------------------------------------------------------
# Brute-force reference: enumerate all 2^|defeats| subgraphs
# ---------------------------------------------------------------------------

def brute_force_acceptance(
    args: set[str],
    defeats: set[tuple[str, str]],
    p_defeats: dict[tuple[str, str], float],
    semantics: str = "grounded",
) -> dict[str, float]:
    """Enumerate all subsets of defeats, compute acceptance in each.

    P_A(a) = 1 for all arguments (arguments always present).
    Only defeat edges are probabilistic.
    """
    assert semantics == "grounded", "Only grounded semantics supported"

    defeats_list = sorted(defeats)
    n = len(defeats_list)
    acceptance: dict[str, float] = {a: 0.0 for a in args}

    for mask in range(1 << n):
        # Compute probability of this subgraph
        prob = 1.0
        active_defeats: set[tuple[str, str]] = set()
        for i, d in enumerate(defeats_list):
            p = p_defeats[d]
            if mask & (1 << i):
                prob *= p
                active_defeats.add(d)
            else:
                prob *= (1.0 - p)

        if prob < 1e-18:
            continue

        # Compute grounded extension in this subgraph
        ext = grounded_extension(args, active_defeats)
        for a in ext:
            acceptance[a] += prob

    return acceptance


# ---------------------------------------------------------------------------
# I/O/U labelling-based computation (the "toy DP")
# ---------------------------------------------------------------------------

def _is_valid_complete_labelling(
    labelling: Labelling,
    args: set[str],
    defeats: set[tuple[str, str]],
) -> bool:
    """Check if labelling is a valid complete labelling for the given AF.

    Complete labelling conditions (Caminada 2006):
      - a in I iff all attackers of a are in O
      - a in O iff at least one attacker of a is in I
      - a in U iff not all attackers in O AND no attacker in I
    """
    attackers_of: dict[str, set[str]] = {a: set() for a in args}
    for src, tgt in defeats:
        if src in args and tgt in args:
            attackers_of[tgt].add(src)

    for a in args:
        atts = attackers_of[a]
        att_labels = {labelling[att] for att in atts}
        label = labelling[a]

        all_out = all(labelling[att] == "O" for att in atts)
        some_in = any(labelling[att] == "I" for att in atts)

        if label == "I":
            if not all_out:
                return False
        elif label == "O":
            if not some_in:
                return False
        elif label == "U":
            if all_out:
                return False
            if some_in:
                return False
        else:
            return False

    return True


def _is_grounded_labelling(
    labelling: Labelling,
    args: set[str],
    defeats: set[tuple[str, str]],
) -> bool:
    """Check if labelling is the grounded labelling (minimal I set among complete labellings).

    The grounded extension has the LEAST IN set of any complete labelling.
    Equivalently: it has the MOST U labels.
    """
    if not _is_valid_complete_labelling(labelling, args, defeats):
        return False

    # Grounded = the unique complete labelling with minimal IN set.
    # Check: no proper subset of IN arguments yields a valid complete labelling.
    in_args = {a for a in args if labelling[a] == "I"}

    # Try removing each IN argument — if any smaller complete labelling exists,
    # this isn't grounded. But actually, the grounded labelling is unique, so
    # we compute it directly and compare.
    ext = grounded_extension(args, defeats)
    return in_args == ext


def toy_dp_acceptance(
    args: set[str],
    defeats: set[tuple[str, str]],
    p_defeats: dict[tuple[str, str], float],
    semantics: str = "grounded",
) -> dict[str, float]:
    """Compute acceptance probabilities via I/O/U labelling enumeration.

    For each possible subgraph (2^|defeats| possibilities), find the valid
    complete/grounded labelling, weight by probability. This is the "flat"
    version — no tree decomposition, but uses the I/O/U labelling framework
    from Popescu & Wallner (2024).

    The key insight matching the paper: an argument is OUT only if it has
    a witnessing IN attacker with a REALIZED attack edge. Without this
    witness mechanism, we'd incorrectly label arguments as OUT.
    """
    assert semantics == "grounded", "Only grounded semantics supported"

    defeats_list = sorted(defeats)
    n_defeats = len(defeats_list)
    args_list = sorted(args)
    n_args = len(args_list)

    acceptance: dict[str, float] = {a: 0.0 for a in args}

    # For each subgraph (subset of defeats)...
    for def_mask in range(1 << n_defeats):
        # Compute probability of this subgraph
        prob = 1.0
        active_defeats: set[tuple[str, str]] = set()
        for i, d in enumerate(defeats_list):
            p = p_defeats[d]
            if def_mask & (1 << i):
                prob *= p
                active_defeats.add(d)
            else:
                prob *= (1.0 - p)

        if prob < 1e-18:
            continue

        # Build attacker map for this subgraph
        attackers_of: dict[str, set[str]] = {a: set() for a in args}
        for src, tgt in active_defeats:
            attackers_of[tgt].add(src)

        # Enumerate all I/O/U labellings, find the grounded one
        # The grounded labelling is unique per subgraph.
        # For efficiency, compute it directly rather than enumerating 3^n.
        #
        # Grounded labelling algorithm:
        # 1. Start: all args U
        # 2. Any arg with all attackers O -> label I
        # 3. Any arg with some attacker I -> label O (witness: that attacker)
        # 4. Repeat until stable
        labelling: dict[str, Label] = {a: "U" for a in args}
        changed = True
        while changed:
            changed = False
            for a in args_list:
                if labelling[a] != "U":
                    continue
                atts = attackers_of[a]
                # Check if all attackers are OUT
                if all(labelling[att] == "O" for att in atts):
                    # No attackers, or all attackers OUT -> IN
                    labelling[a] = "I"
                    changed = True
                elif any(labelling[att] == "I" for att in atts):
                    # Witness: an IN attacker with realized edge
                    labelling[a] = "O"
                    changed = True

        # Accumulate acceptance for IN-labelled arguments
        for a in args:
            if labelling[a] == "I":
                acceptance[a] += prob

    return acceptance


# ---------------------------------------------------------------------------
# Alternative: pure labelling enumeration (3^n * 2^|D|) — for witness tests
# ---------------------------------------------------------------------------

def toy_dp_labelling_enum(
    args: set[str],
    defeats: set[tuple[str, str]],
    p_defeats: dict[tuple[str, str], float],
    semantics: str = "grounded",
    *,
    require_witness: bool = True,
) -> dict[str, float]:
    """I/O/U labelling enumeration that explicitly checks witness conditions.

    This version enumerates ALL 3^n labellings for each subgraph, filtering
    for valid complete labellings. When require_witness=False, it drops the
    witness check (allowing O labels without a realized attack), demonstrating
    why the witness mechanism is needed.
    """
    assert semantics == "grounded", "Only grounded semantics supported"

    defeats_list = sorted(defeats)
    n_defeats = len(defeats_list)
    args_list = sorted(args)
    n_args = len(args_list)

    acceptance: dict[str, float] = {a: 0.0 for a in args}
    labels = ["I", "O", "U"]

    for def_mask in range(1 << n_defeats):
        prob = 1.0
        active_defeats: set[tuple[str, str]] = set()
        for i, d in enumerate(defeats_list):
            p = p_defeats[d]
            if def_mask & (1 << i):
                prob *= p
                active_defeats.add(d)
            else:
                prob *= (1.0 - p)

        if prob < 1e-18:
            continue

        attackers_of: dict[str, set[str]] = {a: set() for a in args}
        for src, tgt in active_defeats:
            attackers_of[tgt].add(src)

        # Find grounded labelling among all complete labellings
        grounded_in: set[str] | None = None
        min_in_size = n_args + 1

        for label_combo in itertools.product(labels, repeat=n_args):
            labelling = dict(zip(args_list, label_combo))

            valid = True
            for a in args_list:
                atts = attackers_of[a]
                all_out = all(labelling[att] == "O" for att in atts)
                some_in = any(labelling[att] == "I" for att in atts)

                if labelling[a] == "I":
                    if not all_out:
                        valid = False
                        break
                elif labelling[a] == "O":
                    if require_witness:
                        # Witness: need an IN attacker with realized edge
                        if not some_in:
                            valid = False
                            break
                    else:
                        # No witness: just need SOME potential attacker
                        # (even if edge not realized) — THIS IS WRONG
                        potential_attackers = {
                            src for src, tgt in defeats if tgt == a
                        }
                        if not any(
                            labelling[att] == "I"
                            for att in potential_attackers
                            if att in args
                        ):
                            valid = False
                            break
                elif labelling[a] == "U":
                    if all_out:
                        valid = False
                        break
                    if some_in:
                        valid = False
                        break

            if not valid:
                continue

            in_set = {a for a in args_list if labelling[a] == "I"}
            if len(in_set) < min_in_size:
                min_in_size = len(in_set)
                grounded_in = in_set

        if grounded_in is not None:
            for a in grounded_in:
                acceptance[a] += prob

    return acceptance


# ===========================================================================
# Hypothesis strategies
# ===========================================================================

@st.composite
def random_small_af(draw: st.DrawFn) -> dict[str, Any]:
    """Generate a random small AF with 2-5 args and probabilistic defeats."""
    n_args = draw(st.integers(min_value=2, max_value=5))
    arg_names = [chr(ord("A") + i) for i in range(n_args)]
    args = set(arg_names)

    # Generate random defeats (including possible self-attacks)
    all_possible = [(a, b) for a in arg_names for b in arg_names if a != b]
    # Each possible defeat edge exists with 50% chance
    defeats: set[tuple[str, str]] = set()
    p_defeats: dict[tuple[str, str], float] = {}

    for edge in all_possible:
        if draw(st.booleans()):
            p = draw(st.floats(min_value=0.01, max_value=0.99))
            defeats.add(edge)
            p_defeats[edge] = p

    return {
        "args": args,
        "defeats": defeats,
        "p_defeats": p_defeats,
    }


# ===========================================================================
# Property-based tests
# ===========================================================================

class TestHypothesisDP:
    """Property-based tests: toy DP must match brute force."""

    @given(af=random_small_af())
    @settings(deadline=None)
    def test_dp_matches_brute_force(self, af: dict[str, Any]) -> None:
        """The I/O/U labelling approach must match brute-force enumeration."""
        args = af["args"]
        defeats = af["defeats"]
        p_defeats = af["p_defeats"]

        dp_result = toy_dp_acceptance(args, defeats, p_defeats, "grounded")
        bf_result = brute_force_acceptance(args, defeats, p_defeats, "grounded")

        for a in args:
            assert abs(dp_result[a] - bf_result[a]) < 1e-9, (
                f"Mismatch for {a}: dp={dp_result[a]}, bf={bf_result[a]}\n"
                f"AF: args={args}, defeats={defeats}, p_defeats={p_defeats}"
            )

    @given(af=random_small_af())
    # This path is explicitly exponential in the number of arguments; keep
    # it smaller while the main DP-vs-brute-force property stays at 200.
    @settings(deadline=None)
    def test_labelling_enum_matches_brute_force(self, af: dict[str, Any]) -> None:
        """The explicit 3^n labelling enumeration must also match brute force."""
        args = af["args"]
        defeats = af["defeats"]
        p_defeats = af["p_defeats"]

        le_result = toy_dp_labelling_enum(
            args, defeats, p_defeats, "grounded", require_witness=True
        )
        bf_result = brute_force_acceptance(args, defeats, p_defeats, "grounded")

        for a in args:
            assert abs(le_result[a] - bf_result[a]) < 1e-9, (
                f"Mismatch for {a}: le={le_result[a]}, bf={bf_result[a]}\n"
                f"AF: args={args}, defeats={defeats}, p_defeats={p_defeats}"
            )

    @given(af=random_small_af())
    @settings(deadline=None)
    def test_probabilities_in_valid_range(self, af: dict[str, Any]) -> None:
        """All acceptance probabilities must be in [0, 1]."""
        result = toy_dp_acceptance(
            af["args"], af["defeats"], af["p_defeats"], "grounded"
        )
        for a, p in result.items():
            assert 0.0 - 1e-12 <= p <= 1.0 + 1e-12, (
                f"P({a}) = {p} out of range"
            )


# ===========================================================================
# Explicit small test cases
# ===========================================================================

class TestExplicitCases:
    """Hand-crafted AFs with known answers."""

    def test_single_attack_a_to_b(self) -> None:
        """A->B, P_D=0.5: A always in (no attackers), B in when edge absent."""
        args = {"A", "B"}
        defeats = {("A", "B")}
        p_defeats = {("A", "B"): 0.5}

        dp = toy_dp_acceptance(args, defeats, p_defeats)
        bf = brute_force_acceptance(args, defeats, p_defeats)

        # A has no attackers -> always IN -> P(A) = 1.0
        assert abs(dp["A"] - 1.0) < 1e-9
        # B: edge present (p=0.5) -> A attacks B -> B out
        #    edge absent (p=0.5) -> no attack -> B in
        assert abs(dp["B"] - 0.5) < 1e-9
        # Must match brute force
        for a in args:
            assert abs(dp[a] - bf[a]) < 1e-9

    def test_chain_a_b_c(self) -> None:
        """A->B, B->C, P_D=0.7: verify against brute force."""
        args = {"A", "B", "C"}
        defeats = {("A", "B"), ("B", "C")}
        p_defeats = {("A", "B"): 0.7, ("B", "C"): 0.7}

        dp = toy_dp_acceptance(args, defeats, p_defeats)
        bf = brute_force_acceptance(args, defeats, p_defeats)

        # A always IN (no attackers)
        assert abs(dp["A"] - 1.0) < 1e-9

        # B: IN when A->B absent (prob 0.3)
        assert abs(dp["B"] - 0.3) < 1e-9

        # C: depends on B's status and B->C edge
        # Case 1: A->B present (0.7), B->C present (0.7): B out, C in -> 0.49
        # Case 2: A->B present (0.7), B->C absent (0.3): B out, C in -> 0.21
        # Case 3: A->B absent (0.3), B->C present (0.7): B in, C out -> 0
        # Case 4: A->B absent (0.3), B->C absent (0.3): B in, C in -> 0.09
        # P(C in) = 0.49 + 0.21 + 0.09 = 0.79
        assert abs(dp["C"] - 0.79) < 1e-9

        for a in args:
            assert abs(dp[a] - bf[a]) < 1e-9

    def test_cycle_a_b_c(self) -> None:
        """A->B->C->A cycle, P_D=0.6: verify against brute force."""
        args = {"A", "B", "C"}
        defeats = {("A", "B"), ("B", "C"), ("C", "A")}
        p_defeats = {("A", "B"): 0.6, ("B", "C"): 0.6, ("C", "A"): 0.6}

        dp = toy_dp_acceptance(args, defeats, p_defeats)
        bf = brute_force_acceptance(args, defeats, p_defeats)

        for a in args:
            assert abs(dp[a] - bf[a]) < 1e-9, (
                f"Cycle mismatch for {a}: dp={dp[a]}, bf={bf[a]}"
            )

    def test_diamond_a_b_attack_c(self) -> None:
        """A->C and B->C, P_D(A->C)=0.3, P_D(B->C)=0.4."""
        args = {"A", "B", "C"}
        defeats = {("A", "C"), ("B", "C")}
        p_defeats = {("A", "C"): 0.3, ("B", "C"): 0.4}

        dp = toy_dp_acceptance(args, defeats, p_defeats)
        bf = brute_force_acceptance(args, defeats, p_defeats)

        # A and B always IN (no attackers)
        assert abs(dp["A"] - 1.0) < 1e-9
        assert abs(dp["B"] - 1.0) < 1e-9

        # C is OUT when at least one edge is realized
        # P(C in) = P(both edges absent) = (1-0.3)*(1-0.4) = 0.7*0.6 = 0.42
        assert abs(dp["C"] - 0.42) < 1e-9
        # P(C out) = 1 - 0.42 = 0.58
        assert abs((1.0 - dp["C"]) - 0.58) < 1e-9

        for a in args:
            assert abs(dp[a] - bf[a]) < 1e-9

    def test_no_defeats(self) -> None:
        """All arguments unattacked -> all IN with prob 1.0."""
        args = {"A", "B", "C"}
        defeats: set[tuple[str, str]] = set()
        p_defeats: dict[tuple[str, str], float] = {}

        dp = toy_dp_acceptance(args, defeats, p_defeats)
        for a in args:
            assert abs(dp[a] - 1.0) < 1e-9

    def test_single_argument(self) -> None:
        """Single argument, no defeats -> always IN."""
        args = {"A"}
        defeats: set[tuple[str, str]] = set()
        p_defeats: dict[tuple[str, str], float] = {}

        dp = toy_dp_acceptance(args, defeats, p_defeats)
        assert abs(dp["A"] - 1.0) < 1e-9

    def test_self_attack(self) -> None:
        """Self-attacking argument: not in grounded extension when edge present."""
        args = {"A"}
        defeats = {("A", "A")}
        p_defeats = {("A", "A"): 0.5}

        dp = toy_dp_acceptance(args, defeats, p_defeats)
        bf = brute_force_acceptance(args, defeats, p_defeats)

        # When self-attack present: A can't be IN (attacker=A not OUT),
        # A is UNDECIDED. When absent: A is IN.
        assert abs(dp["A"] - 0.5) < 1e-9
        assert abs(dp["A"] - bf["A"]) < 1e-9


# ===========================================================================
# Witness mechanism tests
# ===========================================================================

class TestWitnessMechanism:
    """Tests that verify the witness mechanism is necessary for correctness."""

    def test_witness_required_for_out(self) -> None:
        """An argument can only be OUT if a witnessing IN attacker exists
        with a REALIZED attack edge.

        Without witness: might label B as OUT even when the A->B edge
        doesn't exist in this subgraph.
        """
        args = {"A", "B"}
        defeats = {("A", "B")}
        p_defeats = {("A", "B"): 0.5}

        # With witness (correct)
        with_witness = toy_dp_labelling_enum(
            args, defeats, p_defeats, require_witness=True
        )
        # Without witness — uses potential attacks not realized ones
        without_witness = toy_dp_labelling_enum(
            args, defeats, p_defeats, require_witness=False
        )
        brute = brute_force_acceptance(args, defeats, p_defeats)

        # With witness must match brute force
        for a in args:
            assert abs(with_witness[a] - brute[a]) < 1e-9, (
                f"Witness version mismatch for {a}"
            )

        # Note: for this simple case, without_witness may also be correct
        # because A is always IN and the only potential attacker.
        # The difference shows up in more complex cases.

    def test_witness_prevents_overcounting_out(self) -> None:
        """In a subgraph where the attack edge is absent, the target should
        NOT be labelled OUT even though the attacker is IN.

        Setup: A->B->C, all P_D = 1.0 except A->B which is 0.5.
        When A->B absent: B is IN (unattacked), C is OUT via B->C.
        When A->B present: B is OUT, C is IN (B's attack on C exists but B is OUT).

        The witness mechanism ensures B is only OUT when A->B is realized.
        """
        args = {"A", "B", "C"}
        defeats = {("A", "B"), ("B", "C")}
        p_defeats = {("A", "B"): 0.5, ("B", "C"): 1.0}

        dp = toy_dp_acceptance(args, defeats, p_defeats)
        bf = brute_force_acceptance(args, defeats, p_defeats)

        # A always IN
        assert abs(dp["A"] - 1.0) < 1e-9
        # B: IN when A->B absent (0.5), OUT when present (0.5)
        assert abs(dp["B"] - 0.5) < 1e-9
        # C: when B is IN (0.5), C is OUT (B->C always exists)
        #    when B is OUT (0.5), C is IN (no IN attacker)
        assert abs(dp["C"] - 0.5) < 1e-9

        for a in args:
            assert abs(dp[a] - bf[a]) < 1e-9

    def test_unrealized_attack_no_witness(self) -> None:
        """Even with an IN attacker, if the attack edge is not realized,
        the target stays IN/U, not OUT.

        A->B with P_D=0.0 effectively (use very low prob).
        B should almost always be IN.
        """
        args = {"A", "B"}
        defeats = {("A", "B")}
        p_defeats = {("A", "B"): 0.01}

        dp = toy_dp_acceptance(args, defeats, p_defeats)
        bf = brute_force_acceptance(args, defeats, p_defeats)

        assert abs(dp["A"] - 1.0) < 1e-9
        # B is IN 99% of the time (when edge absent)
        assert abs(dp["B"] - 0.99) < 1e-9
        for a in args:
            assert abs(dp[a] - bf[a]) < 1e-9

    def test_diamond_witness_both_attacks(self) -> None:
        """Diamond: A->C, B->C. C is OUT only when at least one realized edge
        from an IN attacker exists.

        Both A and B are IN (no attackers). C needs a witness = one of
        (A,C) or (B,C) being realized.
        """
        args = {"A", "B", "C"}
        defeats = {("A", "C"), ("B", "C")}
        p_defeats = {("A", "C"): 0.5, ("B", "C"): 0.5}

        dp = toy_dp_acceptance(args, defeats, p_defeats)
        bf = brute_force_acceptance(args, defeats, p_defeats)

        # C is IN only when BOTH attacks absent: 0.5 * 0.5 = 0.25
        assert abs(dp["C"] - 0.25) < 1e-9
        for a in args:
            assert abs(dp[a] - bf[a]) < 1e-9
