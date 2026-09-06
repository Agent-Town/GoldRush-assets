from pathlib import Path
import math

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts/town3d-schoolhouse/model-review"
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).resolve().parent / "schoolhouse.blend"))
schoolhouse = bpy.data.objects["SchoolhouseFullWrap"]

bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -0.015))
ground = bpy.context.object
ground.data.materials.append(bpy.data.materials.new("Review ground"))
ground.data.materials[0].diffuse_color = (0.48, 0.35, 0.20, 1)

bpy.ops.object.light_add(type="AREA", location=(-5, -6, 9))
bpy.context.object.data.energy = 1100
bpy.context.object.data.shape = "DISK"
bpy.context.object.data.size = 5
bpy.ops.object.light_add(type="AREA", location=(6, 4, 5))
bpy.context.object.data.energy = 500
bpy.context.object.data.size = 4

bpy.ops.object.camera_add()
camera = bpy.context.object
bpy.context.scene.camera = camera
bpy.context.scene.render.engine = "BLENDER_EEVEE"
bpy.context.scene.render.resolution_x = 720
bpy.context.scene.render.resolution_y = 720
bpy.context.scene.render.resolution_percentage = 100
bpy.context.scene.render.image_settings.file_format = "PNG"
bpy.context.scene.world = bpy.data.worlds.new("Review world")
bpy.context.scene.world.color = (0.16, 0.12, 0.08)

for name, location in {
    "front-left": (-7.2, -8.0, 6.1),
    "front-right": (7.2, -8.0, 6.1),
    "back-left": (-7.2, 8.0, 6.1),
    "back-right": (7.2, 8.0, 6.1),
}.items():
    camera.location = location
    camera.rotation_euler = (Vector((0, 0, 2.0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 6.8
    bpy.context.scene.render.filepath = str(OUT / f"schoolhouse-{name}.png")
    bpy.ops.render.render(write_still=True)
