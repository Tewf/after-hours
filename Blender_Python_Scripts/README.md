# Sorting algorithms animated in Blender

Bubble sort and merge sort driven through Blender's Python API, with bars
swapping, highlighting and translating so that each algorithm's access pattern
becomes visible rather than described.

| | |
|---|---|
| [`sorting_algorithms/bubble_sort.py`](sorting_algorithms/bubble_sort.py) | Builds the bars and keyframes each comparison and swap |
| [`sorting_algorithms/merge_sort.py`](sorting_algorithms/merge_sort.py) | Same, for the recursive merge |

## Recordings

- [Bubble sort](sorting_algorithms/Screencast_bubble_sort.webm) (`.webm`)
- [Merge sort](sorting_algorithms/merge_sort_animation.mkv) (`.mkv`)

## Running

Open Blender, load the script in the Scripting workspace and run it — it
generates the objects and the animation from an empty scene. Tested on Blender
4.x.
