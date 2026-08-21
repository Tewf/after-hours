"""Check that each sort sorts, and that its trace says so on its own.

    python test_sorting_traces.py

One role: assert the traces, not the pictures. `replay` rebuilds the final array
from the events alone, knowing nothing about bubble sort or merge sort. If it
disagrees with the sorted input, then the animation would show a sort that did not
happen, which is the failure worth catching before a render costs four minutes.
"""

import sys

import event_trace
import bubble_sort
import merge_sort

SIZES = (0, 1, 2, 3, 8, 17, 40)


def replay(head, events):
    """Rebuild the final array from the trace alone, using no algorithm knowledge."""
    value, index = {}, {}
    for event in events:
        names, attrs = event.get("ids", []), event.get("attrs", {})
        if event["op"] == "create":
            value[names[0]], index[names[0]] = attrs["value"], attrs["index"]
        elif event["op"] == "swap":
            first, second = names
            index[first], index[second] = index[second], index[first]
        elif event["op"] == "move":
            index[names[0]] = attrs["index"]
    positions = sorted(index.values())
    assert positions == list(range(len(index))), "indices are not a permutation: %s" % positions
    return [value[name] for name in sorted(index, key=index.get)]


def check_module(module, name):
    for size in SIZES:
        writer, values = module.build(elements=size, seed=size)
        expected = sorted(values)
        assert values == expected, "%s of %d elements did not sort: %s" % (name, size, values)

        head, events = writer.head, writer.events
        event_trace.check(head, events)
        assert replay(head, events) == expected, (
            "%s trace of %d elements replays to a different array" % (name, size))
    print("  %-11s sorts and replays for sizes %s" % (name, ", ".join(str(s) for s in SIZES)))


def check_determinism(module, name):
    first, _ = module.build(elements=24, seed=11)
    second, _ = module.build(elements=24, seed=11)
    assert first.dumps() == second.dumps(), "%s is not reproducible from its seed" % name
    print("  %-11s same seed gives byte-identical trace" % name)


def check_rejections():
    writer = event_trace.Writer("made_up", "array")
    try:
        writer.emit("teleport", "a0")
    except ValueError:
        pass
    else:
        raise AssertionError("an undefined op was accepted")

    head = event_trace.header("made_up", "array")
    try:
        event_trace.check(head, [{"t": 0, "op": "swap", "ids": ["a0", "a1"]}])
    except ValueError:
        pass
    else:
        raise AssertionError("an event naming an uncreated id was accepted")
    print("  %-11s undefined op and uncreated id are both refused" % "format")


def main():
    print("sorting traces")
    check_module(bubble_sort, "bubble sort")
    check_module(merge_sort, "merge sort")
    check_determinism(bubble_sort, "bubble sort")
    check_determinism(merge_sort, "merge sort")
    check_rejections()
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
