from pathlib import Path
import math
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
BLEND = Path(__file__).resolve().parent / "dynamo-hall.blend"
OUT = ROOT / "artifacts/town3d-dynamo-hall/model-review"

bpy.ops.wm.open_mainfile(filepath=str(BLEND)); OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 720; scene.render.resolution_y = 560; scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"; scene.render.film_transparent = False
scene.world = bpy.data.worlds.new("ReviewWorld"); scene.world.color = (.22, .16, .09)

bpy.ops.object.camera_add(); camera = bpy.context.object; scene.camera = camera
bpy.ops.object.light_add(type="AREA", location=(-5,-6,9)); key = bpy.context.object; key.data.energy = 1050; key.data.shape = "DISK"; key.data.size = 5
bpy.ops.object.light_add(type="AREA", location=(5,3,6)); fill = bpy.context.object; fill.data.energy = 480; fill.data.size = 4
bpy.ops.mesh.primitive_plane_add(size=30, location=(0,0,-.015)); ground = bpy.context.object
mat = bpy.data.materials.new("ReviewGround"); mat.diffuse_color=(.46,.29,.10,1); mat.roughness=1; ground.data.materials.append(mat)

def point_at(obj, target=(0,0,1.7)):
    obj.rotation_euler = ((Vector(target) - obj.location).to_track_quat('-Z','Y')).to_euler()

for name, location in {
    "front-left": (-7,-8,5.8), "front-right": (7,-8,5.8),
    "back-left": (-7,8,5.8), "back-right": (7,8,5.8),
}.items():
    camera.location = location; point_at(camera)
    scene.render.filepath = str(OUT / f"dynamo-hall-{name}.png")
    bpy.ops.render.render(write_still=True)
