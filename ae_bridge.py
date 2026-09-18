bl_info = {
    "name": "AE2Blender Bridge", "author": "AE2Blender", "version": (1, 1, 0),
    "blender": (3, 0, 0), "location": "View3D > Sidebar > AE2Blender",
    "description": "Import cameras, nulls, and solids exported from After Effects", "category": "Import-Export",
}

import bpy
import json
from math import radians, pi, atan
from mathutils import Matrix, Euler, Vector
from bpy.props import FloatProperty
from bpy_extras.io_utils import ImportHelper

# AE: X right, Y down, Z depth. Blender: X right, Y depth, Z up.
AE_TO_BLENDER = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))
CAMERA_CORRECTION = Matrix.Rotation(pi / 2, 3, 'X')


def solid_mesh(name, width, height, anchor, unit):
    ax, ay = anchor[0], anchor[1]
    l, r = -ax * unit, (width - ax) * unit
    t, b = -ay * unit, (height - ay) * unit
    mesh = bpy.data.meshes.new(name + "_Mesh")
    # Bake the AE-to-Blender plane-axis conversion into the vertices.
    mesh.from_pydata([(l, 0, -t), (r, 0, -t), (r, 0, -b), (l, 0, -b)], [], [(0, 1, 2, 3)])
    mesh.update()
    return mesh


def insert_animation(target, layer, scene, unit, rotation_correction=None):
    previous_quaternion = None
    for sample in layer.get("samples", []):
        frame = int(sample["frame"])
        scene.frame_set(frame)
        target.location = AE_TO_BLENDER @ (Vector(sample["position"]) * unit)
        rx, ry, rz = (radians(v) for v in sample.get("rotation", [0, 0, 0]))
        ox, oy, oz = (radians(v) for v in sample.get("orientation", [0, 0, 0]))
        # Use the reference AE2Blender operation order exactly. Matrix.rotate()
        # is intentionally used instead of an equivalent-looking Euler swap.
        ae_rot = Matrix.Identity(3)
        if rotation_correction is not None:
            ae_rot.rotate(Euler((pi / 2, 0, 0)))
        ae_rot.rotate(Euler((ox, oz, -oy), 'YZX'))
        ae_rot.rotate(Euler((rx, rz, -ry), 'YZX'))
        if rotation_correction is not None:
            target.rotation_mode = 'QUATERNION'
            quaternion = ae_rot.to_quaternion()
            if previous_quaternion is not None:
                quaternion.make_compatible(previous_quaternion)
            target.rotation_quaternion = quaternion
            previous_quaternion = quaternion.copy()
        else:
            target.rotation_mode = 'XYZ'
            target.rotation_euler = ae_rot.to_euler('XYZ')
        scale = sample.get("scale", [100, 100, 100])
        target.scale = (scale[0] / 100, scale[2] / 100, scale[1] / 100)
        target.keyframe_insert(data_path="location", frame=frame)
        target.keyframe_insert(data_path="rotation_quaternion" if rotation_correction is not None else "rotation_euler", frame=frame)
        target.keyframe_insert(data_path="scale", frame=frame)


class AE2B_OT_import(bpy.types.Operator, ImportHelper):
    bl_idname = "ae2blender.import_json"
    bl_label = "Import AE2Blender JSON"
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'})
    unit_scale: FloatProperty(name="AE pixels to Blender units", default=0.01, min=0.000001)

    def execute(self, context):
        try:
            with open(self.filepath, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError) as error:
            self.report({'ERROR'}, "Could not read file: " + str(error))
            return {'CANCELLED'}
        if data.get("format") != "AE2Blender" or not isinstance(data.get("layers"), list):
            self.report({'ERROR'}, "This is not an AE2Blender JSON export")
            return {'CANCELLED'}

        scene = context.scene
        scene.render.fps = round(float(data.get("frameRate", scene.render.fps)))
        scene.frame_start = int(data.get("frameStart", scene.frame_start))
        scene.frame_end = int(data.get("frameEnd", scene.frame_end))
        collection = bpy.data.collections.new("AE2Blender Import")
        scene.collection.children.link(collection)
        transforms = {}

        # The actual camera, empty, or solid is the animated object. This keeps
        # it visible and immediately usable in the Outliner.
        for layer in data["layers"]:
            ident = str(layer.get("id"))
            name = layer.get("name") or "AE Layer " + ident
            kind = layer.get("type", "null")
            if kind == "camera":
                    cam_data = bpy.data.cameras.new(name)
                    root = bpy.data.objects.new(name, cam_data)
                    collection.objects.link(root)
                    zoom = max(0.001, float(layer.get("zoom", 1000)))
                    comp_width = max(1.0, float(data.get("width", 1920)))
                    # AE zoom is a pixel focal length; Blender's angle_x is
                    # the matching horizontal field of view.
                    cam_data.angle_x = 2.0 * atan(comp_width / (2.0 * zoom))
                    scene.camera = root
                    # AE two-node cameras use Point of Interest instead of an
                    # explicit orientation. A hidden target reproduces that aim.
                    if any(sample.get("pointOfInterest") is not None for sample in layer.get("samples", [])):
                        target = bpy.data.objects.new(name + "_AE_Target", None)
                        target.empty_display_type, target.hide_render = 'SPHERE', True
                        collection.objects.link(target)
                        for sample in layer.get("samples", []):
                            if sample.get("pointOfInterest") is not None:
                                target.location = AE_TO_BLENDER @ (Vector(sample["pointOfInterest"]) * self.unit_scale)
                                target.keyframe_insert(data_path="location", frame=int(sample["frame"]))
                        constraint = root.constraints.new('TRACK_TO')
                        constraint.target, constraint.track_axis, constraint.up_axis = target, 'TRACK_NEGATIVE_Z', 'UP_Y'
            elif kind == "solid":
                mesh = solid_mesh(name, float(layer.get("width", 100)), float(layer.get("height", 100)), layer.get("anchor", [0, 0]), self.unit_scale)
                root = bpy.data.objects.new(name, mesh)
                collection.objects.link(root)
                color = layer.get("color")
                if color and len(color) >= 3:
                    material = bpy.data.materials.new(name + "_Material")
                    material.diffuse_color = (color[0] / 255, color[1] / 255, color[2] / 255, 1)
                    mesh.materials.append(material)
            else:
                root = bpy.data.objects.new(name, None)
                root.empty_display_type, root.empty_display_size = 'PLAIN_AXES', 0.4
                collection.objects.link(root)
            transforms[ident] = root

        for layer in data["layers"]:
            root = transforms[str(layer.get("id"))]
            parent_id = layer.get("parentId")
            if parent_id is not None and str(parent_id) in transforms:
                root.parent = transforms[str(parent_id)]
            correction = CAMERA_CORRECTION if layer.get("type") == "camera" else None
            insert_animation(root, layer, scene, self.unit_scale, correction)
        scene.frame_set(scene.frame_start)
        self.report({'INFO'}, "Imported {} AE layers".format(len(data["layers"])))
        return {'FINISHED'}


class AE2B_PT_panel(bpy.types.Panel):
    bl_label, bl_idname = "AE2Blender", "AE2B_PT_panel"
    bl_space_type, bl_region_type, bl_category = 'VIEW_3D', 'UI', "AE2Blender"
    def draw(self, context): self.layout.operator(AE2B_OT_import.bl_idname, icon='IMPORT')


classes = (AE2B_OT_import, AE2B_PT_panel)
def register():
    for cls in classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
if __name__ == "__main__": register()
