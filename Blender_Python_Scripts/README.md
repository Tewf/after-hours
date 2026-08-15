# Sorting algorithms animated in Blender

Bars swapping, highlighting and translating, so that each algorithm's access
pattern becomes something you watch rather than something you read.

## Bubble sort

![Bubble sort animated in Blender](sorting_algorithms/bubble_sort.webp)

The pair being compared flashes red, so the O(n²) sweep is visible as the marker
walking the row again and again, one place shorter each pass. 20 bars, 1407
frames.

## Merge sort

![Merge sort animated in Blender](sorting_algorithms/merge_sort.webp)

Halves move apart in 3D and slide back in order, so recursion depth reads as
physical distance: the further a bar has travelled, the deeper the call that
owns it. 16 bars, 801 frames.

Both were rendered headless at 1080p24 in four and two minutes. The full
resolution files are attached to the
[latest release](https://github.com/Tewf/after-hours/releases/latest).

## Running and rendering them

```sh
cd sorting_algorithms
blender --background --python bubble_sort.py -- --render --output out/bubble_sort.mp4 --seed 7
```

The flags, the Blender 5.2 details and the reason a discrete GPU needs a PRIME
prefix are in
[`sorting_algorithms/README.md`](sorting_algorithms/README.md).

| | |
|---|---|
| [`sorting_algorithms/bubble_sort.py`](sorting_algorithms/bubble_sort.py) | Builds the bars and keyframes each comparison and swap |
| [`sorting_algorithms/merge_sort.py`](sorting_algorithms/merge_sort.py) | Same, for the recursive merge |
| [`sorting_algorithms/scene_setup.py`](sorting_algorithms/scene_setup.py) | Camera, lighting, frame range and video output, shared by both |
