"""Branch and bound over an exact relaxation, as a trace of the tree it walked.

One role: make a linear programme's answer whole, and say where the search went.

    python branch_and_bound.py --problem knapsack --output out/knapsack.jsonl

The relaxation is [`simplex.py`](simplex.py)'s, so every bound here is exact and
a node is pruned because it provably cannot hold the answer, never because a
float said so.

**The dichotomy is Dakin's, not Land and Doig's.** A variable the relaxation
leaves at `v` between two integers is split into `x <= floor(v)` and
`x >= ceil(v)`, two children covering the whole feasible region between them.
Land and Doig branch on *equalities* and step outward to further integers, so
their tree is not binary; the two-child version is Dakin 1965.

The walk is depth first and takes the `<=` child first. Nothing here is clever
about which variable to split or which child to open: the point is a tree small
enough to look at, and a rule anyone can check by hand is worth more here than a
rule that finds the answer two nodes sooner.

What it emits is the `search` world of [`event_trace.py`](../event_trace.py):
a node is `open`ed, `bound`ed by its relaxation, then either `prune`d, or it
`adopt`s a whole point, or it branches and is `close`d when its children are done.
The same five verbs describe the tensor toolkit's tree and its plateau crossing,
which is the whole reason the vocabulary is not the sorts'.
"""

import argparse
import pathlib
import sys
from fractions import Fraction

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import event_trace  # noqa: E402
from simplex import (INFEASIBLE, MAXIMISE, OPTIMAL, Programme,  # noqa: E402
                     UNBOUNDED, solve)

# The default ceiling on nodes. Reaching it stops the walk with the best point
# found so far, which bounds the answer without proving it, and the trace says
# so: a node pruned `limit` is a node nobody looked inside.
NODE_LIMIT = 5000


class Search:
    """The walk, and the trace it writes as it goes."""

    def __init__(self, programme, writer, node_limit=NODE_LIMIT):
        self.root = programme
        self.writer = writer
        self.remaining = node_limit
        self.best = None
        self.best_point = None
        self.opened = 0
        self.exhausted = True

    def improves(self, value):
        if self.best is None:
            return True
        return value > self.best if self.root.sense == MAXIMISE else value < self.best

    def explore(self, node, parent=None, depth=0, branch=None):
        name = "n%d" % self.opened
        self.opened += 1
        self.writer.emit("open", name, parent=parent, depth=depth, branch=branch)

        if self.remaining == 0:
            self.exhausted = False
            self.writer.emit("prune", name, why="limit")
            return
        self.remaining -= 1

        status, point, value = solve(node)
        if status in (INFEASIBLE, UNBOUNDED):
            self.writer.emit("prune", name, why=status)
            return
        self.writer.emit("bound", name, value=str(value))

        # The relaxation bounds everything below this node, so a node that
        # cannot beat the incumbent has no descendant that can.
        if not self.improves(value):
            self.writer.emit("prune", name, why="bounded")
            return

        fractional = next((index for index in self.root.integral
                           if point[index].denominator != 1), None)
        if fractional is None:
            self.best, self.best_point = value, point
            self.writer.emit("adopt", name, value=str(value),
                             point=[str(coordinate) for coordinate in point])
            return

        split = point[fractional].numerator // point[fractional].denominator
        unit = [Fraction(1) if index == fractional else Fraction(0)
                for index in range(self.root.width)]
        for relation, bound in (("<=", split), (">=", split + 1)):
            self.explore(node.with_row(unit, relation, bound), name, depth + 1,
                         "x%d %s %d" % (fractional, relation, bound))
        self.writer.emit("close", name)


def build(programme, node_limit=NODE_LIMIT, name="branch_and_bound"):
    """Run one programme and return (its writer, the best point, its value)."""
    writer = event_trace.Writer(name, "search", seed=None, sense=programme.sense,
                                variables=programme.width,
                                constraints=len(programme.rows),
                                integral=list(programme.integral),
                                node_limit=node_limit)
    search = Search(programme, writer, node_limit)
    search.explore(programme)
    return writer, search.best_point, search.best


