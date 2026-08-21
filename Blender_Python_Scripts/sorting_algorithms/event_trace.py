"""The event trace format: what an algorithm says it did, with no geometry in it.

One role: write, read and check a trace. A trace is JSON Lines. The first line is a
header naming the algorithm and the configuration it ran under; every later line is
one event, stamped with the step that produced it.

**The rule that keeps the format honest: verbs are semantic, never geometric.**
No x, no colour, no frame number appears anywhere in a trace. Where a bar sits and
how long a swap takes are the renderer's decisions, and two renderers may disagree
about them while replaying the same run. Put a coordinate in here and this stops
being a trace: it becomes a scene graph wearing a trace's clothes.

Named `event_trace` and not `trace` because `trace` is a standard library module,
and shadowing it once already left a test suite passing only by accident of the
working directory it happened to run in.
"""

import json

SCHEMA = "trace/1"
# Every verb the format allows. A renderer may ignore one it has no picture for,
# but it must never meet one that is not here.
OPS = ("create", "compare", "swap", "move", "mark")


def header(algorithm, world, seed=None, **config):
    """The first line of a trace: what ran, on what, under which settings."""
    return {"schema": SCHEMA, "algorithm": algorithm, "world": world,
            "seed": seed, "config": config}


class Writer:
    """Collects events in order, numbering each with the step that produced it."""

    def __init__(self, algorithm, world, seed=None, **config):
        self.head = header(algorithm, world, seed, **config)
        self.events = []

    def emit(self, op, ids=None, **attrs):
        if op not in OPS:
            raise ValueError("unknown op %r, expected one of: %s" % (op, ", ".join(OPS)))
        event = {"t": len(self.events), "op": op}
        if ids is not None:
            event["ids"] = list(ids) if isinstance(ids, (list, tuple)) else [ids]
        if attrs:
            event["attrs"] = attrs
        self.events.append(event)
        return event

    def dumps(self):
        return "".join(json.dumps(line) + "\n" for line in [self.head] + self.events)

    def write(self, path):
        with open(path, "w") as handle:
            handle.write(self.dumps())


def read(path):
    """Return the header and the events, in the order they were written."""
    with open(path) as handle:
        lines = [json.loads(line) for line in handle if line.strip()]
    if not lines:
        raise ValueError("%s holds no trace" % path)
    return lines[0], lines[1:]


def check(head, events):
    """Raise unless the trace is internally consistent; return the event count.

    It catches the two mistakes that actually happen: an op the format does not
    define, and an event naming an id that was never created.
    """
    if head.get("schema") != SCHEMA:
        raise ValueError("expected schema %r, found %r" % (SCHEMA, head.get("schema")))
    live = set()
    for event in events:
        if event["op"] not in OPS:
            raise ValueError("event %d: unknown op %r" % (event["t"], event["op"]))
        if event["op"] == "create":
            live.update(event.get("ids", []))
            continue
        unknown = [name for name in event.get("ids", []) if name not in live]
        if unknown:
            raise ValueError("event %d: %s never created" % (event["t"], ", ".join(unknown)))
    return len(events)
