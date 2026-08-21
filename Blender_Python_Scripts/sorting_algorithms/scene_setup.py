"""Turn a bare sorting animation into something Blender can actually render.

The two sort scripts only create bars and insert keyframes. They delete the
default camera and light on their first line, never set a frame range, and never
choose an engine, so pressing Render Animation captures 250 frames of a black
screen. This module supplies the missing half: linear keyframes, a camera framed
on the whole animation, lighting, and video output settings.

Written for Blender 5.2. Two 5.x traps are handled here rather than in the
callers: `Action.fcurves` no longer exists (slotted actions), so keyframe
interpolation has to be chosen *before* insertion; and `file_format = "FFMPEG"`
raises unless `media_type = "VIDEO"` is set first.
"""

import os
import sys
import argparse
import math

import bpy
from mathutils import Vector

EEVEE = "BLENDER_EEVEE"  # 'BLENDER_EEVEE_NEXT' was a 4.2 to 4.5 only spelling


def parse_args(default_output, add_arguments=None):
    """Read the arguments Blender passes after a bare `--`.

    Only the scene's own arguments live here. Anything about which algorithm ran,
    or how fast, belongs to the caller, which passes `add_arguments` to add them.
    """
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true",
                        help="render the animation instead of only building it")
    parser.add_argument("--output", default=default_output)
    parser.add_argument("--resolution", default="1920x1080")
    parser.add_argument("--fps", type=int, default=24)
    if add_arguments is not None:
        add_arguments(parser)
    return parser.parse_args(argv)


def clear_scene():
    """Empty the scene, including the default camera and light."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def use_linear_keyframes():
    """Insert keyframes without Bezier easing.

    Must run before the first keyframe_insert: 5.x removed Action.fcurves, so
    interpolation cannot be corrected afterwards. Ease-in-out on every swap
    misrepresents a sorting step as a gesture rather than a discrete move.
    """
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"


def animation_bounds(objects, frame_start, frame_end, step=5):
    """Bounding box of every object over the whole animation.

    Sampled by stepping the timeline rather than read from fcurves, which 5.x
    no longer exposes. Merge sort throws its halves far off the starting row,
    so framing on the initial layout alone would crop most of the animation.
    """
    scene = bpy.context.scene
    low = Vector((float("inf"),) * 3)
    high = Vector((float("-inf"),) * 3)
    for frame in range(int(frame_start), int(frame_end) + 1, step):
        scene.frame_set(frame)
        for obj in objects:
            for corner in obj.bound_box:
                world = obj.matrix_world @ Vector(corner)
                low = Vector(map(min, low, world))
                high = Vector(map(max, high, world))
    scene.frame_set(int(frame_start))
    return low, high


def add_camera(low, high, direction=(0.0, -1.0, 0.30), fov_deg=40.0, margin=1.30):
    """Place a camera far enough back to hold the whole bounding box."""
    center = (low + high) / 2.0
    radius = (high - low).length / 2.0
    offset = Vector(direction).normalized()
    distance = margin * radius / math.sin(math.radians(fov_deg) / 2.0)

    bpy.ops.object.camera_add(location=center + offset * distance)
    camera = bpy.context.object
    camera.data.angle = math.radians(fov_deg)
    camera.rotation_euler = (-offset).to_track_quat("-Z", "Y").to_euler()
    camera.data.clip_end = max(1000.0, distance * 3.0)
    bpy.context.scene.camera = camera
    return camera


def add_lighting(low, high, sun_energy=4.0, ambient=0.35):
    """A key sun plus flat world ambient, so no bar reads as black."""
    center = (low + high) / 2.0
    height = (high - low).length
    bpy.ops.object.light_add(type="SUN", location=center + Vector((0.0, -height, height)))
    sun = bpy.context.object
    sun.data.energy = sun_energy
    sun.rotation_euler = (math.radians(55.0), 0.0, math.radians(30.0))

    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background is not None:
        background.inputs["Color"].default_value = (0.05, 0.06, 0.08, 1.0)
        background.inputs["Strength"].default_value = ambient
    return sun


def configure_render(frame_end, resolution="1920x1080", fps=24, frame_start=1):
    """Engine, resolution, fps and the frame range the animation really needs.

    Blender's stock frame_end is 250. Bubble sort runs past 1400 frames, so
    without this the render stops around 18% of the way through the algorithm.
    """
    scene = bpy.context.scene
    width, _, height = resolution.partition("x")
    scene.render.engine = EEVEE
    scene.render.resolution_x = int(width)
    scene.render.resolution_y = int(height)
    scene.render.resolution_percentage = 100
    scene.render.fps = fps
    scene.frame_start = int(frame_start)
    scene.frame_end = int(math.ceil(frame_end))
    return scene


def render_animation(output_path):
    """Write the animation to a single H.264 file."""
    scene = bpy.context.scene
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    scene.render.filepath = output_path
    # Without this Blender appends the frame range, giving bubble_sort.mp40001-1420.mp4
    scene.render.use_file_extension = False
    # 5.x gates the container on media_type; setting FFMPEG first raises.
    scene.render.image_settings.media_type = "VIDEO"
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    scene.render.ffmpeg.audio_codec = "NONE"
    print(f"[scene_setup] rendering frames "
          f"{scene.frame_start}-{scene.frame_end} to {output_path}")
    bpy.ops.render.render(animation=True)


def finish(bars, frame_end, args, direction=(0.0, -1.0, 0.30)):
    """Frame, light, configure, and render if asked. Called once per script."""
    scene = configure_render(frame_end, args.resolution, args.fps)
    low, high = animation_bounds(bars, scene.frame_start, scene.frame_end)
    camera = add_camera(low, high, direction=direction)
    add_lighting(low, high)
    print(f"[scene_setup] {len(bars)} bars, frames {scene.frame_start}-{scene.frame_end} "
          f"({(scene.frame_end - scene.frame_start + 1) / scene.render.fps:.1f}s "
          f"at {scene.render.fps} fps), {scene.render.resolution_x}x{scene.render.resolution_y}, "
          f"engine {scene.render.engine}")
    print(f"[scene_setup] bounds {tuple(round(v, 1) for v in low)} to "
          f"{tuple(round(v, 1) for v in high)}, camera at "
          f"{tuple(round(v, 1) for v in camera.location)}")
    if args.render:
        render_animation(args.output)
