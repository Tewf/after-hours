"""Merge sort as a Blender animation: halves split apart in 3D, then slide back merged.

Run inside Blender's Scripting workspace, or headless:

    blender --background --python merge_sort.py -- --render --output out/merge_sort.mp4
"""

import os
import sys
import random

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))
                if "__file__" in globals() else os.getcwd())
import scene_setup  # noqa: E402


def change_object_color(obj, color):
    """Apply a material of the given RGBA colour, creating one if needed."""
    if not obj.data.materials:
        mat = bpy.data.materials.new(name="Material")
        obj.data.materials.append(mat)
    else:
        mat = obj.data.materials[0]

    # No use_nodes assignment: it is a no-op since 5.0 and raises in 6.0.
    principled_bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if principled_bsdf:
        principled_bsdf.inputs["Base Color"].default_value = color
    mat.diffuse_color = color
    obj.active_material = mat


def create_bars(num_elements=16, bar_width=0.5, max_height=20, data=None):
    if data is None:
        data = [random.randint(1, max_height) for _ in range(num_elements)]

    bars = []
    for i, value in enumerate(data):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(i * bar_width * 2, 0, value / 2))
        bar = bpy.context.object
        bar.scale.x = bar_width
        bar.scale.z = value
        change_object_color(bar, (random.random(), random.random(), random.random(), 1))
        bars.append(bar)

    return bars


def move_bars(bars, vector):
    for bar in bars:
        bar.location.x += vector[0]
        bar.location.y += vector[1]
        bar.location.z += vector[2]


def update_location(bar, frame):
    bar.keyframe_insert(data_path="location", frame=frame)


def update_location_all(bars, frame):
    for bar in bars:
        update_location(bar, frame)


def get_coordinates(objects):
    return [(obj.location.x, obj.location.y, obj.location.z) for obj in objects]


def merge_sort_animation(arr, sort_speed):
    global frame_num
    if len(arr) > 1:
        mid = len(arr) // 2
        coordinates = get_coordinates(arr)
        left_half, right_half = arr[:mid], arr[mid:]

        update_location_all(arr, frame_num)
        move_bars(left_half, (-5, 5, 0))
        move_bars(right_half, (5, 5, 0))
        update_location_all(left_half, frame_num + sort_speed)
        update_location_all(right_half, frame_num + sort_speed)
        frame_num += sort_speed

        merge_sort_animation(left_half, sort_speed)
        merge_sort_animation(right_half, sort_speed)
        merge_animation(arr, coordinates, left_half, right_half, sort_speed)


def merge_animation(arr, coordinates, left_half, right_half, sort_speed):
    global frame_num
    i = j = k = 0
    merged = []
    while i < len(left_half) and j < len(right_half):
        if left_half[i].scale.z < right_half[j].scale.z:
            update_location(left_half[i], frame_num)
            left_half[i].location = coordinates[k]
            update_location(left_half[i], frame_num + sort_speed)
            merged.append(left_half[i])
            i += 1
        else:
            update_location(right_half[j], frame_num)
            right_half[j].location = coordinates[k]
            update_location(right_half[j], frame_num + sort_speed)
            merged.append(right_half[j])
            j += 1
        frame_num += sort_speed
        k += 1

    while i < len(left_half):
        update_location(left_half[i], frame_num)
        left_half[i].location = coordinates[k]
        merged.append(left_half[i])
        frame_num += sort_speed
        update_location(left_half[i], frame_num)
        i += 1
        k += 1

    while j < len(right_half):
        update_location(right_half[j], frame_num)
        right_half[j].location = coordinates[k]
        merged.append(right_half[j])
        frame_num += sort_speed
        update_location(right_half[j], frame_num)
        j += 1
        k += 1

    arr[:] = merged[:]


args = scene_setup.parse_args("out/merge_sort.mp4")
if args.seed is not None:
    random.seed(args.seed)

num_elements = args.elements or 16      # Number of elements to sort
bar_width = 0.5                         # Width of each bar
max_height = 20                         # Max height for bars
sort_speed = args.sort_speed or 10      # Frames per split and per merged element
frame_num = 1                           # Start frame for the animation

scene_setup.clear_scene()
scene_setup.use_linear_keyframes()

bars = create_bars(num_elements, bar_width, max_height)
update_location_all(bars, frame_num)
frame_num += sort_speed
merge_sort_animation(bars, sort_speed)
scene_setup.finish(bars, frame_num, args, direction=(0.0, -1.0, 0.55))
