"""Derive an open library portal inside the old entry gate's exact envelope.
Blender --background --python this.py -- --source <base blend> --out <directory>.
No raster edits; four peers and shared atlas are retained byte-for-byte.
"""
from pathlib import Path
import argparse,bpy,hashlib,json,math,sys
from mathutils import Vector
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--out',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path(a.source).resolve()));rig=bpy.data.objects['archive-entry-gate'];mat=rig.data.materials[0]
bounds=lambda o:{'min':[min(v.co[i] for v in o.data.vertices) for i in range(3)],'max':[max(v.co[i] for v in o.data.vertices) for i in range(3)]}
original=bounds(rig);rig.data.clear_geometry();parts=[rig]
# Match the existing native Ember atlas's role allocation.
# UV origin is bottom-left: row 3 selects the image's top row.
roles={'iron':1,'stone':2,'brass':8,'edge':6,'dark':13,'teal':4}
def finish(o,name,role):
 o.name=name;bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.data.materials.clear();o.data.materials.append(mat)
 while o.data.uv_layers:o.data.uv_layers.remove(o.data.uv_layers[0])
 uv=o.data.uv_layers.new(name='ArchiveGateUV');row,col=divmod(roles[role],4)
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
# Two narrow masonry piers replace the central bridge-school slab.
# Extremal foot corners and the high capitals retain the exact original envelope.
for side in [-1,1]:
 x=side*4.5
 box('Archive.Foot',(x,0,.13),(1.6,4.8,.26),'iron')
 box('Archive.PierPlinth',(x,.18,.48),(1.45,2.7,.44),'stone')
 cyl('Archive.Column',(x,.20,.70),(x,.20,7.7),.52,'stone',12)
 for i in range(8):
  t=i*math.tau/8
  cyl('Archive.Flute',(x+.53*math.cos(t),.20+.53*math.sin(t),1.0),(x+.53*math.cos(t),.20+.53*math.sin(t),7.25),.045,'edge',6)
 for z in [.84,3.2,5.6,7.6]:box('Archive.Course',(x,.20,z),(1.36,1.42,.20),'stone')
 box('Archive.Capital',(x,.20,7.95),(1.55,1.75,.5),'stone')
 box('Archive.Crown',(x,.20,8.445),(1.30,1.50,.49),'brass')
 # Broken lintels stop short of one another, as on the library plate.
 box('Archive.BrokenLintel',(side*2.35,.40,7.92),(3.8,.85,.42),'stone')
 box('Archive.Inscription',(side*2.35,-.05,7.92),(3.5,.06,.13),'brass')
 beam('Archive.RuinBrace',(x,1.9,.26),(x,.20,5.8),.16,'iron')
 for z in [1.5,2.1,2.7]:
  box('Archive.Mark',(x,-.38,z),(.36,.06,.15),'brass')
 # Small framed glass niches are part of the piers, not a filled central portal.
 box('Archive.NicheBack',(x,-.51,6.3),(.62,.08,.92),'dark')
 box('Archive.NicheGlass',(x,-.58,6.3),(.39,.06,.68),'teal')
 for dx in [-.27,.27]:box('Archive.NicheStile',(x+dx,-.63,6.3),(.065,.10,.98),'brass')
 for z in [5.85,6.75]:box('Archive.NicheRail',(x,-.63,z),(.60,.10,.065),'brass')
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.join();rig.name='archive-entry-gate'
for p in rig.data.polygons:p.material_index=0
while len(rig.data.materials)>1:rig.data.materials.pop(index=len(rig.data.materials)-1)
tri=sum(len(p.vertices)-2 for p in rig.data.polygons);assert tri<=3000,tri;current=bounds(rig)
assert all(abs(a-b)<.0001 for k in original for a,b in zip(original[k],current[k])),(original,current)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'archive-world-landmarks.blend'))
p=out/'archive-entry-gate.glb';bpy.ops.export_scene.gltf(filepath=str(p),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_animations=False,export_materials='EXPORT',export_extras=True)
result={'triangles':tri,'bounds':current,'glbSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'sourceSha256':hashlib.sha256(Path(a.source).read_bytes()).hexdigest(),'centralOpeningWidthMeters':7.64,'footingAreaChangePercent':(2*1.6/10.6-1)*100}
(out/'derivation.json').write_text(json.dumps(result,indent=2)+'\n');print('ARCHIVE_GATE_REBUILT',json.dumps(result))
