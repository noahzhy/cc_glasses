import bpy
from mathutils import Vector

scale = bpy.context.scene.unit_settings.scale_length
depsgraph = bpy.context.evaluated_depsgraph_get()
results = []

for obj in bpy.context.selected_objects:
    evaluated = obj.evaluated_get(depsgraph)
    corners = [evaluated.matrix_world @ Vector(corner)
               for corner in evaluated.bound_box]

    size = Vector((
        max(v.x for v in corners) - min(v.x for v in corners),
        max(v.y for v in corners) - min(v.y for v in corners),
        max(v.z for v in corners) - min(v.z for v in corners),
    )) * scale * 1000

    results.append(
        f"{obj.name}: "
        f"L={size.x:.2f} mm, "
        f"W={size.y:.2f} mm, "
        f"H={size.z:.2f} mm"
    )


def draw_size(self, context):
    for result in results:
        self.layout.label(text=result)


bpy.context.window_manager.popup_menu(
    draw_size,
    title="Object Dimensions",
    icon="INFO",
)
