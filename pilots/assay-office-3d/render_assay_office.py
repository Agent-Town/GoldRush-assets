from pathlib import Path

import bpy
from mathutils import Vector


OUT = Path(__file__).resolve().parents[3] / "artifacts/town3d-assay-office/model-review"
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).resolve().parent / "assay-office.blend"))

bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -0.015))
ground = bpy.context.object
ground.data.materials.append(bpy.data.materials.new("Review ground"))
ground.data.materials[0].diffuse_color = (0.48, 0.35, 0.20, 1)

for location, energy, size in (((-5, -6, 9), 1100, 5), ((6, 4, 5), 500, 4)):
    bpy.ops.object.light_add(type="AREA", location=location)
    bpy.context.object.data.energy = energy
    bpy.context.object.data.size = size

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
    camera.data.ortho_scale = 6.6
    bpy.context.scene.render.filepath = str(OUT / f"assay-office-{name}.png")
    bpy.ops.render.render(write_still=True)
