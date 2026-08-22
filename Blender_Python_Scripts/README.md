# Sorting algorithms animated in Blender

Bars swapping, highlighting and translating, so that each algorithm's access
pattern becomes something you watch rather than something you read.

## Bubble sort

![Bubble sort animated in Blender](sorting_algorithms/bubble_sort.webp)

The pair being compared flashes red, so the O(n²) sweep is visible as the marker
walking the row again and again, one place shorter each pass. 20 bars, 306 events.

## Merge sort

![Merge sort animated in Blender](sorting_algorithms/merge_sort.webp)

Halves move apart in 3D and slide back in order, so recursion depth reads as
physical distance: the further a bar has travelled, the deeper the call that
owns it. 16 bars, 206 events.

Both were rendered headless at 1080p24 in four and two minutes. The full
resolution files are attached to the
[latest release](https://github.com/Tewf/after-hours/releases/latest).

## Running and rendering them

```sh
cd sorting_algorithms
blender --background --python render_trace.py -- --algorithm bubble_sort --render --output out/bubble_sort.mp4 --seed 7
```

The flags, the Blender 5.2 details and the reason a discrete GPU needs a PRIME
prefix are in
[`sorting_algorithms/README.md`](sorting_algorithms/README.md).

| | |
|---|---|
| [`sorting_algorithms/bubble_sort.py`](sorting_algorithms/bubble_sort.py) | Bubble sort, emitting a trace of what it did. Runs without Blender |
| [`sorting_algorithms/merge_sort.py`](sorting_algorithms/merge_sort.py) | Same, for the recursive merge |
| [`sorting_algorithms/render_trace.py`](sorting_algorithms/render_trace.py) | Replays a trace as Blender keyframes. The entry point for a render |

The rest of the files, and why the trace carries no coordinates, are in that
folder's own [README](sorting_algorithms/README.md).
