"""Add a geared lock wheel within the existing Dome Basin canal-work envelope.
Run with Blender --background --python this.py -- --source <base blend> --out <dir>.
All five mounts and original geometry are retained. No raster is generated.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--out',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path(a.source).resolve()))
rig=bpy.data.objects['canal-gate-works'];material=rig.data.materials[0]
original_bounds=([min(v.co[i] for v in rig.data.vertices) for i in range(3)],[max(v.co[i] for v in rig.data.vertices) for i in range(3)])
parts=[rig];roles={'iron':1,'stone':2,'brass':8,'teal':4,'soot':9}
# The inherited black slab and orange approach sheets receive the same dry stone
# cell. Preserve their UV detail and geometry; change only the atlas region.
uv=rig.data.uv_layers.active
for poly in rig.data.polygons:
 if max(rig.data.vertices[i].co.z for i in poly.vertices)<=.231:
  for li in poly.loop_indices:
   old=uv.data[li].uv.copy();uv.data[li].uv=((2+(old.x*4)%1)/4,((old.y*4)%1)/4)
def finish(obj,name,role):
 obj.name=name;bpy.context.view_layer.objects.active=obj
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 obj.data.materials.clear();obj.data.materials.append(material)
 while obj.data.uv_layers:obj.data.uv_layers.remove(obj.data.uv_layers[0])
 uv=obj.data.uv_layers.new(name='LandmarkAtlasUV');row,col=divmod(roles[role],4)
 for poly in obj.data.polygons:
  for li in poly.loop_indices:
   co=obj.data.vertices[obj.data.loops[li].vertex_index].co
   u=(co.x*.13+co.z*.07)%1;v=(co.y*.13+co.z*.11)%1
   uv.data[li].uv=((col+.08+.84*u)/4,(row+.08+.84*v)/4)
 parts.append(obj);obj.select_set(False);return obj
def beam(name,a,b,width,role='iron'):
 delta=Vector(b)-Vector(a);bpy.ops.mesh.primitive_cube_add(size=1,location=(Vector(a)+Vector(b))*.5)
 o=bpy.context.object;o.dimensions=(width,width,delta.length);o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();return finish(o,name,role)
def cylinder(name,loc,radius,depth,role='iron',sides=12,scale=(1,1,1)):
 bpy.ops.mesh.primitive_cylinder_add(vertices=sides,radius=radius,depth=depth,location=loc)
 o=bpy.context.object;o.scale=scale;return finish(o,name,role)
# Double rim, spokes, hub and drive spindle remain below the original gate apex.
cx,cz=-3.7,1.83
for side in [-.24,.24]:
 for i in range(24):
  t=i*math.tau/24;u=(i+1)*math.tau/24
  beam(f'LockWheel.Rim.{side}.{i}',(cx+1.47*math.cos(t),side,cz+1.47*math.sin(t)),(cx+1.47*math.cos(u),side,cz+1.47*math.sin(u)),.16,'iron')
 for i in range(8):
  t=i*math.tau/8
  beam(f'LockWheel.Spoke.{side}.{i}',(cx,side,cz),(cx+1.43*math.cos(t),side,cz+1.43*math.sin(t)),.105,'brass')
for i in range(24):
 t=i*math.tau/24
 beam(f'LockWheel.Tooth.{i}',(cx+1.46*math.cos(t),-.35,cz+1.46*math.sin(t)),(cx+1.46*math.cos(t),.35,cz+1.46*math.sin(t)),.15,'brass')
beam('LockWheel.Axle',(cx,-.7,cz),(cx,1.15,cz),.32,'iron')
for side in [-.65,.85]:
 beam(f'LockWheel.Support.{side}',(cx,side,.22),(cx,side,cz),.3,'stone')
 beam(f'LockWheel.Shoe.{side}',(cx-.65,side,.22),(cx+.65,side,.22),.32,'stone')
beam('LockWheel.DriveShaft',(cx,1.05,cz),(-1.8,1.05,cz),.16,'iron')
# One body, one material; the four other bodies retain their exact bytes.
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.join();rig.name='canal-gate-works'
for p in rig.data.polygons:p.material_index=0
while len(rig.data.materials)>1:rig.data.materials.pop(index=len(rig.data.materials)-1)
tri=sum(len(p.vertices)-2 for p in rig.data.polygons);assert tri<=3000,tri
bounds=([min(v.co[i] for v in rig.data.vertices) for i in range(3)],[max(v.co[i] for v in rig.data.vertices) for i in range(3)])
assert all(abs(a-b)<.0001 for aa,bb in zip(original_bounds,bounds) for a,b in zip(aa,bb)),(original_bounds,bounds)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str((out/'dome-basin-landmarks.blend').resolve()))
bpy.ops.export_scene.gltf(filepath=str((out/'canal-gate-works.glb').resolve()),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
print('DRESSING_RESULT',json.dumps({'triangles':tri,'bounds':{'min':bounds[0],'max':bounds[1]},'sourceSha256':hashlib.sha256(Path(a.source).read_bytes()).hexdigest(),'glbSha256':hashlib.sha256((out/'canal-gate-works.glb').read_bytes()).hexdigest()}))
