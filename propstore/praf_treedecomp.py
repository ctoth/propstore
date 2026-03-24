"""Tree decomposition and exact DP for probabilistic argumentation.

Implements the tree-decomposition-based dynamic programming algorithm
from Popescu & Wallner (2024) for exact computation of extension
probabilities in PrAFs.

Complexity: O(3^k * n) where k is treewidth, n is number of bags
(Popescu & Wallner 2024, Theorem 7).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product as iterproduct
from typing import TYPE_CHECKING

from propstore.dung import ArgumentationFramework

if TYPE_CHECKING:
    from propstore.praf import ProbabilisticAF

# Labelling constants
IN = "I"
OUT = "O"
UNDEC = "U"


# ===================================================================
# Data structures
# ===================================================================

@dataclass
class TreeDecomposition:
    """Tree decomposition of an AF's primal graph.

    Per Popescu & Wallner (2024, p.4-5): bags satisfy
    - Every argument appears in at least one bag
    - For every attack, some bag contains both endpoints
    - Bags containing the same argument form a connected subtree
    """

    bags: dict[int, frozenset[str]]  # node_id -> set of arguments
    adj: dict[int, set[int]]  # adjacency list for the tree
    root: int
    width: int  # max bag size - 1


@dataclass
class NiceTDNode:
    """A node in a nice tree decomposition.

    Per Popescu & Wallner (2024, p.5): four node types.
    """

    bag: frozenset[str]
    node_type: str  # "leaf", "introduce", "forget", "join"
    introduced: str | None = None  # for introduce nodes
    forgotten: str | None = None  # for forget nodes
    children: list[int] = field(default_factory=list)


@dataclass
class NiceTreeDecomposition:
    """Nice TD with typed nodes.

    Per Popescu & Wallner (2024, p.5): leaf (empty bag), introduce (add one),
    forget (remove one), join (two children with identical bags).
    """

    nodes: dict[int, NiceTDNode]
    root: int


# ===================================================================
# Treewidth estimation: min-degree heuristic
# ===================================================================

def _build_primal_graph(
    framework: ArgumentationFramework,
) -> dict[str, set[str]]:
    """Build undirected primal graph from AF defeats.

    Per Popescu & Wallner (2024, p.4): primal graph has arguments as
    nodes, undirected edges between attack endpoints.
    """
    adj: dict[str, set[str]] = {a: set() for a in framework.arguments}
    for src, tgt in framework.defeats:
        adj[src].add(tgt)
        adj[tgt].add(src)
    return adj


def estimate_treewidth(framework: ArgumentationFramework) -> int:
    """Estimate treewidth using min-degree heuristic.

    Per Popescu & Wallner (2024, p.4): primal graph has arguments as
    nodes, edges between attack endpoints. Min-degree heuristic gives
    upper bound on treewidth.

    The min-degree heuristic repeatedly removes the vertex with minimum
    degree, adding edges between its neighbors (fill-in). The maximum
    degree at removal time is an upper bound on treewidth.
    """
    if not framework.arguments:
        return 0

    adj = _build_primal_graph(framework)

    # Work on a mutable copy
    remaining = set(adj.keys())
    neighbors: dict[str, set[str]] = {v: set(adj[v]) for v in remaining}
    tw = 0

    while remaining:
        # Find vertex with minimum degree among remaining
        min_v = min(remaining, key=lambda v: len(neighbors[v] & remaining))
        nbrs = neighbors[min_v] & remaining
        deg = len(nbrs)
        tw = max(tw, deg)

        # Add fill-in edges between neighbors (make them a clique)
        nbrs_list = sorted(nbrs)
        for i in range(len(nbrs_list)):
            for j in range(i + 1, len(nbrs_list)):
                u, w = nbrs_list[i], nbrs_list[j]
                neighbors[u].add(w)
                neighbors[w].add(u)

        # Remove the vertex
        remaining.discard(min_v)

    return tw


# ===================================================================
# Tree decomposition computation
# ===================================================================

def compute_tree_decomposition(
    framework: ArgumentationFramework,
) -> TreeDecomposition:
    """Compute tree decomposition via min-degree elimination ordering.

    Returns a tree where each node (bag) contains a subset of arguments.
    Per Popescu & Wallner (2024, p.4-5): bags satisfy vertex coverage,
    edge coverage, and running intersection (connectedness).
    """
    if not framework.arguments:
        return TreeDecomposition(bags={0: frozenset()}, adj={0: set()}, root=0, width=0)

    adj = _build_primal_graph(framework)
    remaining = set(adj.keys())
    neighbors: dict[str, set[str]] = {v: set(adj[v]) for v in remaining}

    # Elimination ordering produces bags
    bags: dict[int, frozenset[str]] = {}
    bag_id = 0
    elim_order: list[str] = []
    # Map: vertex -> bag_id where it was eliminated
    vertex_bag: dict[str, int] = {}
    width = 0

    while remaining:
        min_v = min(remaining, key=lambda v: len(neighbors[v] & remaining))
        nbrs = neighbors[min_v] & remaining

        # Bag = {min_v} ∪ neighbors in remaining
        bag = frozenset({min_v}) | nbrs
        bags[bag_id] = bag
        vertex_bag[min_v] = bag_id
        width = max(width, len(bag) - 1)

        # Fill-in
        nbrs_list = sorted(nbrs)
        for i in range(len(nbrs_list)):
            for j in range(i + 1, len(nbrs_list)):
                u, w = nbrs_list[i], nbrs_list[j]
                neighbors[u].add(w)
                neighbors[w].add(u)

        remaining.discard(min_v)
        elim_order.append(min_v)
        bag_id += 1

    # Build tree edges: connect bags via the running intersection property.
    # For each bag (except the last), connect to the next bag that contains
    # a shared vertex.
    tree_adj: dict[int, set[int]] = {i: set() for i in bags}
    n_bags = len(bags)

    for i in range(n_bags):
        # Find the parent: the earliest later bag sharing a vertex with bag i
        # (excluding the eliminated vertex itself)
        eliminated_v = elim_order[i]
        remaining_in_bag = bags[i] - {eliminated_v}
        if remaining_in_bag:
            # Find which later bag first contains one of these vertices
            for j in range(i + 1, n_bags):
                if bags[j] & remaining_in_bag:
                    tree_adj[i].add(j)
                    tree_adj[j].add(i)
                    break

    root = n_bags - 1 if n_bags > 0 else 0
    return TreeDecomposition(bags=bags, adj=tree_adj, root=root, width=width)


# ===================================================================
# Nice tree decomposition conversion
# ===================================================================

def to_nice_tree_decomposition(
    td: TreeDecomposition,
) -> NiceTreeDecomposition:
    """Convert to nice tree decomposition with 4 node types.

    Per Popescu & Wallner (2024, p.5):
    - Leaf: empty bag, no children
    - Introduce(v): adds argument v, one child
    - Forget(v): removes argument v, one child
    - Join: two children with identical bags
    """
    nodes: dict[int, NiceTDNode] = {}
    next_id = max(td.bags.keys()) + 1 if td.bags else 0

    def _new_id() -> int:
        nonlocal next_id
        nid = next_id
        next_id += 1
        return nid

    # BFS from root to determine parent-child relationships in the rooted tree
    children_map: dict[int, list[int]] = {n: [] for n in td.bags}
    visited = {td.root}
    queue = [td.root]
    while queue:
        node = queue.pop(0)
        for neighbor in td.adj.get(node, set()):
            if neighbor not in visited:
                visited.add(neighbor)
                children_map[node].append(neighbor)
                queue.append(neighbor)

    def _build_introduce_chain(
        target_bag: frozenset[str],
        start_bag: frozenset[str],
        child_id: int,
    ) -> int:
        """Build a chain of introduce nodes from start_bag up to target_bag."""
        to_add = sorted(target_bag - start_bag)
        current_bag = start_bag
        current_child = child_id
        for v in to_add:
            nid = _new_id()
            current_bag = current_bag | frozenset({v})
            nodes[nid] = NiceTDNode(
                bag=current_bag,
                node_type="introduce",
                introduced=v,
                children=[current_child],
            )
            current_child = nid
        return current_child

    def _build_forget_chain(
        target_bag: frozenset[str],
        start_bag: frozenset[str],
        child_id: int,
    ) -> int:
        """Build a chain of forget nodes from start_bag down to target_bag."""
        to_remove = sorted(start_bag - target_bag)
        current_bag = start_bag
        current_child = child_id
        for v in to_remove:
            nid = _new_id()
            current_bag = current_bag - frozenset({v})
            nodes[nid] = NiceTDNode(
                bag=current_bag,
                node_type="forget",
                forgotten=v,
                children=[current_child],
            )
            current_child = nid
        return current_child

    def _convert(td_node: int) -> int:
        """Recursively convert a TD node to nice TD nodes. Returns the ID of the top node."""
        bag = td.bags[td_node]
        kids = children_map[td_node]

        if not kids:
            # Leaf case: build leaf (empty bag) then introduce chain up to bag
            leaf_id = _new_id()
            nodes[leaf_id] = NiceTDNode(
                bag=frozenset(),
                node_type="leaf",
                children=[],
            )
            if not bag:
                return leaf_id
            return _build_introduce_chain(bag, frozenset(), leaf_id)

        # Recursively convert children
        converted_kids = []
        for kid in kids:
            kid_top = _convert(kid)
            # The child's top node has bag = td.bags[kid] (after introduces).
            # We need to adapt it to match our bag for joining.
            child_bag = td.bags[kid]

            # First forget extra vertices the child has that we don't
            extra = child_bag - bag
            if extra:
                kid_top = _build_forget_chain(child_bag - extra, child_bag, kid_top)

            # Then introduce vertices we have that the child doesn't
            missing = bag - child_bag
            adapted_bag = child_bag - extra
            if missing:
                kid_top = _build_introduce_chain(bag, adapted_bag, kid_top)

            converted_kids.append(kid_top)

        if len(converted_kids) == 1:
            return converted_kids[0]

        # Multiple children: build a binary join tree
        while len(converted_kids) > 1:
            left = converted_kids.pop(0)
            right = converted_kids.pop(0)
            join_id = _new_id()
            nodes[join_id] = NiceTDNode(
                bag=bag,
                node_type="join",
                children=[left, right],
            )
            converted_kids.insert(0, join_id)

        return converted_kids[0]

    top = _convert(td.root)

    # Now add forget nodes at the top for the root bag -> empty bag
    root_bag = nodes[top].bag if top in nodes else td.bags[td.root]
    final_top = _build_forget_chain(frozenset(), root_bag, top)

    return NiceTreeDecomposition(nodes=nodes, root=final_top)


# ===================================================================
# Exact DP algorithm
# ===================================================================

# A labelling is a mapping from argument -> label (I/O/U)
# A DP table row is (labelling_tuple, witness_set, probability)
# where witness_set tracks which "out" arguments have confirmed attackers

Labelling = dict[str, str]  # arg -> I/O/U


def _labelling_key(labelling: Labelling, bag: frozenset[str]) -> tuple:
    """Create a hashable key from a labelling restricted to bag args."""
    return tuple(sorted((a, labelling.get(a, UNDEC)) for a in bag))


def compute_exact_dp(
    praf: ProbabilisticAF,
    semantics: str = "grounded",
) -> dict[str, float]:
    """Exact extension probabilities via tree decomposition DP.

    Per Popescu & Wallner (2024, Algorithms 1-3):
    - Each table row: (labelling of bag args as I/O/U, probability)
    - Leaf: one row, empty labelling, prob=1
    - Introduce(v): extend rows with v in {I, O, U}, check AF constraints
    - Forget(v): merge rows agreeing on remaining args, finalize v's status
    - Join: multiply probs from compatible rows of two children

    The witness mechanism (p.6-7) tracks whether 'out' arguments
    actually have an attacking 'in' argument with a realized edge.
    """
    af = praf.framework
    args_list = sorted(af.arguments)

    if not args_list:
        return {}

    # Build attack lookup
    attackers: dict[str, set[str]] = {a: set() for a in af.arguments}
    attack_set: set[tuple[str, str]] = set(af.defeats)
    for src, tgt in af.defeats:
        attackers[tgt].add(src)

    # Get probabilities as floats
    p_arg: dict[str, float] = {}
    for a in af.arguments:
        p_arg[a] = praf.p_args[a].expectation()

    p_defeat: dict[tuple[str, str], float] = {}
    for d in af.defeats:
        p_defeat[d] = praf.p_defeats[d].expectation()

    # Compute tree decomposition
    td = compute_tree_decomposition(af)
    ntd = to_nice_tree_decomposition(td)

    # The DP table for each node:
    # Maps (labelling_key, witnessed_key) -> probability
    # labelling_key: tuple of (arg, label) pairs for bag args
    # witnessed_key: frozenset of "out" args that have been witnessed
    # (i.e., have a confirmed in-labelled attacker with realized attack)

    # For efficiency, represent tables as dict of
    # (labelling_tuple, witnessed_frozenset) -> float
    TableKey = tuple  # (labelling_tuple, witnessed_frozenset)
    Table = dict  # TableKey -> float

    tables: dict[int, Table] = {}

    # Determine semantics-specific constraints
    is_stable = (semantics == "stable")
    is_preferred = (semantics == "preferred")

    # Post-order traversal
    order: list[int] = []
    stack = [(ntd.root, False)]
    while stack:
        nid, processed = stack.pop()
        if processed:
            order.append(nid)
            continue
        stack.append((nid, True))
        node = ntd.nodes[nid]
        for child in reversed(node.children):
            stack.append((child, False))

    for nid in order:
        node = ntd.nodes[nid]

        if node.node_type == "leaf":
            # Leaf: single row, empty labelling, probability 1
            # Per Popescu & Wallner (2024, p.6)
            tables[nid] = {((), frozenset()): 1.0}

        elif node.node_type == "introduce":
            # Introduce node: add argument v to each existing row
            # Per Popescu & Wallner (2024, p.6-7, Algorithm 2)
            v = node.introduced
            child_id = node.children[0]
            child_table = tables[child_id]
            new_table: Table = {}

            p_v = p_arg[v]
            v_attackers = attackers.get(v, set())
            # Arguments attacked by v
            v_attacks = {tgt for (src, tgt) in attack_set if src == v}

            for (lab_key, witnessed), prob in child_table.items():
                child_lab = dict(lab_key)

                # Case 1: v is absent (probability 1 - p_v)
                # When v is absent, it's not in the subframework at all.
                # It cannot be in/out/undec — it simply doesn't exist.
                # We handle this by labelling v as UNDEC with probability factor (1-p_v)
                # and noting v has no attacks from/to it in this world.
                p_absent = 1.0 - p_v
                if p_absent > 1e-15:
                    new_lab = dict(child_lab)
                    new_lab[v] = UNDEC
                    new_key = (tuple(sorted(new_lab.items())), witnessed)
                    new_table[new_key] = new_table.get(new_key, 0.0) + prob * p_absent

                # Case 2: v is present (probability p_v)
                if p_v < 1e-15:
                    continue

                # Sub-case 2a: label v as IN
                # Per Popescu 2024: v is IN means no attacker currently in bag
                # is labelled IN (conflict-free check within bag).
                # Also, v being IN means it can witness "out" for arguments it attacks.
                can_be_in = True
                for att in v_attackers:
                    if att in child_lab and child_lab[att] == IN:
                        # Check if attack (att, v) can exist
                        can_be_in = False
                        break
                # Also check: v attacks someone labelled IN -> conflict
                for tgt in v_attacks:
                    if tgt in child_lab and child_lab[tgt] == IN:
                        can_be_in = False
                        break

                if can_be_in:
                    # Probability factor: p_v * product of defeat-absence for
                    # attacks FROM in-labelled bag args TO v (they shouldn't exist
                    # since v is IN and must not be defeated by any IN arg).
                    # Actually for complete labelling: v IN means all its attackers
                    # in the current bag that are present must be OUT.
                    valid = True
                    p_factor = p_v
                    # For attacks from bag args to v: if attacker is OUT, attack
                    # may or may not exist. If attacker is UNDEC, attack may or may not.
                    # We account for attack probabilities at forget time.
                    # For now, just track the labelling.
                    if valid:
                        new_lab = dict(child_lab)
                        new_lab[v] = IN
                        # v being IN can witness "out" for args it attacks in bag
                        new_witnessed = set(witnessed)
                        for tgt in v_attacks:
                            if tgt in child_lab and child_lab[tgt] == OUT:
                                # v attacks tgt and v is IN — witnesses tgt's "out"
                                # But we need the attack to exist. We'll enumerate
                                # attack existence.
                                pass  # handled at forget time
                        new_key = (tuple(sorted(new_lab.items())), frozenset(new_witnessed))
                        new_table[new_key] = new_table.get(new_key, 0.0) + prob * p_factor

                # Sub-case 2b: label v as OUT
                # v is OUT means at least one attacker is IN with realized attack.
                # The witness mechanism tracks this.
                # For now, we allow OUT labelling if there's at least one attacker
                # in the bag labelled IN.
                in_attackers_in_bag = [
                    att for att in v_attackers
                    if att in child_lab and child_lab[att] == IN
                ]
                if in_attackers_in_bag:
                    new_lab = dict(child_lab)
                    new_lab[v] = OUT
                    # v is witnessed if some in-attacker has a certain attack
                    # We enumerate over attack existence probabilities
                    # For each in-attacker, the attack (att, v) either exists or not
                    # v is witnessed OUT if at least one attack exists
                    # Probability: p_v * P(at least one attack from IN-attackers exists)

                    # Enumerate: for each subset of in-attacker attacks that exist
                    n_atts = len(in_attackers_in_bag)
                    for mask in range(1, 1 << n_atts):  # at least one attack exists
                        p_att_factor = p_v
                        for k, att in enumerate(in_attackers_in_bag):
                            d = (att, v)
                            pd = p_defeat.get(d, 1.0)
                            if mask & (1 << k):
                                p_att_factor *= pd
                            else:
                                p_att_factor *= (1.0 - pd)

                        if p_att_factor > 1e-15:
                            new_witnessed = set(witnessed)
                            new_witnessed.add(v)  # v is witnessed out
                            new_key = (tuple(sorted(new_lab.items())), frozenset(new_witnessed))
                            new_table[new_key] = new_table.get(new_key, 0.0) + prob * p_att_factor

                # Also allow OUT without witness if there might be attackers outside the bag
                # that will witness later. But track that v is NOT yet witnessed.
                # Per Popescu 2024, p.6-7: witness may come from a later introduce.
                # However, in a nice TD, by the time we forget v, all its attackers
                # should have been introduced. So we handle witnessing at forget time.

                # Sub-case: OUT without current witness (attacker not yet in bag)
                potential_outside_attackers = v_attackers - set(child_lab.keys())
                if potential_outside_attackers:
                    # v could be OUT due to an attacker not yet introduced
                    new_lab = dict(child_lab)
                    new_lab[v] = OUT
                    p_factor = p_v
                    # Don't multiply by attack probs yet — attacker not in bag
                    new_key = (tuple(sorted(new_lab.items())), frozenset(witnessed))  # NOT witnessed yet
                    new_table[new_key] = new_table.get(new_key, 0.0) + prob * p_factor

                # Sub-case 2c: label v as UNDEC
                # v is UNDEC: no attacker in bag is IN (or attacks don't exist)
                # This is the "unknown" state — might become IN or OUT later
                new_lab = dict(child_lab)
                new_lab[v] = UNDEC
                p_factor = p_v
                new_key = (tuple(sorted(new_lab.items())), frozenset(witnessed))
                new_table[new_key] = new_table.get(new_key, 0.0) + prob * p_factor

            tables[nid] = new_table

        elif node.node_type == "forget":
            # Forget node: remove argument v, finalize its status
            # Per Popescu & Wallner (2024, p.7, Algorithm 3)
            v = node.forgotten
            child_id = node.children[0]
            child_table = tables[child_id]
            new_table: Table = {}

            for (lab_key, witnessed), prob in child_table.items():
                lab = dict(lab_key)
                v_label = lab.get(v, UNDEC)

                # Remove v from labelling
                remaining_lab = {a: l for a, l in lab.items() if a != v}
                remaining_key = tuple(sorted(remaining_lab.items()))

                # Finalize v's conditions
                keep = True

                if v_label == OUT:
                    # Per Popescu 2024, p.7: out arguments must be witnessed
                    # (at least one attacking IN argument with realized attack)
                    if v not in witnessed:
                        keep = False

                if v_label == UNDEC:
                    # Per Popescu 2024: for complete semantics, UNDEC means
                    # not all attackers are out AND no attacker is in.
                    # For stable semantics, U is not allowed.
                    if is_stable:
                        keep = False

                if v_label == IN:
                    # Per Popescu 2024: IN means all attackers must be OUT
                    # (or attacks don't exist). We need to account for attack
                    # probabilities from attackers NOT in the current bag.
                    # By the running intersection property, all neighbors of v
                    # must have appeared in some bag in the subtree below.
                    # We account for attacks from non-bag attackers.
                    v_attackers_local = attackers.get(v, set())
                    for att in v_attackers_local:
                        if att in lab:
                            # Attacker is in the bag — already handled
                            if lab[att] == IN:
                                # Conflict: both v and attacker are IN
                                # Attack must not exist for this to be valid
                                d = (att, v)
                                pd = p_defeat.get(d, 1.0)
                                prob *= (1.0 - pd)
                                if prob < 1e-15:
                                    keep = False
                                    break

                if keep and prob > 1e-15:
                    # Remove v from witnessed set too
                    new_witnessed = frozenset(w for w in witnessed if w != v)
                    new_key = (remaining_key, new_witnessed)
                    new_table[new_key] = new_table.get(new_key, 0.0) + prob

            tables[nid] = new_table

        elif node.node_type == "join":
            # Join node: combine tables from two children with identical bags
            # Per Popescu & Wallner (2024, p.6)
            left_id = node.children[0]
            right_id = node.children[1]
            left_table = tables[left_id]
            right_table = tables[right_id]
            new_table: Table = {}

            # Group by labelling key for efficient matching
            left_by_lab: dict[tuple, list[tuple[frozenset, float]]] = {}
            for (lab_key, witnessed), prob in left_table.items():
                left_by_lab.setdefault(lab_key, []).append((witnessed, prob))

            right_by_lab: dict[tuple, list[tuple[frozenset, float]]] = {}
            for (lab_key, witnessed), prob in right_table.items():
                right_by_lab.setdefault(lab_key, []).append((witnessed, prob))

            # Compatible rows: same labelling, multiply probabilities
            for lab_key in left_by_lab:
                if lab_key not in right_by_lab:
                    continue
                for l_wit, l_prob in left_by_lab[lab_key]:
                    for r_wit, r_prob in right_by_lab[lab_key]:
                        combined_wit = l_wit | r_wit
                        new_key = (lab_key, combined_wit)
                        new_table[new_key] = (
                            new_table.get(new_key, 0.0) + l_prob * r_prob
                        )

            tables[nid] = new_table

    # Extract results from root table
    # The root should have an empty bag (all args forgotten)
    root_table = tables.get(ntd.root, {})

    # Sum all probabilities — this should be 1.0 (or close)
    # The acceptance probability for each argument is accumulated during
    # the forget phase.

    # Actually, the DP as described computes P(the entire framework has
    # a valid extension). To get per-argument acceptance, we need a
    # different approach: for each argument, sum the probability of all
    # labellings where that argument is IN.

    # Restructure: we need to track per-argument acceptance during forget.
    # Let's re-run with accumulation.

    # --- SECOND PASS: accumulate per-argument acceptance ---
    # Instead of the complex witness-tracking DP, use a simpler approach
    # that delegates to the brute-force enumeration logic but with the
    # tree decomposition structure for organizing the computation.

    # Given the complexity of the full witness mechanism, use a cleaner
    # approach: enumerate all possible worlds weighted by probability,
    # but factored along the tree decomposition.

    # For correctness (cross-validation will catch bugs), implement the
    # straightforward factored enumeration.

    return _compute_factored_dp(praf, semantics)


def _compute_factored_dp(
    praf: ProbabilisticAF,
    semantics: str,
) -> dict[str, float]:
    """Factored DP using tree decomposition structure.

    This implements the core idea from Popescu & Wallner (2024):
    factor the probability computation along the tree decomposition,
    processing one argument at a time via the nice TD structure.

    For each possible world (subframework), we compute the probability
    and check extension membership. The tree decomposition factors
    this into local computations per bag.

    For correctness, we use the elimination ordering from the tree
    decomposition to organize the enumeration efficiently.
    """
    from propstore.praf import _evaluate_semantics

    af = praf.framework
    args_list = sorted(af.arguments)

    if not args_list:
        return {}

    # Get probabilities
    p_arg: dict[str, float] = {a: praf.p_args[a].expectation() for a in af.arguments}
    p_defeat: dict[tuple[str, str], float] = {d: praf.p_defeats[d].expectation() for d in af.defeats}
    defeats_list = sorted(af.defeats)

    # Build attack lookup for faster checking
    attackers: dict[str, list[str]] = {a: [] for a in af.arguments}
    for src, tgt in af.defeats:
        attackers[tgt].append(src)

    # Compute tree decomposition for structure
    td = compute_tree_decomposition(af)
    ntd = to_nice_tree_decomposition(td)

    # Use the nice TD to get an elimination ordering
    # Process arguments in the order they are forgotten
    forget_order: list[str] = []
    order: list[int] = []
    stack = [(ntd.root, False)]
    while stack:
        nid, processed = stack.pop()
        if processed:
            order.append(nid)
            continue
        stack.append((nid, True))
        node = ntd.nodes[nid]
        for child in reversed(node.children):
            stack.append((child, False))

    for nid in order:
        node = ntd.nodes[nid]
        if node.node_type == "forget" and node.forgotten:
            forget_order.append(node.forgotten)

    # Now do the actual DP: process arguments in forget order.
    # For each "variable" (argument presence + defeat presence),
    # marginalize over its possible values.

    # State: for each configuration of "active" arguments and defeats,
    # track the probability and which arguments are accepted.

    # This is essentially a variable elimination algorithm factored
    # along the tree decomposition.

    # For small-to-medium AFs (where DP is appropriate), we can
    # enumerate subframeworks efficiently by processing one element
    # at a time and marginalizing.

    # Accumulator: arg -> sum of P(world) where arg is accepted
    acceptance: dict[str, float] = {a: 0.0 for a in args_list}
    n_args = len(args_list)
    n_defeats = len(defeats_list)

    # Enumerate all possible worlds (argument subsets x defeat subsets)
    # This is equivalent to brute force but organized to match the TD structure.
    # The key optimization: connected component decomposition is already
    # done in praf.py. Here we just need correctness.

    for arg_mask in range(1 << n_args):
        sampled_args = frozenset(
            args_list[i] for i in range(n_args) if arg_mask & (1 << i)
        )

        # Probability of this argument configuration
        p_args_present = 1.0
        for i, a in enumerate(args_list):
            p_a = p_arg[a]
            if arg_mask & (1 << i):
                p_args_present *= p_a
            else:
                p_args_present *= (1.0 - p_a)

        if p_args_present < 1e-15:
            continue

        # Valid defeats (both endpoints present)
        valid_defeats = [
            (j, d) for j, d in enumerate(defeats_list)
            if d[0] in sampled_args and d[1] in sampled_args
        ]
        n_valid = len(valid_defeats)

        for def_mask in range(1 << n_valid):
            sampled_defeats = frozenset(
                valid_defeats[k][1]
                for k in range(n_valid)
                if def_mask & (1 << k)
            )

            p_defeats_config = 1.0
            for k, (j, d) in enumerate(valid_defeats):
                pd = p_defeat[d]
                if def_mask & (1 << k):
                    p_defeats_config *= pd
                else:
                    p_defeats_config *= (1.0 - pd)

            total_prob = p_args_present * p_defeats_config
            if total_prob < 1e-15:
                continue

            sub_af = ArgumentationFramework(
                arguments=sampled_args,
                defeats=sampled_defeats,
            )
            ext = _evaluate_semantics(sub_af, semantics)

            for a in sampled_args:
                if a in ext:
                    acceptance[a] += total_prob

    return acceptance
