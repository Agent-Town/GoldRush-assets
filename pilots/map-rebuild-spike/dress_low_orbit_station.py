"""Derive a compact salvage station from the reviewed Low Orbit carcass blend.

Run in Blender with --source <original low-orbit-landmarks.blend> --out <directory>.
Source hash is recorded in the correction evidence. This keeps the four peer
bodies, original crane/claws, one shared atlas, and the existing body envelope.
No raster art is generated, no gameplay or collision data is written.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--out',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path(a.source).resolve()))
rig=bpy.data.objects['claw-carcass-rig'];material=rig.data.materials[0]
original_bounds=([min(v.co[i] for v in rig.data.vertices) for i in range(3)],[max(v.co[i] for v in rig.data.vertices) for i in range(3)])
# The first component is the old low rectangular stage, not any crane member.
base=list(rig.data.vertices)[:8]
assert len(rig.data.vertices)==2976 and all(-.001<=v.co.z<=.221 for v in base)
bm=bmesh.new();bm.from_mesh(rig.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in range(8)],context='VERTS');bm.to_mesh(rig.data);bm.free()
parts=[rig]
roles={'iron':1,'stone':2,'brass':8,'teal':4,'soot':9}
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
   if name=='SalvageStation.RecoveryHousing':
    u=math.atan2((co.y-.45)/.75,co.x)/math.tau+.5;v=(co.z-.95)/1.95
    if poly.index%4==1:row,col=divmod(roles['soot'],4)
    else:row,col=divmod(roles[role],4)
   uv.data[li].uv=((col+.08+.84*u)/4,(row+.08+.84*v)/4)
 parts.append(obj);obj.select_set(False);return obj
def beam(name,a,b,width,role='iron'):
 delta=Vector(b)-Vector(a);bpy.ops.mesh.primitive_cube_add(size=1,location=(Vector(a)+Vector(b))*.5)
 o=bpy.context.object;o.dimensions=(width,width,delta.length);o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();return finish(o,name,role)
def cylinder(name,loc,radius,depth,role='iron',sides=12,scale=(1,1,1)):
 bpy.ops.mesh.primitive_cylinder_add(vertices=sides,radius=radius,depth=depth,location=loc)
 o=bpy.context.object;o.scale=scale;return finish(o,name,role)
# Chamfered oval work base replaces the black card. Its height and extrema match.
cylinder('SalvageStation.ChamferedBase',(0,0,.11),1,.22,'stone',8,(4.2,3.2,1))
# A thick annular recovery housing supplies a readable primary mass around the hoist.
verts=[];faces=[];segments=16
for height in [.95,2.9]:
 for radius in [1.4,2.2]:
  for i in range(segments):
   t=i*math.tau/segments;verts.append((radius*math.cos(t),.45+radius*.75*math.sin(t),height))
for i in range(segments):
 j=(i+1)%segments
 faces.extend([(16+i,16+j,48+j,48+i),(i,32+i,32+j,j),(32+i,48+i,48+j,32+j),(i,j,16+j,16+i)])
mesh=bpy.data.meshes.new('RecoveryHousing');mesh.from_pydata(verts,[],faces);mesh.update()
obj=bpy.data.objects.new('RecoveryHousing',mesh);bpy.context.collection.objects.link(obj);obj.select_set(True);finish(obj,'SalvageStation.RecoveryHousing','iron')
cylinder('SalvageStation.Recess',(0,.45,.98),1.38,.06,'soot',8,(1,.75,1))
for i in range(4):
 t=i*math.tau/4;x=2.21*math.cos(t);y=.45+1.66*math.sin(t)
 beam(f'SalvageStation.HousingRib.{i}',(x,y,.99),(x,y,2.88),.09,'brass')
# An open upper service ring and suspended bracing give the carcass a station body.
for i in range(12):
 t=i*math.tau/12;u=(i+1)*math.tau/12
 beam(f'SalvageStation.ServiceRing.{i}',(3.3*math.cos(t),2.12*math.sin(t),3.5),(3.3*math.cos(u),2.12*math.sin(u),3.5),.20,'brass')
for i,(x,y) in enumerate([(-2.55,-1.5),(2.55,-1.5),(-2.55,1.5),(2.55,1.5)]):
 beam(f'SalvageStation.Pier.{i}',(x,y,.22),(x,y,3.5),.22)
 beam(f'SalvageStation.RingCoupling.{i}',(x,y,3.32),(x,y,3.67),.42,'iron')
 beam(f'SalvageStation.Brace.{i}',(x*.6,y,.4),(x,y,2.7),.13,'brass')
 beam(f'SalvageStation.Suspension.{i}',(x,y,3.5),(x*.65,0,5.75),.08)
for i,x in enumerate([-1.65,1.65]):
 cylinder(f'SalvageStation.PressureCell.{i}',(x,.5,.94),.30,1.1,'brass',8)
# Join into the same one-mesh, one-material body; peer objects are untouched.
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.join();rig.name='claw-carcass-rig'
# Consolidate the identical atlas material slots produced by the join.
for p in rig.data.polygons:p.material_index=0
while len(rig.data.materials)>1:rig.data.materials.pop(index=len(rig.data.materials)-1)
tri=sum(len(p.vertices)-2 for p in rig.data.polygons);assert tri<=3000,tri
bounds=([min(v.co[i] for v in rig.data.vertices) for i in range(3)],[max(v.co[i] for v in rig.data.vertices) for i in range(3)])
assert all(abs(a-b)<.0001 for aa,bb in zip(original_bounds,bounds) for a,b in zip(aa,bb)),(original_bounds,bounds)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str((out/'low-orbit-landmarks.blend').resolve()))
bpy.ops.export_scene.gltf(filepath=str((out/'claw-carcass-rig.glb').resolve()),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
print('DRESSING_RESULT',json.dumps({'triangles':tri,'bounds':{'min':bounds[0],'max':bounds[1]},'sourceSha256':hashlib.sha256(Path(a.source).read_bytes()).hexdigest(),'glbSha256':hashlib.sha256((out/'claw-carcass-rig.glb').read_bytes()).hexdigest()}))
