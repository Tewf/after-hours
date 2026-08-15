"""Bubble sort as a Blender animation: bars swap, and the pair being compared flashes red.

Run inside Blender's Scripting workspace, or headless:

    blender --background --python bubble_sort.py -- --render --output out/bubble_sort.mp4
"""

import os
import sys
import random

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))
                if "__file__" in globals() else os.getcwd())
import scene_setup  # noqa: E402


def change_object_color(obj, color=(1, 1, 1, 1)):
    """Apply a material of the given RGBA colour, creating one if needed."""
    if not obj.data.materials:
        mat = bpy.data.materials.new(name="Material")
        obj.data.materials.append(mat)
    else:
        mat = obj.data.materials[0]

    # No use_nodes assignment: it is a no-op since 5.0 and raises in 6.0.
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = mat.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")

    bsdf.inputs["Base Color"].default_value = color
    mat.diffuse_color = color
    obj.active_material = mat


def get_object_color(obj):
    """Read back the base colour, so a highlighted bar can be restored."""
    if obj.active_material:
        bsdf = obj.active_material.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            return tuple(bsdf.inputs["Base Color"].default_value)
    return None


def key_color(bar, frame):
    bar.active_material.node_tree.nodes["Principled BSDF"].inputs["Base Color"] \
        .keyframe_insert(data_path="default_value", frame=frame)


def create_bars(num_elements=20, bar_width=0.5, max_height=5):
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


def bubble_sort_animation(bars, sort_speed):
    global frame_num
    half_swap = sort_speed // 2  # integer: fractional frames never render
    n = len(bars)
    for i in range(n):
        for j in range(n - i - 1):
            bar1, bar2 = bars[j], bars[j + 1]

            if bar1.scale.z > bar2.scale.z:
                bar1.keyframe_insert(data_path="location", frame=frame_num)
                bar2.keyframe_insert(data_path="location", frame=frame_num)

                original_color1 = get_object_color(bar1)
                original_color2 = get_object_color(bar2)
                change_object_color(bar1, original_color1)
                change_object_color(bar2, original_color2)
                key_color(bar1, frame_num)
                key_color(bar2, frame_num)

                frame_num += 1
                change_object_color(bar1, color=(1, 0, 0, 1))
                change_object_color(bar2, color=(1, 0, 0, 1))
                key_color(bar1, frame_num)
                key_color(bar2, frame_num)

                frame_num += half_swap
                bar1.location.x, bar2.location.x = bar2.location.x, bar1.location.x
                bar1.keyframe_insert(data_path="location", frame=frame_num)
                bar2.keyframe_insert(data_path="location", frame=frame_num)

                change_object_color(bar1, color=original_color1)
                change_object_color(bar2, color=original_color2)
                key_color(bar1, frame_num)
                key_color(bar2, frame_num)

                bars[j], bars[j + 1] = bars[j + 1], bars[j]

            frame_num += half_swap


args = scene_setup.parse_args("out/bubble_sort.mp4")
if args.seed is not None:
    random.seed(args.seed)

num_elements = args.elements or 20     # Number of elements to sort
bar_width = 0.5                        # Width of each bar
max_height = 5                         # Max height for bars
sort_speed = args.sort_speed or 10     # Frames per swap
frame_num = 1                          # Start frame for the animation

scene_setup.clear_scene()
scene_setup.use_linear_keyframes()

bars = create_bars(num_elements, bar_width, max_height)
for bar in bars:
    bar.keyframe_insert(data_path="location", frame=frame_num)
    key_color(bar, frame_num)

bubble_sort_animation(bars, sort_speed)
scene_setup.finish(bars, frame_num, args, direction=(0.0, -1.0, 0.22))
