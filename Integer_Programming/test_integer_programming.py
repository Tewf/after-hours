"""Check the simplex against arithmetic, and branch and bound against brute force.

    python test_integer_programming.py

One role: disagree with the search. Every random programme here is small enough
that every whole point in its box can be looked at, and `brute_force` looks at
all of them. If the tree and the enumeration ever name different optima then the
pruning threw away the answer, which is the failure worth catching, because a
branch and bound that prunes too hard still returns confidently.

The trace is checked the same way the sorts' is: `summarise` reads the events
knowing nothing about branch and bound, and what it reads back has to agree with
what the search said it did.
"""

import pathlib
import random
import sys
from fractions import Fraction

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import event_trace  # noqa: E402
import branch_and_bound  # noqa: E402
from simplex import MAXIMISE, OPTIMAL, Programme, solve  # noqa: E402

INSTANCES = 200
CEILING = 4          # the box brute force searches, and the bound every random row gives


def summarise(head, events):
    """Read a search trace back with no knowledge of what wrote it.

    Returns `(nodes, best adopted value, deepest node)` and asserts on the way
    that the tree is a tree: a node names a parent that was opened before it, at
    one less depth, and no node is spoken about twice.
    """
    depth_of, best, deepest = {}, None, 0
    settled = set()
    for event in events:
        name = event["ids"][0]
        attrs = event.get("attrs", {})
        if event["op"] == "open":
            assert name not in depth_of, "%s opened twice" % name
            parent = attrs["parent"]
            if parent is None:
                assert not depth_of, "%s is a second root" % name
                assert attrs["depth"] == 0, "the root sits at depth %d" % attrs["depth"]
            else:
                assert parent in depth_of, "%s names an unopened parent %s" % (name, parent)
                assert attrs["depth"] == depth_of[parent] + 1, (
                    "%s sits %d below its parent" % (name, attrs["depth"] - depth_of[parent]))
            depth_of[name] = attrs["depth"]
            deepest = max(deepest, attrs["depth"])
        else:
            assert name in depth_of, "%s spoken about before it was opened" % name
            if event["op"] in ("prune", "adopt", "close"):
                assert name not in settled, "%s settled twice" % name
                settled.add(name)
            if event["op"] == "adopt":
                value = Fraction(attrs["value"])
                if best is None:
                    best = value
                elif head["config"]["sense"] == MAXIMISE:
                    best = max(best, value)
                else:
                    best = min(best, value)
    assert settled == set(depth_of), "%d nodes opened and never settled" % (
        len(set(depth_of) - settled))
    return len(depth_of), best, deepest


def random_programme(rng):
    """A small bounded maximisation, whole in every variable."""
    width = rng.randint(2, 4)
    rows = [([Fraction(rng.randint(0, 5)) for _ in range(width)], "<=",
             Fraction(rng.randint(3, 18))) for _ in range(rng.randint(1, 3))]
    # One row bounding every variable, so the box brute force walks really does
    # hold the optimum and the two are answering the same question.
    rows.append(([Fraction(1)] * width, "<=", Fraction(CEILING * width)))
    for index in range(width):
        unit = [Fraction(1) if position == index else Fraction(0) for position in range(width)]
        rows.append((unit, "<=", Fraction(CEILING)))
    objective = [Fraction(rng.randint(1, 9)) for _ in range(width)]
    return Programme(objective, rows, MAXIMISE, tuple(range(width)))


def check_against_brute_force():
    rng = random.Random(20260822)
    hardest = 0
    for _ in range(INSTANCES):
        programme = random_programme(rng)
        writer, point, value = branch_and_bound.build(programme)
        expected_point, expected = branch_and_bound.brute_force(programme, CEILING)
        assert value == expected, ("branch and bound found %s where enumeration found %s\n%s"
                                   % (value, expected, [str(x) for x in programme.objective]))
        if point is not None:
            assert programme.satisfies(point), "the point returned is outside the programme"
            assert programme.value_at(point) == value, "the point does not have the value claimed"
        event_trace.check(writer.head, writer.events)
        nodes, adopted, _ = summarise(writer.head, writer.events)
        assert adopted == expected, "the trace alone says %s, the search says %s" % (adopted, value)
        hardest = max(hardest, nodes)
    print("  %-13s %d random programmes agree with enumeration, hardest %d nodes"
          % ("brute force", INSTANCES, hardest))


def check_relaxation():
    """The vertex cover's relaxation is 5/2 and its answer is 3, which is the point of it."""
    cover = branch_and_bound.PROBLEMS["vertex_cover"]
    status, _, relaxed = solve(cover)
    assert status == OPTIMAL and relaxed == Fraction(5, 2), "the relaxation is %s" % relaxed
    _, point, value = branch_and_bound.build(cover)
    assert value == 3, "the cover costs %s" % value
    assert cover.satisfies(point)
    print("  %-13s five-cycle relaxes to 5/2 and covers at 3" % "relaxation")


def check_shipped():
    """Every shipped programme solves, and its trace replays to what it returned."""
    for name in sorted(branch_and_bound.PROBLEMS):
        programme = branch_and_bound.PROBLEMS[name]
        writer, point, value = branch_and_bound.build(programme, name=name)
        event_trace.check(writer.head, writer.events)
        nodes, adopted, deepest = summarise(writer.head, writer.events)
        assert adopted == value, "%s: the trace says %s, the search %s" % (name, adopted, value)
        assert programme.satisfies(point), "%s: the point is outside the programme" % name
        print("  %-13s %s at %s, %d nodes, depth %d"
              % (name, programme.sense, value, nodes, deepest))


def check_rejections():
    writer = event_trace.Writer("made_up", "search")
    for op in ("swap", "compare"):
        try:
            writer.emit(op, "n0")
        except ValueError:
            continue
        raise AssertionError("the array vocabulary was accepted in the search world")
    try:
        event_trace.Writer("made_up", "orbit")
    except ValueError:
        pass
    else:
        raise AssertionError("an undefined world was accepted")
    print("  %-13s a sort's verbs and an undefined world are both refused" % "worlds")


def main():
    print("integer programming")
    check_relaxation()
    check_shipped()
    check_against_brute_force()
    check_rejections()
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
