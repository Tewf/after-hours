"""Replay an event trace as a Blender animation.

    blender --background --python render_trace.py -- --algorithm bubble_sort --seed 7 --render
    blender --background --python render_trace.py -- --trace out/bubble_sort.jsonl --render

One role: decide *when* things happen, and hand the finished scene to scene_setup.
This is the only file here that knows about traces and about Blender at once, which
is the whole point of the split: the algorithms stay runnable under plain Python and
testable in CI, and the trace format stays free of geometry.

The timing lives here rather than in the trace because it is a reading of the run,
not a fact about it. A compare that flashes for two frames and one that flashes for
ten are the same comparison.
"""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))
                if "__file__" in globals() else os.getcwd())
import event_trace     # noqa: E402
import bar_scene       # noqa: E402
import scene_setup     # noqa: E402
import bubble_sort     # noqa: E402
import merge_sort      # noqa: E402

ALGORITHMS = {"bubble_sort": bubble_sort, "merge_sort": merge_sort}
COMPARING = (1.0, 0.0, 0.0, 1.0)
SORTED = (0.15, 0.8, 0.3, 1.0)


def add_arguments(parser):
    parser.add_argument("--algorithm", choices=sorted(ALGORITHMS), default="bubble_sort")
    parser.add_argument("--trace", default=None, help="replay this trace instead of generating one")
    parser.add_argument("--elements", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--compare-frames", type=int, default=2)
    parser.add_argument("--move-frames", type=int, default=5)


def load(args):
    """The trace to replay, either read from a file or generated on the spot."""
    if args.trace:
        head, events = event_trace.read(args.trace)
        event_trace.check(head, events)
        return head, events
    module = ALGORITHMS[args.algorithm]
    kwargs = {"seed": args.seed}
    if args.elements is not None:
        kwargs["elements"] = args.elements
    writer, _ = module.build(**kwargs)
    return writer.head, writer.events


def replay(events, args):
    """Turn events into keyframes. Returns the bars and the last frame used."""
    bars, base = {}, {}
    frame = 1
    for event in events:
        names = event.get("ids", [])
        attrs = event.get("attrs", {})
        operation = event["op"]

        if operation == "create":
            bar = bar_scene.create(names[0], attrs["index"], attrs["value"])
            bars[names[0]] = bar
            base[names[0]] = bar_scene.colour_of(bar)
            bar_scene.key_location(bar, frame)
            bar_scene.key_colour(bar, frame)
        elif operation == "compare":
            frame = flash([bars[name] for name in names], [base[name] for name in names],
                          frame, args.compare_frames)
        elif operation == "swap":
            first, second = (bars[name] for name in names)
            bar_scene.key_location(first, frame)
            bar_scene.key_location(second, frame)
            frame += args.move_frames
            bar_scene.swap_places(first, second)
            bar_scene.key_location(first, frame)
            bar_scene.key_location(second, frame)
        elif operation == "move":
            bar = bars[names[0]]
            bar_scene.key_location(bar, frame)
            frame += args.move_frames
            bar_scene.place(bar, attrs["index"], attrs.get("depth", 0))
            bar_scene.key_location(bar, frame)
        elif operation == "mark":
            bar = bars[names[0]]
            bar_scene.key_colour(bar, frame)
            frame += 1
            base[names[0]] = SORTED
            bar_scene.set_colour(bar, SORTED)
            bar_scene.key_colour(bar, frame)
    return list(bars.values()), frame


def flash(pair, originals, frame, hold):
    """Hold, turn red, hold, turn back: one comparison, seen."""
    for bar in pair:
        bar_scene.key_colour(bar, frame)
    frame += hold
    for bar in pair:
        bar_scene.set_colour(bar, COMPARING)
        bar_scene.key_colour(bar, frame)
    frame += hold
    for bar, colour in zip(pair, originals):
        bar_scene.set_colour(bar, colour)
        bar_scene.key_colour(bar, frame)
    return frame


def main():
    args = scene_setup.parse_args("out/animation.mp4", add_arguments)
    head, events = load(args)
    if args.output == "out/animation.mp4":
        args.output = "out/%s.mp4" % head["algorithm"]

    scene_setup.clear_scene()
    scene_setup.use_linear_keyframes()
    bars, last_frame = replay(events, args)
    print("[render_trace] %s, seed %s: %d events over %d frames"
          % (head["algorithm"], head.get("seed"), len(events), last_frame))
    direction = (0.0, -1.0, 0.22) if head["algorithm"] == "bubble_sort" else (0.0, -1.0, 0.55)
    scene_setup.finish(bars, last_frame, args, direction=direction)


main()
