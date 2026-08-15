# Sorting algorithms animated in Blender

Bubble sort and merge sort driven through Blender's Python API, with bars
swapping, highlighting and translating so that each algorithm's access pattern
becomes visible rather than described.

| | |
|---|---|
| [`sorting_algorithms/bubble_sort.py`](sorting_algorithms/bubble_sort.py) | Builds the bars and keyframes each comparison and swap |
| [`sorting_algorithms/merge_sort.py`](sorting_algorithms/merge_sort.py) | Same, for the recursive merge |
| [`sorting_algorithms/scene_setup.py`](sorting_algorithms/scene_setup.py) | Camera, lighting, frame range and video output, shared by both |

The animations and how to render them are in
[`sorting_algorithms/`](sorting_algorithms/README.md).
