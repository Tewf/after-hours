# Integer programming

A linear programme whose answer has to come out whole, solved exactly and shown
walking the tree it needed to get there.

Nothing here is a float. The relaxation is a two-phase simplex over `Fraction`
under Bland's rule, so a bound is a fact about the programme rather than about
the arithmetic, and a node is pruned because it provably cannot hold the answer.
That is slow and it is the point: `test_integer_programming.py` puts 200 random
programmes through both the tree and an enumeration of every whole point in the
box, and they have to name the same optimum. A branch and bound that prunes too
hard still returns confidently, which is exactly why it needs disagreeing with.

## The three that ship

| | | |
|---|---|---|
| `knapsack` | 44, in **9 nodes** to depth 4 | The whole vocabulary in one small tree: two `infeasible` prunes, two `bounded` ones, one adoption |
| `vertex_cover` | 3, in **3 nodes** | A five-cycle. Half a vertex each satisfies every edge at a cost of 5/2, and no cover of an odd cycle is that cheap. The gap between 5/2 and 3 is what branching exists to close |
| `assignment` | 34, in **1 node** | No tree at all. The assignment polytope's corners are already whole, so the relaxation answers and there is nothing to branch on. Here to mark the boundary: this method is not always needed |

![The knapsack tree, built one event at a time](../thumbs/branch_and_bound.webp)

```sh
python branch_and_bound.py --problem knapsack --output out/knapsack.jsonl
python draw_tree.py --problem knapsack --animate ../thumbs/branch_and_bound.webp
python test_integer_programming.py
```

The loop above is not a recording of the program. It is the trace replayed one
event per frame, so what you watch is the order the search actually did things:
a node opens, takes its relaxation's bound, and then goes grey when pruned or
gold when it turns out whole. Layout is computed from the finished tree, so
nothing shifts as nodes arrive — you are watching a search, not a diagram
rearranging itself.

## The dichotomy is Dakin's

A variable the relaxation leaves at `v` between two integers becomes `x <= ⌊v⌋`
and `x >= ⌈v⌉`, two children covering everything between them. Land and Doig,
whose paper is where branch and bound starts, branch on *equalities* and step
outward to further integers, so their tree is not binary; the two-child version
is Dakin 1965.

Which variable to split and which child to open first are the crudest possible
rules here — lowest index, `<=` first. A rule you can check by hand is worth more
in a repository like this one than a rule that finds the answer two nodes sooner.

## What it writes

The `search` world of [`event_trace.py`](../event_trace.py): a node is `open`ed,
`bound`ed by its relaxation, and then `prune`d, or it `adopt`s a whole point, or
it branches and is `close`d once its children are done. The same five verbs
describe the sorts' sibling tree searches, which is the reason they are not the
sorts' own five.

`summarise` in the test reads a trace back knowing nothing about branch and
bound: it checks the tree really is a tree, and that the best value the events
mention is the value the search returned.

## The files

| | |
|---|---|
| [`simplex.py`](simplex.py) | The relaxation: two-phase simplex, exact rationals, Bland's rule |
| [`branch_and_bound.py`](branch_and_bound.py) | The tree, the three programmes, and the trace |
| [`test_integer_programming.py`](test_integer_programming.py) | Against enumeration, 200 programmes; and the trace against itself |
