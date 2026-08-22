"""Bubble sort, as a trace of what it did. No Blender, no geometry, no colour.

One role: sort a list and say so in events. Import `sort`, or run the file:

    python bubble_sort.py --elements 20 --seed 7 --output out/bubble_sort.jsonl

Rendering that trace is `render_trace.py`'s job. Keeping the two apart is what lets
this run under plain Python in CI, so the animation in the README can be checked
against a sort that demonstrably sorted, rather than against a video of bars moving.
"""

import argparse
import pathlib
import random
import sys

# event_trace sits at the repository root, because the sorts and the branch and
# bound both write it and neither may reach sideways into the other.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import event_trace  # noqa: E402


def sort(values, writer):
    """Bubble sort in place, emitting a compare for every look and a swap for every move.

    `order` tracks which bar currently sits at each position, so the ids in an
    event name the bars themselves rather than the slots they happen to occupy.
    """
    order = ["a%d" % index for index in range(len(values))]
    for position, value in enumerate(values):
        writer.emit("create", order[position], index=position, value=value)

    count = len(values)
    for settled in range(count):
        for position in range(count - settled - 1):
            writer.emit("compare", [order[position], order[position + 1]])
            if values[position] > values[position + 1]:
                values[position], values[position + 1] = values[position + 1], values[position]
                order[position], order[position + 1] = order[position + 1], order[position]
                writer.emit("swap", [order[position], order[position + 1]])
        writer.emit("mark", order[count - settled - 1], role="sorted")
    return values


def build(elements=20, max_height=5, seed=None):
    """Generate a run and return its writer, already holding the whole trace."""
    if seed is not None:
        random.seed(seed)
    values = [random.randint(1, max_height) for _ in range(elements)]
    writer = event_trace.Writer("bubble_sort", "array", seed=seed,
                                elements=elements, max_height=max_height)
    sort(values, writer)
    return writer, values


def main(argv=None):
    parser = argparse.ArgumentParser(description="Bubble sort, emitting an event trace.")
    parser.add_argument("--elements", type=int, default=20)
    parser.add_argument("--max-height", type=int, default=5)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--output", default=None, help="write here instead of stdout")
    args = parser.parse_args(argv)

    writer, _ = build(args.elements, args.max_height, args.seed)
    if args.output:
        writer.write(args.output)
    else:
        sys.stdout.write(writer.dumps())


if __name__ == "__main__":
    main()
