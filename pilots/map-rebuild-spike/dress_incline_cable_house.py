"""Complete the existing sheave and service bins with cable returns and wheels.

Run Blender from the game checkout. The pinned art-store source makes reruns
idempotent; the existing body bounds, atlas pixels and collision stay unchanged.
"""
from pathlib import Path
import hashlib, json, subprocess, time
import bpy
from mathutils import Vector

ROOT=Path.cwd()
assert (ROOT/'src/world/Terrain3dClaimPilot.ts').is_file(), 'Run from the game checkout'
OUT=Path(__file__).resolve().parent
STORE=OUT.parents[1]
PACK=OUT/'landmarks/incline'
PIN='9fa06cc'
BODY='upper-ore-cable-house'
RAW=ROOT/'artifacts/sol/map-art-campaign-2/_raw/run-4'/f'incline-details-{time.time_ns()}'
RAW.mkdir(parents=True)
original=subprocess.check_output(['git','show',f'{PIN}:pilots/map-rebuild-spike/landmarks/incline/incline-landmarks.blend'],cwd=STORE)
(RAW/'input.blend').write_bytes(original)
bpy.ops.wm.open_mainfile(filepath=str(RAW/'input.blend'))
body=bpy.data.objects[BODY]
assert sum(len(p.vertices)-2 for p in body.data.polygons)==1636
original_bounds=[tuple(v) for v in body.bound_box]
material=body.data.materials[0]
parts=[]
def cylinder(name,start,end,radius,role,segments):
    a,b=Vector(start),Vector(end)
    bpy.ops.mesh.primitive_cylinder_add(vertices=segments,radius=radius,depth=(b-a).length,location=(a+b)*.5)
    obj=bpy.context.object;obj.name=name;obj.rotation_mode='QUATERNION';obj.rotation_quaternion=(b-a).to_track_quat('Z','Y')
    obj.data.materials.append(material)
    # Existing atlas roles: iron index 1, brass index 8. Preserve the sampler and painting.
    row,column=divmod(role,4)
    for loop in obj.data.uv_layers.active.data:
        loop.uv=((column+.08+loop.uv.x*.84)/4,(row+.08+loop.uv.y*.84)/4)
    parts.append(obj)
for x in (-.68,.68):cylinder('CableHouse.ReturnCable',(x,-1.43,1.1),(x,-1.43,4.65),.045,1,6)
for center in (-3.2,3.2):
    for x in (center-.68,center+.68):
        for y in (.22,2.18):
            cylinder('CableHouse.ServiceWheel',(x,y-.06,.31),(x,y+.06,.31),.28,1,12)
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
for p in parts:p.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.object.join()
assert [tuple(v) for v in body.bound_box]==original_bounds
triangles=sum(len(p.vertices)-2 for p in body.data.polygons)
assert triangles==2028 and triangles<=3000
body['detail_recipe']='dress_incline_cable_house.py'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(PACK/'incline-landmarks.blend'))
bpy.ops.export_scene.gltf(filepath=str(PACK/f'{BODY}.glb'),export_format='GLB',use_selection=True,export_apply=True,
    export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=PACK/'incline-landmark-pack-contract.json';pack=json.loads(p.read_text())
pack['blend']['sha256']=sha(PACK/'incline-landmarks.blend')
record=pack['assets'][BODY];record.update(triangles=triangles,sha256=sha(PACK/f'{BODY}.glb'))
record['detailCorrection']={'recipe':'dress_incline_cable_house.py','storeInput':PIN,'addedTriangles':392,
    'cableReturns':2,'serviceBinWheels':8,'bounds':'unchanged','atlas':'existing iron tile; pixels unchanged'}
p.write_text(json.dumps(pack,indent=2)+'\n')
(RAW/'result.json').write_text(json.dumps(record,indent=2)+'\n')
print('INCLINE_DETAILS',triangles,sha(PACK/f'{BODY}.glb'))
