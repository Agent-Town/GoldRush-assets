"""Derive a cooled mechanical hull inside the old titan shelf's exact envelope.
Blender --background --python this.py -- --source <base blend> --out <directory>.
No raster edits; four peers and shared atlas are retained byte-for-byte.
"""
from pathlib import Path
import argparse,bpy,hashlib,json,math,sys
from mathutils import Vector
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--out',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path(a.source).resolve()));rig=bpy.data.objects['cooled-titan-shelf'];mat=rig.data.materials[0]
bounds=lambda o:{'min':[min(v.co[i] for v in o.data.vertices) for i in range(3)],'max':[max(v.co[i] for v in o.data.vertices) for i in range(3)]}
original=bounds(rig);rig.data.clear_geometry();parts=[rig]
# Match the existing native Ember atlas's role allocation.
# UV origin is bottom-left: row 3 selects the image's top row.
roles={'iron':1,'stone':9,'brass':8,'edge':13,'dark':9}
def finish(o,name,role):
 o.name=name;bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.data.materials.clear();o.data.materials.append(mat)
 while o.data.uv_layers:o.data.uv_layers.remove(o.data.uv_layers[0])
 uv=o.data.uv_layers.new(name='EmberTitanUV');row,col=divmod(roles[role],4)
 low=[min(v.co[k] for v in o.data.vertices) for k in range(3)];span=max(max(v.co[k] for v in o.data.vertices)-low[k] for k in range(3))
 for p in o.data.polygons:
  axis=max(range(3),key=lambda k:abs(p.normal[k]));axes=[k for k in range(3) if k!=axis]
  for li in p.loop_indices:
   co=o.data.vertices[o.data.loops[li].vertex_index].co;u=(co[axes[0]]-low[axes[0]])/span;v=(co[axes[1]]-low[axes[1]])/span;uv.data[li].uv=((col+.08+.84*u)/4,(row+.08+.84*v)/4)
 parts.append(o);o.select_set(False);return o

def box(name,p,s,role='iron'):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.dimensions=s;return finish(o,name,role)
def beam(name,a,b,w,role='iron'):
 d=Vector(b)-Vector(a);bpy.ops.mesh.primitive_cube_add(size=1,location=(Vector(a)+Vector(b))*.5);o=bpy.context.object;o.dimensions=(w,w,d.length);o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return finish(o,name,role)
def cyl(name,a,b,r,role='iron',n=12):
 d=Vector(b)-Vector(a);bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=d.length,location=(Vector(a)+Vector(b))*.5);o=bpy.context.object;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return finish(o,name,role)
def torus(name,p,r,t,role='brass',rot=(math.pi/2,0,0),n=24):
 bpy.ops.mesh.primitive_torus_add(major_segments=n,minor_segments=5,location=p,major_radius=r,minor_radius=t,rotation=rot);return finish(bpy.context.object,name,role)
# An octagonal rock footing retains the old exact X/Y extrema and reduces slab area.
bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=1,depth=.20,location=(0,0,.10));o=bpy.context.object;o.scale=(3.2,2.2,1);finish(o,'Titan.BrokenShelf','stone')
box('Titan.Keel',(0,.25,.51),(2.1,2.4,.60),'dark')
cyl('Titan.Hull',(0,-.48,1.47),(0,1.32,1.47),.77,'iron',24)
for y in [-.42,.22,.89,1.27]:torus('Titan.HullBand',(0,y,1.47),.80,.065,'edge',n=20)
box('Titan.Crown',(0,.80,2.42),(1.65,.48,.16),'brass')
for x in [-.62,.62]:beam('Titan.CrownSupport',(x,.80,1.95),(x,.80,2.4),.16,'iron')
cyl('Titan.ColdCore',(0,-.57,1.47),(0,-.69,1.47),.60,'dark',20)
torus('Titan.CoreRim',(0,-.73,1.47),.58,.075,'edge',n=24)
cyl('Titan.CoreHub',(0,-.72,1.47),(0,-.86,1.47),.20,'brass',12)
for i in range(8):
 t=i*math.tau/8;beam('Titan.CoreSpoke',(0,-.76,1.47),(.53*math.cos(t),-.76,1.47+.53*math.sin(t)),.055,'iron')
for side in [-1,1]:
 # Articulated recovery arms lie against the cooled ground; no weapon barrels.
 shoulder=(side*1.02,.87,1.35);elbow=(side*2.15,-.15,.77);wrist=(side*2.42,-1.23,.40)
 cyl('Titan.Shoulder',(side*.72,.87,1.35),(side*1.42,.87,1.35),.43,'iron',16)
 cyl('Titan.ShoulderRim',(side*1.34,.87,1.35),(side*1.44,.87,1.35),.47,'edge',16)
 cyl('Titan.UpperArm',shoulder,elbow,.32,'iron',12);cyl('Titan.Forearm',elbow,wrist,.28,'iron',12)
 for p,r in [(elbow,.36),(wrist,.32)]:
  cyl('Titan.Joint',(p[0],p[1]-.12,p[2]),(p[0],p[1]+.12,p[2]),r,'brass',12)
 beam('Titan.Piston',(side*1.18,.91,1.73),(side*2.28,-.04,1.05),.11,'edge')
 box('Titan.Palm',(side*2.40,-1.37,.36),(.78,.53,.30),'iron')
 for j in range(3):
  x=side*2.40+(j-1)*.23
  beam('Titan.FingerRoot',(x,-1.50,.37),(x,-1.83,.24),.16,'edge')
  beam('Titan.FingerTip',(x,-1.83,.24),(x,-2.02,.14),.14,'iron')
 # Pipes terminate into the hull and rear support, rather than floating rods.
 cyl('Titan.ReturnPipe',(side*.92,.55,.66),(side*.92,1.42,.66),.11,'edge',8)
 cyl('Titan.ReturnElbow',(side*.92,1.42,.66),(side*.48,1.42,1.02),.11,'iron',8)
for x in [-.53,0,.53]:box('Titan.RearFin',(x,1.40,1.55),(.12,.32,1.06),'brass')
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.join();rig.name='cooled-titan-shelf'
for p in rig.data.polygons:p.material_index=0
while len(rig.data.materials)>1:rig.data.materials.pop(index=len(rig.data.materials)-1)
tri=sum(len(p.vertices)-2 for p in rig.data.polygons);assert tri<=3000,tri;current=bounds(rig)
assert all(abs(a-b)<.0001 for k in original for a,b in zip(original[k],current[k])),(original,current)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'ember-shore-landmarks.blend'))
p=out/'cooled-titan-shelf.glb';bpy.ops.export_scene.gltf(filepath=str(p),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
result={'triangles':tri,'bounds':current,'glbSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'sourceSha256':hashlib.sha256(Path(a.source).read_bytes()).hexdigest(),'baseAreaChangePercent':(math.sqrt(2)/2-1)*100}
(out/'derivation.json').write_text(json.dumps(result,indent=2)+'\n');print('TITAN_REBUILT',json.dumps(result))