def brute_force(programme, ceiling):
    """The best whole point in `[0, ceiling]^n`, by looking at every one of them.

    Here to be disagreed with. It is the only thing in this folder that cannot be
    wrong in an interesting way, which is what makes it worth testing against.
    """
    best, best_point = None, None
    width = programme.width
    for index in range((ceiling + 1) ** width):
        point, remainder = [], index
        for _ in range(width):
            point.append(Fraction(remainder % (ceiling + 1)))
            remainder //= ceiling + 1
        if not programme.satisfies(point):
            continue
        value = programme.value_at(point)
        if best is None or (value > best if programme.sense == MAXIMISE else value < best):
            best, best_point = value, point
    return best_point, best


# The programmes this ships with, as data. A knapsack is here because its
# relaxation is famously fractional in exactly one variable, so the tree it
# forces is the smallest thing that is honestly a tree and not a line.
PROBLEMS = {
    "knapsack": Programme(
        objective=[16, 22, 12, 8],
        rows=[([5, 7, 4, 3], "<=", 14)],
        sense=MAXIMISE, integral=(0, 1, 2, 3)),
    "assignment": Programme(
        objective=[13, 8, 5, 9, 11, 6, 7, 4, 10],
        rows=[([1, 1, 1, 0, 0, 0, 0, 0, 0], "=", 1),
              ([0, 0, 0, 1, 1, 1, 0, 0, 0], "=", 1),
              ([0, 0, 0, 0, 0, 0, 1, 1, 1], "=", 1),
              ([1, 0, 0, 1, 0, 0, 1, 0, 0], "=", 1),
              ([0, 1, 0, 0, 1, 0, 0, 1, 0], "=", 1),
              ([0, 0, 1, 0, 0, 1, 0, 0, 1], "=", 1)],
        sense=MAXIMISE, integral=tuple(range(9))),
    # Minimum vertex cover on a five-cycle, the standard example of a relaxation
    # that is not whole. Every edge wants one of its two ends, and setting every
    # x to 1/2 satisfies all five at a cost of 5/2. No cover of an odd cycle is
    # that cheap: three vertices are needed, so the gap between 5/2 and 3 is real
    # and the branching that closes it is not an artefact of how it was written.
    "vertex_cover": Programme(
        objective=[1, 1, 1, 1, 1],
        rows=[([1, 1, 0, 0, 0], ">=", 1), ([0, 1, 1, 0, 0], ">=", 1),
              ([0, 0, 1, 1, 0], ">=", 1), ([0, 0, 0, 1, 1], ">=", 1),
              ([1, 0, 0, 0, 1], ">=", 1),
              ([1, 0, 0, 0, 0], "<=", 1), ([0, 1, 0, 0, 0], "<=", 1),
              ([0, 0, 1, 0, 0], "<=", 1), ([0, 0, 0, 1, 0], "<=", 1),
              ([0, 0, 0, 0, 1], "<=", 1)],
        sense="min", integral=(0, 1, 2, 3, 4)),
}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Branch and bound, emitting an event trace.")
    parser.add_argument("--problem", choices=sorted(PROBLEMS), default="knapsack")
    parser.add_argument("--node-limit", type=int, default=NODE_LIMIT)
    parser.add_argument("--output", default=None, help="write here instead of stdout")
    args = parser.parse_args(argv)

    writer, point, value = build(PROBLEMS[args.problem], args.node_limit, args.problem)
    if args.output:
        pathlib.Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        writer.write(args.output)
        print("[%s] %d events, best %s at %s"
              % (args.problem, len(writer.events), value,
                 [str(coordinate) for coordinate in point] if point else "nothing"))
    else:
        sys.stdout.write(writer.dumps())
    return 0


if __name__ == "__main__":
    sys.exit(main())
