"""Merge sort, as a trace of what it did. No Blender, no geometry, no colour.

One role: sort a list and say so in events. Import `sort`, or run the file:

    python merge_sort.py --elements 16 --seed 7 --output out/merge_sort.jsonl

Every `move` carries a `depth`, which is the recursion level the element belongs to
at that moment. A renderer is free to spend that however it likes; the Blender one
spends it as distance, so how far a bar has travelled is how deep the call that owns
it. The trace itself says only which call owns it, never where to put it.
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
    """Merge sort in place, emitting the split, the comparisons and each placement."""
    order = ["a%d" % index for index in range(len(values))]
    for position, value in enumerate(values):
        writer.emit("create", order[position], index=position, value=value)

    _sort_range(values, order, 0, len(values), 0, writer)
    for name in order:
        writer.emit("mark", name, role="sorted")
    return values


def _sort_range(values, order, low, high, depth, writer):
    if high - low <= 1:
        return
    middle = (low + high) // 2
    for position in range(low, high):
        writer.emit("move", order[position], index=position, depth=depth + 1,
                    side="left" if position < middle else "right")
    _sort_range(values, order, low, middle, depth + 1, writer)
    _sort_range(values, order, middle, high, depth + 1, writer)
    _merge(values, order, low, middle, high, depth, writer)


def _merge(values, order, low, middle, high, depth, writer):
    """Interleave the two sorted halves back into `low:high`, one placement at a time."""
    left_values, left_order = values[low:middle], order[low:middle]
    right_values, right_order = values[middle:high], order[middle:high]
    left = right = 0
    for position in range(low, high):
        if left < len(left_values) and right < len(right_values):
            writer.emit("compare", [left_order[left], right_order[right]])
        take_left = right >= len(right_values) or (
            left < len(left_values) and left_values[left] <= right_values[right])
        if take_left:
            values[position], order[position] = left_values[left], left_order[left]
            left += 1
        else:
            values[position], order[position] = right_values[right], right_order[right]
            right += 1
        writer.emit("move", order[position], index=position, depth=depth)


def build(elements=16, max_height=5, seed=None):
    """Generate a run and return its writer, already holding the whole trace."""
    if seed is not None:
        random.seed(seed)
    values = [random.randint(1, max_height) for _ in range(elements)]
    writer = event_trace.Writer("merge_sort", "array", seed=seed,
                                elements=elements, max_height=max_height)
    sort(values, writer)
    return writer, values


def main(argv=None):
    parser = argparse.ArgumentParser(description="Merge sort, emitting an event trace.")
    parser.add_argument("--elements", type=int, default=16)
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
