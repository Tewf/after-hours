"""The event trace format: what a program says it did, with no geometry in it.

One role: write, read and check a trace. A trace is JSON Lines. The first line is a
header naming the algorithm, the *world* whose vocabulary it speaks, and the
configuration it ran under; every later line is one event, stamped with the step
that produced it.

**The rule that keeps the format honest: verbs are semantic, never geometric.**
No x, no colour, no frame number appears anywhere in a trace. Where a bar sits and
how long a swap takes are the renderer's decisions, and two renderers may disagree
about them while replaying the same run. Put a coordinate in here and this stops
being a trace: it becomes a scene graph wearing a trace's clothes.

**A world is a vocabulary, and there are two.** `array` is a row of values being
put in order. `search` is a tree being walked: a node is opened, bounded, and then
either pruned or descended from, and something is adopted when the walk finds it.
The two share no verbs and are not meant to. A world is here so that a second kind
of program can be traced without the sorts' vocabulary spreading to cover a thing
it does not describe, and so that a renderer meeting an unknown verb is a bug
rather than a shrug.

Every world names the one verb that introduces an identifier, because the check
worth having is the same in both: nothing may be spoken about before it exists.
A bar is `create`d before it is swapped; a node is `open`ed before it is closed.

Named `event_trace` and not `trace` because `trace` is a standard library module,
and shadowing it once already left a test suite passing only by accident of the
working directory it happened to run in.

It sits at the root of the repository rather than beside any one of its writers,
because the sorts and the branch and bound are siblings, and a sibling reaching
sideways into another is the import this layout exists to prevent.
"""

import json

SCHEMA = "trace/1"

# world -> (the verb that introduces an identifier, every verb the world allows).
# A renderer may ignore a verb it has no picture for, but it must never meet one
# that is not listed here for the world the header declares.
WORLDS = {
    "array": ("create", ("create", "compare", "swap", "move", "mark")),
    "search": ("open", ("open", "bound", "prune", "adopt", "close")),
}


def vocabulary(world):
    """(the introducing verb, the allowed verbs) for a world, or a refusal."""
    if world not in WORLDS:
        raise ValueError("unknown world %r, expected one of: %s"
                         % (world, ", ".join(sorted(WORLDS))))
    return WORLDS[world]


def header(algorithm, world, seed=None, **config):
    """The first line of a trace: what ran, in whose vocabulary, under which settings."""
    vocabulary(world)
    return {"schema": SCHEMA, "algorithm": algorithm, "world": world,
            "seed": seed, "config": config}


class Writer:
    """Collects events in order, numbering each with the step that produced it."""

    def __init__(self, algorithm, world, seed=None, **config):
        self.head = header(algorithm, world, seed, **config)
        self.world = world
        self.ops = vocabulary(world)[1]
        self.events = []

    def emit(self, op, ids=None, **attrs):
        if op not in self.ops:
            raise ValueError("unknown op %r in world %r, expected one of: %s"
                             % (op, self.world, ", ".join(self.ops)))
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

    It catches the three mistakes that actually happen: a world nothing defines,
    an op the world does not define, and an event naming an id that was never
    introduced.
    """
    if head.get("schema") != SCHEMA:
        raise ValueError("expected schema %r, found %r" % (SCHEMA, head.get("schema")))
    introduces, ops = vocabulary(head.get("world"))
    live = set()
    for event in events:
        if event["op"] not in ops:
            raise ValueError("event %d: unknown op %r in world %r"
                             % (event["t"], event["op"], head["world"]))
        if event["op"] == introduces:
            live.update(event.get("ids", []))
            continue
        unknown = [name for name in event.get("ids", []) if name not in live]
        if unknown:
            raise ValueError("event %d: %s never %sed"
                             % (event["t"], ", ".join(unknown), introduces))
    return len(events)
