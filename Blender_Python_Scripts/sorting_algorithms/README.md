# Sorting algorithm visualisations in Blender

Bars of random height and colour, sorted by keyframed animation so the
algorithm's access pattern is something you watch rather than read.

**The algorithm and the picture are separate programs.** A sort runs under plain
Python and emits a *trace*: a line per thing it did, in the vocabulary of sorting
rather than of geometry. A renderer replays that trace as keyframes. That split is
what lets CI check the sort actually sorted, which a video cannot show you, and it
means a second renderer could tell the same run differently without touching either
algorithm.

## Bubble sort

![Bubble sort animated in Blender](bubble_sort.webp)

Compares adjacent bars and swaps them when they are out of order. The pair being
compared flashes red, so the O(n²) sweep is visible as the red marker walking
the row again and again, one place shorter each pass. 20 bars, 306 events.

## Merge sort

![Merge sort animated in Blender](merge_sort.webp)

Recursively splits the row into halves that move apart in 3D, then slides them
back together in order. The recursion depth is legible as physical distance: the
further a bar has travelled, the deeper the call that owns it. 16 bars, 206 events.

Both previews are sped up and cut to 640 px. Full 1080p renders are attached to
the [latest release](https://github.com/Tewf/after-hours/releases/latest).

**The committed clips predate this split** and were rendered at the old timing,
1407 and 801 frames. The same runs now key out to 1161 and 841 frames, because
timing moved into the renderer where it belongs. The clips are replaced at the next
render; nothing about which bars move, or when, has changed.

## Running them

A trace needs no Blender at all:

```sh
python bubble_sort.py --elements 20 --seed 7 --output out/bubble_sort.jsonl
python test_sorting_traces.py
```

Rendering replays one, either from a file or generated on the spot:

```sh
blender --background --python render_trace.py -- --trace out/bubble_sort.jsonl --render
blender --background --python render_trace.py -- --algorithm merge_sort --seed 7 --render
```

On a machine with a discrete GPU behind PRIME, prefix the Blender lines with
`__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia`. Blender takes
its GL context from the integrated GPU otherwise, which here is the difference
between four minutes and several hours.

Tested on Blender 5.2.0 LTS. Leave `--render` off to build the scene and stop,
which is what you want in the GUI.

| Flag | Default | |
|---|---|---|
| `--algorithm` | `bubble_sort` | Which sort to generate, when no `--trace` is given |
| `--trace` | none | Replay this file instead of generating a run |
| `--elements` | 20 bubble, 16 merge | Number of bars |
| `--compare-frames` | 2 | Frames a comparison holds, each way |
| `--move-frames` | 5 | Frames a swap or a placement takes |
| `--resolution` | `1920x1080` | |
| `--fps` | 24 | |
| `--seed` | random | Fixes the shuffle, so a run is reproducible |
| `--render` | off | Render, rather than only building the scene |

## The files

| | |
|---|---|
| [`event_trace.py`](../../event_trace.py) | The format: write, read and check a trace, and why it holds no coordinates. At the repository root, because [the branch and bound](../../Integer_Programming/) writes it too |
| [`bubble_sort.py`](bubble_sort.py) | Bubble sort, emitting a trace. No Blender |
| [`merge_sort.py`](merge_sort.py) | Merge sort, emitting a trace. No Blender |
| [`bar_scene.py`](bar_scene.py) | A bar as a Blender object: geometry and material |
| [`render_trace.py`](render_trace.py) | Replays a trace as keyframes, and decides the timing |
| [`scene_setup.py`](scene_setup.py) | Camera, lighting, frame range and video output |
| [`test_sorting_traces.py`](test_sorting_traces.py) | Each sort sorts, and its trace replays to the same array |

Note that the renderer clears the scene first, including the default camera and
light. `scene_setup.py` puts a camera and a key light back, framed on the whole
animation rather than on the opening layout, which matters for merge sort
because its halves travel a long way off the starting row.
