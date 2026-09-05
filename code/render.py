#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Blender: render a top-view outline image.

Usage:
    blender scene.blend -b --python topview_outline.py -- \
        --output /tmp/top_outline.png \
        --width 2048 \
        --height 2048 \
        --margin 1.08 \
        --line-thickness 1.5

The script:
1. Finds all render-visible mesh objects.
2. Computes their world-space bounding box.
3. Creates/reuses an orthographic camera looking straight down.
4. Overrides materials with pure white emission.
5. Enables Freestyle and renders visible contours/creases as black lines.
"""

import bpy
import sys
import argparse
from mathutils import Matrix, Vector


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default="//topview_outline.png")
    parser.add_argument("--width", type=int, default=2048)
    parser.add_argument("--height", type=int, default=2048)
    parser.add_argument("--margin", type=float, default=1.08)
    parser.add_argument("--line-thickness", type=float, default=1.5)
    parser.add_argument(
        "--selected-only",
        action="store_true",
        help="Only render currently selected mesh objects."
    )
    return parser.parse_args(argv)


def get_target_objects(selected_only=False):
    selected = [
        obj for obj in bpy.context.selected_objects
        if obj.type == "MESH" and not obj.hide_render
    ]
    if selected:
        return selected

    if selected_only:
        raise RuntimeError("No selected render-visible mesh objects found.")

    objs = [
        obj for obj in bpy.context.scene.objects
        if obj.type == "MESH" and not obj.hide_render
    ]

    if not objs:
        raise RuntimeError("No render-visible mesh objects found.")
    return objs


def world_bbox(objects):
    points = []
    for obj in objects:
        matrix_world = obj.matrix_world
        for corner in obj.bound_box:
            points.append(matrix_world @ Vector(corner))

    min_x = min(p.x for p in points)
    max_x = max(p.x for p in points)
    min_y = min(p.y for p in points)
    max_y = max(p.y for p in points)
    min_z = min(p.z for p in points)
    max_z = max(p.z for p in points)

    return min_x, max_x, min_y, max_y, min_z, max_z


def create_top_camera(scene, bbox, width, height, margin):
    min_x, max_x, min_y, max_y, min_z, max_z = bbox

    cx = (min_x + max_x) * 0.5
    cy = (min_y + max_y) * 0.5

    bbox_w = max(max_x - min_x, 1e-6)
    bbox_h = max(max_y - min_y, 1e-6)
    bbox_d = max(max_z - min_z, 1e-6)

    cam_obj = scene.camera
    if cam_obj is None:
        raise RuntimeError("The scene has no camera.")

    # Blender camera looks along local -Z.
    # Put camera safely above all geometry.
    lift = max(bbox_w, bbox_h, bbox_d, 1.0) * 2.0
    cam_obj.matrix_world = Matrix.Translation((cx, cy, max_z + lift))

    cam_obj.data.type = "ORTHO"

    aspect = width / max(height, 1)

    # ortho_scale is vertical field size.
    # Ensure both X and Y extents fit the image.
    required_vertical = max(bbox_h, bbox_w / aspect)
    cam_obj.data.ortho_scale = required_vertical * margin

    # Make clipping robust for very large scenes.
    cam_obj.data.clip_start = max(lift * 1e-5, 0.001)
    cam_obj.data.clip_end = lift * 10.0 + bbox_d

    scene.camera = cam_obj
    return cam_obj


def make_white_override_material():
    mat = bpy.data.materials.get("__OUTLINE_WHITE_MATERIAL__")
    if mat is None:
        mat = bpy.data.materials.new("__OUTLINE_WHITE_MATERIAL__")

    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    emission.inputs["Strength"].default_value = 1.0
    links.new(emission.outputs["Emission"], out.inputs["Surface"])

    return mat


def setup_white_world(scene):
    scene.world.color = (1.0, 1.0, 1.0)
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
        bg.inputs["Strength"].default_value = 1.0


def setup_freestyle(scene, line_thickness=1.5):
    # Freestyle is supported by Eevee/Cycles, not Workbench.
    engines = {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    if "BLENDER_EEVEE_NEXT" in engines:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    elif "BLENDER_EEVEE" in engines:
        scene.render.engine = "BLENDER_EEVEE"
    else:
        scene.render.engine = "BLENDER_EEVEE_NEXT"

    scene.render.use_freestyle = True
    scene.render.line_thickness = line_thickness

    view_layer = bpy.context.view_layer
    fs = view_layer.freestyle_settings

    if len(fs.linesets) == 0:
        lineset = fs.linesets.new("TopViewOutline")
    else:
        lineset = fs.linesets[0]

    linestyle = lineset.linestyle
    linestyle.color = (0.0, 0.0, 0.0)
    linestyle.alpha = 1.0
    linestyle.thickness = line_thickness
    linestyle.use_dashed_line = False

    lineset.select_by_visibility = True

    # Keep the selection robust across Blender versions.
    feature_flags = {
        "select_silhouette": False,
        "select_border": False,
        "select_external_contour": True,
        "select_contour": False,
        "select_crease": False,
        "select_edge_mark": False,
        "select_material_boundary": False,
        "select_suggestive_contour": False,
        "select_ridge_valley": False,
    }

    for name, value in feature_flags.items():
        if hasattr(lineset, name):
            setattr(lineset, name, value)


def configure_render(scene, output, width, height):
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100

    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False

    # Neutral color management so white stays white and black stays black.
    vs = scene.view_settings
    if hasattr(vs, "look"):
        try:
            vs.look = "Medium High Contrast"
        except Exception:
            pass

    scene.render.filepath = bpy.path.abspath(output)


def main():
    args = parse_args()
    scene = bpy.context.scene

    objects = get_target_objects(args.selected_only)
    bbox = world_bbox(objects)

    print("[INFO] Rendering meshes:", ", ".join(obj.name for obj in objects))
    print("[INFO] Bounding box:", tuple(round(value, 4) for value in bbox))

    setup_white_world(scene)
    create_top_camera(
        scene,
        bbox,
        width=args.width,
        height=args.height,
        margin=args.margin,
    )

    white_mat = make_white_override_material()
    bpy.context.view_layer.material_override = white_mat

    setup_freestyle(
        scene,
        line_thickness=args.line_thickness,
    )

    configure_render(
        scene,
        output=args.output,
        width=args.width,
        height=args.height,
    )

    bpy.ops.render.render(write_still=True)
    print(f"[OK] Saved top-view outline to: {scene.render.filepath}")


if __name__ == "__main__":
    main()
