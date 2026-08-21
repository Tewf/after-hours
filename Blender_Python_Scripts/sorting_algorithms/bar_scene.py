"""The bars as Blender objects: build them, colour them, and put them where told.

One role: everything about a bar that is geometry or material. It knows nothing
about sorting and nothing about traces. What happens when is `render_trace.py`'s
decision, and this file only carries it out.

Written for Blender 5.2. The 5.x trap handled here: assigning `use_nodes` is a
no-op since 5.0 and raises in 6.0, so a material's node tree is used directly.
"""

import random

import bpy

BAR_WIDTH = 0.5
SPACING = 2.0        # bar centres, in bar widths
DEPTH_STEP = 4.0     # how far one level of recursion pulls a bar off the row


def position(index, depth=0):
    """Where a bar sits: along x by its index, back along y by its recursion depth."""
    return (index * BAR_WIDTH * SPACING, depth * DEPTH_STEP)


def create(name, index, value, colour=None):
    """One bar, standing on the ground, as tall as the value it holds."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.0, 0.0, 0.0))
    bar = bpy.context.object
    bar.name = name
    bar.scale.x = BAR_WIDTH
    bar.scale.z = value
    place(bar, index)
    set_colour(bar, colour or (random.random(), random.random(), random.random(), 1.0))
    return bar


def place(bar, index, depth=0):
    """Move a bar to an index and a depth, keeping it standing on the ground."""
    x, y = position(index, depth)
    bar.location = (x, y, bar.scale.z / 2.0)


def swap_places(first, second):
    """Exchange two bars' positions without disturbing their heights."""
    first.location.x, second.location.x = second.location.x, first.location.x
    first.location.y, second.location.y = second.location.y, first.location.y


def set_colour(bar, colour):
    if not bar.data.materials:
        material = bpy.data.materials.new(name="bar")
        bar.data.materials.append(material)
    else:
        material = bar.data.materials[0]
    shader = material.node_tree.nodes.get("Principled BSDF")
    if shader is None:
        shader = material.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = colour
    material.diffuse_color = colour
    bar.active_material = material


def colour_of(bar):
    """Read a bar's base colour back, so a highlight can be undone exactly."""
    shader = None
    if bar.active_material:
        shader = bar.active_material.node_tree.nodes.get("Principled BSDF")
    return tuple(shader.inputs["Base Color"].default_value) if shader else None


def key_colour(bar, frame):
    bar.active_material.node_tree.nodes["Principled BSDF"].inputs["Base Color"] \
        .keyframe_insert(data_path="default_value", frame=frame)


def key_location(bar, frame):
    bar.keyframe_insert(data_path="location", frame=frame)
