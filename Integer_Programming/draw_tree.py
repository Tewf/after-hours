"""A search trace as an SVG tree. The second consumer, and the one with no Blender in it.

    python draw_tree.py --problem knapsack --output ../thumbs/branch_and_bound.svg

One role: turn `open`/`bound`/`prune`/`adopt` into a picture. It knows nothing
about linear programmes; hand it any trace in the `search` world and it draws the
tree that trace describes. That is the claim the format is for, and a second
renderer is the only way to make it a claim rather than an intention.

Where a node sits is decided here and appears nowhere in a trace, for the same
reason the sorts' frame numbers do not: it is a reading of the run, not a fact
about it. The Blender renderer and this one disagree about everything visual and
agree about what happened.
"""

import argparse
import html
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import branch_and_bound  # noqa: E402
import event_trace  # noqa: E402

# Outcome to fill, taken from the site's palette so a thumbnail and the page it
# sits on are the same drawing twice rather than two drawings.
# The site's own tokens, by value, since a thumbnail cannot read a stylesheet:
# --gold, --muted, --sunken, --correction, --ink. The claim above is only true if
# these stay the site's, so an adopted node is gold in both places and not green
# in one of them.
COLOURS = {"adopt": "#9A6B00", "bounded": "#6A6D77", "infeasible": "#EFEFF3",
           "limit": "#B23A1B", "branch": "#101014"}
STEP_X, STEP_Y, RADIUS, MARGIN = 74, 84, 13, 34
BOUND_DROP = 22   # where a node's bound sits below it, and the last row's floor


def outcomes(events):
    """`{node: (its outcome, the bound it was given)}`, read from the events alone."""
    verdict, bound = {}, {}
    for event in events:
        name = event["ids"][0]
        attrs = event.get("attrs", {})
        if event["op"] == "bound":
            bound[name] = attrs["value"]
        elif event["op"] == "prune":
            verdict[name] = attrs["why"]
        elif event["op"] == "adopt":
            verdict[name] = "adopt"
    return verdict, bound


def tree(events):
    """`(children, depth, branch label)` per node, in the order they were opened."""
    children, depth, label = {}, {}, {}
    for event in events:
        if event["op"] != "open":
            continue
        name, attrs = event["ids"][0], event["attrs"]
        children.setdefault(name, [])
        depth[name] = attrs["depth"]
        label[name] = attrs["branch"]
        if attrs["parent"] is not None:
            children[attrs["parent"]].append(name)
    return children, depth, label


def place(children, root):
    """`{node: column}`, leaves in the order they were opened and parents above their span."""
    column, next_free = {}, [0]

    def walk(name):
        if not children[name]:
            column[name] = next_free[0]
            next_free[0] += 1
            return column[name]
        spans = [walk(child) for child in children[name]]
        column[name] = (spans[0] + spans[-1]) / 2
        return column[name]

    walk(root)
    return column


def draw(head, events):
    children, depth, label = tree(events)
    verdict, bound = outcomes(events)
    root = next(event["ids"][0] for event in events if event["op"] == "open")
    column = place(children, root)

    width = int((max(column.values()) + 1) * STEP_X + 2 * MARGIN)
    # Down to the last row's bound label and no further. Reserving a whole extra
    # STEP_Y below the deepest node left a band of empty picture, which a README
    # renders at whatever width it likes and so shows at whatever size it likes.
    height = int(MARGIN + 2 * RADIUS + max(depth.values()) * STEP_Y + BOUND_DROP + MARGIN)
    at = lambda name: (MARGIN + RADIUS + column[name] * STEP_X,
                       MARGIN + RADIUS + depth[name] * STEP_Y)

    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" '
             'font-family="ui-monospace, SFMono-Regular, Menlo, monospace">' % (width, height),
             '<title>%s: %d nodes, depth %d</title>'
             % (html.escape(head["algorithm"]), len(depth), max(depth.values()))]

    for name, kids in children.items():
        for child in kids:
            (x0, y0), (x1, y1) = at(name), at(child)
            # `stroke-opacity` rather than an eight-digit hex: #RRGGBBAA is CSS
            # Color 4, which browsers take and standalone SVG renderers need not,
            # and a thumbnail that loses its edges outside a browser is no use.
            parts.append('<path d="M %.1f %.1f V %.1f H %.1f V %.1f" fill="none" '
                         'stroke="#101014" stroke-opacity="0.28" stroke-width="1.5"/>'
                         % (x0, y0 + RADIUS, (y0 + y1) / 2, x1, y1 - RADIUS))
            if label[child]:
                parts.append('<text x="%.1f" y="%.1f" font-size="9.5" fill="#6A6D77" '
                             'text-anchor="middle">%s</text>'
                             % (x1, (y0 + y1) / 2 - 4, html.escape(label[child])))

    for name in depth:
        x, y = at(name)
        fill = COLOURS.get(verdict.get(name, "branch"), COLOURS["branch"])
        parts.append('<circle cx="%.1f" cy="%.1f" r="%d" fill="%s"/>' % (x, y, RADIUS, fill))
        if name in bound:
            parts.append('<text x="%.1f" y="%.1f" font-size="10" fill="#101014" '
                         'text-anchor="middle">%s</text>'
                         % (x, y + RADIUS + 13, html.escape(bound[name])))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Draw a search trace as an SVG tree.")
    parser.add_argument("--problem", choices=sorted(branch_and_bound.PROBLEMS), default="knapsack")
    parser.add_argument("--trace", default=None, help="draw this file instead of generating a run")
    parser.add_argument("--output", default=None, help="write here instead of stdout")
    args = parser.parse_args(argv)

    if args.trace:
        head, events = event_trace.read(args.trace)
    else:
        writer, _, _ = branch_and_bound.build(branch_and_bound.PROBLEMS[args.problem],
                                              name=args.problem)
        head, events = writer.head, writer.events
    event_trace.check(head, events)
    if head["world"] != "search":
        raise SystemExit("this draws the search world, not %r" % head["world"])

    picture = draw(head, events)
    if args.output:
        pathlib.Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(args.output).write_text(picture)
        print("[draw_tree] %s: %d bytes" % (args.output, len(picture)))
    else:
        sys.stdout.write(picture)
    return 0


if __name__ == "__main__":
    sys.exit(main())
