# Sorting Algorithm Visualizations in Blender

3D animated visualizations of sorting algorithms using Blender's Python API. Bars of random heights and colors are sorted in real-time with keyframed animations.

## Algorithms

### Bubble Sort (`bubble_sort.py`)
- Compares adjacent bars and swaps them if out of order
- Swapping bars flash red during the exchange
- O(n^2) comparisons visualized step by step

### Merge Sort (`merge_sort.py`)
- Recursively splits bars into halves, moving each group apart in 3D space
- Merges sorted halves back together, sliding bars into their correct positions
- The recursive structure is visible as bars physically separate and rejoin

## Demos

Recorded animations are included in this folder:

- [Bubble Sort screencast](Screencast_bubble_sort.webm) (.webm)
- [Merge Sort animation](merge_sort_animation.mkv) (.mkv)

> To view: download the files and open locally, or clone the repo. GitHub does not preview these formats inline.

## Usage

1. Open Blender
2. Go to the Scripting workspace
3. Open `bubble_sort.py` or `merge_sort.py`
4. Click Run Script
5. Press Space to play the animation

## Parameters

Both scripts expose these at the bottom of the file:
- `num_elements` - Number of bars to sort (default: 16-20)
- `bar_width` - Width of each bar (default: 0.5)
- `max_height` - Maximum bar height (default: 5-20)
- `sort_speed` - Frames per swap/action (default: 10)
